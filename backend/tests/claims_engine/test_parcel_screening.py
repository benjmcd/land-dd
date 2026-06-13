from __future__ import annotations

from uuid import UUID, uuid4

from app.claims_engine.rule_engine import (
    RuleEngine,
    _is_county_parcel_screen_evidence,
)
from app.domain.enums import ConfidenceBand, EvidenceType, SeverityBand
from app.domain.evidence_contracts import EvidenceContract


def _make_parcel_evidence(
    area_id: UUID,
    *,
    evidence_code: str = "COUNTY_PARCEL_INTERSECTION",
    is_source_failure: bool = False,
    parcel_pin: str = "0060143",
    parcel_acres: float = 42.5,
    parcel_zoning: str = "RA",
    parcel_county: str = "Chatham County, NC",
) -> EvidenceContract:
    return EvidenceContract(
        area_id=area_id,
        source_id=uuid4(),
        evidence_type=EvidenceType.SPATIAL_INTERSECTION,
        evidence_code=evidence_code,
        domain="parcels",
        observation="County GIS parcel intersects AOI.",
        observed_value={
            "parcel_pin": parcel_pin,
            "parcel_acres": parcel_acres,
            "parcel_zoning": parcel_zoning,
            "parcel_county": parcel_county,
        },
        method_code="chatham_parcels_live",
        confidence=ConfidenceBand.LOW,
        caveat="Parcel boundaries from county GIS are approximate; not survey-grade.",
        is_source_failure=is_source_failure,
    )


def test_is_county_parcel_screen_evidence_detects_live_evidence() -> None:
    area_id = uuid4()
    ev = _make_parcel_evidence(area_id)

    assert _is_county_parcel_screen_evidence(ev) is True


def test_is_county_parcel_screen_evidence_rejects_fixture_screen_code() -> None:
    area_id = uuid4()
    ev = _make_parcel_evidence(area_id, evidence_code="PARCEL_INTERSECTION_SCREEN")

    assert _is_county_parcel_screen_evidence(ev) is False


def test_is_county_parcel_screen_evidence_rejects_source_failure() -> None:
    area_id = uuid4()
    ev = _make_parcel_evidence(area_id, is_source_failure=True)

    assert _is_county_parcel_screen_evidence(ev) is False


def test_is_county_parcel_screen_evidence_rejects_wrong_domain() -> None:
    area_id = uuid4()
    ev = _make_parcel_evidence(area_id)
    ev = ev.model_copy(update={"domain": "flood"})

    assert _is_county_parcel_screen_evidence(ev) is False


def test_parcel_screen_claim_fires_on_county_parcel_intersection() -> None:
    area_id = uuid4()
    ev = _make_parcel_evidence(area_id)
    engine = RuleEngine.from_file()

    claims = engine.evaluate([ev])

    parcel_claims = [c for c in claims if c.claim_code == "PARCEL_SCREEN_001"]
    assert len(parcel_claims) == 1
    claim = parcel_claims[0]
    assert claim.severity == SeverityBand.UNKNOWN
    assert claim.confidence == ConfidenceBand.LOW
    assert claim.domain == "parcels"
    assert claim.rule_code == "PARCEL_SCREEN_G001"
    assert claim.verification_required is True
    assert ev.evidence_id in claim.evidence_ids
    assert claim.ruleset_id == "homestead_mvp_v0_1"
    assert "county gis" in claim.user_safe_language.lower()
    assert "survey" in claim.user_safe_language.lower()


def test_parcel_screen_claim_not_fired_for_fixture_connector_evidence() -> None:
    area_id = uuid4()
    ev = _make_parcel_evidence(area_id, evidence_code="PARCEL_INTERSECTION_SCREEN")
    engine = RuleEngine.from_file()

    claims = engine.evaluate([ev])

    parcel_claims = [c for c in claims if c.claim_code == "PARCEL_SCREEN_001"]
    assert len(parcel_claims) == 0


def test_parcel_screen_claim_is_deterministic() -> None:
    area_id = uuid4()
    ev = _make_parcel_evidence(area_id)
    engine = RuleEngine.from_file()

    first = engine.evaluate([ev])
    second = engine.evaluate([ev])

    first_claim = next(c for c in first if c.claim_code == "PARCEL_SCREEN_001")
    second_claim = next(c for c in second if c.claim_code == "PARCEL_SCREEN_001")
    assert first_claim.claim_id == second_claim.claim_id


def test_parcel_screen_claim_does_not_fire_for_source_failure() -> None:
    area_id = uuid4()
    ev = _make_parcel_evidence(area_id, is_source_failure=True)
    engine = RuleEngine.from_file()

    claims = engine.evaluate([ev])

    parcel_claims = [c for c in claims if c.claim_code == "PARCEL_SCREEN_001"]
    assert len(parcel_claims) == 0


def test_parcel_screen_claim_includes_caveat_from_evidence() -> None:
    area_id = uuid4()
    ev = _make_parcel_evidence(area_id)
    engine = RuleEngine.from_file()

    claims = engine.evaluate([ev])

    claim = next(c for c in claims if c.claim_code == "PARCEL_SCREEN_001")
    assert "approximate" in claim.user_safe_language.lower()


def test_parcel_screen_claim_surfaces_pin_acreage_and_county() -> None:
    area_id = uuid4()
    ev = _make_parcel_evidence(area_id, parcel_pin="1234567", parcel_acres=17.3)
    engine = RuleEngine.from_file()

    claims = engine.evaluate([ev])

    lang = next(c.user_safe_language for c in claims if c.claim_code == "PARCEL_SCREEN_001")
    assert "1234567" in lang
    assert "17.3" in lang
    assert "Chatham County, NC" in lang
