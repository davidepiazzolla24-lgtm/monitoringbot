from __future__ import annotations

import pytest

from common.metrics import metrics
from parser import parse_service_payload


@pytest.fixture(autouse=True)
def reset_metrics() -> None:
    metrics.reset()


def test_parse_valid_payload_maps_state():
    payload = {"results": [{"name": "web!http", "attrs": {"state": 2, "output": "down"}}]}

    parsed = parse_service_payload(payload)

    assert parsed == {"host": "web!http", "state": "CRITICAL", "output": "down"}
    assert metrics.parser_errors_total._value.get() == 0  # type: ignore[attr-defined]


def test_parse_unknown_state_records_error():
    payload = {"results": [{"name": "cache!redis", "attrs": {"state": 7, "output": "??"}}]}

    parsed = parse_service_payload(payload)

    assert parsed["state"] == "UNKNOWN"
    assert metrics.parser_errors_total._value.get() == 1  # type: ignore[attr-defined]


def test_invalid_payload_raises_value_error():
    with pytest.raises(ValueError):
        parse_service_payload({})

    assert metrics.parser_errors_total._value.get() == 1  # type: ignore[attr-defined]
