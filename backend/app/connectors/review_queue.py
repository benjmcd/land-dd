from __future__ import annotations

import json
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
    workspace_id: UUID | None = None
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
        *,
        workspace_id: UUID | None = None,
        requested_by: UUID | None = None,
    ) -> ConnectorReviewQueueItem: ...

    def get_by_ingest_run_id(
        self,
        ingest_run_id: UUID,
        *,
        workspace_id: UUID | None = None,
    ) -> ConnectorReviewQueueItem | None: ...

    def list_connector_runs(
        self,
        *,
        workspace_id: UUID | None = None,
        status: str | None = None,
        connector_name: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ConnectorReviewQueueItem]: ...

    def lease_next(self, *, worker_id: str) -> ConnectorReviewQueueItem | None: ...

    def mark_succeeded(self, job_id: UUID) -> ConnectorReviewQueueItem: ...

    def mark_failed(self, job_id: UUID, *, error: str) -> ConnectorReviewQueueItem: ...

    def approve_for_connector_qa(
        self,
        job_id: UUID,
        *,
        reviewer_id: str,
        reason: str | None = None,
    ) -> ConnectorReviewQueueItem: ...

    def request_fixture_fix(
        self,
        job_id: UUID,
        *,
        reviewer_id: str,
        reason: str,
    ) -> ConnectorReviewQueueItem: ...

    def requeue_failed(
        self,
        job_id: UUID,
        *,
        reason: str,
        reviewer_id: str | None = None,
        not_before: datetime | None = None,
    ) -> ConnectorReviewQueueItem: ...

    def cancel(
        self,
        job_id: UUID,
        *,
        reason: str,
        reviewer_id: str | None = None,
    ) -> ConnectorReviewQueueItem: ...


