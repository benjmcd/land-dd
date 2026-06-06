from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from importlib.resources import as_file
from typing import Annotated, Any
from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Header,
    HTTPException,
    Query,
    Request,
    status,
)
from pydantic import BaseModel

from app.api.dependencies import (
    ApiServices,
    RequestAuthContext,
    get_request_auth_context,
    get_services,
)
from app.api.live_connectors import (
    DS_001_REGISTRY_ID,
    DS_002_REGISTRY_ID,
    DS_003_REGISTRY_ID,
    DS_004_REGISTRY_ID,
    orchestrate_fema_nfhl_for_area,
    orchestrate_nwi_for_area,
    orchestrate_ssurgo_for_area,
    orchestrate_usgs_tnm_for_area,
)
from app.api.reports import schedule_report_background
from app.api.reviewer_auth import (
    REVIEWER_SCOPE_CONNECTOR_REVIEW,
    REVIEWER_SCOPE_CONNECTOR_RUN,
    REVIEWER_SCOPE_OPERATIONS_READ,
    REVIEWER_SCOPE_REPORT_RUN,
    ReviewerPrincipal,
    require_reviewer_scope,
)
from app.connectors import (
    ConnectorFixtureQualityProfile,
    FixtureConnectorProtocol,
    FixtureConnectorResultProtocol,
    StaticAccessFixtureConnector,
    StaticFloodFixtureConnector,
    StaticZoningFixtureConnector,
    build_connector_review_handoff,
    build_connector_run_review_packet,
    build_connector_run_review_status,
    build_fixture_workflow_with_public_lane_services,
    evaluate_access_fixture_quality,
    evaluate_flood_fixture_quality,
    evaluate_zoning_fixture_quality,
)
from app.connectors.fema_nfhl import FEMA_NFHL_MAX_FEATURES, FemaNfhlBbox
from app.connectors.fixture_resources import (
    connector_fixture_resource,
    fixture_dataset_contract,
    fixture_dataset_version_contract,
)
from app.connectors.live_jobs import LiveConnectorJobRecord
from app.connectors.nwi import NWI_MAX_FEATURES, NwiBbox
from app.connectors.review_queue import ConnectorReviewQueueItem
from app.connectors.ssurgo import SSURGO_MAX_ROWS, SsurgoBbox
from app.connectors.usgs_tnm import USGS_TNM_MAX_SAMPLE_POINTS, UsgsTnmBbox
from app.domain.connector_contracts import (
    ConnectorReviewQueueItemContract,
    ConnectorRunResultContract,
)
from app.domain.enums import IntentCode, JobStatus

router = APIRouter(prefix="/connector-runs", tags=["connector-runs"])
review_queue_router = APIRouter(
    prefix="/connector-review-queue",
    tags=["connector-review-queue"],
)
ServicesDep = Annotated[ApiServices, Depends(get_services)]
AuthDep = Annotated[RequestAuthContext, Depends(get_request_auth_context)]

_SUPPORTED_FIXTURE_CONNECTOR_NAMES = frozenset(
    {"fixture_access_static", "fixture_flood_static", "fixture_zoning_static"}
)
_FIXTURE_CONNECTORS: dict[str, FixtureConnectorProtocol] = {
    "fixture_access_static": StaticAccessFixtureConnector(),
    "fixture_flood_static": StaticFloodFixtureConnector(),
    "fixture_zoning_static": StaticZoningFixtureConnector(),
}
_QUALITY_EVALUATORS: dict[
    str,
    Callable[[FixtureConnectorResultProtocol], ConnectorFixtureQualityProfile],
] = {
    "fixture_access_static": evaluate_access_fixture_quality,
    "fixture_flood_static": evaluate_flood_fixture_quality,
    "fixture_zoning_static": evaluate_zoning_fixture_quality,
}


def get_reviewer_principal(
    services: ServicesDep,
    reviewer_id: Annotated[str | None, Header(alias="X-Reviewer-Id")] = None,
    reviewer_token: Annotated[str | None, Header(alias="X-Reviewer-Token")] = None,
) -> ReviewerPrincipal:
    return services.reviewer_auth(reviewer_id=reviewer_id, reviewer_token=reviewer_token)


def _get_queue_item_or_404(
    services: ApiServices,
    ingest_run_id: UUID,
) -> ConnectorReviewQueueItem:
    item = services.connector_review_queue.get_by_ingest_run_id(ingest_run_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="connector review queue item not found",
        )
    return item


class ConnectorFixtureQualityIssueResponse(BaseModel):
    code: str
    message: str
    blocking: bool


class ConnectorFixtureQualityResponse(BaseModel):
    passed: bool
    evidence_count: int
    source_failure_count: int
    blocking_issue_count: int
    issues: tuple[ConnectorFixtureQualityIssueResponse, ...]


class ConnectorRunReviewStatusResponse(BaseModel):
    queue_name: str
    disposition: str
    priority: str
    title: str
    summary: str
    connector_name: str
    ingest_run_id: UUID
    area_id: UUID | None
    dataset_version_id: UUID | None
    retrieval_status: str
    review_required: bool
    evidence_created_count: int
    evidence_skipped_count: int
    source_failure_created_count: int
    source_failure_skipped_count: int
    signal_codes: tuple[str, ...]
    tasks: tuple[str, ...]
    quality: ConnectorFixtureQualityResponse


