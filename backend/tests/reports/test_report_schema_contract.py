from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

from app.domain.enums import IntentCode, JobStatus
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
