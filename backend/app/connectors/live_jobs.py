from __future__ import annotations

import json
import threading
from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.connectors.fema_nfhl import (
    FEMA_NFHL_CONNECTOR_NAME,
    FEMA_NFHL_MAX_FEATURES,
    FemaNfhlBbox,
)
from app.connectors.nwi import NWI_CONNECTOR_NAME, NWI_MAX_FEATURES, NwiBbox
from app.connectors.ssurgo import SSURGO_CONNECTOR_NAME, SSURGO_MAX_ROWS, SsurgoBbox
from app.connectors.usgs_tnm import (
    USGS_TNM_CONNECTOR_NAME,
    USGS_TNM_MAX_SAMPLE_POINTS,
    UsgsTnmBbox,
)
from app.domain.enums import JobStatus
from app.domain.job_health import STALE_RUNNING_THRESHOLD_SECONDS, JobQueueHealth

LIVE_CONNECTOR_JOB_TYPE = "live_connector_run"
LIVE_CONNECTOR_DS001_ID = "DS-001"
LIVE_CONNECTOR_DS002_ID = "DS-002"
LIVE_CONNECTOR_DS003_ID = "DS-003"
LIVE_CONNECTOR_DS004_ID = "DS-004"
LiveConnectorBbox = UsgsTnmBbox | FemaNfhlBbox | SsurgoBbox | NwiBbox


@dataclass(frozen=True)
class LiveConnectorJobRecord:
    job_id: UUID
    area_id: UUID
    source_registry_id: str
    connector_name: str
    status: JobStatus
    priority: int
    idempotency_key: str
    payload: dict[str, Any]
    created_at: datetime
    max_features: int
    bbox: LiveConnectorBbox | None = None
    connector_ingest_run_id: UUID | None = None
    connector_review_status: str | None = None
    request_url: str | None = None
    not_before: datetime | None = None
    attempts: int = 0
    max_attempts: int = 1
    locked_by: str | None = None
    locked_at: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    last_error: str | None = None


class LiveConnectorJobStoreProtocol(Protocol):
    def enqueue_usgs_tnm(
        self,
        *,
        area_id: UUID,
        bbox: UsgsTnmBbox | None = None,
        max_sample_points: int = USGS_TNM_MAX_SAMPLE_POINTS,
    ) -> LiveConnectorJobRecord: ...

    def enqueue_fema_nfhl(
        self,
        *,
        area_id: UUID,
        bbox: FemaNfhlBbox | None = None,
        max_features: int = FEMA_NFHL_MAX_FEATURES,
    ) -> LiveConnectorJobRecord: ...

    def enqueue_nwi(
        self,
        *,
        area_id: UUID,
        bbox: NwiBbox | None = None,
        max_features: int = NWI_MAX_FEATURES,
    ) -> LiveConnectorJobRecord: ...

    def enqueue_ssurgo(
        self,
        *,
        area_id: UUID,
        bbox: SsurgoBbox | None = None,
        max_rows: int = SSURGO_MAX_ROWS,
    ) -> LiveConnectorJobRecord: ...

    def get(self, job_id: UUID) -> LiveConnectorJobRecord | None: ...

    def list_recent(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        status: JobStatus | None = None,
        stale: bool = False,
    ) -> list[LiveConnectorJobRecord]: ...

    def lease_next(self, *, worker_id: str) -> LiveConnectorJobRecord | None: ...

    def mark_succeeded(
        self,
        job_id: UUID,
        *,
        connector_ingest_run_id: UUID,
        connector_review_status: str,
        request_url: str,
    ) -> LiveConnectorJobRecord: ...

    def mark_failed(self, job_id: UUID, *, error_msg: str) -> LiveConnectorJobRecord: ...

    def health(self) -> JobQueueHealth: ...


class InMemoryLiveConnectorJobStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jobs: dict[UUID, LiveConnectorJobRecord] = {}
        self._idempotency_index: dict[str, UUID] = {}

    def enqueue_usgs_tnm(
        self,
        *,
        area_id: UUID,
        bbox: UsgsTnmBbox | None = None,
        max_sample_points: int = USGS_TNM_MAX_SAMPLE_POINTS,
    ) -> LiveConnectorJobRecord:
        return self._enqueue(
            area_id=area_id,
            source_registry_id=LIVE_CONNECTOR_DS001_ID,
            connector_name=USGS_TNM_CONNECTOR_NAME,
            bbox=bbox,
            max_features=max_sample_points,
            max_allowed_features=USGS_TNM_MAX_SAMPLE_POINTS,
        )

    def enqueue_fema_nfhl(
        self,
        *,
        area_id: UUID,
        bbox: FemaNfhlBbox | None = None,
        max_features: int = FEMA_NFHL_MAX_FEATURES,
    ) -> LiveConnectorJobRecord:
        return self._enqueue(
            area_id=area_id,
            source_registry_id=LIVE_CONNECTOR_DS002_ID,
            connector_name=FEMA_NFHL_CONNECTOR_NAME,
            bbox=bbox,
            max_features=max_features,
            max_allowed_features=FEMA_NFHL_MAX_FEATURES,
        )

    def enqueue_nwi(
        self,
        *,
        area_id: UUID,
        bbox: NwiBbox | None = None,
        max_features: int = NWI_MAX_FEATURES,
    ) -> LiveConnectorJobRecord:
        return self._enqueue(
            area_id=area_id,
            source_registry_id=LIVE_CONNECTOR_DS004_ID,
            connector_name=NWI_CONNECTOR_NAME,
            bbox=bbox,
            max_features=max_features,
            max_allowed_features=NWI_MAX_FEATURES,
        )

    def enqueue_ssurgo(
        self,
        *,
        area_id: UUID,
        bbox: SsurgoBbox | None = None,
        max_rows: int = SSURGO_MAX_ROWS,
    ) -> LiveConnectorJobRecord:
        return self._enqueue(
            area_id=area_id,
            source_registry_id=LIVE_CONNECTOR_DS003_ID,
            connector_name=SSURGO_CONNECTOR_NAME,
            bbox=bbox,
            max_features=max_rows,
            max_allowed_features=SSURGO_MAX_ROWS,
        )

    def _enqueue(
        self,
        *,
        area_id: UUID,
        source_registry_id: str,
        connector_name: str,
        bbox: LiveConnectorBbox | None,
        max_features: int,
        max_allowed_features: int,
    ) -> LiveConnectorJobRecord:
        max_features = _require_max_features(max_features, max_allowed_features)
        idempotency_key = _idempotency_key(
            source_registry_id=source_registry_id,
            area_id=area_id,
            bbox=bbox,
            max_features=max_features,
        )
        now = datetime.now(UTC)
        with self._lock:
            existing_id = self._idempotency_index.get(idempotency_key)
            if existing_id is not None:
                return self._jobs[existing_id]
            record = LiveConnectorJobRecord(
                job_id=_stable_job_id(idempotency_key),
                area_id=area_id,
                source_registry_id=source_registry_id,
                connector_name=connector_name,
                status=JobStatus.QUEUED,
                priority=40,
                idempotency_key=idempotency_key,
                payload=_payload(
                    source_registry_id=source_registry_id,
                    connector_name=connector_name,
                    area_id=area_id,
                    bbox=bbox,
                    max_features=max_features,
                ),
                created_at=now,
                max_features=max_features,
                bbox=bbox,
                not_before=now,
            )
            self._jobs[record.job_id] = record
            self._idempotency_index[idempotency_key] = record.job_id
            return record

    def get(self, job_id: UUID) -> LiveConnectorJobRecord | None:
        with self._lock:
            return self._jobs.get(job_id)

    def list_recent(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        status: JobStatus | None = None,
        stale: bool = False,
    ) -> list[LiveConnectorJobRecord]:
        with self._lock:
            jobs = sorted(self._jobs.values(), key=lambda job: job.created_at, reverse=True)
            if status is not None:
                jobs = [job for job in jobs if job.status == status]
            if stale:
                jobs = [job for job in jobs if _is_stale_running(job)]
            return jobs[offset : offset + limit]

    def lease_next(self, *, worker_id: str) -> LiveConnectorJobRecord | None:
        worker_id = _require_worker_id(worker_id)
        now = datetime.now(UTC)
        with self._lock:
            candidates = [
                job
                for job in self._jobs.values()
                if job.status == JobStatus.QUEUED
                and job.attempts < job.max_attempts
                and (job.not_before is None or job.not_before <= now)
            ]
            if not candidates:
                return None
            selected = min(candidates, key=lambda job: (job.priority, job.created_at))
            leased = replace(
                selected,
                status=JobStatus.RUNNING,
                attempts=selected.attempts + 1,
                locked_by=worker_id,
                locked_at=now,
                started_at=selected.started_at or now,
            )
            self._jobs[leased.job_id] = leased
            return leased

    def mark_succeeded(
        self,
        job_id: UUID,
        *,
        connector_ingest_run_id: UUID,
        connector_review_status: str,
        request_url: str,
    ) -> LiveConnectorJobRecord:
        job = self._get_running_job(job_id)
        finished = replace(
            job,
            status=JobStatus.SUCCEEDED,
            connector_ingest_run_id=connector_ingest_run_id,
            connector_review_status=connector_review_status,
            request_url=request_url,
            payload=_payload_with_result(
                job.payload,
                connector_ingest_run_id=connector_ingest_run_id,
                connector_review_status=connector_review_status,
                request_url=request_url,
            ),
            finished_at=datetime.now(UTC),
            last_error=None,
        )
        with self._lock:
            self._jobs[finished.job_id] = finished
        return finished

    def mark_failed(self, job_id: UUID, *, error_msg: str) -> LiveConnectorJobRecord:
        job = self._get_running_job(job_id)
        failed = replace(
            job,
            status=JobStatus.FAILED,
            finished_at=datetime.now(UTC),
            last_error=_require_error(error_msg),
        )
        with self._lock:
            self._jobs[failed.job_id] = failed
        return failed

    def health(self) -> JobQueueHealth:
        with self._lock:
            return _health_from_records(LIVE_CONNECTOR_JOB_TYPE, tuple(self._jobs.values()))

    def _get_running_job(self, job_id: UUID) -> LiveConnectorJobRecord:
        with self._lock:
            job = self._jobs.get(job_id)
        if job is None:
            raise ValueError("live connector job not found")
        if job.status != JobStatus.RUNNING:
            raise ValueError("live connector job is not running")
        return job


