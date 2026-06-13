from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

import pytest

from app.claims_engine.rule_engine import (
    BROADBAND_NO_ACCESS_CLAIM_CODE,
    BROADBAND_SOURCE_UNAVAILABLE_CLAIM_CODE,
    DEFAULT_RULESET_PATH,
    ENV_HAZARD_NEEDS_REVIEW_CLAIM_CODE,
    ENV_HAZARD_STALE_CLAIM_CODE,
    FLOOD_MODERATE_CLAIM_CODE,
    GEOLOGY_NOT_EVALUATED_CLAIM_CODE,
    MINERALS_ACTIVE_CLAIM_CODE,
    MINERALS_SOURCE_UNAVAILABLE_CLAIM_CODE,
    SOIL_POOR_DRAINAGE_CLAIM_CODE,
    RuleEngine,
    load_ruleset,
)
from app.domain.enums import ConfidenceBand, EvidenceType, SeverityBand
from app.domain.evidence_contracts import EvidenceContract


def make_flood_evidence(
    *,
    area_id: UUID,
    flood_zone: str = "AE",
    confidence: ConfidenceBand = ConfidenceBand.MEDIUM,
    is_negative_evidence: bool = False,
    source_stale: bool = False,
    superseded_by: UUID | None = None,
) -> EvidenceContract:
    observed_value: dict[str, object] = {"flood_zone": flood_zone}
    if source_stale:
        observed_value["source_stale"] = True
    return EvidenceContract(
        area_id=area_id,
        source_id=uuid4(),
        evidence_type=EvidenceType.SPATIAL_INTERSECTION,
        evidence_code="FLOOD_ZONE_SCREEN",
        domain="flood",
        observation="Fixture flood source intersects a mapped flood zone.",
        observed_value=observed_value,
        method_code="fixture_flood_overlay",
        confidence=confidence,
        caveat="Screening fixture only; confirm locally.",
        is_negative_evidence=is_negative_evidence,
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


def make_access_evidence(
    *,
    area_id: UUID,
    public_road_adjacency: bool = False,
    confidence: ConfidenceBand = ConfidenceBand.MEDIUM,
    source_stale: bool = False,
    superseded_by: UUID | None = None,
) -> EvidenceContract:
    observed_value: dict[str, object] = {
        "public_road_adjacency": public_road_adjacency,
    }
    if source_stale:
        observed_value["source_stale"] = True
    return EvidenceContract(
        area_id=area_id,
        source_id=uuid4(),
        evidence_type=EvidenceType.SPATIAL_INTERSECTION,
        evidence_code="ACCESS_ROAD_ADJACENCY_SCREEN",
        domain="access",
        observation="Fixture road source screens apparent public road adjacency.",
        observed_value=observed_value,
        method_code="fixture_road_adjacency_overlay",
        confidence=confidence,
        caveat="Road adjacency is a physical proxy only; verify recorded access.",
        superseded_by=superseded_by,
    )


def make_access_failure(area_id: UUID) -> EvidenceContract:
    return EvidenceContract(
        area_id=area_id,
        source_id=uuid4(),
        evidence_type=EvidenceType.SOURCE_FAILURE,
        evidence_code="ACCESS_SOURCE_FAILURE",
        domain="access",
        observation="Fixture road/access source request failed.",
        observed_value={},
        method_code="fixture_road_adjacency_overlay",
        confidence=ConfidenceBand.UNKNOWN,
        caveat="Road adjacency fixture endpoint returned 503.",
        is_source_failure=True,
    )


def make_wetland_evidence(
    *,
    area_id: UUID,
    intersects_mapped_wetlands: bool = True,
    confidence: ConfidenceBand = ConfidenceBand.MEDIUM,
    source_stale: bool = False,
    superseded_by: UUID | None = None,
) -> EvidenceContract:
    observed_value: dict[str, object] = {
        "intersects_mapped_wetlands": intersects_mapped_wetlands,
        "mapped_wetland_area_sq_m": 1700.0 if intersects_mapped_wetlands else 0.0,
    }
    if source_stale:
        observed_value["source_stale"] = True
    return EvidenceContract(
        area_id=area_id,
        source_id=uuid4(),
        evidence_type=EvidenceType.SPATIAL_INTERSECTION,
        evidence_code="WETLAND_SCREEN",
        domain="wetlands",
        observation="Fixture wetland source screens mapped wetland/deepwater features.",
        observed_value=observed_value,
        method_code="fixture_wetland_overlay",
        confidence=confidence,
        caveat="Mapped wetlands are screening inputs only; order delineation.",
        superseded_by=superseded_by,
    )


def make_wetland_failure(area_id: UUID) -> EvidenceContract:
    return EvidenceContract(
        area_id=area_id,
        source_id=uuid4(),
        evidence_type=EvidenceType.SOURCE_FAILURE,
        evidence_code="WETLAND_SOURCE_FAILURE",
        domain="wetlands",
        observation="Fixture wetland source request failed.",
        observed_value={},
        method_code="fixture_wetland_overlay",
        confidence=ConfidenceBand.UNKNOWN,
        caveat="Wetland fixture endpoint returned 503.",
        is_source_failure=True,
    )


def make_slope_evidence(
    *,
    area_id: UUID,
    insufficient_low_slope_area: bool = True,
    confidence: ConfidenceBand = ConfidenceBand.MEDIUM,
    source_stale: bool = False,
    superseded_by: UUID | None = None,
) -> EvidenceContract:
    observed_value: dict[str, object] = {
        "metric_code": "low_slope_buildable_area_sq_m",
        "value": 900.0 if insufficient_low_slope_area else 6000.0,
        "unit": "sq_m",
        "insufficient_low_slope_buildable_area": insufficient_low_slope_area,
    }
    if source_stale:
        observed_value["source_stale"] = True
    return EvidenceContract(
        area_id=area_id,
        source_id=uuid4(),
        evidence_type=EvidenceType.DERIVED_METRIC,
        evidence_code="SLOPE_BUILDABLE_AREA_SCREEN",
        domain="buildability",
        observation="Fixture slope model estimates low-slope buildable area.",
        observed_value=observed_value,
        method_code="fixture_slope_buildability_metric",
        confidence=confidence,
        caveat="Slope model is a screening proxy only; confirm with surveyor/engineer.",
        superseded_by=superseded_by,
    )


def make_slope_failure(area_id: UUID) -> EvidenceContract:
    return EvidenceContract(
        area_id=area_id,
        source_id=uuid4(),
        evidence_type=EvidenceType.SOURCE_FAILURE,
        evidence_code="SLOPE_SOURCE_FAILURE",
        domain="buildability",
        observation="Fixture slope source request failed.",
        observed_value={},
        method_code="fixture_slope_buildability_metric",
        confidence=ConfidenceBand.UNKNOWN,
        caveat="Slope fixture endpoint returned 503.",
        is_source_failure=True,
    )


def make_zoning_evidence(
    *,
    area_id: UUID,
    intended_residential_use_prohibited: bool = True,
    intended_residential_use_allowed: bool | None = None,
    confidence: ConfidenceBand = ConfidenceBand.MEDIUM,
    source_stale: bool = False,
    superseded_by: UUID | None = None,
) -> EvidenceContract:
    observed_value: dict[str, object] = {
        "zoning_district": "fixture-rural-district",
        "intended_residential_use_prohibited": intended_residential_use_prohibited,
    }
    if intended_residential_use_allowed is not None:
        observed_value["intended_residential_use_allowed"] = (
            intended_residential_use_allowed
        )
    if source_stale:
        observed_value["source_stale"] = True
    return EvidenceContract(
        area_id=area_id,
        source_id=uuid4(),
        evidence_type=EvidenceType.SOURCE_OBSERVATION,
        evidence_code="ZONING_USE_SCREEN",
        domain="zoning",
        observation="Fixture zoning source screens intended residential/homestead use.",
        observed_value=observed_value,
        method_code="fixture_zoning_use_screen",
        confidence=confidence,
        caveat="Fixture zoning/use screening only; verify with county planning.",
        superseded_by=superseded_by,
    )


def make_zoning_failure(area_id: UUID) -> EvidenceContract:
    return EvidenceContract(
        area_id=area_id,
        source_id=uuid4(),
        evidence_type=EvidenceType.SOURCE_FAILURE,
        evidence_code="ZONING_SOURCE_FAILURE",
        domain="zoning",
        observation="Fixture zoning source request failed.",
        observed_value={},
        method_code="fixture_zoning_use_screen",
        confidence=ConfidenceBand.UNKNOWN,
        caveat="Zoning fixture endpoint returned 503.",
        is_source_failure=True,
    )


def make_water_evidence(
    *,
    area_id: UUID,
    no_plausible_water_context: bool = True,
    plausible_water_context: bool | None = None,
    confidence: ConfidenceBand = ConfidenceBand.MEDIUM,
    source_stale: bool = False,
    superseded_by: UUID | None = None,
) -> EvidenceContract:
    observed_value: dict[str, object] = {
        "water_context_status": "fixture-no-plausible-context",
        "no_plausible_water_context": no_plausible_water_context,
        "nearby_well_log_count": 0 if no_plausible_water_context else 3,
    }
    if plausible_water_context is not None:
        observed_value["plausible_water_context"] = plausible_water_context
    if source_stale:
        observed_value["source_stale"] = True
    return EvidenceContract(
        area_id=area_id,
        source_id=uuid4(),
        evidence_type=EvidenceType.SOURCE_OBSERVATION,
        evidence_code="WATER_CONTEXT_SCREEN",
        domain="water",
        observation="Fixture water source screens plausible water context.",
        observed_value=observed_value,
        method_code="fixture_water_context_screen",
        confidence=confidence,
        caveat="Fixture water-context screening only; verify water rights and wells.",
        superseded_by=superseded_by,
    )


def make_water_failure(area_id: UUID) -> EvidenceContract:
    return EvidenceContract(
        area_id=area_id,
        source_id=uuid4(),
        evidence_type=EvidenceType.SOURCE_FAILURE,
        evidence_code="WATER_SOURCE_FAILURE",
        domain="water",
        observation="Fixture water source request failed.",
        observed_value={},
        method_code="fixture_water_context_screen",
        confidence=ConfidenceBand.UNKNOWN,
        caveat="Water fixture endpoint returned 503.",
        is_source_failure=True,
    )


def test_load_ruleset_exposes_versioned_access_gate() -> None:
    ruleset = load_ruleset(DEFAULT_RULESET_PATH)
    rule = ruleset.hard_gate_for_condition(
        "no_public_road_adjacency_or_access_source_unavailable"
    )

    assert rule.code == "ACCESS_G001"
    assert rule.claim_code == "ACCESS_001"
    assert rule.severity_on_fail == SeverityBand.CRITICAL


def test_load_ruleset_exposes_versioned_zoning_gate() -> None:
    ruleset = load_ruleset(DEFAULT_RULESET_PATH)
    rule = ruleset.hard_gate_for_condition(
        "intended_residential_use_prohibited_or_unknown"
    )

    assert rule.code == "ZONING_G001"
    assert rule.claim_code == "ZONING_001"
    assert rule.severity_on_fail == SeverityBand.CRITICAL


def test_load_ruleset_exposes_versioned_water_gate() -> None:
    ruleset = load_ruleset(DEFAULT_RULESET_PATH)
    rule = ruleset.hard_gate_for_condition(
        "no_plausible_water_context_or_source_unavailable"
    )

    assert rule.code == "WATER_G001"
    assert rule.claim_code == "WATER_001"
    assert rule.severity_on_fail == SeverityBand.HIGH


def test_load_ruleset_exposes_versioned_wetland_gate() -> None:
    ruleset = load_ruleset(DEFAULT_RULESET_PATH)
    rule = ruleset.hard_gate_for_condition("material_intersection_with_mapped_wetlands")

    assert rule.code == "WETLAND_G001"
    assert rule.claim_code == "WETLAND_001"
    assert rule.severity_on_fail == SeverityBand.HIGH


def test_load_ruleset_exposes_versioned_slope_gate() -> None:
    ruleset = load_ruleset(DEFAULT_RULESET_PATH)
    rule = ruleset.hard_gate_for_condition("insufficient_low_slope_buildable_area")

    assert rule.code == "SLOPE_G001"
    assert rule.claim_code == "SLOPE_001"
    assert rule.severity_on_fail == SeverityBand.HIGH


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


def test_evaluate_creates_access_claim_from_no_public_road_adjacency() -> None:
    area_id = uuid4()
    evidence = make_access_evidence(area_id=area_id, public_road_adjacency=False)
    engine = RuleEngine.from_file()

    first_result = engine.evaluate([evidence])
    second_result = engine.evaluate([evidence])

    assert first_result == second_result
    claim = first_result[0]
    assert claim.claim_code == "ACCESS_001"
    assert claim.area_id == area_id
    assert claim.rule_code == "ACCESS_G001"
    assert claim.ruleset_id == "homestead_mvp_v0_1"
    assert claim.ruleset_version == "0.1"
    assert claim.severity == SeverityBand.CRITICAL
    assert claim.confidence == ConfidenceBand.MEDIUM
    assert claim.evidence_ids == [evidence.evidence_id]
    assert claim.verification_required is True
    assert "title review" in (claim.verification_task or "")
    assert "physical proxy only" in claim.user_safe_language
    assert "does not determine recorded legal access" in claim.user_safe_language


def test_evaluate_ignores_public_road_adjacency_access_evidence() -> None:
    area_id = uuid4()
    evidence = make_access_evidence(area_id=area_id, public_road_adjacency=True)

    assert RuleEngine.from_file().evaluate([evidence]) == []


def test_evaluate_creates_unknown_claim_from_access_source_failure() -> None:
    area_id = uuid4()
    failure = make_access_failure(area_id)

    claims = RuleEngine.from_file().evaluate([failure])

    assert len(claims) == 1
    claim = claims[0]
    assert claim.claim_code == "ACCESS_SOURCE_UNAVAILABLE_UNKNOWN"
    assert claim.severity == SeverityBand.UNKNOWN
    assert claim.confidence == ConfidenceBand.UNKNOWN
    assert claim.rule_code == "ACCESS_G001"
    assert claim.evidence_ids == [failure.evidence_id]
    assert "503" in claim.user_safe_language


def test_evaluate_creates_stale_access_review_claim_from_fixture_signal() -> None:
    area_id = uuid4()
    stale_evidence = make_access_evidence(
        area_id=area_id,
        public_road_adjacency=True,
        confidence=ConfidenceBand.LOW,
        source_stale=True,
    )

    claims = RuleEngine.from_file().evaluate([stale_evidence])

    assert len(claims) == 1
    stale_claim = claims[0]
    assert stale_claim.claim_code == "ACCESS_STALE_EVIDENCE_NEEDS_REVIEW"
    assert stale_claim.severity == SeverityBand.INFORMATIONAL
    assert stale_claim.confidence == ConfidenceBand.LOW
    assert stale_claim.evidence_ids == [stale_evidence.evidence_id]
    assert "stale" in stale_claim.user_safe_language


def test_evaluate_access_outputs_are_deterministic_when_input_order_changes() -> None:
    area_id = uuid4()
    no_adjacency = make_access_evidence(
        area_id=area_id,
        public_road_adjacency=False,
    )
    adjacency = make_access_evidence(
        area_id=area_id,
        public_road_adjacency=True,
        confidence=ConfidenceBand.HIGH,
    )
    failure = make_access_failure(area_id)
    stale = make_access_evidence(
        area_id=area_id,
        public_road_adjacency=True,
        source_stale=True,
    )

    first_result = RuleEngine.from_file().evaluate(
        [stale, adjacency, failure, no_adjacency]
    )
    second_result = RuleEngine.from_file().evaluate(
        [no_adjacency, failure, adjacency, stale]
    )

    assert first_result == second_result
    assert [claim.claim_code for claim in first_result] == [
        "ACCESS_001",
        "ACCESS_SOURCE_UNAVAILABLE_UNKNOWN",
        "ACCESS_EVIDENCE_NEEDS_REVIEW",
        "ACCESS_STALE_EVIDENCE_NEEDS_REVIEW",
    ]


def test_evaluate_creates_zoning_claim_from_prohibited_intended_use() -> None:
    area_id = uuid4()
    evidence = make_zoning_evidence(area_id=area_id)
    engine = RuleEngine.from_file()

    first_result = engine.evaluate([evidence])
    second_result = engine.evaluate([evidence])

    assert first_result == second_result
    claim = first_result[0]
    assert claim.claim_code == "ZONING_001"
    assert claim.area_id == area_id
    assert claim.rule_code == "ZONING_G001"
    assert claim.ruleset_id == "homestead_mvp_v0_1"
    assert claim.ruleset_version == "0.1"
    assert claim.severity == SeverityBand.CRITICAL
    assert claim.confidence == ConfidenceBand.MEDIUM
    assert claim.evidence_ids == [evidence.evidence_id]
    assert claim.verification_required is True
    assert "county planning" in (claim.verification_task or "")
    assert "screening" in claim.user_safe_language
    assert "does not determine final legal use" in claim.user_safe_language
    assert "permit eligibility" in claim.user_safe_language


def test_evaluate_creates_zoning_claim_from_unsupported_intended_use() -> None:
    area_id = uuid4()
    evidence = EvidenceContract(
        area_id=area_id,
        source_id=uuid4(),
        evidence_type=EvidenceType.SOURCE_OBSERVATION,
        evidence_code="ZONING_USE_SCREEN",
        domain="zoning",
        observation="Fixture zoning source screens intended residential/homestead use.",
        observed_value={
            "zoning_district": "fixture-rural-district",
            "intended_residential_use_allowed": False,
        },
        method_code="fixture_zoning_use_screen",
        confidence=ConfidenceBand.MEDIUM,
        caveat="Fixture zoning/use screening only; verify with county planning.",
    )

    claims = RuleEngine.from_file().evaluate([evidence])

    assert len(claims) == 1
    claim = claims[0]
    assert claim.claim_code == "ZONING_001"
    assert claim.evidence_ids == [evidence.evidence_id]
    assert "does not determine final legal use" in claim.user_safe_language


def test_zoning_prohibited_claim_surfaces_zone_code_and_district_name() -> None:
    area_id = uuid4()
    evidence = EvidenceContract(
        area_id=area_id,
        source_id=uuid4(),
        evidence_type=EvidenceType.SOURCE_OBSERVATION,
        evidence_code="ZONING_USE_SCREEN",
        domain="zoning",
        observation="Brunswick County zoning: I-1 (Light Industrial) — residential prohibited.",
        observed_value={
            "zoning_code": "I-1",
            "district_name": "Light Industrial",
            "use_category": "Industrial",
            "intended_residential_use_prohibited": True,
        },
        method_code="live_brunswick_zoning_recorded",
        confidence=ConfidenceBand.LOW,
    )
    claims = RuleEngine.from_file().evaluate([evidence])
    zoning = [c for c in claims if c.claim_code == "ZONING_001"]
    assert len(zoning) == 1
    lang = zoning[0].user_safe_language
    assert "I-1" in lang
    assert "Light Industrial" in lang
    assert "Industrial" in lang


def test_evaluate_ignores_allowed_zoning_use_evidence() -> None:
    area_id = uuid4()
    evidence = make_zoning_evidence(
        area_id=area_id,
        intended_residential_use_prohibited=False,
        intended_residential_use_allowed=True,
    )

    assert RuleEngine.from_file().evaluate([evidence]) == []


def test_evaluate_creates_unknown_claim_from_zoning_source_failure() -> None:
    area_id = uuid4()
    failure = make_zoning_failure(area_id)

    claims = RuleEngine.from_file().evaluate([failure])

    assert len(claims) == 1
    claim = claims[0]
    assert claim.claim_code == "ZONING_SOURCE_UNAVAILABLE_UNKNOWN"
    assert claim.severity == SeverityBand.UNKNOWN
    assert claim.confidence == ConfidenceBand.UNKNOWN
    assert claim.rule_code == "ZONING_G001"
    assert claim.evidence_ids == [failure.evidence_id]
    assert "503" in claim.user_safe_language
    assert "does not establish legal use" in claim.user_safe_language


def test_evaluate_creates_stale_zoning_review_claim_from_fixture_signal() -> None:
    area_id = uuid4()
    stale_evidence = make_zoning_evidence(
        area_id=area_id,
        intended_residential_use_prohibited=False,
        intended_residential_use_allowed=True,
        confidence=ConfidenceBand.LOW,
        source_stale=True,
    )

    claims = RuleEngine.from_file().evaluate([stale_evidence])

    assert len(claims) == 1
    stale_claim = claims[0]
    assert stale_claim.claim_code == "ZONING_STALE_EVIDENCE_NEEDS_REVIEW"
    assert stale_claim.severity == SeverityBand.INFORMATIONAL
    assert stale_claim.confidence == ConfidenceBand.LOW
    assert stale_claim.evidence_ids == [stale_evidence.evidence_id]
    assert "stale" in stale_claim.user_safe_language
    assert "does not determine final legal use" in stale_claim.user_safe_language


def test_evaluate_creates_needs_review_claim_from_incomplete_zoning_evidence() -> None:
    area_id = uuid4()
    incomplete_evidence = EvidenceContract(
        area_id=area_id,
        source_id=uuid4(),
        evidence_type=EvidenceType.SOURCE_OBSERVATION,
        evidence_code="ZONING_USE_SCREEN",
        domain="zoning",
        observation="Fixture zoning source did not expose intended-use compatibility.",
        observed_value={"zoning_district": "fixture-rural-district"},
        method_code="fixture_zoning_use_screen",
        confidence=ConfidenceBand.LOW,
        caveat="Zoning fixture lacks intended-use compatibility signal.",
    )

    claims = RuleEngine.from_file().evaluate([incomplete_evidence])

    assert len(claims) == 1
    claim = claims[0]
    assert claim.claim_code == "ZONING_EVIDENCE_NEEDS_REVIEW"
    assert claim.severity == SeverityBand.UNKNOWN
    assert claim.confidence == ConfidenceBand.LOW
    assert claim.evidence_ids == [incomplete_evidence.evidence_id]
    assert "conflicting or incomplete" in claim.user_safe_language
    assert "does not determine final legal use" in claim.user_safe_language


def test_needs_review_claim_surfaces_zone_codes_from_evidence() -> None:
    area_id = uuid4()
    evidence = EvidenceContract(
        area_id=area_id,
        source_id=uuid4(),
        evidence_type=EvidenceType.SOURCE_OBSERVATION,
        evidence_code="ZONING_USE_SCREEN",
        domain="zoning",
        observation="Zoning evidence with known code but conflicting signals.",
        observed_value={"zoning_code": "RA", "zoning_district": "Rural Agricultural"},
        method_code="fixture_zoning_use_screen",
        confidence=ConfidenceBand.LOW,
        caveat="Conflicting use signals.",
    )

    claims = RuleEngine.from_file().evaluate([evidence])

    claim = next((c for c in claims if c.claim_code == "ZONING_EVIDENCE_NEEDS_REVIEW"), None)
    assert claim is not None
    assert "code(s) found: RA" in claim.user_safe_language


def test_evaluate_zoning_outputs_are_deterministic_when_input_order_changes() -> None:
    area_id = uuid4()
    prohibited = make_zoning_evidence(area_id=area_id)
    allowed = make_zoning_evidence(
        area_id=area_id,
        intended_residential_use_prohibited=False,
        intended_residential_use_allowed=True,
        confidence=ConfidenceBand.HIGH,
    )
    failure = make_zoning_failure(area_id)
    stale = make_zoning_evidence(
        area_id=area_id,
        intended_residential_use_prohibited=False,
        intended_residential_use_allowed=True,
        source_stale=True,
    )

    first_result = RuleEngine.from_file().evaluate([stale, allowed, failure, prohibited])
    second_result = RuleEngine.from_file().evaluate([prohibited, failure, allowed, stale])

    assert first_result == second_result
    assert [claim.claim_code for claim in first_result] == [
        "ZONING_001",
        "ZONING_SOURCE_UNAVAILABLE_UNKNOWN",
        "ZONING_EVIDENCE_NEEDS_REVIEW",
        "ZONING_STALE_EVIDENCE_NEEDS_REVIEW",
    ]


def test_evaluate_creates_water_claim_from_no_plausible_context() -> None:
    area_id = uuid4()
    evidence = make_water_evidence(area_id=area_id)
    engine = RuleEngine.from_file()

    first_result = engine.evaluate([evidence])
    second_result = engine.evaluate([evidence])

    assert first_result == second_result
    claim = first_result[0]
    assert claim.claim_code == "WATER_001"
    assert claim.area_id == area_id
    assert claim.rule_code == "WATER_G001"
    assert claim.ruleset_id == "homestead_mvp_v0_1"
    assert claim.ruleset_version == "0.1"
    assert claim.severity == SeverityBand.HIGH
    assert claim.confidence == ConfidenceBand.MEDIUM
    assert claim.evidence_ids == [evidence.evidence_id]
    assert claim.verification_required is True
    assert "well logs" in (claim.verification_task or "")
    assert "water-context screening" in claim.user_safe_language
    assert "does not determine water rights" in claim.user_safe_language
    assert "well yield or viability" in claim.user_safe_language
    assert "in the fixture" not in claim.user_safe_language
    assert "in the screening area" in claim.user_safe_language


def test_water_no_context_claim_surfaces_station_count_when_present() -> None:
    area_id = uuid4()
    evidence = make_water_evidence(area_id=area_id)
    evidence = EvidenceContract(
        **{**evidence.model_dump(), "observed_value": {
            **evidence.observed_value,
            "monitoring_station_count": 0,
        }}
    )
    engine = RuleEngine.from_file()

    claims = engine.evaluate([evidence])

    lang = next(c.user_safe_language for c in claims if c.claim_code == "WATER_001")
    assert "0 USGS monitoring stations" in lang


def test_evaluate_ignores_plausible_water_context_evidence() -> None:
    area_id = uuid4()
    evidence = make_water_evidence(
        area_id=area_id,
        no_plausible_water_context=False,
        plausible_water_context=True,
    )

    assert RuleEngine.from_file().evaluate([evidence]) == []


def test_evaluate_routes_internally_conflicting_water_evidence_to_review() -> None:
    area_id = uuid4()
    evidence = make_water_evidence(
        area_id=area_id,
        no_plausible_water_context=True,
        plausible_water_context=True,
    )

    claims = RuleEngine.from_file().evaluate([evidence])

    assert len(claims) == 1
    claim = claims[0]
    assert claim.claim_code == "WATER_EVIDENCE_NEEDS_REVIEW"
    assert claim.severity == SeverityBand.UNKNOWN
    assert claim.evidence_ids == [evidence.evidence_id]
    assert "conflicting or incomplete" in claim.user_safe_language
    assert "does not determine water rights" in claim.user_safe_language


def test_evaluate_creates_unknown_claim_from_water_source_failure() -> None:
    area_id = uuid4()
    failure = make_water_failure(area_id)

    claims = RuleEngine.from_file().evaluate([failure])

    assert len(claims) == 1
    claim = claims[0]
    assert claim.claim_code == "WATER_SOURCE_UNAVAILABLE_UNKNOWN"
    assert claim.severity == SeverityBand.UNKNOWN
    assert claim.confidence == ConfidenceBand.UNKNOWN
    assert claim.rule_code == "WATER_G001"
    assert claim.evidence_ids == [failure.evidence_id]
    assert "503" in claim.user_safe_language
    assert "does not establish water rights" in claim.user_safe_language


def test_evaluate_creates_needs_review_claim_from_incomplete_water_evidence() -> None:
    area_id = uuid4()
    incomplete_evidence = EvidenceContract(
        area_id=area_id,
        source_id=uuid4(),
        evidence_type=EvidenceType.SOURCE_OBSERVATION,
        evidence_code="WATER_CONTEXT_SCREEN",
        domain="water",
        observation="Fixture water source did not expose water-context compatibility.",
        observed_value={"water_context_status": "fixture-incomplete"},
        method_code="fixture_water_context_screen",
        confidence=ConfidenceBand.LOW,
        caveat="Water fixture lacks explicit context signal.",
    )

    claims = RuleEngine.from_file().evaluate([incomplete_evidence])

    assert len(claims) == 1
    claim = claims[0]
    assert claim.claim_code == "WATER_EVIDENCE_NEEDS_REVIEW"
    assert claim.severity == SeverityBand.UNKNOWN
    assert claim.confidence == ConfidenceBand.LOW
    assert claim.evidence_ids == [incomplete_evidence.evidence_id]
    assert "conflicting or incomplete" in claim.user_safe_language
    assert "does not determine water rights" in claim.user_safe_language


def test_water_needs_review_claim_surfaces_station_count() -> None:
    area_id = uuid4()
    evidence = EvidenceContract(
        area_id=area_id,
        source_id=uuid4(),
        evidence_type=EvidenceType.SOURCE_OBSERVATION,
        evidence_code="WATER_CONTEXT_SCREEN",
        domain="water",
        observation="Conflicting water context signals.",
        observed_value={
            "plausible_water_context": True,
            "no_plausible_water_context": True,
            "monitoring_station_count": 3,
        },
        method_code="fixture_water_context_screen",
        confidence=ConfidenceBand.LOW,
    )

    claims = RuleEngine.from_file().evaluate([evidence])

    claim = next((c for c in claims if c.claim_code == "WATER_EVIDENCE_NEEDS_REVIEW"), None)
    assert claim is not None
    assert "3 USGS monitoring station(s)" in claim.user_safe_language


def test_evaluate_creates_stale_water_review_claim_from_fixture_signal() -> None:
    area_id = uuid4()
    stale_evidence = make_water_evidence(
        area_id=area_id,
        no_plausible_water_context=False,
        plausible_water_context=True,
        confidence=ConfidenceBand.LOW,
        source_stale=True,
    )

    claims = RuleEngine.from_file().evaluate([stale_evidence])

    assert len(claims) == 1
    stale_claim = claims[0]
    assert stale_claim.claim_code == "WATER_STALE_EVIDENCE_NEEDS_REVIEW"
    assert stale_claim.severity == SeverityBand.INFORMATIONAL
    assert stale_claim.confidence == ConfidenceBand.LOW
    assert stale_claim.evidence_ids == [stale_evidence.evidence_id]
    assert "stale" in stale_claim.user_safe_language
    assert "does not determine water rights" in stale_claim.user_safe_language


def test_evaluate_water_outputs_are_deterministic_when_input_order_changes() -> None:
    area_id = uuid4()
    no_context = make_water_evidence(area_id=area_id)
    plausible = make_water_evidence(
        area_id=area_id,
        no_plausible_water_context=False,
        plausible_water_context=True,
        confidence=ConfidenceBand.HIGH,
    )
    failure = make_water_failure(area_id)
    stale = make_water_evidence(
        area_id=area_id,
        no_plausible_water_context=False,
        plausible_water_context=True,
        source_stale=True,
    )

    first_result = RuleEngine.from_file().evaluate([stale, plausible, failure, no_context])
    second_result = RuleEngine.from_file().evaluate([no_context, failure, plausible, stale])

    assert first_result == second_result
    assert [claim.claim_code for claim in first_result] == [
        "WATER_001",
        "WATER_SOURCE_UNAVAILABLE_UNKNOWN",
        "WATER_EVIDENCE_NEEDS_REVIEW",
        "WATER_STALE_EVIDENCE_NEEDS_REVIEW",
    ]


def test_evaluate_creates_wetland_claim_from_mapped_intersection() -> None:
    area_id = uuid4()
    evidence = make_wetland_evidence(area_id=area_id)
    engine = RuleEngine.from_file()

    first_result = engine.evaluate([evidence])
    second_result = engine.evaluate([evidence])

    assert first_result == second_result
    claim = first_result[0]
    assert claim.claim_code == "WETLAND_001"
    assert claim.area_id == area_id
    assert claim.rule_code == "WETLAND_G001"
    assert claim.ruleset_id == "homestead_mvp_v0_1"
    assert claim.ruleset_version == "0.1"
    assert claim.severity == SeverityBand.HIGH
    assert claim.confidence == ConfidenceBand.MEDIUM
    assert claim.evidence_ids == [evidence.evidence_id]
    assert claim.verification_required is True
    assert "wetland delineation" in (claim.verification_task or "")
    assert "screening" in claim.user_safe_language
    assert "not a jurisdictional wetland determination" in claim.user_safe_language


def test_evaluate_ignores_no_mapped_wetland_intersection() -> None:
    area_id = uuid4()
    evidence = make_wetland_evidence(
        area_id=area_id,
        intersects_mapped_wetlands=False,
    )

    assert RuleEngine.from_file().evaluate([evidence]) == []


def test_evaluate_creates_unknown_claim_from_wetland_source_failure() -> None:
    area_id = uuid4()
    failure = make_wetland_failure(area_id)

    claims = RuleEngine.from_file().evaluate([failure])

    assert len(claims) == 1
    claim = claims[0]
    assert claim.claim_code == "WETLAND_SOURCE_UNAVAILABLE_UNKNOWN"
    assert claim.severity == SeverityBand.UNKNOWN
    assert claim.confidence == ConfidenceBand.UNKNOWN
    assert claim.rule_code == "WETLAND_G001"
    assert claim.evidence_ids == [failure.evidence_id]
    assert "503" in claim.user_safe_language


def test_evaluate_creates_stale_wetland_review_claim_from_fixture_signal() -> None:
    area_id = uuid4()
    stale_evidence = make_wetland_evidence(
        area_id=area_id,
        intersects_mapped_wetlands=False,
        confidence=ConfidenceBand.LOW,
        source_stale=True,
    )

    claims = RuleEngine.from_file().evaluate([stale_evidence])

    assert len(claims) == 1
    stale_claim = claims[0]
    assert stale_claim.claim_code == "WETLAND_STALE_EVIDENCE_NEEDS_REVIEW"
    assert stale_claim.severity == SeverityBand.INFORMATIONAL
    assert stale_claim.confidence == ConfidenceBand.LOW
    assert stale_claim.evidence_ids == [stale_evidence.evidence_id]
    assert "stale" in stale_claim.user_safe_language


def test_evaluate_wetland_outputs_are_deterministic_when_input_order_changes() -> None:
    area_id = uuid4()
    positive = make_wetland_evidence(area_id=area_id)
    negative = make_wetland_evidence(
        area_id=area_id,
        intersects_mapped_wetlands=False,
        confidence=ConfidenceBand.HIGH,
    )
    failure = make_wetland_failure(area_id)
    stale = make_wetland_evidence(
        area_id=area_id,
        intersects_mapped_wetlands=False,
        source_stale=True,
    )

    first_result = RuleEngine.from_file().evaluate([stale, negative, failure, positive])
    second_result = RuleEngine.from_file().evaluate([positive, failure, negative, stale])

    assert first_result == second_result
    assert [claim.claim_code for claim in first_result] == [
        "WETLAND_001",
        "WETLAND_SOURCE_UNAVAILABLE_UNKNOWN",
        "WETLAND_EVIDENCE_NEEDS_REVIEW",
        "WETLAND_STALE_EVIDENCE_NEEDS_REVIEW",
    ]


def test_wetland_needs_review_claim_surfaces_feature_count_and_types() -> None:
    area_id = uuid4()
    positive = EvidenceContract(
        area_id=area_id,
        source_id=uuid4(),
        evidence_type=EvidenceType.SPATIAL_INTERSECTION,
        evidence_code="NWI_WETLAND_SCREEN",
        domain="wetlands",
        observation="NWI wetland features intersect.",
        observed_value={
            "intersects_mapped_wetlands": True,
            "mapped_wetland_area_sq_m": 2000.0,
            "wetland_class": "Palustrine",
            "wetland_type": "Emergent",
        },
        method_code="fixture_nwi_wetland_screen",
        confidence=ConfidenceBand.MEDIUM,
    )
    negative = make_wetland_evidence(
        area_id=area_id, intersects_mapped_wetlands=False, confidence=ConfidenceBand.HIGH
    )

    claims = RuleEngine.from_file().evaluate([positive, negative])

    claim = next((c for c in claims if c.claim_code == "WETLAND_EVIDENCE_NEEDS_REVIEW"), None)
    assert claim is not None
    assert "NWI feature(s) present" in claim.user_safe_language
    assert "Palustrine" in claim.user_safe_language


def test_evaluate_creates_slope_claim_from_insufficient_low_slope_area() -> None:
    area_id = uuid4()
    evidence = make_slope_evidence(area_id=area_id)
    engine = RuleEngine.from_file()

    first_result = engine.evaluate([evidence])
    second_result = engine.evaluate([evidence])

    assert first_result == second_result
    claim = first_result[0]
    assert claim.claim_code == "SLOPE_001"
    assert claim.area_id == area_id
    assert claim.rule_code == "SLOPE_G001"
    assert claim.ruleset_id == "homestead_mvp_v0_1"
    assert claim.ruleset_version == "0.1"
    assert claim.severity == SeverityBand.HIGH
    assert claim.confidence == ConfidenceBand.MEDIUM
    assert claim.evidence_ids == [evidence.evidence_id]
    assert claim.verification_required is True
    assert "surveyor/engineer" in (claim.verification_task or "")
    assert "screening proxy" in claim.user_safe_language
    assert "does not determine final buildability" in claim.user_safe_language


def test_evaluate_ignores_sufficient_low_slope_area() -> None:
    area_id = uuid4()
    evidence = make_slope_evidence(
        area_id=area_id,
        insufficient_low_slope_area=False,
    )

    assert RuleEngine.from_file().evaluate([evidence]) == []


def test_evaluate_creates_unknown_claim_from_slope_source_failure() -> None:
    area_id = uuid4()
    failure = make_slope_failure(area_id)

    claims = RuleEngine.from_file().evaluate([failure])

    assert len(claims) == 1
    claim = claims[0]
    assert claim.claim_code == "SLOPE_SOURCE_UNAVAILABLE_UNKNOWN"
    assert claim.severity == SeverityBand.UNKNOWN
    assert claim.confidence == ConfidenceBand.UNKNOWN
    assert claim.rule_code == "SLOPE_G001"
    assert claim.evidence_ids == [failure.evidence_id]
    assert "503" in claim.user_safe_language


def test_evaluate_creates_stale_slope_review_claim_from_fixture_signal() -> None:
    area_id = uuid4()
    stale_evidence = make_slope_evidence(
        area_id=area_id,
        insufficient_low_slope_area=False,
        confidence=ConfidenceBand.LOW,
        source_stale=True,
    )

    claims = RuleEngine.from_file().evaluate([stale_evidence])

    assert len(claims) == 1
    stale_claim = claims[0]
    assert stale_claim.claim_code == "SLOPE_STALE_EVIDENCE_NEEDS_REVIEW"
    assert stale_claim.severity == SeverityBand.INFORMATIONAL
    assert stale_claim.confidence == ConfidenceBand.LOW
    assert stale_claim.evidence_ids == [stale_evidence.evidence_id]
    assert "stale" in stale_claim.user_safe_language


def test_evaluate_slope_outputs_are_deterministic_when_input_order_changes() -> None:
    area_id = uuid4()
    insufficient = make_slope_evidence(area_id=area_id)
    sufficient = make_slope_evidence(
        area_id=area_id,
        insufficient_low_slope_area=False,
        confidence=ConfidenceBand.HIGH,
    )
    failure = make_slope_failure(area_id)
    stale = make_slope_evidence(
        area_id=area_id,
        insufficient_low_slope_area=False,
        source_stale=True,
    )

    first_result = RuleEngine.from_file().evaluate([stale, sufficient, failure, insufficient])
    second_result = RuleEngine.from_file().evaluate([insufficient, failure, sufficient, stale])

    assert first_result == second_result
    assert [claim.claim_code for claim in first_result] == [
        "SLOPE_001",
        "SLOPE_SOURCE_UNAVAILABLE_UNKNOWN",
        "SLOPE_EVIDENCE_NEEDS_REVIEW",
        "SLOPE_STALE_EVIDENCE_NEEDS_REVIEW",
    ]


def test_slope_needs_review_claim_surfaces_available_metrics() -> None:
    area_id = uuid4()
    insufficient = EvidenceContract(
        area_id=area_id,
        source_id=uuid4(),
        evidence_type=EvidenceType.DERIVED_METRIC,
        evidence_code="SLOPE_BUILDABLE_AREA_SCREEN",
        domain="buildability",
        observation="Conflicting slope model result.",
        observed_value={
            "insufficient_low_slope_buildable_area": True,
            "low_slope_area_ratio": 0.12,
            "mean_slope_pct": 34.5,
            "metric_code": "low_slope_buildable_area_sq_m",
            "value": 900.0,
            "unit": "sq_m",
        },
        method_code="fixture_slope_buildability_metric",
        confidence=ConfidenceBand.LOW,
    )
    sufficient = make_slope_evidence(
        area_id=area_id, insufficient_low_slope_area=False, confidence=ConfidenceBand.HIGH
    )

    claims = RuleEngine.from_file().evaluate([insufficient, sufficient])

    review_claim = next(
        (c for c in claims if c.claim_code == "SLOPE_EVIDENCE_NEEDS_REVIEW"), None
    )
    assert review_claim is not None
    assert "available metrics:" in review_claim.user_safe_language
    assert "12%" in review_claim.user_safe_language
    assert "34.5%" in review_claim.user_safe_language


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
        "FLOOD_EVIDENCE_NEEDS_REVIEW",
    ]
    assert claims[-1].evidence_ids == sorted(
        [evidence.evidence_id, failure.evidence_id],
        key=str,
    )


