from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, cast

import pytest

from app.project_readiness import (
    ProjectReadinessError,
    load_project_readiness,
    parse_project_state,
)
from app.release_readiness import (
    ReleaseReadinessError,
    load_release_readiness,
    parse_release_readiness,
)

yaml = cast(Any, __import__("yaml"))

REPO_ROOT = Path(__file__).resolve().parents[2]


def _release_catalog() -> dict[str, Any]:
    payload = yaml.safe_load(
        (REPO_ROOT / "config" / "release_readiness.yaml").read_text(encoding="utf-8"),
    )
    assert isinstance(payload, dict)
    return cast(dict[str, Any], payload)


def test_release_readiness_app_model_loads_current_catalog() -> None:
    readiness = load_release_readiness(REPO_ROOT)

    assert readiness.schema_version == "release_readiness_v1"
    assert readiness.operator_runbook == "docs/runbooks/release_readiness.md"
    assert "production_authority_intake" in readiness.check_ids
    assert "bologna_pilot_scope_authority" in readiness.check_ids
    assert "bologna_recorded_source_corpus" in readiness.check_ids
    assert "source_entitlement" in readiness.check_ids
    assert "non_ready_must_sources" in readiness.blocker_ids
    assert "hosted_deployment_attestation" in readiness.blocker_ids
    assert all(blocker.status == "blocked" for blocker in readiness.blockers)
    assert readiness.ci_backed_check_count > 0
    assert readiness.local_only_check_count > 0


def test_release_readiness_app_model_rejects_duplicate_checks() -> None:
    payload = _release_catalog()
    duplicate = deepcopy(payload["required_checks"][0])
    payload["required_checks"].append(duplicate)

    with pytest.raises(ReleaseReadinessError, match="duplicate release check"):
        parse_release_readiness(payload, root=REPO_ROOT)


def test_project_readiness_app_model_loads_current_control_plane() -> None:
    readiness = load_project_readiness(REPO_ROOT)

    assert (
        readiness.checkpoint.active_plan
        == "plans/2026-06-22-hcv-4-status-config-consistency.md"
    )
    assert "EQP2-1" in readiness.checkpoint.completed_task_ids
    assert "EQP2-2" in readiness.checkpoint.completed_task_ids
    assert "EQP2-3" in readiness.checkpoint.completed_task_ids
    assert "EQP2-4" in readiness.checkpoint.completed_task_ids
    assert "BOL-AUTH-SYNC" in readiness.checkpoint.completed_task_ids
    assert "BAP-001" in readiness.checkpoint.completed_task_ids
    assert "BAR-001" in readiness.checkpoint.completed_task_ids
    assert "BSA-REC" in readiness.checkpoint.completed_task_ids
    assert "HCV-1" in readiness.checkpoint.completed_task_ids
    assert "HCV-2" in readiness.checkpoint.completed_task_ids
    assert "HCV-3" in readiness.checkpoint.completed_task_ids
    assert "READINESS-CORE" in readiness.checkpoint.completed_task_ids
    assert "BOL-PRIORITY" in readiness.checkpoint.completed_task_ids
    assert "BPS-001" in readiness.checkpoint.completed_task_ids
    assert "BPS-REQ-001" in readiness.checkpoint.completed_task_ids
    assert "EQ-1" in readiness.checkpoint.completed_task_ids
    assert "EQ-BOL" in readiness.checkpoint.completed_task_ids
    assert "EQ-2" in readiness.checkpoint.completed_task_ids
    assert "EQ-3" in readiness.checkpoint.completed_task_ids
    assert "EQ-4" in readiness.checkpoint.completed_task_ids
    assert "DS-017" in readiness.checkpoint.blocked_terms
    assert "Level 10" in readiness.checkpoint.blocked_terms
    assert "Bologna" in readiness.checkpoint.boundary_text
    assert readiness.task_queue.active_plan == readiness.checkpoint.active_plan
    assert any(task.task_id == "READINESS-CORE" for task in readiness.task_queue.completed_tasks)
    assert any(task.task_id == "BOL-PRIORITY" for task in readiness.task_queue.completed_tasks)
    assert any(task.task_id == "BPS-001" for task in readiness.task_queue.completed_tasks)
    assert any(task.task_id == "BPS-REQ-001" for task in readiness.task_queue.completed_tasks)
    assert any(task.task_id == "EQ-1" for task in readiness.task_queue.completed_tasks)
    assert any(task.task_id == "EQ-BOL" for task in readiness.task_queue.completed_tasks)
    assert any(task.task_id == "EQ-2" for task in readiness.task_queue.completed_tasks)
    assert any(task.task_id == "EQ-3" for task in readiness.task_queue.completed_tasks)
    assert any(task.task_id == "EQ-4" for task in readiness.task_queue.completed_tasks)
    assert any(task.task_id == "EQP2-4" for task in readiness.task_queue.completed_tasks)
    assert any(task.task_id == "BOL-AUTH-SYNC" for task in readiness.task_queue.completed_tasks)
    assert any(task.task_id == "BAP-001" for task in readiness.task_queue.completed_tasks)
    assert any(task.task_id == "BAR-001" for task in readiness.task_queue.completed_tasks)
    assert any(task.task_id == "BSA-REC" for task in readiness.task_queue.completed_tasks)
    assert any(task.task_id == "HCV-1" for task in readiness.task_queue.completed_tasks)
    assert any(task.task_id == "HCV-2" for task in readiness.task_queue.completed_tasks)
    assert any(task.task_id == "HCV-3" for task in readiness.task_queue.completed_tasks)
    assert any(task.task_id == "HCV-4" for task in readiness.task_queue.active_tasks)
    assert not any(
        task.task_id in {"REC-001", "BPS-001"}
        for task in readiness.task_queue.active_tasks
    )
    assert readiness.gate_matrix.status_counts["BLOCKED"] >= 1
    assert "L10-SEC-010" in readiness.gate_matrix.blocked_gate_ids
    assert any("verify.ps1" in command for command in readiness.validation.commands)


def test_project_readiness_app_model_rejects_missing_active_plan() -> None:
    state_text = (REPO_ROOT / "state" / "PROJECT_STATE.md").read_text(encoding="utf-8")
    broken_text = state_text.replace("**Current implementation plan**", "**Former plan**", 1)

    with pytest.raises(ProjectReadinessError, match="Current implementation plan"):
        parse_project_state(broken_text)
