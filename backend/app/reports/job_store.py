from __future__ import annotations

import json
import threading
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from app.db.engine import get_session_factory
from app.domain.enums import IntentCode, JobStatus
from app.domain.job_health import JobQueueHealth

REPORT_RUN_JOB_TYPE = "report_run"


@dataclass
class ReportJobRecord:
    report_run_id: UUID
    area_id: UUID
    intent_code: IntentCode
    status: JobStatus = JobStatus.QUEUED
    error_msg: str | None = None
    retry_of_report_run_id: UUID | None = None
    # client_idempotency_key is the caller-supplied Idempotency-Key header value
    # (stripped, non-empty). None means this job was created without a key.
    client_idempotency_key: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class AsyncReportJobStoreProtocol(Protocol):
    def create(
        self,
        *,
        area_id: UUID,
        intent_code: IntentCode,
        retry_of_report_run_id: UUID | None = None,
        client_idempotency_key: str | None = None,
    ) -> ReportJobRecord: ...

    def get_by_client_idempotency_key(
        self,
        client_idempotency_key: str,
        *,
        area_id: UUID,
        intent_code: IntentCode,
    ) -> ReportJobRecord | None:
        # area_id and intent_code are accepted for symmetry with the call-site
        # but the lookup is keyed solely by client_idempotency_key; callers are
        # responsible for payload-mismatch checks after the lookup returns.
        ...

    def get(self, report_run_id: UUID) -> ReportJobRecord | None: ...

    def mark_running(self, report_run_id: UUID) -> None: ...

    def mark_succeeded(self, report_run_id: UUID) -> None: ...

    def mark_failed(self, report_run_id: UUID, *, error_msg: str) -> None: ...

    def health(self) -> JobQueueHealth: ...

    def list_recent(
        self,
        limit: int = 50,
        offset: int = 0,
        status: JobStatus | None = None,
    ) -> list[ReportJobRecord]: ...


class AsyncReportJobStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jobs: dict[UUID, ReportJobRecord] = {}
        # Maps storage_client_key -> report_run_id for idempotency dedup
        self._client_keys: dict[str, UUID] = {}

    def create(
        self,
        *,
        area_id: UUID,
        intent_code: IntentCode,
        retry_of_report_run_id: UUID | None = None,
        client_idempotency_key: str | None = None,
    ) -> ReportJobRecord:
        with self._lock:
            if client_idempotency_key is not None:
                storage_key = _client_storage_key(client_idempotency_key)
                existing_id = self._client_keys.get(storage_key)
                if existing_id is not None:
                    existing = self._jobs.get(existing_id)
                    if existing is not None:
                        return existing
            record = ReportJobRecord(
                report_run_id=uuid4(),
                area_id=area_id,
                intent_code=intent_code,
                retry_of_report_run_id=retry_of_report_run_id,
                client_idempotency_key=client_idempotency_key,
            )
            self._jobs[record.report_run_id] = record
            if client_idempotency_key is not None:
                storage_key = _client_storage_key(client_idempotency_key)
                self._client_keys[storage_key] = record.report_run_id
        return record

    def get_by_client_idempotency_key(
        self,
        client_idempotency_key: str,
        *,
        area_id: UUID,
        intent_code: IntentCode,
    ) -> ReportJobRecord | None:
        storage_key = _client_storage_key(client_idempotency_key)
        with self._lock:
            job_id = self._client_keys.get(storage_key)
            if job_id is None:
                return None
            return self._jobs.get(job_id)

    def get(self, report_run_id: UUID) -> ReportJobRecord | None:
        with self._lock:
            return self._jobs.get(report_run_id)

    def mark_running(self, report_run_id: UUID) -> None:
        with self._lock:
            record = self._jobs.get(report_run_id)
            if record is not None:
                record.status = JobStatus.RUNNING

    def mark_succeeded(self, report_run_id: UUID) -> None:
        with self._lock:
            record = self._jobs.get(report_run_id)
            if record is not None:
                record.status = JobStatus.SUCCEEDED

    def mark_failed(self, report_run_id: UUID, *, error_msg: str) -> None:
        with self._lock:
            record = self._jobs.get(report_run_id)
            if record is not None:
                record.status = JobStatus.FAILED
                record.error_msg = error_msg

    def health(self) -> JobQueueHealth:
        with self._lock:
            return _health_from_records(REPORT_RUN_JOB_TYPE, tuple(self._jobs.values()))

    def list_recent(
        self,
        limit: int = 50,
        offset: int = 0,
        status: JobStatus | None = None,
    ) -> list[ReportJobRecord]:
        with self._lock:
            jobs = sorted(self._jobs.values(), key=lambda r: r.created_at, reverse=True)
            if status is not None:
                jobs = [r for r in jobs if r.status == status]
            return jobs[offset : offset + limit]


