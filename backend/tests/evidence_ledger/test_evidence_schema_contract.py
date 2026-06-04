from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

from app.domain.enums import ConfidenceBand, EvidenceType
from app.domain.evidence_contracts import EvidenceContract

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = REPO_ROOT / "schemas" / "evidence_schema.json"


def load_schema() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))


def test_evidence_schema_matches_serialized_contract_fields() -> None:
    schema = load_schema()
    properties = cast(dict[str, Any], schema["properties"])
    required = cast(list[str], schema["required"])

    assert set(properties) == set(EvidenceContract.model_fields)
    assert set(required) == set(EvidenceContract.model_fields)


def test_evidence_schema_tracks_contract_enums_and_geometry_guards() -> None:
    schema = load_schema()
    properties = cast(dict[str, Any], schema["properties"])

    assert properties["evidence_type"]["enum"] == [item.value for item in EvidenceType]
    assert properties["confidence"]["enum"] == [item.value for item in ConfidenceBand]
    assert properties["geometry_srid"] == {"type": "integer", "const": 4326}
    assert properties["spatial_precision_meters"]["minimum"] == 0


def test_evidence_schema_rejects_stale_contract_fields() -> None:
    schema = load_schema()
    properties = cast(dict[str, Any], schema["properties"])

    assert "retrieved_at" not in properties
    assert "geometry_wkt" not in properties
    assert "metadata" not in properties
    assert "authority_level" not in properties


def test_serialized_evidence_contract_uses_schema_field_set() -> None:
    evidence = EvidenceContract(
        area_id=uuid4(),
        evidence_code="FLOOD_ZONE_AE",
        domain="flood",
        observation="Flood source geometry intersects the area.",
        source_id=uuid4(),
        method_code="fixture_flood_overlay",
        evidence_type=EvidenceType.SPATIAL_INTERSECTION,
        confidence=ConfidenceBand.MEDIUM,
        geometry_geojson={"type": "Point", "coordinates": [-120.0, 38.0]},
        spatial_precision_meters=15.5,
    )
    schema = load_schema()
    properties = cast(dict[str, Any], schema["properties"])

    assert set(evidence.model_dump(mode="json")) == set(properties)
