from __future__ import annotations

from importlib.resources import as_file
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.dependencies import ApiServices, get_services
from app.connectors import (
    build_connector_review_handoff,
    build_connector_run_review_packet,
    build_connector_run_review_status,
    build_fixture_workflow_with_public_lane_services,
    evaluate_flood_fixture_quality,
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

router = APIRouter(prefix="/connector-review-queue", tags=["connector-review-queue"])
runs_router = APIRouter(prefix="/connector-runs", tags=["connector-runs"])
ServicesDep = Annotated[ApiServices, Depends(get_services)]

_SUPPORTED_CONNECTOR_NAMES: frozenset[str] = frozenset({"fixture_flood_static"})


def _is_safe_fixture_key(key: str) -> bool:
    return bool(key) and all(c.isalnum() or c in ("_", "-") for c in key)


@router.get("/{ingest_run_id}", response_model=ConnectorReviewQueueItemContract)
def get_connector_review_queue_item(
    ingest_run_id: UUID,
    services: ServicesDep,
) -> ConnectorReviewQueueItemContract:
    item = services.connector_review_queue_repo.get_by_ingest_run_id(ingest_run_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="connector review queue item not found",
        )
    return ConnectorReviewQueueItemContract(
        job_id=item.job_id,
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


class ConnectorRunRequest(BaseModel):
    connector_name: str
    fixture_key: str


@runs_router.post(
    "", response_model=ConnectorRunResultContract, status_code=status.HTTP_201_CREATED
)
def run_connector_fixture(
    request: ConnectorRunRequest,
    services: ServicesDep,
) -> ConnectorRunResultContract:
    if request.connector_name not in _SUPPORTED_CONNECTOR_NAMES:
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
    _ensure_fixture_provenance(services)
    workflow = build_fixture_workflow_with_public_lane_services(
        source_provenance_service=services.source_provenance_service,
        evidence_service=services.evidence_service,
    )
    try:
        with as_file(fixture_resource) as fixture_path:
            result = workflow.ingest_fixture(fixture_path)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    packet = build_connector_run_review_packet(result)
    handoff = build_connector_review_handoff(packet)
    quality = evaluate_flood_fixture_quality(result.connector_result)
    review_status = build_connector_run_review_status(handoff, quality)
    queue_item = services.connector_review_queue_repo.enqueue_review_status(review_status)
    return ConnectorRunResultContract(
        ingest_run_id=result.connector_result.retrieval_run.ingest_run_id,
        connector_name=result.connector_result.retrieval_run.connector_name,
        retrieval_status=result.connector_result.retrieval_run.status.value,
        evidence_created=len(result.evidence_ingestion.created_evidence),
        evidence_skipped=len(result.evidence_ingestion.skipped_evidence),
        review_required=review_status.review_required,
        queue_job_id=queue_item.job_id,
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
