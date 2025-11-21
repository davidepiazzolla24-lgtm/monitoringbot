from __future__ import annotations

import json

import responses

from common.metrics import metrics
from notifier import Notifier


def test_notifier_sends_payload_and_success_response():
    metrics.reset()
    webhook_url = "https://hooks.example/webhook"
    notifier = Notifier(webhook_url)

    alert = {"summary": "Service down", "severity": "critical", "details": {"host": "web"}}

    with responses.RequestsMock() as rsps:
        rsps.add("POST", webhook_url, status=204)
        delivered = notifier.send(alert)

    assert delivered is True
    assert len(rsps.calls) == 1
    posted_body = json.loads(rsps.calls[0].request.body)
    assert posted_body == alert
    assert metrics.notifier_failures_total.labels(reason="http_error")._value.get() == 0  # type: ignore[attr-defined]


def test_notifier_records_failure_on_error():
    metrics.reset()
    webhook_url = "https://hooks.example/webhook"
    notifier = Notifier(webhook_url)

    with responses.RequestsMock() as rsps:
        rsps.add("POST", webhook_url, status=500)
        delivered = notifier.send({"summary": "fail"})

    assert delivered is False
    assert metrics.notifier_failures_total.labels(reason="http_error")._value.get() == 1  # type: ignore[attr-defined]
