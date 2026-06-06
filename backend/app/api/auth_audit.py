from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from ipaddress import ip_address
from typing import Any, Protocol
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker


class ApiKeyAuthAuditOutcome(StrEnum):
    ACCEPTED = "accepted"
    INVALID = "invalid"
    MISSING = "missing"
    UNCONFIGURED = "unconfigured"


@dataclass(frozen=True)
class ApiKeyAuthAuditEvent:
    outcome: ApiKeyAuthAuditOutcome
    status_code: int
    method: str
    path: str
    key_id: str | None = None
    source: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    event_id: UUID = field(default_factory=uuid4)
    recorded_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class ApiKeyAuthAuditLog(Protocol):
    def record(self, event: ApiKeyAuthAuditEvent) -> ApiKeyAuthAuditEvent: ...


class InMemoryApiKeyAuthAuditLog:
    def __init__(self) -> None:
        self._events: list[ApiKeyAuthAuditEvent] = []

    def record(self, event: ApiKeyAuthAuditEvent) -> ApiKeyAuthAuditEvent:
        self._events.append(event)
        return event

    def list_all(self) -> list[ApiKeyAuthAuditEvent]:
        return list(self._events)


class SqlAlchemyApiKeyAuthAuditLog:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def record(self, event: ApiKeyAuthAuditEvent) -> ApiKeyAuthAuditEvent:
        with self._session_factory() as session:
            row = _insert_event(session, event)
            session.commit()
        return _row_to_event(row)

    def list_all(self) -> list[ApiKeyAuthAuditEvent]:
        with self._session_factory() as session:
            rows = session.execute(
                text(
                    """
                    SELECT
                        audit_event_id,
                        event_type,
                        occurred_at,
                        host(ip_address) AS ip_address,
                        user_agent,
                        payload
                    FROM audit.events
                    WHERE event_type = 'api_key_auth'
                    ORDER BY occurred_at, audit_event_id
                    """
                )
            ).mappings().all()
        return [_row_to_event(row) for row in rows]


def _insert_event(session: Session, event: ApiKeyAuthAuditEvent) -> Any:
    return session.execute(
        text(
            """
            INSERT INTO audit.events (
                audit_event_id,
                event_type,
                target_table,
                occurred_at,
                ip_address,
                user_agent,
                payload
            )
            VALUES (
                :event_id,
                'api_key_auth',
                'api.api_key_auth',
                :recorded_at,
                CAST(:ip_address AS inet),
                :user_agent,
                CAST(:payload AS jsonb)
            )
            RETURNING
                audit_event_id,
                event_type,
                occurred_at,
                host(ip_address) AS ip_address,
                user_agent,
                payload
            """
        ),
        {
            "event_id": event.event_id,
            "recorded_at": event.recorded_at,
            "ip_address": _valid_ip_or_none(event.ip_address),
            "user_agent": event.user_agent,
            "payload": json.dumps(_event_payload(event)),
        },
    ).mappings().one()


def _event_payload(event: ApiKeyAuthAuditEvent) -> dict[str, object]:
    return {
        "outcome": event.outcome.value,
        "status_code": event.status_code,
        "api_key_id": event.key_id,
        "api_key_source": event.source,
        "method": event.method,
        "path": event.path,
    }


def _row_to_event(row: Any) -> ApiKeyAuthAuditEvent:
    if row["event_type"] != "api_key_auth":
        raise ValueError("audit.events row is not an API-key auth event")
    payload = _json_object(row["payload"], "payload")
    return ApiKeyAuthAuditEvent(
        outcome=ApiKeyAuthAuditOutcome(_payload_str(payload, "outcome")),
        status_code=_payload_int(payload, "status_code"),
        method=_payload_str(payload, "method"),
        path=_payload_str(payload, "path"),
        key_id=_optional_payload_str(payload, "api_key_id"),
        source=_optional_payload_str(payload, "api_key_source"),
        ip_address=row["ip_address"],
        user_agent=row["user_agent"],
        event_id=row["audit_event_id"],
        recorded_at=row["occurred_at"],
    )


def _valid_ip_or_none(value: str | None) -> str | None:
    if value is None:
        return None
    try:
        return str(ip_address(value))
    except ValueError:
        return None


def _payload_str(payload: dict[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"audit.events payload.{key} is required")
    return value


def _optional_payload_str(payload: dict[str, object], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ValueError(f"audit.events payload.{key} must be a string")
    return value


def _payload_int(payload: dict[str, object], key: str) -> int:
    value = payload.get(key)
    if not isinstance(value, int):
        raise ValueError(f"audit.events payload.{key} must be an integer")
    return value


def _json_object(value: object, label: str) -> dict[str, object]:
    if isinstance(value, str):
        value = json.loads(value)
    if not isinstance(value, dict):
        raise ValueError(f"audit.events returned invalid {label}")
    return value


__all__ = [
    "ApiKeyAuthAuditEvent",
    "ApiKeyAuthAuditLog",
    "ApiKeyAuthAuditOutcome",
    "InMemoryApiKeyAuthAuditLog",
    "SqlAlchemyApiKeyAuthAuditLog",
]