def test_evaluate_creates_needs_review_claim_for_contradictory_flood_evidence() -> None:
    area_id = uuid4()
    positive = make_flood_evidence(area_id=area_id, flood_zone="AE")
    negative = make_flood_evidence(
        area_id=area_id,
        flood_zone="X",
        confidence=ConfidenceBand.HIGH,
        is_negative_evidence=True,
    )

    claims = RuleEngine.from_file().evaluate([negative, positive])

    assert [claim.claim_code for claim in claims] == [
        "FLOOD_001",
        "FLOOD_EVIDENCE_NEEDS_REVIEW",
    ]
    review_claim = claims[-1]
    assert review_claim.severity == SeverityBand.UNKNOWN
    assert review_claim.confidence == ConfidenceBand.MEDIUM
    assert review_claim.verification_required is True
    assert "conflicting" in review_claim.user_safe_language
    assert "zone(s) found:" in review_claim.user_safe_language
    assert "AE" in review_claim.user_safe_language
    assert review_claim.evidence_ids == sorted(
        [positive.evidence_id, negative.evidence_id],
        key=str,
    )


def test_evaluate_creates_stale_claim_from_fixture_signal() -> None:
    area_id = uuid4()
    stale_evidence = make_flood_evidence(
        area_id=area_id,
        flood_zone="X",
        confidence=ConfidenceBand.LOW,
        source_stale=True,
    )

    claims = RuleEngine.from_file().evaluate([stale_evidence])

    assert len(claims) == 1
    stale_claim = claims[0]
    assert stale_claim.claim_code == "FLOOD_STALE_EVIDENCE_NEEDS_REVIEW"
    assert stale_claim.severity == SeverityBand.INFORMATIONAL
    assert stale_claim.confidence == ConfidenceBand.LOW
    assert stale_claim.evidence_ids == [stale_evidence.evidence_id]
    assert "stale" in stale_claim.user_safe_language