class ConnectorReviewQueueItemResponse(BaseModel):
    job_id: UUID
    ingest_run_id: UUID
    job_type: str
    status: str
    priority: int
    idempotency_key: str
    payload: dict[str, Any]
    created_at: datetime
    attempts: int
    max_attempts: int
    locked_by: str | None
    locked_at: datetime | None
    started_at: datetime | None
    finished_at: datetime | None
    last_error: str | None


class ConnectorReviewActionRequest(BaseModel):
    reason: str | None = None


class ConnectorReviewActionResponse(BaseModel):
    action: str
    ingest_run_id: UUID
    reviewer_id: str
    new_status: str
    reason: str | None
    queue_item: ConnectorReviewQueueItemResponse


class ConnectorReportRunCreateRequest(BaseModel):
    intent_code: IntentCode


class ConnectorReportRunResponse(BaseModel):
    report_run_id: UUID
    status: str
    connector_ingest_run_id: UUID


class FemaNfhlBboxRequest(BaseModel):
    xmin: float
    ymin: float
    xmax: float
    ymax: float


class FemaNfhlQueryRequest(BaseModel):
    area_id: UUID
    bbox: FemaNfhlBboxRequest
    max_features: int = FEMA_NFHL_MAX_FEATURES


class FemaNfhlQueryResponse(BaseModel):
    connector_name: str
    ingest_run_id: UUID
    retrieval_status: str
    row_count: int | None
    error_count: int
    evidence_input_count: int
    evidence_created_count: int
    evidence_skipped_count: int
    source_failure_created_count: int
    source_failure_skipped_count: int
    review_required: bool
    queue_item_status: str
    queue_name: str
    source_registry_id: str
    request_url: str


class UsgsTnmBboxRequest(BaseModel):
    xmin: float
    ymin: float
    xmax: float
    ymax: float


class UsgsTnmQueryRequest(BaseModel):
    area_id: UUID
    bbox: UsgsTnmBboxRequest
    max_sample_points: int = USGS_TNM_MAX_SAMPLE_POINTS


class UsgsTnmQueryResponse(BaseModel):
    connector_name: str
    ingest_run_id: UUID
    retrieval_status: str
    row_count: int | None
    error_count: int
    evidence_input_count: int
    evidence_created_count: int
    evidence_skipped_count: int
    source_failure_created_count: int
    source_failure_skipped_count: int
    review_required: bool
    queue_item_status: str
    queue_name: str
    source_registry_id: str
    request_url: str


class NwiBboxRequest(BaseModel):
    xmin: float
    ymin: float
    xmax: float
    ymax: float


class NwiQueryRequest(BaseModel):
    area_id: UUID
    bbox: NwiBboxRequest
    max_features: int = NWI_MAX_FEATURES


class NwiQueryResponse(BaseModel):
    connector_name: str
    ingest_run_id: UUID
    retrieval_status: str
    row_count: int | None
    error_count: int
    evidence_input_count: int
    evidence_created_count: int
    evidence_skipped_count: int
    source_failure_created_count: int
    source_failure_skipped_count: int
    review_required: bool
    queue_item_status: str
    queue_name: str
    source_registry_id: str
    request_url: str


class SsurgoBboxRequest(BaseModel):
    xmin: float
    ymin: float
    xmax: float
    ymax: float


class SsurgoQueryRequest(BaseModel):
    area_id: UUID
    bbox: SsurgoBboxRequest
    max_rows: int = SSURGO_MAX_ROWS


class SsurgoQueryResponse(BaseModel):
    connector_name: str
    ingest_run_id: UUID
    retrieval_status: str
    row_count: int | None
    error_count: int
    evidence_input_count: int
    evidence_created_count: int
    evidence_skipped_count: int
    source_failure_created_count: int
    source_failure_skipped_count: int
    review_required: bool
    queue_item_status: str
    queue_name: str
    source_registry_id: str
    request_url: str


class LiveConnectorJobResponse(BaseModel):
    job_id: UUID
    area_id: UUID
    source_registry_id: str
    connector_name: str
    status: str
    priority: int
    idempotency_key: str
    max_features: int
    payload: dict[str, Any]
    connector_ingest_run_id: UUID | None = None
    connector_review_status: str | None = None
    request_url: str | None = None


class LiveConnectorSequenceBboxRequest(BaseModel):
    xmin: float
    ymin: float
    xmax: float
    ymax: float


class LiveConnectorSequenceScheduleRequest(BaseModel):
    area_id: UUID
    bbox: LiveConnectorSequenceBboxRequest
    max_sample_points: int = USGS_TNM_MAX_SAMPLE_POINTS
    max_features: int = FEMA_NFHL_MAX_FEATURES
    max_rows: int = SSURGO_MAX_ROWS


class LiveConnectorSequenceScheduleResponse(BaseModel):
    area_id: UUID
    policy_id: str
    jobs: tuple[LiveConnectorJobResponse, ...]


class ConnectorRunRequest(BaseModel):
    connector_name: str
    fixture_key: str


class ConnectorReviewQueueActionRequest(BaseModel):
    reviewer_id: str
    reason: str | None = None
    not_before: datetime | None = None


def _is_safe_fixture_key(key: str) -> bool:
    return bool(key) and all(char.isalnum() or char in ("_", "-") for char in key)