class InMemoryConnectorReviewQueueRepository:
    def __init__(self) -> None:
        self._store: dict[UUID, ConnectorReviewQueueItem] = {}

    def enqueue_review_status(
        self,
        review_status: ConnectorRunReviewStatus,
        *,
        workspace_id: UUID | None = None,
        requested_by: UUID | None = None,
    ) -> ConnectorReviewQueueItem:
        ingest_run_id = review_status.handoff.packet.ingest_run_id
        existing = self.get_by_ingest_run_id(
            ingest_run_id,
            workspace_id=workspace_id,
        )
        if existing is not None:
            return existing
        if ingest_run_id in self._store:
            raise ValueError("connector review queue insert did not round-trip")
        item = ConnectorReviewQueueItem(
            job_id=ingest_run_id,
            workspace_id=workspace_id,
            ingest_run_id=ingest_run_id,
            job_type=CONNECTOR_REVIEW_STATUS_JOB_TYPE,
            status=JobStatus.NEEDS_REVIEW
            if review_status.review_required
            else JobStatus.QUEUED,
            priority=_priority(review_status),
            idempotency_key=_idempotency_key(ingest_run_id),
            payload=_payload(
                review_status,
                workspace_id=workspace_id,
                requested_by=requested_by,
            ),
            created_at=review_status.handoff.packet.started_at,
            not_before=review_status.handoff.packet.started_at,
        )
        self._store[ingest_run_id] = item
        return item

    def get_by_ingest_run_id(
        self,
        ingest_run_id: UUID,
        *,
        workspace_id: UUID | None = None,
    ) -> ConnectorReviewQueueItem | None:
        item = self._store.get(ingest_run_id)
        if item is None:
            return None
        if workspace_id is not None and item.workspace_id != workspace_id:
            return None
        return item

    def list_connector_runs(
        self,
        *,
        workspace_id: UUID | None = None,
        status: str | None = None,
        connector_name: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ConnectorReviewQueueItem]:
        items = list(self._store.values())
        if workspace_id is not None:
            items = [item for item in items if item.workspace_id == workspace_id]
        if status is not None:
            items = [item for item in items if item.status.value == status]
        if connector_name is not None:
            items = [
                item
                for item in items
                if item.payload.get("connector_name") == connector_name
            ]
        items.sort(key=lambda item: (item.created_at, item.job_id))
        return items[offset : offset + limit]

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

    def approve_for_connector_qa(
        self,
        job_id: UUID,
        *,
        reviewer_id: str,
        reason: str | None = None,
    ) -> ConnectorReviewQueueItem:
        reviewer_id = _require_reviewer_id(reviewer_id)
        reason = _optional_reason(reason)
        item = self._get_open_review_job(job_id, action="approved")
        decided_at = datetime.now(UTC)
        approved = replace(
            item,
            status=JobStatus.SUCCEEDED,
            locked_by=reviewer_id,
            locked_at=item.locked_at or decided_at,
            started_at=item.started_at or decided_at,
            finished_at=decided_at,
            last_error=None,
            payload=_payload_with_review_decision(
                item.payload,
                action="approve_for_connector_qa",
                reviewer_id=reviewer_id,
                reason=reason,
                decided_at=decided_at,
            ),
        )
        self._store[approved.ingest_run_id] = approved
        return approved

    def request_fixture_fix(
        self,
        job_id: UUID,
        *,
        reviewer_id: str,
        reason: str,
    ) -> ConnectorReviewQueueItem:
        reviewer_id = _require_reviewer_id(reviewer_id)
        reason = _require_reason(reason)
        item = self._get_open_review_job(job_id, action="failed")
        decided_at = datetime.now(UTC)
        failed = replace(
            item,
            status=JobStatus.FAILED,
            locked_by=reviewer_id,
            locked_at=item.locked_at or decided_at,
            started_at=item.started_at or decided_at,
            finished_at=decided_at,
            last_error=reason,
            payload=_payload_with_review_decision(
                item.payload,
                action="request_fixture_fix",
                reviewer_id=reviewer_id,
                reason=reason,
                decided_at=decided_at,
            ),
        )
        self._store[failed.ingest_run_id] = failed
        return failed

    def requeue_failed(
        self,
        job_id: UUID,
        *,
        reason: str,
        reviewer_id: str | None = None,
        not_before: datetime | None = None,
    ) -> ConnectorReviewQueueItem:
        reason = _require_reason(reason)
        reviewer_id = _optional_reviewer_id(reviewer_id)
        item = self._get_job(job_id)
        if item.status != JobStatus.FAILED:
            raise ValueError("connector review queue job is not failed")
        if item.attempts >= item.max_attempts:
            raise ValueError("connector review queue job has no retry attempts remaining")
        decided_at = datetime.now(UTC)
        requeued = replace(
            item,
            status=JobStatus.QUEUED,
            not_before=not_before or decided_at,
            locked_by=None,
            locked_at=None,
            finished_at=None,
            last_error=reason,
            payload=_payload_with_review_action(
                item.payload,
                action="requeue_after_fix",
                reviewer_id=reviewer_id,
                reason=reason,
                decided_at=decided_at,
            ),
        )
        self._store[requeued.ingest_run_id] = requeued
        return requeued

    def cancel(
        self,
        job_id: UUID,
        *,
        reason: str,
        reviewer_id: str | None = None,
    ) -> ConnectorReviewQueueItem:
        reason = _require_reason(reason)
        reviewer_id = _optional_reviewer_id(reviewer_id)
        item = self._get_job(job_id)
        if item.status in {JobStatus.SUCCEEDED, JobStatus.CANCELLED}:
            raise ValueError("connector review queue job cannot be cancelled")
        decided_at = datetime.now(UTC)
        cancelled = replace(
            item,
            status=JobStatus.CANCELLED,
            finished_at=decided_at,
            last_error=reason,
            payload=_payload_with_review_action(
                item.payload,
                action="cancel_review",
                reviewer_id=reviewer_id,
                reason=reason,
                decided_at=decided_at,
            ),
        )
        self._store[cancelled.ingest_run_id] = cancelled
        return cancelled

    def _get_running_job(self, job_id: UUID) -> ConnectorReviewQueueItem:
        item = self._get_job(job_id)
        if item.status != JobStatus.RUNNING:
            raise ValueError("connector review queue job is not running")
        return item

    def _get_open_review_job(
        self,
        job_id: UUID,
        *,
        action: str,
    ) -> ConnectorReviewQueueItem:
        item = self._get_job(job_id)
        if item.status not in {JobStatus.NEEDS_REVIEW, JobStatus.QUEUED, JobStatus.RUNNING}:
            raise ValueError(f"connector review queue job cannot be {action}")
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
        *,
        workspace_id: UUID | None = None,
        requested_by: UUID | None = None,
    ) -> ConnectorReviewQueueItem:
        ingest_run_id = review_status.handoff.packet.ingest_run_id
        existing = self.get_by_ingest_run_id(
            ingest_run_id,
            workspace_id=workspace_id,
        )
        if existing is not None:
            return existing
        self._session.execute(
            text(
                """
                INSERT INTO jobs.job_queue (
                    job_type,
                    workspace_id,
                    status,
                    priority,
                    payload,
                    idempotency_key,
                    max_attempts
                )
                VALUES (
                    :job_type,
                    :workspace_id,
                    :status,
                    :priority,
                    CAST(:payload AS jsonb),
                    :idempotency_key,
                    1
                )
                ON CONFLICT (idempotency_key) DO NOTHING
                """
            ),
            {
                "job_type": CONNECTOR_REVIEW_STATUS_JOB_TYPE,
                "workspace_id": workspace_id,
                "status": (
                    JobStatus.NEEDS_REVIEW
                    if review_status.review_required
                    else JobStatus.QUEUED
                ).value,
                "priority": _priority(review_status),
                "payload": _json_payload(
                    review_status,
                    workspace_id=workspace_id,
                    requested_by=requested_by,
                ),
                "idempotency_key": _idempotency_key(ingest_run_id),
            },
        )
        self._session.flush()
        queued = self.get_by_ingest_run_id(
            ingest_run_id,
            workspace_id=workspace_id,
        )
        if queued is None:
            raise ValueError("connector review queue insert did not round-trip")
        return queued

    def get_by_ingest_run_id(
        self,
        ingest_run_id: UUID,
        *,
        workspace_id: UUID | None = None,
    ) -> ConnectorReviewQueueItem | None:
        row = self._session.execute(
            text(
                """
                SELECT
                    job_id,
                    workspace_id,
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
        if workspace_id is not None and item.workspace_id != workspace_id:
            return None
        return item

    def list_connector_runs(
        self,
        *,
        workspace_id: UUID | None = None,
        status: str | None = None,
        connector_name: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ConnectorReviewQueueItem]:
        predicates = ["job_type = :job_type"]
        params: dict[str, object] = {
            "job_type": CONNECTOR_REVIEW_STATUS_JOB_TYPE,
            "limit": limit,
            "offset": offset,
        }
        if workspace_id is not None:
            predicates.append("workspace_id = :workspace_id")
            params["workspace_id"] = str(workspace_id)
        if status is not None:
            predicates.append("status = CAST(:status AS jobs.job_status)")
            params["status"] = status
        if connector_name is not None:
            predicates.append("payload->>'connector_name' = :connector_name")
            params["connector_name"] = connector_name
        where_clause = " AND ".join(predicates)
        rows = self._session.execute(
            text(
                f"""
                SELECT
                    job_id,
                    workspace_id,
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
                ORDER BY created_at, job_id
                LIMIT :limit OFFSET :offset
                """
            ),
            params,
        ).mappings().all()
        return [_item_from_row(row) for row in rows]

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

    def approve_for_connector_qa(
        self,
        job_id: UUID,
        *,
        reviewer_id: str,
        reason: str | None = None,
    ) -> ConnectorReviewQueueItem:
        return self._manual_closeout_job(
            job_id,
            status=JobStatus.SUCCEEDED,
            reviewer_id=_require_reviewer_id(reviewer_id),
            action="approve_for_connector_qa",
            reason=_optional_reason(reason),
            error=None,
        )

    def request_fixture_fix(
        self,
        job_id: UUID,
        *,
        reviewer_id: str,
        reason: str,
    ) -> ConnectorReviewQueueItem:
        reason = _require_reason(reason)
        return self._manual_closeout_job(
            job_id,
            status=JobStatus.FAILED,
            reviewer_id=_require_reviewer_id(reviewer_id),
            action="request_fixture_fix",
            reason=reason,
            error=reason,
        )

    def requeue_failed(
        self,
        job_id: UUID,
        *,
        reason: str,
        reviewer_id: str | None = None,
        not_before: datetime | None = None,
    ) -> ConnectorReviewQueueItem:
        reviewer_id = _optional_reviewer_id(reviewer_id)
        decided_at = datetime.now(UTC)
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
                    last_error = :last_error,
                    payload = jsonb_set(
                        payload,
                        '{review_action_history}',
                        COALESCE(payload->'review_action_history', '[]'::jsonb)
                            || jsonb_build_array(CAST(:review_action AS jsonb)),
                        true
                    )
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
                "review_action": _review_action_json(
                    action="requeue_after_fix",
                    reviewer_id=reviewer_id,
                    reason=reason,
                    decided_at=decided_at,
                ),
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

    def cancel(
        self,
        job_id: UUID,
        *,
        reason: str,
        reviewer_id: str | None = None,
    ) -> ConnectorReviewQueueItem:
        reviewer_id = _optional_reviewer_id(reviewer_id)
        decided_at = datetime.now(UTC)
        row = self._session.execute(
            text(
                """
                UPDATE jobs.job_queue
                SET
                    status = CAST(:cancelled_status AS jobs.job_status),
                    finished_at = now(),
                    last_error = :last_error,
                    payload = jsonb_set(
                        payload,
                        '{review_action_history}',
                        COALESCE(payload->'review_action_history', '[]'::jsonb)
                            || jsonb_build_array(CAST(:review_action AS jsonb)),
                        true
                    )
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
                "review_action": _review_action_json(
                    action="cancel_review",
                    reviewer_id=reviewer_id,
                    reason=reason,
                    decided_at=decided_at,
                ),
                "job_type": CONNECTOR_REVIEW_STATUS_JOB_TYPE,
                "job_id": str(job_id),
                "succeeded_status": JobStatus.SUCCEEDED.value,
            },
        ).mappings().one_or_none()
        self._session.flush()
        if row is None:
            raise ValueError("connector review queue job cannot be cancelled")
        return _item_from_row(row)

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

    def _manual_closeout_job(
        self,
        job_id: UUID,
        *,
        status: JobStatus,
        reviewer_id: str,
        action: str,
        reason: str | None,
        error: str | None,
    ) -> ConnectorReviewQueueItem:
        decided_at = datetime.now(UTC)
        review_decision = _review_action_json(
            action=action,
            reviewer_id=reviewer_id,
            reason=reason,
            decided_at=decided_at,
        )
        row = self._session.execute(
            text(
                """
                UPDATE jobs.job_queue
                SET
                    status = CAST(:finished_status AS jobs.job_status),
                    locked_by = :reviewer_id,
                    locked_at = COALESCE(locked_at, now()),
                    started_at = COALESCE(started_at, now()),
                    finished_at = now(),
                    last_error = :last_error,
                    payload = jsonb_set(
                        jsonb_set(
                            payload,
                            '{review_decision}',
                            CAST(:review_decision AS jsonb),
                            true
                        ),
                        '{review_action_history}',
                        COALESCE(payload->'review_action_history', '[]'::jsonb)
                            || jsonb_build_array(CAST(:review_decision AS jsonb)),
                        true
                    )
                WHERE job_type = :job_type
                  AND job_id = :job_id
                  AND status IN (
                      CAST(:needs_review_status AS jobs.job_status),
                      CAST(:queued_status AS jobs.job_status),
                      CAST(:running_status AS jobs.job_status)
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
                "finished_status": status.value,
                "reviewer_id": reviewer_id,
                "last_error": error,
                "review_decision": review_decision,
                "job_type": CONNECTOR_REVIEW_STATUS_JOB_TYPE,
                "job_id": str(job_id),
                "needs_review_status": JobStatus.NEEDS_REVIEW.value,
                "queued_status": JobStatus.QUEUED.value,
                "running_status": JobStatus.RUNNING.value,
            },
        ).mappings().one_or_none()
        self._session.flush()
        if row is None:
            raise ValueError(f"connector review queue job cannot be {action}")
        return _item_from_row(row)


def _priority(review_status: ConnectorRunReviewStatus) -> int:
    if review_status.review_required:
        return 10
    return 100


def _idempotency_key(ingest_run_id: UUID) -> str:
    return f"{CONNECTOR_REVIEW_STATUS_JOB_TYPE}:{ingest_run_id}"


def _json_ready(value: Any) -> Any:
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, list | tuple | set):
        return [_json_ready(item) for item in value]
    return str(value)


def _payload(
    review_status: ConnectorRunReviewStatus,
    *,
    workspace_id: UUID | None = None,
    requested_by: UUID | None = None,
) -> dict[str, Any]:
    record = review_status.to_status_record()
    packet = review_status.handoff.packet
    payload = {
        "kind": CONNECTOR_REVIEW_STATUS_JOB_TYPE,
        "title": record["title"],
        "summary": record["summary"],
        "connector_name": record["connector_name"],
        "ingest_run_id": record["ingest_run_id"],
        "area_id": record["area_id"],
        "dataset_version_id": record["dataset_version_id"],
        "retrieval_status": record["retrieval_status"],
        "retrieval_recorded": packet.retrieval_recorded,
        "retrieval_skipped": packet.retrieval_skipped,
        "started_at": packet.started_at.isoformat(),
        "finished_at": (
            packet.finished_at.isoformat() if packet.finished_at is not None else None
        ),
        "row_count": packet.row_count,
        "error_count": packet.error_count,
        "warning_count": packet.warning_count,
        "log_uri": packet.log_uri,
        "metrics": _json_ready(packet.metrics),
        "review_required": record["review_required"],
        "disposition": record["disposition"],
        "priority": record["priority"],
        "queue_name": record["queue_name"],
        "signal_codes": _json_ready(record["signal_codes"]),
        "tasks": _json_ready(record["tasks"]),
        "evidence_input_count": packet.evidence_input_count,
        "evidence_created_count": record["evidence_created_count"],
        "evidence_skipped_count": record["evidence_skipped_count"],
        "source_failure_created_count": record["source_failure_created_count"],
        "source_failure_skipped_count": record["source_failure_skipped_count"],
        "created_evidence_ids": _json_ready(packet.created_evidence_ids),
        "skipped_evidence_ids": _json_ready(packet.skipped_evidence_ids),
        "source_failure_evidence_ids": _json_ready(packet.source_failure_evidence_ids),
        "created_evidence": [
            summary.to_review_record() for summary in packet.created_evidence
        ],
        "skipped_evidence": [
            summary.to_review_record() for summary in packet.skipped_evidence
        ],
        "quality": _json_ready(record["quality"]),
    }
    if workspace_id is not None:
        payload["workspace_id"] = str(workspace_id)
    if requested_by is not None:
        payload["requested_by"] = str(requested_by)
    return payload


def _json_payload(
    review_status: ConnectorRunReviewStatus,
    *,
    workspace_id: UUID | None = None,
    requested_by: UUID | None = None,
) -> str:
    import json

    return json.dumps(
        _payload(
            review_status,
            workspace_id=workspace_id,
            requested_by=requested_by,
        ),
        sort_keys=True,
    )


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
        workspace_id=(
            UUID(str(payload["workspace_id"]))
            if payload.get("workspace_id") is not None
            else None
        ),
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


def _require_reviewer_id(reviewer_id: str) -> str:
    cleaned = reviewer_id.strip()
    if not cleaned:
        raise ValueError("connector review queue reviewer_id is required")
    return cleaned


def _optional_reviewer_id(reviewer_id: str | None) -> str | None:
    if reviewer_id is None:
        return None
    return _require_reviewer_id(reviewer_id)


def _require_reason(reason: str) -> str:
    cleaned = reason.strip()
    if not cleaned:
        raise ValueError("connector review queue reason is required")
    return cleaned


def _optional_reason(reason: str | None) -> str | None:
    if reason is None:
        return None
    return _require_reason(reason)


def _payload_with_review_decision(
    payload: dict[str, Any],
    *,
    action: str,
    reviewer_id: str,
    reason: str | None,
    decided_at: datetime,
) -> dict[str, Any]:
    review_decision = _review_action_entry(
        action=action,
        reviewer_id=reviewer_id,
        reason=reason,
        decided_at=decided_at,
    )
    history = _append_review_action_history(payload, review_decision)
    compat_action = _compat_review_action_entry(review_decision)
    compat_history = _append_compat_review_actions(payload, compat_action)
    return {
        **payload,
        "review_decision": review_decision,
        "last_review_action": compat_action,
        "review_action_history": history,
        "review_actions": compat_history,
    }


def _payload_with_review_action(
    payload: dict[str, Any],
    *,
    action: str,
    reviewer_id: str | None,
    reason: str | None,
    decided_at: datetime,
) -> dict[str, Any]:
    review_action = _review_action_entry(
        action=action,
        reviewer_id=reviewer_id,
        reason=reason,
        decided_at=decided_at,
    )
    history = _append_review_action_history(payload, review_action)
    compat_action = _compat_review_action_entry(review_action)
    compat_history = _append_compat_review_actions(payload, compat_action)
    return {
        **payload,
        "last_review_action": compat_action,
        "review_action_history": history,
        "review_actions": compat_history,
    }


def _append_review_action_history(
    payload: dict[str, Any],
    review_action: dict[str, object],
) -> list[object]:
    current = payload.get("review_action_history")
    if isinstance(current, list):
        return [*current, review_action]
    return [review_action]


def _append_compat_review_actions(
    payload: dict[str, Any],
    review_action: dict[str, object],
) -> list[object]:
    current = payload.get("review_actions")
    if isinstance(current, list):
        return [*current, review_action]
    return [review_action]


def _compat_review_action_entry(
    review_action: dict[str, object],
) -> dict[str, object]:
    action = review_action.get("action")
    action_name = str(action) if action is not None else ""
    aliases = {
        "approve_for_connector_qa": "approve",
        "request_fixture_fix": "reject",
        "requeue_after_fix": "requeue",
        "cancel_review": "cancel",
    }
    return {
        **review_action,
        "action": aliases.get(action_name, action_name),
    }


def _review_action_entry(
    *,
    action: str,
    reviewer_id: str | None,
    reason: str | None,
    decided_at: datetime,
) -> dict[str, object]:
    return {
        "action": action,
        "reviewer_id": reviewer_id,
        "reason": reason,
        "decided_at": decided_at.isoformat(),
    }


def _review_action_json(
    *,
    action: str,
    reviewer_id: str | None,
    reason: str | None,
    decided_at: datetime,
) -> str:
    return json.dumps(
        _review_action_entry(
            action=action,
            reviewer_id=reviewer_id,
            reason=reason,
            decided_at=decided_at,
        ),
        sort_keys=True,
    )


__all__ = [
    "CONNECTOR_REVIEW_STATUS_JOB_TYPE",
    "ConnectorReviewQueueItem",
    "ConnectorReviewQueueRepository",
    "InMemoryConnectorReviewQueueRepository",
    "SqlAlchemyConnectorReviewQueueRepository",
]