def test_evaluate_does_not_create_stale_claim_without_fixture_signal() -> None:
    area_id = uuid4()
    fresh_low_risk = make_flood_evidence(area_id=area_id, flood_zone="X")

    assert RuleEngine.from_file().evaluate([fresh_low_risk]) == []


def test_evaluate_ignores_superseded_stale_and_contradictory_evidence() -> None:
    area_id = uuid4()
    positive = make_flood_evidence(area_id=area_id, flood_zone="AE")
    superseded_negative = make_flood_evidence(
        area_id=area_id,
        flood_zone="X",
        is_negative_evidence=True,
        superseded_by=uuid4(),
    )
    superseded_stale = make_flood_evidence(
        area_id=area_id,
        flood_zone="X",
        source_stale=True,
        superseded_by=uuid4(),
    )

    claims = RuleEngine.from_file().evaluate(
        [superseded_negative, positive, superseded_stale]
    )

    assert [claim.claim_code for claim in claims] == ["FLOOD_001"]


def test_evaluate_review_outputs_are_deterministic_when_input_order_changes() -> None:
    area_id = uuid4()
    positive = make_flood_evidence(area_id=area_id, flood_zone="AE")
    failure = make_flood_failure(area_id)
    negative = make_flood_evidence(
        area_id=area_id,
        flood_zone="X",
        is_negative_evidence=True,
    )
    stale = make_flood_evidence(area_id=area_id, flood_zone="X", source_stale=True)

    first_result = RuleEngine.from_file().evaluate([stale, negative, failure, positive])
    second_result = RuleEngine.from_file().evaluate([positive, failure, negative, stale])

    assert first_result == second_result
    assert [claim.claim_code for claim in first_result] == [
        "FLOOD_001",
        "FLOOD_SOURCE_UNAVAILABLE_UNKNOWN",
        "FLOOD_EVIDENCE_NEEDS_REVIEW",
        "FLOOD_STALE_EVIDENCE_NEEDS_REVIEW",
    ]


