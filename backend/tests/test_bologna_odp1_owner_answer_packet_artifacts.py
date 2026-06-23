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
CONFIG_PATH = REPO_ROOT / "config" / "bologna_odp1_owner_answer_packet.yaml"


def _load_validator() -> ModuleType:
    script_path = REPO_ROOT / "scripts" / "bologna_odp1_owner_answer_packet_check.py"
    spec = importlib.util.spec_from_file_location(
        "bologna_odp1_owner_answer_packet_check",
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


def test_odp1_owner_answer_packet_is_validate_only_and_blocked() -> None:
    validator = cast(Any, _load_validator())
    packet = _yaml(CONFIG_PATH)

    assert packet["schema_version"] == "bologna_odp1_owner_answer_packet_v1"
    assert packet["operator_runbook"] == (
        "docs/runbooks/bologna_odp1_owner_answer_packet.md"
    )
    assert packet["status"] == "ready_for_external_owner_response"
    assert packet["validation"] == "scripts/run_bologna_odp1_owner_answer_packet_check.ps1"
    assert packet["approvals"] == validator.EXPECTED_APPROVALS
    assert packet["limits"] == validator.EXPECTED_LIMITS
    assert all(value is False for value in packet["approvals"].values())


def test_odp1_owner_answer_packet_aligns_to_gate_and_templates() -> None:
    validator = cast(Any, _load_validator())
    packet = _yaml(CONFIG_PATH)
    body = packet["packet"]

    assert body["odp_id"] == validator.ODP_ID
    assert body["source_owner_answer_intake"] == validator.OWNER_INTAKE_PATH
    assert body["source_response_gate"] == validator.ODP1_GATE_PATH
    assert body["source_pilot_scope_authority"] == validator.PILOT_SCOPE_PATH
    assert body["current_owner_answer_references"] == []
    assert body["current_authority_record_references"] == []
    assert set(body["owner_answer_template"]) == validator.owner_answer_fields()
    assert set(body["pilot_scope_authority_record_template"]) == (
        validator.pilot_authority_record_fields()
    )
    assert set(body["pilot_scope_authority_record_template"]["scope_decision_ids"]) == (
        validator.pilot_scope_decisions()
    )
    assert set(body["allowed_answer_types"]) == validator.allowed_owner_answer_types()
    assert {row["decision_id"] for row in packet["decision_checklist"]} == (
        validator.pilot_scope_decisions()
    )


def test_odp1_owner_answer_packet_outcomes_do_not_unlock_work() -> None:
    validator = cast(Any, _load_validator())
    packet = _yaml(CONFIG_PATH)

    assert {row["answer_type"] for row in packet["outcome_policy"]} == (
        validator.allowed_owner_answer_types()
    )
    assert all(row["downstream_updates_allowed"] is False for row in packet["outcome_policy"])
    assert packet["submission_policy"]["current_owner_answers_must_remain_empty"] is True
    assert packet["submission_policy"]["current_authority_records_must_remain_empty"] is True
    assert packet["submission_policy"]["downstream_updates_allowed_by_packet"] is False
    assert all(packet["no_overclaim_controls"].values())


def test_odp1_owner_answer_packet_current_artifacts_validate() -> None:
    validator = cast(Any, _load_validator())

    assert validator.main() == 0


def test_odp1_owner_answer_packet_rejects_missing_required_decision() -> None:
    validator = cast(Any, _load_validator())
    packet = deepcopy(_yaml(CONFIG_PATH))
    packet["decision_checklist"] = [
        row
        for row in packet["decision_checklist"]
        if row["decision_id"] != "report_runtime_boundary"
    ]

    with pytest.raises(SystemExit, match="decision checklist coverage drifted"):
        validator.validate_packet(packet)


def test_odp1_owner_answer_packet_script_and_wrappers_are_validate_only() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/bologna_odp1_owner_answer_packet_check.py"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == "Bologna ODP-BOL-001 owner answer packet check: ok"
    ps1 = (
        REPO_ROOT / "scripts" / "run_bologna_odp1_owner_answer_packet_check.ps1"
    ).read_text(encoding="utf-8")
    sh = (
        REPO_ROOT / "scripts" / "run_bologna_odp1_owner_answer_packet_check.sh"
    ).read_text(encoding="utf-8")
    for script in (ps1, sh):
        assert "bologna_odp1_owner_answer_packet_check.py" in script
        assert "Bologna ODP-BOL-001 owner answer packet check: ok" in script
    assert "$LASTEXITCODE" in ps1
    assert "New-Item" not in ps1
    assert "Remove-Item" not in ps1
    assert "mkdir" not in sh
    assert "rm " not in sh


def test_odp1_owner_answer_packet_runbook_preserves_boundary() -> None:
    runbook = (
        REPO_ROOT / "docs" / "runbooks" / "bologna_odp1_owner_answer_packet.md"
    ).read_text(encoding="utf-8")

    for phrase in (
        "bologna_odp1_owner_answer_packet_v1",
        "validate-only",
        "does not record owner authority",
        "ODP-BOL-001",
        "current_owner_answers",
        "current_authority_records",
        "downstream_updates_allowed",
    ):
        assert phrase in runbook
