from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

from app.domain.source_contracts import (
    SourceContract,
    SourceDatasetContract,
    SourceDatasetVersionContract,
    SourceRetrievalRunContract,
    SourceRetrievalStatus,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = REPO_ROOT / "schemas" / "source_provenance_schema.json"


def load_schema() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))


def contract_schema(name: str) -> dict[str, Any]:
    schema = load_schema()
    definitions = cast(dict[str, Any], schema["$defs"])
    return cast(dict[str, Any], definitions[name])


def test_source_provenance_schema_matches_dataset_contract_fields() -> None:
    schema = contract_schema("SourceDatasetContract")
    properties = cast(dict[str, Any], schema["properties"])
    required = cast(list[str], schema["required"])

    assert set(properties) == set(SourceDatasetContract.model_fields)
    assert set(required) == set(SourceDatasetContract.model_fields)


def test_source_provenance_schema_embeds_source_contract_schema() -> None:
    schema = load_schema()
    source_provenance_source = contract_schema("SourceContract")
    source_schema = cast(
        dict[str, Any],
        json.loads(
            (REPO_ROOT / "schemas" / "source_schema.json").read_text(
                encoding="utf-8",
            ),
        ),
    )
    properties = cast(dict[str, Any], source_provenance_source["properties"])
    required = cast(list[str], source_provenance_source["required"])

    assert schema["properties"]["source"] == {"$ref": "#/$defs/SourceContract"}
    assert set(properties) == set(SourceContract.model_fields)
    assert set(required) == set(SourceContract.model_fields)
    assert source_provenance_source == {
        key: value
        for key, value in source_schema.items()
        if key not in {"$schema", "$id", "title"}
    }


def test_source_provenance_schema_matches_dataset_version_contract_fields() -> None:
    schema = contract_schema("SourceDatasetVersionContract")
    properties = cast(dict[str, Any], schema["properties"])
    required = cast(list[str], schema["required"])

    assert set(properties) == set(SourceDatasetVersionContract.model_fields)
    assert set(required) == set(SourceDatasetVersionContract.model_fields)


def test_source_provenance_schema_matches_retrieval_run_contract_fields() -> None:
    schema = contract_schema("SourceRetrievalRunContract")
    properties = cast(dict[str, Any], schema["properties"])
    required = cast(list[str], schema["required"])

    assert set(properties) == set(SourceRetrievalRunContract.model_fields)
    assert set(required) == set(SourceRetrievalRunContract.model_fields)


def test_source_provenance_schema_tracks_retrieval_status_enum() -> None:
    schema = contract_schema("SourceRetrievalRunContract")
    properties = cast(dict[str, Any], schema["properties"])

    assert properties["status"]["enum"] == [
        item.value for item in SourceRetrievalStatus
    ]


def test_source_provenance_schema_declares_non_negative_counts() -> None:
    schema = contract_schema("SourceRetrievalRunContract")
    properties = cast(dict[str, Any], schema["properties"])

    assert properties["row_count"]["minimum"] == 0
    assert properties["error_count"]["minimum"] == 0
    assert properties["warning_count"]["minimum"] == 0


def test_source_provenance_schema_matches_review_bundle_root_fields() -> None:
    schema = load_schema()
    properties = cast(dict[str, Any], schema["properties"])
    required = cast(list[str], schema["required"])

    assert set(properties) == {
        "source",
        "production_use_allowed",
        "datasets",
        "dataset_versions",
        "retrieval_runs",
        "latest_retrieval_status",
        "review_summary",
    }
    assert set(required) == set(properties)
    assert properties["latest_retrieval_status"]["enum"] == [
        item.value for item in SourceRetrievalStatus
    ]


def test_serialized_source_provenance_contracts_use_schema_field_sets() -> None:
    dataset = SourceDatasetContract(
        source_id=uuid4(),
        dataset_name="National Flood Hazard Layer",
        domain="flood",
        legal_caveat="Screening only; not a flood determination.",
    )
    version = SourceDatasetVersionContract(
        dataset_id=dataset.dataset_id,
        version_label="2026-06",
    )
    run = SourceRetrievalRunContract(
        dataset_version_id=version.dataset_version_id,
        connector_name="fixture_flood_static",
        status=SourceRetrievalStatus.SUCCEEDED,
        row_count=1,
    )

    dataset_schema = contract_schema("SourceDatasetContract")
    version_schema = contract_schema("SourceDatasetVersionContract")
    run_schema = contract_schema("SourceRetrievalRunContract")

    assert set(dataset.model_dump(mode="json")) == set(dataset_schema["properties"])
    assert set(version.model_dump(mode="json")) == set(version_schema["properties"])
    assert set(run.model_dump(mode="json")) == set(run_schema["properties"])
