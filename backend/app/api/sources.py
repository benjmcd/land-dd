from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import ApiServices, get_services
from app.domain.source_contracts import SourceContract

router = APIRouter(prefix="/sources", tags=["sources"])
ServicesDep = Annotated[ApiServices, Depends(get_services)]


@router.get("", response_model=list[SourceContract])
def list_sources(services: ServicesDep) -> list[SourceContract]:
    return services.source_service.list_all()


@router.post("", response_model=SourceContract, status_code=status.HTTP_201_CREATED)
def create_source(source: SourceContract, services: ServicesDep) -> SourceContract:
    try:
        return services.source_service.register(source)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
