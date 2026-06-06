from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, cast
from uuid import UUID

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.api.reviewer_auth import LocalServiceAccountReviewerAuth
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
from app.connectors.fema_nfhl import JsonFetcher
from app.connectors.live_jobs import (
    InMemoryLiveConnectorJobStore,
    LiveConnectorJobStoreProtocol,
    SqlAlchemyLiveConnectorJobStore,
)
from app.connectors.nwi import NwiJsonFetcher
from app.connectors.ssurgo import SsurgoJsonFetcher
from app.connectors.usgs_tnm import UsgsTnmJsonFetcher
from app.core.config import Settings, get_settings
from app.db.session import get_db_session
from app.evidence_ledger.evidence_repo import (
    InMemoryEvidenceRepository,
    SqlAlchemyEvidenceRepository,
)
from app.evidence_ledger.service import EvidenceService
from app.reports.adapters import AreaServiceProtocolAdapter, SourceServiceProtocolAdapter
from app.reports.job_store import (
    AsyncReportJobStore,
    AsyncReportJobStoreProtocol,
    SqlAlchemyAsyncReportJobStore,
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
    connector_review_statuses: dict[UUID, ConnectorRunReviewStatus]
    connector_review_queue: ConnectorReviewQueueRepository
    live_connector_jobs: LiveConnectorJobStoreProtocol
    async_report_jobs: AsyncReportJobStoreProtocol
    reviewer_auth: LocalServiceAccountReviewerAuth
    source_provenance_service: SourceProvenanceService
    fema_nfhl_fetch_json: JsonFetcher | None = None
    usgs_tnm_fetch_json: UsgsTnmJsonFetcher | None = None
    nwi_fetch_json: NwiJsonFetcher | None = None
    ssurgo_fetch_json: SsurgoJsonFetcher | None = None


def create_api_services(settings: Settings | None = None) -> ApiServices:
    resolved = settings or get_settings()
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
    connector_review_queue = InMemoryConnectorReviewQueueRepository()
    report_service = ReportRunService(
        source_service=source_service,
        area_service=area_service,
        evidence_service=evidence_service,
        claim_service=claim_service,
        rule_engine=RuleEngine.from_file(),
        connector_review_queue=connector_review_queue,
    )
    return ApiServices(
        source_service=source_service,
        area_service=area_service,
        evidence_service=evidence_service,
        report_service=report_service,
        connector_review_statuses={},
        connector_review_queue=connector_review_queue,
        live_connector_jobs=InMemoryLiveConnectorJobStore(),
        async_report_jobs=AsyncReportJobStore(),
        reviewer_auth=LocalServiceAccountReviewerAuth(
            resolved.parsed_reviewer_accounts(),
            resolved.parsed_reviewer_account_scopes(),
        ),
        source_provenance_service=source_provenance_service,
    )


def create_db_api_services(
    session: Session,
    *,
    object_store_root: str | Path,
    settings: Settings | None = None,
) -> ApiServices:
    resolved = settings or get_settings()
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
    connector_review_queue = SqlAlchemyConnectorReviewQueueRepository(session)
    report_service = ReportRunService(
        source_service=source_service,
        area_service=area_service,
        evidence_service=evidence_service,
        claim_service=claim_service,
        rule_engine=RuleEngine.from_file(),
        report_repo=SqlAlchemyReportRunRepository(session, object_store_root),
        connector_review_queue=connector_review_queue,
    )
    return ApiServices(
        source_service=source_service,
        area_service=area_service,
        evidence_service=evidence_service,
        report_service=report_service,
        connector_review_statuses={},
        connector_review_queue=connector_review_queue,
        live_connector_jobs=SqlAlchemyLiveConnectorJobStore(session),
        async_report_jobs=SqlAlchemyAsyncReportJobStore(),
        reviewer_auth=LocalServiceAccountReviewerAuth(
            resolved.parsed_reviewer_accounts(),
            resolved.parsed_reviewer_account_scopes(),
        ),
        source_provenance_service=source_provenance_service,
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
            settings=cast(Settings, request.app.state.settings),
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
