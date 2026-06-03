from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.domain.enums import ConfidenceBand, EvidenceType


class EvidenceContract(BaseModel):
    evidence_id: UUID = Field(default_factory=uuid4)
    area_id: UUID
    evidence_type: EvidenceType = EvidenceType.SOURCE_OBSERVATION
    evidence_code: str
    domain: str
    observation: str
    observed_value: dict[str, object] = Field(default_factory=dict)
    source_id: UUID
    dataset_version_id: UUID | None = None
    method_code: str
    method_version: str = "0.1.0"
    confidence: ConfidenceBand = ConfidenceBand.UNKNOWN
    caveat: str | None = None
    is_negative_evidence: bool = False
    is_source_failure: bool = False
    superseded_by: UUID | None = None
    source_date: str | None = None
    observed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
