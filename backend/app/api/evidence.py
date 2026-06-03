from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies import ApiServices, get_services
from app.domain.evidence_contracts import EvidenceContract

router = APIRouter(prefix="/evidence", tags=["evidence"])
ServicesDep = Annotated[ApiServices, Depends(get_services)]


@router.get("", response_model=list[EvidenceContract])
def list_evidence(
    services: ServicesDep,
    area_id: UUID,
) -> list[EvidenceContract]:
    return services.evidence_service.list_by_area(area_id)
