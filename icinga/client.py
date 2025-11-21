"""Client for interacting with the Icinga monitoring API."""
from __future__ import annotations

import time
from typing import Any, Mapping, MutableMapping

import requests

from common.logging import get_logger
from common.metrics import metrics

DEFAULT_TIMEOUT = 10


class IcingaClient:
    """Lightweight HTTP client for Icinga."""

    def __init__(
        self,
        base_url: str,
        api_token: str,
        *,
        session: requests.Session | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()
        self.session.headers.update({"Accept": "application/json", "Authorization": api_token})
        self.logger = get_logger(__name__, component="icinga_client")

    def fetch_service(self, service: str, timeout: int = DEFAULT_TIMEOUT) -> Mapping[str, Any]:
        """Fetch a service object from the Icinga API.

        Parameters
        ----------
        service: str
            The host/service pair, e.g. "web!http".
        timeout: int
            Timeout for the request in seconds.
        """

        url = f"{self.base_url}/v1/objects/services/{service}"
        start = time.monotonic()
        response = None
        try:
            response = self.session.get(url, timeout=timeout)
            metrics.record_request(response.status_code)
            response.raise_for_status()
            payload: MutableMapping[str, Any] = response.json()
            self.logger.info("Fetched service", extra={"service": service, "status": response.status_code})
            return payload
        except requests.RequestException as exc:
            metrics.record_request("exception")
            self.logger.error("Failed to fetch service", extra={"service": service, "error": str(exc)})
            raise
        finally:
            elapsed = time.monotonic() - start
            metrics.observe_latency(elapsed)
            if response is not None:
                self.logger.debug(
                    "Request complete",
                    extra={"service": service, "elapsed_seconds": round(elapsed, 3)},
                )
