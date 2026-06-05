from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.connectors.observability import (
    ConnectorEventType,
    ConnectorObservabilityEvent,
    new_observability_log,
)


def _make_event(
    event_type: ConnectorEventType = ConnectorEventType.run_started,
    connector_name: str = "test_connector",
    message: str = "test message",
) -> ConnectorObservabilityEvent:
    return ConnectorObservabilityEvent(
        event_type=event_type,
        connector_name=connector_name,
        ingest_run_id=uuid4(),
        message=message,
        timestamp=datetime.now(UTC),
    )


def test_empty_log_has_len_zero() -> None:
    log = new_observability_log()
    assert len(log) == 0


def test_recording_run_started_event_increases_len_to_one() -> None:
    log = new_observability_log()
    log.record(_make_event(ConnectorEventType.run_started))
    assert len(log) == 1


def test_recording_multiple_events_accumulates_correctly() -> None:
    log = new_observability_log()
    log.record(_make_event(ConnectorEventType.run_started))
    log.record(_make_event(ConnectorEventType.evidence_stored))
    log.record(_make_event(ConnectorEventType.run_succeeded))
    assert len(log) == 3
    assert len(log.events) == 3


def test_events_of_type_filters_correctly() -> None:
    log = new_observability_log()
    log.record(_make_event(ConnectorEventType.run_started))
    log.record(_make_event(ConnectorEventType.evidence_stored))
    log.record(_make_event(ConnectorEventType.evidence_stored))
    log.record(_make_event(ConnectorEventType.run_succeeded))

    evidence_events = log.events_of_type(ConnectorEventType.evidence_stored)
    assert len(evidence_events) == 2
    assert all(e.event_type == ConnectorEventType.evidence_stored for e in evidence_events)


def test_events_of_type_returns_empty_tuple_when_no_matching_events() -> None:
    log = new_observability_log()
    log.record(_make_event(ConnectorEventType.run_started))

    result = log.events_of_type(ConnectorEventType.rate_limited)
    assert result == ()
    assert isinstance(result, tuple)


def test_connector_observability_event_is_frozen() -> None:
    event = _make_event()
    with pytest.raises(FrozenInstanceError):
        event.message = "mutated"  # type: ignore[misc]


def test_all_connector_event_types_are_accessible() -> None:
    expected = {
        "run_started",
        "run_succeeded",
        "run_failed",
        "rate_limited",
        "retry_attempt",
        "evidence_stored",
        "source_failure_stored",
    }
    actual = {e.value for e in ConnectorEventType}
    assert actual == expected
