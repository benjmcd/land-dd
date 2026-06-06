#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

required_files=(
  "config/access_control.yaml"
  "docs/runbooks/access_control.md"
  ".env.example"
  ".github/workflows/ci.yml"
  "docker-compose.yml"
  "backend/app/api/auth_audit.py"
  "backend/app/api/api_key_auth.py"
  "backend/app/api/reviewer_auth.py"
  "backend/app/api/secret_specs.py"
  "backend/app/api/connectors.py"
  "backend/app/api/operations.py"
  "backend/app/api/reports.py"
  "backend/app/core/config.py"
  "backend/tests/api/test_api_key_auth.py"
  "backend/tests/api/test_reviewer_auth.py"
)

for file in "${required_files[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "required access-control artifact missing: $file" >&2
    exit 1
  fi
done

python - <<'PY'
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path.cwd()
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


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def require_existing(path_text: str) -> None:
    normalized = path_text.replace("\\", "/")
    require((ROOT / normalized).exists(), f"referenced access-control artifact missing: {normalized}")


def step_text(job: dict[str, Any], job_name: str) -> str:
    steps = job.get("steps")
    require(isinstance(steps, list) and steps, f"{job_name} job has no steps")
    return "\n".join(
        str(step.get("uses", "")) + "\n" + str(step.get("run", "")) + "\n" + str(step.get("with", ""))
        for step in steps
        if isinstance(step, dict)
    )


catalog = yaml.safe_load((ROOT / "config" / "access_control.yaml").read_text(encoding="utf-8"))
require(isinstance(catalog, dict), "access-control catalog must be a mapping")
require(catalog.get("schema_version") == "access_control_v1", "unexpected access-control schema")
require(catalog.get("operator_runbook") == "docs/runbooks/access_control.md", "operator runbook mismatch")
controls = catalog.get("current_controls")
require(isinstance(controls, list) and controls, "current controls missing")
control_ids = set()
for control in controls:
    require(isinstance(control, dict), "each current control must be a mapping")
    control_id = control.get("id")
    require(isinstance(control_id, str) and control_id, "control id missing")
    control_ids.add(control_id)
    authority = control.get("authority")
    require(isinstance(authority, list) and authority, f"{control_id} authority missing")
    for authority_path in authority:
        require(isinstance(authority_path, str), f"{control_id} authority path must be a string")
        require_existing(authority_path)
    validation = control.get("validation")
    require(isinstance(validation, str) and validation, f"{control_id} validation missing")
    require_existing(validation)
require(REQUIRED_CONTROLS.issubset(control_ids), f"missing controls: {sorted(REQUIRED_CONTROLS - control_ids)}")

blockers = catalog.get("production_blockers")
require(isinstance(blockers, list) and blockers, "production blockers missing")
blocker_ids = set()
for blocker in blockers:
    require(isinstance(blocker, dict), "each production blocker must be a mapping")
    blocker_id = blocker.get("id")
    require(isinstance(blocker_id, str) and blocker_id, "blocker id missing")
    blocker_ids.add(blocker_id)
    require(blocker.get("status") == "blocked", f"{blocker_id} must remain blocked")
    authority = blocker.get("authority")
    require(isinstance(authority, str) and authority, f"{blocker_id} authority missing")
    require_existing(authority)
require(REQUIRED_BLOCKERS.issubset(blocker_ids), f"missing blockers: {sorted(REQUIRED_BLOCKERS - blocker_ids)}")

api_auth = (ROOT / "backend" / "app" / "api" / "api_key_auth.py").read_text(encoding="utf-8")
auth_audit = (ROOT / "backend" / "app" / "api" / "auth_audit.py").read_text(encoding="utf-8")
main = (ROOT / "backend" / "app" / "main.py").read_text(encoding="utf-8")
secret_specs = (ROOT / "backend" / "app" / "api" / "secret_specs.py").read_text(encoding="utf-8")
api_tests = (ROOT / "backend" / "tests" / "api" / "test_api_key_auth.py").read_text(encoding="utf-8")
settings = (ROOT / "backend" / "app" / "core" / "config.py").read_text(encoding="utf-8")
for phrase in (
    'API_KEY_HEADER = "X-API-Key"',
    'PUBLIC_PATHS = frozenset({"/health", "/version"})',
    "matches_any_secret_spec",
    "ApiKeyCredential",
    "event_type",
    "api_key_auth",
    "api_key_id",
    "api_key_source",
    "logger.info",
    "ApiKeyAuthAuditEvent",
    "audit_log.record",
    "API key audit logging failed",
    "API key auth is not configured",
    "API key is required",
    "API key is invalid",
    "status_code=503",
    "status_code=401",
    "status_code=403",
):
    require(phrase in api_auth, f"api key auth missing phrase: {phrase}")
