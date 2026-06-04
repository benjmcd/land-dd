from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError

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


def test_evidence_contract_captures_geometry_and_spatial_precision() -> None:
    evidence = EvidenceContract(
        area_id=uuid4(),
        evidence_code="FLOOD_ZONE_AE",
        domain="flood",
        observation="Flood source geometry intersects the area.",
        source_id=uuid4(),
        method_code="fixture_flood_overlay",
        evidence_type=EvidenceType.SPATIAL_INTERSECTION,
        geometry_geojson={
            "type": "Point",
            "coordinates": [-120.0, 38.0],
        },
        spatial_precision_meters=15.5,
    )

    assert evidence.geometry_srid == 4326
    assert evidence.geometry_geojson is not None
    assert evidence.geometry_geojson["type"] == "Point"
    assert evidence.spatial_precision_meters == 15.5


def test_evidence_contract_rejects_wrong_geometry_srid() -> None:
    with pytest.raises(ValidationError, match="geometry SRID must be 4326"):
        EvidenceContract(
            area_id=uuid4(),
            evidence_code="FLOOD_ZONE_AE",
            domain="flood",
            observation="Flood source geometry intersects the area.",
            source_id=uuid4(),
            method_code="fixture_flood_overlay",
            geometry_geojson={"type": "Point", "coordinates": [-120.0, 38.0]},
            geometry_srid=3857,
        )


def test_evidence_contract_rejects_negative_spatial_precision() -> None:
    with pytest.raises(ValidationError, match="greater than or equal to 0"):
        EvidenceContract(
            area_id=uuid4(),
            evidence_code="FLOOD_ZONE_AE",
            domain="flood",
            observation="Flood source geometry intersects the area.",
            source_id=uuid4(),
            method_code="fixture_flood_overlay",
            spatial_precision_meters=-1,
        )
