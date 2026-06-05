from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from importlib.resources import as_file
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.api.dependencies import (
    ApiServices,
    RequestAuthContext,
    get_request_auth_context,
    get_services,
)
from app.connectors import (
    ConnectorFixtureQualityProfile,
    ConnectorReviewQueueItem,
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
from app.connectors.fixture_resources import (
    connector_fixture_resource,
    fixture_dataset_contract,
    fixture_dataset_version_contract,
)
from app.domain.connector_contracts import (
    ConnectorReviewQueueItemContract,
    ConnectorRunResultContract,
)
from app.domain.enums import JobStatus

router = APIRouter(prefix="/connector-review-queue", tags=["connector-review-queue"])
runs_router = APIRouter(prefix="/connector-runs", tags=["connector-runs"])
ServicesDep = Annotated[ApiServices, Depends(get_services)]
AuthDep = Annotated[RequestAuthContext, Depends(get_request_auth_context)]

_SUPPORTED_CONNECTOR_NAMES: frozenset[str] = frozenset(
    {"fixture_access_static", "fixture_flood_static", "fixture_zoning_static"}
)

_CONNECTOR_INSTANCES: dict[str, FixtureConnectorProtocol] = {
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


def _is_safe_fixture_key(key: str) -> bool:
    return bool(key) and all(c.isalnum() or c in ("_", "-") for c in key)


@router.get("", response_model=list[ConnectorReviewQueueItemContract])
def list_connector_review_queue(
    services: ServicesDep,
    auth: AuthDep,
    status: JobStatus | None = None,
    connector_name: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[ConnectorReviewQueueItemContract]:
    items = services.connector_review_queue_repo.list_connector_runs(
        workspace_id=auth.workspace_id,
        status=status.value if status is not None else None,
        connector_name=connector_name,
        limit=limit,
        offset=offset,
    )
    return [_queue_item_contract(item) for item in items]


@router.get("/{ingest_run_id}", response_model=ConnectorReviewQueueItemContract)
def get_connector_review_queue_item(
    ingest_run_id: UUID,
    services: ServicesDep,
    auth: AuthDep,
) -> ConnectorReviewQueueItemContract:
    item = _get_queue_item_or_404(ingest_run_id, services, auth)
    return _queue_item_contract(item)


def _queue_item_contract(
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


def _get_queue_item_or_404(
    ingest_run_id: UUID,
    services: ApiServices,
    auth: RequestAuthContext,
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


class ConnectorReviewActionRequest(BaseModel):
    reviewer_id: str
    reason: str | None = None
    not_before: datetime | None = None


@router.post("/{ingest_run_id}/approve", response_model=ConnectorReviewQueueItemContract)
def approve_connector_review_queue_item(
    ingest_run_id: UUID,
    request: ConnectorReviewActionRequest,
    services: ServicesDep,
    auth: AuthDep,
) -> ConnectorReviewQueueItemContract:
    item = _get_queue_item_or_404(ingest_run_id, services, auth)
    return _run_queue_action(
        lambda: services.connector_review_queue_repo.approve_review(
            item.job_id,
            reviewer_id=_reviewer_id(auth, request.reviewer_id),
            reason=request.reason,
        )
    )


@router.post("/{ingest_run_id}/reject", response_model=ConnectorReviewQueueItemContract)
def reject_connector_review_queue_item(
    ingest_run_id: UUID,
    request: ConnectorReviewActionRequest,
    services: ServicesDep,
    auth: AuthDep,
) -> ConnectorReviewQueueItemContract:
    item = _get_queue_item_or_404(ingest_run_id, services, auth)
    return _run_queue_action(
        lambda: services.connector_review_queue_repo.reject_review(
            item.job_id,
            reviewer_id=_reviewer_id(auth, request.reviewer_id),
            reason=_required_action_reason(request.reason),
        )
    )


@router.post("/{ingest_run_id}/requeue", response_model=ConnectorReviewQueueItemContract)
def requeue_connector_review_queue_item(
    ingest_run_id: UUID,
    request: ConnectorReviewActionRequest,
    services: ServicesDep,
    auth: AuthDep,
) -> ConnectorReviewQueueItemContract:
    item = _get_queue_item_or_404(ingest_run_id, services, auth)
    return _run_queue_action(
        lambda: services.connector_review_queue_repo.requeue_failed(
            item.job_id,
            reason=_required_action_reason(request.reason),
            not_before=request.not_before,
            reviewer_id=_reviewer_id(auth, request.reviewer_id),
        )
    )


@router.post("/{ingest_run_id}/cancel", response_model=ConnectorReviewQueueItemContract)
def cancel_connector_review_queue_item(
    ingest_run_id: UUID,
    request: ConnectorReviewActionRequest,
    services: ServicesDep,
    auth: AuthDep,
) -> ConnectorReviewQueueItemContract:
    item = _get_queue_item_or_404(ingest_run_id, services, auth)
    return _run_queue_action(
        lambda: services.connector_review_queue_repo.cancel(
            item.job_id,
            reason=_required_action_reason(request.reason),
            reviewer_id=_reviewer_id(auth, request.reviewer_id),
        )
    )


def _run_queue_action(
    action: Callable[[], ConnectorReviewQueueItem],
) -> ConnectorReviewQueueItemContract:
    try:
        return _queue_item_contract(action())
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


def _required_action_reason(reason: str | None) -> str:
    if reason is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="connector review queue reason is required",
        )
    return reason


def _reviewer_id(auth: RequestAuthContext, reviewer_id: str) -> str:
    reviewer = reviewer_id.strip()
    if not reviewer:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="reviewer_id is required",
        )
    if reviewer != str(auth.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="reviewer_id does not match authenticated user",
        )
    return reviewer


class ConnectorRunRequest(BaseModel):
    connector_name: str
    fixture_key: str


@runs_router.post(
    "", response_model=ConnectorRunResultContract, status_code=status.HTTP_201_CREATED
)
def run_connector_fixture(
    request: ConnectorRunRequest,
    services: ServicesDep,
    auth: AuthDep,
) -> ConnectorRunResultContract:
    if request.connector_name not in _SUPPORTED_CONNECTOR_NAMES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"unsupported connector: {request.connector_name!r}",
        )
    if not _is_safe_fixture_key(request.fixture_key):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="fixture_key must be non-empty alphanumeric with underscores or hyphens",
        )
    fixture_resource = connector_fixture_resource(request.fixture_key)
    if fixture_resource is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"fixture not found: {request.fixture_key!r}",
        )
    connector = _CONNECTOR_INSTANCES[request.connector_name]
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
                workspace_id=auth.workspace_id,
            )
            result = workflow.ingest_fixture(fixture_path)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    packet = build_connector_run_review_packet(result)
    handoff = build_connector_review_handoff(packet)
    quality = _QUALITY_EVALUATORS[request.connector_name](result.connector_result)
    review_status = build_connector_run_review_status(handoff, quality)
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
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
