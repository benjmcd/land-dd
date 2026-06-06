from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any, cast

yaml = cast(Any, importlib.import_module("yaml"))

REPO_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_CONTROLS = {
    "api_key_middleware",
    "api_key_rotation",
    "api_key_audit_logging",
    "reviewer_service_account",
    "reviewer_scope_enforcement",
    "protected_operator_routes",
    "public_health_routes",
}
REQUIRED_BLOCKERS = {
    "full_user_auth_rbac",
    "oauth_oidc_identity_provider",
    "user_account_persistence",
    "automatic_api_key_rotation",
    "full_user_role_policy",
}


def test_access_control_catalog_covers_current_controls_and_blockers() -> None:
    catalog = yaml.safe_load(
        (REPO_ROOT / "config" / "access_control.yaml").read_text(encoding="utf-8"),
    )

    assert catalog["schema_version"] == "access_control_v1"
    assert catalog["operator_runbook"] == "docs/runbooks/access_control.md"
    controls = {control["id"]: control for control in catalog["current_controls"]}
    assert REQUIRED_CONTROLS.issubset(set(controls))
    for control in controls.values():
        assert control["validation"] == "scripts/run_access_control_check.ps1"
        for authority in control["authority"]:
            assert (REPO_ROOT / authority).exists()

    blockers = {blocker["id"]: blocker for blocker in catalog["production_blockers"]}
    assert REQUIRED_BLOCKERS.issubset(set(blockers))
    for blocker in blockers.values():
        assert blocker["status"] == "blocked"
        assert (REPO_ROOT / blocker["authority"]).exists()


def test_access_control_runbook_records_validation_and_limits() -> None:
    runbook = (REPO_ROOT / "docs" / "runbooks" / "access_control.md").read_text(
        encoding="utf-8",
    )

    for phrase in (
        "run_access_control_check.ps1",
        "validate-only",
        "X-API-Key",
        "X-Reviewer-Id",
        "X-Reviewer-Token",
        "REVIEWER_ACCOUNT_SCOPES",
        "connector:run",
        "connector:review",
        "operations:read",
        "report:retry",
        "report:run",
        "No full user auth/RBAC exists yet.",
        "No OAuth/OIDC",
        "No user-account persistence",
        "API_KEY_SPECS",
        "API-key audit logging",
        "event_type=api_key_auth",
        "audit.events",
        "DB-service mode",
        "hosted log-retention/export/SIEM",
        "durable per-key usage audit ledger",
        "configured static key lifecycle exists",
        "no automatic",
    ):
        assert phrase in runbook


def test_access_control_ci_job_runs_validate_only_proof() -> None:
    ci_text = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8",
    )
    ci = yaml.safe_load(ci_text)
    job = ci["jobs"]["access-control"]
    steps_text = "\n".join(
        str(step.get("uses", ""))
        + "\n"
        + str(step.get("run", ""))
        + "\n"
        + str(step.get("with", ""))
        for step in job["steps"]
    )

    assert job["permissions"]["contents"] == "read"
    assert "actions/checkout@v4" in steps_text
    assert "actions/setup-python@v5" in steps_text
    assert "python-version: '3.12'" in ci_text
    assert "python -m pip install PyYAML" in steps_text
    assert "./scripts/run_access_control_check.sh" in steps_text


def test_access_control_scripts_exist_for_windows_and_posix() -> None:
    assert (REPO_ROOT / "scripts" / "run_access_control_check.ps1").is_file()
    assert (REPO_ROOT / "scripts" / "run_access_control_check.sh").is_file()