@router.post(
    "",
    response_model=ConnectorRunResultContract,
    status_code=status.HTTP_201_CREATED,
)
def run_fixture_connector(
    request: ConnectorRunRequest,
    services: ServicesDep,
    auth: AuthDep,
) -> ConnectorRunResultContract:
    if request.connector_name not in _SUPPORTED_FIXTURE_CONNECTOR_NAMES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"unsupported connector: {request.connector_name!r}",
        )
    if not _is_safe_fixture_key(request.fixture_key):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="fixture_key must be non-empty alphanumeric with underscores or hyphens",
        )
    fixture_resource = connector_fixture_resource(request.fixture_key)
    if fixture_resource is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"fixture not found: {request.fixture_key!r}",
        )
    connector = _FIXTURE_CONNECTORS[request.connector_name]
    try:
        with as_file(fixture_resource) as fixture_path:
            connector_result = connector.load_fixture(fixture_path)
            _ensure_connector_areas_in_workspace(
                connector_result,
                services=services,
                auth=auth,
            )
            _ensure_fixture_provenance(services)
            workflow = build_fixture_workflow_with_public_lane_services(
                source_provenance_service=services.source_provenance_service,
                evidence_service=services.evidence_service,
                connector=connector,
            )
            result = workflow.ingest_fixture(fixture_path)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    packet = build_connector_run_review_packet(result)
    handoff = build_connector_review_handoff(packet)
    quality = _QUALITY_EVALUATORS[request.connector_name](result.connector_result)
    review_status = build_connector_run_review_status(handoff, quality)
    services.connector_review_statuses[result.connector_result.retrieval_run.ingest_run_id] = (
        review_status
    )
    queue_item = services.connector_review_queue_repo.enqueue_review_status(
        review_status,
        workspace_id=auth.workspace_id,
        requested_by=auth.user_id,
    )
    return ConnectorRunResultContract(
        ingest_run_id=result.connector_result.retrieval_run.ingest_run_id,
        connector_name=result.connector_result.retrieval_run.connector_name,
        retrieval_status=result.connector_result.retrieval_run.status.value,
        evidence_created=len(result.evidence_ingestion.created_evidence),
        evidence_skipped=len(result.evidence_ingestion.skipped_evidence),
        review_required=review_status.review_required,
        queue_job_id=queue_item.job_id,
    )


@review_queue_router.get("", response_model=list[ConnectorReviewQueueItemContract])
def list_connector_review_queue_compat(
    services: ServicesDep,
    auth: AuthDep,
    status_filter: Annotated[
        JobStatus | None,
        Query(alias="status"),
    ] = None,
    connector_name: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ConnectorReviewQueueItemContract]:
    items = services.connector_review_queue_repo.list_connector_runs(
        workspace_id=auth.workspace_id,
        status=status_filter.value if status_filter is not None else None,
        connector_name=connector_name,
        limit=limit,
        offset=offset,
    )
    return [_connector_review_queue_item_contract(item) for item in items]


@review_queue_router.get(
    "/{ingest_run_id}",
    response_model=ConnectorReviewQueueItemContract,
)
def get_connector_review_queue_item_compat(
    ingest_run_id: UUID,
    services: ServicesDep,
    auth: AuthDep,
) -> ConnectorReviewQueueItemContract:
    return _connector_review_queue_item_contract(
        _get_compat_queue_item_or_404(services, auth, ingest_run_id)
    )


@review_queue_router.post(
    "/{ingest_run_id}/approve",
    response_model=ConnectorReviewQueueItemContract,
)
def approve_connector_review_queue_item_compat(
    ingest_run_id: UUID,
    request: ConnectorReviewQueueActionRequest,
    services: ServicesDep,
    auth: AuthDep,
) -> ConnectorReviewQueueItemContract:
    item = _get_compat_queue_item_or_404(services, auth, ingest_run_id)
    return _run_compat_queue_action(
        lambda: services.connector_review_queue_repo.approve_for_connector_qa(
            item.job_id,
            reviewer_id=_compat_reviewer_id(auth, request.reviewer_id),
            reason=request.reason,
        )
    )


@review_queue_router.post(
    "/{ingest_run_id}/reject",
    response_model=ConnectorReviewQueueItemContract,
)
def reject_connector_review_queue_item_compat(
    ingest_run_id: UUID,
    request: ConnectorReviewQueueActionRequest,
    services: ServicesDep,
    auth: AuthDep,
) -> ConnectorReviewQueueItemContract:
    item = _get_compat_queue_item_or_404(services, auth, ingest_run_id)
    return _run_compat_queue_action(
        lambda: services.connector_review_queue_repo.request_fixture_fix(
            item.job_id,
            reviewer_id=_compat_reviewer_id(auth, request.reviewer_id),
            reason=_required_compat_reason(request.reason),
        )
    )


@review_queue_router.post(
    "/{ingest_run_id}/requeue",
    response_model=ConnectorReviewQueueItemContract,
)
def requeue_connector_review_queue_item_compat(
    ingest_run_id: UUID,
    request: ConnectorReviewQueueActionRequest,
    services: ServicesDep,
    auth: AuthDep,
) -> ConnectorReviewQueueItemContract:
    item = _get_compat_queue_item_or_404(services, auth, ingest_run_id)
    return _run_compat_queue_action(
        lambda: services.connector_review_queue_repo.requeue_failed(
            item.job_id,
            reason=_required_compat_reason(request.reason),
            not_before=request.not_before,
            reviewer_id=_compat_reviewer_id(auth, request.reviewer_id),
        )
    )


