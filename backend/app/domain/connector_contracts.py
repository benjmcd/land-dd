from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.domain.enums import JobStatus


class ConnectorReviewQueueItemContract(BaseModel):
    job_id: UUID
    workspace_id: UUID | None = None
    ingest_run_id: UUID
    job_type: str
    status: JobStatus
    priority: int
    payload: dict[str, object]
    created_at: datetime
    not_before: datetime | None = None
    attempts: int = 0
    max_attempts: int = 1
    locked_by: str | None = None
    locked_at: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    last_error: str | None = None


class ConnectorRunResultContract(BaseModel):
    ingest_run_id: UUID
    connector_name: str
    retrieval_status: str
    evidence_created: int
    evidence_skipped: int
    review_required: bool
    queue_job_id: UUID | None = None


__all__ = ["ConnectorReviewQueueItemContract", "ConnectorRunResultContract"]
