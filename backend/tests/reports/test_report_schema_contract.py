from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

from app.domain.enums import AuthorityLevel, IntentCode, JobStatus
from app.domain.report_contracts import ReportRunContract

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = REPO_ROOT / "schemas" / "report_run_schema.json"
EVIDENCE_REF = "https://example.com/schemas/evidence.schema.json"
CLAIM_REF = "https://example.com/schemas/claim.schema.json"


def load_schema() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))


def test_report_run_schema_matches_serialized_report_contract_fields() -> None:
    schema = load_schema()
    properties = cast(dict[str, Any], schema["properties"])
    required = cast(list[str], schema["required"])

    assert set(properties) == set(ReportRunContract.model_fields)
    assert set(required) == set(ReportRunContract.model_fields)


def test_report_run_schema_tracks_report_contract_enums() -> None:
    schema = load_schema()
    properties = cast(dict[str, Any], schema["properties"])

    assert properties["intent_code"]["enum"] == [item.value for item in IntentCode]
    assert properties["status"]["enum"] == [item.value for item in JobStatus]


def test_report_run_schema_references_lane_owned_nested_contract_schemas() -> None:
    schema = load_schema()
    properties = cast(dict[str, Any], schema["properties"])

    assert properties["evidence"]["items"]["$ref"] == EVIDENCE_REF
    assert properties["claims"]["items"]["$ref"] == CLAIM_REF
    assert properties["unknowns"]["items"]["$ref"] == CLAIM_REF
    assert properties["red_flags"]["items"]["$ref"] == CLAIM_REF


def test_report_run_schema_tightens_source_manifest_shape() -> None:
    schema = load_schema()
    properties = cast(dict[str, Any], schema["properties"])
    source_manifest = cast(dict[str, Any], properties["source_manifest"])
    manifest_properties = cast(dict[str, Any], source_manifest["properties"])
    source_details = cast(dict[str, Any], manifest_properties["source_details"])
    source_detail_item = cast(dict[str, Any], source_details["items"])
    source_detail_properties = cast(dict[str, Any], source_detail_item["properties"])

    assert set(source_manifest["required"]) == {
        "source_ids",
        "source_count",
        "evidence_count",
        "claim_count",
        "ruleset_id",
        "ruleset_version",
        "source_names",
        "source_details",
    }
    assert manifest_properties["source_ids"]["items"] == {
        "type": "string",
        "format": "uuid",
    }
    assert manifest_properties["source_count"]["minimum"] == 0
    assert manifest_properties["evidence_count"]["minimum"] == 0
    assert manifest_properties["claim_count"]["minimum"] == 0
    assert manifest_properties["ruleset_id"]["minLength"] == 1
    assert manifest_properties["ruleset_version"]["minLength"] == 1
    assert manifest_properties["source_names"]["items"]["type"] == "string"

    assert set(source_detail_item["required"]) == {
        "source_id",
        "name",
        "authority_level",
        "license_status",
        "commercial_use_status",
        "freshness_class",
        "review_status",
        "review_owner",
        "last_checked_at",
    }
    assert source_detail_properties["source_id"] == {
        "type": "string",
        "format": "uuid",
    }
    assert source_detail_properties["authority_level"]["enum"] == [
        item.value for item in AuthorityLevel
    ]
    assert source_detail_properties["review_owner"]["type"] == ["string", "null"]
    assert source_detail_properties["last_checked_at"]["type"] == ["string", "null"]
    assert source_detail_item["additionalProperties"] is True
    assert source_manifest["additionalProperties"] is True


def test_report_run_schema_tightens_artifact_metadata_shape() -> None:
    schema = load_schema()
    properties = cast(dict[str, Any], schema["properties"])
    artifact_metadata = cast(dict[str, Any], properties["artifact_metadata"])
    artifact_properties = cast(dict[str, Any], artifact_metadata["properties"])
    validation = cast(dict[str, Any], artifact_properties["validation"])
    validation_properties = cast(dict[str, Any], validation["properties"])
    cost_metrics = cast(dict[str, Any], artifact_properties["cost_metrics"])
    cost_metric_properties = cast(dict[str, Any], cost_metrics["properties"])

    assert set(artifact_metadata["required"]) == {
        "artifact_kind",
        "report_schema",
        "cost_metrics",
    }
    assert artifact_properties["artifact_kind"]["const"] == "report_run"
    assert artifact_properties["report_schema"]["const"] == "report_run_contract_v1"
    assert artifact_properties["persistence"]["enum"] == [
        "memory",
        "postgres+object_store",
    ]
    assert artifact_properties["output_uri"]["type"] == "string"
    assert artifact_properties["machine_json_uri"]["type"] == "string"
    assert set(validation["required"]) == {
        "contract_name",
        "contract_version",
        "validation_profile",
        "ruleset_id",
        "ruleset_version",
    }
    assert validation_properties["contract_name"]["const"] == "ReportRunContract"
    assert validation_properties["contract_version"]["const"] == "report_run_contract_v1"
    assert validation_properties["validation_profile"]["const"] == "fixture_report_contract_v1"
    assert validation_properties["ruleset_id"]["minLength"] == 1
    assert validation_properties["ruleset_version"]["minLength"] == 1
    assert validation["additionalProperties"] is True
    assert set(cost_metrics["required"]) == {
        "evidence_count",
        "claim_count",
        "unknown_count",
        "red_flag_count",
        "verification_task_count",
        "estimated_total_usd_cents",
        "compute_usd_cents",
        "storage_usd_cents",
        "llm_usd_cents",
        "map_tile_usd_cents",
        "geocoding_usd_cents",
        "paid_data_usd_cents",
        "human_review_usd_cents",
        "human_review_minutes",
    }
    assert all(
        cost_metric_properties[name]["minimum"] == 0
        for name in cost_metrics["required"]
    )
    assert cost_metrics["additionalProperties"] is True
    assert artifact_metadata["additionalProperties"] is True


def test_serialized_report_run_contract_uses_schema_field_set() -> None:
    report_run = ReportRunContract(
        area_id=uuid4(),
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
        status=JobStatus.SUCCEEDED,
        source_manifest={"source_count": 0},
        assumptions=["fixture assumption"],
        caveats=["fixture caveat"],
        artifact_metadata={"report_schema": "report_run_contract_v1"},
        output_uri="local-artifact://fixture-report.json",
    )
    schema = load_schema()
    properties = cast(dict[str, Any], schema["properties"])

    assert set(report_run.model_dump(mode="json")) == set(properties)
