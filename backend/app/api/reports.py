from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.api.dependencies import ApiServices, get_services
from app.domain.enums import IntentCode
from app.domain.report_contracts import ReportRunContract

router = APIRouter(prefix="/report-runs", tags=["report-runs"])
ServicesDep = Annotated[ApiServices, Depends(get_services)]


class ReportRunCreateRequest(BaseModel):
    area_id: UUID
    intent_code: IntentCode


@router.post("", response_model=ReportRunContract, status_code=status.HTTP_201_CREATED)
def create_report_run(
    request: ReportRunCreateRequest,
    services: ServicesDep,
) -> ReportRunContract:
    try:
        return services.report_service.create_report_run(
            area_id=request.area_id,
            intent_code=request.intent_code,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


@router.get("", response_model=list[ReportRunContract])
def list_report_runs(
    services: ServicesDep,
    area_id: UUID | None = None,
    intent_code: IntentCode | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[ReportRunContract]:
    return services.report_service.list_report_runs(
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
