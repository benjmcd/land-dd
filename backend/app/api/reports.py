from __future__ import annotations

from collections.abc import Callable
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel

from app.api.dependencies import (
    ApiServices,
    RequestAuthContext,
    get_request_auth_context,
    get_services,
)
from app.domain.enums import IntentCode
from app.domain.report_contracts import ReportRunContract, ReportRunJobContract

router = APIRouter(prefix="/report-runs", tags=["report-runs"])
ServicesDep = Annotated[ApiServices, Depends(get_services)]
AuthDep = Annotated[RequestAuthContext, Depends(get_request_auth_context)]


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


class ReportRunJobExecuteRequest(BaseModel):
    worker_id: str


class ReportRunJobRequeueRequest(BaseModel):
    reason: str


class ReportReviewActionRequest(BaseModel):
    reviewer_id: str
    reason: str | None = None


@router.post("", response_model=ReportRunContract, status_code=status.HTTP_201_CREATED)
def create_report_run(
    request: ReportRunCreateRequest,
    services: ServicesDep,
    auth: AuthDep,
) -> ReportRunContract:
    try:
        _enforce_request_scope(
            auth,
            workspace_id=request.workspace_id,
            requested_by=request.requested_by,
        )
        return services.report_service.create_report_run(
            area_id=request.area_id,
            intent_code=request.intent_code,
            workspace_id=auth.workspace_id,
            requested_by=auth.user_id,
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
    auth: AuthDep,
    workspace_id: UUID | None = None,
    area_id: UUID | None = None,
    intent_code: IntentCode | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[ReportRunContract]:
    scoped_workspace_id = _authorized_workspace_filter(auth, workspace_id)
    return services.report_service.list_report_runs(
        workspace_id=scoped_workspace_id,
        area_id=area_id,
        intent_code=intent_code,
        limit=limit,
        offset=offset,
    )


@router.get("/{report_run_id}", response_model=ReportRunContract)
def get_report_run(
    report_run_id: UUID,
    services: ServicesDep,
    auth: AuthDep,
) -> ReportRunContract:
    return _get_authorized_report_run(report_run_id, services, auth)


@router.get("/{report_run_id}/dossier")
def get_report_run_dossier(
    report_run_id: UUID,
    services: ServicesDep,
    auth: AuthDep,
) -> Response:
    _get_authorized_report_run(report_run_id, services, auth)
    try:
        dossier = services.report_service.render_approved_dossier(report_run_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    if dossier is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="report run not found")
    return Response(content=dossier, media_type="text/markdown; charset=utf-8")


@router.post("/jobs", response_model=ReportRunJobContract, status_code=status.HTTP_202_ACCEPTED)
def submit_report_run_job(
    request: ReportRunJobCreateRequest,
    services: ServicesDep,
    auth: AuthDep,
) -> ReportRunJobContract:
    try:
        _enforce_request_scope(
            auth,
            workspace_id=request.workspace_id,
            requested_by=request.requested_by,
        )
        return services.report_service.submit_report_run_job(
            area_id=request.area_id,
            intent_code=request.intent_code,
            idempotency_key=request.idempotency_key,
            workspace_id=auth.workspace_id,
            requested_by=auth.user_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


@router.post("/jobs/execute-next", response_model=ReportRunJobContract)
def execute_next_report_run_job(
    request: ReportRunJobExecuteRequest,
    services: ServicesDep,
    auth: AuthDep,
) -> ReportRunJobContract:
    try:
        job = services.report_service.execute_next_report_run_job(
            worker_id=request.worker_id,
            workspace_id=auth.workspace_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="no queued report job available",
        )
    return job


@router.get("/jobs/{job_id}", response_model=ReportRunJobContract)
def get_report_run_job(
    job_id: UUID,
    services: ServicesDep,
    auth: AuthDep,
) -> ReportRunJobContract:
    job = services.report_service.get_report_run_job(job_id)
    if job is None or job.workspace_id != auth.workspace_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="report job not found")
    return job


@router.post("/jobs/{job_id}/requeue", response_model=ReportRunJobContract)
def requeue_report_run_job(
    job_id: UUID,
    request: ReportRunJobRequeueRequest,
    services: ServicesDep,
    auth: AuthDep,
) -> ReportRunJobContract:
    job = services.report_service.get_report_run_job(job_id)
    if job is None or job.workspace_id != auth.workspace_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="report job not found")
    try:
        return services.report_service.requeue_report_run_job(
            job_id,
            reason=request.reason,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


@router.post("/{report_run_id}/approve", response_model=ReportRunContract)
def approve_report_run(
    report_run_id: UUID,
    request: ReportReviewActionRequest,
    services: ServicesDep,
    auth: AuthDep,
) -> ReportRunContract:
    _get_authorized_report_run(report_run_id, services, auth)
    return _run_report_action(
        lambda: services.report_service.approve_report_run(
            report_run_id,
            reviewer_id=_reviewer_id(auth, request.reviewer_id),
            reason=request.reason,
        )
    )


@router.post("/{report_run_id}/reject", response_model=ReportRunContract)
def reject_report_run(
    report_run_id: UUID,
    request: ReportReviewActionRequest,
    services: ServicesDep,
    auth: AuthDep,
) -> ReportRunContract:
    _get_authorized_report_run(report_run_id, services, auth)
    return _run_report_action(
        lambda: services.report_service.reject_report_run(
            report_run_id,
            reviewer_id=_reviewer_id(auth, request.reviewer_id),
            reason=_required_action_reason(request.reason),
        )
    )


@router.post("/{report_run_id}/supersede", response_model=ReportRunContract)
def supersede_report_run(
    report_run_id: UUID,
    request: ReportReviewActionRequest,
    services: ServicesDep,
    auth: AuthDep,
) -> ReportRunContract:
    _get_authorized_report_run(report_run_id, services, auth)
    return _run_report_action(
        lambda: services.report_service.supersede_report_run(
            report_run_id,
            reviewer_id=_reviewer_id(auth, request.reviewer_id),
            reason=_required_action_reason(request.reason),
        )
    )


def _enforce_request_scope(
    auth: RequestAuthContext,
    *,
    workspace_id: UUID | None,
    requested_by: UUID | None,
) -> None:
    if workspace_id is not None and workspace_id != auth.workspace_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="request workspace does not match authenticated workspace",
        )
    if requested_by is not None and requested_by != auth.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="request user does not match authenticated user",
        )


def _authorized_workspace_filter(
    auth: RequestAuthContext,
    workspace_id: UUID | None,
) -> UUID:
    if workspace_id is not None and workspace_id != auth.workspace_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="workspace filter does not match authenticated workspace",
        )
    return auth.workspace_id


def _get_authorized_report_run(
    report_run_id: UUID,
    services: ApiServices,
    auth: RequestAuthContext,
) -> ReportRunContract:
    report_run = services.report_service.get_report_run(report_run_id)
    if report_run is None or report_run.workspace_id != auth.workspace_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="report run not found")
    return report_run


def _reviewer_id(auth: RequestAuthContext, reviewer_id: str) -> str:
    reviewer = reviewer_id.strip()
    if not reviewer:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="reviewer_id is required",
        )
    if reviewer != str(auth.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="reviewer_id does not match authenticated user",
        )
    return reviewer


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
