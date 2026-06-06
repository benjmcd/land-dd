from __future__ import annotations

import logging
from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel

from app.api.dependencies import ApiServices, create_db_api_services, get_services
from app.api.live_connectors import orchestrate_request_time_live_connectors_for_area
from app.api.reviewer_auth import (
    REVIEWER_SCOPE_REPORT_RETRY,
    ReviewerPrincipal,
    require_reviewer_scope,
)
from app.core.config import Settings
from app.db.engine import get_session_factory
from app.domain.enums import IntentCode, JobStatus
from app.domain.report_contracts import ReportRunContract
from app.reports.job_store import SqlAlchemyAsyncReportJobStore

router = APIRouter(prefix="/report-runs", tags=["report-runs"])
ServicesDep = Annotated[ApiServices, Depends(get_services)]
logger = logging.getLogger(__name__)


class ReportRunCreateRequest(BaseModel):
    area_id: UUID
    intent_code: IntentCode


class AsyncReportRunResponse(BaseModel):
    report_run_id: UUID | None = None
    status: str
    connector_ingest_run_id: UUID | None = None
    connector_review_status: str | None = None
    retry_of_report_run_id: UUID | None = None


def get_reviewer_principal(
    services: ServicesDep,
    reviewer_id: Annotated[str | None, Header(alias="X-Reviewer-Id")] = None,
    reviewer_token: Annotated[str | None, Header(alias="X-Reviewer-Token")] = None,
) -> ReviewerPrincipal:
    return services.reviewer_auth(reviewer_id=reviewer_id, reviewer_token=reviewer_token)


def run_report_background(
    *,
    services: ApiServices,
    report_run_id: UUID,
    area_id: UUID,
    intent_code: IntentCode,
) -> None:
    services.async_report_jobs.mark_running(report_run_id)
    logger.info(
        "report job running",
        extra=_job_log_context(report_run_id, area_id, intent_code),
    )
    try:
        services.report_service.create_report_run(
            area_id=area_id,
            intent_code=intent_code,
            report_run_id=report_run_id,
        )
        services.async_report_jobs.mark_succeeded(report_run_id)
        logger.info(
            "report job succeeded",
            extra=_job_log_context(report_run_id, area_id, intent_code),
        )
    except Exception as exc:  # noqa: BLE001
        services.async_report_jobs.mark_failed(report_run_id, error_msg=str(exc))
        logger.exception(
            "report job failed",
            extra=_job_log_context(report_run_id, area_id, intent_code),
        )


def run_db_report_background(
    *,
    report_run_id: UUID,
    area_id: UUID,
    intent_code: IntentCode,
    object_store_root: str,
    settings: Settings,
) -> None:
    job_store = SqlAlchemyAsyncReportJobStore()
    try:
        job_store.mark_running(report_run_id)
        logger.info(
            "report job running",
            extra=_job_log_context(report_run_id, area_id, intent_code),
        )
        with get_session_factory()() as session:
            services = create_db_api_services(
                session,
                object_store_root=object_store_root,
                settings=settings,
            )
            services.report_service.create_report_run(
                area_id=area_id,
                intent_code=intent_code,
                report_run_id=report_run_id,
            )
            session.commit()
        job_store.mark_succeeded(report_run_id)
        logger.info(
            "report job succeeded",
            extra=_job_log_context(report_run_id, area_id, intent_code),
        )
    except Exception as exc:  # noqa: BLE001
        job_store.mark_failed(report_run_id, error_msg=str(exc))
        logger.exception(
            "report job failed",
            extra=_job_log_context(report_run_id, area_id, intent_code),
        )


def schedule_report_background(
    *,
    background_tasks: BackgroundTasks,
    request_context: Request,
    services: ApiServices,
    report_run_id: UUID,
    area_id: UUID,
    intent_code: IntentCode,
) -> None:
    logger.info(
        "report job queued",
        extra=_job_log_context(report_run_id, area_id, intent_code),
    )
    if bool(getattr(request_context.app.state, "use_db_services", False)):
        background_tasks.add_task(
            run_db_report_background,
            report_run_id=report_run_id,
            area_id=area_id,
            intent_code=intent_code,
            object_store_root=str(request_context.app.state.object_store_root),
            settings=cast(Settings, request_context.app.state.settings),
        )
        return
    background_tasks.add_task(
        run_report_background,
        services=services,
        report_run_id=report_run_id,
        area_id=area_id,
        intent_code=intent_code,
    )