def test_evaluate_ignores_low_risk_and_superseded_flood_evidence() -> None:
    area_id = uuid4()
    low_risk = make_flood_evidence(area_id=area_id, flood_zone="X")
    superseded = make_flood_evidence(area_id=area_id, superseded_by=uuid4())
    engine = RuleEngine.from_file()

    assert engine.evaluate([low_risk, superseded]) == []


def make_env_hazard_evidence(
    area_id: UUID,
    has_env_hazard_proximity: bool = True,
    no_env_hazard_proximity: bool | None = None,
    source_stale: bool = False,
) -> EvidenceContract:
    observed_value: dict[str, object] = {
        "env_hazard_status": (
            "regulated_facilities_found" if has_env_hazard_proximity
            else "no_regulated_facilities_found"
        ),
        "regulated_facility_count": 2 if has_env_hazard_proximity else 0,
        "has_env_hazard_proximity": has_env_hazard_proximity,
    }
    if no_env_hazard_proximity is not None:
        observed_value["no_env_hazard_proximity"] = no_env_hazard_proximity
    if source_stale:
        observed_value["source_stale"] = True
    return EvidenceContract(
        area_id=area_id,
        source_id=uuid4(),
        evidence_type=EvidenceType.SOURCE_OBSERVATION,
        evidence_code="ENV_HAZ_FACILITY_SCREEN",
        domain="env_hazard",
        observation="Fixture env_hazard source screens facility proximity.",
        observed_value=observed_value,
        method_code="fixture_env_hazard_screen",
        confidence=ConfidenceBand.MEDIUM,
        caveat="Fixture env-hazard screening only; verify with Phase I ESA.",
    )


