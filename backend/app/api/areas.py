from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from app.api.dependencies import (
    ApiServices,
    get_request_auth_context,
    get_services,
)
from app.domain.area_contracts import AreaContract

router = APIRouter(prefix="/areas", tags=["areas"])
ServicesDep = Annotated[ApiServices, Depends(get_services)]
_HTTP_422_UNPROCESSABLE: int = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422)


@router.get("", response_model=list[AreaContract])
def list_areas(services: ServicesDep) -> list[AreaContract]:
    return services.area_service.list_all()


@router.post("", response_model=AreaContract, status_code=status.HTTP_201_CREATED)
def create_area(
    area: AreaContract,
    services: ServicesDep,
    request_context: Request,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
    x_user_id: Annotated[str | None, Header(alias="X-User-Id")] = None,
) -> AreaContract:
    try:
        if (
            request_context.app.state.settings.report_auth_mode == "signed_token"
            or _has_header_value(x_workspace_id)
            or _has_header_value(x_user_id)
        ):
            auth = get_request_auth_context(
                request_context,
                authorization=authorization,
                x_workspace_id=x_workspace_id,
                x_user_id=x_user_id,
            )
            area = area.model_copy(
                update={
                    "workspace_id": auth.workspace_id,
                    "created_by": auth.user_id,
                }
            )
        return services.area_service.create(area)
    except ValueError as exc:
        raise HTTPException(
            status_code=_HTTP_422_UNPROCESSABLE,
            detail=str(exc),
        ) from exc


def _has_header_value(raw: str | None) -> bool:
    return raw is not None and bool(raw.strip())