class SqlAlchemyAsyncReportJobStore:
    def __init__(
        self,
        session_factory: sessionmaker[Session] | None = None,
    ) -> None:
        self._session_factory = session_factory or get_session_factory()

    def create(
        self,
        *,
        area_id: UUID,
        intent_code: IntentCode,
        retry_of_report_run_id: UUID | None = None,
        client_idempotency_key: str | None = None,
    ) -> ReportJobRecord:
        # For client-keyed requests: check for existing job first (durable dedup).
        if client_idempotency_key is not None:
            existing = self.get_by_client_idempotency_key(
                client_idempotency_key,
                area_id=area_id,
                intent_code=intent_code,
            )
            if existing is not None:
                return existing
        record = ReportJobRecord(
            report_run_id=uuid4(),
            area_id=area_id,
            intent_code=intent_code,
            retry_of_report_run_id=retry_of_report_run_id,
            client_idempotency_key=client_idempotency_key,
        )
        db_idem_key = (
            _client_storage_key(client_idempotency_key)
            if client_idempotency_key is not None
            else _idempotency_key(record.report_run_id)
        )
        with self._session_factory() as session:
            session.execute(
                text(
                    """
                    INSERT INTO jobs.job_queue (
                        job_id,
                        job_type,
                        status,
                        payload,
                        idempotency_key,
                        max_attempts
                    )
                    VALUES (
                        :job_id,
                        :job_type,
                        CAST(:status AS jobs.job_status),
                        CAST(:payload AS jsonb),
                        :idempotency_key,
                        1
                    )
                    ON CONFLICT (idempotency_key) DO NOTHING
                    """
                ),
                {
                    "job_id": str(record.report_run_id),
                    "job_type": REPORT_RUN_JOB_TYPE,
                    "status": record.status.value,
                    "payload": _json_payload(record),
                    "idempotency_key": db_idem_key,
                },
            )
            session.commit()
        # If ON CONFLICT suppressed the insert (race), return the winner row.
        if client_idempotency_key is not None:
            winner = self.get_by_client_idempotency_key(
                client_idempotency_key,
                area_id=area_id,
                intent_code=intent_code,
            )
            if winner is not None:
                return winner
        return record

    def get_by_client_idempotency_key(
        self,
        client_idempotency_key: str,
        *,
        area_id: UUID,
        intent_code: IntentCode,
    ) -> ReportJobRecord | None:
        storage_key = _client_storage_key(client_idempotency_key)
        with self._session_factory() as session:
            row = session.execute(
                text(
                    """
                    SELECT job_id, status, payload, last_error, created_at
                    FROM jobs.job_queue
                    WHERE job_type = :job_type
                      AND idempotency_key = :idempotency_key
                    LIMIT 1
                    """
                ),
                {
                    "job_type": REPORT_RUN_JOB_TYPE,
                    "idempotency_key": storage_key,
                },
            ).mappings().one_or_none()
        if row is None:
            return None
        return _record_from_row(row)

    def get(self, report_run_id: UUID) -> ReportJobRecord | None:
        with self._session_factory() as session:
            row = session.execute(
                text(
                    """
                    SELECT job_id, status, payload, last_error, created_at
                    FROM jobs.job_queue
                    WHERE job_type = :job_type
                      AND job_id = :job_id
                    LIMIT 1
                    """
                ),
                {
                    "job_type": REPORT_RUN_JOB_TYPE,
                    "job_id": str(report_run_id),
                },
            ).mappings().one_or_none()
        if row is None:
            return None
        return _record_from_row(row)

    def mark_running(self, report_run_id: UUID) -> None:
        self._update_status(
            report_run_id,
            status=JobStatus.RUNNING,
            started=True,
            error_msg=None,
        )

    def mark_succeeded(self, report_run_id: UUID) -> None:
        self._update_status(
            report_run_id,
            status=JobStatus.SUCCEEDED,
            finished=True,
            error_msg=None,
        )

    def mark_failed(self, report_run_id: UUID, *, error_msg: str) -> None:
        self._update_status(
            report_run_id,
            status=JobStatus.FAILED,
            finished=True,
            error_msg=error_msg,
        )

    def list_recent(
        self,
        limit: int = 50,
        offset: int = 0,
        status: JobStatus | None = None,
    ) -> list[ReportJobRecord]:
        params: dict[str, object] = {
            "job_type": REPORT_RUN_JOB_TYPE,
            "limit": limit,
            "offset": offset,
        }
        if status is not None:
            params["status"] = status.value
            sql = """
                SELECT job_id, status, payload, last_error, created_at
                FROM jobs.job_queue
                WHERE job_type = :job_type
                  AND status = CAST(:status AS jobs.job_status)
                ORDER BY created_at DESC
                LIMIT :limit
                OFFSET :offset
                """
        else:
            sql = """
                SELECT job_id, status, payload, last_error, created_at
                FROM jobs.job_queue
                WHERE job_type = :job_type
                ORDER BY created_at DESC
                LIMIT :limit
                OFFSET :offset
                """
        with self._session_factory() as session:
            rows = session.execute(text(sql), params).mappings().all()
        return [_record_from_row(row) for row in rows]

    def health(self) -> JobQueueHealth:
        with self._session_factory() as session:
            row = session.execute(
                text(
                    """
                    SELECT
                        count(*) AS total,
                        count(*) FILTER (
                            WHERE status = CAST(:queued_status AS jobs.job_status)
                        ) AS queued,
                        count(*) FILTER (
                            WHERE status = CAST(:running_status AS jobs.job_status)
                        ) AS running,
                        count(*) FILTER (
                            WHERE status = CAST(:succeeded_status AS jobs.job_status)
                        ) AS succeeded,
                        count(*) FILTER (
                            WHERE status = CAST(:failed_status AS jobs.job_status)
                        ) AS failed,
                        count(*) FILTER (
                            WHERE status = CAST(:cancelled_status AS jobs.job_status)
                        ) AS cancelled,
                        count(*) FILTER (
                            WHERE status = CAST(:needs_review_status AS jobs.job_status)
                        ) AS needs_review,
                        min(created_at) FILTER (
                            WHERE status = CAST(:queued_status AS jobs.job_status)
                        ) AS oldest_queued_at
                    FROM jobs.job_queue
                    WHERE job_type = :job_type
                    """
                ),
                _health_query_params(REPORT_RUN_JOB_TYPE),
            ).mappings().one()
        return _health_from_row(REPORT_RUN_JOB_TYPE, row)

    def _update_status(
        self,
        report_run_id: UUID,
        *,
        status: JobStatus,
        started: bool = False,
        finished: bool = False,
        error_msg: str | None,
    ) -> None:
        statement = text(
            """
            UPDATE jobs.job_queue
            SET
                status = CAST(:status AS jobs.job_status),
                last_error = :last_error
            WHERE job_type = :job_type
              AND job_id = :job_id
            """
        )
        if started:
            statement = text(
                """
                UPDATE jobs.job_queue
                SET
                    status = CAST(:status AS jobs.job_status),
                    started_at = COALESCE(started_at, now()),
                    attempts = attempts + 1,
                    last_error = :last_error
                WHERE job_type = :job_type
                  AND job_id = :job_id
                """
            )
        if finished:
            statement = text(
                """
                UPDATE jobs.job_queue
                SET
                    status = CAST(:status AS jobs.job_status),
                    finished_at = now(),
                    last_error = :last_error
                WHERE job_type = :job_type
                  AND job_id = :job_id
                """
            )
        with self._session_factory() as session:
            session.execute(
                statement,
                {
                    "status": status.value,
                    "last_error": error_msg,
                    "job_type": REPORT_RUN_JOB_TYPE,
                    "job_id": str(report_run_id),
                },
            )
            session.commit()