def make_env_hazard_failure(area_id: UUID) -> EvidenceContract:
    return EvidenceContract(
        area_id=area_id,
        source_id=uuid4(),
        evidence_type=EvidenceType.SOURCE_FAILURE,
        evidence_code="ENV_HAZ_SOURCE_UNAVAILABLE",
        domain="env_hazard",
        observation="Fixture env_hazard source request failed.",
        observed_value={"failure_reason": "fixture_test_failure", "retryable": False},
        method_code="fixture_env_hazard_screen",
        confidence=ConfidenceBand.UNKNOWN,
        is_source_failure=True,
    )


def test_load_ruleset_exposes_versioned_env_hazard_gate() -> None:
    ruleset = load_ruleset(DEFAULT_RULESET_PATH)
    rule = ruleset.hard_gate_for_condition("env_hazard_facility_proximity")
    assert rule.code == "ENV_G001"
    assert rule.claim_code == "ENV_001"
    assert rule.domain == "env_hazard"


def test_evaluate_creates_env_hazard_claim_from_proximity_evidence() -> None:
    area_id = uuid4()
    engine = RuleEngine.from_file()
    evidence = make_env_hazard_evidence(area_id, has_env_hazard_proximity=True)

    claims = engine.evaluate([evidence])

    env_claims = [c for c in claims if c.domain == "env_hazard"]
    proximity_claims = [c for c in env_claims if c.claim_code == "ENV_001"]
    assert len(proximity_claims) == 1
    claim = proximity_claims[0]
    assert claim.rule_code == "ENV_G001"
    assert claim.severity == SeverityBand.HIGH
    assert claim.confidence == ConfidenceBand.MEDIUM
    assert "does not prove subject-property contamination" in claim.user_safe_language


