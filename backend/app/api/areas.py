from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import ApiServices, get_services
from app.domain.area_contracts import AreaContract

router = APIRouter(prefix="/areas", tags=["areas"])
ServicesDep = Annotated[ApiServices, Depends(get_services)]


@router.get("", response_model=list[AreaContract])
def list_areas(services: ServicesDep) -> list[AreaContract]:
    return services.area_service.list_all()


@router.post("", response_model=AreaContract, status_code=status.HTTP_201_CREATED)
def create_area(area: AreaContract, services: ServicesDep) -> AreaContract:
    try:
        return services.area_service.create(area)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
