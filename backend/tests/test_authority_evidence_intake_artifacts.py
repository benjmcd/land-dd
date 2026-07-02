from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from types import ModuleType
from typing import Any, cast

import pytest

yaml = cast(Any, __import__("yaml"))

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_validator() -> ModuleType:
    script_path = REPO_ROOT / "scripts" / "authority_evidence_intake_check.py"
    spec = importlib.util.spec_from_file_location(
        "authority_evidence_intake_check",
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


def test_authority_evidence_intake_current_artifacts_validate() -> None:
    validator = cast(Any, _load_validator())

    assert validator.main([]) == 0


def test_authority_evidence_intake_requires_active_intake_task() -> None:
    validator = cast(Any, _load_validator())
    task_queue = deepcopy(_yaml(REPO_ROOT / "tasks" / "task_queue.yaml"))
    task_queue["active_plan"] = "plans/2026-07-02-post-geology-routing.md"

    with pytest.raises(SystemExit, match="active_plan must point"):
        validator.validate_task_routing(task_queue)


def test_authority_evidence_intake_requires_complete_stream_set() -> None:
    validator = cast(Any, _load_validator())
    catalog = deepcopy(_yaml(REPO_ROOT / "config" / "production_authority_intake.yaml"))
    catalog["authority_streams"] = [
        stream
        for stream in catalog["authority_streams"]
        if stream["id"] != "ds017_source_entitlement"
    ]

    with pytest.raises(SystemExit, match="stream set drifted"):
        validator.validate_production_streams(catalog)


def test_authority_evidence_intake_rejects_unblocked_bologna_answer() -> None:
    validator = cast(Any, _load_validator())
    intake = deepcopy(_yaml(REPO_ROOT / "config" / "bologna_owner_answer_intake.yaml"))
    for thread in intake["bologna_decision_threads"]:
        if thread["odp_id"] == "ODP-BOL-003":
            thread["downstream_updates_allowed"] = True
            break

    with pytest.raises(SystemExit, match="ODP-BOL-003 unlocked downstream"):
        validator.validate_bologna_owner_threads(intake)


def test_authority_evidence_intake_rejects_p0_pass() -> None:
    validator = cast(Any, _load_validator())
    status = deepcopy(_yaml(REPO_ROOT / "state" / "EMPIRICAL_QUALIFICATION_STATUS.yaml"))
    status["qualifications"]["p0"]["status"] = "PASS"

    with pytest.raises(SystemExit, match="P0 must remain BLOCKED"):
        validator.validate_qualification_status(status)


def test_authority_evidence_intake_script_and_wrappers_are_validate_only() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/authority_evidence_intake_check.py"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "authority evidence intake check: ok" in result.stdout
    ps1 = (
        REPO_ROOT / "scripts" / "run_authority_evidence_intake_check.ps1"
    ).read_text(encoding="utf-8")
    sh = (
        REPO_ROOT / "scripts" / "run_authority_evidence_intake_check.sh"
    ).read_text(encoding="utf-8")
    for script in (ps1, sh):
        assert "authority_evidence_intake_check.py" in script
        assert "authority evidence intake" in script
    assert "New-Item" not in ps1
    assert "Remove-Item" not in ps1
    assert "mkdir" not in sh
    assert "rm " not in sh
    assert "@CheckerArgs" in ps1
    assert 'if ($CheckerArgs.Count -eq 0)' in ps1
    assert 'if [[ "$#" -eq 0 ]]' in sh


def test_authority_evidence_intake_wrapper_forwards_summary_and_json() -> None:
    wrapper_command = [
        "powershell",
        "-NoProfile",
        "-File",
        "scripts/run_authority_evidence_intake_check.ps1",
    ]
    ps_summary = subprocess.run(
        [*wrapper_command, "--summary"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "authority evidence intake summary: blocked" in ps_summary.stdout
    assert "authority evidence intake: ok" not in ps_summary.stdout

    ps_json = subprocess.run(
        [*wrapper_command, "--json"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    parsed = json.loads(ps_json.stdout)
    assert parsed["schema_version"] == "authority_evidence_intake_summary_v1"
    assert parsed["active_task"] == "AUTH-EVIDENCE-INTAKE"


def test_authority_evidence_intake_json_summary_reports_missing_authority() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/authority_evidence_intake_check.py", "--json"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    summary = json.loads(result.stdout)
    assert summary["schema_version"] == "authority_evidence_intake_summary_v1"
    assert summary["ok"] is True
    assert summary["active_plan"] == "plans/2026-07-02-authority-evidence-intake.md"
    assert summary["active_task"] == "AUTH-EVIDENCE-INTAKE"
    assert summary["active_tasks"] == ["AUTH-EVIDENCE-INTAKE"]
    assert summary["completed_prerequisite"] == "POST-GEOLOGY-ROUTING"
    assert summary["production_authority_status"] == "blocked_no_external_authority"
    assert summary["bologna_owner_answer_status"] == "blocked_review_only_scope_pursuit"
    assert summary["qualification"]["p0_status"] == "BLOCKED"
    assert summary["qualification"]["p0_result_path"] is None
    assert summary["authority_record_state"] == {
        "odp2_owner_answer_reference_count": 0,
        "odp2_source_authority_record_reference_count": 0,
        "odp2_source_rights_approval_reference_count": 0,
        "pilot_authority_record_count": 0,
        "source_authority_record_count": 0,
    }

    streams = {stream["id"]: stream for stream in summary["production_streams"]}
    assert set(streams) == validator_expected_streams()
    assert streams["ds017_source_entitlement"]["evidence_status"] == "missing"
    assert streams["ds017_source_entitlement"]["authority_reference_count"] == 0
    assert streams["ds017_source_entitlement"]["decision_updates_allowed"] is False
    assert streams["bologna_pilot_scope"]["required_evidence_count"] == 12

    threads = {thread["odp_id"]: thread for thread in summary["bologna_threads"]}
    assert threads["ODP-BOL-001"]["status"] == "review_only_scope_pursuit_answered"
    assert "config/bologna_pilot_scope_authority.yaml" in threads["ODP-BOL-001"]["source_packets"]
    assert threads["ODP-BOL-002"]["status"] == "missing_owner_answer"
    assert threads["ODP-BOL-002"]["owner_answer_reference_count"] == 0
    assert threads["ODP-BOL-004"]["required_field_count"] == 11
    assert all(thread["downstream_updates_allowed"] is False for thread in threads.values())
    assert "p0_unblock" in summary["blocked_implementation_boundaries"]
    assert "hosted_level_10_authority" in summary["blocked_implementation_boundaries"]


def test_authority_evidence_intake_text_summary_keeps_blocked_boundaries() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/authority_evidence_intake_check.py", "--summary"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "authority evidence intake summary: blocked" in result.stdout
    assert "schema_version: authority_evidence_intake_summary_v1" in result.stdout
    assert "active_task: AUTH-EVIDENCE-INTAKE" in result.stdout
    assert "active_tasks: AUTH-EVIDENCE-INTAKE" in result.stdout
    assert "completed_prerequisite: POST-GEOLOGY-ROUTING" in result.stdout
    assert (
        "production_stream ds017_source_entitlement: status=blocked evidence_status=missing"
        in result.stdout
    )
    assert "bologna_thread ODP-BOL-002: status=missing_owner_answer" in result.stdout
    assert "authority_record_state: pilot=0 source=0 odp2_owner_answers=0" in result.stdout
    assert "blocked_implementation_boundaries:" in result.stdout
    assert "p0_unblock" in result.stdout
    assert "authority evidence intake check: ok" in result.stdout


def test_authority_evidence_summary_is_discoverable_from_operator_runbooks() -> None:
    runbook_paths = (
        REPO_ROOT / "docs" / "runbooks" / "production_authority_intake.md",
        REPO_ROOT / "docs" / "runbooks" / "bologna_owner_answer_intake.md",
        REPO_ROOT / "docs" / "runbooks" / "source_entitlements.md",
    )

    for path in runbook_paths:
        text = path.read_text(encoding="utf-8")
        assert "authority_evidence_intake_check.py --summary" in text
        assert "Use `--json` on the same checker" in text
        assert "reporting only" in text
        assert "unlock" in text


def test_authority_evidence_state_includes_reference_contract() -> None:
    project_state = (REPO_ROOT / "state" / "PROJECT_STATE.md").read_text(
        encoding="utf-8",
    )
    plan = (
        REPO_ROOT / "plans" / "2026-07-02-authority-evidence-intake.md"
    ).read_text(encoding="utf-8")
    plan_index = (REPO_ROOT / "plans" / "README.md").read_text(encoding="utf-8")
    task_queue = _yaml(REPO_ROOT / "tasks" / "task_queue.yaml")
    tasks = {task["id"]: task for task in task_queue["tasks"]}

    assert "production authority evidence reference contract" in project_state
    assert "b7cc96e58c9a881eec0cc6896c1733d44a2f29cb" in project_state
    assert "wrapper argument passthrough merged through PR #179" in project_state
    assert "authority follow-on sequencing contract" in project_state
    assert "reporting-only output for that reference contract" in project_state
    assert "production_authority_evidence_references_check.py" in project_state
    assert "it does not record authority or change any" in project_state
    assert "implementation surface" in project_state
    assert "PR #179" in plan
    assert "forwarded wrapper arguments" in plan
    assert "production_authority_evidence_references_check.py" in plan
    assert "authority_follow_on_sequence_check.py" in plan
    assert "through PR #182" in plan_index
    assert "production authority evidence reference checker" in plan_index
    assert "authority follow-on sequence checker" in plan_index
    assert "Authority-evidence posture after PR #182" in (
        tasks["AUTH-EVIDENCE-INTAKE"]["notes"]
    )
    assert "production authority evidence reference contract" in (
        tasks["AUTH-EVIDENCE-INTAKE"]["notes"]
    )
    assert "reporting-only output" in tasks["AUTH-EVIDENCE-INTAKE"]["notes"]
    assert "authority follow-on sequencing contract" in (
        tasks["AUTH-EVIDENCE-INTAKE"]["notes"]
    )
    assert any(
        "Summary/JSON output and wrapper passthrough remain reporting-only"
        in acceptance
        for acceptance in tasks["AUTH-EVIDENCE-INTAKE"]["acceptance"]
    )
    assert any(
        "production authority evidence reference checker" in acceptance
        for acceptance in tasks["AUTH-EVIDENCE-INTAKE"]["acceptance"]
    )
    assert any(
        "authority follow-on sequence checker" in acceptance
        for acceptance in tasks["AUTH-EVIDENCE-INTAKE"]["acceptance"]
    )
    assert tasks["AUTH-EVIDENCE-INTAKE"]["status"] == "active"
    assert tasks["BSA-001"]["status"] == "blocked"


def validator_expected_streams() -> set[str]:
    validator = cast(Any, _load_validator())
    return set(validator.EXPECTED_PRODUCTION_STREAMS)
