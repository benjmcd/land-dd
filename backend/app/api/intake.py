from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.dependencies import ApiServices, get_services
from app.api.reports import run_report_background
from app.domain.area_contracts import AreaContract
from app.domain.enums import AreaType, IntentCode

router = APIRouter(tags=["intake"])


class IntakeRequest(BaseModel):
    area_geojson: dict[str, object]
    intent_code: IntentCode


class IntakeResponse(BaseModel):
    report_run_id: UUID
    area_id: UUID
    status: str = "queued"


ServicesDep = Annotated[ApiServices, Depends(get_services)]


@router.post("/intake", response_model=IntakeResponse, status_code=status.HTTP_202_ACCEPTED)
def intake_report(
    request: IntakeRequest,
    background_tasks: BackgroundTasks,
    services: ServicesDep,
) -> IntakeResponse:
    area = AreaContract(
        area_type=AreaType.DRAWN_POLYGON,
        geom_geojson=request.area_geojson,
    )
    try:
        created = services.area_service.create(area)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    job = services.async_report_jobs.create(
        area_id=created.area_id,
        intent_code=request.intent_code,
    )
    background_tasks.add_task(
        run_report_background,
        services=services,
        report_run_id=job.report_run_id,
        area_id=created.area_id,
        intent_code=request.intent_code,
    )
    return IntakeResponse(
        report_run_id=job.report_run_id,
        area_id=created.area_id,
    )
