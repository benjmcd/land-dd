from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.api.dependencies import ApiServices, get_services
from app.api.reviewer_auth import (
    REVIEWER_SCOPE_SOURCE_MANAGE,
    ReviewerPrincipal,
    require_reviewer_scope,
)
from app.domain.source_contracts import SourceContract

router = APIRouter(prefix="/sources", tags=["sources"])
ServicesDep = Annotated[ApiServices, Depends(get_services)]


def get_reviewer_principal(
    services: ServicesDep,
    reviewer_id: Annotated[str | None, Header(alias="X-Reviewer-Id")] = None,
    reviewer_token: Annotated[str | None, Header(alias="X-Reviewer-Token")] = None,
) -> ReviewerPrincipal:
    return services.reviewer_auth(reviewer_id=reviewer_id, reviewer_token=reviewer_token)


@router.get("", response_model=list[SourceContract])
def list_sources(services: ServicesDep) -> list[SourceContract]:
    return services.source_service.list_all()


@router.post("", response_model=SourceContract, status_code=status.HTTP_201_CREATED)
def create_source(
    source: SourceContract,
    services: ServicesDep,
    principal: Annotated[ReviewerPrincipal, Depends(get_reviewer_principal)],
) -> SourceContract:
    require_reviewer_scope(principal, REVIEWER_SCOPE_SOURCE_MANAGE)
    try:
        return services.source_service.register(source)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
