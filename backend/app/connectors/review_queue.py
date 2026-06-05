from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
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
    not_before: datetime | None = None
    attempts: int = 0
    max_attempts: int = 1
    locked_by: str | None = None
    locked_at: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    last_error: str | None = None


class ConnectorReviewQueueRepository(Protocol):
    def enqueue_review_status(
        self,
        review_status: ConnectorRunReviewStatus,
    ) -> ConnectorReviewQueueItem: ...

    def get_by_ingest_run_id(
        self,
        ingest_run_id: UUID,
    ) -> ConnectorReviewQueueItem | None: ...

    def lease_next(self, *, worker_id: str) -> ConnectorReviewQueueItem | None: ...

    def mark_succeeded(self, job_id: UUID) -> ConnectorReviewQueueItem: ...

    def mark_failed(self, job_id: UUID, *, error: str) -> ConnectorReviewQueueItem: ...

    def requeue_failed(
        self,
        job_id: UUID,
        *,
        reason: str,
        not_before: datetime | None = None,
    ) -> ConnectorReviewQueueItem: ...

    def cancel(self, job_id: UUID, *, reason: str) -> ConnectorReviewQueueItem: ...

    def list_connector_runs(
        self,
        *,
        status: str | None = None,
        connector_name: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ConnectorReviewQueueItem]: ...


