from __future__ import annotations

import textwrap
from pathlib import Path
from uuid import uuid4

import pytest

from app.claims_engine.rule_engine import DEFAULT_RULESET_PATH, RuleEngine
from app.domain.claim_contracts import ClaimContract
from app.domain.enums import ConfidenceBand, EvidenceType, SeverityBand
from app.domain.evidence_contracts import EvidenceContract

# ---------------------------------------------------------------------------
# Minimal fake YAML fixture
# ---------------------------------------------------------------------------

_MINIMAL_RULESET_YAML = textwrap.dedent("""\
    ruleset:
      id: test-ruleset
      version: 0.0.1
      hard_gates:
        - code: HG-ACCESS-001
          domain: access
          severity_on_fail: critical
          condition: no_public_road_adjacency_or_access_source_unavailable
          claim_code: ACCESS_NO_PUBLIC_ROAD
          verification_task: Verify legal road access with county recorder and survey.
        - code: HG-ZONING-001
          domain: zoning
          severity_on_fail: critical
          condition: intended_residential_use_prohibited_or_unknown
          claim_code: ZONING_INTENDED_USE
          verification_task: Verify permitted zoning use with county planning department.
        - code: HG-WATER-001
          domain: water
          severity_on_fail: high
          condition: no_plausible_water_context_or_source_unavailable
          claim_code: WATER_CONTEXT
          verification_task: Verify water source with county and state water authority.
        - code: HG-FLOOD-001
          domain: flood
          severity_on_fail: high
          condition: material_intersection_with_high_risk_flood_zone
          claim_code: FLOOD_HIGH_RISK
          verification_task: Obtain elevation certificate and confirm FEMA flood map.
        - code: HG-SLOPE-001
          domain: slope
          severity_on_fail: high
          condition: insufficient_low_slope_buildable_area
          claim_code: SLOPE_INSUFFICIENT
          verification_task: Commission site engineering review for slope constraints.
        - code: HG-WETLAND-001
          domain: wetlands
          severity_on_fail: critical
          condition: material_intersection_with_mapped_wetlands
          claim_code: WETLAND_MAPPED
          verification_task: Commission jurisdictional wetland delineation.
        - code: HG-SOIL-001
          domain: soil_septic
          severity_on_fail: informational
          condition: soil_septic_unsupported
          claim_code: SOIL_NOT_EVALUATED
          verification_task: Verify soil and septic feasibility with local professionals.
        - code: HG-ENV-001
          domain: env_hazard
          severity_on_fail: informational
          condition: env_hazard_unsupported
          claim_code: ENV_HAZ_NOT_EVALUATED
          verification_task: Review environmental hazard records.
        - code: HG-RESOURCE-001
          domain: resource_context
          severity_on_fail: informational
          condition: resource_context_unsupported
          claim_code: RESOURCE_NOT_EVALUATED
          verification_task: Review title and state resource records.
        - code: HG-MARKET-001
          domain: market_context
          severity_on_fail: informational
          condition: market_context_out_of_scope
          claim_code: MARKET_OUT_OF_SCOPE
          verification_task: Consult qualified local professionals for market context.
      forbidden_language:
        - You can build here.
        - This parcel has legal access.
""")