def _payload(record: ReportJobRecord) -> dict[str, str | None]:
    payload: dict[str, str | None] = {
        "kind": REPORT_RUN_JOB_TYPE,
        "report_run_id": str(record.report_run_id),
        "area_id": str(record.area_id),
        "intent_code": record.intent_code.value,
    }
    if record.retry_of_report_run_id is not None:
        payload["retry_of_report_run_id"] = str(record.retry_of_report_run_id)
    if record.client_idempotency_key is not None:
        payload["client_idempotency_key"] = record.client_idempotency_key
    return payload


def _json_payload(record: ReportJobRecord) -> str:
    return json.dumps(_payload(record), sort_keys=True)


def _idempotency_key(report_run_id: UUID) -> str:
    return f"{REPORT_RUN_JOB_TYPE}:{report_run_id}"


def _client_storage_key(client_idempotency_key: str) -> str:
    """Storage key for a caller-supplied Idempotency-Key header value."""
    return f"{REPORT_RUN_JOB_TYPE}:client:{client_idempotency_key}"


def _record_from_row(row: Any) -> ReportJobRecord:
    payload = dict(row["payload"]) if isinstance(row["payload"], Mapping) else {}
    return ReportJobRecord(
        report_run_id=UUID(str(row["job_id"])),
        area_id=UUID(str(payload["area_id"])),
        intent_code=IntentCode(str(payload["intent_code"])),
        status=JobStatus(str(row["status"])),
        error_msg=None if row["last_error"] is None else str(row["last_error"]),
        retry_of_report_run_id=_optional_payload_uuid(payload, "retry_of_report_run_id"),
        client_idempotency_key=payload.get("client_idempotency_key"),
        created_at=row["created_at"],
    )


