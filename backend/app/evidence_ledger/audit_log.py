from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Protocol
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

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


class SqlAlchemyEvidenceAuditLog:
    def __init__(self, session: Session) -> None:
        self._session = session

    def record(self, event: EvidenceAuditEvent) -> EvidenceAuditEvent:
        row = self._session.execute(
            text(
                """
                INSERT INTO audit.events (
                    audit_event_id,
                    event_type,
                    target_table,
                    target_id,
                    occurred_at,
                    payload
                )
                VALUES (
                    :event_id,
                    :event_type,
                    'evidence.observations',
                    :target_id,
                    :recorded_at,
                    CAST(:payload AS jsonb)
                )
                RETURNING
                    audit_event_id,
                    event_type,
                    target_id,
                    occurred_at,
                    payload
                """
            ),
            {
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "target_id": event.evidence_id,
                "recorded_at": event.recorded_at,
                "payload": json.dumps(_event_payload(event)),
            },
        ).mappings().one()
        self._session.flush()
        return _row_to_event(row)

    def list_by_evidence(self, evidence_id: UUID) -> list[EvidenceAuditEvent]:
        rows = self._session.execute(
            text(
                """
                SELECT
                    audit_event_id,
                    event_type,
                    target_id,
                    occurred_at,
                    payload
                FROM audit.events
                WHERE target_table = 'evidence.observations'
                    AND target_id = :evidence_id
                ORDER BY occurred_at, audit_event_id
                """
            ),
            {"evidence_id": evidence_id},
        ).mappings().all()
        return [_row_to_event(row) for row in rows]

    def list_all(self) -> list[EvidenceAuditEvent]:
        rows = self._session.execute(
            text(
                """
                SELECT
                    audit_event_id,
                    event_type,
                    target_id,
                    occurred_at,
                    payload
                FROM audit.events
                WHERE target_table = 'evidence.observations'
                ORDER BY occurred_at, audit_event_id
                """
            )
        ).mappings().all()
        return [_row_to_event(row) for row in rows]


def _event_payload(event: EvidenceAuditEvent) -> dict[str, object]:
    payload: dict[str, object] = {
        "area_id": str(event.area_id),
        "source_id": str(event.source_id),
        "evidence_type": event.evidence_type.value,
    }
    if event.superseded_by is not None:
        payload["superseded_by"] = str(event.superseded_by)
    return payload


def _row_to_event(row: Any) -> EvidenceAuditEvent:
    payload = _json_object(row["payload"], "payload")
    return EvidenceAuditEvent(
        event_type=EvidenceAuditEventType(row["event_type"]),
        evidence_id=row["target_id"],
        area_id=_payload_uuid(payload, "area_id"),
        source_id=_payload_uuid(payload, "source_id"),
        evidence_type=EvidenceType(_payload_str(payload, "evidence_type")),
        superseded_by=_optional_payload_uuid(payload, "superseded_by"),
        event_id=row["audit_event_id"],
        recorded_at=row["occurred_at"],
    )


def _payload_str(payload: dict[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"audit.events payload.{key} is required")
    return value


def _payload_uuid(payload: dict[str, object], key: str) -> UUID:
    return UUID(_payload_str(payload, key))


def _optional_payload_uuid(payload: dict[str, object], key: str) -> UUID | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ValueError(f"audit.events payload.{key} must be a UUID string")
    return UUID(value)


def _json_object(value: object, label: str) -> dict[str, object]:
    if isinstance(value, str):
        value = json.loads(value)
    if not isinstance(value, dict):
        raise ValueError(f"audit.events returned invalid {label}")
    return value


__all__ = [
    "EvidenceAuditEvent",
    "EvidenceAuditEventType",
    "EvidenceAuditLog",
    "InMemoryEvidenceAuditLog",
    "SqlAlchemyEvidenceAuditLog",
]
