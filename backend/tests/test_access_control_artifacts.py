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
    "hosted_secret_manager",
    "full_user_role_policy",
}
REQUIRED_SECRET_REFS = {
    "API_KEY_SPECS",
    "REVIEWER_ACCOUNTS",
    "REVIEWER_ACCOUNT_SCOPES",
    "UI_AUTH_COOKIE_SECRET",
    "REPORT_IDENTITY_TOKEN_SECRET",
    "DATABASE_URL",
}
REQUIRED_IDENTITY_CLAIMS = {
    "subject",
    "email",
    "display_name",
    "workspace_id",
    "user_id",
    "groups_or_roles",
}
REQUIRED_IDENTITY_ROLES = {
    "platform_admin",
    "workspace_admin",
    "reviewer",
    "operator",
    "read_only",
}
REQUIRED_ROUTE_SCOPES = {
    "connector:run",
    "connector:review",
    "operations:read",
    "report:retry",
    "report:run",
    "report:approve",
    "source:manage",
}
REQUIRED_IDENTITY_AUDIT_REQUIREMENTS = {
    "idp_subject",
    "workspace_id",
    "user_id",
    "route_scope",
    "session_or_token_id",
    "decision_outcome",
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


def test_access_control_catalog_records_secret_management_contract() -> None:
    catalog = yaml.safe_load(
        (REPO_ROOT / "config" / "access_control.yaml").read_text(encoding="utf-8"),
    )

    contract = catalog["secret_management_contract"]
    assert contract["status"] == "repo_local_handoff_contract"
    assert contract["hosted_secret_manager_status"] == "blocked"
    for authority in contract["authority"]:
        assert (REPO_ROOT / authority).exists()

    refs = {ref["id"]: ref for ref in contract["required_runtime_refs"]}
    assert REQUIRED_SECRET_REFS == set(refs)
    assert refs["API_KEY_SPECS"]["required_when"].startswith("REQUIRE_API_KEY=true")
    assert "sha256:<64-hex>" in refs["API_KEY_SPECS"]["format"]
    assert "sha256:<64-hex>" in refs["REVIEWER_ACCOUNTS"]["format"]
    assert refs["REVIEWER_ACCOUNT_SCOPES"]["required_when"].startswith("every")
    assert refs["UI_AUTH_COOKIE_SECRET"]["required_when"].startswith(
        "REQUIRE_API_KEY=true",
    )
    assert refs["REPORT_IDENTITY_TOKEN_SECRET"]["required_when"] == (
        "REPORT_AUTH_MODE=signed_token"
    )
    assert refs["DATABASE_URL"]["required_when"].startswith("USE_DB_SERVICES=true")

    assert {
        "external_secret_manager_reference_names",
        "per_environment_secret_owner",
        "rotation_runbook_or_ticket",
        "post_rotation_access_control_check",
        "no_plaintext_committed_secret_values",
    } == set(contract["handoff_requirements"])
    assert contract["limits"] == {
        "validate_only_catalog": True,
        "writes_secrets": False,
        "provisions_hosted_secret_manager": False,
        "permits_committed_plaintext_secrets": False,
    }


def test_access_control_catalog_records_identity_rbac_contract() -> None:
    catalog = yaml.safe_load(
        (REPO_ROOT / "config" / "access_control.yaml").read_text(encoding="utf-8"),
    )

    blockers = {blocker["id"]: blocker for blocker in catalog["production_blockers"]}
    for blocker_id in (
        "oauth_oidc_identity_provider",
        "full_user_auth_rbac",
        "user_account_persistence",
        "full_user_role_policy",
    ):
        assert blockers[blocker_id]["status"] == "blocked"

    contract = catalog["identity_rbac_contract"]
    assert contract["status"] == "repo_local_design_contract"
    assert contract["hosted_identity_provider_status"] == "blocked"
    assert contract["user_account_persistence_status"] == "blocked"
    assert contract["full_role_policy_status"] == "blocked"
    for authority in contract["authority"]:
        assert (REPO_ROOT / authority).exists()

    assert REQUIRED_IDENTITY_CLAIMS == set(contract["required_identity_claims"])
    assert REQUIRED_IDENTITY_ROLES == set(contract["role_mappings"])

    mapped_scopes = {
        scope
        for role in contract["role_mappings"].values()
        for scope in role["scopes"]
    }
    assert REQUIRED_ROUTE_SCOPES == mapped_scopes
    assert REQUIRED_IDENTITY_AUDIT_REQUIREMENTS.issubset(
        set(contract["audit_requirements"]),
    )
    assert "record_user_bound_audit_events" in contract["migration_requirements"]
    assert contract["limits"] == {
        "validate_only_catalog": True,
        "provisions_identity_provider": False,
        "creates_user_account_tables": False,
        "implements_oauth_oidc": False,
        "claims_production_rbac": False,
    }


def test_access_control_runbook_records_validation_and_limits() -> None:
    runbook = (REPO_ROOT / "docs" / "runbooks" / "access_control.md").read_text(
        encoding="utf-8",
    )

    for phrase in (
        "run_access_control_check.ps1",
        "scripts/access_control_check.py",
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
        "secret_management_contract",
        "validate-only secret handoff",
        "API_KEY_SPECS, REVIEWER_ACCOUNTS, REVIEWER_ACCOUNT_SCOPES",
        "UI_AUTH_COOKIE_SECRET, REPORT_IDENTITY_TOKEN_SECRET, and DATABASE_URL",
        "REPORT_AUTH_MODE=signed_token",
        "no committed secret values",
        "no secret writes",
        "no hosted secret manager provisioning",
        "identity_rbac_contract",
        "validate-only identity/RBAC design handoff",
        "required identity claims are subject, email, display_name, workspace_id",
        "groups_or_roles",
        "groups/roles supplied",
        "platform_admin, workspace_admin, reviewer, operator, and read_only",
        "connector:run, connector:review, operations:read",
        "report:retry, report:run, report:approve, and source:manage",
        "user-bound audit events",
        "IdP subject",
        "workspace/user id",
        "session/token id",
        "decision outcome",
        "no IdP provisioning",
        "no user DB tables",
        "no OAuth/OIDC implementation",
        "no production RBAC claim",
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
    assert "actions/checkout@v6" in steps_text
    assert "actions/setup-python@v6" in steps_text
    assert "python-version: '3.12'" in ci_text
    assert "python -m pip install PyYAML" in steps_text
    assert "./scripts/run_access_control_check.sh" in steps_text


def test_access_control_scripts_exist_for_windows_and_posix() -> None:
    assert (REPO_ROOT / "scripts" / "access_control_check.py").is_file()
    assert (REPO_ROOT / "scripts" / "run_access_control_check.ps1").is_file()
    assert (REPO_ROOT / "scripts" / "run_access_control_check.sh").is_file()


def test_operator_source_seed_scripts_use_reviewer_headers() -> None:
    live_smoke = (REPO_ROOT / "scripts" / "run_live_smoke.py").read_text(
        encoding="utf-8",
    )
    demo_mvp = (REPO_ROOT / "scripts" / "demo_mvp.py").read_text(
        encoding="utf-8",
    )

    assert "X-Reviewer-Id" in live_smoke
    assert "X-Reviewer-Token" in live_smoke
    assert '_post(base_url, "/sources", body, _reviewer_headers())' in live_smoke
    assert "X-Reviewer-Id" in demo_mvp
    assert "X-Reviewer-Token" in demo_mvp
    assert 'client.request("POST", "/sources", payload, headers=reviewer_headers)' in demo_mvp


def test_access_control_validator_tracks_compat_review_queue_scope() -> None:
    validator = (REPO_ROOT / "scripts" / "access_control_check.py").read_text(
        encoding="utf-8",
    )

    for phrase in (
        "approve_connector_review_queue_item_compat",
        "reject_connector_review_queue_item_compat",
        "requeue_connector_review_queue_item_compat",
        "cancel_connector_review_queue_item_compat",
        "test_connector_review_action_requires_reviewer_credentials",
        "test_connector_review_action_rejects_reviewer_without_review_scope",
    ):
        assert phrase in validator


def test_access_control_validator_tracks_current_ui_reviewer_session_design() -> None:
    validator = (REPO_ROOT / "scripts" / "access_control_check.py").read_text(
        encoding="utf-8",
    )
    design = (REPO_ROOT / "DESIGN.md").read_text(encoding="utf-8")

    for phrase in (
        "API reviewer tokens remain header-only and separate from API keys",
        "browser reviewer actions can use `/ui/auth/reviewer`",
        "signed, expiring, HttpOnly reviewer session cookie scoped to `/ui`",
    ):
        assert phrase in validator
        assert phrase in design


def test_access_control_validator_tracks_route_level_ui_csrf_proofs() -> None:
    validator = (REPO_ROOT / "scripts" / "access_control_check.py").read_text(
        encoding="utf-8",
    )

    for phrase in (
        "test_ui_intake_reviewer_session_requires_csrf",
        "test_ui_retry_report_run_reviewer_session_requires_csrf",
        "test_ui_review_mutation_reviewer_session_requires_csrf",
        '("reject", "flood_failure.json")',
        '("requeue", "flood_failure.json")',
        '("cancel", "flood_failure.json")',
        '("resume-report", "flood_success.json")',
        "assert response.status_code == 403",
        '"Security Check Failed" in response.text',
        "test_ui_review_reject_reviewer_session_accepts_valid_csrf",
        "test_ui_review_requeue_reviewer_session_accepts_valid_csrf",
        "test_ui_review_cancel_reviewer_session_accepts_valid_csrf",
        "test_ui_review_resume_report_reviewer_session_accepts_valid_csrf",
        "test_ui_operations_recovery_preview_post_reviewer_session_requires_csrf",
        "test_ui_operations_recovery_preview_post_reviewer_session_accepts_valid_csrf",
    ):
        assert phrase in validator


def test_operator_runbook_tracks_current_ui_reviewer_session_design() -> None:
    runbook = (REPO_ROOT / "docs" / "runbooks" / "mvp_operator.md").read_text(
        encoding="utf-8",
    )

    assert "reviewer UI session" in runbook
    assert "the form requires **Reviewer ID** and **Reviewer token** fields" in runbook
    assert "can establish the UI-only" in runbook
    assert "reviewer session described below" in runbook
    assert "There is no session or cookie" not in runbook


def test_access_control_wrappers_delegate_to_shared_validator() -> None:
    for script_name in ("run_access_control_check.ps1", "run_access_control_check.sh"):
        script = (REPO_ROOT / "scripts" / script_name).read_text(encoding="utf-8")

        assert "access_control_check.py" in script