def test_env_hazard_proximity_claim_surfaces_facility_count() -> None:
    area_id = uuid4()
    engine = RuleEngine.from_file()
    evidence = make_env_hazard_evidence(area_id, has_env_hazard_proximity=True)

    claims = engine.evaluate([evidence])

    lang = next(c.user_safe_language for c in claims if c.claim_code == "ENV_001")
    assert "2 regulated facility" in lang


def test_evaluate_ignores_no_env_hazard_proximity_evidence() -> None:
    area_id = uuid4()
    engine = RuleEngine.from_file()
    evidence = make_env_hazard_evidence(
        area_id, has_env_hazard_proximity=False, no_env_hazard_proximity=True
    )

    claims = engine.evaluate([evidence])

    env_claims = [c for c in claims if c.domain == "env_hazard"]
    assert all(c.claim_code != "ENV_001" for c in env_claims)


def test_evaluate_routes_internally_conflicting_env_hazard_evidence_to_review() -> None:
    area_id = uuid4()
    engine = RuleEngine.from_file()
    # Both has_env_hazard_proximity=True AND no_env_hazard_proximity=True in the same record
    evidence = make_env_hazard_evidence(
        area_id, has_env_hazard_proximity=True, no_env_hazard_proximity=True
    )

    claims = engine.evaluate([evidence])

    env_claims = [c for c in claims if c.domain == "env_hazard"]
    review_claims = [c for c in env_claims if c.claim_code == ENV_HAZARD_NEEDS_REVIEW_CLAIM_CODE]
    assert len(review_claims) >= 1


def test_evaluate_creates_unknown_claim_from_env_hazard_source_failure() -> None:
    area_id = uuid4()
    engine = RuleEngine.from_file()
    evidence = make_env_hazard_failure(area_id)

    claims = engine.evaluate([evidence])

    env_claims = [c for c in claims if c.domain == "env_hazard"]
    unknown_claims = [c for c in env_claims if c.claim_code == "ENV_SOURCE_UNAVAILABLE_UNKNOWN"]
    assert len(unknown_claims) == 1
    claim = unknown_claims[0]
    assert claim.rule_code == "ENV_G001"
    assert "does not prove contamination" in claim.user_safe_language.lower()


def test_evaluate_creates_needs_review_claim_from_incomplete_env_hazard_evidence() -> None:
    area_id = uuid4()
    engine = RuleEngine.from_file()
    # Evidence with no has_env_hazard_proximity and no no_env_hazard_proximity keys
    evidence = EvidenceContract(
        area_id=area_id,
        source_id=uuid4(),
        evidence_type=EvidenceType.SOURCE_OBSERVATION,
        evidence_code="ENV_HAZ_FACILITY_SCREEN",
        domain="env_hazard",
        observation="Incomplete env_hazard evidence.",
        observed_value={"env_hazard_status": "unknown"},
        method_code="fixture_env_hazard_screen",
        confidence=ConfidenceBand.MEDIUM,
    )

    claims = engine.evaluate([evidence])

    env_claims = [c for c in claims if c.domain == "env_hazard"]
    review_claims = [c for c in env_claims if c.claim_code == ENV_HAZARD_NEEDS_REVIEW_CLAIM_CODE]
    assert len(review_claims) >= 1


def test_evaluate_creates_stale_env_hazard_review_claim_from_fixture_signal() -> None:
    area_id = uuid4()
    engine = RuleEngine.from_file()
    evidence = make_env_hazard_evidence(area_id, has_env_hazard_proximity=True, source_stale=True)

    claims = engine.evaluate([evidence])

    env_claims = [c for c in claims if c.domain == "env_hazard"]
    stale_claims = [c for c in env_claims if c.claim_code == ENV_HAZARD_STALE_CLAIM_CODE]
    assert len(stale_claims) == 1


def test_evaluate_env_hazard_outputs_are_deterministic_when_input_order_changes() -> None:
    area_id = uuid4()
    engine = RuleEngine.from_file()
    proximity_ev = make_env_hazard_evidence(area_id, has_env_hazard_proximity=True)
    no_proximity_ev = make_env_hazard_evidence(
        area_id, has_env_hazard_proximity=False, no_env_hazard_proximity=True
    )
    failure_ev = make_env_hazard_failure(area_id)
    stale_ev = make_env_hazard_evidence(area_id, has_env_hazard_proximity=True, source_stale=True)

    order_a = [proximity_ev, no_proximity_ev, failure_ev, stale_ev]
    order_b = [stale_ev, failure_ev, proximity_ev, no_proximity_ev]

    claims_a = engine.evaluate(order_a)
    claims_b = engine.evaluate(order_b)

    env_a = {c.claim_code for c in claims_a if c.domain == "env_hazard"}
    env_b = {c.claim_code for c in claims_b if c.domain == "env_hazard"}
    assert env_a == env_b
    # Should produce at minimum proximity, unknown, needs-review, stale codes
    expected = {
        "ENV_001",
        "ENV_SOURCE_UNAVAILABLE_UNKNOWN",
        ENV_HAZARD_NEEDS_REVIEW_CLAIM_CODE,
        ENV_HAZARD_STALE_CLAIM_CODE,
    }
    assert expected.issubset(env_a)


def make_minerals_active_evidence(
    area_id: UUID,
    *,
    blm_active_mining_claim_count: int = 3,
    confidence: ConfidenceBand = ConfidenceBand.LOW,
) -> EvidenceContract:
    return EvidenceContract(
        area_id=area_id,
        source_id=uuid4(),
        evidence_type=EvidenceType.SPATIAL_INTERSECTION,
        evidence_code="BLM_MLRS_ACTIVE_MINING_CLAIM_CONTEXT",
        domain="minerals",
        observation=f"BLM MLRS: {blm_active_mining_claim_count} active mining claim(s) in bbox.",
        observed_value={"blm_active_mining_claim_count": blm_active_mining_claim_count},
        method_code="fixture_blm_mlrs_screen",
        confidence=confidence,
        caveat="BLM MLRS bounding-box screen only; does not determine parcel-level mineral rights.",
        is_negative_evidence=False,
    )


def make_minerals_failure_evidence(area_id: UUID) -> EvidenceContract:
    return EvidenceContract(
        area_id=area_id,
        source_id=uuid4(),
        evidence_type=EvidenceType.SOURCE_FAILURE,
        evidence_code="BLM_MLRS_SOURCE_FAILURE",
        domain="minerals",
        observation="BLM MLRS source request failed.",
        observed_value={},
        method_code="fixture_blm_mlrs_screen",
        confidence=ConfidenceBand.UNKNOWN,
        caveat="BLM MLRS endpoint unavailable.",
        is_source_failure=True,
    )


def test_minerals_active_claim_generated_when_blm_count_positive() -> None:
    area_id = uuid4()
    engine = RuleEngine.from_file()
    evidence = make_minerals_active_evidence(area_id, blm_active_mining_claim_count=2)

    claims = engine.evaluate([evidence])

    mineral_claims = [c for c in claims if c.domain == "minerals"]
    active_claims = [c for c in mineral_claims if c.claim_code == MINERALS_ACTIVE_CLAIM_CODE]
    assert len(active_claims) == 1
    assert active_claims[0].severity == SeverityBand.LOW
    assert active_claims[0].verification_required is True


def test_minerals_zero_count_generates_no_active_claim() -> None:
    area_id = uuid4()
    engine = RuleEngine.from_file()
    evidence = make_minerals_active_evidence(area_id, blm_active_mining_claim_count=0)

    claims = engine.evaluate([evidence])

    active_claims = [c for c in claims if c.claim_code == MINERALS_ACTIVE_CLAIM_CODE]
    assert len(active_claims) == 0


def test_minerals_source_failure_generates_unknown_claim() -> None:
    area_id = uuid4()
    engine = RuleEngine.from_file()
    evidence = make_minerals_failure_evidence(area_id)

    claims = engine.evaluate([evidence])

    mineral_claims = [c for c in claims if c.domain == "minerals"]
    unknown_claims = [
        c for c in mineral_claims if c.claim_code == MINERALS_SOURCE_UNAVAILABLE_CLAIM_CODE
    ]
    assert len(unknown_claims) == 1
    assert unknown_claims[0].severity == SeverityBand.UNKNOWN


def test_minerals_source_failure_suppressed_when_active_claims_present() -> None:
    area_id = uuid4()
    engine = RuleEngine.from_file()
    active_ev = make_minerals_active_evidence(area_id, blm_active_mining_claim_count=1)
    failure_ev = make_minerals_failure_evidence(area_id)

    claims = engine.evaluate([active_ev, failure_ev])

    mineral_claims = [c for c in claims if c.domain == "minerals"]
    assert any(c.claim_code == MINERALS_ACTIVE_CLAIM_CODE for c in mineral_claims)
    assert not any(
        c.claim_code == MINERALS_SOURCE_UNAVAILABLE_CLAIM_CODE for c in mineral_claims
    )


