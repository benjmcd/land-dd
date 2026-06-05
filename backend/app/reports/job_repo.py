from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import TextClause

from app.domain.enums import IntentCode, JobStatus
from app.domain.report_contracts import ReportRunJobContract
from app.reports.scope import validate_scope_refs

REPORT_RUN_JOB_TYPE = "report_run"


class ReportRunJobRepository(Protocol):
    def enqueue(self, job: ReportRunJobContract) -> ReportRunJobContract: ...

    def get(self, job_id: UUID) -> ReportRunJobContract | None: ...

    def get_by_idempotency_key(
        self,
        idempotency_key: str,
        *,
        workspace_id: UUID | None = None,
    ) -> ReportRunJobContract | None: ...

    def lease_next(self, *, worker_id: str) -> ReportRunJobContract | None: ...

    def mark_succeeded(
        self,
        job_id: UUID,
        *,
        report_run_id: UUID,
    ) -> ReportRunJobContract: ...

    def mark_failed(self, job_id: UUID, *, error: str) -> ReportRunJobContract: ...

    def requeue_failed(self, job_id: UUID, *, reason: str) -> ReportRunJobContract: ...


class InMemoryReportRunJobRepository:
    def __init__(self) -> None:
        self._by_id: dict[UUID, ReportRunJobContract] = {}
        self._by_key: dict[str, UUID] = {}

    def enqueue(self, job: ReportRunJobContract) -> ReportRunJobContract:
        existing = self.get_by_idempotency_key(
            job.idempotency_key,
            workspace_id=job.workspace_id,
        )
        if existing is not None:
            return existing
        normalized_key = _normalize_idempotency_key(job.idempotency_key)
        stored = job.model_copy(
            update={
                "job_type": REPORT_RUN_JOB_TYPE,
                "status": JobStatus.QUEUED,
                "idempotency_key": normalized_key,
                "not_before": job.not_before or job.created_at,
            }
        )
        self._by_id[stored.job_id] = stored
        self._by_key[_storage_idempotency_key(stored.workspace_id, normalized_key)] = (
            stored.job_id
        )
        return stored

    def get(self, job_id: UUID) -> ReportRunJobContract | None:
        return self._by_id.get(job_id)

    def get_by_idempotency_key(
        self,
        idempotency_key: str,
        *,
        workspace_id: UUID | None = None,
    ) -> ReportRunJobContract | None:
        job_id = self._by_key.get(
            _storage_idempotency_key(
                workspace_id,
                _normalize_idempotency_key(idempotency_key),
            )
        )
        if job_id is None:
            return None
        return self.get(job_id)

    def lease_next(self, *, worker_id: str) -> ReportRunJobContract | None:
        worker_id = _require_worker_id(worker_id)
        leased_at = datetime.now(UTC)
        candidates = [
            job
            for job in self._by_id.values()
            if job.status == JobStatus.QUEUED
            and job.attempts < job.max_attempts
            and (job.not_before is None or job.not_before <= leased_at)
        ]
        if not candidates:
            return None
        selected = min(candidates, key=lambda job: (job.created_at, str(job.job_id)))
        leased = selected.model_copy(
            update={
                "status": JobStatus.RUNNING,
                "attempts": selected.attempts + 1,
                "locked_by": worker_id,
                "locked_at": leased_at,
                "started_at": selected.started_at or leased_at,
            }
        )
        self._by_id[leased.job_id] = leased
        return leased

    def mark_succeeded(
        self,
        job_id: UUID,
        *,
        report_run_id: UUID,
    ) -> ReportRunJobContract:
        job = self._get_running_job(job_id)
        finished = job.model_copy(
            update={
                "status": JobStatus.SUCCEEDED,
                "report_run_id": report_run_id,
                "locked_by": None,
                "locked_at": None,
                "finished_at": datetime.now(UTC),
                "last_error": None,
            }
        )
        self._by_id[job_id] = finished
        return finished

    def mark_failed(self, job_id: UUID, *, error: str) -> ReportRunJobContract:
        error = _require_error(error)
        job = self._get_running_job(job_id)
        failed = job.model_copy(
            update={
                "status": JobStatus.FAILED,
                "locked_by": None,
                "locked_at": None,
                "finished_at": datetime.now(UTC),
                "last_error": error,
            }
        )
        self._by_id[job_id] = failed
        return failed

    def requeue_failed(self, job_id: UUID, *, reason: str) -> ReportRunJobContract:
        reason = _require_error(reason)
        job = self.get(job_id)
        if job is None or job.status != JobStatus.FAILED:
            raise ValueError("report run job is not failed")
        if job.attempts >= job.max_attempts:
            raise ValueError("report run job has no retry attempts remaining")
        requeued = job.model_copy(
            update={
                "status": JobStatus.QUEUED,
                "not_before": datetime.now(UTC),
                "locked_by": None,
                "locked_at": None,
                "finished_at": None,
                "last_error": reason,
            }
        )
        self._by_id[job_id] = requeued
        return requeued

    def _get_running_job(self, job_id: UUID) -> ReportRunJobContract:
        job = self.get(job_id)
        if job is None or job.status != JobStatus.RUNNING:
            raise ValueError("report run job is not running")
        return job


class SqlAlchemyReportRunJobRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def enqueue(self, job: ReportRunJobContract) -> ReportRunJobContract:
        normalized_key = _normalize_idempotency_key(job.idempotency_key)
        storage_key = _storage_idempotency_key(job.workspace_id, normalized_key)
        existing = self.get_by_idempotency_key(
            normalized_key,
            workspace_id=job.workspace_id,
        )
        if existing is not None:
            return existing
        validate_scope_refs(
            self._session,
            workspace_id=job.workspace_id,
            requested_by=job.requested_by,
        )
        self._session.execute(
            text(
                """
                INSERT INTO jobs.job_queue (
                    job_id,
                    workspace_id,
                    job_type,
                    status,
                    payload,
                    idempotency_key,
                    max_attempts,
                    attempts,
                    not_before
                )
                VALUES (
                    :job_id,
                    :workspace_id,
                    :job_type,
                    :status,
                    CAST(:payload AS jsonb),
                    :idempotency_key,
                    :max_attempts,
                    :attempts,
                    :not_before
                )
                ON CONFLICT (idempotency_key) DO NOTHING
                """
            ),
            {
                "job_id": job.job_id,
                "workspace_id": job.workspace_id,
                "job_type": REPORT_RUN_JOB_TYPE,
                "status": JobStatus.QUEUED.value,
                "payload": _json_payload(job, idempotency_key=normalized_key),
                "idempotency_key": storage_key,
                "max_attempts": job.max_attempts,
                "attempts": job.attempts,
                "not_before": job.not_before or job.created_at,
            },
        )
        self._session.flush()
        queued = self.get_by_idempotency_key(
            normalized_key,
            workspace_id=job.workspace_id,
        )
        if queued is None:
            raise ValueError("report run job insert did not round-trip")
        return queued

    def get(self, job_id: UUID) -> ReportRunJobContract | None:
        row = self._session.execute(
            _select_job_sql("WHERE job_type = :job_type AND job_id = :job_id"),
            {"job_type": REPORT_RUN_JOB_TYPE, "job_id": job_id},
        ).mappings().one_or_none()
        if row is None:
            return None
        return _row_to_job(row)

    def lease_next(self, *, worker_id: str) -> ReportRunJobContract | None:
        worker_id = _require_worker_id(worker_id)
        row = self._session.execute(
            text(
                f"""
                WITH candidate AS (
                    SELECT job_id
                    FROM jobs.job_queue
                    WHERE job_type = :job_type
                      AND status = CAST(:queued_status AS jobs.job_status)
                      AND not_before <= now()
                      AND attempts < max_attempts
                    ORDER BY created_at ASC, job_id ASC
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
                RETURNING {_RETURNING_QUEUE_COLUMNS}
                """
            ),
            {
                "job_type": REPORT_RUN_JOB_TYPE,
                "queued_status": JobStatus.QUEUED.value,
                "running_status": JobStatus.RUNNING.value,
                "worker_id": worker_id,
            },
        ).mappings().one_or_none()
        self._session.flush()
        if row is None:
            return None
        return _row_to_job(row)

    def mark_succeeded(
        self,
        job_id: UUID,
        *,
        report_run_id: UUID,
    ) -> ReportRunJobContract:
        row = self._session.execute(
            text(
                f"""
                UPDATE jobs.job_queue AS queue
                SET
                    status = CAST(:succeeded_status AS jobs.job_status),
                    locked_by = NULL,
                    locked_at = NULL,
                    finished_at = now(),
                    last_error = NULL,
                    payload = jsonb_set(
                        payload,
                        '{{report_run_id}}',
                        to_jsonb(CAST(:report_run_id AS text)),
                        true
                    )
                WHERE queue.job_type = :job_type
                  AND queue.job_id = :job_id
                  AND queue.status = CAST(:running_status AS jobs.job_status)
                RETURNING {_RETURNING_QUEUE_COLUMNS}
                """
            ),
            {
                "succeeded_status": JobStatus.SUCCEEDED.value,
                "report_run_id": str(report_run_id),
                "job_type": REPORT_RUN_JOB_TYPE,
                "job_id": str(job_id),
                "running_status": JobStatus.RUNNING.value,
            },
        ).mappings().one_or_none()
        self._session.flush()
        if row is None:
            raise ValueError("report run job is not running")
        return _row_to_job(row)

    def mark_failed(self, job_id: UUID, *, error: str) -> ReportRunJobContract:
        error = _require_error(error)
        row = self._session.execute(
            text(
                f"""
                UPDATE jobs.job_queue AS queue
                SET
                    status = CAST(:failed_status AS jobs.job_status),
                    locked_by = NULL,
                    locked_at = NULL,
                    finished_at = now(),
                    last_error = :last_error
                WHERE queue.job_type = :job_type
                  AND queue.job_id = :job_id
                  AND queue.status = CAST(:running_status AS jobs.job_status)
                RETURNING {_RETURNING_QUEUE_COLUMNS}
                """
            ),
            {
                "failed_status": JobStatus.FAILED.value,
                "last_error": error,
                "job_type": REPORT_RUN_JOB_TYPE,
                "job_id": str(job_id),
                "running_status": JobStatus.RUNNING.value,
            },
        ).mappings().one_or_none()
        self._session.flush()
        if row is None:
            raise ValueError("report run job is not running")
        return _row_to_job(row)

    def requeue_failed(self, job_id: UUID, *, reason: str) -> ReportRunJobContract:
        reason = _require_error(reason)
        row = self._session.execute(
            text(
                f"""
                UPDATE jobs.job_queue AS queue
                SET
                    status = CAST(:queued_status AS jobs.job_status),
                    not_before = now(),
                    locked_by = NULL,
                    locked_at = NULL,
                    finished_at = NULL,
                    last_error = :last_error
                WHERE queue.job_type = :job_type
                  AND queue.job_id = :job_id
                  AND queue.status = CAST(:failed_status AS jobs.job_status)
                  AND queue.attempts < queue.max_attempts
                RETURNING {_RETURNING_QUEUE_COLUMNS}
                """
            ),
            {
                "queued_status": JobStatus.QUEUED.value,
                "last_error": reason,
                "job_type": REPORT_RUN_JOB_TYPE,
                "job_id": str(job_id),
                "failed_status": JobStatus.FAILED.value,
            },
        ).mappings().one_or_none()
        self._session.flush()
        if row is None:
            raise ValueError(
                "report run job is not failed or has no retry attempts remaining"
            )
        return _row_to_job(row)

    def get_by_idempotency_key(
        self,
        idempotency_key: str,
        *,
        workspace_id: UUID | None = None,
    ) -> ReportRunJobContract | None:
        row = self._session.execute(
            _select_job_sql(
                "WHERE job_type = :job_type AND idempotency_key = :idempotency_key"
            ),
            {
                "job_type": REPORT_RUN_JOB_TYPE,
                "idempotency_key": _storage_idempotency_key(
                    workspace_id,
                    _normalize_idempotency_key(idempotency_key),
                ),
            },
        ).mappings().one_or_none()
        if row is None:
            return None
        return _row_to_job(row)