def _write_temp_ruleset(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "ruleset.yaml"
    p.write_text(content, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# 1. Test that the default YAML loads the 6 forbidden phrases
# ---------------------------------------------------------------------------


def test_from_file_loads_all_six_forbidden_phrases() -> None:
    engine = RuleEngine.from_file(DEFAULT_RULESET_PATH)
    forbidden = engine._ruleset.forbidden_language  # noqa: SLF001 (white-box test)
    assert len(forbidden) == 6, f"Expected 6 forbidden phrases, got {len(forbidden)}: {forbidden}"
    expected = {
        "You can build here.",
        "This parcel has legal access.",
        "This land has water rights.",
        "This property is safe.",
        "This property is worth",
        "No environmental problems exist.",
    }
    assert forbidden == expected


# ---------------------------------------------------------------------------
# 2. Test that evaluate() raises ValueError when a claim contains a phrase
# ---------------------------------------------------------------------------


def test_evaluate_raises_on_forbidden_assertion(tmp_path: Path) -> None:
    ruleset_path = _write_temp_ruleset(tmp_path, _MINIMAL_RULESET_YAML)
    engine = RuleEngine.from_file(ruleset_path)

    area_id = uuid4()
    # Produce a claim with forbidden text by injecting it directly via
    # _check_forbidden_language (white-box), then verify evaluate() raises.
    forbidden_claim = ClaimContract(
        area_id=area_id,
        claim_code="ACCESS_NO_PUBLIC_ROAD",
        domain="access",
        assertion="You can build here. Road adjacency screening found no adjacency.",
        user_safe_language="Nothing of note.",
        severity=SeverityBand.CRITICAL,
        evidence_ids=[uuid4()],
    )
    with pytest.raises(ValueError, match="forbidden language"):
        engine._check_forbidden_language(forbidden_claim)  # noqa: SLF001


def test_evaluate_raises_on_forbidden_user_safe_language(tmp_path: Path) -> None:
    ruleset_path = _write_temp_ruleset(tmp_path, _MINIMAL_RULESET_YAML)
    engine = RuleEngine.from_file(ruleset_path)

    area_id = uuid4()
    forbidden_claim = ClaimContract(
        area_id=area_id,
        claim_code="ACCESS_NO_PUBLIC_ROAD",
        domain="access",
        assertion="Road screening found no adjacency.",
        user_safe_language="This parcel has legal access. Please verify.",
        severity=SeverityBand.CRITICAL,
        evidence_ids=[uuid4()],
    )
    with pytest.raises(ValueError, match="forbidden language"):
        engine._check_forbidden_language(forbidden_claim)  # noqa: SLF001


def test_evaluate_raises_via_evaluate_pipeline(tmp_path: Path) -> None:
    """Confirm the forbidden-language check is wired into evaluate() end-to-end."""
    # Build a ruleset that has one forbidden phrase and a monkey-patched
    # evaluate path. We do this by subclassing RuleEngine, overriding
    # _access_no_adjacency_claim to inject forbidden text, and confirming
    # evaluate() raises.
    ruleset_path = _write_temp_ruleset(tmp_path, _MINIMAL_RULESET_YAML)
    engine = RuleEngine.from_file(ruleset_path)

    area_id = uuid4()
    # Produce access evidence that will trigger _access_no_adjacency_claim.
    evidence = EvidenceContract(
        area_id=area_id,
        source_id=uuid4(),
        evidence_type=EvidenceType.SPATIAL_INTERSECTION,
        evidence_code="ACCESS_ROAD_ADJACENCY_SCREEN",
        domain="access",
        observation="No road adjacency detected.",
        observed_value={"public_road_adjacency": False},
        method_code="fixture_road_adjacency_overlay",
        confidence=ConfidenceBand.MEDIUM,
        caveat="Screening fixture only.",
    )

    # Monkey-patch the claim builder to inject forbidden text.
    original = engine._access_no_adjacency_claim  # noqa: SLF001

    def _patched_claim(*args, **kwargs):  # type: ignore[no-untyped-def]
        claim = original(*args, **kwargs)
        return claim.model_copy(
            update={"assertion": "You can build here. " + claim.assertion}
        )

    engine._access_no_adjacency_claim = _patched_claim  # type: ignore[method-assign]  # noqa: SLF001

    with pytest.raises(ValueError, match="forbidden language"):
        engine.evaluate([evidence])


# ---------------------------------------------------------------------------
# 3. Test that normal claims pass through without error
# ---------------------------------------------------------------------------


def test_evaluate_passes_for_clean_claims(tmp_path: Path) -> None:
    ruleset_path = _write_temp_ruleset(tmp_path, _MINIMAL_RULESET_YAML)
    engine = RuleEngine.from_file(ruleset_path)

    area_id = uuid4()
    evidence = EvidenceContract(
        area_id=area_id,
        source_id=uuid4(),
        evidence_type=EvidenceType.SPATIAL_INTERSECTION,
        evidence_code="ACCESS_ROAD_ADJACENCY_SCREEN",
        domain="access",
        observation="No road adjacency detected.",
        observed_value={"public_road_adjacency": False},
        method_code="fixture_road_adjacency_overlay",
        confidence=ConfidenceBand.MEDIUM,
        caveat="Screening fixture only.",
    )
    # Should not raise — the generated assertion text never contains
    # "You can build here." or "This parcel has legal access."
    claims = engine.evaluate([evidence])
    assert len(claims) >= 1


def test_check_forbidden_language_passes_for_clean_claim(tmp_path: Path) -> None:
    ruleset_path = _write_temp_ruleset(tmp_path, _MINIMAL_RULESET_YAML)
    engine = RuleEngine.from_file(ruleset_path)

    area_id = uuid4()
    clean_claim = ClaimContract(
        area_id=area_id,
        claim_code="ACCESS_NO_PUBLIC_ROAD",
        domain="access",
        assertion="Screening evidence found no apparent public road adjacency.",
        user_safe_language="Road adjacency screening indicates no apparent public road adjacency.",
        severity=SeverityBand.CRITICAL,
        evidence_ids=[uuid4()],
    )
    # Must not raise
    engine._check_forbidden_language(clean_claim)  # noqa: SLF001


def test_forbidden_language_check_is_case_insensitive(tmp_path: Path) -> None:
    ruleset_path = _write_temp_ruleset(tmp_path, _MINIMAL_RULESET_YAML)
    engine = RuleEngine.from_file(ruleset_path)

    area_id = uuid4()
    # Uppercase variant of a forbidden phrase
    forbidden_claim = ClaimContract(
        area_id=area_id,
        claim_code="ACCESS_NO_PUBLIC_ROAD",
        domain="access",
        assertion="YOU CAN BUILD HERE. See details.",
        user_safe_language="Nothing of note.",
        severity=SeverityBand.CRITICAL,
        evidence_ids=[uuid4()],
    )
    with pytest.raises(ValueError, match="forbidden language"):
        engine._check_forbidden_language(forbidden_claim)  # noqa: SLF001
