import json
from typing import Dict

import requests

from ..models import Notification


class WebhookChannel:
    def __init__(self, endpoint: str, headers: Dict[str, str] | None = None) -> None:
        self.endpoint = endpoint
        self.headers = {"Content-Type": "application/json"}
        if headers:
            self.headers.update(headers)

    def send(self, notification: Notification) -> None:
        payload = notification.as_dict()
        response = requests.post(self.endpoint, data=json.dumps(payload), headers=self.headers)
        response.raise_for_status()
