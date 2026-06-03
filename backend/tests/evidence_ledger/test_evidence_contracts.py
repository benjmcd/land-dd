from __future__ import annotations

from uuid import uuid4

from app.domain.enums import ConfidenceBand, EvidenceType
from app.domain.evidence_contracts import EvidenceContract


def test_evidence_requires_source_and_method_context() -> None:
    evidence = EvidenceContract(
        area_id=uuid4(),
        evidence_type=EvidenceType.SOURCE_FAILURE,
        evidence_code="SOURCE_UNAVAILABLE",
        domain="flood",
        observation="FEMA NFHL endpoint returned HTTP 503; flood data unavailable.",
        source_id=uuid4(),
        method_code="fixture_test",
        confidence=ConfidenceBand.UNKNOWN,
        is_source_failure=True,
    )
    assert evidence.source_id
    assert evidence.method_code == "fixture_test"
    assert evidence.is_source_failure is True


def test_evidence_stores_caveat_and_observed_value() -> None:
    evidence = EvidenceContract(
        area_id=uuid4(),
        evidence_code="FLOOD_ZONE_AE",
        domain="flood",
        observation="Parcel intersects FEMA SFHA Zone AE.",
        observed_value={"flood_zone": "AE", "bfe_ft": 2310},
        source_id=uuid4(),
        method_code="fema_nfhl_intersection",
        confidence=ConfidenceBand.MEDIUM,
        caveat="Effective map; modernized map may differ.",
    )
    assert evidence.observed_value["flood_zone"] == "AE"
    assert evidence.caveat is not None


def test_evidence_type_and_confidence_are_separate_fields() -> None:
    evidence = EvidenceContract(
        area_id=uuid4(),
        evidence_code="SOIL_PERC_RATE",
        domain="soils",
        observation="SSURGO indicates limited perc rate.",
        source_id=uuid4(),
        method_code="ssurgo_lookup",
        evidence_type=EvidenceType.DERIVED_METRIC,
        confidence=ConfidenceBand.LOW,
    )
    assert evidence.evidence_type == EvidenceType.DERIVED_METRIC
    assert evidence.confidence == ConfidenceBand.LOW
