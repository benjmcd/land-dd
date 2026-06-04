from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.domain.enums import JobStatus

from .review_status import ConnectorRunReviewStatus

CONNECTOR_REVIEW_STATUS_JOB_TYPE = "connector_review_status"


@dataclass(frozen=True)
class ConnectorReviewQueueItem:
    job_id: UUID
    ingest_run_id: UUID
    job_type: str
    status: JobStatus
    priority: int
    idempotency_key: str
    payload: dict[str, Any]
    created_at: datetime


class ConnectorReviewQueueRepository(Protocol):
    def enqueue_review_status(
        self,
        review_status: ConnectorRunReviewStatus,
    ) -> ConnectorReviewQueueItem: ...

    def get_by_ingest_run_id(
        self,
        ingest_run_id: UUID,
    ) -> ConnectorReviewQueueItem | None: ...


class InMemoryConnectorReviewQueueRepository:
    def __init__(self) -> None:
        self._store: dict[UUID, ConnectorReviewQueueItem] = {}

    def enqueue_review_status(
        self,
        review_status: ConnectorRunReviewStatus,
    ) -> ConnectorReviewQueueItem:
        ingest_run_id = review_status.handoff.packet.ingest_run_id
        existing = self._store.get(ingest_run_id)
        if existing is not None:
            return existing
        item = ConnectorReviewQueueItem(
            job_id=ingest_run_id,
            ingest_run_id=ingest_run_id,
            job_type=CONNECTOR_REVIEW_STATUS_JOB_TYPE,
            status=JobStatus.NEEDS_REVIEW
            if review_status.review_required
            else JobStatus.QUEUED,
            priority=_priority(review_status),
            idempotency_key=_idempotency_key(ingest_run_id),
            payload=_payload(review_status),
            created_at=review_status.handoff.packet.started_at,
        )
        self._store[ingest_run_id] = item
        return item

    def get_by_ingest_run_id(
        self,
        ingest_run_id: UUID,
    ) -> ConnectorReviewQueueItem | None:
        return self._store.get(ingest_run_id)


class SqlAlchemyConnectorReviewQueueRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def enqueue_review_status(
        self,
        review_status: ConnectorRunReviewStatus,
    ) -> ConnectorReviewQueueItem:
        ingest_run_id = review_status.handoff.packet.ingest_run_id
        existing = self.get_by_ingest_run_id(ingest_run_id)
        if existing is not None:
            return existing
        self._session.execute(
            text(
                """
                INSERT INTO jobs.job_queue (
                    job_type,
                    status,
                    priority,
                    payload,
                    idempotency_key,
                    max_attempts
                )
                VALUES (
                    :job_type,
                    :status,
                    :priority,
                    CAST(:payload AS jsonb),
                    :idempotency_key,
                    1
                )
                """
            ),
            {
                "job_type": CONNECTOR_REVIEW_STATUS_JOB_TYPE,
                "status": (
                    JobStatus.NEEDS_REVIEW
                    if review_status.review_required
                    else JobStatus.QUEUED
                ).value,
                "priority": _priority(review_status),
                "payload": _json_payload(review_status),
                "idempotency_key": _idempotency_key(ingest_run_id),
            },
        )
        self._session.flush()
        queued = self.get_by_ingest_run_id(ingest_run_id)
        if queued is None:
            raise ValueError("connector review queue insert did not round-trip")
        return queued

    def get_by_ingest_run_id(
        self,
        ingest_run_id: UUID,
    ) -> ConnectorReviewQueueItem | None:
        row = self._session.execute(
            text(
                """
                SELECT
                    job_id,
                    job_type,
                    status,
                    priority,
                    payload,
                    idempotency_key,
                    created_at
                FROM jobs.job_queue
                WHERE job_type = :job_type
                  AND idempotency_key = :idempotency_key
                LIMIT 1
                """
            ),
            {
                "job_type": CONNECTOR_REVIEW_STATUS_JOB_TYPE,
                "idempotency_key": _idempotency_key(ingest_run_id),
            },
        ).mappings().one_or_none()
        if row is None:
            return None
        payload = dict(row["payload"])
        payload_ingest_run_id = UUID(str(payload["ingest_run_id"]))
        if payload_ingest_run_id != ingest_run_id:
            raise ValueError("connector review queue payload ingest_run_id mismatch")
        return ConnectorReviewQueueItem(
            job_id=UUID(str(row["job_id"])),
            ingest_run_id=payload_ingest_run_id,
            job_type=str(row["job_type"]),
            status=JobStatus(str(row["status"])),
            priority=int(row["priority"]),
            idempotency_key=str(row["idempotency_key"]),
            payload=payload,
            created_at=row["created_at"],
        )


def _priority(review_status: ConnectorRunReviewStatus) -> int:
    if review_status.review_required:
        return 10
    return 100


def _idempotency_key(ingest_run_id: UUID) -> str:
    return f"{CONNECTOR_REVIEW_STATUS_JOB_TYPE}:{ingest_run_id}"


def _payload(review_status: ConnectorRunReviewStatus) -> dict[str, Any]:
    record = review_status.to_status_record()
    return {
        "kind": CONNECTOR_REVIEW_STATUS_JOB_TYPE,
        "connector_name": record["connector_name"],
        "ingest_run_id": record["ingest_run_id"],
        "dataset_version_id": record["dataset_version_id"],
        "retrieval_status": record["retrieval_status"],
        "review_required": record["review_required"],
        "disposition": record["disposition"],
        "priority": record["priority"],
        "queue_name": record["queue_name"],
        "signal_codes": record["signal_codes"],
        "quality": record["quality"],
    }


def _json_payload(review_status: ConnectorRunReviewStatus) -> str:
    import json

    return json.dumps(_payload(review_status), sort_keys=True)


__all__ = [
    "CONNECTOR_REVIEW_STATUS_JOB_TYPE",
    "ConnectorReviewQueueItem",
    "ConnectorReviewQueueRepository",
    "InMemoryConnectorReviewQueueRepository",
    "SqlAlchemyConnectorReviewQueueRepository",
]
