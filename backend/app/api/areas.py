from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import (
    ApiServices,
    RequestAuthContext,
    get_request_auth_context,
    get_services,
)
from app.domain.area_contracts import AreaContract

router = APIRouter(prefix="/areas", tags=["areas"])
ServicesDep = Annotated[ApiServices, Depends(get_services)]
AuthDep = Annotated[RequestAuthContext, Depends(get_request_auth_context)]


@router.get("", response_model=list[AreaContract])
def list_areas(services: ServicesDep, auth: AuthDep) -> list[AreaContract]:
    return services.area_service.list_all(workspace_id=auth.workspace_id)


@router.post("", response_model=AreaContract, status_code=status.HTTP_201_CREATED)
def create_area(
    area: AreaContract,
    services: ServicesDep,
    auth: AuthDep,
) -> AreaContract:
    try:
        _enforce_area_scope(area, auth)
        scoped_area = area.model_copy(
            update={
                "workspace_id": auth.workspace_id,
                "created_by": auth.user_id,
            }
        )
        return services.area_service.create(scoped_area)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


def _enforce_area_scope(area: AreaContract, auth: RequestAuthContext) -> None:
    if area.workspace_id is not None and area.workspace_id != auth.workspace_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="area workspace does not match authenticated workspace",
        )
    if area.created_by is not None and area.created_by != auth.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="area creator does not match authenticated user",
        )
