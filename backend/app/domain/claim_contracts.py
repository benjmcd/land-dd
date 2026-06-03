from __future__ import annotations

from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator

from app.domain.enums import ConfidenceBand, SeverityBand


class ClaimContract(BaseModel):
    claim_id: UUID = Field(default_factory=uuid4)
    area_id: UUID
    claim_code: str
    domain: str = "unknown"
    assertion: str
    user_safe_language: str = ""
    severity: SeverityBand = SeverityBand.UNKNOWN
    confidence: ConfidenceBand = ConfidenceBand.UNKNOWN
    evidence_ids: list[UUID]
    rule_code: str | None = None
    ruleset_id: str | None = None
    ruleset_version: str | None = None
    verification_required: bool = True
    verification_task: str | None = None

    @model_validator(mode="after")
    def require_evidence_ids(self) -> ClaimContract:
        if not self.evidence_ids:
            raise ValueError("claims must cite at least one evidence_id")
        return self
