from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies import (
    ApiServices,
    RequestAuthContext,
    get_request_auth_context,
    get_services,
)
from app.domain.evidence_contracts import EvidenceContract

router = APIRouter(prefix="/evidence", tags=["evidence"])
ServicesDep = Annotated[ApiServices, Depends(get_services)]
AuthDep = Annotated[RequestAuthContext, Depends(get_request_auth_context)]


@router.get("", response_model=list[EvidenceContract])
def list_evidence(
    services: ServicesDep,
    auth: AuthDep,
    area_id: UUID,
) -> list[EvidenceContract]:
    if not services.area_service.area_is_registered(
        area_id,
        workspace_id=auth.workspace_id,
    ):
        return []
    return services.evidence_service.list_by_area(area_id)