for phrase in (
    "ApiKeyAuthAuditEvent",
    "ApiKeyAuthAuditOutcome",
    "InMemoryApiKeyAuthAuditLog",
    "SqlAlchemyApiKeyAuthAuditLog",
    "INSERT INTO audit.events",
    "'api_key_auth'",
    "'api.api_key_auth'",
    "api_key_id",
    "api_key_source",
    "CAST(:payload AS jsonb)",
    "CAST(:ip_address AS inet)",
):
    require(phrase in auth_audit, f"api key audit module missing phrase: {phrase}")
for phrase in (
    "SqlAlchemyApiKeyAuthAuditLog",
    "get_session_factory",
    "_build_api_key_audit_log",
    "use_db_services=resolved_use_db_services",
    "api_key_audit_log",
):
    require(phrase in main, f"app wiring missing API-key audit phrase: {phrase}")
for phrase in (
    "SHA256_SECRET_PREFIX",
    "normalize_secret_spec",
    "matches_any_secret_spec",
    "matches_secret_spec",
    "compare_digest",
    "sha256(",
):
    require(phrase in secret_specs, f"secret spec helper missing phrase: {phrase}")
for phrase in (
    "require_api_key: bool = Field(default=False",
    "api_keys: str = Field(",
    "api_key_specs: str = Field(",
    "API_KEY_SPECS",
    "API_KEY_STATUS_ACTIVE",
    "API_KEY_STATUS_RETIRED",
    "parsed_api_key_specs",
    "Duplicate API_KEYS entry",
    "Duplicate API_KEY_SPECS id",
    "Duplicate API_KEY_SPECS secret",
    "normalize_secret_spec",
):
    require(phrase in settings, f"settings missing API-key phrase: {phrase}")
for phrase in (
    "test_api_key_auth_requires_key_for_protected_paths",
    "test_api_key_auth_rejects_invalid_key",
    "test_api_key_auth_fails_closed_when_required_but_unconfigured",
    "test_api_key_auth_leaves_health_and_version_public",
    "test_api_key_auth_accepts_configured_sha256_key_hash",
    "test_api_key_auth_accepts_active_api_key_spec",
    "test_api_key_auth_rejects_retired_api_key_spec",
    "test_api_key_auth_logs_accepted_lifecycle_key_without_secret",
    "test_api_key_auth_logs_invalid_key_without_secret_or_key_id",
    "test_api_key_auth_logs_legacy_key_without_key_id",
    "test_api_key_auth_records_accepted_lifecycle_key_audit_event_without_secret",
    "test_api_key_auth_records_invalid_key_audit_event_without_secret_or_key_id",
    "test_api_key_auth_fails_closed_when_audit_event_persistence_fails",
    "test_sqlalchemy_api_key_auth_audit_log_persists_event_without_secret",
    "test_settings_parses_api_key_lifecycle_specs",
    "test_settings_api_key_lifecycle_specs_fail_closed_for_malformed_entries",
    "test_settings_api_key_hash_specs_fail_closed_for_malformed_entries",
):
    require(phrase in api_tests, f"api key tests missing phrase: {phrase}")

reviewer_auth = (ROOT / "backend" / "app" / "api" / "reviewer_auth.py").read_text(encoding="utf-8")
reviewer_tests = (ROOT / "backend" / "tests" / "api" / "test_reviewer_auth.py").read_text(encoding="utf-8")
for phrase in (
    'Header(alias="X-Reviewer-Id")',
    'Header(alias="X-Reviewer-Token")',
    "REVIEWER_SCOPE_CONNECTOR_RUN",
    "REVIEWER_SCOPE_CONNECTOR_REVIEW",
    "REVIEWER_SCOPE_OPERATIONS_READ",
    "REVIEWER_SCOPE_REPORT_RETRY",
    "REVIEWER_SCOPE_REPORT_RUN",
    "require_reviewer_scope",
    "matches_secret_spec",
    "normalize_secret_spec",
    "connector reviewer auth is not configured",
    "connector reviewer credentials are required",
    "connector reviewer credentials are invalid",
    "reviewer scope is required:",
    "HTTP_503_SERVICE_UNAVAILABLE",
    "HTTP_401_UNAUTHORIZED",
    "HTTP_403_FORBIDDEN",
    "scopes: frozenset[str]",
    'auth_scheme: str = "local_service_account"',
):
    require(phrase in reviewer_auth, f"reviewer auth missing phrase: {phrase}")
for phrase in (
    "reviewer_accounts: str = Field(",
    "reviewer_account_scopes: str = Field(",
    "REVIEWER_ACCOUNT_SCOPES",
    "Defaults to a local fixture account; override in production.",
    "parsed_reviewer_accounts",
    "parsed_reviewer_account_scopes",
    "Duplicate REVIEWER_ACCOUNTS",
    "Duplicate REVIEWER_ACCOUNT_SCOPES",
    "normalize_secret_spec",
):
    require(phrase in settings, f"settings missing reviewer phrase: {phrase}")