def _status_filter(status: str | None) -> str | None:
    if status is None:
        return None
    try:
        return JobStatus(status).value
    except ValueError as exc:
        raise ValueError("unsupported connector review queue status") from exc


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
            not_before=review_status.handoff.packet.started_at,
        )
        self._store[ingest_run_id] = item
        return item

    def get_by_ingest_run_id(
        self,
        ingest_run_id: UUID,
    ) -> ConnectorReviewQueueItem | None:
        return self._store.get(ingest_run_id)

    def lease_next(self, *, worker_id: str) -> ConnectorReviewQueueItem | None:
        worker_id = _require_worker_id(worker_id)
        leased_at = datetime.now(UTC)
        candidates = [
            item
            for item in self._store.values()
            if item.status in {JobStatus.NEEDS_REVIEW, JobStatus.QUEUED}
            and item.attempts < item.max_attempts
            and (item.not_before is None or item.not_before <= leased_at)
        ]
        if not candidates:
            return None
        selected = min(candidates, key=lambda item: (item.priority, item.created_at))
        leased = replace(
            selected,
            status=JobStatus.RUNNING,
            attempts=selected.attempts + 1,
            locked_by=worker_id,
            locked_at=leased_at,
            started_at=selected.started_at or leased_at,
        )
        self._store[leased.ingest_run_id] = leased
        return leased

    def mark_succeeded(self, job_id: UUID) -> ConnectorReviewQueueItem:
        item = self._get_running_job(job_id)
        finished = replace(
            item,
            status=JobStatus.SUCCEEDED,
            finished_at=datetime.now(UTC),
            last_error=None,
        )
        self._store[finished.ingest_run_id] = finished
        return finished

    def mark_failed(self, job_id: UUID, *, error: str) -> ConnectorReviewQueueItem:
        error = _require_error(error)
        item = self._get_running_job(job_id)
        failed = replace(
            item,
            status=JobStatus.FAILED,
            finished_at=datetime.now(UTC),
            last_error=error,
        )
        self._store[failed.ingest_run_id] = failed
        return failed

    def requeue_failed(
        self,
        job_id: UUID,
        *,
        reason: str,
        not_before: datetime | None = None,
    ) -> ConnectorReviewQueueItem:
        reason = _require_reason(reason)
        item = self._get_job(job_id)
        if item.status != JobStatus.FAILED:
            raise ValueError("connector review queue job is not failed")
        if item.attempts >= item.max_attempts:
            raise ValueError("connector review queue job has no retry attempts remaining")
        requeued = replace(
            item,
            status=JobStatus.QUEUED,
            not_before=not_before or datetime.now(UTC),
            locked_by=None,
            locked_at=None,
            finished_at=None,
            last_error=reason,
        )
        self._store[requeued.ingest_run_id] = requeued
        return requeued

    def cancel(self, job_id: UUID, *, reason: str) -> ConnectorReviewQueueItem:
        reason = _require_reason(reason)
        item = self._get_job(job_id)
        if item.status in {JobStatus.SUCCEEDED, JobStatus.CANCELLED}:
            raise ValueError("connector review queue job cannot be cancelled")
        cancelled = replace(
            item,
            status=JobStatus.CANCELLED,
            finished_at=datetime.now(UTC),
            last_error=reason,
        )
        self._store[cancelled.ingest_run_id] = cancelled
        return cancelled

    def list_connector_runs(
        self,
        *,
        status: str | None = None,
        connector_name: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ConnectorReviewQueueItem]:
        status_filter = _status_filter(status)
        items = list(self._store.values())
        if status_filter is not None:
            items = [i for i in items if i.status.value == status_filter]
        if connector_name is not None:
            items = [
                i
                for i in items
                if i.payload.get("connector_name") == connector_name
            ]
        items.sort(key=lambda i: (i.priority, i.created_at))
        return items[offset : offset + limit]

    def _get_running_job(self, job_id: UUID) -> ConnectorReviewQueueItem:
        item = self._get_job(job_id)
        if item.status != JobStatus.RUNNING:
            raise ValueError("connector review queue job is not running")
        return item

    def _get_job(self, job_id: UUID) -> ConnectorReviewQueueItem:
        for item in self._store.values():
            if item.job_id == job_id:
                return item
        raise ValueError("connector review queue job not found")


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
                    created_at,
                    not_before,
                    attempts,
                    max_attempts,
                    locked_by,
                    locked_at,
                    started_at,
                    finished_at,
                    last_error
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
        item = _item_from_row(row)
        if item.ingest_run_id != ingest_run_id:
            raise ValueError("connector review queue payload ingest_run_id mismatch")
        return item

    def lease_next(self, *, worker_id: str) -> ConnectorReviewQueueItem | None:
        worker_id = _require_worker_id(worker_id)
        row = self._session.execute(
            text(
                """
                WITH candidate AS (
                    SELECT job_id
                    FROM jobs.job_queue
                    WHERE job_type = :job_type
                      AND status IN (
                          CAST(:needs_review_status AS jobs.job_status),
                          CAST(:queued_status AS jobs.job_status)
                      )
                      AND not_before <= now()
                      AND attempts < max_attempts
                    ORDER BY priority ASC, created_at ASC
                    FOR UPDATE SKIP LOCKED
                    LIMIT 1
                )
                UPDATE jobs.job_queue AS queue
                SET
                    status = CAST(:running_status AS jobs.job_status),
                    attempts = queue.attempts + 1,
                    locked_by = :worker_id,
                    locked_at = now(),
                    started_at = COALESCE(queue.started_at, now())
                FROM candidate
                WHERE queue.job_id = candidate.job_id
                RETURNING
                    queue.job_id,
                    queue.job_type,
                    queue.status,
                    queue.priority,
                    queue.payload,
                    queue.idempotency_key,
                    queue.created_at,
                    queue.not_before,
                    queue.attempts,
                    queue.max_attempts,
                    queue.locked_by,
                    queue.locked_at,
                    queue.started_at,
                    queue.finished_at,
                    queue.last_error
                """
            ),
            {
                "job_type": CONNECTOR_REVIEW_STATUS_JOB_TYPE,
                "needs_review_status": JobStatus.NEEDS_REVIEW.value,
                "queued_status": JobStatus.QUEUED.value,
                "running_status": JobStatus.RUNNING.value,
                "worker_id": worker_id,
            },
        ).mappings().one_or_none()
        self._session.flush()
        if row is None:
            return None
        return _item_from_row(row)

    def mark_succeeded(self, job_id: UUID) -> ConnectorReviewQueueItem:
        return self._finish_job(
            job_id,
            status=JobStatus.SUCCEEDED,
            error=None,
        )

    def mark_failed(self, job_id: UUID, *, error: str) -> ConnectorReviewQueueItem:
        return self._finish_job(
            job_id,
            status=JobStatus.FAILED,
            error=_require_error(error),
        )

    def requeue_failed(
        self,
        job_id: UUID,
        *,
        reason: str,
        not_before: datetime | None = None,
    ) -> ConnectorReviewQueueItem:
        row = self._session.execute(
            text(
                """
                UPDATE jobs.job_queue
                SET
                    status = CAST(:queued_status AS jobs.job_status),
                    not_before = COALESCE(CAST(:not_before AS timestamptz), now()),
                    locked_by = NULL,
                    locked_at = NULL,
                    finished_at = NULL,
                    last_error = :last_error
                WHERE job_type = :job_type
                  AND job_id = :job_id
                  AND status = CAST(:failed_status AS jobs.job_status)
                  AND attempts < max_attempts
                RETURNING
                    job_id,
                    job_type,
                    status,
                    priority,
                    payload,
                    idempotency_key,
                    created_at,
                    not_before,
                    attempts,
                    max_attempts,
                    locked_by,
                    locked_at,
                    started_at,
                    finished_at,
                    last_error
                """
            ),
            {
                "queued_status": JobStatus.QUEUED.value,
                "not_before": not_before,
                "last_error": _require_reason(reason),
                "job_type": CONNECTOR_REVIEW_STATUS_JOB_TYPE,
                "job_id": str(job_id),
                "failed_status": JobStatus.FAILED.value,
            },
        ).mappings().one_or_none()
        self._session.flush()
        if row is None:
            raise ValueError(
                "connector review queue job is not failed or has no retry attempts remaining"
            )
        return _item_from_row(row)

    def cancel(self, job_id: UUID, *, reason: str) -> ConnectorReviewQueueItem:
        row = self._session.execute(
            text(
                """
                UPDATE jobs.job_queue
                SET
                    status = CAST(:cancelled_status AS jobs.job_status),
                    finished_at = now(),
                    last_error = :last_error
                WHERE job_type = :job_type
                  AND job_id = :job_id
                  AND status NOT IN (
                      CAST(:succeeded_status AS jobs.job_status),
                      CAST(:cancelled_status AS jobs.job_status)
                  )
                RETURNING
                    job_id,
                    job_type,
                    status,
                    priority,
                    payload,
                    idempotency_key,
                    created_at,
                    not_before,
                    attempts,
                    max_attempts,
                    locked_by,
                    locked_at,
                    started_at,
                    finished_at,
                    last_error
                """
            ),
            {
                "cancelled_status": JobStatus.CANCELLED.value,
                "last_error": _require_reason(reason),
                "job_type": CONNECTOR_REVIEW_STATUS_JOB_TYPE,
                "job_id": str(job_id),
                "succeeded_status": JobStatus.SUCCEEDED.value,
            },
        ).mappings().one_or_none()
        self._session.flush()
        if row is None:
            raise ValueError("connector review queue job cannot be cancelled")
        return _item_from_row(row)

    def list_connector_runs(
        self,
        *,
        status: str | None = None,
        connector_name: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ConnectorReviewQueueItem]:
        status_filter = _status_filter(status)
        rows = self._session.execute(
            text(
                """
                SELECT
                    job_id,
                    job_type,
                    status,
                    priority,
                    payload,
                    idempotency_key,
                    created_at,
                    not_before,
                    attempts,
                    max_attempts,
                    locked_by,
                    locked_at,
                    started_at,
                    finished_at,
                    last_error
                FROM jobs.job_queue
                WHERE job_type = :job_type
                  AND (
                      :status IS NULL
                      OR status = CAST(:status AS jobs.job_status)
                  )
                  AND (
                      :connector_name IS NULL
                      OR payload->>'connector_name' = :connector_name
                  )
                ORDER BY priority ASC, created_at ASC
                LIMIT :limit OFFSET :offset
                """
            ),
            {
                "job_type": CONNECTOR_REVIEW_STATUS_JOB_TYPE,
                "status": status_filter,
                "connector_name": connector_name,
                "limit": limit,
                "offset": offset,
            },
        ).mappings().all()
        return [_item_from_row(row) for row in rows]

    def _finish_job(
        self,
        job_id: UUID,
        *,
        status: JobStatus,
        error: str | None,
    ) -> ConnectorReviewQueueItem:
        row = self._session.execute(
            text(
                """
                UPDATE jobs.job_queue
                SET
                    status = CAST(:finished_status AS jobs.job_status),
                    finished_at = now(),
                    last_error = :last_error
                WHERE job_type = :job_type
                  AND job_id = :job_id
                  AND status = CAST(:running_status AS jobs.job_status)
                RETURNING
                    job_id,
                    job_type,
                    status,
                    priority,
                    payload,
                    idempotency_key,
                    created_at,
                    not_before,
                    attempts,
                    max_attempts,
                    locked_by,
                    locked_at,
                    started_at,
                    finished_at,
                    last_error
                """
            ),
            {
                "finished_status": status.value,
                "last_error": error,
                "job_type": CONNECTOR_REVIEW_STATUS_JOB_TYPE,
                "job_id": str(job_id),
                "running_status": JobStatus.RUNNING.value,
            },
        ).mappings().one_or_none()
        self._session.flush()
        if row is None:
            raise ValueError("connector review queue job is not running")
        return _item_from_row(row)


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