@router.post("", response_model=AsyncReportRunResponse, status_code=status.HTTP_202_ACCEPTED)
def create_report_run(
    request: ReportRunCreateRequest,
    background_tasks: BackgroundTasks,
    request_context: Request,
    services: ServicesDep,
) -> AsyncReportRunResponse:
    area = services.area_service.get(request.area_id)
    if area is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Area '{request.area_id}' is not registered",
        )
    if _live_connectors_enabled(request_context):
        connector_result = orchestrate_request_time_live_connectors_for_area(
            services=services,
            area=area,
        )
        if connector_result is not None:
            return AsyncReportRunResponse(
                status="pending_connector_review",
                connector_ingest_run_id=connector_result.ingest_run_id,
                connector_review_status=connector_result.queue_item.status.value,
            )
    job = services.async_report_jobs.create(
        area_id=request.area_id,
        intent_code=request.intent_code,
    )
    schedule_report_background(
        background_tasks=background_tasks,
        request_context=request_context,
        services=services,
        report_run_id=job.report_run_id,
        area_id=request.area_id,
        intent_code=request.intent_code,
    )
    return AsyncReportRunResponse(
        report_run_id=job.report_run_id,
        status="queued",
    )


@router.post(
    "/{report_run_id}/retry",
    response_model=AsyncReportRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def retry_report_run(
    report_run_id: UUID,
    background_tasks: BackgroundTasks,
    request_context: Request,
    services: ServicesDep,
    principal: Annotated[ReviewerPrincipal, Depends(get_reviewer_principal)],
) -> AsyncReportRunResponse:
    require_reviewer_scope(principal, REVIEWER_SCOPE_REPORT_RETRY)
    failed_job = services.async_report_jobs.get(report_run_id)
    if failed_job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="report run job not found",
        )
    if failed_job.status != JobStatus.FAILED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="report run retry requires a failed report job",
        )

    retry_job = services.async_report_jobs.create(
        area_id=failed_job.area_id,
        intent_code=failed_job.intent_code,
        retry_of_report_run_id=failed_job.report_run_id,
    )
    schedule_report_background(
        background_tasks=background_tasks,
        request_context=request_context,
        services=services,
        report_run_id=retry_job.report_run_id,
        area_id=retry_job.area_id,
        intent_code=retry_job.intent_code,
    )
    return AsyncReportRunResponse(
        report_run_id=retry_job.report_run_id,
        status="queued",
        retry_of_report_run_id=failed_job.report_run_id,
    )


@router.get("/{report_run_id}", response_model=ReportRunContract)
def get_report_run(
    report_run_id: UUID,
    services: ServicesDep,
) -> ReportRunContract:
    job = services.async_report_jobs.get(report_run_id)
    if job is not None:
        if job.status in (JobStatus.QUEUED, JobStatus.RUNNING):
            return ReportRunContract(
                report_run_id=report_run_id,
                area_id=job.area_id,
                intent_code=job.intent_code,
                status=job.status,
            )
        if job.status == JobStatus.FAILED:
            return ReportRunContract(
                report_run_id=report_run_id,
                area_id=job.area_id,
                intent_code=job.intent_code,
                status=JobStatus.FAILED,
                caveats=[job.error_msg or "Report generation failed"],
            )
        # SUCCEEDED — fall through to fetch full report from repo

    report = services.report_service.get_report_run(report_run_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="report run not found")
    return report


def _job_log_context(
    report_run_id: UUID,
    area_id: UUID,
    intent_code: IntentCode,
) -> dict[str, str]:
    return {
        "report_run_id": str(report_run_id),
        "area_id": str(area_id),
        "intent_code": intent_code.value,
    }


def _live_connectors_enabled(request_context: Request) -> bool:
    settings = cast(Settings, request_context.app.state.settings)
    return settings.enable_live_connectors
