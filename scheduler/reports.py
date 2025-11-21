"""
Scheduled job to aggregate events from the last hour and deliver reports.
"""
from __future__ import annotations

import csv
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from io import StringIO
from pathlib import Path
from typing import Iterable, List, Mapping, MutableMapping, Sequence

from jinja2 import Environment, FileSystemLoader, select_autoescape

from reports.notifications import EmailChannel, SlackFileChannel

SEVERITIES = ("critical", "error", "warning", "info", "debug")


@dataclass
class Event:
    id: int
    occurred_at: datetime
    severity: str
    source: str
    message: str


@dataclass
class SeverityFilter:
    allowed: Sequence[str]

    def normalize(self) -> Sequence[str]:
        normalized = [level.lower() for level in self.allowed]
        return [level for level in normalized if level in SEVERITIES]


class ReportScheduler:
    def __init__(self, db_path: Path, template_dir: Path, output_dir: Path) -> None:
        self.db_path = db_path
        self.template_dir = template_dir
        self.output_dir = output_dir
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def fetch_recent_events(self, severity_filter: SeverityFilter) -> List[Event]:
        since = datetime.now(timezone.utc) - timedelta(hours=1)
        allowed = severity_filter.normalize()
        query = """
            SELECT id, occurred_at, severity, source, message
            FROM events
            WHERE occurred_at >= ?
            {severity_clause}
            ORDER BY occurred_at DESC
        """
        severity_clause = ""
        params: List[str] = [since.isoformat()]
        if allowed:
            placeholders = ",".join("?" for _ in allowed)
            severity_clause = f"AND LOWER(severity) IN ({placeholders})"
            params.extend(allowed)

        rows = self._execute_query(query.format(severity_clause=severity_clause), params)
        events = [
            Event(
                id=row[0],
                occurred_at=datetime.fromisoformat(row[1]),
                severity=row[2].lower(),
                source=row[3],
                message=row[4],
            )
            for row in rows
        ]
        return events

    def _execute_query(self, query: str, params: Iterable[str]) -> List[sqlite3.Row]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return cursor.fetchall()

    def summarize_events(self, events: Sequence[Event]) -> Mapping[str, int]:
        counts: MutableMapping[str, int] = {level: 0 for level in SEVERITIES}
        for event in events:
            if event.severity in counts:
                counts[event.severity] += 1
        return counts

    def render_html(self, events: Sequence[Event], summary: Mapping[str, int]) -> str:
        template = self.jinja_env.get_template("summary.html")
        return template.render(events=events, summary=summary, generated_at=datetime.now(timezone.utc))

    def build_csv(self, events: Sequence[Event]) -> bytes:
        buffer = StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["id", "occurred_at", "severity", "source", "message"])
        for event in events:
            writer.writerow([event.id, event.occurred_at.isoformat(), event.severity, event.source, event.message])
        return buffer.getvalue().encode("utf-8")

    def run(self, severity_filter: SeverityFilter, channel: str = "email") -> None:
        events = self.fetch_recent_events(severity_filter)
        summary = self.summarize_events(events)
        html_body = self.render_html(events, summary)
        csv_payload = self.build_csv(events)

        attachments = {"events_last_hour.csv": csv_payload}
        subject = "Hourly monitoring summary"

        if channel == "email":
            email_channel = EmailChannel(
                smtp_host="localhost",
                smtp_port=25,
                sender="noreply@example.com",
                recipients=["ops@example.com"],
                use_tls=False,
            )
            email_channel.send(subject, html_body, attachments)
        elif channel == "slack":
            slack_channel = SlackFileChannel(output_dir=self.output_dir)
            slack_channel.send(subject, html_body, attachments)
        else:
            raise ValueError(f"Unsupported channel: {channel}")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Generate and deliver monitoring reports")
    parser.add_argument("--db-path", type=Path, required=True, help="Path to the SQLite database")
    parser.add_argument(
        "--template-dir",
        type=Path,
        default=Path("reports/templates"),
        help="Directory containing Jinja2 templates",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("/tmp/monitoringbot"),
        help="Directory used by the Slack file channel",
    )
    parser.add_argument(
        "--severities",
        nargs="*",
        default=list(SEVERITIES),
        help="List of severity levels to include (default: all)",
    )
    parser.add_argument(
        "--channel",
        choices=["email", "slack"],
        default="email",
        help="Delivery channel for the report",
    )

    args = parser.parse_args()
    scheduler = ReportScheduler(db_path=args.db_path, template_dir=args.template_dir, output_dir=args.output_dir)
    scheduler.run(SeverityFilter(allowed=args.severities), channel=args.channel)


if __name__ == "__main__":
    main()
