from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel

from app.api.dependencies import ApiServices, get_services
from app.api.reviewer_auth import (
    REVIEWER_SCOPE_OPERATIONS_READ,
    ReviewerPrincipal,
    require_reviewer_scope,
)
from app.domain.enums import JobStatus
from app.domain.job_health import JobQueueHealth
from app.operations.recovery_preview import (
    JobRecoveryPreviewItem,
    build_recovery_preview,
)

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
    oldest_running_age_seconds: float | None = None
    oldest_running_job_id: UUID | None = None
    stale_running: int
    stale_running_threshold_seconds: int


class OperationsQueueHealthResponse(BaseModel):
    schema_version: str
    report_jobs: JobQueueHealthResponse
    live_connector_jobs: JobQueueHealthResponse


class JobRecoveryPreviewCandidateResponse(BaseModel):
    job_type: str
    job_id: UUID
    status: JobStatus
    area_id: UUID
    reason_code: str
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    age_seconds: float | None = None
    error_message: str | None = None
    detail_api_path: str
    detail_ui_path: str
    recommended_action: str
    recommended_action_label: str
    intent_code: str | None = None
    workspace_id: UUID | None = None
    retry_of_job_id: UUID | None = None
    source_registry_id: str | None = None
    connector_name: str | None = None
    attempts: int | None = None
    max_attempts: int | None = None
    locked_by: str | None = None
    locked_at: datetime | None = None


class JobRecoveryPreviewQueueResponse(BaseModel):
    job_type: str
    failed_count: int
    stale_running_count: int
    queued_count: int
    oldest_queued_age_seconds: float | None = None
    failed_candidates_truncated: bool
    stale_running_candidates_truncated: bool
    candidates: list[JobRecoveryPreviewCandidateResponse]


class OperationsRecoveryPreviewResponse(BaseModel):
    schema_version: str
    generated_at: datetime
    stale_running_threshold_seconds: int
    candidate_limit_per_state: int
    report_jobs: JobRecoveryPreviewQueueResponse
    live_connector_jobs: JobRecoveryPreviewQueueResponse


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
        report_jobs=job_queue_health_response(services.async_report_jobs.health()),
        live_connector_jobs=job_queue_health_response(services.live_connector_jobs.health()),
    )


@router.get("/recovery-preview", response_model=OperationsRecoveryPreviewResponse)
def recovery_preview(
    services: ServicesDep,
    principal: Annotated[ReviewerPrincipal, Depends(get_reviewer_principal)],
) -> OperationsRecoveryPreviewResponse:
    require_reviewer_scope(principal, REVIEWER_SCOPE_OPERATIONS_READ)
    preview = build_recovery_preview(
        report_jobs=services.async_report_jobs,
        live_connector_jobs=services.live_connector_jobs,
    )
    report_health = services.async_report_jobs.health()
    live_connector_health = services.live_connector_jobs.health()
    return OperationsRecoveryPreviewResponse(
        schema_version=preview.schema_version,
        generated_at=preview.generated_at,
        stale_running_threshold_seconds=preview.stale_running_threshold_seconds,
        candidate_limit_per_state=preview.candidate_limit_per_state,
        report_jobs=_recovery_queue_response(report_health, preview.report_jobs),
        live_connector_jobs=_recovery_queue_response(
            live_connector_health,
            preview.live_connector_jobs,
        ),
    )


def job_queue_health_response(health: JobQueueHealth) -> JobQueueHealthResponse:
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
        oldest_running_age_seconds=health.oldest_running_age_seconds,
        oldest_running_job_id=health.oldest_running_job_id,
        stale_running=health.stale_running,
        stale_running_threshold_seconds=health.stale_running_threshold_seconds,
    )


def _recovery_queue_response(
    health: JobQueueHealth,
    candidates: tuple[JobRecoveryPreviewItem, ...],
) -> JobRecoveryPreviewQueueResponse:
    failed_candidate_count = sum(1 for candidate in candidates if not candidate.stale_running)
    stale_candidate_count = sum(1 for candidate in candidates if candidate.stale_running)
    return JobRecoveryPreviewQueueResponse(
        job_type=health.job_type,
        failed_count=health.failed,
        stale_running_count=health.stale_running,
        queued_count=health.queued,
        oldest_queued_age_seconds=health.oldest_queued_age_seconds,
        failed_candidates_truncated=health.failed > failed_candidate_count,
        stale_running_candidates_truncated=health.stale_running > stale_candidate_count,
        candidates=[_recovery_candidate_response(candidate) for candidate in candidates],
    )


def _recovery_candidate_response(
    candidate: JobRecoveryPreviewItem,
) -> JobRecoveryPreviewCandidateResponse:
    return JobRecoveryPreviewCandidateResponse(
        job_type=candidate.job_type,
        job_id=candidate.job_id,
        status=candidate.status,
        area_id=candidate.area_id,
        reason_code="stale_running" if candidate.stale_running else "failed",
        created_at=candidate.created_at,
        started_at=candidate.started_at,
        finished_at=candidate.finished_at,
        age_seconds=candidate.age_seconds,
        error_message=candidate.error_message,
        detail_api_path=candidate.detail_api_path,
        detail_ui_path=candidate.detail_ui_path,
        recommended_action=candidate.recommended_action,
        recommended_action_label=candidate.reason,
        intent_code=candidate.intent_code,
        workspace_id=candidate.workspace_id,
        retry_of_job_id=candidate.retry_of_job_id,
        source_registry_id=candidate.source_registry_id,
        connector_name=candidate.connector_name,
        attempts=candidate.attempts,
        max_attempts=candidate.max_attempts,
        locked_by=candidate.locked_by,
        locked_at=candidate.locked_at,
    )


__all__ = ["router"]