def _optional_payload_uuid(payload: dict[str, Any], key: str) -> UUID | None:
    value = payload.get(key)
    if value is None:
        return None
    return UUID(str(value))


def _health_from_records(
    job_type: str,
    records: tuple[ReportJobRecord, ...],
) -> JobQueueHealth:
    counts = {status: 0 for status in JobStatus}
    queued_created_at: list[datetime] = []
    for record in records:
        counts[record.status] += 1
        if record.status == JobStatus.QUEUED:
            queued_created_at.append(record.created_at)
    oldest_queued_at = min(queued_created_at) if queued_created_at else None
    return JobQueueHealth(
        job_type=job_type,
        total=len(records),
        queued=counts[JobStatus.QUEUED],
        running=counts[JobStatus.RUNNING],
        succeeded=counts[JobStatus.SUCCEEDED],
        failed=counts[JobStatus.FAILED],
        cancelled=counts[JobStatus.CANCELLED],
        needs_review=counts[JobStatus.NEEDS_REVIEW],
        oldest_queued_age_seconds=_age_seconds(oldest_queued_at),
    )


def _health_query_params(job_type: str) -> dict[str, str]:
    return {
        "job_type": job_type,
        "queued_status": JobStatus.QUEUED.value,
        "running_status": JobStatus.RUNNING.value,
        "succeeded_status": JobStatus.SUCCEEDED.value,
        "failed_status": JobStatus.FAILED.value,
        "cancelled_status": JobStatus.CANCELLED.value,
        "needs_review_status": JobStatus.NEEDS_REVIEW.value,
    }


def _health_from_row(job_type: str, row: Any) -> JobQueueHealth:
    return JobQueueHealth(
        job_type=job_type,
        total=int(row["total"]),
        queued=int(row["queued"]),
        running=int(row["running"]),
        succeeded=int(row["succeeded"]),
        failed=int(row["failed"]),
        cancelled=int(row["cancelled"]),
        needs_review=int(row["needs_review"]),
        oldest_queued_age_seconds=_age_seconds(row["oldest_queued_at"]),
    )


def _age_seconds(created_at: datetime | None) -> float | None:
    if created_at is None:
        return None
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=UTC)
    return max(0.0, (datetime.now(UTC) - created_at).total_seconds())


__all__ = [
    "AsyncReportJobStore",
    "AsyncReportJobStoreProtocol",
    "REPORT_RUN_JOB_TYPE",
    "ReportJobRecord",
    "SqlAlchemyAsyncReportJobStore",
]
