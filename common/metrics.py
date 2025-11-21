"""Prometheus metrics helpers for the monitoring bot."""
from __future__ import annotations

import time
from prometheus_client import Counter, Histogram, generate_latest


class Metrics:
    """A small collection of Prometheus metrics used by the service."""

    def __init__(self) -> None:
        self.icinga_requests_total = Counter(
            "icinga_requests_total",
            "Total number of requests issued to the Icinga API.",
            ["status"],
        )
        self.parser_errors_total = Counter(
            "parser_errors_total", "Total parser failures when processing payloads."
        )
        self.notifier_failures_total = Counter(
            "notifier_failures_total",
            "Total number of failed attempts to deliver notifications.",
            ["reason"],
        )
        self.request_latency_seconds = Histogram(
            "icinga_request_latency_seconds",
            "Latency of Icinga requests in seconds.",
            buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5),
        )

    def record_request(self, status: int | str) -> None:
        self.icinga_requests_total.labels(status=str(status)).inc()

    def observe_latency(self, seconds: float) -> None:
        self.request_latency_seconds.observe(seconds)

    def record_parser_error(self) -> None:
        self.parser_errors_total.inc()

    def record_notifier_failure(self, reason: str) -> None:
        self.notifier_failures_total.labels(reason=reason).inc()

    def export(self) -> bytes:
        return generate_latest()  # pragma: no cover - thin wrapper

    def reset(self) -> None:
        self._reset_counter(self.icinga_requests_total)
        self._reset_counter(self.parser_errors_total)
        self._reset_counter(self.notifier_failures_total)
        self._reset_histogram(self.request_latency_seconds)

    @staticmethod
    def _reset_counter(counter: Counter) -> None:
        counter._value.set(0)  # type: ignore[attr-defined,protected-access]
        for sample in counter._metrics.values():  # type: ignore[attr-defined,protected-access]
            sample._value.set(0)  # type: ignore[attr-defined,protected-access]

    @staticmethod
    def _reset_histogram(histogram: Histogram) -> None:
        histogram._sum.set(0)  # type: ignore[attr-defined,protected-access]
        histogram._count.set(0)  # type: ignore[attr-defined,protected-access]
        for bucket in histogram._buckets.values():  # type: ignore[attr-defined,protected-access]
            bucket.set(0)  # type: ignore[attr-defined]


metrics = Metrics()


def time_operation(func):
    """Decorator to time operations and record latency."""

    def wrapper(*args, **kwargs):
        start = time.monotonic()
        try:
            return func(*args, **kwargs)
        finally:
            metrics.observe_latency(time.monotonic() - start)

    return wrapper
