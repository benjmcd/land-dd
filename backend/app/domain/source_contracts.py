from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, HttpUrl

from app.domain.enums import AuthorityLevel


class SourceRetrievalStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


class SourceContract(BaseModel):
    source_id: UUID = Field(default_factory=uuid4)
    name: str
    organization: str | None = None
    homepage_url: HttpUrl | None = None
    source_type: str | None = None
    authority_level: AuthorityLevel = AuthorityLevel.UNKNOWN
    domain: str
    geographic_scope: str | None = None
    update_cadence: str | None = None
    license_status: str = "unknown"
    commercial_use_status: str = "unknown"
    redistribution_status: str = "unknown"
    license_summary: str | None = None
    attribution_required: bool = False
    cache_allowed: str = "unknown"
    export_allowed: str = "unknown"
    ai_use_allowed: str = "unknown"
    raw_data_allowed: str = "unknown"
    freshness_class: str = "unknown"
    last_checked_at: str | None = None
    review_owner: str | None = None
    review_status: str = "pending"
    notes: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)


class SourceDatasetContract(BaseModel):
    dataset_id: UUID = Field(default_factory=uuid4)
    source_id: UUID
    dataset_name: str
    dataset_code: str | None = None
    domain: str
    geometry_type: str | None = None
    spatial_resolution: str | None = None
    temporal_coverage: str | None = None
    legal_caveat: str | None = None
    source_url: HttpUrl | None = None
    metadata: dict[str, object] = Field(default_factory=dict)


class SourceDatasetVersionContract(BaseModel):
    dataset_version_id: UUID = Field(default_factory=uuid4)
    dataset_id: UUID
    version_label: str
    published_at: datetime | None = None
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    checksum: str | None = None
    storage_uri: str | None = None
    manifest: dict[str, object] = Field(default_factory=dict)
    is_current: bool = False
    notes: str | None = None


class SourceRetrievalRunContract(BaseModel):
    ingest_run_id: UUID = Field(default_factory=uuid4)
    dataset_version_id: UUID | None = None
    connector_name: str
    status: SourceRetrievalStatus = SourceRetrievalStatus.PENDING
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime | None = None
    row_count: int | None = None
    error_count: int = 0
    warning_count: int = 0
    log_uri: str | None = None
    metrics: dict[str, object] = Field(default_factory=dict)
