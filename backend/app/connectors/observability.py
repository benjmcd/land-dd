from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class ConnectorEventType(StrEnum):
    run_started = "run_started"
    run_succeeded = "run_succeeded"
    run_failed = "run_failed"
    rate_limited = "rate_limited"
    retry_attempt = "retry_attempt"
    evidence_stored = "evidence_stored"
    source_failure_stored = "source_failure_stored"


@dataclass(frozen=True)
class ConnectorObservabilityEvent:
    event_type: ConnectorEventType
    connector_name: str
    ingest_run_id: UUID
    message: str
    timestamp: datetime


class ConnectorRunObservabilityLog:
    def __init__(self) -> None:
        self._events: list[ConnectorObservabilityEvent] = []

    def record(self, event: ConnectorObservabilityEvent) -> None:
        self._events.append(event)

    @property
    def events(self) -> tuple[ConnectorObservabilityEvent, ...]:
        return tuple(self._events)

    def events_of_type(
        self,
        event_type: ConnectorEventType,
    ) -> tuple[ConnectorObservabilityEvent, ...]:
        return tuple(e for e in self._events if e.event_type == event_type)

    def __len__(self) -> int:
        return len(self._events)


def new_observability_log() -> ConnectorRunObservabilityLog:
    return ConnectorRunObservabilityLog()


__all__ = [
    "ConnectorEventType",
    "ConnectorObservabilityEvent",
    "ConnectorRunObservabilityLog",
    "new_observability_log",
]
