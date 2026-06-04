from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from app.domain.enums import AuthorityLevel
from app.domain.source_contracts import SourceContract

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = REPO_ROOT / "schemas" / "source_schema.json"


def load_schema() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))


def test_source_schema_matches_serialized_source_contract_fields() -> None:
    schema = load_schema()
    properties = cast(dict[str, Any], schema["properties"])
    required = cast(list[str], schema["required"])

    assert set(properties) == set(SourceContract.model_fields)
    assert set(required) == set(SourceContract.model_fields)


def test_source_schema_tracks_authority_level_enum() -> None:
    schema = load_schema()
    properties = cast(dict[str, Any], schema["properties"])

    assert properties["authority_level"]["enum"] == [
        item.value for item in AuthorityLevel
    ]


def test_source_schema_rejects_source_provenance_family_fields() -> None:
    schema = load_schema()
    properties = cast(dict[str, Any], schema["properties"])

    assert "dataset_id" not in properties
    assert "dataset_version_id" not in properties
    assert "ingest_run_id" not in properties
    assert "connector_name" not in properties


def test_serialized_source_contract_uses_schema_field_set() -> None:
    source = SourceContract(
        name="Fixture FEMA NFHL",
        organization="FEMA",
        domain="flood",
        authority_level=AuthorityLevel.OFFICIAL_PRIMARY,
        source_type="public_dataset",
        geographic_scope="United States fixture",
        update_cadence="fixture",
        license_status="allowed",
        commercial_use_status="allowed",
        redistribution_status="allowed",
        license_summary="Fixture-only test source.",
        attribution_required=True,
        cache_allowed="allowed",
        export_allowed="allowed",
        ai_use_allowed="allowed",
        raw_data_allowed="allowed",
        freshness_class="fixture",
        last_checked_at="2026-06-04",
        review_owner="fixture-reviewer",
        review_status="approved",
        notes="Schema contract fixture.",
        metadata={"fixture_only": True},
    )
    schema = load_schema()
    properties = cast(dict[str, Any], schema["properties"])

    assert set(source.model_dump(mode="json")) == set(properties)
