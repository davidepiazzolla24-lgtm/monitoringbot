from __future__ import annotations

import pytest
import responses
from requests import HTTPError

from common.metrics import metrics
from icinga.client import IcingaClient


@pytest.fixture(autouse=True)
def reset_metrics() -> None:
    metrics.reset()


def test_fetch_service_success():
    client = IcingaClient("https://icinga.example", "token")
    service = "web!http"
    payload = {"results": [{"name": service, "attrs": {"state": 0, "output": "ok"}}]}

    with responses.RequestsMock() as rsps:
        rsps.add(
            "GET",
            f"https://icinga.example/v1/objects/services/{service}",
            json=payload,
            status=200,
        )

        result = client.fetch_service(service)

    assert result == payload
    assert metrics.icinga_requests_total.labels(status="200")._value.get() == 1  # type: ignore[attr-defined]
    assert metrics.request_latency_seconds._count.get() == 1  # type: ignore[attr-defined]


def test_fetch_service_failure_records_metrics():
    client = IcingaClient("https://icinga.example", "token")
    service = "db!mysql"

    with responses.RequestsMock() as rsps:
        rsps.add(
            "GET",
            f"https://icinga.example/v1/objects/services/{service}",
            status=500,
        )

        with pytest.raises(HTTPError):
            client.fetch_service(service)

    assert metrics.icinga_requests_total.labels(status="500")._value.get() == 1  # type: ignore[attr-defined]
    assert metrics.icinga_requests_total.labels(status="exception")._value.get() == 1  # type: ignore[attr-defined]
