from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

REPO_ROOT = Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def test_planning_pack_evidence_and_claim_schemas_match_root_contract_schemas() -> None:
    schema_names = ("evidence_schema.json", "claim_schema.json")

    for schema_name in schema_names:
        root_schema = load_json(REPO_ROOT / "schemas" / schema_name)
        planning_pack_schema = load_json(
            REPO_ROOT / "docs" / "planning_pack" / "schemas" / schema_name
        )

        assert planning_pack_schema == root_schema
