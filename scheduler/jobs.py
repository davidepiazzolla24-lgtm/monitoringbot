"""Scheduled jobs for Icinga polling and queue dispatch."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Iterable

from icinga.client import IcingaClient
from icinga.parser import normalize_event

LOGGER = logging.getLogger(__name__)


class EventPublisher:
    """Abstract queue publisher used by polling jobs."""

    def publish(self, event: dict) -> None:  # pragma: no cover - interface
        raise NotImplementedError


@dataclass
class RedisPublisher(EventPublisher):
    """Publish events to a Redis channel using a provided client."""

    client: "redis.Redis"
    channel: str

    def publish(self, event: dict) -> None:
        self.client.publish(self.channel, json.dumps(event))
        LOGGER.debug("Published event to Redis channel %s", self.channel)


@dataclass
class AMQPPublisher(EventPublisher):
    """Publish events to an AMQP queue using a provided channel."""

    channel: "pika.adapters.blocking_connection.BlockingChannel"
    queue: str

    def __post_init__(self) -> None:
        self.channel.queue_declare(queue=self.queue, durable=True)

    def publish(self, event: dict) -> None:
        pika_module = __import__("pika")
        properties = getattr(pika_module, "BasicProperties", None)
        prepared_properties = properties(delivery_mode=2) if properties else None
        self.channel.basic_publish(
            exchange="",
            routing_key=self.queue,
            body=json.dumps(event),
            properties=prepared_properties,
        )
        LOGGER.debug("Published event to AMQP queue %s", self.queue)


class IcingaPollingJob:
    """Pull events from Icinga and push them to the configured queue."""

    def __init__(
        self,
        client: IcingaClient,
        publisher: EventPublisher,
        *,
        interval: int = 60,
        queue: str = "icinga",
    ) -> None:
        self.client = client
        self.publisher = publisher
        self.interval = interval
        self.queue = queue

    def fetch_events(self) -> Iterable[dict]:
        LOGGER.debug("Fetching events from Icinga queue '%s'", self.queue)
        return self.client.get_events(queue=self.queue)

    def dispatch(self, events: Iterable[dict]) -> None:
        for event in events:
            normalized = normalize_event(event)
            LOGGER.info(
                "Dispatching event host=%s service=%s severity=%s",
                normalized.get("host"),
                normalized.get("service"),
                normalized.get("severity"),
            )
            self.publisher.publish(normalized)

    def run_once(self) -> None:
        events = list(self.fetch_events())
        if not events:
            LOGGER.debug("No events returned from Icinga queue '%s'", self.queue)
            return
        self.dispatch(events)

    def run_forever(self) -> None:
        while True:
            try:
                self.run_once()
            except Exception:  # pragma: no cover - logging safeguard
                LOGGER.exception("Unhandled error while running Icinga polling job")
            time.sleep(self.interval)


def register_celery_task(app, job: IcingaPollingJob):
    """Return a Celery task callable suitable for beat scheduling.

    Example
    -------
    >>> task = register_celery_task(celery_app, job)
    >>> app.conf.beat_schedule = {
    ...     "icinga-poll": {"task": task.name, "schedule": 60},
    ... }
    """

    @app.task(name="icinga.poll")
    def poll_icinga() -> None:
        job.run_once()

    return poll_icinga
