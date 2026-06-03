from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.domain.enums import JobStatus


class ReportRunContract(BaseModel):
    report_run_id: UUID = Field(default_factory=uuid4)
    area_id: UUID
    intent_code: str
    status: JobStatus = JobStatus.QUEUED
    source_manifest: dict[str, object] = Field(default_factory=dict)
    assumptions: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime | None = None
    output_uri: str | None = None
