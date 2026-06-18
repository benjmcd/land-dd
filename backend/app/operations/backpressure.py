from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.job_health import JobQueueHealth


@dataclass(frozen=True)
class QueueBackpressureThresholds:
    enabled: bool
    max_report_queue_depth: int
    max_live_connector_queue_depth: int
    max_queue_oldest_queued_seconds: int
    max_queue_stale_running: int


@dataclass(frozen=True)
class QueueBackpressureDecision:
    allowed: bool
    detail: dict[str, Any] | None = None


REPORT_QUEUE_TYPE = "report_run"
LIVE_CONNECTOR_QUEUE_TYPE = "live_connector_run"


def evaluate_queue_backpressure(
    health: JobQueueHealth,
    thresholds: QueueBackpressureThresholds,
    *,
    admission_count: int = 1,
) -> QueueBackpressureDecision:
    if admission_count < 1:
        raise ValueError("admission_count must be at least 1")
    if not thresholds.enabled:
        return QueueBackpressureDecision(allowed=True)

    max_depth = _max_depth_for_queue(health.job_type, thresholds)
    projected_depth = health.queued + admission_count
    if projected_depth > max_depth:
        return _blocked(
            queue=health.job_type,
            reason="queue_depth_exceeded",
            observed=projected_depth,
            threshold=max_depth,
            extra={
                "current_queued": health.queued,
                "admission_count": admission_count,
            },
        )

    oldest_queued_age = health.oldest_queued_age_seconds
    if (
        oldest_queued_age is not None
        and oldest_queued_age > thresholds.max_queue_oldest_queued_seconds
    ):
        return _blocked(
            queue=health.job_type,
            reason="oldest_queued_age_exceeded",
            observed=oldest_queued_age,
            threshold=thresholds.max_queue_oldest_queued_seconds,
        )

    if health.stale_running > thresholds.max_queue_stale_running:
        return _blocked(
            queue=health.job_type,
            reason="stale_running_exceeded",
            observed=health.stale_running,
            threshold=thresholds.max_queue_stale_running,
        )

    return QueueBackpressureDecision(allowed=True)


def _max_depth_for_queue(
    queue_type: str,
    thresholds: QueueBackpressureThresholds,
) -> int:
    if queue_type == LIVE_CONNECTOR_QUEUE_TYPE:
        return thresholds.max_live_connector_queue_depth
    return thresholds.max_report_queue_depth


def _blocked(
    *,
    queue: str,
    reason: str,
    observed: int | float,
    threshold: int,
    extra: dict[str, Any] | None = None,
) -> QueueBackpressureDecision:
    detail: dict[str, Any] = {
        "type": "queue_backpressure",
        "queue": queue,
        "reason": reason,
        "observed": observed,
        "threshold": threshold,
    }
    if extra:
        detail.update(extra)
    return QueueBackpressureDecision(
        allowed=False,
        detail=detail,
    )


__all__ = [
    "QueueBackpressureDecision",
    "QueueBackpressureThresholds",
    "evaluate_queue_backpressure",
]