def test_minerals_active_claim_surfaces_count_and_case_name() -> None:
    area_id = uuid4()
    evidence = EvidenceContract(
        area_id=area_id,
        source_id=uuid4(),
        evidence_type=EvidenceType.SPATIAL_INTERSECTION,
        evidence_code="BLM_MLRS_ACTIVE_MINING_CLAIM_CONTEXT",
        domain="minerals",
        observation="BLM MLRS: 3 active mining claim(s) in bbox.",
        observed_value={
            "blm_active_mining_claim_count": 3,
            "primary_blm_mlrs_case_name": "Copper Creek Mining Claim",
            "primary_blm_mlrs_case_serial_number": "NMC123456",
        },
        method_code="live_blm_mlrs_screen",
        confidence=ConfidenceBand.LOW,
    )
    claims = RuleEngine.from_file().evaluate([evidence])
    active = [c for c in claims if c.claim_code == MINERALS_ACTIVE_CLAIM_CODE]
    assert len(active) == 1
    lang = active[0].user_safe_language
    assert "3 active claim(s)" in lang
    assert "Copper Creek Mining Claim" in lang
    assert "NMC123456" in lang


def make_broadband_no_access_evidence(
    area_id: UUID,
    *,
    confidence: ConfidenceBand = ConfidenceBand.LOW,
) -> EvidenceContract:
    return EvidenceContract(
        area_id=area_id,
        source_id=uuid4(),
        evidence_type=EvidenceType.SOURCE_OBSERVATION,
        evidence_code="FCC_BROADBAND_AVAILABILITY",
        domain="broadband",
        observation="FCC broadband: no providers reported in this area.",
        observed_value={"has_any_broadband": False, "provider_count": 0},
        method_code="fixture_fcc_broadband_screen",
        confidence=confidence,
        caveat="FCC broadband data may lag real availability for fixed wireless.",
        is_negative_evidence=True,
    )


def make_broadband_failure_evidence(area_id: UUID) -> EvidenceContract:
    return EvidenceContract(
        area_id=area_id,
        source_id=uuid4(),
        evidence_type=EvidenceType.SOURCE_FAILURE,
        evidence_code="FCC_BROADBAND_SOURCE_FAILURE",
        domain="broadband",
        observation="FCC broadband source request failed.",
        observed_value={},
        method_code="fixture_fcc_broadband_screen",
        confidence=ConfidenceBand.UNKNOWN,
        caveat="FCC endpoint unavailable.",
        is_source_failure=True,
    )


def test_broadband_no_access_claim_generated() -> None:
    area_id = uuid4()
    engine = RuleEngine.from_file()
    evidence = make_broadband_no_access_evidence(area_id)

    claims = engine.evaluate([evidence])

    bb_claims = [c for c in claims if c.domain == "broadband"]
    no_access = [c for c in bb_claims if c.claim_code == BROADBAND_NO_ACCESS_CLAIM_CODE]
    assert len(no_access) == 1
    assert no_access[0].severity == SeverityBand.LOW
    assert no_access[0].verification_required is True


def test_broadband_with_access_generates_no_claim() -> None:
    area_id = uuid4()
    engine = RuleEngine.from_file()
    evidence = EvidenceContract(
        area_id=area_id,
        source_id=uuid4(),
        evidence_type=EvidenceType.SOURCE_OBSERVATION,
        evidence_code="FCC_BROADBAND_AVAILABILITY",
        domain="broadband",
        observation="FCC broadband: providers available.",
        observed_value={"has_any_broadband": True, "provider_count": 3},
        method_code="fixture_fcc_broadband_screen",
        confidence=ConfidenceBand.LOW,
        caveat="FCC data may lag.",
    )

    claims = engine.evaluate([evidence])

    no_access = [c for c in claims if c.claim_code == BROADBAND_NO_ACCESS_CLAIM_CODE]
    assert len(no_access) == 0


def test_broadband_source_failure_generates_unknown_claim() -> None:
    area_id = uuid4()
    engine = RuleEngine.from_file()
    evidence = make_broadband_failure_evidence(area_id)

    claims = engine.evaluate([evidence])

    bb_claims = [c for c in claims if c.domain == "broadband"]
    unknown = [c for c in bb_claims if c.claim_code == BROADBAND_SOURCE_UNAVAILABLE_CLAIM_CODE]
    assert len(unknown) == 1
    assert unknown[0].severity == SeverityBand.UNKNOWN


def test_broadband_failure_suppressed_when_no_access_present() -> None:
    area_id = uuid4()
    engine = RuleEngine.from_file()
    no_access_ev = make_broadband_no_access_evidence(area_id)
    failure_ev = make_broadband_failure_evidence(area_id)

    claims = engine.evaluate([no_access_ev, failure_ev])

    bb_claims = [c for c in claims if c.domain == "broadband"]
    assert any(c.claim_code == BROADBAND_NO_ACCESS_CLAIM_CODE for c in bb_claims)
    assert not any(
        c.claim_code == BROADBAND_SOURCE_UNAVAILABLE_CLAIM_CODE for c in bb_claims
    )


def test_evaluate_creates_flood_moderate_claim_from_x500_zone() -> None:
    area_id = uuid4()
    evidence = EvidenceContract(
        area_id=area_id,
        source_id=uuid4(),
        evidence_type=EvidenceType.SPATIAL_INTERSECTION,
        evidence_code="FLOOD_ZONE_SCREEN",
        domain="flood",
        observation="FEMA NFHL: Zone X500 intersection.",
        observed_value={"flood_zone_code": "X500"},
        method_code="fema_nfhl_wfs_live",
        confidence=ConfidenceBand.MEDIUM,
        caveat="FEMA NFHL screening only.",
    )

    claims = RuleEngine.from_file().evaluate([evidence])

    moderate_claims = [c for c in claims if c.claim_code == FLOOD_MODERATE_CLAIM_CODE]
    assert len(moderate_claims) == 1
    claim = moderate_claims[0]
    assert claim.area_id == area_id
    assert claim.severity == SeverityBand.LOW
    assert claim.verification_required is True
    assert "X500" in claim.assertion or "X500" in claim.user_safe_language


def test_flood_positive_claim_surfaces_zone_code() -> None:
    evidence = EvidenceContract(
        area_id=uuid4(),
        source_id=uuid4(),
        evidence_type=EvidenceType.SPATIAL_INTERSECTION,
        evidence_code="FLOOD_ZONE_SCREEN",
        domain="flood",
        observation="FEMA NFHL: Zone AE intersection.",
        observed_value={"flood_zone_code": "AE"},
        method_code="fema_nfhl_wfs_live",
        confidence=ConfidenceBand.MEDIUM,
    )
    claims = RuleEngine.from_file().evaluate([evidence])
    flood_claims = [c for c in claims if c.claim_code == "FLOOD_001"]
    assert len(flood_claims) == 1
    lang = flood_claims[0].user_safe_language
    assert "AE" in lang
    assert "high-risk flood zone" in lang.lower()


def test_evaluate_does_not_create_moderate_flood_claim_for_high_risk_zone() -> None:
    evidence = EvidenceContract(
        area_id=uuid4(),
        source_id=uuid4(),
        evidence_type=EvidenceType.SPATIAL_INTERSECTION,
        evidence_code="FLOOD_ZONE_SCREEN",
        domain="flood",
        observation="FEMA NFHL: Zone AE intersection.",
        observed_value={"flood_zone_code": "AE"},
        method_code="fema_nfhl_wfs_live",
        confidence=ConfidenceBand.MEDIUM,
        caveat="FEMA NFHL screening only.",
    )

    claims = RuleEngine.from_file().evaluate([evidence])
    moderate_claims = [c for c in claims if c.claim_code == FLOOD_MODERATE_CLAIM_CODE]
    assert len(moderate_claims) == 0


def test_evaluate_creates_soil_poor_drainage_claim_from_poorly_drained_evidence() -> None:
    area_id = uuid4()
    evidence = EvidenceContract(
        area_id=area_id,
        source_id=uuid4(),
        evidence_type=EvidenceType.SPATIAL_INTERSECTION,
        evidence_code="SSURGO_SOIL_MAPUNIT_INTERSECTION",
        domain="soil_septic",
        observation="USDA NRCS SSURGO mapunit intersects the query area.",
        observed_value={
            "intersects_soil_mapunit": True,
            "soil_mapunit_key": "123456",
            "drainage_class": "poorly drained",
            "hydric_rating": "No",
        },
        method_code="live_usda_ssurgo_soil_mapunit_query",
        confidence=ConfidenceBand.MEDIUM,
        caveat="SSURGO screening only.",
    )

    claims = RuleEngine.from_file().evaluate([evidence])

    drainage_claims = [c for c in claims if c.claim_code == SOIL_POOR_DRAINAGE_CLAIM_CODE]
    assert len(drainage_claims) == 1
    claim = drainage_claims[0]
    assert claim.area_id == area_id
    assert claim.severity == SeverityBand.LOW
    assert claim.verification_required is True
    assert "poorly drained" in claim.user_safe_language.lower()


def test_evaluate_creates_soil_poor_drainage_claim_from_hydric_evidence() -> None:
    area_id = uuid4()
    evidence = EvidenceContract(
        area_id=area_id,
        source_id=uuid4(),
        evidence_type=EvidenceType.SPATIAL_INTERSECTION,
        evidence_code="SSURGO_SOIL_MAPUNIT_INTERSECTION",
        domain="soil_septic",
        observation="USDA NRCS SSURGO mapunit intersects the query area.",
        observed_value={
            "intersects_soil_mapunit": True,
            "soil_mapunit_key": "789012",
            "drainage_class": "very poorly drained",
            "hydric_rating": "Yes",
        },
        method_code="live_usda_ssurgo_soil_mapunit_query",
        confidence=ConfidenceBand.MEDIUM,
        caveat="SSURGO screening only.",
    )

    claims = RuleEngine.from_file().evaluate([evidence])

    drainage_claims = [c for c in claims if c.claim_code == SOIL_POOR_DRAINAGE_CLAIM_CODE]
    assert len(drainage_claims) == 1
    assert "hydric" in drainage_claims[0].user_safe_language.lower()


