from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import yaml

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "config/access_control.yaml",
    "MANIFEST.md",
    "docs/runbooks/access_control.md",
    "docs/runbooks/mvp_operator.md",
    ".env.example",
    ".github/workflows/ci.yml",
    "docker-compose.yml",
    "DESIGN.md",
    "backend/app/api/auth_audit.py",
    "backend/app/api/api_key_auth.py",
    "backend/app/api/ui.py",
    "backend/app/api/ui_auth.py",
    "backend/app/api/ui_lineage.py",
    "backend/app/api/ui_operations.py",
    "backend/app/api/ui_review.py",
    "backend/app/api/ui_shared.py",
    "backend/app/api/reviewer_auth.py",
    "backend/app/api/secret_specs.py",
    "backend/app/api/connectors.py",
    "backend/app/api/operations.py",
    "backend/app/api/reports.py",
    "backend/app/api/sources.py",
    "backend/app/core/config.py",
    "backend/tests/api/test_api_key_auth.py",
    "backend/tests/api/test_ui_api_key_auth.py",
    "backend/tests/api/test_reviewer_auth.py",
    "scripts/access_control_check.py",
    "scripts/run_access_control_check.ps1",
    "scripts/run_access_control_check.sh",
)
REQUIRED_CONTROLS = {
    "api_key_middleware",
    "api_key_rotation",
    "api_key_audit_logging",
    "ui_api_key_cookie_bridge",
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
REQUIRED_SECRET_HANDOFFS = {
    "external_secret_manager_reference_names",
    "no_plaintext_committed_secret_values",
    "per_environment_secret_owner",
    "post_rotation_access_control_check",
    "rotation_runbook_or_ticket",
}
REQUIRED_IDENTITY_CLAIMS = {
    "display_name",
    "email",
    "groups_or_roles",
    "subject",
    "user_id",
    "workspace_id",
}
REQUIRED_IDENTITY_ROLES = {
    "operator",
    "platform_admin",
    "read_only",
    "reviewer",
    "workspace_admin",
}
REQUIRED_ROUTE_SCOPES = {
    "connector:review",
    "connector:run",
    "operations:read",
    "report:approve",
    "report:retry",
    "report:run",
    "source:manage",
}
REQUIRED_IDENTITY_AUDIT_REQUIREMENTS = {
    "decision_outcome",
    "idp_subject",
    "role_ids",
    "route_scope",
    "session_or_token_id",
    "user_id",
    "workspace_id",
}
REQUIRED_IDENTITY_MIGRATIONS = {
    "bind_report_identity_tokens_to_user_account",
    "map_current_reviewer_scopes_to_roles",
    "preserve_static_service_account_breakglass",
    "record_user_bound_audit_events",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def require_existing(path_text: str) -> None:
    normalized = path_text.replace("\\", "/")
    require(
        (ROOT / normalized).exists(),
        f"referenced access-control artifact missing: {normalized}",
    )


def read_text(path_text: str) -> str:
    return (ROOT / path_text).read_text(encoding="utf-8")


def step_text(job: dict[str, Any], job_name: str) -> str:
    steps = job.get("steps")
    if not isinstance(steps, list) or not steps:
        raise SystemExit(f"{job_name} job has no steps")
    return "\n".join(
        str(step.get("uses", ""))
        + "\n"
        + str(step.get("run", ""))
        + "\n"
        + str(step.get("with", ""))
        for step in steps
        if isinstance(step, dict)
    )


def require_phrases(text: str, phrases: tuple[str, ...], label: str) -> None:
    for phrase in phrases:
        require(phrase in text, f"{label} missing phrase: {phrase}")


def function_block(text: str, function_name: str) -> str:
    marker = f"def {function_name}("
    start = text.find(marker)
    require(start >= 0, f"function not found: {function_name}")
    next_start = text.find("\ndef ", start + len(marker))
    if next_start < 0:
        return text[start:]
    return text[start:next_start]


def validate_required_files() -> None:
    for path_text in REQUIRED_FILES:
        require(
            (ROOT / path_text).is_file(),
            f"required access-control artifact missing: {path_text}",
        )


def validate_catalog() -> None:
    payload = yaml.safe_load(read_text("config/access_control.yaml"))
    require(isinstance(payload, dict), "access-control catalog must be a mapping")
    require(
        payload.get("schema_version") == "access_control_v1",
        "unexpected access-control schema",
    )
    require(
        payload.get("operator_runbook") == "docs/runbooks/access_control.md",
        "operator runbook mismatch",
    )

    controls = payload.get("current_controls")
    if not isinstance(controls, list) or not controls:
        raise SystemExit("current controls missing")
    control_ids: set[str] = set()
    control_authorities: dict[str, set[str]] = {}
    for control in controls:
        require(isinstance(control, dict), "each current control must be a mapping")
        control_id = control.get("id")
        if not isinstance(control_id, str) or not control_id:
            raise SystemExit("control id missing")
        require(control_id not in control_ids, f"duplicate control id: {control_id}")
        control_ids.add(control_id)
        control_authorities[control_id] = set()
        authority = control.get("authority")
        if not isinstance(authority, list) or not authority:
            raise SystemExit(f"{control_id} authority missing")
        for authority_path in authority:
            require(
                isinstance(authority_path, str),
                f"{control_id} authority path must be a string",
            )
            control_authorities[control_id].add(authority_path)
            require_existing(authority_path)
        validation = control.get("validation")
        if not isinstance(validation, str) or not validation:
            raise SystemExit(f"{control_id} validation missing")
        require_existing(validation)
    missing_controls = sorted(REQUIRED_CONTROLS - control_ids)
    require(not missing_controls, f"missing controls: {missing_controls}")
    ui_bridge_authority = control_authorities.get("ui_api_key_cookie_bridge", set())
    required_ui_bridge_authority = {
        ".env.example",
        "DESIGN.md",
        "backend/app/api/api_key_auth.py",
        "backend/app/api/ui.py",
        "backend/app/api/ui_auth.py",
        "backend/app/api/ui_lineage.py",
        "backend/app/api/ui_operations.py",
        "backend/app/api/ui_review.py",
        "backend/app/api/ui_shared.py",
        "backend/app/core/config.py",
        "backend/app/main.py",
        "backend/tests/api/test_ui_api_key_auth.py",
        "docs/runbooks/access_control.md",
        "docs/runbooks/mvp_operator.md",
    }
    missing_ui_bridge_authority = sorted(
        required_ui_bridge_authority - ui_bridge_authority
    )
    require(
        not missing_ui_bridge_authority,
        f"ui_api_key_cookie_bridge authority missing: {missing_ui_bridge_authority}",
    )
    unexpected_ui_bridge_authority = sorted(
        ui_bridge_authority - required_ui_bridge_authority
    )
    require(
        not unexpected_ui_bridge_authority,
        f"ui_api_key_cookie_bridge authority unexpected: {unexpected_ui_bridge_authority}",
    )

    blockers = payload.get("production_blockers")
    if not isinstance(blockers, list) or not blockers:
        raise SystemExit("production blockers missing")
    blocker_ids: set[str] = set()
    for blocker in blockers:
        require(isinstance(blocker, dict), "each production blocker must be a mapping")
        blocker_id = blocker.get("id")
        if not isinstance(blocker_id, str) or not blocker_id:
            raise SystemExit("blocker id missing")
        require(blocker_id not in blocker_ids, f"duplicate blocker id: {blocker_id}")
        blocker_ids.add(blocker_id)
        require(blocker.get("status") == "blocked", f"{blocker_id} must remain blocked")
        authority = blocker.get("authority")
        if not isinstance(authority, str) or not authority:
            raise SystemExit(f"{blocker_id} authority missing")
        require_existing(authority)
    missing_blockers = sorted(REQUIRED_BLOCKERS - blocker_ids)
    require(not missing_blockers, f"missing blockers: {missing_blockers}")
    validate_secret_management_contract(payload)
    validate_identity_rbac_contract(payload)


def validate_secret_management_contract(payload: dict[str, Any]) -> None:
    contract_raw = payload.get("secret_management_contract")
    require(isinstance(contract_raw, dict), "secret_management_contract missing")
    contract = cast(dict[str, Any], contract_raw)
    require(
        contract.get("status") == "repo_local_handoff_contract",
        "secret_management_contract status mismatch",
    )
    authority_raw = contract.get("authority")
    require(
        isinstance(authority_raw, list) and bool(authority_raw),
        "secret management authority missing",
    )
    authority = cast(list[Any], authority_raw)
    for authority_path in authority:
        require(isinstance(authority_path, str), "secret management authority must be strings")
        require_existing(authority_path)
    require(
        contract.get("hosted_secret_manager_status") == "blocked",
        "hosted secret manager status must remain blocked until provisioned",
    )

    refs_raw = contract.get("required_runtime_refs")
    require(isinstance(refs_raw, list) and bool(refs_raw), "required_runtime_refs missing")
    refs = cast(list[Any], refs_raw)
    seen_refs: set[str] = set()
    for ref_raw in refs:
        require(isinstance(ref_raw, dict), "each secret runtime ref must be a mapping")
        ref = cast(dict[str, Any], ref_raw)
        ref_id = ref.get("id")
        if not isinstance(ref_id, str) or not ref_id:
            raise SystemExit("secret ref id missing")
        require(ref_id not in seen_refs, f"duplicate secret ref id: {ref_id}")
        seen_refs.add(ref_id)
        for key in ("required_when", "format", "rotation"):
            value = ref.get(key)
            require(
                isinstance(value, str) and bool(value.strip()),
                f"{ref_id} missing {key}",
            )
    missing_refs = sorted(REQUIRED_SECRET_REFS - seen_refs)
    require(not missing_refs, f"missing secret refs: {missing_refs}")

    handoffs_raw = contract.get("handoff_requirements")
    require(
        isinstance(handoffs_raw, list) and bool(handoffs_raw),
        "handoff_requirements missing",
    )
    handoffs = cast(list[Any], handoffs_raw)
    missing_handoffs = sorted(REQUIRED_SECRET_HANDOFFS - set(handoffs))
    require(not missing_handoffs, f"missing secret handoff requirements: {missing_handoffs}")

    limits_raw = contract.get("limits")
    require(isinstance(limits_raw, dict), "secret management limits missing")
    limits = cast(dict[str, Any], limits_raw)
    require(limits.get("validate_only_catalog") is True, "secret contract must be validate-only")
    require(limits.get("writes_secrets") is False, "secret contract must not write secrets")
    require(
        limits.get("provisions_hosted_secret_manager") is False,
        "secret contract must not provision hosted secret manager",
    )
    require(
        limits.get("permits_committed_plaintext_secrets") is False,
        "secret contract must not permit committed plaintext secrets",
    )


def validate_identity_rbac_contract(payload: dict[str, Any]) -> None:
    contract_raw = payload.get("identity_rbac_contract")
    require(isinstance(contract_raw, dict), "identity_rbac_contract missing")
    contract = cast(dict[str, Any], contract_raw)
    require(
        contract.get("status") == "repo_local_design_contract",
        "identity_rbac_contract status mismatch",
    )
    authority_raw = contract.get("authority")
    require(
        isinstance(authority_raw, list) and bool(authority_raw),
        "identity RBAC authority missing",
    )
    authority = cast(list[Any], authority_raw)
    for authority_path in authority:
        require(isinstance(authority_path, str), "identity RBAC authority must be strings")
        require_existing(authority_path)
    for key in (
        "hosted_identity_provider_status",
        "user_account_persistence_status",
        "full_role_policy_status",
    ):
        require(contract.get(key) == "blocked", f"{key} must remain blocked")

    claims_raw = contract.get("required_identity_claims")
    require(
        isinstance(claims_raw, list) and bool(claims_raw),
        "required_identity_claims missing",
    )
    claims = cast(list[Any], claims_raw)
    missing_claims = sorted(REQUIRED_IDENTITY_CLAIMS - set(claims))
    require(not missing_claims, f"identity claims missing: {missing_claims}")

    role_mappings_raw = contract.get("role_mappings")
    require(isinstance(role_mappings_raw, dict), "role_mappings missing")
    role_mappings = cast(dict[str, Any], role_mappings_raw)
    missing_roles = sorted(REQUIRED_IDENTITY_ROLES - set(role_mappings))
    require(not missing_roles, f"identity roles missing: {missing_roles}")
    mapped_scopes: set[str] = set()
    for role_id in REQUIRED_IDENTITY_ROLES:
        role_raw = role_mappings.get(role_id)
        require(isinstance(role_raw, dict), f"{role_id} mapping must be a mapping")
        role = cast(dict[str, Any], role_raw)
        scopes_raw = role.get("scopes")
        require(
            isinstance(scopes_raw, list) and bool(scopes_raw),
            f"{role_id} scopes missing",
        )
        scopes_list = cast(list[Any], scopes_raw)
        scopes = {str(scope) for scope in scopes_list}
        unknown_scopes = sorted(scopes - REQUIRED_ROUTE_SCOPES)
        require(not unknown_scopes, f"{role_id} has unknown scopes: {unknown_scopes}")
        mapped_scopes.update(scopes)
    missing_scopes = sorted(REQUIRED_ROUTE_SCOPES - mapped_scopes)
    require(not missing_scopes, f"route scopes missing from roles: {missing_scopes}")

    audit_raw = contract.get("audit_requirements")
    require(isinstance(audit_raw, list) and bool(audit_raw), "audit_requirements missing")
    audit_requirements = cast(list[Any], audit_raw)
    missing_audit = sorted(REQUIRED_IDENTITY_AUDIT_REQUIREMENTS - set(audit_requirements))
    require(not missing_audit, f"identity audit requirements missing: {missing_audit}")

    migrations_raw = contract.get("migration_requirements")
    require(
        isinstance(migrations_raw, list) and bool(migrations_raw),
        "migration_requirements missing",
    )
    migration_requirements = cast(list[Any], migrations_raw)
    missing_migrations = sorted(REQUIRED_IDENTITY_MIGRATIONS - set(migration_requirements))
    require(
        not missing_migrations,
        f"identity migration requirements missing: {missing_migrations}",
    )

    limits_raw = contract.get("limits")
    require(isinstance(limits_raw, dict), "identity RBAC limits missing")
    limits = cast(dict[str, Any], limits_raw)
    require(limits.get("validate_only_catalog") is True, "identity contract must be validate-only")
    require(
        limits.get("provisions_identity_provider") is False,
        "identity contract must not provision identity providers",
    )
    require(
        limits.get("creates_user_account_tables") is False,
        "identity contract must not create user account tables",
    )
    require(limits.get("implements_oauth_oidc") is False, "identity contract must not implement OIDC")
    require(limits.get("claims_production_rbac") is False, "identity contract must not claim RBAC")


def validate_api_key_auth() -> None:
    api_auth = read_text("backend/app/api/api_key_auth.py")
    auth_audit = read_text("backend/app/api/auth_audit.py")
    main = read_text("backend/app/main.py")
    secret_specs = read_text("backend/app/api/secret_specs.py")
    api_tests = read_text("backend/tests/api/test_api_key_auth.py")
    settings = read_text("backend/app/core/config.py")

    require_phrases(
        api_auth,
        (
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
        ),
        "api key auth",
    )
    require_phrases(
        auth_audit,
        (
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
        ),
        "api key audit module",
    )
    require_phrases(
        main,
        (
            "SqlAlchemyApiKeyAuthAuditLog",
            "get_session_factory",
            "_build_api_key_audit_log",
            "use_db_services=resolved_use_db_services",
            "api_key_audit_log",
        ),
        "app wiring",
    )
    require_phrases(
        secret_specs,
        (
            "SHA256_SECRET_PREFIX",
            "normalize_secret_spec",
            "matches_any_secret_spec",
            "matches_secret_spec",
            "compare_digest",
            "sha256(",
        ),
        "secret spec helper",
    )
    require_phrases(
        settings,
        (
            "require_api_key: bool = Field(default=False",
            "api_keys: str = Field(",
            "api_key_specs: str = Field(",
            "API_KEY_SPECS",
            "API_KEY_STATUS_ACTIVE",
            "API_KEY_STATUS_RETIRED",
            "LOCAL_APP_ENVS",
            "validate_secret_hygiene",
            "API_KEYS is local-only",
            "API_KEY_SPECS is required when REQUIRE_API_KEY=true outside",
            "Non-local APP_ENV API_KEY_SPECS secrets must use",
            "parsed_api_key_specs",
            "Duplicate API_KEYS entry",
            "Duplicate API_KEY_SPECS id",
            "Duplicate API_KEY_SPECS secret",
            "normalize_secret_spec",
        ),
        "settings",
    )
    require_phrases(
        api_tests,
        (
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
            "test_non_local_settings_require_hashed_api_key_specs",
            "test_non_local_settings_reject_raw_or_missing_api_key_specs",
            "test_non_local_secret_hygiene_allows_no_api_key_config_when_auth_disabled",
            "test_non_local_secret_hygiene_rejects_legacy_api_key_config_when_auth_disabled",
        ),
        "api key tests",
    )


def validate_ui_api_key_bridge() -> None:
    api_auth = read_text("backend/app/api/api_key_auth.py")
    ui = read_text("backend/app/api/ui.py")
    ui_auth = read_text("backend/app/api/ui_auth.py")
    ui_lineage = read_text("backend/app/api/ui_lineage.py")
    ui_operations = read_text("backend/app/api/ui_operations.py")
    ui_review = read_text("backend/app/api/ui_review.py")
    ui_shared = read_text("backend/app/api/ui_shared.py")
    main = read_text("backend/app/main.py")
    settings = read_text("backend/app/core/config.py")
    ui_tests = read_text("backend/tests/api/test_ui_api_key_auth.py")
    runbook = read_text("docs/runbooks/access_control.md")
    mvp_operator = read_text("docs/runbooks/mvp_operator.md")
    design = read_text("DESIGN.md")
    manifest = read_text("MANIFEST.md")
    env_example = read_text(".env.example")

    require_phrases(
        api_auth,
        (
            'UI_API_KEY_COOKIE = "land_dd_ui_api_key"',
            "UI_API_KEY_COOKIE_MAX_AGE_SECONDS",
            'PUBLIC_UI_AUTH_PATHS = frozenset({"/ui/auth"})',
            "create_ui_api_key_cookie_token",
            "verify_ui_api_key_cookie_token",
            "UI_API_KEY_COOKIE_TOKEN_PREFIX",
            "UI_CSRF_FORM_FIELD",
            "UI_CSRF_TOKEN_PREFIX",
            "create_ui_csrf_token",
            "verify_ui_csrf_token",
            "ui_cookie_signing_secret",
            "ui_cookie_secure",
            "_sign_ui_cookie_token(signed_part, config)",
            "request.state.api_key_auth_source",
            "_is_ui_path",
            "ui_cookie",
            "_ui_login_redirect(request)",
            "next=",
            "_ui_next_path",
            '"API key is required"',
            '"API key is invalid"',
        ),
        "ui api key bridge middleware",
    )
    require_phrases(
        ui_auth,
        (
            'APIRouter(prefix="/ui/auth"',
            "_safe_next_path",
            'path="/ui"',
            "max_age=UI_API_KEY_COOKIE_MAX_AGE_SECONDS",
            "httponly=True",
            'samesite="lax"',
            "secure=config.ui_cookie_secure",
            "escape(",
            'type="password"',
            'name="next"',
            "urlsplit",
            "scheme",
            "netloc",
            "_match_api_key",
            "_record_api_key_audit_event",
            "ApiKeyAuthAuditOutcome",
            "csrf_form_field",
            "require_ui_csrf",
            '@router.post("/logout")',
        ),
        "ui api key bridge route",
    )
    for label, text in (
        ("ui home routes", ui),
        ("ui operations routes", ui_operations),
        ("ui review routes", ui_review),
    ):
        require_phrases(
            text,
            (
                "csrf_form_field",
                "require_ui_csrf",
                "csrf_token",
            ),
            label,
        )
    require_phrases(
        ui_shared,
        (
            "def csrf_form_field",
            "def require_ui_csrf",
            "def ui_csrf_required",
            "verify_ui_csrf_token",
            "api_key_auth_source",
        ),
        "ui csrf helpers",
    )
    require_phrases(
        ui_lineage,
        (
            'APIRouter(prefix="/ui/report-runs"',
            '@router.get("/{report_run_id}/lineage"',
            "page_head(",
            "error_page(",
            "build_lineage_response",
        ),
        "ui lineage route",
    )
    require_phrases(
        main,
        (
            "_ui_auth_cookie_secure",
            "_ui_cookie_signing_secret",
            "_is_local_app_env",
            "settings.is_local_app_env()",
            "ui_cookie_signing_secret=_ui_cookie_signing_secret(resolved)",
            "ui_cookie_secure=_ui_auth_cookie_secure(resolved)",
            "UI_AUTH_COOKIE_SECRET is required when REQUIRE_API_KEY is true",
            "outside local/dev/development/test APP_ENV values",
            "secrets.token_urlsafe(48)",
        ),
        "ui api key bridge app wiring",
    )
    require_phrases(
        settings,
        (
            "ui_auth_cookie_secret",
            'alias="UI_AUTH_COOKIE_SECRET"',
            "Required when REQUIRE_API_KEY is true outside local/dev/development/test",
            "per-process local fallback",
            "ui_auth_cookie_secure",
            'alias="UI_AUTH_COOKIE_SECURE"',
        ),
        "ui api key bridge settings",
    )
    require_phrases(
        design,
        (
            "Canonical planning/design ownership: this repo-root `DESIGN.md`",
            "server-rendered private operator UI under `/ui/*`",
            "When `REQUIRE_API_KEY=true`, JSON/API routes still require `X-API-Key`",
            "/ui/auth",
            "signed, expiring, HttpOnly cookie scoped to `/ui`",
            "Non-local API-key-locked app environments require `UI_AUTH_COOKIE_SECRET`",
            "local/dev/development/test environments may use a per-process fallback",
            "API reviewer tokens remain header-only and separate from API keys",
            "browser reviewer actions can use `/ui/auth/reviewer`",
            "signed, expiring, HttpOnly reviewer session cookie scoped to `/ui`",
        ),
        "ui api key bridge design source of truth",
    )
    require_phrases(
        manifest,
        (
            "Use this as the repo/file routing index. "
            "It is intentionally not an exhaustive file listing.",
            "Operator UI design",
            "`DESIGN.md`",
            "Active private operator console contract",
            "Access control",
            "`docs/runbooks/mvp_operator.md`",
            "UI API-key cookie bridge",
        ),
        "repo manifest ui access-control routing",
    )
    require_phrases(
        ui_tests,
        (
            "test_ui_auth_form_is_public_and_does_not_expose_configured_secret",
            "test_ui_auth_cookie_enables_ui_when_api_key_required",
            "test_tampered_ui_auth_cookie_redirects_to_login",
            "test_ui_auth_cookie_is_rejected_when_active_api_key_config_changes",
            "test_sha256_api_key_digest_cannot_forge_ui_auth_cookie",
            "test_configured_ui_auth_cookie_secret_allows_restart_with_same_api_key",
            "test_non_local_app_env_sets_secure_ui_auth_cookie",
            "test_non_local_api_key_auth_requires_configured_ui_auth_cookie_secret",
            'pytest.raises(ValueError, match="UI_AUTH_COOKIE_SECRET")',
            "test_expired_ui_auth_cookie_redirects_to_login",
            "test_invalid_ui_auth_login_records_audit_event_without_secret",
            "test_api_routes_reject_forced_ui_auth_cookie_header_without_header_key",
            "test_ui_auth_redirect_preserves_safe_next_path_for_unauthenticated_ui_get",
            "test_successful_ui_auth_redirects_to_safe_next_path",
            "test_successful_ui_auth_falls_back_when_next_path_is_unsafe",
            "test_ui_auth_accepts_active_api_key_spec",
            "test_ui_auth_cookie_records_api_key_spec_id_and_ui_cookie_source",
            "test_ui_cookie_auth_forms_include_csrf_token",
            "test_ui_cookie_auth_post_requires_valid_csrf_token",
            "test_ui_header_auth_post_does_not_require_csrf_token",
            "test_ui_logout_requires_post_with_csrf_token",
            "test_existing_api_key_header_still_enables_areas_route",
            '"Max-Age=" in set_cookie',
            '"wrong-key" not in response.text',
            '"production-key" not in response.text',
        ),
        "ui api key bridge tests",
    )
    require_phrases(
        runbook,
        (
            "UI API-key cookie bridge",
            "/ui/auth",
            "signed expiring path-scoped HttpOnly SameSite cookie",
            "UI_AUTH_COOKIE_SECRET",
            "UI_AUTH_COOKIE_SECURE",
            "separate UI-cookie signing material",
            "requires `UI_AUTH_COOKIE_SECRET`",
            "non-local API-key-locked app environments",
            "local/dev/development/test app environments",
            "sets `Secure` automatically",
            "CSRF token",
            "logout uses a CSRF-protected POST",
            "without storing the submitted API key",
            "/areas` rejects cookie-only API access",
            "safe `/ui/*` return path",
            "No full user auth/RBAC exists yet.",
            "No OAuth/OIDC",
            "No user-account persistence",
            "No hosted secret manager integration",
        ),
        "ui api key bridge docs",
    )
    require_phrases(
        mvp_operator,
        (
            "When `REQUIRE_API_KEY=true` is set, JSON/API routes require `X-API-Key`",
            "`/ui/auth` is public",
            "signed expiring HttpOnly SameSite cookie scoped to `/ui`",
            "`UI_AUTH_COOKIE_SECRET` to a high-entropy value in shared environments",
            "non-local `APP_ENV` values fail startup if it is blank",
            "config uses a per-process signing secret",
            "mutation forms include a signed CSRF token",
            "Sign-out is",
            "CSRF-protected POST from",
            "JSON/API paths still require `X-API-Key`",
            "not full user auth/RBAC",
        ),
        "mvp operator ui api key bridge docs",
    )
    require_phrases(
        env_example,
        (
            "UI_AUTH_COOKIE_SECRET=",
            "Blank is local/dev/development/test only",
            "UI_AUTH_COOKIE_SECURE=false",
        ),
        "ui api key bridge environment example",
    )


def validate_reviewer_auth() -> None:
    reviewer_auth = read_text("backend/app/api/reviewer_auth.py")
    reviewer_tests = read_text("backend/tests/api/test_reviewer_auth.py")
    settings = read_text("backend/app/core/config.py")

    require_phrases(
        reviewer_auth,
        (
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
        ),
        "reviewer auth",
    )
    require_phrases(
        settings,
        (
            "reviewer_accounts: str = Field(",
            "reviewer_account_scopes: str = Field(",
            "REVIEWER_ACCOUNT_SCOPES",
            "Defaults to a local fixture account; override in production.",
            "The default fixture reviewer account is local-only.",
            "Non-local APP_ENV REVIEWER_ACCOUNTS tokens must use",
            "Non-local APP_ENV values require explicit REVIEWER_ACCOUNT_SCOPES",
            "parsed_reviewer_accounts",
            "parsed_reviewer_account_scopes",
            "Duplicate REVIEWER_ACCOUNTS",
            "Duplicate REVIEWER_ACCOUNT_SCOPES",
            "normalize_secret_spec",
        ),
        "settings",
    )
    require_phrases(
        reviewer_tests,
        (
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
            "test_non_local_settings_require_hashed_reviewer_accounts_with_scopes",
            "test_non_local_settings_reject_fixture_or_raw_reviewer_accounts",
        ),
        "reviewer auth tests",
    )


def validate_operator_routes() -> None:
    for route_file in (
        "connectors.py",
        "operator_cases.py",
        "operations.py",
        "reports.py",
        "sources.py",
    ):
        text = read_text(f"backend/app/api/{route_file}")
        require("ReviewerPrincipal" in text, f"{route_file} must depend on ReviewerPrincipal")
        require("get_reviewer_principal" in text, f"{route_file} must expose reviewer dependency")
        require("require_reviewer_scope" in text, f"{route_file} must enforce reviewer scopes")

    connectors = read_text("backend/app/api/connectors.py")
    live_connectors = read_text("backend/app/api/live_connectors.py")
    operator_cases = read_text("backend/app/api/operator_cases.py")
    operations = read_text("backend/app/api/operations.py")
    reports = read_text("backend/app/api/reports.py")
    sources = read_text("backend/app/api/sources.py")
    require(
        "reviewer_id=principal.reviewer_id" in connectors,
        "connector review actions must use authenticated reviewer id",
    )
    require_phrases(
        connectors,
        (
            "REVIEWER_SCOPE_CONNECTOR_RUN",
            "REVIEWER_SCOPE_CONNECTOR_REVIEW",
            "REVIEWER_SCOPE_OPERATIONS_READ",
            "REVIEWER_SCOPE_REPORT_RUN",
        ),
        "connectors route",
    )
    require_phrases(
        connectors,
        (
            "def _get_live_connector_area_or_422(",
            "auth: RequestAuthContext",
            "area.workspace_id != auth.workspace_id",
            'return area.model_copy(update={"created_by": auth.user_id})',
            "def _get_scoped_review_status_or_404(",
            "workspace_id=auth.workspace_id",
        ),
        "workspace-scoped connector reads",
    )
    for function_name in (
        "query_blm_mlrs_bbox",
        "query_brunswick_parcels_bbox",
        "query_buncombe_parcels_bbox",
        "query_census_tiger_bbox",
        "query_chatham_parcels_bbox",
        "query_epa_echo_bbox",
        "query_fcc_broadband_bbox",
        "query_fema_nfhl_bbox",
        "query_nc_geologic_map_bbox",
        "query_nwi_bbox",
        "query_noaa_climate_bbox",
        "query_osm_road_access_bbox",
        "query_ssurgo_bbox",
        "query_usgs_mrds_bbox",
        "query_usgs_tnm_bbox",
        "query_usgs_water_monitoring_bbox",
    ):
        block = function_block(connectors, function_name)
        require_phrases(
            block,
            (
                "auth: AuthDep",
                "_get_live_connector_area_or_422(",
                "auth=auth",
            ),
            f"{function_name} workspace identity",
        )
    for function_name in (
        "get_connector_run_review_status",
        "get_connector_review_queue_item",
    ):
        block = function_block(connectors, function_name)
        require_phrases(
            block,
            (
                "auth: AuthDep",
                "auth, ingest_run_id",
            ),
            f"{function_name} workspace identity",
        )
    require_phrases(
        live_connectors,
        (
            "def _enqueue_review_status_for_area(",
            "workspace_id=area.workspace_id",
            "requested_by=area.created_by",
        ),
        "live connector review queue scope",
    )
    require(
        "REVIEWER_SCOPE_OPERATIONS_READ" in operations,
        "operations route must require operations read scope",
    )
    require_phrases(
        operator_cases,
        (
            "AuthDep = Annotated[RequestAuthContext, Depends(get_request_auth_context)]",
            "REVIEWER_SCOPE_REPORT_RUN",
            "require_reviewer_scope(principal, REVIEWER_SCOPE_REPORT_RUN)",
            "body reviewer_id must match the authenticated reviewer",
            "reviewer_id=reviewer_id",
            "workspace_id=auth.workspace_id",
            "requested_by=auth.user_id",
        ),
        "operator case report route auth",
    )
    require(
        "REVIEWER_SCOPE_REPORT_RETRY" in reports,
        "reports route must require report retry scope",
    )
    require(
        "REVIEWER_SCOPE_SOURCE_MANAGE" in sources,
        "sources route must require source manage scope",
    )
    tests = "\n".join(
        read_text(f"backend/tests/api/{test_file}")
        for test_file in (
            "test_connector_review_actions.py",
            "test_operations.py",
            "test_async_report_runs.py",
            "test_fema_nfhl_connector_api.py",
            "test_api_scaffold.py",
            "test_connector_review_queue_api.py",
            "test_connector_review_status.py",
            "test_operator_cases_api.py",
            "test_usgs_tnm_connector_api.py",
        )
    )
    require_phrases(
        tests,
        (
            "test_request_fixture_fix_rejects_reviewer_without_review_scope",
            "test_connector_review_action_rejects_reviewer_without_review_scope",
            "test_connector_review_action_requires_reviewer_credentials",
            "test_queue_health_rejects_reviewer_without_operations_read_scope",
            "test_retry_report_run_rejects_reviewer_without_retry_scope",
            "test_fema_nfhl_schedule_bbox_rejects_reviewer_without_connector_run_scope",
            "test_api_scaffold_source_create_requires_source_manage_scope",
            "test_connector_review_status_endpoint_requires_identity",
            "test_connector_review_status_endpoint_hides_other_workspace",
            "test_connector_review_queue_endpoint_requires_identity",
            "test_connector_review_queue_endpoint_hides_other_workspace",
            "test_operator_case_report_create_rejects_missing_workspace_identity",
            "test_operator_case_report_create_rejects_missing_reviewer_auth",
            "test_operator_case_report_create_rejects_body_reviewer_mismatch",
            "test_usgs_tnm_schedule_bbox_requires_workspace_identity",
            "test_usgs_tnm_schedule_bbox_hides_area_from_other_workspace",
        ),
        "scoped route tests",
    )
    for function_name in (
        "approve_connector_review_queue_item_compat",
        "reject_connector_review_queue_item_compat",
        "requeue_connector_review_queue_item_compat",
        "cancel_connector_review_queue_item_compat",
    ):
        block = function_block(connectors, function_name)
        require_phrases(
            block,
            (
                "principal: Annotated[ReviewerPrincipal, Depends(get_reviewer_principal)]",
                "require_reviewer_scope(principal, REVIEWER_SCOPE_CONNECTOR_REVIEW)",
                "_compat_reviewer_id(principal, request.reviewer_id)",
            ),
            f"{function_name} reviewer scope",
        )

    live_smoke = read_text("scripts/run_live_smoke.py")
    demo_mvp = read_text("scripts/demo_mvp.py")
    require_phrases(
        live_smoke,
        (
            "X-Reviewer-Id",
            "X-Reviewer-Token",
            '_post(base_url, "/sources", body, _reviewer_headers())',
        ),
        "live smoke source seed auth",
    )
    require_phrases(
        demo_mvp,
        (
            "X-Reviewer-Id",
            "X-Reviewer-Token",
            'client.request("POST", "/sources", payload, headers=reviewer_headers)',
        ),
        "demo MVP source seed auth",
    )


def validate_ci_and_runbook() -> None:
    ci_text = read_text(".github/workflows/ci.yml")
    ci = yaml.safe_load(ci_text)
    require(isinstance(ci, dict), "ci workflow must be a mapping")
    jobs = ci.get("jobs")
    require(isinstance(jobs, dict), "ci workflow jobs missing")
    job = jobs.get("access-control")
    require(isinstance(job, dict), "ci workflow missing access-control job")
    permissions = job.get("permissions")
    require(isinstance(permissions, dict), "access-control permissions missing")
    require(
        permissions.get("contents") == "read",
        "access-control must use read-only contents permission",
    )
    text = step_text(job, "access-control")
    require("actions/checkout@v6" in text, "access-control job must checkout repo")
    require("actions/setup-python@v6" in text, "access-control job must setup Python")
    require("python-version: '3.12'" in ci_text, "access-control job must use Python 3.12")
    require("python -m pip install PyYAML" in text, "access-control job must install PyYAML")
    require(
        "./scripts/run_access_control_check.sh" in text,
        "access-control job must run POSIX proof",
    )

    runbook = read_text("docs/runbooks/access_control.md")
    require_phrases(
        runbook,
        (
            "run_access_control_check.ps1",
            "scripts/access_control_check.py",
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
            "source:manage",
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
            "reject `API_KEYS` and raw `API_KEY_SPECS` secrets",
            "rejects fixture reviewer defaults and raw token specs in non-local",
            "secret management handoff contract",
            "REPORT_IDENTITY_TOKEN_SECRET",
            "DATABASE_URL",
            "hosted secret manager remains blocked",
            "no plaintext secret values are committed",
            "identity_rbac_contract",
            "identity/RBAC design handoff",
            "subject, email, display_name, workspace_id, user_id, and groups_or_roles",
            "platform_admin, workspace_admin, reviewer, operator, and read_only",
            "hosted identity provider remains blocked",
            "no OAuth/OIDC implementation",
            "no production RBAC claim",
        ),
        "access-control runbook",
    )
    env_example = read_text(".env.example")
    compose = read_text("docker-compose.yml")
    mvp_operator = read_text("docs/runbooks/mvp_operator.md")
    for text_name, text_payload in ((".env.example", env_example), ("docker-compose.yml", compose)):
        require(
            "REVIEWER_ACCOUNT_SCOPES" in text_payload,
            f"{text_name} missing reviewer scope env",
        )
        require("API_KEY_SPECS" in text_payload, f"{text_name} missing API key lifecycle env")
        require(
            "UI_AUTH_COOKIE_SECRET" in text_payload,
            f"{text_name} missing UI cookie secret env",
        )
        require(
            "REPORT_IDENTITY_TOKEN_SECRET" in text_payload,
            f"{text_name} missing report identity secret env",
        )
    require("sha256:<64-hex>" in env_example, ".env.example missing hashed secret guidance")
    require("REPORT_AUTH_MODE=trusted_headers" in env_example, ".env.example missing report auth mode")
    require("API_KEYS is local/dev/development/test only" in env_example, ".env.example missing local-only API_KEYS guidance")
    require("non-local APP_ENV" in compose, "docker-compose.yml missing non-local secret guidance")
    require("REPORT_AUTH_MODE" in compose, "docker-compose.yml missing report auth mode")
    require("report:approve" in compose, "docker-compose.yml fixture reviewer scopes missing report approval")
    require_phrases(
        mvp_operator,
        (
            "identity_rbac_contract",
            "maps future roles to current route scopes",
            "does not add user accounts, OAuth/OIDC, full user RBAC",
            "design handoff only",
        ),
        "mvp operator identity RBAC docs",
    )


def main() -> int:
    validate_required_files()
    validate_catalog()
    validate_api_key_auth()
    validate_ui_api_key_bridge()
    validate_reviewer_auth()
    validate_operator_routes()
    validate_ci_and_runbook()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
