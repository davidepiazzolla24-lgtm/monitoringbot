"""Lightweight Icinga2 REST API client wrapper.

This module provides a small helper around the Icinga2 REST API. It wraps the
endpoints we need for hosts, services, status and event streams and handles the
basic authentication configuration once at startup.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, Optional

import requests

LOGGER = logging.getLogger(__name__)


class IcingaClient:
    """Simple wrapper around the Icinga2 REST API.

    Parameters
    ----------
    base_url:
        Base URL of the Icinga2 API (for example: ``https://icinga.example:5665/v1``).
    username:
        API username configured on the Icinga2 master.
    password:
        API password for the user.
    verify:
        Whether TLS verification should be enabled. Set to ``False`` for self-signed
        labs and tests.
    timeout:
        Default request timeout in seconds.
    """

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        *,
        verify: bool = True,
        timeout: int = 10,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.auth = (username, password)
        self.session.verify = verify
        self.timeout = timeout

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        LOGGER.debug("Requesting %s with params=%s", url, params)
        response = self.session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def get_hosts(self, filters: Optional[Dict[str, Any]] = None) -> Iterable[Dict[str, Any]]:
        """Return host objects.

        Parameters
        ----------
        filters:
            Optional query parameters to pass to the API.
        """

        payload = self._get("objects/hosts", filters)
        return payload.get("results", [])

    def get_services(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> Iterable[Dict[str, Any]]:
        """Return service objects."""

        payload = self._get("objects/services", filters)
        return payload.get("results", [])

    def get_status(self) -> Dict[str, Any]:
        """Return the overall Icinga status summary."""

        return self._get("status")

    def get_events(self, queue: str = "icinga") -> Iterable[Dict[str, Any]]:
        """Read events from the events API endpoint.

        The Icinga event API (``events``) acts like a small queue that can be filtered
        by ``queue`` name. This helper keeps the interface consistent across the
        application.
        """

        payload = self._get("events", params={"queue": queue})
        return payload.get("results", [])
