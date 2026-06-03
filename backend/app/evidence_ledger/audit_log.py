from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Protocol
from uuid import UUID, uuid4

from app.domain.enums import EvidenceType


class EvidenceAuditEventType(StrEnum):
    CREATED = "created"
    SUPERSEDED = "superseded"


@dataclass(frozen=True)
class EvidenceAuditEvent:
    event_type: EvidenceAuditEventType
    evidence_id: UUID
    area_id: UUID
    source_id: UUID
    evidence_type: EvidenceType
    superseded_by: UUID | None = None
    event_id: UUID = field(default_factory=uuid4)
    recorded_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class EvidenceAuditLog(Protocol):
    def record(self, event: EvidenceAuditEvent) -> EvidenceAuditEvent: ...

    def list_by_evidence(self, evidence_id: UUID) -> list[EvidenceAuditEvent]: ...

    def list_all(self) -> list[EvidenceAuditEvent]: ...


class InMemoryEvidenceAuditLog:
    def __init__(self) -> None:
        self._events: list[EvidenceAuditEvent] = []

    def record(self, event: EvidenceAuditEvent) -> EvidenceAuditEvent:
        self._events.append(event)
        return event

    def list_by_evidence(self, evidence_id: UUID) -> list[EvidenceAuditEvent]:
        return [
            event
            for event in self._events
            if event.evidence_id == evidence_id
        ]

    def list_all(self) -> list[EvidenceAuditEvent]:
        return list(self._events)


__all__ = [
    "EvidenceAuditEvent",
    "EvidenceAuditEventType",
    "EvidenceAuditLog",
    "InMemoryEvidenceAuditLog",
]
