from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, cast

yaml = cast(Any, __import__("yaml"))

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "config" / "bologna_odp2_source_rights_response_gate.yaml"


def _load_validator() -> ModuleType:
    script_path = REPO_ROOT / "scripts" / (
        "bologna_odp2_source_rights_response_gate_check.py"
    )
    spec = importlib.util.spec_from_file_location(
        "bologna_odp2_source_rights_response_gate_check",
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


def test_odp2_source_rights_response_gate_is_validate_only_and_blocked() -> None:
    validator = cast(Any, _load_validator())
    catalog = _yaml(CONFIG_PATH)

    assert catalog["schema_version"] == (
        "bologna_odp2_source_rights_response_gate_v1"
    )
    assert catalog["operator_runbook"] == (
        "docs/runbooks/bologna_odp2_source_rights_response_gate.md"
    )
    assert catalog["status"] == (
        "blocked_until_odp_bol_001_and_missing_odp_bol_002_owner_answer"
    )
    assert catalog["validation"] == (
        "scripts/run_bologna_odp2_source_rights_response_gate_check.ps1"
    )
    assert catalog["approvals"] == validator.EXPECTED_APPROVALS
    assert catalog["limits"] == validator.EXPECTED_LIMITS
    assert all(value is False for value in catalog["approvals"].values())


def test_odp2_source_rights_response_gate_aligns_with_source_contracts() -> None:
    validator = cast(Any, _load_validator())
    catalog = _yaml(CONFIG_PATH)
    gate = catalog["odp_bol_002_gate"]

    assert gate["odp_id"] == validator.ODP_ID
    assert gate["status"] == "blocked_until_odp_bol_001"
    assert gate["prerequisite_odp_ids"] == [validator.PREREQUISITE_ODP_ID]
    assert gate["prerequisite_status"] == "missing_owner_answer"
    assert gate["current_owner_answer_references"] == []
    assert gate["current_source_authority_record_references"] == []
    assert gate["current_source_rights_approval_references"] == []
    assert set(gate["required_owner_answer_fields"]) == validator.owner_answer_fields()
    assert set(gate["required_source_authority_record_fields"]) == (
        validator.source_authority_record_fields()
    )
    assert set(gate["required_rights_decisions"]) == validator.source_rights_decisions()
    assert set(gate["candidate_review_ids"]) == validator.source_rights_candidate_ids()


def test_odp2_candidate_requirements_match_source_authority_slots() -> None:
    validator = cast(Any, _load_validator())
    catalog = _yaml(CONFIG_PATH)
    expected_slots = validator.source_authority_evidence_slots()

    requirements = {
        item["candidate_id"]: item for item in catalog["candidate_review_requirements"]
    }
    assert set(requirements) == validator.source_rights_candidate_ids()
    for candidate_id, requirement in requirements.items():
        assert set(requirement["required_evidence"]) == expected_slots[candidate_id]
        assert requirement["downstream_updates_allowed"] is False


def test_odp2_decision_requirements_and_outcomes_do_not_unlock_work() -> None:
    validator = cast(Any, _load_validator())
    catalog = _yaml(CONFIG_PATH)

    assert {item["decision_id"] for item in catalog["decision_requirements"]} == (
        validator.source_rights_decisions()
    )
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


def test_odp2_source_rights_response_gate_current_artifacts_validate() -> None:
    validator = cast(Any, _load_validator())

    assert validator.main() == 0


def test_odp2_source_rights_response_gate_script_and_wrappers_validate_only() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/bologna_odp2_source_rights_response_gate_check.py"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == (
        "Bologna ODP-BOL-002 source-rights response gate check: ok"
    )
    ps1 = (
        REPO_ROOT / "scripts" / (
            "run_bologna_odp2_source_rights_response_gate_check.ps1"
        )
    ).read_text(encoding="utf-8")
    sh = (
        REPO_ROOT / "scripts" / (
            "run_bologna_odp2_source_rights_response_gate_check.sh"
        )
    ).read_text(encoding="utf-8")
    for script in (ps1, sh):
        assert "bologna_odp2_source_rights_response_gate_check.py" in script
        assert "Bologna ODP-BOL-002 source-rights response gate check: ok" in script
    assert "$LASTEXITCODE" in ps1
    assert "New-Item" not in ps1
    assert "Remove-Item" not in ps1
    assert "mkdir" not in sh
    assert "rm " not in sh


def test_odp2_source_rights_response_gate_runbook_preserves_boundary() -> None:
    runbook = (
        REPO_ROOT / "docs" / "runbooks" / (
            "bologna_odp2_source_rights_response_gate.md"
        )
    ).read_text(encoding="utf-8")

    for phrase in (
        "bologna_odp2_source_rights_response_gate_v1",
        "validate-only",
        "does not record source authority",
        "ODP-BOL-002",
        "ODP-BOL-001",
        "current_source_authority_record_references",
        "current_source_rights_approval_references",
        "downstream_updates_allowed",
    ):
        assert phrase in runbook
