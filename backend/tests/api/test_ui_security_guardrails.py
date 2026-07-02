from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, cast

import pytest
import yaml
from fastapi.testclient import TestClient

from app.api import ui as ui_module
from app.main import create_app
from app.security_guardrails import (
    SecurityGuardrailsError,
    load_security_guardrails,
    parse_security_guardrails,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
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
REQUIRED_ROUTE_SCOPES = {
    "connector:run",
    "connector:review",
    "operations:read",
    "report:retry",
    "report:run",
    "report:approve",
    "source:manage",
}


def _catalog() -> dict[str, Any]:
    payload = yaml.safe_load(
        (REPO_ROOT / "config" / "access_control.yaml").read_text(encoding="utf-8")
    )
    assert isinstance(payload, dict)
    return cast(dict[str, Any], payload)


def test_security_guardrails_parser_composes_access_control_contract() -> None:
    readiness = load_security_guardrails(REPO_ROOT)

    assert readiness.schema_version == "access_control_v1"
    assert REQUIRED_CONTROL_IDS.issubset(set(readiness.control_ids))
    assert set(readiness.production_blocker_ids) == REQUIRED_BLOCKERS
    assert readiness.secret_management_status == "repo_local_handoff_contract"
    assert readiness.hosted_secret_manager_status == "blocked"
    assert readiness.identity_contract_status == "repo_local_design_contract"
    assert readiness.hosted_identity_provider_status == "blocked"
    assert readiness.user_account_persistence_status == "blocked"
    assert readiness.full_role_policy_status == "blocked"
    assert set(readiness.route_scopes) == REQUIRED_ROUTE_SCOPES
    assert readiness.secret_limits["writes_secrets"] is False
    assert readiness.secret_limits["provisions_hosted_secret_manager"] is False
    assert readiness.identity_limits["implements_oauth_oidc"] is False
    assert readiness.identity_limits["claims_production_rbac"] is False


def test_security_guardrails_parser_fails_closed_on_schema_drift() -> None:
    catalog = deepcopy(_catalog())
    catalog["schema_version"] = "access_control_v2"

    with pytest.raises(SecurityGuardrailsError, match="schema"):
        parse_security_guardrails(catalog, root=REPO_ROOT)


def test_security_guardrails_parser_fails_closed_on_missing_hosted_identity_blocker() -> None:
    catalog = deepcopy(_catalog())
    catalog["production_blockers"] = [
        blocker
        for blocker in cast(list[dict[str, Any]], catalog["production_blockers"])
        if blocker["id"] != "oauth_oidc_identity_provider"
    ]

    with pytest.raises(SecurityGuardrailsError, match="production blocker"):
        parse_security_guardrails(catalog, root=REPO_ROOT)


def test_security_guardrails_loader_uses_repo_relative_error_paths(
    tmp_path: Path,
) -> None:
    with pytest.raises(SecurityGuardrailsError) as exc_info:
        load_security_guardrails(tmp_path)

    message = str(exc_info.value)
    assert "config/access_control.yaml" in message
    assert str(tmp_path) not in message


def test_ui_security_guardrails_route_returns_503_when_loader_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _raise_loader() -> None:
        raise SecurityGuardrailsError(
            "LEAK_SENTINEL drift at /workspace/config/access_control.yaml field role_mappings"
        )

    monkeypatch.setattr(ui_module, "load_security_guardrails", _raise_loader)
    client = TestClient(create_app())

    response = client.get("/ui/security-guardrails")

    assert response.status_code == 503
    assert "Security guardrails could not be verified from repo-owned artifacts" in response.text
    # Fail-closed: raw exception detail (paths, catalog field names) must NOT leak to the page.
    assert "LEAK_SENTINEL" not in response.text
    assert "/workspace/" not in response.text
    assert "Traceback" not in response.text


def test_ui_security_guardrails_route_renders_catalog_and_boundaries() -> None:
    client = TestClient(create_app())

    response = client.get("/ui/security-guardrails")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert 'name="viewport"' in response.text
    assert "Security Guardrails" in response.text
    for text in (
        "access_control_v1",
        "api_key_middleware",
        "implemented_default_off",
        "ui_api_key_cookie_bridge",
        "implemented_private_beta_browser_bridge_default_local_unmounted",
        "protected_operator_routes",
        "full_user_auth_rbac",
        "oauth_oidc_identity_provider",
        "hosted_secret_manager",
        "repo_local_handoff_contract",
        "repo_local_design_contract",
        "API_KEY_SPECS",
        "REVIEWER_ACCOUNTS",
        "UI_AUTH_COOKIE_SECRET",
        "connector:run",
        "connector:review",
        "operations:read",
        "report:approve",
        "source:manage",
        "does not add OAuth/OIDC",
        "does not create user accounts",
        "does not claim hosted identity/RBAC",
        "does not approve DS-017",
        "does not write secrets",
        "does not provision a hosted secret manager",
    ):
        assert text in response.text


def test_current_ui_navigation_links_to_security_guardrails() -> None:
    client = TestClient(create_app())

    for path in ("/ui/", "/ui/raw-data", "/ui/deployment-readiness", "/ui/source-provenance"):
        response = client.get(path)

        assert response.status_code == 200
        assert 'href="/ui/security-guardrails"' in response.text
