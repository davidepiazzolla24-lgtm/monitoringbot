"""Parser for Icinga service payloads."""
from __future__ import annotations

from typing import Any, Dict, Mapping

from common.metrics import metrics

_STATE_MAP = {
    0: "OK",
    1: "WARNING",
    2: "CRITICAL",
    3: "UNKNOWN",
}


def parse_service_payload(payload: Mapping[str, Any]) -> Dict[str, Any]:
    """Parse an Icinga API response into a simplified dictionary."""

    try:
        result = payload["results"][0]
        attrs = result["attrs"]
        service_state = attrs.get("state", 3)
        output = attrs.get("output", "")
        host = result.get("name", "unknown")
    except (KeyError, IndexError, TypeError) as exc:  # pragma: no cover - defensive
        metrics.record_parser_error()
        raise ValueError("Invalid service payload") from exc

    parsed = {
        "host": host,
        "state": _STATE_MAP.get(service_state, "UNKNOWN"),
        "output": output,
    }

    if parsed["state"] == "UNKNOWN":
        metrics.record_parser_error()

    return parsed