@review_queue_router.post(
    "/{ingest_run_id}/cancel",
    response_model=ConnectorReviewQueueItemContract,
)
def cancel_connector_review_queue_item_compat(
    ingest_run_id: UUID,
    request: ConnectorReviewQueueActionRequest,
    services: ServicesDep,
    auth: AuthDep,
) -> ConnectorReviewQueueItemContract:
    item = _get_compat_queue_item_or_404(services, auth, ingest_run_id)
    return _run_compat_queue_action(
        lambda: services.connector_review_queue_repo.cancel(
            item.job_id,
            reason=_required_compat_reason(request.reason),
            reviewer_id=_compat_reviewer_id(auth, request.reviewer_id),
        )
    )


def _ensure_connector_areas_in_workspace(
    connector_result: FixtureConnectorResultProtocol,
    *,
    services: ApiServices,
    auth: RequestAuthContext,
) -> None:
    for area_id in {evidence.area_id for evidence in connector_result.evidence_inputs}:
        if not services.area_service.area_is_registered(
            area_id,
            workspace_id=auth.workspace_id,
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="area not found",
            )


def _ensure_fixture_provenance(services: ApiServices) -> None:
    try:
        services.source_provenance_service.ensure_dataset(fixture_dataset_contract())
        services.source_provenance_service.ensure_dataset_version(
            fixture_dataset_version_contract()
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


def _get_compat_queue_item_or_404(
    services: ApiServices,
    auth: RequestAuthContext,
    ingest_run_id: UUID,
) -> ConnectorReviewQueueItem:
    item = services.connector_review_queue_repo.get_by_ingest_run_id(
        ingest_run_id,
        workspace_id=auth.workspace_id,
    )
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="connector review queue item not found",
        )
    return item


def _connector_review_queue_item_contract(
    item: ConnectorReviewQueueItem,
) -> ConnectorReviewQueueItemContract:
    return ConnectorReviewQueueItemContract(
        job_id=item.job_id,
        workspace_id=item.workspace_id,
        ingest_run_id=item.ingest_run_id,
        job_type=item.job_type,
        status=item.status,
        priority=item.priority,
        payload=dict(item.payload),
        created_at=item.created_at,
        not_before=item.not_before,
        attempts=item.attempts,
        max_attempts=item.max_attempts,
        locked_by=item.locked_by,
        locked_at=item.locked_at,
        started_at=item.started_at,
        finished_at=item.finished_at,
        last_error=item.last_error,
    )


def _run_compat_queue_action(
    action: Callable[[], ConnectorReviewQueueItem],
) -> ConnectorReviewQueueItemContract:
    try:
        return _connector_review_queue_item_contract(action())
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


def _compat_reviewer_id(auth: RequestAuthContext, reviewer_id: str) -> str:
    reviewer = reviewer_id.strip()
    if not reviewer:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="reviewer_id is required",
        )
    if reviewer != str(auth.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="reviewer_id does not match authenticated user",
        )
    return reviewer


def _required_compat_reason(reason: str | None) -> str:
    if reason is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="connector review queue reason is required",
        )
    return reason


@router.post(
    "/fema-nfhl/query-bbox",
    response_model=FemaNfhlQueryResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def query_fema_nfhl_bbox(
    request: FemaNfhlQueryRequest,
    services: ServicesDep,
    principal: Annotated[ReviewerPrincipal, Depends(get_reviewer_principal)],
) -> dict[str, object]:
    require_reviewer_scope(principal, REVIEWER_SCOPE_CONNECTOR_RUN)
    try:
        area = services.area_service.get(request.area_id)
        if area is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Area '{request.area_id}' is not registered",
            )
        area_for_bbox = _area_with_bbox_geometry(
            area=area,
            xmin=request.bbox.xmin,
            ymin=request.bbox.ymin,
            xmax=request.bbox.xmax,
            ymax=request.bbox.ymax,
        )
        result = orchestrate_fema_nfhl_for_area(
            services=services,
            area=area_for_bbox,
            max_features=request.max_features,
        )
        queue_item = result.queue_item
        review_status = services.connector_review_statuses[result.ingest_run_id]
        packet = review_status.handoff.packet
        handoff = review_status.handoff
    except HTTPException:
        raise

    return {
        "connector_name": packet.connector_name,
        "ingest_run_id": packet.ingest_run_id,
        "retrieval_status": packet.retrieval_status.value,
        "row_count": packet.row_count,
        "error_count": packet.error_count,
        "evidence_input_count": packet.evidence_input_count,
        "evidence_created_count": packet.evidence_created_count,
        "evidence_skipped_count": packet.evidence_skipped_count,
        "source_failure_created_count": packet.source_failure_created_count,
        "source_failure_skipped_count": packet.source_failure_skipped_count,
        "review_required": review_status.review_required,
        "queue_item_status": queue_item.status.value,
        "queue_name": handoff.queue_name,
        "source_registry_id": DS_002_REGISTRY_ID,
        "request_url": result.request_url,
    }


