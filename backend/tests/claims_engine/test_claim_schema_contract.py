from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

from app.domain.claim_contracts import ClaimContract
from app.domain.enums import ConfidenceBand, SeverityBand

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = REPO_ROOT / "schemas" / "claim_schema.json"


def load_schema() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))


def test_claim_schema_matches_serialized_contract_fields() -> None:
    schema = load_schema()
    properties = cast(dict[str, Any], schema["properties"])
    required = cast(list[str], schema["required"])

    assert set(properties) == set(ClaimContract.model_fields)
    assert set(required) == set(ClaimContract.model_fields)


def test_claim_schema_tracks_contract_enums() -> None:
    schema = load_schema()
    properties = cast(dict[str, Any], schema["properties"])

    assert properties["severity"]["enum"] == [item.value for item in SeverityBand]
    assert properties["confidence"]["enum"] == [item.value for item in ConfidenceBand]


def test_claim_schema_rejects_stale_contract_fields() -> None:
    schema = load_schema()
    properties = cast(dict[str, Any], schema["properties"])

    assert "intent" not in properties
    assert "contradiction_group_ids" not in properties
    assert "metadata" not in properties


def test_serialized_claim_contract_uses_schema_field_set() -> None:
    claim = ClaimContract(
        area_id=uuid4(),
        claim_code="FLOOD_001",
        domain="flood",
        assertion="Mapped data indicates possible flood constraint.",
        severity=SeverityBand.HIGH,
        confidence=ConfidenceBand.MEDIUM,
        evidence_ids=[uuid4()],
        rule_code="FLOOD_G001",
        ruleset_id="homestead_mvp_v0_1",
        ruleset_version="0.1",
    )
    schema = load_schema()
    properties = cast(dict[str, Any], schema["properties"])

    assert set(claim.model_dump(mode="json")) == set(properties)
