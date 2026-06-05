from __future__ import annotations

from collections.abc import Callable
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.api.dependencies import ApiServices, get_services
from app.domain.enums import IntentCode
from app.domain.report_contracts import ReportRunContract, ReportRunJobContract

router = APIRouter(prefix="/report-runs", tags=["report-runs"])
ServicesDep = Annotated[ApiServices, Depends(get_services)]


class ReportRunCreateRequest(BaseModel):
    area_id: UUID
    intent_code: IntentCode
    workspace_id: UUID | None = None
    requested_by: UUID | None = None
    idempotency_key: str | None = None


class ReportRunJobCreateRequest(BaseModel):
    area_id: UUID
    intent_code: IntentCode
    idempotency_key: str
    workspace_id: UUID | None = None
    requested_by: UUID | None = None


class ReportReviewActionRequest(BaseModel):
    reviewer_id: str
    reason: str | None = None


@router.post("", response_model=ReportRunContract, status_code=status.HTTP_201_CREATED)
def create_report_run(
    request: ReportRunCreateRequest,
    services: ServicesDep,
) -> ReportRunContract:
    try:
        return services.report_service.create_report_run(
            area_id=request.area_id,
            intent_code=request.intent_code,
            workspace_id=request.workspace_id,
            requested_by=request.requested_by,
            idempotency_key=request.idempotency_key,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


@router.get("", response_model=list[ReportRunContract])
def list_report_runs(
    services: ServicesDep,
    workspace_id: UUID | None = None,
    area_id: UUID | None = None,
    intent_code: IntentCode | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[ReportRunContract]:
    return services.report_service.list_report_runs(
        workspace_id=workspace_id,
        area_id=area_id,
        intent_code=intent_code,
        limit=limit,
        offset=offset,
    )


@router.get("/{report_run_id}", response_model=ReportRunContract)
def get_report_run(
    report_run_id: UUID,
    services: ServicesDep,
) -> ReportRunContract:
    report_run = services.report_service.get_report_run(report_run_id)
    if report_run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="report run not found")
    return report_run


@router.post("/jobs", response_model=ReportRunJobContract, status_code=status.HTTP_202_ACCEPTED)
def submit_report_run_job(
    request: ReportRunJobCreateRequest,
    services: ServicesDep,
) -> ReportRunJobContract:
    try:
        return services.report_service.submit_report_run_job(
            area_id=request.area_id,
            intent_code=request.intent_code,
            idempotency_key=request.idempotency_key,
            workspace_id=request.workspace_id,
            requested_by=request.requested_by,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


@router.get("/jobs/{job_id}", response_model=ReportRunJobContract)
def get_report_run_job(
    job_id: UUID,
    services: ServicesDep,
) -> ReportRunJobContract:
    job = services.report_service.get_report_run_job(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="report job not found")
    return job


@router.post("/{report_run_id}/approve", response_model=ReportRunContract)
def approve_report_run(
    report_run_id: UUID,
    request: ReportReviewActionRequest,
    services: ServicesDep,
) -> ReportRunContract:
    return _run_report_action(
        lambda: services.report_service.approve_report_run(
            report_run_id,
            reviewer_id=request.reviewer_id,
            reason=request.reason,
        )
    )


@router.post("/{report_run_id}/reject", response_model=ReportRunContract)
def reject_report_run(
    report_run_id: UUID,
    request: ReportReviewActionRequest,
    services: ServicesDep,
) -> ReportRunContract:
    return _run_report_action(
        lambda: services.report_service.reject_report_run(
            report_run_id,
            reviewer_id=request.reviewer_id,
            reason=_required_action_reason(request.reason),
        )
    )


@router.post("/{report_run_id}/supersede", response_model=ReportRunContract)
def supersede_report_run(
    report_run_id: UUID,
    request: ReportReviewActionRequest,
    services: ServicesDep,
) -> ReportRunContract:
    return _run_report_action(
        lambda: services.report_service.supersede_report_run(
            report_run_id,
            reviewer_id=request.reviewer_id,
            reason=_required_action_reason(request.reason),
        )
    )


def _run_report_action(action: Callable[[], ReportRunContract]) -> ReportRunContract:
    try:
        return action()
    except ValueError as exc:
        message = str(exc)
        status_code = (
            status.HTTP_404_NOT_FOUND
            if "was not found" in message
            else status.HTTP_422_UNPROCESSABLE_CONTENT
        )
        raise HTTPException(status_code=status_code, detail=message) from exc


def _required_action_reason(reason: str | None) -> str:
    if reason is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="report review reason is required",
        )
    return reason
