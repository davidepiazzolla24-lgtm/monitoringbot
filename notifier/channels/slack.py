import json
from typing import Dict, Optional

import requests

from ..models import Notification


class SlackChannel:
    def __init__(
        self,
        webhook_url: str,
        default_channel: Optional[str] = None,
        username: str = "monitoringbot",
    ) -> None:
        self.webhook_url = webhook_url
        self.default_channel = default_channel
        self.username = username

    def build_payload(self, notification: Notification) -> Dict:
        attachments = [
            {
                "title": f"{notification.severity} alert for {notification.service}",
                "text": notification.message,
                "fields": [
                    {"title": "Host", "value": notification.host, "short": True},
                    {"title": "Service", "value": notification.service, "short": True},
                    {"title": "State", "value": notification.state, "short": True},
                ],
                "ts": int(notification.timestamp.timestamp()),
            }
        ]
        payload = {"username": self.username, "attachments": attachments}
        if self.default_channel:
            payload["channel"] = self.default_channel
        return payload

    def send(self, notification: Notification) -> None:
        payload = self.build_payload(notification)
        response = requests.post(self.webhook_url, data=json.dumps(payload), headers={"Content-Type": "application/json"})
        response.raise_for_status()
