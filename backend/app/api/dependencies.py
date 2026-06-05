from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, cast
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.area_geometry.area_repo import InMemoryAreaRepository, SqlAlchemyAreaRepository
from app.area_geometry.service import AreaService
from app.claims_engine.claim_repo import InMemoryClaimRepository, SqlAlchemyClaimRepository
from app.claims_engine.rule_engine import RuleEngine
from app.claims_engine.service import ClaimService
from app.connectors import (
    ConnectorReviewQueueRepository,
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
from app.reports.job_repo import (
    InMemoryReportRunJobRepository,
    SqlAlchemyReportRunJobRepository,
)
from app.reports.report_repo import SqlAlchemyReportRunRepository
from app.reports.service import ReportRunService
from app.source_registry.provenance_repo import (
    InMemorySourceProvenanceRepository,
    SqlAlchemySourceProvenanceRepository,
)
from app.source_registry.provenance_service import SourceProvenanceService
from app.source_registry.service import SourceService
from app.source_registry.source_repo import InMemorySourceRepository, SqlAlchemySourceRepository


@dataclass
class ApiServices:
    source_service: SourceService
    area_service: AreaService
    evidence_service: EvidenceService
    report_service: ReportRunService
    connector_review_queue_repo: ConnectorReviewQueueRepository
    source_provenance_service: SourceProvenanceService


@dataclass(frozen=True)
class RequestAuthContext:
    workspace_id: UUID
    user_id: UUID


def create_api_services() -> ApiServices:
    source_service = SourceService(InMemorySourceRepository())
    source_provenance_service = SourceProvenanceService(
        source_service=source_service,
        repo=InMemorySourceProvenanceRepository(),
    )
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
        report_job_repo=InMemoryReportRunJobRepository(),
    )
    return ApiServices(
        source_service=source_service,
        area_service=area_service,
        evidence_service=evidence_service,
        report_service=report_service,
        connector_review_queue_repo=InMemoryConnectorReviewQueueRepository(),
        source_provenance_service=source_provenance_service,
    )


def create_db_api_services(
    session: Session,
    *,
    object_store_root: str | Path,
) -> ApiServices:
    source_service = SourceService(SqlAlchemySourceRepository(session))
    source_provenance_service = SourceProvenanceService(
        source_service=source_service,
        repo=SqlAlchemySourceProvenanceRepository(session),
    )
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
        report_job_repo=SqlAlchemyReportRunJobRepository(session),
    )
    return ApiServices(
        source_service=source_service,
        area_service=area_service,
        evidence_service=evidence_service,
        report_service=report_service,
        connector_review_queue_repo=SqlAlchemyConnectorReviewQueueRepository(session),
        source_provenance_service=source_provenance_service,
    )


def get_services(request: Request) -> ApiServices:
    return cast(ApiServices, request.app.state.services)


def get_request_auth_context(
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
    x_user_id: Annotated[str | None, Header(alias="X-User-Id")] = None,
) -> RequestAuthContext:
    if x_workspace_id is None or not x_workspace_id.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Workspace-Id header is required",
        )
    if x_user_id is None or not x_user_id.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-User-Id header is required",
        )
    return RequestAuthContext(
        workspace_id=_parse_uuid_header(x_workspace_id, "X-Workspace-Id"),
        user_id=_parse_uuid_header(x_user_id, "X-User-Id"),
    )


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


def _parse_uuid_header(value: str, header_name: str) -> UUID:
    try:
        return UUID(value.strip())
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"{header_name} header must be a UUID",
        ) from exc


__all__ = [
    "ApiServices",
    "RequestAuthContext",
    "create_api_services",
    "create_db_api_services",
    "get_request_auth_context",
    "get_db_services",
    "get_services",
]
