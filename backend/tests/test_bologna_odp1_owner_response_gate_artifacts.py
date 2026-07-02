from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, cast

yaml = cast(Any, __import__("yaml"))

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "config" / "bologna_odp1_owner_response_gate.yaml"
ODP1_OWNER_ANSWER_ID = "odp-bol-001-scope-pursuit-2026-06-26"


def _load_validator() -> ModuleType:
    script_path = REPO_ROOT / "scripts" / "bologna_odp1_owner_response_gate_check.py"
    spec = importlib.util.spec_from_file_location(
        "bologna_odp1_owner_response_gate_check",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return cast(dict[str, Any], payload)


def test_odp1_owner_response_gate_is_validate_only_and_blocked() -> None:
    validator = cast(Any, _load_validator())
    catalog = _yaml(CONFIG_PATH)

    assert catalog["schema_version"] == "bologna_odp1_owner_response_gate_v1"
    assert catalog["operator_runbook"] == "docs/runbooks/bologna_odp1_owner_response_gate.md"
    assert catalog["status"] == "blocked_review_only_scope_pursuit_answered"
    assert catalog["validation"] == "scripts/run_bologna_odp1_owner_response_gate_check.ps1"
    assert catalog["approvals"] == validator.EXPECTED_APPROVALS
    assert catalog["limits"] == validator.EXPECTED_LIMITS
    assert catalog["approvals"]["owner_answer_recorded"] is True
    assert all(
        value is False
        for key, value in catalog["approvals"].items()
        if key != "owner_answer_recorded"
    )


def test_odp1_owner_response_gate_aligns_with_source_contracts() -> None:
    validator = cast(Any, _load_validator())
    catalog = _yaml(CONFIG_PATH)
    gate = catalog["odp_bol_001_gate"]

    assert gate["odp_id"] == validator.ODP_ID
    assert gate["status"] == "review_only_scope_pursuit_answered"
    assert gate["current_owner_answer_references"] == [ODP1_OWNER_ANSWER_ID]
    assert gate["current_authority_record_references"] == []
    assert set(gate["required_owner_answer_fields"]) == validator.owner_answer_fields()
    assert set(gate["required_authority_record_fields"]) == (
        validator.pilot_authority_record_fields()
    )
    assert set(gate["required_scope_decisions"]) == validator.pilot_scope_decisions()
    assert {
        item["decision_id"] for item in catalog["decision_requirements"]
    } == validator.pilot_scope_decisions()


def test_odp1_owner_response_gate_outcomes_do_not_unlock_downstream_work() -> None:
    validator = cast(Any, _load_validator())
    catalog = _yaml(CONFIG_PATH)

    assert {item["answer_type"] for item in catalog["outcome_matrix"]} == (
        validator.EXPECTED_ANSWER_TYPES
    )
    assert {item["answer_type"] for item in catalog["outcome_matrix"]} == (
        validator.allowed_owner_answer_types()
    )
    for outcome in catalog["outcome_matrix"]:
        assert outcome["downstream_updates_allowed"] is False
        assert outcome["still_disallowed"]
    assert all(catalog["no_overclaim_controls"].values())


def test_odp1_owner_response_gate_current_artifacts_validate() -> None:
    validator = cast(Any, _load_validator())

    assert validator.main() == 0


def test_odp1_owner_response_gate_script_and_wrappers_are_validate_only() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/bologna_odp1_owner_response_gate_check.py"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == "Bologna ODP-BOL-001 owner response gate check: ok"
    ps1 = (
        REPO_ROOT / "scripts" / "run_bologna_odp1_owner_response_gate_check.ps1"
    ).read_text(encoding="utf-8")
    sh = (
        REPO_ROOT / "scripts" / "run_bologna_odp1_owner_response_gate_check.sh"
    ).read_text(encoding="utf-8")
    for script in (ps1, sh):
        assert "bologna_odp1_owner_response_gate_check.py" in script
        assert "Bologna ODP-BOL-001 owner response gate check: ok" in script
    assert "$LASTEXITCODE" in ps1
    assert "New-Item" not in ps1
    assert "Remove-Item" not in ps1
    assert "mkdir" not in sh
    assert "rm " not in sh


def test_odp1_owner_response_gate_runbook_preserves_boundary() -> None:
    runbook = (
        REPO_ROOT / "docs" / "runbooks" / "bologna_odp1_owner_response_gate.md"
    ).read_text(encoding="utf-8")

    for phrase in (
        "bologna_odp1_owner_response_gate_v1",
        "validate-only",
        "review-only scope pursuit",
        ODP1_OWNER_ANSWER_ID,
        "ODP-BOL-001",
        "current_owner_answer_references",
        "current_authority_record_references",
        "downstream_updates_allowed",
    ):
        assert phrase in runbook
