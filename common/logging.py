"""Structured logging helpers."""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime
from typing import Any, Mapping, MutableMapping

_DEFAULT_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


class StructuredFormatter(logging.Formatter):
    """A JSON formatter that preserves structured log fields."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401 - overriding base doc
        payload: MutableMapping[str, Any] = {
            "timestamp": datetime.utcfromtimestamp(record.created).strftime(
                _DEFAULT_TIME_FORMAT
            ),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        if record.stack_info:
            payload["stack_info"] = self.formatStack(record.stack_info)

        # Include any custom attributes provided via LoggerAdapter extra
        for key, value in record.__dict__.items():
            if key.startswith("_"):
                continue
            if key in payload:
                continue
            if key in {
                "msg",
                "args",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "pathname",
                "filename",
                "module",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "levelno",
                "levelname",
                "name",
                "thread",
                "threadName",
                "processName",
                "process",
            }:
                continue
            payload[key] = value

        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: int | str = logging.INFO) -> logging.Logger:
    """Configure the root logger with a structured handler."""

    root = logging.getLogger()
    root.setLevel(level)

    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        root.addHandler(handler)

    return root


class StructuredLoggerAdapter(logging.LoggerAdapter):
    """Logger adapter that merges in structured context for every record."""

    def process(self, msg: str, kwargs: Mapping[str, Any]):  # type: ignore[override]
        extra = dict(self.extra)
        extra.update(kwargs.pop("extra", {}))
        kwargs["extra"] = extra
        return msg, kwargs


def get_logger(name: str, **context: Any) -> StructuredLoggerAdapter:
    """Return a logger that emits JSON-formatted structured logs."""

    base_logger = logging.getLogger(name)
    return StructuredLoggerAdapter(base_logger, context)
