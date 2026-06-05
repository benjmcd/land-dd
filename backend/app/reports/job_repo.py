from __future__ import annotations

import json
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
                    not_before
                )
                VALUES (
                    :job_id,
                    :workspace_id,
                    :job_type,
                    :status,
                    CAST(:payload AS jsonb),
                    :idempotency_key,
                    1,
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


def _select_job_sql(where_clause: str) -> TextClause:
    return text(
        f"""
        SELECT
            job_id,
            workspace_id,
            job_type,
            status,
            payload,
            idempotency_key,
            created_at,
            not_before,
            started_at,
            finished_at,
            last_error
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
        started_at=row["started_at"],
        finished_at=row["finished_at"],
        last_error=row["last_error"],
    )


def _normalize_idempotency_key(idempotency_key: str) -> str:
    normalized = idempotency_key.strip()
    if not normalized:
        raise ValueError("idempotency_key is required")
    return normalized


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
