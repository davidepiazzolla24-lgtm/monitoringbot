import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Sequence

import yaml

from .dedupe import DedupeCache
from .models import Notification
from .channels.email import EmailChannel
from .channels.slack import SlackChannel
from .channels.webhook import WebhookChannel


class NotificationRouter:
    def __init__(
        self,
        config_path: str = "config/notifications.yaml",
        dedupe_cache: DedupeCache | None = None,
    ) -> None:
        self.config_path = config_path
        self.config = self._load_config()
        self.dedupe_cache = dedupe_cache or self._build_default_dedupe()
        self.channels = self._build_channels()
        warning_config = self.config.get("routing", {}).get("warning", {})
        self.batch_size = int(warning_config.get("batch_size", 10))
        self.batch_window_seconds = int(warning_config.get("batch_window_seconds", 300))
        self._warning_batch: List[Notification] = []
        self._batch_started_at: datetime | None = None

    def _load_config(self) -> Dict:
        path = Path(self.config_path)
        if not path.exists():
            raise FileNotFoundError(f"Notification config not found at {self.config_path}")
        with path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}

    def _build_default_dedupe(self) -> DedupeCache:
        dedupe_cfg = self.config.get("dedupe", {})
        return DedupeCache(
            redis_url=dedupe_cfg.get("redis_url", "redis://localhost:6379/0"),
            ttl_seconds=int(dedupe_cfg.get("ttl_seconds", 300)),
            key_prefix=dedupe_cfg.get("key_prefix", "notifier"),
        )

    def _build_channels(self) -> Dict[str, object]:
        channels = {}
        channel_cfg = self.config.get("channels", {})
        if channel_cfg.get("slack", {}).get("enabled", False):
            slack_conf = channel_cfg.get("slack", {})
            channels["slack"] = SlackChannel(
                webhook_url=slack_conf["webhook_url"],
                default_channel=slack_conf.get("default_channel"),
                username=slack_conf.get("username", "monitoringbot"),
            )
        if channel_cfg.get("email", {}).get("enabled", False):
            email_conf = channel_cfg.get("email", {})
            channels["email"] = EmailChannel(
                sender=email_conf["sender"],
                recipients=email_conf.get("recipients", []),
                smtp_host=email_conf.get("smtp_host", "localhost"),
                smtp_port=int(email_conf.get("smtp_port", 25)),
                smtp_username=email_conf.get("smtp_username"),
                smtp_password=email_conf.get("smtp_password"),
                use_tls=bool(email_conf.get("use_tls", False)),
            )
        if channel_cfg.get("webhook", {}).get("enabled", False):
            webhook_conf = channel_cfg.get("webhook", {})
            channels["webhook"] = WebhookChannel(
                endpoint=webhook_conf["endpoint"],
                headers=webhook_conf.get("headers", {}),
            )
        return channels

    def route(self, notification: Notification) -> Dict[str, object]:
        if self.dedupe_cache and self.dedupe_cache.is_duplicate(notification):
            return {"status": "ignored", "reason": "duplicate"}

        severity = notification.severity.upper()
        if severity in {"CRITICAL", "DOWN"}:
            deliveries = self._deliver(notification, "critical")
            return {"status": "sent", "deliveries": deliveries}

        if severity == "WARNING":
            self._add_to_batch(notification)
            deliveries = []
            if self._should_flush_batch():
                deliveries = self.flush_warnings()
            return {"status": "batched", "queued": len(self._warning_batch), "deliveries": deliveries}

        deliveries = self._deliver(notification, "info")
        return {"status": "sent", "deliveries": deliveries}

    def _deliver(self, notification: Notification, route_key: str) -> List[str]:
        routing_config = self.config.get("routing", {})
        channels_for_route: Sequence[str] = routing_config.get(route_key, {}).get("channels", [])
        delivered_channels: List[str] = []
        for channel_name in channels_for_route:
            channel = self.channels.get(channel_name)
            if not channel:
                continue
            channel.send(notification)
            delivered_channels.append(channel_name)
        return delivered_channels

    def _add_to_batch(self, notification: Notification) -> None:
        self._warning_batch.append(notification)
        if not self._batch_started_at:
            self._batch_started_at = datetime.utcnow()

    def _should_flush_batch(self) -> bool:
        if not self._warning_batch:
            return False
        if len(self._warning_batch) >= self.batch_size:
            return True
        if not self._batch_started_at:
            return False
        return datetime.utcnow() - self._batch_started_at >= timedelta(seconds=self.batch_window_seconds)

    def flush_warnings(self) -> List[str]:
        if not self._warning_batch:
            return []
        combined_message = self._build_batch_message(self._warning_batch)
        representative = self._warning_batch[-1]
        batch_notification = Notification(
            host="warning-batch",
            service="warnings",
            state="WARNING",
            severity="WARNING",
            message=combined_message,
            timestamp=datetime.utcnow(),
            metadata={"count": len(self._warning_batch)},
        )
        deliveries = self._deliver(batch_notification, "warning")
        self._warning_batch = []
        self._batch_started_at = None
        if representative and self.dedupe_cache:
            self.dedupe_cache.mark(representative)
        return deliveries

    def flush_stale_batches(self) -> List[str]:
        if self._should_flush_batch():
            return self.flush_warnings()
        return []

    def _build_batch_message(self, notifications: Sequence[Notification]) -> str:
        lines = [
            f"{n.timestamp.isoformat()} | {n.host} | {n.service} | {n.state} | {n.message}"
            for n in notifications
        ]
        return "\n".join(lines)

    def wait_and_flush(self, wait_seconds: int) -> List[str]:
        time.sleep(wait_seconds)
        return self.flush_stale_batches()
