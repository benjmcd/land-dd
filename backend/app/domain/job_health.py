from __future__ import annotations

from dataclasses import dataclass


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


__all__ = ["JobQueueHealth"]
