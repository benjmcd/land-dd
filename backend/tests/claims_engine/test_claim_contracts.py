from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.domain.claim_contracts import ClaimContract
from app.domain.enums import ConfidenceBand, SeverityBand


def test_claim_requires_evidence_ids() -> None:
    with pytest.raises(ValidationError):
        ClaimContract(
            area_id=uuid4(),
            claim_code="FLOOD_CONSTRAINT_PRESENT",
            domain="flood",
            assertion="Mapped data indicates possible flood constraint.",
            severity=SeverityBand.HIGH,
            confidence=ConfidenceBand.MEDIUM,
            evidence_ids=[],
        )


def test_claim_accepts_evidence_ids_and_separates_severity_confidence() -> None:
    claim = ClaimContract(
        area_id=uuid4(),
        claim_code="SOURCE_UNAVAILABLE_UNKNOWN",
        domain="flood",
        assertion="Flood source unavailable; risk cannot be determined from this source.",
        severity=SeverityBand.UNKNOWN,
        confidence=ConfidenceBand.UNKNOWN,
        evidence_ids=[uuid4()],
    )
    assert claim.severity == SeverityBand.UNKNOWN
    assert claim.confidence == ConfidenceBand.UNKNOWN


def test_claim_stores_verification_task() -> None:
    claim = ClaimContract(
        area_id=uuid4(),
        claim_code="WETLAND_SCREEN_REQUIRED",
        domain="wetlands",
        assertion="NWI data indicates possible wetland. Professional delineation required.",
        severity=SeverityBand.HIGH,
        confidence=ConfidenceBand.LOW,
        evidence_ids=[uuid4()],
        verification_required=True,
        verification_task="Commission a jurisdictional wetland delineation.",
    )
    assert claim.verification_required is True
    assert "delineation" in (claim.verification_task or "")


def test_claim_stores_rule_metadata() -> None:
    claim = ClaimContract(
        area_id=uuid4(),
        claim_code="FLOOD_001",
        domain="flood",
        assertion="Mapped data indicates possible flood constraint.",
        severity=SeverityBand.HIGH,
        confidence=ConfidenceBand.MEDIUM,
        evidence_ids=[uuid4()],
        rule_code="FLOOD_G001",
        ruleset_id="homestead_mvp_v0_1",
        ruleset_version="0.1",
    )
    assert claim.rule_code == "FLOOD_G001"
    assert claim.ruleset_id == "homestead_mvp_v0_1"
    assert claim.ruleset_version == "0.1"
