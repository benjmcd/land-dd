from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import ApiServices, get_services
from app.domain.connector_contracts import ConnectorReviewQueueItemContract

router = APIRouter(prefix="/connector-review-queue", tags=["connector-review-queue"])
ServicesDep = Annotated[ApiServices, Depends(get_services)]


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
