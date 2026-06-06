from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel

from app.api.dependencies import ApiServices, get_services
from app.api.reviewer_auth import (
    REVIEWER_SCOPE_OPERATIONS_READ,
    ReviewerPrincipal,
    require_reviewer_scope,
)
from app.domain.job_health import JobQueueHealth

router = APIRouter(prefix="/operations", tags=["operations"])
ServicesDep = Annotated[ApiServices, Depends(get_services)]


class JobQueueHealthResponse(BaseModel):
    job_type: str
    total: int
    queued: int
    running: int
    succeeded: int
    failed: int
    cancelled: int
    needs_review: int
    oldest_queued_age_seconds: float | None = None


class OperationsQueueHealthResponse(BaseModel):
    schema_version: str
    report_jobs: JobQueueHealthResponse
    live_connector_jobs: JobQueueHealthResponse


def get_reviewer_principal(
    services: ServicesDep,
    reviewer_id: Annotated[str | None, Header(alias="X-Reviewer-Id")] = None,
    reviewer_token: Annotated[str | None, Header(alias="X-Reviewer-Token")] = None,
) -> ReviewerPrincipal:
    return services.reviewer_auth(reviewer_id=reviewer_id, reviewer_token=reviewer_token)


@router.get("/queue-health", response_model=OperationsQueueHealthResponse)
def queue_health(
    services: ServicesDep,
    principal: Annotated[ReviewerPrincipal, Depends(get_reviewer_principal)],
) -> OperationsQueueHealthResponse:
    require_reviewer_scope(principal, REVIEWER_SCOPE_OPERATIONS_READ)
    return OperationsQueueHealthResponse(
        schema_version="operations_queue_health_v1",
        report_jobs=_job_queue_health_response(services.async_report_jobs.health()),
        live_connector_jobs=_job_queue_health_response(services.live_connector_jobs.health()),
    )


def _job_queue_health_response(health: JobQueueHealth) -> JobQueueHealthResponse:
    return JobQueueHealthResponse(
        job_type=health.job_type,
        total=health.total,
        queued=health.queued,
        running=health.running,
        succeeded=health.succeeded,
        failed=health.failed,
        cancelled=health.cancelled,
        needs_review=health.needs_review,
        oldest_queued_age_seconds=health.oldest_queued_age_seconds,
    )


__all__ = ["router"]
