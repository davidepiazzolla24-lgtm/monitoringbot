"""Notifier for delivering alerts to downstream systems."""
from __future__ import annotations

import json
from typing import Any, Mapping

import requests

from common.logging import get_logger
from common.metrics import metrics


class Notifier:
    def __init__(self, webhook_url: str) -> None:
        self.webhook_url = webhook_url
        self.logger = get_logger(__name__, component="notifier")

    def send(self, alert: Mapping[str, Any]) -> bool:
        payload = {
            "summary": alert.get("summary", ""),
            "severity": alert.get("severity", "info"),
            "details": alert.get("details", {}),
        }

        try:
            response = requests.post(
                self.webhook_url,
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            response.raise_for_status()
            self.logger.info("Notification delivered", extra={"severity": payload["severity"]})
            return True
        except requests.RequestException as exc:
            metrics.record_notifier_failure(reason="http_error")
            self.logger.error("Notification failed", extra={"error": str(exc)})
            return False
