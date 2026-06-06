from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.domain.claim_contracts import ClaimContract
from app.domain.enums import IntentCode, JobStatus, ReportReviewStatus
from app.domain.evidence_contracts import EvidenceContract


class ReportReviewActionContract(BaseModel):
    action: ReportReviewStatus
    from_status: ReportReviewStatus
    to_status: ReportReviewStatus
    reviewer_id: str
    reason: str | None = None
    reviewed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ReportRunContract(BaseModel):
    report_run_id: UUID = Field(default_factory=uuid4)
    workspace_id: UUID | None = None
    requested_by: UUID | None = None
    area_id: UUID
    intent_code: IntentCode
    idempotency_key: str | None = None
    status: JobStatus = JobStatus.QUEUED
    review_status: ReportReviewStatus = ReportReviewStatus.NEEDS_REVIEW
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    review_actions: list[ReportReviewActionContract] = Field(default_factory=list)
    source_manifest: dict[str, object] = Field(default_factory=dict)
    assumptions: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)
    evidence: list[EvidenceContract] = Field(default_factory=list)
    claims: list[ClaimContract] = Field(default_factory=list)
    unknowns: list[ClaimContract] = Field(default_factory=list)
    red_flags: list[ClaimContract] = Field(default_factory=list)
    verification_tasks: list[str] = Field(default_factory=list)
    artifact_metadata: dict[str, object] = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime | None = None
    output_uri: str | None = None


class ReportRunJobContract(BaseModel):
    job_id: UUID = Field(default_factory=uuid4)
    job_type: str = "report_run"
    status: JobStatus = JobStatus.QUEUED
    workspace_id: UUID | None = None
    requested_by: UUID | None = None
    area_id: UUID
    intent_code: IntentCode
    idempotency_key: str
    report_run_id: UUID | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    not_before: datetime | None = None
    attempts: int = Field(default=0, ge=0)
    max_attempts: int = Field(default=3, ge=1)
    locked_by: str | None = None
    locked_at: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    last_error: str | None = None