class SqlAlchemyLiveConnectorJobStore:
    def __init__(self, session: Session) -> None:
        self._session = session

    def enqueue_usgs_tnm(
        self,
        *,
        area_id: UUID,
        bbox: UsgsTnmBbox | None = None,
        max_sample_points: int = USGS_TNM_MAX_SAMPLE_POINTS,
    ) -> LiveConnectorJobRecord:
        return self._enqueue(
            area_id=area_id,
            source_registry_id=LIVE_CONNECTOR_DS001_ID,
            connector_name=USGS_TNM_CONNECTOR_NAME,
            bbox=bbox,
            max_features=max_sample_points,
            max_allowed_features=USGS_TNM_MAX_SAMPLE_POINTS,
        )

    def enqueue_fema_nfhl(
        self,
        *,
        area_id: UUID,
        bbox: FemaNfhlBbox | None = None,
        max_features: int = FEMA_NFHL_MAX_FEATURES,
    ) -> LiveConnectorJobRecord:
        return self._enqueue(
            area_id=area_id,
            source_registry_id=LIVE_CONNECTOR_DS002_ID,
            connector_name=FEMA_NFHL_CONNECTOR_NAME,
            bbox=bbox,
            max_features=max_features,
            max_allowed_features=FEMA_NFHL_MAX_FEATURES,
        )

    def enqueue_nwi(
        self,
        *,
        area_id: UUID,
        bbox: NwiBbox | None = None,
        max_features: int = NWI_MAX_FEATURES,
    ) -> LiveConnectorJobRecord:
        return self._enqueue(
            area_id=area_id,
            source_registry_id=LIVE_CONNECTOR_DS004_ID,
            connector_name=NWI_CONNECTOR_NAME,
            bbox=bbox,
            max_features=max_features,
            max_allowed_features=NWI_MAX_FEATURES,
        )

    def enqueue_ssurgo(
        self,
        *,
        area_id: UUID,
        bbox: SsurgoBbox | None = None,
        max_rows: int = SSURGO_MAX_ROWS,
    ) -> LiveConnectorJobRecord:
        return self._enqueue(
            area_id=area_id,
            source_registry_id=LIVE_CONNECTOR_DS003_ID,
            connector_name=SSURGO_CONNECTOR_NAME,
            bbox=bbox,
            max_features=max_rows,
            max_allowed_features=SSURGO_MAX_ROWS,
        )

    def _enqueue(
        self,
        *,
        area_id: UUID,
        source_registry_id: str,
        connector_name: str,
        bbox: LiveConnectorBbox | None,
        max_features: int,
        max_allowed_features: int,
    ) -> LiveConnectorJobRecord:
        max_features = _require_max_features(max_features, max_allowed_features)
        idempotency_key = _idempotency_key(
            source_registry_id=source_registry_id,
            area_id=area_id,
            bbox=bbox,
            max_features=max_features,
        )
        self._session.execute(
            text(
                """
                INSERT INTO jobs.job_queue (
                    job_id,
                    job_type,
                    status,
                    priority,
                    payload,
                    idempotency_key,
                    max_attempts
                )
                VALUES (
                    :job_id,
                    :job_type,
                    CAST(:status AS jobs.job_status),
                    :priority,
                    CAST(:payload AS jsonb),
                    :idempotency_key,
                    1
                )
                ON CONFLICT (idempotency_key) DO NOTHING
                """
            ),
            {
                "job_id": str(_stable_job_id(idempotency_key)),
                "job_type": LIVE_CONNECTOR_JOB_TYPE,
                "status": JobStatus.QUEUED.value,
                "priority": 40,
                "payload": _json_payload(
                    source_registry_id=source_registry_id,
                    connector_name=connector_name,
                    area_id=area_id,
                    bbox=bbox,
                    max_features=max_features,
                ),
                "idempotency_key": idempotency_key,
            },
        )
        self._session.flush()
        queued = self._get_by_idempotency_key(idempotency_key)
        if queued is None:
            raise ValueError("live connector job insert did not round-trip")
        return queued

    def get(self, job_id: UUID) -> LiveConnectorJobRecord | None:
        row = (
            self._session.execute(
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
                  AND job_id = :job_id
                LIMIT 1
                """
                ),
                {
                    "job_type": LIVE_CONNECTOR_JOB_TYPE,
                    "job_id": str(job_id),
                },
            )
            .mappings()
            .one_or_none()
        )
        return None if row is None else _record_from_row(row)

    def list_recent(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        status: JobStatus | None = None,
        stale: bool = False,
    ) -> list[LiveConnectorJobRecord]:
        params: dict[str, object] = {
            "job_type": LIVE_CONNECTOR_JOB_TYPE,
            "limit": limit,
            "offset": offset,
        }
        predicates = ["job_type = :job_type"]
        if status is not None:
            params["status"] = status.value
            predicates.append("status = CAST(:status AS jobs.job_status)")
        if stale:
            params["running_status"] = JobStatus.RUNNING.value
            params["stale_running_threshold_seconds"] = STALE_RUNNING_THRESHOLD_SECONDS
            predicates.append("status = CAST(:running_status AS jobs.job_status)")
            predicates.append(
                """
                EXTRACT(EPOCH FROM (now() - COALESCE(started_at, created_at)))
                    >= :stale_running_threshold_seconds
                """
            )
        where_clause = " AND ".join(predicates)
        sql = f"""
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
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT :limit
                OFFSET :offset
                """
        rows = self._session.execute(text(sql), params).mappings().all()
        return [_record_from_row(row) for row in rows]

    def lease_next(self, *, worker_id: str) -> LiveConnectorJobRecord | None:
        worker_id = _require_worker_id(worker_id)
        row = (
            self._session.execute(
                text(
                    """
                WITH candidate AS (
                    SELECT job_id
                    FROM jobs.job_queue
                    WHERE job_type = :job_type
                      AND status = CAST(:queued_status AS jobs.job_status)
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
                    "job_type": LIVE_CONNECTOR_JOB_TYPE,
                    "queued_status": JobStatus.QUEUED.value,
                    "running_status": JobStatus.RUNNING.value,
                    "worker_id": worker_id,
                },
            )
            .mappings()
            .one_or_none()
        )
        self._session.flush()
        return None if row is None else _record_from_row(row)

    def mark_succeeded(
        self,
        job_id: UUID,
        *,
        connector_ingest_run_id: UUID,
        connector_review_status: str,
        request_url: str,
    ) -> LiveConnectorJobRecord:
        result_payload = _result_payload(
            connector_ingest_run_id=connector_ingest_run_id,
            connector_review_status=connector_review_status,
            request_url=request_url,
        )
        row = (
            self._session.execute(
                text(
                    """
                UPDATE jobs.job_queue
                SET
                    status = CAST(:status AS jobs.job_status),
                    finished_at = now(),
                    last_error = NULL,
                    payload = payload || CAST(:result_payload AS jsonb)
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
                    "status": JobStatus.SUCCEEDED.value,
                    "result_payload": json.dumps(result_payload, sort_keys=True),
                    "job_type": LIVE_CONNECTOR_JOB_TYPE,
                    "job_id": str(job_id),
                    "running_status": JobStatus.RUNNING.value,
                },
            )
            .mappings()
            .one_or_none()
        )
        self._session.flush()
        if row is None:
            raise ValueError("live connector job is not running")
        return _record_from_row(row)

    def mark_failed(self, job_id: UUID, *, error_msg: str) -> LiveConnectorJobRecord:
        row = (
            self._session.execute(
                text(
                    """
                UPDATE jobs.job_queue
                SET
                    status = CAST(:status AS jobs.job_status),
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
                    "status": JobStatus.FAILED.value,
                    "last_error": _require_error(error_msg),
                    "job_type": LIVE_CONNECTOR_JOB_TYPE,
                    "job_id": str(job_id),
                    "running_status": JobStatus.RUNNING.value,
                },
            )
            .mappings()
            .one_or_none()
        )
        self._session.flush()
        if row is None:
            raise ValueError("live connector job is not running")
        return _record_from_row(row)

    def health(self) -> JobQueueHealth:
        row = (
            self._session.execute(
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
                    ) AS oldest_queued_at,
                    min(COALESCE(started_at, created_at)) FILTER (
                        WHERE status = CAST(:running_status AS jobs.job_status)
                    ) AS oldest_running_at,
                    (
                        SELECT job_id
                        FROM jobs.job_queue
                        WHERE job_type = :job_type
                          AND status = CAST(:running_status AS jobs.job_status)
                        ORDER BY COALESCE(started_at, created_at), job_id
                        LIMIT 1
                    ) AS oldest_running_job_id,
                    count(*) FILTER (
                        WHERE status = CAST(:running_status AS jobs.job_status)
                          AND EXTRACT(
                              EPOCH FROM (now() - COALESCE(started_at, created_at))
                          ) >= :stale_running_threshold_seconds
                    ) AS stale_running
                FROM jobs.job_queue
                WHERE job_type = :job_type
                """
                ),
                _health_query_params(LIVE_CONNECTOR_JOB_TYPE),
            )
            .mappings()
            .one()
        )
        return _health_from_row(LIVE_CONNECTOR_JOB_TYPE, row)

    def _get_by_idempotency_key(
        self,
        idempotency_key: str,
    ) -> LiveConnectorJobRecord | None:
        row = (
            self._session.execute(
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
                    "job_type": LIVE_CONNECTOR_JOB_TYPE,
                    "idempotency_key": idempotency_key,
                },
            )
            .mappings()
            .one_or_none()
        )
        return None if row is None else _record_from_row(row)


def _payload(
    *,
    source_registry_id: str,
    connector_name: str,
    area_id: UUID,
    bbox: LiveConnectorBbox | None,
    max_features: int,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "kind": LIVE_CONNECTOR_JOB_TYPE,
        "source_registry_id": source_registry_id,
        "connector_name": connector_name,
        "area_id": str(area_id),
        "max_features": max_features,
    }
    if source_registry_id == LIVE_CONNECTOR_DS003_ID:
        payload["max_rows"] = max_features
    if source_registry_id == LIVE_CONNECTOR_DS001_ID:
        payload["max_sample_points"] = max_features
    if bbox is not None:
        payload["bbox"] = _bbox_payload(bbox)
    return payload


def _payload_with_result(
    payload: dict[str, Any],
    *,
    connector_ingest_run_id: UUID,
    connector_review_status: str,
    request_url: str,
) -> dict[str, Any]:
    return {
        **payload,
        **_result_payload(
            connector_ingest_run_id=connector_ingest_run_id,
            connector_review_status=connector_review_status,
            request_url=request_url,
        ),
    }


def _result_payload(
    *,
    connector_ingest_run_id: UUID,
    connector_review_status: str,
    request_url: str,
) -> dict[str, str]:
    return {
        "connector_ingest_run_id": str(connector_ingest_run_id),
        "connector_review_status": connector_review_status,
        "request_url": request_url,
    }


def _json_payload(
    *,
    source_registry_id: str,
    connector_name: str,
    area_id: UUID,
    bbox: LiveConnectorBbox | None,
    max_features: int,
) -> str:
    return json.dumps(
        _payload(
            source_registry_id=source_registry_id,
            connector_name=connector_name,
            area_id=area_id,
            bbox=bbox,
            max_features=max_features,
        ),
        sort_keys=True,
    )


def _bbox_payload(bbox: LiveConnectorBbox) -> dict[str, float]:
    return {
        "xmin": bbox.xmin,
        "ymin": bbox.ymin,
        "xmax": bbox.xmax,
        "ymax": bbox.ymax,
    }


def _bbox_from_payload(payload: Mapping[str, object]) -> LiveConnectorBbox | None:
    value = payload.get("bbox")
    if not isinstance(value, Mapping):
        return None
    bbox_kwargs = {
        "xmin": float(value["xmin"]),
        "ymin": float(value["ymin"]),
        "xmax": float(value["xmax"]),
        "ymax": float(value["ymax"]),
    }
    if payload.get("source_registry_id") == LIVE_CONNECTOR_DS001_ID:
        return UsgsTnmBbox(**bbox_kwargs)
    if payload.get("source_registry_id") == LIVE_CONNECTOR_DS003_ID:
        return SsurgoBbox(**bbox_kwargs)
    if payload.get("source_registry_id") == LIVE_CONNECTOR_DS004_ID:
        return NwiBbox(**bbox_kwargs)
    return FemaNfhlBbox(**bbox_kwargs)


def _idempotency_key(
    *,
    source_registry_id: str,
    area_id: UUID,
    bbox: LiveConnectorBbox | None,
    max_features: int,
) -> str:
    bbox_key = "area" if bbox is None else bbox.fingerprint
    return f"{LIVE_CONNECTOR_JOB_TYPE}:{source_registry_id}:{area_id}:{bbox_key}:{max_features}"


def _stable_job_id(idempotency_key: str) -> UUID:
    from uuid import NAMESPACE_URL, uuid5

    return uuid5(NAMESPACE_URL, idempotency_key)


def _record_from_row(row: Any) -> LiveConnectorJobRecord:
    payload = dict(row["payload"])
    return LiveConnectorJobRecord(
        job_id=UUID(str(row["job_id"])),
        area_id=UUID(str(payload["area_id"])),
        source_registry_id=str(payload["source_registry_id"]),
        connector_name=str(payload["connector_name"]),
        status=JobStatus(str(row["status"])),
        priority=int(row["priority"]),
        idempotency_key=str(row["idempotency_key"]),
        payload=payload,
        created_at=row["created_at"],
        max_features=int(payload["max_features"]),
        bbox=_bbox_from_payload(payload),
        connector_ingest_run_id=_optional_uuid(payload.get("connector_ingest_run_id")),
        connector_review_status=_optional_str(payload.get("connector_review_status")),
        request_url=_optional_str(payload.get("request_url")),
        not_before=row["not_before"],
        attempts=int(row["attempts"]),
        max_attempts=int(row["max_attempts"]),
        locked_by=row["locked_by"],
        locked_at=row["locked_at"],
        started_at=row["started_at"],
        finished_at=row["finished_at"],
        last_error=row["last_error"],
    )


def _optional_uuid(value: object) -> UUID | None:
    if value is None:
        return None
    return UUID(str(value))


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _require_worker_id(worker_id: str) -> str:
    cleaned = worker_id.strip()
    if not cleaned:
        raise ValueError("live connector worker_id is required")
    return cleaned


def _require_error(error_msg: str) -> str:
    cleaned = error_msg.strip()
    if not cleaned:
        raise ValueError("live connector job error is required")
    return cleaned


def _require_max_features(max_features: int, max_allowed_features: int) -> int:
    if max_features <= 0 or max_features > max_allowed_features:
        raise ValueError(f"max_features must be between 1 and {max_allowed_features}")
    return max_features


def _health_from_records(
    job_type: str,
    records: tuple[LiveConnectorJobRecord, ...],
) -> JobQueueHealth:
    counts = {status: 0 for status in JobStatus}
    queued_created_at: list[datetime] = []
    running_started_at: list[tuple[datetime, UUID]] = []
    stale_running = 0
    for record in records:
        counts[record.status] += 1
        if record.status == JobStatus.QUEUED:
            queued_created_at.append(record.created_at)
        if record.status == JobStatus.RUNNING:
            started_at = record.started_at or record.created_at
            running_started_at.append((started_at, record.job_id))
            age_seconds = _age_seconds(started_at)
            if age_seconds is not None and age_seconds >= STALE_RUNNING_THRESHOLD_SECONDS:
                stale_running += 1
    oldest_queued_at = min(queued_created_at) if queued_created_at else None
    oldest_running = min(running_started_at, default=None, key=lambda item: item[0])
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
        oldest_running_age_seconds=_age_seconds(oldest_running[0])
        if oldest_running is not None
        else None,
        oldest_running_job_id=oldest_running[1] if oldest_running is not None else None,
        stale_running=stale_running,
    )


def _health_query_params(job_type: str) -> dict[str, object]:
    return {
        "job_type": job_type,
        "queued_status": JobStatus.QUEUED.value,
        "running_status": JobStatus.RUNNING.value,
        "succeeded_status": JobStatus.SUCCEEDED.value,
        "failed_status": JobStatus.FAILED.value,
        "cancelled_status": JobStatus.CANCELLED.value,
        "needs_review_status": JobStatus.NEEDS_REVIEW.value,
        "stale_running_threshold_seconds": STALE_RUNNING_THRESHOLD_SECONDS,
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
        oldest_running_age_seconds=_age_seconds(row["oldest_running_at"]),
        oldest_running_job_id=_optional_uuid(row["oldest_running_job_id"]),
        stale_running=int(row["stale_running"]),
    )


def _age_seconds(created_at: datetime | None) -> float | None:
    if created_at is None:
        return None
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=UTC)
    return max(0.0, (datetime.now(UTC) - created_at).total_seconds())


def _is_stale_running(record: LiveConnectorJobRecord) -> bool:
    if record.status != JobStatus.RUNNING:
        return False
    age_seconds = _age_seconds(record.started_at or record.created_at)
    return age_seconds is not None and age_seconds >= STALE_RUNNING_THRESHOLD_SECONDS


__all__ = [
    "InMemoryLiveConnectorJobStore",
    "LIVE_CONNECTOR_DS001_ID",
    "LIVE_CONNECTOR_DS002_ID",
    "LIVE_CONNECTOR_DS003_ID",
    "LIVE_CONNECTOR_DS004_ID",
    "LIVE_CONNECTOR_JOB_TYPE",
    "LiveConnectorBbox",
    "LiveConnectorJobRecord",
    "LiveConnectorJobStoreProtocol",
    "SqlAlchemyLiveConnectorJobStore",
]