for phrase in (
    "test_local_service_account_reviewer_auth_returns_principal",
    "test_local_service_account_reviewer_auth_rejects_missing_scope",
    "test_local_service_account_reviewer_auth_fails_closed_without_scopes",
    "test_settings_parses_reviewer_account_scopes",
    "test_settings_reviewer_account_scopes_fail_closed_for_malformed_entries",
    "test_local_service_account_reviewer_auth_rejects_missing_credentials",
    "test_local_service_account_reviewer_auth_rejects_invalid_credentials",
    "test_local_service_account_reviewer_auth_fails_closed_when_unconfigured",
    "test_local_service_account_reviewer_auth_accepts_sha256_token_hash",
    "test_settings_reviewer_account_hash_specs_fail_closed_for_malformed_entries",
):
    require(phrase in reviewer_tests, f"reviewer auth tests missing phrase: {phrase}")

for route_file in ("connectors.py", "operations.py", "reports.py"):
    text = (ROOT / "backend" / "app" / "api" / route_file).read_text(encoding="utf-8")
    require("ReviewerPrincipal" in text, f"{route_file} must depend on ReviewerPrincipal")
    require("get_reviewer_principal" in text, f"{route_file} must expose reviewer dependency")
    require("require_reviewer_scope" in text, f"{route_file} must enforce reviewer scopes")
connectors = (ROOT / "backend" / "app" / "api" / "connectors.py").read_text(encoding="utf-8")
operations = (ROOT / "backend" / "app" / "api" / "operations.py").read_text(encoding="utf-8")
reports = (ROOT / "backend" / "app" / "api" / "reports.py").read_text(encoding="utf-8")
require("reviewer_id=principal.reviewer_id" in connectors, "connector review actions must use authenticated reviewer id")
for phrase in (
    "REVIEWER_SCOPE_CONNECTOR_RUN",
    "REVIEWER_SCOPE_CONNECTOR_REVIEW",
    "REVIEWER_SCOPE_OPERATIONS_READ",
    "REVIEWER_SCOPE_REPORT_RUN",
):
    require(phrase in connectors, f"connectors route missing scope phrase: {phrase}")
require("REVIEWER_SCOPE_OPERATIONS_READ" in operations, "operations route must require operations read scope")
require("REVIEWER_SCOPE_REPORT_RETRY" in reports, "reports route must require report retry scope")
tests = "\n".join(
    (ROOT / "backend" / "tests" / "api" / test_file).read_text(encoding="utf-8")
    for test_file in (
        "test_connector_review_actions.py",
        "test_operations.py",
        "test_async_report_runs.py",
        "test_fema_nfhl_connector_api.py",
    )
)
for phrase in (
    "test_request_fixture_fix_rejects_reviewer_without_review_scope",
    "test_queue_health_rejects_reviewer_without_operations_read_scope",
    "test_retry_report_run_rejects_reviewer_without_retry_scope",
    "test_fema_nfhl_schedule_bbox_rejects_reviewer_without_connector_run_scope",
):
    require(phrase in tests, f"scoped route tests missing phrase: {phrase}")

ci_text = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
ci = yaml.safe_load(ci_text)
require(isinstance(ci, dict), "ci workflow must be a mapping")
jobs = ci.get("jobs")
require(isinstance(jobs, dict), "ci workflow jobs missing")
job = jobs.get("access-control")
require(isinstance(job, dict), "ci workflow missing access-control job")
permissions = job.get("permissions")
require(isinstance(permissions, dict), "access-control permissions missing")
require(permissions.get("contents") == "read", "access-control must use read-only contents permission")
text = step_text(job, "access-control")
require("actions/checkout@v6" in text, "access-control job must checkout repo")
require("actions/setup-python@v6" in text, "access-control job must setup Python")
require("python-version: '3.12'" in ci_text, "access-control job must use Python 3.12")
require("python -m pip install PyYAML" in text, "access-control job must install PyYAML")
require("./scripts/run_access_control_check.sh" in text, "access-control job must run POSIX proof")

runbook = (ROOT / "docs" / "runbooks" / "access_control.md").read_text(encoding="utf-8")
for phrase in (
    "run_access_control_check.ps1",
    "validate-only",
    "X-API-Key",
    "X-Reviewer-Id",
    "X-Reviewer-Token",
    "sha256:<64-hex>",
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
    require(phrase in runbook, f"access-control runbook missing phrase: {phrase}")
env_example = (ROOT / ".env.example").read_text(encoding="utf-8")
compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
for text_name, text_payload in ((".env.example", env_example), ("docker-compose.yml", compose)):
    require("REVIEWER_ACCOUNT_SCOPES" in text_payload, f"{text_name} missing reviewer scope env")
    require("API_KEY_SPECS" in text_payload, f"{text_name} missing API key lifecycle env")
require("sha256:<64-hex>" in env_example, ".env.example missing hashed secret guidance")
PY

echo "access-control check: ok"
