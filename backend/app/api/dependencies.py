from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, cast
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.report_auth import (
    MIN_SECRET_LENGTH,
    ReportIdentityClaims,
    verify_report_identity_token,
)
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
from app.connectors.brunswick_parcels import JsonFetcher as BrunswickParcelsJsonFetcher
from app.connectors.buncombe_parcels import JsonFetcher as BuncombeParcelsJsonFetcher
from app.connectors.chatham_parcels import JsonFetcher as ChathamParcelsJsonFetcher
from app.connectors.epa_echo import JsonFetcher as EpaEchoJsonFetcher
from app.connectors.fcc_broadband import JsonFetcher as FccBroadbandJsonFetcher
from app.connectors.fema_nfhl import JsonFetcher
from app.connectors.live_jobs import (
    InMemoryLiveConnectorJobStore,
    LiveConnectorJobStoreProtocol,
    SqlAlchemyLiveConnectorJobStore,
)
from app.connectors.nwi import NwiJsonFetcher
from app.connectors.osm_road_access import JsonFetcher as OsmRoadAccessJsonFetcher
from app.connectors.ssurgo import SsurgoJsonFetcher
from app.connectors.usgs_tnm import UsgsTnmJsonFetcher
from app.connectors.usgs_water_monitoring import JsonFetcher as UsgsWaterJsonFetcher
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
    chatham_parcels_fetch_json: ChathamParcelsJsonFetcher | None = None
    buncombe_parcels_fetch_json: BuncombeParcelsJsonFetcher | None = None
    brunswick_parcels_fetch_json: BrunswickParcelsJsonFetcher | None = None
    osm_road_access_fetch_json: OsmRoadAccessJsonFetcher | None = None
    usgs_water_fetch_json: UsgsWaterJsonFetcher | None = None
    epa_echo_fetch_json: EpaEchoJsonFetcher | None = None
    fcc_broadband_fetch_json: FccBroadbandJsonFetcher | None = None

    @property
    def connector_review_queue_repo(self) -> ConnectorReviewQueueRepository:
        return self.connector_review_queue


@dataclass(frozen=True)
class RequestAuthContext:
    workspace_id: UUID
    user_id: UUID


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


def get_request_auth_context(
    request: Request,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
    x_user_id: Annotated[str | None, Header(alias="X-User-Id")] = None,
) -> RequestAuthContext:
    settings = cast(Settings, request.app.state.settings)
    if settings.report_auth_mode == "signed_token":
        return _get_signed_token_auth_context(
            settings,
            authorization=authorization,
            x_workspace_id=x_workspace_id,
            x_user_id=x_user_id,
        )
    return _get_trusted_header_auth_context(
        x_workspace_id=x_workspace_id,
        x_user_id=x_user_id,
    )


def _get_trusted_header_auth_context(
    *,
    x_workspace_id: str | None,
    x_user_id: str | None,
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


def _get_signed_token_auth_context(
    settings: Settings,
    *,
    authorization: str | None,
    x_workspace_id: str | None,
    x_user_id: str | None,
) -> RequestAuthContext:
    if (
        settings.report_identity_token_secret is None
        or len(settings.report_identity_token_secret.strip()) < MIN_SECRET_LENGTH
    ):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "report identity token secret must be configured with "
                f"at least {MIN_SECRET_LENGTH} characters"
            ),
        )
    token = _bearer_token(authorization)
    try:
        claims = verify_report_identity_token(
            token,
            secret=settings.report_identity_token_secret,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    _enforce_matching_identity_headers(
        claims,
        x_workspace_id=x_workspace_id,
        x_user_id=x_user_id,
    )
    return RequestAuthContext(workspace_id=claims.workspace_id, user_id=claims.user_id)


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


def _parse_uuid_header(value: str, header_name: str) -> UUID:
    try:
        return UUID(value.strip())
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"{header_name} header must be a UUID",
        ) from exc


def _bearer_token(authorization: str | None) -> str:
    if authorization is None or not authorization.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization bearer token is required",
        )
    scheme, separator, token = authorization.strip().partition(" ")
    if scheme.lower() != "bearer" or not separator or not token.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization bearer token is required",
        )
    return token.strip()


def _enforce_matching_identity_headers(
    claims: ReportIdentityClaims,
    *,
    x_workspace_id: str | None,
    x_user_id: str | None,
) -> None:
    if x_workspace_id is not None and x_workspace_id.strip():
        workspace_id = _parse_uuid_header(x_workspace_id, "X-Workspace-Id")
        if workspace_id != claims.workspace_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="X-Workspace-Id header does not match bearer token",
            )
    if x_user_id is not None and x_user_id.strip():
        user_id = _parse_uuid_header(x_user_id, "X-User-Id")
        if user_id != claims.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="X-User-Id header does not match bearer token",
            )


__all__ = [
    "ApiServices",
    "RequestAuthContext",
    "create_api_services",
    "create_db_api_services",
    "get_request_auth_context",
    "get_db_services",
    "get_services",
]
