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