def _item_from_row(row: Any) -> ConnectorReviewQueueItem:
    payload = dict(row["payload"])
    return ConnectorReviewQueueItem(
        job_id=UUID(str(row["job_id"])),
        ingest_run_id=UUID(str(payload["ingest_run_id"])),
        job_type=str(row["job_type"]),
        status=JobStatus(str(row["status"])),
        priority=int(row["priority"]),
        idempotency_key=str(row["idempotency_key"]),
        payload=payload,
        created_at=row["created_at"],
        not_before=row["not_before"],
        attempts=int(row["attempts"]),
        max_attempts=int(row["max_attempts"]),
        locked_by=row["locked_by"],
        locked_at=row["locked_at"],
        started_at=row["started_at"],
        finished_at=row["finished_at"],
        last_error=row["last_error"],
    )


def _require_worker_id(worker_id: str) -> str:
    cleaned = worker_id.strip()
    if not cleaned:
        raise ValueError("connector review queue worker_id is required")
    return cleaned


def _require_error(error: str) -> str:
    cleaned = error.strip()
    if not cleaned:
        raise ValueError("connector review queue failure error is required")
    return cleaned


def _require_reason(reason: str) -> str:
    cleaned = reason.strip()
    if not cleaned:
        raise ValueError("connector review queue reason is required")
    return cleaned


__all__ = [
    "CONNECTOR_REVIEW_STATUS_JOB_TYPE",
    "ConnectorReviewQueueItem",
    "ConnectorReviewQueueRepository",
    "InMemoryConnectorReviewQueueRepository",
    "SqlAlchemyConnectorReviewQueueRepository",
]
