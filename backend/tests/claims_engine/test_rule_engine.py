from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

import pytest

from app.claims_engine.rule_engine import DEFAULT_RULESET_PATH, RuleEngine, load_ruleset
from app.domain.enums import ConfidenceBand, EvidenceType, SeverityBand
from app.domain.evidence_contracts import EvidenceContract


def make_flood_evidence(
    *,
    area_id: UUID,
    flood_zone: str = "AE",
    confidence: ConfidenceBand = ConfidenceBand.MEDIUM,
    superseded_by: UUID | None = None,
) -> EvidenceContract:
    return EvidenceContract(
        area_id=area_id,
        source_id=uuid4(),
        evidence_type=EvidenceType.SPATIAL_INTERSECTION,
        evidence_code="FLOOD_ZONE_SCREEN",
        domain="flood",
        observation="Fixture flood source intersects a mapped flood zone.",
        observed_value={"flood_zone": flood_zone},
        method_code="fixture_flood_overlay",
        confidence=confidence,
        caveat="Screening fixture only; confirm locally.",
        superseded_by=superseded_by,
    )


def make_flood_failure(area_id: UUID) -> EvidenceContract:
    return EvidenceContract(
        area_id=area_id,
        source_id=uuid4(),
        evidence_type=EvidenceType.SOURCE_FAILURE,
        evidence_code="FLOOD_SOURCE_FAILURE",
        domain="flood",
        observation="Fixture flood source request failed.",
        observed_value={},
        method_code="fixture_flood_overlay",
        confidence=ConfidenceBand.UNKNOWN,
        caveat="FEMA fixture endpoint returned 503.",
        is_source_failure=True,
    )


def test_load_ruleset_exposes_versioned_flood_gate() -> None:
    ruleset = load_ruleset(DEFAULT_RULESET_PATH)
    rule = ruleset.hard_gate_for_condition("material_intersection_with_high_risk_flood_zone")

    assert ruleset.ruleset_id == "homestead_mvp_v0_1"
    assert ruleset.version == "0.1"
    assert rule.code == "FLOOD_G001"
    assert rule.claim_code == "FLOOD_001"
    assert rule.severity_on_fail == SeverityBand.HIGH


def test_evaluate_creates_deterministic_flood_claim_from_high_risk_evidence() -> None:
    area_id = uuid4()
    evidence = make_flood_evidence(area_id=area_id)
    engine = RuleEngine.from_file()

    first_result = engine.evaluate([evidence])
    second_result = engine.evaluate([evidence])

    assert first_result == second_result
    claim = first_result[0]
    assert claim.claim_code == "FLOOD_001"
    assert claim.area_id == area_id
    assert claim.rule_code == "FLOOD_G001"
    assert claim.ruleset_id == "homestead_mvp_v0_1"
    assert claim.ruleset_version == "0.1"
    assert claim.severity == SeverityBand.HIGH
    assert claim.confidence == ConfidenceBand.MEDIUM
    assert claim.evidence_ids == [evidence.evidence_id]
    assert claim.verification_required is True
    assert "local floodplain administrator" in (claim.verification_task or "")
    assert "Screening fixture only" in claim.user_safe_language


def test_evaluate_is_deterministic_when_input_order_changes() -> None:
    area_id = uuid4()
    first_evidence = make_flood_evidence(area_id=area_id, flood_zone="AE")
    second_evidence = make_flood_evidence(area_id=area_id, flood_zone="VE")
    engine = RuleEngine.from_file()

    first_result = engine.evaluate([first_evidence, second_evidence])
    second_result = engine.evaluate([second_evidence, first_evidence])

    assert first_result == second_result
    assert first_result[0].evidence_ids == sorted(
        [first_evidence.evidence_id, second_evidence.evidence_id],
        key=str,
    )


def test_evaluate_creates_unknown_claim_from_flood_source_failure() -> None:
    area_id = uuid4()
    failure = make_flood_failure(area_id)
    engine = RuleEngine.from_file()

    claims = engine.evaluate([failure])

    assert len(claims) == 1
    claim = claims[0]
    assert claim.claim_code == "FLOOD_SOURCE_UNAVAILABLE_UNKNOWN"
    assert claim.severity == SeverityBand.UNKNOWN
    assert claim.confidence == ConfidenceBand.UNKNOWN
    assert claim.rule_code == "FLOOD_G001"
    assert claim.ruleset_id == "homestead_mvp_v0_1"
    assert claim.ruleset_version == "0.1"
    assert claim.evidence_ids == [failure.evidence_id]
    assert "503" in claim.user_safe_language


def test_evaluate_empty_evidence_returns_no_claims() -> None:
    assert RuleEngine.from_file().evaluate([]) == []


def test_evaluate_creates_independent_claims_per_area() -> None:
    first_area_id = uuid4()
    second_area_id = uuid4()
    first_evidence = make_flood_evidence(area_id=first_area_id)
    second_evidence = make_flood_evidence(area_id=second_area_id)

    claims = RuleEngine.from_file().evaluate([second_evidence, first_evidence])

    assert len(claims) == 2
    claim_by_area = {claim.area_id: claim for claim in claims}
    assert claim_by_area[first_area_id].evidence_ids == [first_evidence.evidence_id]
    assert claim_by_area[second_area_id].evidence_ids == [second_evidence.evidence_id]


def test_evaluate_reports_positive_and_source_failure_evidence_explicitly() -> None:
    area_id = uuid4()
    evidence = make_flood_evidence(area_id=area_id)
    failure = make_flood_failure(area_id)

    claims = RuleEngine.from_file().evaluate([evidence, failure])

    assert [claim.claim_code for claim in claims] == [
        "FLOOD_001",
        "FLOOD_SOURCE_UNAVAILABLE_UNKNOWN",
    ]


def test_evaluate_ignores_low_risk_and_superseded_flood_evidence() -> None:
    area_id = uuid4()
    low_risk = make_flood_evidence(area_id=area_id, flood_zone="X")
    superseded = make_flood_evidence(area_id=area_id, superseded_by=uuid4())
    engine = RuleEngine.from_file()

    assert engine.evaluate([low_risk, superseded]) == []


def test_load_ruleset_rejects_invalid_severity(tmp_path: Path) -> None:
    bad_ruleset = tmp_path / "bad-ruleset.yaml"
    bad_ruleset.write_text(
        "\n".join(
            [
                "ruleset:",
                "  id: bad_ruleset",
                "  version: 0.1",
                "  hard_gates:",
                "    - code: FLOOD_G001",
                "      domain: flood",
                "      severity_on_fail: not_a_severity",
                "      condition: material_intersection_with_high_risk_flood_zone",
                "      claim_code: FLOOD_001",
                "      verification_task: Confirm flood risk locally.",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_ruleset(bad_ruleset)