_RETURNING_COLUMNS = """
job_id,
workspace_id,
job_type,
status,
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

_RETURNING_QUEUE_COLUMNS = """
queue.job_id,
queue.workspace_id,
queue.job_type,
queue.status,
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


def _select_job_sql(where_clause: str) -> TextClause:
    return text(
        f"""
        SELECT
            {_RETURNING_COLUMNS}
        FROM jobs.job_queue
        {where_clause}
        LIMIT 1
        """
    )


def _json_payload(job: ReportRunJobContract, *, idempotency_key: str) -> str:
    return json.dumps(
        {
            "area_id": str(job.area_id),
            "intent_code": job.intent_code.value,
            "idempotency_key": idempotency_key,
            "requested_by": str(job.requested_by) if job.requested_by is not None else None,
            "report_run_id": str(job.report_run_id)
            if job.report_run_id is not None
            else None,
        },
        sort_keys=True,
    )


def _row_to_job(row: Any) -> ReportRunJobContract:
    payload = row["payload"]
    if isinstance(payload, str):
        payload = json.loads(payload)
    if not isinstance(payload, dict):
        raise ValueError("report run job payload is not an object")
    return ReportRunJobContract(
        job_id=UUID(str(row["job_id"])),
        workspace_id=UUID(str(row["workspace_id"]))
        if row["workspace_id"] is not None
        else None,
        job_type=str(row["job_type"]),
        status=JobStatus(str(row["status"])),
        area_id=UUID(str(payload["area_id"])),
        intent_code=IntentCode(str(payload["intent_code"])),
        requested_by=UUID(str(payload["requested_by"]))
        if payload.get("requested_by") is not None
        else None,
        idempotency_key=str(payload["idempotency_key"]),
        report_run_id=UUID(str(payload["report_run_id"]))
        if payload.get("report_run_id") is not None
        else None,
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


def _normalize_idempotency_key(idempotency_key: str) -> str:
    normalized = idempotency_key.strip()
    if not normalized:
        raise ValueError("idempotency_key is required")
    return normalized


def _require_worker_id(worker_id: str) -> str:
    cleaned = worker_id.strip()
    if not cleaned:
        raise ValueError("report run job worker_id is required")
    return cleaned


def _require_error(error: str) -> str:
    cleaned = error.strip()
    if not cleaned:
        raise ValueError("error is required")
    return cleaned


def _storage_idempotency_key(
    workspace_id: UUID | None,
    idempotency_key: str,
) -> str:
    workspace_scope = str(workspace_id) if workspace_id is not None else "global"
    return f"{REPORT_RUN_JOB_TYPE}:{workspace_scope}:{idempotency_key}"


__all__ = [
    "InMemoryReportRunJobRepository",
    "REPORT_RUN_JOB_TYPE",
    "ReportRunJobRepository",
    "SqlAlchemyReportRunJobRepository",
]
