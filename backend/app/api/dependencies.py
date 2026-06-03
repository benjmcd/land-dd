from __future__ import annotations

from dataclasses import dataclass, field
from typing import cast
from uuid import UUID

from fastapi import Request

from app.area_geometry.area_repo import InMemoryAreaRepository
from app.area_geometry.service import AreaService
from app.domain.report_contracts import ReportRunContract
from app.evidence_ledger.evidence_repo import InMemoryEvidenceRepository
from app.evidence_ledger.service import EvidenceService
from app.source_registry.service import SourceService
from app.source_registry.source_repo import InMemorySourceRepository


@dataclass
class ApiServices:
    source_service: SourceService
    area_service: AreaService
    evidence_service: EvidenceService
    report_runs: dict[UUID, ReportRunContract] = field(default_factory=dict)


def create_api_services() -> ApiServices:
    source_service = SourceService(InMemorySourceRepository())
    area_service = AreaService(InMemoryAreaRepository())
    evidence_service = EvidenceService(
        InMemoryEvidenceRepository(),
        source_service,
        area_service,
    )
    return ApiServices(
        source_service=source_service,
        area_service=area_service,
        evidence_service=evidence_service,
    )


def get_services(request: Request) -> ApiServices:
    return cast(ApiServices, request.app.state.services)


__all__ = ["ApiServices", "create_api_services", "get_services"]
