from __future__ import annotations

from uuid import UUID, uuid4

from pydantic import BaseModel, Field, HttpUrl

from app.domain.enums import AuthorityLevel


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
