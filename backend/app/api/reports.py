from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.dependencies import ApiServices, get_services
from app.domain.enums import IntentCode, JobStatus
from app.domain.report_contracts import ReportRunContract

router = APIRouter(prefix="/report-runs", tags=["report-runs"])
ServicesDep = Annotated[ApiServices, Depends(get_services)]


class ReportRunCreateRequest(BaseModel):
    area_id: UUID
    intent_code: IntentCode


class AsyncReportRunResponse(BaseModel):
    report_run_id: UUID
    status: str


def run_report_background(
    *,
    services: ApiServices,
    report_run_id: UUID,
    area_id: UUID,
    intent_code: IntentCode,
) -> None:
    services.async_report_jobs.mark_running(report_run_id)
    try:
        services.report_service.create_report_run(
            area_id=area_id,
            intent_code=intent_code,
            report_run_id=report_run_id,
        )
        services.async_report_jobs.mark_succeeded(report_run_id)
    except Exception as exc:  # noqa: BLE001
        services.async_report_jobs.mark_failed(report_run_id, error_msg=str(exc))


@router.post("", response_model=AsyncReportRunResponse, status_code=status.HTTP_202_ACCEPTED)
def create_report_run(
    request: ReportRunCreateRequest,
    background_tasks: BackgroundTasks,
    services: ServicesDep,
) -> AsyncReportRunResponse:
    if not services.area_service.area_is_registered(request.area_id):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Area '{request.area_id}' is not registered",
        )
    job = services.async_report_jobs.create(
        area_id=request.area_id,
        intent_code=request.intent_code,
    )
    background_tasks.add_task(
        run_report_background,
        services=services,
        report_run_id=job.report_run_id,
        area_id=request.area_id,
        intent_code=request.intent_code,
    )
    return AsyncReportRunResponse(report_run_id=job.report_run_id, status="queued")


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
