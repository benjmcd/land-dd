from __future__ import annotations

from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from pydantic import BaseModel

from app.api.dependencies import ApiServices, get_services
from app.api.live_connectors import orchestrate_request_time_live_connectors_for_area
from app.api.reports import schedule_report_background
from app.core.config import Settings
from app.domain.area_contracts import AreaContract
from app.domain.enums import AreaType, IntentCode

router = APIRouter(tags=["intake"])


class IntakeRequest(BaseModel):
    area_geojson: dict[str, object]
    intent_code: IntentCode


class IntakeResponse(BaseModel):
    report_run_id: UUID | None = None
    area_id: UUID
    status: str = "queued"
    connector_ingest_run_id: UUID | None = None
    connector_review_status: str | None = None


ServicesDep = Annotated[ApiServices, Depends(get_services)]


@router.post("/intake", response_model=IntakeResponse, status_code=status.HTTP_202_ACCEPTED)
def intake_report(
    request: IntakeRequest,
    background_tasks: BackgroundTasks,
    request_context: Request,
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
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    if _live_connectors_enabled(request_context):
        connector_result = orchestrate_request_time_live_connectors_for_area(
            services=services,
            area=created,
        )
        if connector_result is not None:
            return IntakeResponse(
                area_id=created.area_id,
                status="pending_connector_review",
                connector_ingest_run_id=connector_result.ingest_run_id,
                connector_review_status=connector_result.queue_item.status.value,
            )

    job = services.async_report_jobs.create(
        area_id=created.area_id,
        intent_code=request.intent_code,
    )
    schedule_report_background(
        background_tasks=background_tasks,
        request_context=request_context,
        services=services,
        report_run_id=job.report_run_id,
        area_id=created.area_id,
        intent_code=request.intent_code,
    )
    return IntakeResponse(
        report_run_id=job.report_run_id,
        area_id=created.area_id,
    )


def _live_connectors_enabled(request_context: Request) -> bool:
    settings = cast(Settings, request_context.app.state.settings)
    return settings.enable_live_connectors
