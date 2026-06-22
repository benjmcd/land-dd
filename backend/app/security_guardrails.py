from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

EXPECTED_SCHEMA = "access_control_v1"
EXPECTED_OPERATOR_RUNBOOK = "docs/runbooks/access_control.md"
REQUIRED_CONTROL_IDS = {
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
REQUIRED_ROUTE_SCOPES = {
    "connector:run",
    "connector:review",
    "operations:read",
    "report:retry",
    "report:run",
    "report:approve",
    "source:manage",
}
REQUIRED_ROLE_IDS = {
    "operator",
    "platform_admin",
    "read_only",
    "reviewer",
    "workspace_admin",
}
REQUIRED_ROUTE_SCOPE_MAPPING_IDS = {
    "approved_connector_report_runs",
    "connector_review_decisions",
    "fixture_connector_runs",
    "live_connector_job_reads",
    "live_connector_runs",
    "operations_api_reads",
    "report_approval",
    "report_retry",
    "selected_county_report_runs",
    "source_registry_mutation",
    "ui_connector_resume_report",
    "ui_connector_review_decisions",
    "ui_operations_reads",
    "ui_report_approval",
    "ui_report_retry",
    "ui_selected_county_report_runs",
}


class SecurityGuardrailsError(RuntimeError):
    """Raised when security guardrail artifacts cannot be trusted for UI rendering."""


@dataclass(frozen=True)
class SecurityControl:
    control_id: str
    status: str
    validation: str
    authority: tuple[str, ...]


@dataclass(frozen=True)
class ProductionBlocker:
    blocker_id: str
    status: str
    authority: str


@dataclass(frozen=True)
class SecurityGuardrailsReadiness:
    schema_version: str
    operator_runbook: str
    controls: tuple[SecurityControl, ...]
    production_blockers: tuple[ProductionBlocker, ...]
    secret_management_status: str
    hosted_secret_manager_status: str
    secret_runtime_refs: tuple[str, ...]
    secret_handoff_requirements: tuple[str, ...]
    secret_limits: dict[str, bool]
    identity_contract_status: str
    hosted_identity_provider_status: str
    user_account_persistence_status: str
    full_role_policy_status: str
    identity_role_ids: tuple[str, ...]
    route_scopes: tuple[str, ...]
    identity_limits: dict[str, bool]

    @property
    def control_ids(self) -> tuple[str, ...]:
        return tuple(control.control_id for control in self.controls)

    @property
    def production_blocker_ids(self) -> tuple[str, ...]:
        return tuple(blocker.blocker_id for blocker in self.production_blockers)


def repo_root_from_app() -> Path:
    return Path(__file__).resolve().parents[2]


def load_security_guardrails(
    repo_root: Path | None = None,
) -> SecurityGuardrailsReadiness:
    root = repo_root or repo_root_from_app()
    catalog = _read_yaml(root / "config" / "access_control.yaml")
    return parse_security_guardrails(catalog, root=root)


def parse_security_guardrails(
    catalog: dict[str, Any],
    *,
    root: Path,
) -> SecurityGuardrailsReadiness:
    schema_version = _require_exact_text(
        catalog.get("schema_version"),
        EXPECTED_SCHEMA,
        "access-control schema",
    )
    operator_runbook = _require_exact_text(
        catalog.get("operator_runbook"),
        EXPECTED_OPERATOR_RUNBOOK,
        "operator runbook",
    )
    _require_existing(root, operator_runbook)

    controls = _parse_controls(catalog.get("current_controls"), root)
    control_ids = {control.control_id for control in controls}
    if not REQUIRED_CONTROL_IDS.issubset(control_ids):
        raise SecurityGuardrailsError("current control set missing required controls")

    blockers = _parse_blockers(catalog.get("production_blockers"), root)
    if {blocker.blocker_id for blocker in blockers} != REQUIRED_BLOCKERS:
        raise SecurityGuardrailsError("production blocker set mismatch")

    secret_contract = _require_mapping(
        catalog.get("secret_management_contract"),
        "secret management contract missing",
    )
    identity_contract = _require_mapping(
        catalog.get("identity_rbac_contract"),
        "identity/RBAC contract missing",
    )

    secret_runtime_refs = _runtime_ref_ids(secret_contract.get("required_runtime_refs"))
    if set(secret_runtime_refs) != REQUIRED_SECRET_REFS:
        raise SecurityGuardrailsError("secret runtime reference set mismatch")

    secret_limits = _bool_mapping(secret_contract.get("limits"), "secret limits missing")
    _require_false_limits(
        secret_limits,
        (
            "writes_secrets",
            "provisions_hosted_secret_manager",
            "permits_committed_plaintext_secrets",
        ),
        "secret",
    )

    identity_limits = _bool_mapping(identity_contract.get("limits"), "identity limits missing")
    _require_false_limits(
        identity_limits,
        (
            "provisions_identity_provider",
            "creates_user_account_tables",
            "implements_oauth_oidc",
            "claims_production_rbac",
        ),
        "identity",
    )

    route_scopes = _route_scopes(identity_contract.get("route_scope_mappings"))
    if set(route_scopes) != REQUIRED_ROUTE_SCOPES:
        raise SecurityGuardrailsError("identity route-scope set mismatch")

    for authority in _require_text_tuple(
        secret_contract.get("authority"),
        "secret contract authority missing",
    ):
        _require_existing(root, authority)
    for authority in _require_text_tuple(
        identity_contract.get("authority"),
        "identity contract authority missing",
    ):
        _require_existing(root, authority)

    role_mappings = _require_mapping(
        identity_contract.get("role_mappings"),
        "identity role mappings missing",
    )

    # SG-1: validate required role ids and each role's scope set
    missing_roles = REQUIRED_ROLE_IDS - set(str(k) for k in role_mappings)
    if missing_roles:
        raise SecurityGuardrailsError(
            f"identity role mappings missing required roles: {sorted(missing_roles)}"
        )
    for role_id in REQUIRED_ROLE_IDS:
        role_entry = _require_mapping(
            role_mappings.get(role_id),
            f"identity role mapping for {role_id} must be a mapping",
        )
        scopes_raw = role_entry.get("scopes")
        if not isinstance(scopes_raw, list) or not scopes_raw:
            raise SecurityGuardrailsError(
                f"identity role {role_id} scopes missing or empty"
            )
        role_scopes = {str(s) for s in scopes_raw}
        unknown = role_scopes - REQUIRED_ROUTE_SCOPES
        if unknown:
            raise SecurityGuardrailsError(
                f"identity role {role_id} has unknown scopes: {sorted(unknown)}"
            )

    # SG-3: validate required mapping ids at the id level (not just route_scope coverage)
    route_scope_mappings_raw = _require_list(
        identity_contract.get("route_scope_mappings"),
        "route scope mappings missing",
    )
    actual_mapping_ids = set()
    for item in route_scope_mappings_raw:
        payload = _require_mapping(item, "route scope mapping must be a mapping")
        mapping_id = _require_text(payload.get("id"), "route scope mapping id missing")
        actual_mapping_ids.add(mapping_id)
    missing_mapping_ids = REQUIRED_ROUTE_SCOPE_MAPPING_IDS - actual_mapping_ids
    if missing_mapping_ids:
        raise SecurityGuardrailsError(
            f"route scope mapping ids missing: {sorted(missing_mapping_ids)}"
        )

    # SG-4: validate_only_catalog must be True in both contracts
    if secret_limits.get("validate_only_catalog") is not True:
        raise SecurityGuardrailsError(
            "secret_management_contract.limits.validate_only_catalog must be True"
        )
    if identity_limits.get("validate_only_catalog") is not True:
        raise SecurityGuardrailsError(
            "identity_rbac_contract.limits.validate_only_catalog must be True"
        )

    return SecurityGuardrailsReadiness(
        schema_version=schema_version,
        operator_runbook=operator_runbook,
        controls=controls,
        production_blockers=blockers,
        secret_management_status=_require_exact_text(
            secret_contract.get("status"),
            "repo_local_handoff_contract",
            "secret management status",
        ),
        hosted_secret_manager_status=_require_exact_text(
            secret_contract.get("hosted_secret_manager_status"),
            "blocked",
            "hosted secret-manager status",
        ),
        secret_runtime_refs=secret_runtime_refs,
        secret_handoff_requirements=_require_text_tuple(
            secret_contract.get("handoff_requirements"),
            "secret handoff requirements missing",
        ),
        secret_limits=secret_limits,
        identity_contract_status=_require_exact_text(
            identity_contract.get("status"),
            "repo_local_design_contract",
            "identity contract status",
        ),
        hosted_identity_provider_status=_require_exact_text(
            identity_contract.get("hosted_identity_provider_status"),
            "blocked",
            "hosted identity provider status",
        ),
        user_account_persistence_status=_require_exact_text(
            identity_contract.get("user_account_persistence_status"),
            "blocked",
            "user account persistence status",
        ),
        full_role_policy_status=_require_exact_text(
            identity_contract.get("full_role_policy_status"),
            "blocked",
            "full role policy status",
        ),
        identity_role_ids=tuple(sorted(str(key) for key in role_mappings)),
        route_scopes=route_scopes,
        identity_limits=identity_limits,
    )


def _parse_controls(value: Any, root: Path) -> tuple[SecurityControl, ...]:
    controls = []
    for item in _require_list(value, "current controls missing"):
        payload = _require_mapping(item, "current control must be a mapping")
        control_id = _require_text(payload.get("id"), "current control id missing")
        authority = _require_text_tuple(payload.get("authority"), f"{control_id} authority missing")
        for path_text in authority:
            _require_existing(root, path_text)
        validation = _require_exact_text(
            payload.get("validation"),
            "scripts/run_access_control_check.ps1",
            f"{control_id} validation",
        )
        _require_existing(root, validation)
        controls.append(
            SecurityControl(
                control_id=control_id,
                status=_require_text(payload.get("status"), f"{control_id} status missing"),
                validation=validation,
                authority=authority,
            )
        )
    return tuple(sorted(controls, key=lambda control: control.control_id))


def _parse_blockers(value: Any, root: Path) -> tuple[ProductionBlocker, ...]:
    blockers = []
    for item in _require_list(value, "production blockers missing"):
        payload = _require_mapping(item, "production blocker must be a mapping")
        blocker_id = _require_text(payload.get("id"), "production blocker id missing")
        authority = _require_text(payload.get("authority"), f"{blocker_id} authority missing")
        _require_existing(root, authority)
        blockers.append(
            ProductionBlocker(
                blocker_id=blocker_id,
                status=_require_exact_text(
                    payload.get("status"),
                    "blocked",
                    f"{blocker_id} status",
                ),
                authority=authority,
            )
        )
    return tuple(sorted(blockers, key=lambda blocker: blocker.blocker_id))


def _runtime_ref_ids(value: Any) -> tuple[str, ...]:
    refs = []
    for item in _require_list(value, "runtime refs missing"):
        payload = _require_mapping(item, "runtime ref must be a mapping")
        ref_id = _require_text(payload.get("id"), "runtime ref id missing")
        # SG-2: each ref must carry non-empty required_when, format, rotation
        for field in ("required_when", "format", "rotation"):
            _require_text(
                payload.get(field),
                f"runtime ref {ref_id} missing or empty field: {field}",
            )
        refs.append(ref_id)
    return tuple(sorted(refs))


def _route_scopes(value: Any) -> tuple[str, ...]:
    scopes = []
    for item in _require_list(value, "route scope mappings missing"):
        payload = _require_mapping(item, "route scope mapping must be a mapping")
        scopes.append(_require_text(payload.get("route_scope"), "route scope missing"))
    return tuple(sorted(set(scopes)))


def _read_yaml(path: Path) -> dict[str, Any]:
    label = _catalog_label(path)
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise SecurityGuardrailsError(f"cannot read {label}") from exc
    return _require_mapping(payload, f"{label} must be a mapping")


def _require_existing(root: Path, path_text: str) -> None:
    path = _resolved_repo_path(root, path_text)
    if not path.exists():
        raise SecurityGuardrailsError(
            f"referenced security guardrail artifact missing: {path_text}"
        )


def _resolved_repo_path(root: Path, path_text: str) -> Path:
    if not path_text:
        raise SecurityGuardrailsError("empty path reference")
    candidate = Path(_normalize_path(path_text))
    if candidate.is_absolute():
        raise SecurityGuardrailsError(f"path must be repo-relative: {path_text}")
    root_resolved = root.resolve()
    resolved = (root_resolved / candidate).resolve()
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise SecurityGuardrailsError(f"path escapes repo root: {path_text}") from exc
    return resolved


def _require_mapping(value: Any, message: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SecurityGuardrailsError(message)
    return value


def _require_list(value: Any, message: str) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise SecurityGuardrailsError(message)
    return value


def _require_text(value: Any, message: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SecurityGuardrailsError(message)
    return value.strip()


def _require_exact_text(value: Any, expected: str, label: str) -> str:
    text = _require_text(value, f"{label} missing")
    if text != expected:
        raise SecurityGuardrailsError(f"{label} must be {expected}")
    return text


def _require_text_tuple(value: Any, message: str) -> tuple[str, ...]:
    values = _require_list(value, message)
    text_values = tuple(_require_text(item, message) for item in values)
    if not text_values:
        raise SecurityGuardrailsError(message)
    return text_values


def _bool_mapping(value: Any, message: str) -> dict[str, bool]:
    raw = _require_mapping(value, message)
    if not all(isinstance(key, str) and isinstance(val, bool) for key, val in raw.items()):
        raise SecurityGuardrailsError(message)
    return {str(key): bool(val) for key, val in raw.items()}


def _require_false_limits(
    limits: dict[str, bool],
    required_false_keys: tuple[str, ...],
    label: str,
) -> None:
    for key in required_false_keys:
        if limits.get(key) is not False:
            raise SecurityGuardrailsError(f"{label} limit must remain false: {key}")


def _normalize_path(path_text: str) -> str:
    return path_text.replace("\\", "/")


def _catalog_label(path: Path) -> str:
    parts = path.parts
    if len(parts) >= 2:
        return f"{parts[-2]}/{parts[-1]}"
    return path.name
