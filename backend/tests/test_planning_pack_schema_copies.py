from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any, cast

from app.main import create_app

REPO_ROOT = Path(__file__).resolve().parents[2]
yaml = cast(Any, importlib.import_module("yaml"))


def load_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def load_yaml(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], yaml.safe_load(path.read_text(encoding="utf-8")))


def test_planning_pack_evidence_and_claim_schemas_match_root_contract_schemas() -> None:
    schema_names = ("evidence_schema.json", "claim_schema.json")

    for schema_name in schema_names:
        root_schema = load_json(REPO_ROOT / "schemas" / schema_name)
        planning_pack_schema = load_json(
            REPO_ROOT / "docs" / "planning_pack" / "schemas" / schema_name
        )

        assert planning_pack_schema == root_schema


def test_planning_pack_openapi_stub_matches_generated_fastapi_contract() -> None:
    generated_openapi = create_app().openapi()
    planning_pack_openapi = load_yaml(
        REPO_ROOT / "docs" / "planning_pack" / "api" / "openapi_stub.yaml"
    )

    assert planning_pack_openapi == generated_openapi
