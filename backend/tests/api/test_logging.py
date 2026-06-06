from __future__ import annotations

import json
import logging
from uuid import uuid4

import pytest

from app.core.logging import JsonLogFormatter, configure_json_logging


def test_json_log_formatter_includes_extra_context() -> None:
    report_run_id = uuid4()
    record = logging.LogRecord(
        name="app.api.reports",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="report job queued",
        args=(),
        exc_info=None,
    )
    record.__dict__["report_run_id"] = str(report_run_id)
    record.__dict__["attempt"] = 1

    payload = json.loads(JsonLogFormatter().format(record))

    assert payload["level"] == "INFO"
    assert payload["logger"] == "app.api.reports"
    assert payload["message"] == "report job queued"
    assert payload["report_run_id"] == str(report_run_id)
    assert payload["attempt"] == 1
    assert "timestamp" in payload


def test_configure_json_logging_is_idempotent() -> None:
    logger = logging.getLogger("app")
    original_handlers = list(logger.handlers)
    original_level = logger.level
    original_propagate = logger.propagate
    try:
        configure_json_logging("DEBUG")
        configure_json_logging("INFO")

        json_handlers = [
            handler
            for handler in logger.handlers
            if getattr(handler, "_land_diligence_json_handler", False)
        ]
        assert len(json_handlers) == 1
        assert isinstance(json_handlers[0].formatter, JsonLogFormatter)
        assert logger.level == logging.INFO
        assert logger.propagate is False
    finally:
        logger.handlers.clear()
        logger.handlers.extend(original_handlers)
        logger.setLevel(original_level)
        logger.propagate = original_propagate


def test_configure_json_logging_rejects_unknown_level() -> None:
    with pytest.raises(ValueError, match="Unsupported LOG_LEVEL"):
        configure_json_logging("verbose")