@router.post(
    "/usgs-tnm/query-bbox",
    response_model=UsgsTnmQueryResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def query_usgs_tnm_bbox(
    request: UsgsTnmQueryRequest,
    services: ServicesDep,
    principal: Annotated[ReviewerPrincipal, Depends(get_reviewer_principal)],
) -> dict[str, object]:
    require_reviewer_scope(principal, REVIEWER_SCOPE_CONNECTOR_RUN)
    try:
        area = services.area_service.get(request.area_id)
        if area is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Area '{request.area_id}' is not registered",
            )
        area_for_bbox = _area_with_bbox_geometry(
            area=area,
            xmin=request.bbox.xmin,
            ymin=request.bbox.ymin,
            xmax=request.bbox.xmax,
            ymax=request.bbox.ymax,
        )
        result = orchestrate_usgs_tnm_for_area(
            services=services,
            area=area_for_bbox,
            max_sample_points=request.max_sample_points,
        )
        queue_item = result.queue_item
        review_status = services.connector_review_statuses[result.ingest_run_id]
        packet = review_status.handoff.packet
        handoff = review_status.handoff
    except HTTPException:
        raise

    return {
        "connector_name": packet.connector_name,
        "ingest_run_id": packet.ingest_run_id,
        "retrieval_status": packet.retrieval_status.value,
        "row_count": packet.row_count,
        "error_count": packet.error_count,
        "evidence_input_count": packet.evidence_input_count,
        "evidence_created_count": packet.evidence_created_count,
        "evidence_skipped_count": packet.evidence_skipped_count,
        "source_failure_created_count": packet.source_failure_created_count,
        "source_failure_skipped_count": packet.source_failure_skipped_count,
        "review_required": review_status.review_required,
        "queue_item_status": queue_item.status.value,
        "queue_name": handoff.queue_name,
        "source_registry_id": DS_001_REGISTRY_ID,
        "request_url": result.request_url,
    }


@router.post(
    "/ssurgo/query-bbox",
    response_model=SsurgoQueryResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def query_ssurgo_bbox(
    request: SsurgoQueryRequest,
    services: ServicesDep,
    principal: Annotated[ReviewerPrincipal, Depends(get_reviewer_principal)],
) -> dict[str, object]:
    require_reviewer_scope(principal, REVIEWER_SCOPE_CONNECTOR_RUN)
    try:
        area = services.area_service.get(request.area_id)
        if area is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Area '{request.area_id}' is not registered",
            )
        area_for_bbox = _area_with_bbox_geometry(
            area=area,
            xmin=request.bbox.xmin,
            ymin=request.bbox.ymin,
            xmax=request.bbox.xmax,
            ymax=request.bbox.ymax,
        )
        result = orchestrate_ssurgo_for_area(
            services=services,
            area=area_for_bbox,
            max_rows=request.max_rows,
        )
        queue_item = result.queue_item
        review_status = services.connector_review_statuses[result.ingest_run_id]
        packet = review_status.handoff.packet
        handoff = review_status.handoff
    except HTTPException:
        raise

    return {
        "connector_name": packet.connector_name,
        "ingest_run_id": packet.ingest_run_id,
        "retrieval_status": packet.retrieval_status.value,
        "row_count": packet.row_count,
        "error_count": packet.error_count,
        "evidence_input_count": packet.evidence_input_count,
        "evidence_created_count": packet.evidence_created_count,
        "evidence_skipped_count": packet.evidence_skipped_count,
        "source_failure_created_count": packet.source_failure_created_count,
        "source_failure_skipped_count": packet.source_failure_skipped_count,
        "review_required": review_status.review_required,
        "queue_item_status": queue_item.status.value,
        "queue_name": handoff.queue_name,
        "source_registry_id": DS_003_REGISTRY_ID,
        "request_url": result.request_url,
    }


@router.post(
    "/nwi/query-bbox",
    response_model=NwiQueryResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def query_nwi_bbox(
    request: NwiQueryRequest,
    services: ServicesDep,
    principal: Annotated[ReviewerPrincipal, Depends(get_reviewer_principal)],
) -> dict[str, object]:
    require_reviewer_scope(principal, REVIEWER_SCOPE_CONNECTOR_RUN)
    try:
        area = services.area_service.get(request.area_id)
        if area is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Area '{request.area_id}' is not registered",
            )
        area_for_bbox = _area_with_bbox_geometry(
            area=area,
            xmin=request.bbox.xmin,
            ymin=request.bbox.ymin,
            xmax=request.bbox.xmax,
            ymax=request.bbox.ymax,
        )
        result = orchestrate_nwi_for_area(
            services=services,
            area=area_for_bbox,
            max_features=request.max_features,
        )
        queue_item = result.queue_item
        review_status = services.connector_review_statuses[result.ingest_run_id]
        packet = review_status.handoff.packet
        handoff = review_status.handoff
    except HTTPException:
        raise

    return {
        "connector_name": packet.connector_name,
        "ingest_run_id": packet.ingest_run_id,
        "retrieval_status": packet.retrieval_status.value,
        "row_count": packet.row_count,
        "error_count": packet.error_count,
        "evidence_input_count": packet.evidence_input_count,
        "evidence_created_count": packet.evidence_created_count,
        "evidence_skipped_count": packet.evidence_skipped_count,
        "source_failure_created_count": packet.source_failure_created_count,
        "source_failure_skipped_count": packet.source_failure_skipped_count,
        "review_required": review_status.review_required,
        "queue_item_status": queue_item.status.value,
        "queue_name": handoff.queue_name,
        "source_registry_id": DS_004_REGISTRY_ID,
        "request_url": result.request_url,
    }


def _area_with_bbox_geometry(
    *,
    area: Any,
    xmin: float,
    ymin: float,
    xmax: float,
    ymax: float,
) -> Any:
    return area.model_copy(
        update={
            "geom_geojson": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [xmin, ymin],
                        [xmax, ymin],
                        [xmax, ymax],
                        [xmin, ymax],
                        [xmin, ymin],
                    ]
                ],
            }
        }
    )


