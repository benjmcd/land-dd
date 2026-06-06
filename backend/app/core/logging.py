from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

_JSON_HANDLER_MARKER = "_land_diligence_json_handler"

_STANDARD_ATTRS = set(logging.makeLogRecord({}).__dict__)


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key not in _STANDARD_ATTRS and not key.startswith("_"):
                payload[key] = _json_safe(value)
        if record.exc_info is not None:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, sort_keys=True)


def configure_json_logging(log_level: str) -> None:
    logger = logging.getLogger("app")
    logger.setLevel(_parse_log_level(log_level))
    logger.propagate = False

    for handler in list(logger.handlers):
        if getattr(handler, _JSON_HANDLER_MARKER, False):
            logger.removeHandler(handler)

    handler = logging.StreamHandler()
    handler.setFormatter(JsonLogFormatter())
    setattr(handler, _JSON_HANDLER_MARKER, True)
    logger.addHandler(handler)


def _parse_log_level(log_level: str) -> int:
    level = logging.getLevelName(log_level.strip().upper())
    if isinstance(level, int):
        return level
    raise ValueError(f"Unsupported LOG_LEVEL: {log_level!r}")


def _json_safe(value: object) -> object:
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_json_safe(item) for item in value]
    return str(value)


__all__ = ["JsonLogFormatter", "configure_json_logging"]
