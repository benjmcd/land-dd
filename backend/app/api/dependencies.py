from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, cast
from uuid import UUID

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.area_geometry.area_repo import InMemoryAreaRepository, SqlAlchemyAreaRepository
from app.area_geometry.service import AreaService
from app.claims_engine.claim_repo import InMemoryClaimRepository, SqlAlchemyClaimRepository
from app.claims_engine.rule_engine import RuleEngine
from app.claims_engine.service import ClaimService
from app.connectors import (
    ConnectorReviewQueueRepository,
    ConnectorRunReviewStatus,
    InMemoryConnectorReviewQueueRepository,
    SqlAlchemyConnectorReviewQueueRepository,
)
from app.db.session import get_db_session
from app.evidence_ledger.evidence_repo import (
    InMemoryEvidenceRepository,
    SqlAlchemyEvidenceRepository,
)
from app.evidence_ledger.service import EvidenceService
from app.reports.adapters import AreaServiceProtocolAdapter, SourceServiceProtocolAdapter
from app.reports.report_repo import SqlAlchemyReportRunRepository
from app.reports.service import ReportRunService
from app.source_registry.service import SourceService
from app.source_registry.source_repo import InMemorySourceRepository, SqlAlchemySourceRepository


@dataclass
class ApiServices:
    source_service: SourceService
    area_service: AreaService
    evidence_service: EvidenceService
    report_service: ReportRunService
    connector_review_statuses: dict[UUID, ConnectorRunReviewStatus]
    connector_review_queue: ConnectorReviewQueueRepository


def create_api_services() -> ApiServices:
    source_service = SourceService(InMemorySourceRepository())
    area_service = AreaService(InMemoryAreaRepository())
    evidence_repo = InMemoryEvidenceRepository()
    evidence_service = EvidenceService(
        evidence_repo,
        SourceServiceProtocolAdapter(source_service),
        AreaServiceProtocolAdapter(area_service),
    )
    claim_service = ClaimService(InMemoryClaimRepository(), evidence_repo)
    report_service = ReportRunService(
        source_service=source_service,
        area_service=area_service,
        evidence_service=evidence_service,
        claim_service=claim_service,
        rule_engine=RuleEngine.from_file(),
    )
    return ApiServices(
        source_service=source_service,
        area_service=area_service,
        evidence_service=evidence_service,
        report_service=report_service,
        connector_review_statuses={},
        connector_review_queue=InMemoryConnectorReviewQueueRepository(),
    )


def create_db_api_services(
    session: Session,
    *,
    object_store_root: str | Path,
) -> ApiServices:
    source_service = SourceService(SqlAlchemySourceRepository(session))
    area_service = AreaService(SqlAlchemyAreaRepository(session))
    evidence_repo = SqlAlchemyEvidenceRepository(session)
    evidence_service = EvidenceService(
        evidence_repo,
        SourceServiceProtocolAdapter(source_service),
        AreaServiceProtocolAdapter(area_service),
    )
    claim_service = ClaimService(SqlAlchemyClaimRepository(session), evidence_repo)
    report_service = ReportRunService(
        source_service=source_service,
        area_service=area_service,
        evidence_service=evidence_service,
        claim_service=claim_service,
        rule_engine=RuleEngine.from_file(),
        report_repo=SqlAlchemyReportRunRepository(session, object_store_root),
    )
    return ApiServices(
        source_service=source_service,
        area_service=area_service,
        evidence_service=evidence_service,
        report_service=report_service,
        connector_review_statuses={},
        connector_review_queue=SqlAlchemyConnectorReviewQueueRepository(session),
    )


def get_services(request: Request) -> ApiServices:
    return cast(ApiServices, request.app.state.services)


def get_db_services(
    request: Request,
    session: Annotated[Session, Depends(get_db_session)],
) -> Iterator[ApiServices]:
    try:
        yield create_db_api_services(
            session,
            object_store_root=cast(str, request.app.state.object_store_root),
        )
        session.commit()
    except Exception:
        session.rollback()
        raise


__all__ = [
    "ApiServices",
    "create_api_services",
    "create_db_api_services",
    "get_db_services",
    "get_services",
]
