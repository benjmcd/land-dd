from __future__ import annotations

import importlib.util
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from types import ModuleType
from typing import Any, cast

import pytest

yaml = cast(Any, __import__("yaml"))

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "config" / "bol_scope_auth.yaml"
ODP1_OWNER_ANSWER_ID = "odp-bol-001-scope-pursuit-2026-06-26"


def _load_validator() -> ModuleType:
    script_path = REPO_ROOT / "scripts" / "bol_scope_auth_check.py"
    spec = importlib.util.spec_from_file_location("bol_scope_auth_check", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return cast(dict[str, Any], payload)


def test_bol_scope_auth_gate_is_validate_only_and_blocked() -> None:
    validator = cast(Any, _load_validator())
    gate = _yaml(CONFIG_PATH)

    assert gate["schema_version"] == "bol_scope_auth_v1"
    assert gate["operator_runbook"] == "docs/runbooks/bol_scope_auth.md"
    assert gate["status"] == "blocked_review_only_owner_answer"
    assert gate["validation"] == "scripts/run_bol_scope_auth_check.ps1"
    assert gate["approvals"] == validator.EXPECTED_APPROVALS
    assert gate["limits"] == validator.EXPECTED_LIMITS
    assert all(value is False for value in gate["approvals"].values())
    assert gate["limits"]["validate_only_promotion_readiness"] is True
    assert all(
        value is False
        for key, value in gate["limits"].items()
        if key != "validate_only_promotion_readiness"
    )


def test_bol_scope_auth_gate_aligns_to_current_odp1_state() -> None:
    validator = cast(Any, _load_validator())
    gate = _yaml(CONFIG_PATH)
    readiness = gate["promotion_readiness"]

    assert readiness["odp_id"] == validator.ODP_ID
    assert readiness["current_owner_answer_references"] == [ODP1_OWNER_ANSWER_ID]
    assert readiness["current_authority_record_references"] == []
    assert readiness["current_owner_answer_type"] == "approve_review_only"
    assert readiness["required_next_owner_answer_type"] == "approve_with_cited_authority"
    assert set(readiness["required_owner_answer_fields"]) == validator.owner_answer_fields()
    assert set(readiness["required_authority_record_fields"]) == (
        validator.pilot_authority_record_fields()
    )
    assert set(readiness["required_scope_decisions"]) == validator.pilot_scope_decisions()


def test_bol_scope_auth_gate_preserves_downstream_boundaries() -> None:
    validator = cast(Any, _load_validator())
    gate = _yaml(CONFIG_PATH)

    assert set(gate["allowed_future_authority_targets"]) == validator.EXPECTED_ALLOWED_TARGETS
    assert set(gate["forbidden_bundled_targets"]) == validator.EXPECTED_FORBIDDEN_TARGETS
    assert {
        row["id"] for row in gate["downstream_after_valid_scope_authority"]
    } == {"ODP-BOL-002", "ODP-BOL-003", "ODP-BOL-004"}
    assert all(
        row["update_allowed_by_this_gate"] is False
        for row in gate["downstream_after_valid_scope_authority"]
    )
    assert all(gate["no_overclaim_controls"].values())


def test_bol_scope_auth_current_artifacts_validate() -> None:
    validator = cast(Any, _load_validator())

    assert validator.main() == 0


def test_bol_scope_auth_rejects_review_only_as_cited_authority() -> None:
    validator = cast(Any, _load_validator())
    gate = deepcopy(_yaml(CONFIG_PATH))
    gate["promotion_readiness"]["required_next_owner_answer_type"] = "approve_review_only"

    with pytest.raises(SystemExit, match="required next answer type changed"):
        validator.validate_catalog(gate)


def test_bol_scope_auth_rejects_downstream_unlock() -> None:
    validator = cast(Any, _load_validator())
    gate = deepcopy(_yaml(CONFIG_PATH))
    gate["downstream_after_valid_scope_authority"][0]["update_allowed_by_this_gate"] = True

    with pytest.raises(SystemExit, match="unexpectedly allowed"):
        validator.validate_catalog(gate)


def test_bol_scope_auth_script_and_wrappers_are_validate_only() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/bol_scope_auth_check.py"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == "Bologna scope authority readiness check: ok"
    ps1 = (REPO_ROOT / "scripts" / "run_bol_scope_auth_check.ps1").read_text(
        encoding="utf-8"
    )
    sh = (REPO_ROOT / "scripts" / "run_bol_scope_auth_check.sh").read_text(
        encoding="utf-8"
    )
    for script in (ps1, sh):
        assert "bol_scope_auth_check.py" in script
        assert "Bologna scope authority readiness check: ok" in script
    assert "$LASTEXITCODE" in ps1
    assert "New-Item" not in ps1
    assert "Remove-Item" not in ps1
    assert "mkdir" not in sh
    assert "rm " not in sh
    assert "CheckerArgs.Count -eq 0" in ps1
    assert 'if [[ "$#" -eq 0 ]]' in sh


def test_bol_scope_auth_runbook_preserves_boundary() -> None:
    runbook = (REPO_ROOT / "docs" / "runbooks" / "bol_scope_auth.md").read_text(
        encoding="utf-8"
    )

    for phrase in (
        "bol_scope_auth_v1",
        "validate-only",
        "approve_review_only",
        "approve_with_cited_authority",
        ODP1_OWNER_ANSWER_ID,
        "current_authority_records",
        "request no downstream unlocks",
    ):
        assert phrase in runbook


def test_bol_scope_auth_json_reports_blocked_promotion_requirements() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/bol_scope_auth_check.py", "--json"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    summary = yaml.safe_load(result.stdout)
    assert summary["schema_version"] == "bol_scope_auth_summary_v1"
    assert summary["ok"] is True
    assert summary["gate_status"] == "blocked_review_only_owner_answer"
    assert summary["odp_id"] == "ODP-BOL-001"
    assert summary["readiness_state"] == "blocked_current_answer_review_only"
    assert summary["current_owner_answer_references"] == [ODP1_OWNER_ANSWER_ID]
    assert summary["current_authority_record_reference_count"] == 0
    assert summary["current_owner_answer_type"] == "approve_review_only"
    assert summary["required_next_owner_answer_type"] == "approve_with_cited_authority"
    assert summary["owner_answer_submission_target"] == (
        "config/bologna_owner_answer_intake.yaml"
    )
    assert summary["authority_record_submission_target"] == (
        "config/bologna_pilot_scope_authority.yaml"
    )
    assert summary["required_owner_answer_field_count"] == 11
    assert summary["required_authority_record_field_count"] == 14
    assert summary["required_scope_decision_count"] == 12
    assert "authority_reference" in summary["required_owner_answer_fields"]
    assert "scope_decision_ids" in summary["required_authority_record_fields"]
    assert "no_overclaim_review_owner" in summary["required_scope_decisions"]
    assert summary["downstream_gate_count"] == 3
    assert {
        row["id"] for row in summary["downstream_after_valid_scope_authority"]
    } == {"ODP-BOL-002", "ODP-BOL-003", "ODP-BOL-004"}
    assert all(
        row["update_allowed_by_this_gate"] is False
        for row in summary["downstream_after_valid_scope_authority"]
    )
    assert summary["no_overclaim_control_count"] == 9


def test_bol_scope_auth_summary_keeps_blocked_boundaries() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/bol_scope_auth_check.py", "--summary"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Bologna scope authority readiness summary: blocked" in result.stdout
    assert "schema_version: bol_scope_auth_summary_v1" in result.stdout
    assert "gate_status: blocked_review_only_owner_answer" in result.stdout
    assert "odp_id: ODP-BOL-001" in result.stdout
    assert "current_owner_answer_type: approve_review_only" in result.stdout
    assert "required_next_owner_answer_type: approve_with_cited_authority" in result.stdout
    assert "current_authority_records: 0" in result.stdout
    assert "required_scope_decisions: 12" in result.stdout
    assert (
        "downstream_after_valid_scope_authority ODP-BOL-002: "
        "status=still_requires_separate_source_authority_and_rights"
    ) in result.stdout
    assert "no_overclaim_controls: 9" in result.stdout
    assert "Bologna scope authority readiness check: ok" in result.stdout


def test_bol_scope_auth_wrapper_forwards_summary_and_json() -> None:
    wrapper_command = [
        "powershell",
        "-NoProfile",
        "-File",
        "scripts/run_bol_scope_auth_check.ps1",
    ]
    ps_summary = subprocess.run(
        [*wrapper_command, "--summary"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Bologna scope authority readiness summary: blocked" in ps_summary.stdout
    assert "Bologna scope authority readiness check: ok" in ps_summary.stdout
    assert ps_summary.stdout.count("Bologna scope authority readiness check: ok") == 1

    ps_json = subprocess.run(
        [*wrapper_command, "--json"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    parsed = yaml.safe_load(ps_json.stdout)
    assert parsed["schema_version"] == "bol_scope_auth_summary_v1"
    assert parsed["gate_status"] == "blocked_review_only_owner_answer"
    assert parsed["current_authority_record_reference_count"] == 0
    assert "Bologna scope authority readiness check: ok" not in ps_json.stdout
