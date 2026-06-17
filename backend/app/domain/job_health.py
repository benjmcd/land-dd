from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

STALE_RUNNING_THRESHOLD_SECONDS = 900


@dataclass(frozen=True)
class JobQueueHealth:
    job_type: str
    total: int
    queued: int
    running: int
    succeeded: int
    failed: int
    cancelled: int
    needs_review: int
    oldest_queued_age_seconds: float | None = None
    oldest_running_age_seconds: float | None = None
    oldest_running_job_id: UUID | None = None
    stale_running: int = 0
    stale_running_threshold_seconds: int = STALE_RUNNING_THRESHOLD_SECONDS


__all__ = ["JobQueueHealth", "STALE_RUNNING_THRESHOLD_SECONDS"]
