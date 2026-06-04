from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.dependencies import ApiServices, get_services

router = APIRouter(prefix="/connector-runs", tags=["connector-runs"])
ServicesDep = Annotated[ApiServices, Depends(get_services)]


class ConnectorFixtureQualityIssueResponse(BaseModel):
    code: str
    message: str
    blocking: bool


class ConnectorFixtureQualityResponse(BaseModel):
    passed: bool
    evidence_count: int
    source_failure_count: int
    blocking_issue_count: int
    issues: tuple[ConnectorFixtureQualityIssueResponse, ...]


class ConnectorRunReviewStatusResponse(BaseModel):
    queue_name: str
    disposition: str
    priority: str
    title: str
    summary: str
    connector_name: str
    ingest_run_id: UUID
    dataset_version_id: UUID | None
    retrieval_status: str
    review_required: bool
    evidence_created_count: int
    evidence_skipped_count: int
    source_failure_created_count: int
    source_failure_skipped_count: int
    signal_codes: tuple[str, ...]
    tasks: tuple[str, ...]
    quality: ConnectorFixtureQualityResponse


class ConnectorReviewQueueItemResponse(BaseModel):
    job_id: UUID
    ingest_run_id: UUID
    job_type: str
    status: str
    priority: int
    idempotency_key: str
    payload: dict[str, Any]
    created_at: datetime
    attempts: int
    max_attempts: int
    locked_by: str | None
    locked_at: datetime | None
    started_at: datetime | None
    finished_at: datetime | None
    last_error: str | None


@router.get(
    "/{ingest_run_id}/review-status",
    response_model=ConnectorRunReviewStatusResponse,
)
def get_connector_run_review_status(
    ingest_run_id: UUID,
    services: ServicesDep,
) -> dict[str, object]:
    review_status = services.connector_review_statuses.get(ingest_run_id)
    if review_status is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="connector run review status not found",
        )
    return review_status.to_status_record()


@router.get(
    "/{ingest_run_id}/review-queue",
    response_model=ConnectorReviewQueueItemResponse,
)
def get_connector_review_queue_item(
    ingest_run_id: UUID,
    services: ServicesDep,
) -> dict[str, object]:
    queue_item = services.connector_review_queue.get_by_ingest_run_id(ingest_run_id)
    if queue_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="connector review queue item not found",
        )
    return {
        "job_id": queue_item.job_id,
        "ingest_run_id": queue_item.ingest_run_id,
        "job_type": queue_item.job_type,
        "status": queue_item.status.value,
        "priority": queue_item.priority,
        "idempotency_key": queue_item.idempotency_key,
        "payload": queue_item.payload,
        "created_at": queue_item.created_at,
        "attempts": queue_item.attempts,
        "max_attempts": queue_item.max_attempts,
        "locked_by": queue_item.locked_by,
        "locked_at": queue_item.locked_at,
        "started_at": queue_item.started_at,
        "finished_at": queue_item.finished_at,
        "last_error": queue_item.last_error,
    }