def test_evaluate_soil_drainage_claim_includes_water_table_depth_when_present() -> None:
    area_id = uuid4()
    evidence = EvidenceContract(
        area_id=area_id,
        source_id=uuid4(),
        evidence_type=EvidenceType.SPATIAL_INTERSECTION,
        evidence_code="SSURGO_SOIL_MAPUNIT_INTERSECTION",
        domain="soil_septic",
        observation="USDA NRCS SSURGO mapunit intersects the query area.",
        observed_value={
            "intersects_soil_mapunit": True,
            "soil_mapunit_key": "123456",
            "drainage_class": "poorly drained",
            "hydric_rating": "No",
            "water_table_depth_cm": 30,
        },
        method_code="live_usda_ssurgo_soil_mapunit_query",
        confidence=ConfidenceBand.MEDIUM,
        caveat="SSURGO screening only.",
    )

    claims = RuleEngine.from_file().evaluate([evidence])
    drainage_claims = [c for c in claims if c.claim_code == SOIL_POOR_DRAINAGE_CLAIM_CODE]
    assert len(drainage_claims) == 1
    assert "30" in drainage_claims[0].user_safe_language
    assert "water table" in drainage_claims[0].user_safe_language.lower()


def test_evaluate_does_not_create_soil_drainage_claim_for_well_drained_soils() -> None:
    evidence = EvidenceContract(
        area_id=uuid4(),
        source_id=uuid4(),
        evidence_type=EvidenceType.SPATIAL_INTERSECTION,
        evidence_code="SSURGO_SOIL_MAPUNIT_INTERSECTION",
        domain="soil_septic",
        observation="USDA NRCS SSURGO mapunit intersects the query area.",
        observed_value={
            "intersects_soil_mapunit": True,
            "soil_mapunit_key": "999",
            "drainage_class": "well drained",
            "hydric_rating": "No",
        },
        method_code="live_usda_ssurgo_soil_mapunit_query",
        confidence=ConfidenceBand.MEDIUM,
        caveat="SSURGO screening only.",
    )

    claims = RuleEngine.from_file().evaluate([evidence])
    drainage_claims = [c for c in claims if c.claim_code == SOIL_POOR_DRAINAGE_CLAIM_CODE]
    assert len(drainage_claims) == 0


def test_evaluate_creates_geology_not_evaluated_claim_when_hazard_not_determined() -> None:
    area_id = uuid4()
    evidence = EvidenceContract(
        area_id=area_id,
        source_id=uuid4(),
        evidence_type=EvidenceType.SPATIAL_INTERSECTION,
        evidence_code="NCGS_GEOLOGIC_MAP_INTERSECTION",
        domain="geology",
        observation="NC geologic map unit intersects query area.",
        observed_value={
            "geologic_unit_labels": ["Ts"],
            "geologic_hazard_determined": False,
            "buildability_determined": False,
        },
        method_code="fixture_ncgs_geologic_map",
        confidence=ConfidenceBand.LOW,
        caveat="Regional 1:500k map — not parcel-scale.",
    )

    claims = RuleEngine.from_file().evaluate([evidence])
    geology_claims = [c for c in claims if c.claim_code == GEOLOGY_NOT_EVALUATED_CLAIM_CODE]
    assert len(geology_claims) == 1
    claim = geology_claims[0]
    assert claim.area_id == area_id
    assert claim.domain == "geology"
    assert claim.verification_required is True


def test_evaluate_does_not_create_geology_claim_when_hazard_determined() -> None:
    evidence = EvidenceContract(
        area_id=uuid4(),
        source_id=uuid4(),
        evidence_type=EvidenceType.SPATIAL_INTERSECTION,
        evidence_code="NCGS_GEOLOGIC_MAP_INTERSECTION",
        domain="geology",
        observation="NC geologic map unit intersects query area.",
        observed_value={
            "geologic_unit_labels": ["Ts"],
            "geologic_hazard_determined": True,
        },
        method_code="fixture_ncgs_geologic_map",
        confidence=ConfidenceBand.LOW,
        caveat="Regional map only.",
    )

    claims = RuleEngine.from_file().evaluate([evidence])
    geology_claims = [c for c in claims if c.claim_code == GEOLOGY_NOT_EVALUATED_CLAIM_CODE]
    assert len(geology_claims) == 0


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


def test_wetland_claim_surfaces_feature_count_and_mapped_area() -> None:
    area_id = uuid4()
    evidence = make_wetland_evidence(area_id=area_id)
    claims = RuleEngine.from_file().evaluate([evidence])
    wetland_claims = [c for c in claims if c.claim_code == "WETLAND_001"]
    assert len(wetland_claims) == 1
    lang = wetland_claims[0].user_safe_language
    assert "1 NWI feature(s)" in lang
    assert "0.42" in lang or "mapped acres" in lang


def test_wetland_claim_surfaces_wetland_class_when_present() -> None:
    area_id = uuid4()
    evidence = EvidenceContract(
        area_id=area_id,
        source_id=uuid4(),
        evidence_type=EvidenceType.SPATIAL_INTERSECTION,
        evidence_code="WETLAND_SCREEN",
        domain="wetlands",
        observation="NWI wetland intersects area.",
        observed_value={
            "intersects_mapped_wetlands": True,
            "mapped_wetland_area_sq_m": 4047.0,
            "wetland_class": "Freshwater Emergent Wetland",
            "wetland_type": "PEM1C",
        },
        method_code="live_fws_nwi_spatial_query",
        confidence=ConfidenceBand.MEDIUM,
    )
    claims = RuleEngine.from_file().evaluate([evidence])
    wetland_claims = [c for c in claims if c.claim_code == "WETLAND_001"]
    assert len(wetland_claims) == 1
    lang = wetland_claims[0].user_safe_language
    assert "Freshwater Emergent Wetland" in lang
    assert "1.00" in lang or "mapped acres" in lang


def test_slope_insufficient_claim_surfaces_buildable_area_in_acres() -> None:
    area_id = uuid4()
    evidence = make_slope_evidence(area_id=area_id, insufficient_low_slope_area=True)
    claims = RuleEngine.from_file().evaluate([evidence])
    slope_claims = [c for c in claims if c.claim_code == "SLOPE_001"]
    assert len(slope_claims) == 1
    lang = slope_claims[0].user_safe_language
    assert "0.22" in lang or "ac low-slope" in lang


def test_geology_not_evaluated_claim_surfaces_primary_unit_when_present() -> None:
    area_id = uuid4()
    evidence = EvidenceContract(
        area_id=area_id,
        source_id=uuid4(),
        evidence_type=EvidenceType.SPATIAL_INTERSECTION,
        evidence_code="NC_GEOLOGIC_MAP_UNIT_CONTEXT",
        domain="geology",
        observation="NC geologic map unit intersects query area.",
        observed_value={
            "geologic_hazard_determined": False,
            "buildability_determined": False,
            "primary_geologic_unit_label": "GEL",
            "primary_geologic_formation": "Metavolcanic sequence",
        },
        method_code="live_nc_geologic_map_unit_context",
        confidence=ConfidenceBand.LOW,
    )
    claims = RuleEngine.from_file().evaluate([evidence])
    geology_claims = [c for c in claims if c.claim_code == GEOLOGY_NOT_EVALUATED_CLAIM_CODE]
    assert len(geology_claims) == 1
    lang = geology_claims[0].user_safe_language
    assert "GEL" in lang
    assert "Metavolcanic sequence" in lang


def test_soil_screening_review_claim_surfaces_mapunit_name_and_hydrologic_group() -> None:
    area_id = uuid4()
    evidence = EvidenceContract(
        area_id=area_id,
        source_id=uuid4(),
        evidence_type=EvidenceType.SPATIAL_INTERSECTION,
        evidence_code="SSURGO_SOIL_MAPUNIT_INTERSECTION",
        domain="soil_septic",
        observation="USDA NRCS SSURGO mapunit intersects the query area.",
        observed_value={
            "intersects_soil_mapunit": True,
            "soil_mapunit_key": "111222",
            "soil_mapunit_name": "Cecil sandy loam",
            "hydrologic_group": "B",
            "drainage_class": "well drained",
            "hydric_rating": "No",
        },
        method_code="live_usda_ssurgo_soil_mapunit_query",
        confidence=ConfidenceBand.MEDIUM,
    )
    claims = RuleEngine.from_file().evaluate([evidence])
    soil_review_claims = [c for c in claims if c.claim_code == "SOIL_NOT_EVALUATED"]
    assert len(soil_review_claims) == 1
    lang = soil_review_claims[0].user_safe_language
    assert "Cecil sandy loam" in lang
    assert "hydrologic group B" in lang


def test_access_no_adjacency_claim_surfaces_road_count_when_zero() -> None:
    area_id = uuid4()
    evidence = EvidenceContract(
        area_id=area_id,
        source_id=uuid4(),
        evidence_type=EvidenceType.SPATIAL_INTERSECTION,
        evidence_code="ACCESS_ROAD_ADJACENCY_SCREEN",
        domain="access",
        observation="OSM Overpass query found no road ways adjacent to the query area.",
        observed_value={
            "has_public_road_adjacency": False,
            "public_road_adjacency": False,
            "no_public_road_adjacency": True,
            "road_count": 0,
            "highway_types": [],
        },
        method_code="live_osm_road_adjacency_bbox_screen",
        confidence=ConfidenceBand.LOW,
    )
    claims = RuleEngine.from_file().evaluate([evidence])
    access_claims = [c for c in claims if c.claim_code == "ACCESS_001"]
    assert len(access_claims) == 1
    lang = access_claims[0].user_safe_language
    assert "0 OSM road segments in screening area" in lang
    assert "physical proxy only" in lang
