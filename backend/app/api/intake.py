from __future__ import annotations

from typing import Annotated, cast
from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Header,
    HTTPException,
    Request,
    Response,
    status,
)
from pydantic import BaseModel

from app.api.dependencies import ApiServices, RequestAuthContext, get_services
from app.api.live_connectors import orchestrate_request_time_live_connectors_for_area
from app.api.reports import (
    _authenticated_idempotency_key,
    _optional_report_auth_context,
    _validate_idempotency_key,
    raise_report_queue_backpressure_if_needed,
    schedule_report_background,
)
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
_HTTP_422_UNPROCESSABLE: int = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422)

# Sentinel area_id used for idempotency pre-check on intake (area not yet created).
# The actual area_id is unknown before geometry registration, so we store the job
# keyed only by the client key. The payload mismatch check is skipped for intake
# (geometry hash is the payload discriminator, stored in the client key itself).
_INTAKE_NULL_AREA = UUID("00000000-0000-0000-0000-000000000000")


@router.post("/intake", response_model=IntakeResponse, status_code=status.HTTP_202_ACCEPTED)
def intake_report(
    request: IntakeRequest,
    background_tasks: BackgroundTasks,
    request_context: Request,
    services: ServicesDep,
    response: Response,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
    x_user_id: Annotated[str | None, Header(alias="X-User-Id")] = None,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> IntakeResponse:
    client_key = _validate_idempotency_key(idempotency_key)
    auth = _optional_report_auth_context(
        request_context,
        authorization=authorization,
        x_workspace_id=x_workspace_id,
        x_user_id=x_user_id,
    )

    # Idempotency pre-check for intake: the client key embeds intent so we look
    # up by key alone (area_id is unknown pre-registration).
    if client_key is not None:
        # Build a scoped key that includes the intent_code so same geometry +
        # different intent is treated as a different request.
        scoped_key = _effective_intake_idempotency_key(
            client_key,
            request.intent_code,
            auth=auth,
        )
        existing = services.async_report_jobs.get_by_client_idempotency_key(
            scoped_key,
            area_id=_INTAKE_NULL_AREA,
            intent_code=request.intent_code,
        )
        if existing is not None:
            response.status_code = status.HTTP_200_OK
            return IntakeResponse(
                report_run_id=existing.report_run_id,
                area_id=existing.area_id,
                status=existing.status.value,
            )

    area = AreaContract(
        workspace_id=auth.workspace_id if auth is not None else None,
        created_by=auth.user_id if auth is not None else None,
        area_type=AreaType.DRAWN_POLYGON,
        geom_geojson=request.area_geojson,
    )
    try:
        created = services.area_service.create(area)
    except ValueError as exc:
        raise HTTPException(
            status_code=_HTTP_422_UNPROCESSABLE,
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

    effective_key = (
        _effective_intake_idempotency_key(client_key, request.intent_code, auth=auth)
        if client_key is not None
        else None
    )
    raise_report_queue_backpressure_if_needed(
        request_context=request_context,
        services=services,
    )
    job = services.async_report_jobs.create(
        area_id=created.area_id,
        intent_code=request.intent_code,
        client_idempotency_key=effective_key,
        workspace_id=auth.workspace_id if auth is not None else None,
        requested_by=auth.user_id if auth is not None else None,
    )
    schedule_report_background(
        background_tasks=background_tasks,
        request_context=request_context,
        services=services,
        report_run_id=job.report_run_id,
        area_id=created.area_id,
        intent_code=request.intent_code,
        workspace_id=job.workspace_id,
        requested_by=job.requested_by,
    )
    return IntakeResponse(
        report_run_id=job.report_run_id,
        area_id=created.area_id,
    )


def _make_intake_scoped_key(client_key: str, intent_code: IntentCode) -> str:
    """Scope an intake idempotency key by intent_code (non-optional variant)."""
    return f"intake:{intent_code.value}:{client_key}"


def _effective_intake_idempotency_key(
    client_key: str,
    intent_code: IntentCode,
    *,
    auth: RequestAuthContext | None,
) -> str:
    scoped_key = _make_intake_scoped_key(client_key, intent_code)
    if auth is None:
        return scoped_key
    return _authenticated_idempotency_key(scoped_key, auth=auth)


def _live_connectors_enabled(request_context: Request) -> bool:
    settings = cast(Settings, request_context.app.state.settings)
    return settings.enable_live_connectors
