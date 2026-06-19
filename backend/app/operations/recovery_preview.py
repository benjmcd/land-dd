from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from app.connectors.live_jobs import (
    LIVE_CONNECTOR_JOB_TYPE,
    LiveConnectorJobRecord,
    LiveConnectorJobStoreProtocol,
)
from app.core.error_safety import REDACTED_ERROR_MESSAGE, safe_error_message
from app.domain.enums import JobStatus
from app.domain.job_health import STALE_RUNNING_THRESHOLD_SECONDS
from app.reports.job_store import (
    REPORT_RUN_JOB_TYPE,
    AsyncReportJobStoreProtocol,
    ReportJobRecord,
)

RECOVERY_PREVIEW_SCHEMA_VERSION = "operations_recovery_preview_v1"
RECOVERY_PREVIEW_REDACTED_ERROR_MESSAGE = REDACTED_ERROR_MESSAGE


@dataclass(frozen=True)
class JobRecoveryPreviewItem:
    job_type: str
    job_id: UUID
    status: JobStatus
    area_id: UUID
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    age_seconds: float | None
    stale_running: bool
    error_message: str | None
    recommended_action: str
    reason: str
    detail_ui_path: str
    detail_api_path: str
    intent_code: str | None = None
    workspace_id: UUID | None = None
    retry_of_job_id: UUID | None = None
    source_registry_id: str | None = None
    connector_name: str | None = None
    attempts: int | None = None
    max_attempts: int | None = None
    locked_by: str | None = None
    locked_at: datetime | None = None


@dataclass(frozen=True)
class OperationsRecoveryPreview:
    schema_version: str
    generated_at: datetime
    stale_running_threshold_seconds: int
    candidate_limit_per_state: int
    report_jobs: tuple[JobRecoveryPreviewItem, ...]
    live_connector_jobs: tuple[JobRecoveryPreviewItem, ...]


def build_recovery_preview(
    *,
    report_jobs: AsyncReportJobStoreProtocol,
    live_connector_jobs: LiveConnectorJobStoreProtocol,
    limit_per_state: int = 25,
) -> OperationsRecoveryPreview:
    return OperationsRecoveryPreview(
        schema_version=RECOVERY_PREVIEW_SCHEMA_VERSION,
        generated_at=datetime.now(UTC),
        stale_running_threshold_seconds=STALE_RUNNING_THRESHOLD_SECONDS,
        candidate_limit_per_state=limit_per_state,
        report_jobs=tuple(
            _report_item(job)
            for job in (
                *report_jobs.list_recent(limit=limit_per_state, status=JobStatus.FAILED),
                *_stale_report_jobs(report_jobs, limit_per_state=limit_per_state),
            )
        ),
        live_connector_jobs=tuple(
            _live_connector_item(job)
            for job in (
                *live_connector_jobs.list_recent(
                    limit=limit_per_state,
                    status=JobStatus.FAILED,
                ),
                *live_connector_jobs.list_recent(
                    limit=limit_per_state,
                    status=JobStatus.RUNNING,
                    stale=True,
                ),
            )
        ),
    )


def _stale_report_jobs(
    report_jobs: AsyncReportJobStoreProtocol,
    *,
    limit_per_state: int,
) -> tuple[ReportJobRecord, ...]:
    return tuple(
        report_jobs.list_recent(
            limit=limit_per_state,
            status=JobStatus.RUNNING,
            stale=True,
        )
    )


def _report_item(job: ReportJobRecord) -> JobRecoveryPreviewItem:
    stale_running = job.status == JobStatus.RUNNING and _is_stale(
        job.started_at or job.created_at,
    )
    if stale_running:
        recommended_action = "inspect_report_worker"
        reason = "Report job is still running beyond the stale-running threshold."
    else:
        recommended_action = "retry_report"
        reason = "Report job failed; use the existing report retry flow after inspection."
    return JobRecoveryPreviewItem(
        job_type=REPORT_RUN_JOB_TYPE,
        job_id=job.report_run_id,
        status=job.status,
        area_id=job.area_id,
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=None,
        age_seconds=_age_seconds(job.started_at or job.created_at),
        stale_running=stale_running,
        error_message=safe_recovery_error_message(job.error_msg),
        recommended_action=recommended_action,
        reason=reason,
        detail_ui_path=f"/ui/report-runs/{job.report_run_id}",
        detail_api_path=f"/report-runs/{job.report_run_id}",
        intent_code=job.intent_code.value,
        workspace_id=job.workspace_id,
        retry_of_job_id=job.retry_of_report_run_id,
    )


def _live_connector_item(job: LiveConnectorJobRecord) -> JobRecoveryPreviewItem:
    stale_running = job.status == JobStatus.RUNNING and _is_stale(
        job.started_at or job.created_at,
    )
    if stale_running:
        recommended_action = "inspect_live_connector_worker"
        reason = "Live connector job is still running beyond the stale-running threshold."
    else:
        recommended_action = "inspect_live_connector_failure"
        reason = "Live connector job failed; inspect source and review state before requeue."
    return JobRecoveryPreviewItem(
        job_type=LIVE_CONNECTOR_JOB_TYPE,
        job_id=job.job_id,
        status=job.status,
        area_id=job.area_id,
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
        age_seconds=_age_seconds(job.started_at or job.created_at),
        stale_running=stale_running,
        error_message=safe_recovery_error_message(job.last_error),
        recommended_action=recommended_action,
        reason=reason,
        detail_ui_path=f"/ui/live-connector-jobs/{job.job_id}",
        detail_api_path=f"/connector-runs/live-jobs/{job.job_id}",
        source_registry_id=job.source_registry_id,
        connector_name=job.connector_name,
        attempts=job.attempts,
        max_attempts=job.max_attempts,
        locked_by=job.locked_by,
        locked_at=job.locked_at,
    )


def _is_stale(started_or_created_at: datetime | None) -> bool:
    age_seconds = _age_seconds(started_or_created_at)
    return age_seconds is not None and age_seconds >= STALE_RUNNING_THRESHOLD_SECONDS


def _age_seconds(started_or_created_at: datetime | None) -> float | None:
    if started_or_created_at is None:
        return None
    if started_or_created_at.tzinfo is None:
        started_or_created_at = started_or_created_at.replace(tzinfo=UTC)
    return max(0.0, (datetime.now(UTC) - started_or_created_at).total_seconds())


def safe_recovery_error_message(message: str | None) -> str | None:
    """Return an operator-safe error summary for recovery preview surfaces."""
    return safe_error_message(message)


__all__ = [
    "JobRecoveryPreviewItem",
    "OperationsRecoveryPreview",
    "RECOVERY_PREVIEW_SCHEMA_VERSION",
    "RECOVERY_PREVIEW_REDACTED_ERROR_MESSAGE",
    "build_recovery_preview",
    "safe_recovery_error_message",
]
