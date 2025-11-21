from typing import Optional

import redis

from .models import Notification


class DedupeCache:
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        ttl_seconds: int = 300,
        key_prefix: str = "notifier",
    ) -> None:
        self.redis = redis.from_url(redis_url)
        self.ttl_seconds = ttl_seconds
        self.key_prefix = key_prefix

    def _build_key(self, notification: Notification) -> str:
        return f"{self.key_prefix}:{notification.key()}"

    def is_duplicate(self, notification: Notification) -> bool:
        key = self._build_key(notification)
        added = self.redis.set(name=key, value=notification.state, ex=self.ttl_seconds, nx=True)
        return added is None

    def mark(self, notification: Notification) -> None:
        key = self._build_key(notification)
        self.redis.set(name=key, value=notification.state, ex=self.ttl_seconds)

    def get_ttl(self, notification: Notification) -> Optional[int]:
        key = self._build_key(notification)
        ttl_value = self.redis.ttl(key)
        if ttl_value is None:
            return None
        if ttl_value < 0:
            return None
        return int(ttl_value)
