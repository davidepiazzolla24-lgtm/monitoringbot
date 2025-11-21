"""
Notification channel implementations for report delivery.
"""
from __future__ import annotations

import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path
from typing import Iterable, Mapping, Optional


@dataclass
class EmailChannel:
    """Simple SMTP email channel.

    Args:
        smtp_host: Hostname of the SMTP server.
        smtp_port: Port to connect to.
        sender: Email address to use as sender.
        recipients: List of recipient addresses.
        username: Optional username for authenticated SMTP.
        password: Optional password for authenticated SMTP.
        use_tls: Whether to use STARTTLS.
    """

    smtp_host: str
    smtp_port: int
    sender: str
    recipients: Iterable[str]
    username: Optional[str] = None
    password: Optional[str] = None
    use_tls: bool = True

    def send(self, subject: str, html_body: str, attachments: Mapping[str, bytes]) -> None:
        message = EmailMessage()
        message["From"] = self.sender
        message["To"] = ", ".join(self.recipients)
        message["Subject"] = subject
        message.set_content("This email contains an HTML summary and attachments.")
        message.add_alternative(html_body, subtype="html")

        for filename, content in attachments.items():
            message.add_attachment(content, maintype="text", subtype="csv", filename=filename)

        if self.use_tls:
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls(context=context)
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.send_message(message)
        else:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.send_message(message)


@dataclass
class SlackFileChannel:
    """Placeholder Slack channel that stores payloads locally.

    The implementation writes the HTML body and attachments to disk so the
    scheduler can operate without a real Slack token in this environment.
    """

    output_dir: Path

    def send(self, subject: str, html_body: str, attachments: Mapping[str, bytes]) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        summary_path = self.output_dir / f"{subject.replace(' ', '_')}.html"
        summary_path.write_text(html_body, encoding="utf-8")
        for filename, content in attachments.items():
            (self.output_dir / filename).write_bytes(content)