def _validate_live_sequence_limits(request: LiveConnectorSequenceScheduleRequest) -> None:
    if request.max_sample_points <= 0 or request.max_sample_points > USGS_TNM_MAX_SAMPLE_POINTS:
        raise ValueError(f"max_sample_points must be between 1 and {USGS_TNM_MAX_SAMPLE_POINTS}")
    if request.max_features <= 0 or request.max_features > FEMA_NFHL_MAX_FEATURES:
        raise ValueError(f"max_features must be between 1 and {FEMA_NFHL_MAX_FEATURES}")
    if request.max_rows <= 0 or request.max_rows > SSURGO_MAX_ROWS:
        raise ValueError(f"max_rows must be between 1 and {SSURGO_MAX_ROWS}")


@router.post(
    "/live-sequence/schedule-bbox",
    response_model=LiveConnectorSequenceScheduleResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def schedule_live_connector_sequence_bbox(
    request: LiveConnectorSequenceScheduleRequest,
    services: ServicesDep,
    principal: Annotated[ReviewerPrincipal, Depends(get_reviewer_principal)],
) -> dict[str, object]:
    require_reviewer_scope(principal, REVIEWER_SCOPE_CONNECTOR_RUN)
    area = services.area_service.get(request.area_id)
    if area is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Area '{request.area_id}' is not registered",
        )
    try:
        usgs_tnm_bbox = UsgsTnmBbox(
            xmin=request.bbox.xmin,
            ymin=request.bbox.ymin,
            xmax=request.bbox.xmax,
            ymax=request.bbox.ymax,
        )
        fema_nfhl_bbox = FemaNfhlBbox(
            xmin=request.bbox.xmin,
            ymin=request.bbox.ymin,
            xmax=request.bbox.xmax,
            ymax=request.bbox.ymax,
        )
        nwi_bbox = NwiBbox(
            xmin=request.bbox.xmin,
            ymin=request.bbox.ymin,
            xmax=request.bbox.xmax,
            ymax=request.bbox.ymax,
        )
        ssurgo_bbox = SsurgoBbox(
            xmin=request.bbox.xmin,
            ymin=request.bbox.ymin,
            xmax=request.bbox.xmax,
            ymax=request.bbox.ymax,
        )
        _validate_live_sequence_limits(request)
        jobs = (
            services.live_connector_jobs.enqueue_usgs_tnm(
                area_id=request.area_id,
                bbox=usgs_tnm_bbox,
                max_sample_points=request.max_sample_points,
            ),
            services.live_connector_jobs.enqueue_fema_nfhl(
                area_id=request.area_id,
                bbox=fema_nfhl_bbox,
                max_features=request.max_features,
            ),
            services.live_connector_jobs.enqueue_nwi(
                area_id=request.area_id,
                bbox=nwi_bbox,
                max_features=request.max_features,
            ),
            services.live_connector_jobs.enqueue_ssurgo(
                area_id=request.area_id,
                bbox=ssurgo_bbox,
                max_rows=request.max_rows,
            ),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    return {
        "area_id": request.area_id,
        "policy_id": "reviewed_live_sequence_ds001_ds002_ds004_ds003_v1",
        "jobs": tuple(_live_connector_job_response(job) for job in jobs),
    }


@router.post(
    "/fema-nfhl/schedule-bbox",
    response_model=LiveConnectorJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def schedule_fema_nfhl_bbox(
    request: FemaNfhlQueryRequest,
    services: ServicesDep,
    principal: Annotated[ReviewerPrincipal, Depends(get_reviewer_principal)],
) -> dict[str, object]:
    require_reviewer_scope(principal, REVIEWER_SCOPE_CONNECTOR_RUN)
    area = services.area_service.get(request.area_id)
    if area is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Area '{request.area_id}' is not registered",
        )
    try:
        bbox = FemaNfhlBbox(
            xmin=request.bbox.xmin,
            ymin=request.bbox.ymin,
            xmax=request.bbox.xmax,
            ymax=request.bbox.ymax,
        )
        job = services.live_connector_jobs.enqueue_fema_nfhl(
            area_id=request.area_id,
            bbox=bbox,
            max_features=request.max_features,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    return _live_connector_job_response(job)


@router.post(
    "/usgs-tnm/schedule-bbox",
    response_model=LiveConnectorJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def schedule_usgs_tnm_bbox(
    request: UsgsTnmQueryRequest,
    services: ServicesDep,
    principal: Annotated[ReviewerPrincipal, Depends(get_reviewer_principal)],
) -> dict[str, object]:
    require_reviewer_scope(principal, REVIEWER_SCOPE_CONNECTOR_RUN)
    area = services.area_service.get(request.area_id)
    if area is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Area '{request.area_id}' is not registered",
        )
    try:
        bbox = UsgsTnmBbox(
            xmin=request.bbox.xmin,
            ymin=request.bbox.ymin,
            xmax=request.bbox.xmax,
            ymax=request.bbox.ymax,
        )
        job = services.live_connector_jobs.enqueue_usgs_tnm(
            area_id=request.area_id,
            bbox=bbox,
            max_sample_points=request.max_sample_points,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    return _live_connector_job_response(job)


@router.post(
    "/nwi/schedule-bbox",
    response_model=LiveConnectorJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def schedule_nwi_bbox(
    request: NwiQueryRequest,
    services: ServicesDep,
    principal: Annotated[ReviewerPrincipal, Depends(get_reviewer_principal)],
) -> dict[str, object]:
    require_reviewer_scope(principal, REVIEWER_SCOPE_CONNECTOR_RUN)
    area = services.area_service.get(request.area_id)
    if area is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Area '{request.area_id}' is not registered",
        )
    try:
        bbox = NwiBbox(
            xmin=request.bbox.xmin,
            ymin=request.bbox.ymin,
            xmax=request.bbox.xmax,
            ymax=request.bbox.ymax,
        )
        job = services.live_connector_jobs.enqueue_nwi(
            area_id=request.area_id,
            bbox=bbox,
            max_features=request.max_features,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    return _live_connector_job_response(job)


@router.post(
    "/ssurgo/schedule-bbox",
    response_model=LiveConnectorJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def schedule_ssurgo_bbox(
    request: SsurgoQueryRequest,
    services: ServicesDep,
    principal: Annotated[ReviewerPrincipal, Depends(get_reviewer_principal)],
) -> dict[str, object]:
    require_reviewer_scope(principal, REVIEWER_SCOPE_CONNECTOR_RUN)
    area = services.area_service.get(request.area_id)
    if area is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Area '{request.area_id}' is not registered",
        )
    try:
        bbox = SsurgoBbox(
            xmin=request.bbox.xmin,
            ymin=request.bbox.ymin,
            xmax=request.bbox.xmax,
            ymax=request.bbox.ymax,
        )
        job = services.live_connector_jobs.enqueue_ssurgo(
            area_id=request.area_id,
            bbox=bbox,
            max_rows=request.max_rows,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    return _live_connector_job_response(job)


@router.get(
    "/live-jobs/{job_id}",
    response_model=LiveConnectorJobResponse,
)
def get_live_connector_job(
    job_id: UUID,
    services: ServicesDep,
    principal: Annotated[ReviewerPrincipal, Depends(get_reviewer_principal)],
) -> dict[str, object]:
    require_reviewer_scope(principal, REVIEWER_SCOPE_OPERATIONS_READ)
    job = services.live_connector_jobs.get(job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="live connector job not found",
        )
    return _live_connector_job_response(job)


@router.get(
    "/{ingest_run_id}/review-status",
    response_model=ConnectorRunReviewStatusResponse,
)
def get_connector_run_review_status(
    ingest_run_id: UUID,
    services: ServicesDep,
) -> dict[str, object]:
    review_status = services.connector_review_statuses.get(ingest_run_id)
    if review_status is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="connector run review status not found",
        )
    return review_status.to_status_record()


@router.get(
    "/{ingest_run_id}/review-queue",
    response_model=ConnectorReviewQueueItemResponse,
)
def get_connector_review_queue_item(
    ingest_run_id: UUID,
    services: ServicesDep,
) -> dict[str, object]:
    queue_item = services.connector_review_queue.get_by_ingest_run_id(ingest_run_id)
    if queue_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="connector review queue item not found",
        )
    return _queue_item_response(queue_item)


@router.post(
    "/{ingest_run_id}/review-actions/approve_for_connector_qa",
    response_model=ConnectorReviewActionResponse,
)
def approve_for_connector_qa(
    ingest_run_id: UUID,
    services: ServicesDep,
    principal: Annotated[ReviewerPrincipal, Depends(get_reviewer_principal)],
    request: ConnectorReviewActionRequest | None = None,
) -> dict[str, object]:
    require_reviewer_scope(principal, REVIEWER_SCOPE_CONNECTOR_REVIEW)
    item = _get_queue_item_or_404(services, ingest_run_id)
    reason = _optional_action_reason(request)
    try:
        updated_item = services.connector_review_queue.approve_for_connector_qa(
            item.job_id,
            reviewer_id=principal.reviewer_id,
            reason=reason,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="queue item cannot be approved",
        ) from None
    return _review_action_response(
        action="approve_for_connector_qa",
        ingest_run_id=ingest_run_id,
        reviewer_id=principal.reviewer_id,
        reason=reason,
        queue_item=updated_item,
    )


@router.post(
    "/{ingest_run_id}/review-actions/request_fixture_fix",
    response_model=ConnectorReviewActionResponse,
)
def request_fixture_fix(
    ingest_run_id: UUID,
    services: ServicesDep,
    principal: Annotated[ReviewerPrincipal, Depends(get_reviewer_principal)],
    request: ConnectorReviewActionRequest | None = None,
) -> dict[str, object]:
    require_reviewer_scope(principal, REVIEWER_SCOPE_CONNECTOR_REVIEW)
    item = _get_queue_item_or_404(services, ingest_run_id)
    reason = _required_action_reason(request)
    try:
        updated_item = services.connector_review_queue.request_fixture_fix(
            item.job_id,
            reviewer_id=principal.reviewer_id,
            reason=reason,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="queue item cannot request fixture fix",
        ) from None
    return _review_action_response(
        action="request_fixture_fix",
        ingest_run_id=ingest_run_id,
        reviewer_id=principal.reviewer_id,
        reason=reason,
        queue_item=updated_item,
    )


@router.post(
    "/{ingest_run_id}/review-actions/requeue_after_fix",
    response_model=ConnectorReviewActionResponse,
)
def requeue_after_fix(
    ingest_run_id: UUID,
    services: ServicesDep,
    principal: Annotated[ReviewerPrincipal, Depends(get_reviewer_principal)],
    request: ConnectorReviewActionRequest | None = None,
) -> dict[str, object]:
    require_reviewer_scope(principal, REVIEWER_SCOPE_CONNECTOR_REVIEW)
    item = _get_queue_item_or_404(services, ingest_run_id)
    reason = _required_action_reason(request)
    try:
        updated_item = services.connector_review_queue.requeue_failed(
            item.job_id,
            reason=reason,
            reviewer_id=principal.reviewer_id,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="queue item cannot be requeued",
        ) from None
    return _review_action_response(
        action="requeue_after_fix",
        ingest_run_id=ingest_run_id,
        reviewer_id=principal.reviewer_id,
        reason=reason,
        queue_item=updated_item,
    )


@router.post(
    "/{ingest_run_id}/review-actions/cancel_review",
    response_model=ConnectorReviewActionResponse,
)
def cancel_review(
    ingest_run_id: UUID,
    services: ServicesDep,
    principal: Annotated[ReviewerPrincipal, Depends(get_reviewer_principal)],
    request: ConnectorReviewActionRequest | None = None,
) -> dict[str, object]:
    require_reviewer_scope(principal, REVIEWER_SCOPE_CONNECTOR_REVIEW)
    item = _get_queue_item_or_404(services, ingest_run_id)
    reason = _required_action_reason(request)
    try:
        updated_item = services.connector_review_queue.cancel(
            item.job_id,
            reason=reason,
            reviewer_id=principal.reviewer_id,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="queue item cannot be cancelled",
        ) from None
    return _review_action_response(
        action="cancel_review",
        ingest_run_id=ingest_run_id,
        reviewer_id=principal.reviewer_id,
        reason=reason,
        queue_item=updated_item,
    )


@router.post(
    "/{ingest_run_id}/report-runs",
    response_model=ConnectorReportRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_report_run_from_approved_connector(
    ingest_run_id: UUID,
    request: ConnectorReportRunCreateRequest,
    background_tasks: BackgroundTasks,
    request_context: Request,
    services: ServicesDep,
    principal: Annotated[ReviewerPrincipal, Depends(get_reviewer_principal)],
) -> ConnectorReportRunResponse:
    require_reviewer_scope(principal, REVIEWER_SCOPE_REPORT_RUN)
    item = _get_queue_item_or_404(services, ingest_run_id)
    if not _queue_item_approved_for_report(item):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="connector review item is not approved for report generation",
        )
    area_id = _area_id_from_queue_item(item)
    area = services.area_service.get(area_id)
    if area is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="connector review item area is not registered",
        )
    job = services.async_report_jobs.create(
        area_id=area_id,
        intent_code=request.intent_code,
    )
    schedule_report_background(
        background_tasks=background_tasks,
        request_context=request_context,
        services=services,
        report_run_id=job.report_run_id,
        area_id=area_id,
        intent_code=request.intent_code,
    )
    return ConnectorReportRunResponse(
        report_run_id=job.report_run_id,
        status="queued",
        connector_ingest_run_id=ingest_run_id,
    )


def _queue_item_response(queue_item: ConnectorReviewQueueItem) -> dict[str, object]:
    return {
        "job_id": queue_item.job_id,
        "ingest_run_id": queue_item.ingest_run_id,
        "job_type": queue_item.job_type,
        "status": queue_item.status.value,
        "priority": queue_item.priority,
        "idempotency_key": queue_item.idempotency_key,
        "payload": queue_item.payload,
        "created_at": queue_item.created_at,
        "attempts": queue_item.attempts,
        "max_attempts": queue_item.max_attempts,
        "locked_by": queue_item.locked_by,
        "locked_at": queue_item.locked_at,
        "started_at": queue_item.started_at,
        "finished_at": queue_item.finished_at,
        "last_error": queue_item.last_error,
    }


def _live_connector_job_response(
    job: LiveConnectorJobRecord,
) -> dict[str, object]:
    return {
        "job_id": job.job_id,
        "area_id": job.area_id,
        "source_registry_id": job.source_registry_id,
        "connector_name": job.connector_name,
        "status": job.status.value,
        "priority": job.priority,
        "idempotency_key": job.idempotency_key,
        "max_features": job.max_features,
        "payload": job.payload,
        "connector_ingest_run_id": job.connector_ingest_run_id,
        "connector_review_status": job.connector_review_status,
        "request_url": job.request_url,
    }


def _review_action_response(
    *,
    action: str,
    ingest_run_id: UUID,
    reviewer_id: str,
    reason: str | None,
    queue_item: ConnectorReviewQueueItem,
) -> dict[str, object]:
    return {
        "action": action,
        "ingest_run_id": ingest_run_id,
        "reviewer_id": reviewer_id,
        "new_status": queue_item.status.value,
        "reason": reason,
        "queue_item": _queue_item_response(queue_item),
    }


def _queue_item_approved_for_report(queue_item: ConnectorReviewQueueItem) -> bool:
    if queue_item.status != JobStatus.SUCCEEDED:
        return False
    decision = queue_item.payload.get("review_decision")
    if not isinstance(decision, dict):
        return False
    return decision.get("action") == "approve_for_connector_qa"


def _area_id_from_queue_item(queue_item: ConnectorReviewQueueItem) -> UUID:
    value = queue_item.payload.get("area_id")
    if not isinstance(value, str) or not value.strip():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="connector review item does not include an area_id for report resume",
        )
    try:
        return UUID(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="connector review item has an invalid area_id for report resume",
        ) from exc


def _required_action_reason(request: ConnectorReviewActionRequest | None) -> str:
    reason = _optional_action_reason(request)
    if reason is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="reason is required",
        )
    return reason


def _optional_action_reason(request: ConnectorReviewActionRequest | None) -> str | None:
    if request is None or request.reason is None:
        return None
    reason = request.reason.strip()
    if not reason:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="reason is required",
        )
    return reason
