"""Utilities to normalize Icinga events for downstream consumers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

STATUS_MAPPING = {
    "OK": "OK",
    "UP": "OK",
    "WARNING": "WARNING",
    "CRITICAL": "CRITICAL",
    "UNKNOWN": "UNKNOWN",
    "DOWN": "DOWN",
}


def _to_iso_timestamp(value: Any) -> str:
    """Convert various timestamp formats to ISO 8601 strings."""

    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()

    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            # Fallback for unknown formats: treat as UTC naive
            parsed = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            parsed = parsed.replace(tzinfo=timezone.utc)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.isoformat()

    return datetime.now(tz=timezone.utc).isoformat()


def normalize_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a raw Icinga event structure.

    The function harmonizes severity/status values and ensures timestamps are ISO 8601
    strings so that downstream queues can consume a predictable shape.
    """

    raw_status = str(event.get("state", event.get("status", "UNKNOWN"))).upper()
    normalized_status = STATUS_MAPPING.get(raw_status, "UNKNOWN")

    return {
        "host": event.get("host") or event.get("host_name"),
        "service": event.get("service") or event.get("service_name"),
        "severity": normalized_status,
        "message": event.get("message") or event.get("output"),
        "timestamp": _to_iso_timestamp(event.get("timestamp") or event.get("time")),
        "raw": event,
    }
