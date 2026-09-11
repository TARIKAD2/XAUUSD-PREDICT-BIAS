"""Structured application logging without exposing settings or secrets."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any


class JsonFormatter(logging.Formatter):
    """Render application records as one JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in ("request_id", "method", "path", "status_code", "duration_ms", "environment"):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str, ensure_ascii=False)


def configure_logging(log_level: str) -> None:
    """Configure the project's logger idempotently for container-friendly output."""
    application_logger = logging.getLogger("app")
    application_logger.setLevel(log_level)
    application_logger.handlers.clear()
    application_logger.propagate = False

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    application_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Return a logger that inherits the configured application handler."""
    return logging.getLogger(name)