from __future__ import annotations

from typing import Annotated
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
