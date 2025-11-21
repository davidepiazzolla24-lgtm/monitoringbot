from email.message import EmailMessage
from typing import Iterable, List, Optional
import smtplib

from ..models import Notification


class EmailChannel:
    def __init__(
        self,
        sender: str,
        recipients: Iterable[str],
        smtp_host: str = "localhost",
        smtp_port: int = 25,
        smtp_username: Optional[str] = None,
        smtp_password: Optional[str] = None,
        use_tls: bool = False,
    ) -> None:
        self.sender = sender
        self.recipients: List[str] = list(recipients)
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.use_tls = use_tls

    def _build_message(self, notification: Notification) -> EmailMessage:
        msg = EmailMessage()
        msg["From"] = self.sender
        msg["To"] = ", ".join(self.recipients)
        msg["Subject"] = f"[{notification.severity}] {notification.service} on {notification.host}"
        msg.set_content(notification.message)
        return msg

    def send(self, notification: Notification) -> None:
        if not self.recipients:
            return
        message = self._build_message(notification)
        with smtplib.SMTP(self.smtp_host, self.smtp_port) as client:
            if self.use_tls:
                client.starttls()
            if self.smtp_username and self.smtp_password:
                client.login(self.smtp_username, self.smtp_password)
            client.send_message(message)
