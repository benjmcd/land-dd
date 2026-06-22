"""Tests for security_guardrails.py parser hardening (SG-1 through SG-4).

Each test drifts the valid catalog in one specific way and asserts that
parse_security_guardrails raises SecurityGuardrailsError (fail-closed).
Happy-path is covered by a single test that uses the real catalog.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from app.security_guardrails import (
    REQUIRED_ROLE_IDS,
    REQUIRED_ROUTE_SCOPE_MAPPING_IDS,
    REQUIRED_ROUTE_SCOPES,
    SecurityGuardrailsError,
    parse_security_guardrails,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = REPO_ROOT / "config" / "access_control.yaml"


def _load_catalog() -> dict[str, Any]:
    return yaml.safe_load(CATALOG_PATH.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Happy-path: real catalog parses without error
# ---------------------------------------------------------------------------


def test_security_guardrails_parse_happy_path() -> None:
    catalog = _load_catalog()
    result = parse_security_guardrails(catalog, root=REPO_ROOT)
    assert result.schema_version == "access_control_v1"
    assert set(result.identity_role_ids) == REQUIRED_ROLE_IDS
    assert set(result.route_scopes) == REQUIRED_ROUTE_SCOPES


# ---------------------------------------------------------------------------
# SG-1: required role ids + scope validation
# ---------------------------------------------------------------------------


def test_sg1_missing_role_raises() -> None:
    """Removing a required role id from role_mappings must raise SecurityGuardrailsError."""
    catalog = _load_catalog()
    role_mappings = catalog["identity_rbac_contract"]["role_mappings"]
    # Remove one required role
    removed = role_mappings.pop("operator")
    with pytest.raises(SecurityGuardrailsError, match="role"):
        parse_security_guardrails(catalog, root=REPO_ROOT)
    role_mappings["operator"] = removed  # restore (not strictly needed but clean)


def test_sg1_role_with_empty_scopes_raises() -> None:
    """A role with an empty scopes list must raise SecurityGuardrailsError."""
    catalog = _load_catalog()
    catalog["identity_rbac_contract"]["role_mappings"]["read_only"]["scopes"] = []
    with pytest.raises(SecurityGuardrailsError, match="scope"):
        parse_security_guardrails(catalog, root=REPO_ROOT)


def test_sg1_role_with_unknown_scope_raises() -> None:
    """A role carrying an unknown scope (outside REQUIRED_ROUTE_SCOPES) must raise."""
    catalog = _load_catalog()
    catalog["identity_rbac_contract"]["role_mappings"]["operator"]["scopes"].append(
        "not:a:real:scope"
    )
    with pytest.raises(SecurityGuardrailsError, match="scope"):
        parse_security_guardrails(catalog, root=REPO_ROOT)


# ---------------------------------------------------------------------------
# SG-2: secret ref metadata fields (required_when, format, rotation)
# ---------------------------------------------------------------------------


def test_sg2_ref_missing_required_when_raises() -> None:
    """A runtime ref entry with missing required_when must raise SecurityGuardrailsError."""
    catalog = _load_catalog()
    refs = catalog["secret_management_contract"]["required_runtime_refs"]
    ref = next(r for r in refs if r["id"] == "API_KEY_SPECS")
    del ref["required_when"]
    with pytest.raises(SecurityGuardrailsError):
        parse_security_guardrails(catalog, root=REPO_ROOT)


def test_sg2_ref_missing_format_raises() -> None:
    """A runtime ref entry with missing format must raise SecurityGuardrailsError."""
    catalog = _load_catalog()
    refs = catalog["secret_management_contract"]["required_runtime_refs"]
    ref = next(r for r in refs if r["id"] == "REVIEWER_ACCOUNTS")
    del ref["format"]
    with pytest.raises(SecurityGuardrailsError):
        parse_security_guardrails(catalog, root=REPO_ROOT)


def test_sg2_ref_missing_rotation_raises() -> None:
    """A runtime ref entry with missing rotation must raise SecurityGuardrailsError."""
    catalog = _load_catalog()
    refs = catalog["secret_management_contract"]["required_runtime_refs"]
    ref = next(r for r in refs if r["id"] == "DATABASE_URL")
    del ref["rotation"]
    with pytest.raises(SecurityGuardrailsError):
        parse_security_guardrails(catalog, root=REPO_ROOT)


def test_sg2_ref_empty_rotation_raises() -> None:
    """A runtime ref entry with an empty rotation string must raise SecurityGuardrailsError."""
    catalog = _load_catalog()
    refs = catalog["secret_management_contract"]["required_runtime_refs"]
    ref = next(r for r in refs if r["id"] == "UI_AUTH_COOKIE_SECRET")
    ref["rotation"] = "   "
    with pytest.raises(SecurityGuardrailsError):
        parse_security_guardrails(catalog, root=REPO_ROOT)


# ---------------------------------------------------------------------------
# SG-3: route-scope mapping id-level validation
# ---------------------------------------------------------------------------


def test_sg3_dropping_mapping_id_raises() -> None:
    """Dropping a required route-scope mapping id must raise SecurityGuardrailsError
    even if the route_scope value still appears in a surviving mapping."""
    catalog = _load_catalog()
    mappings = catalog["identity_rbac_contract"]["route_scope_mappings"]
    # Remove `ui_report_retry` — its route_scope (report:retry) still covered by `report_retry`
    before = len(mappings)
    catalog["identity_rbac_contract"]["route_scope_mappings"] = [
        m for m in mappings if m["id"] != "ui_report_retry"
    ]
    assert len(catalog["identity_rbac_contract"]["route_scope_mappings"]) == before - 1
    with pytest.raises(SecurityGuardrailsError, match="mapping"):
        parse_security_guardrails(catalog, root=REPO_ROOT)


def test_sg3_required_mapping_ids_constant_is_correct() -> None:
    """Sanity: REQUIRED_ROUTE_SCOPE_MAPPING_IDS matches the real catalog ids."""
    catalog = _load_catalog()
    actual_ids = {m["id"] for m in catalog["identity_rbac_contract"]["route_scope_mappings"]}
    assert REQUIRED_ROUTE_SCOPE_MAPPING_IDS == actual_ids


# ---------------------------------------------------------------------------
# SG-4: validate_only_catalog must be True in both contracts
# ---------------------------------------------------------------------------


def test_sg4_secret_validate_only_false_raises() -> None:
    """secret_management_contract.limits.validate_only_catalog = False must raise."""
    catalog = _load_catalog()
    catalog["secret_management_contract"]["limits"]["validate_only_catalog"] = False
    with pytest.raises(SecurityGuardrailsError, match="validate_only"):
        parse_security_guardrails(catalog, root=REPO_ROOT)


def test_sg4_identity_validate_only_false_raises() -> None:
    """identity_rbac_contract.limits.validate_only_catalog = False must raise."""
    catalog = _load_catalog()
    catalog["identity_rbac_contract"]["limits"]["validate_only_catalog"] = False
    with pytest.raises(SecurityGuardrailsError, match="validate_only"):
        parse_security_guardrails(catalog, root=REPO_ROOT)


def test_sg4_secret_validate_only_missing_raises() -> None:
    """secret_management_contract.limits missing validate_only_catalog must raise."""
    catalog = _load_catalog()
    del catalog["secret_management_contract"]["limits"]["validate_only_catalog"]
    with pytest.raises(SecurityGuardrailsError):
        parse_security_guardrails(catalog, root=REPO_ROOT)


def test_sg4_identity_validate_only_missing_raises() -> None:
    """identity_rbac_contract.limits missing validate_only_catalog must raise."""
    catalog = _load_catalog()
    del catalog["identity_rbac_contract"]["limits"]["validate_only_catalog"]
    with pytest.raises(SecurityGuardrailsError):
        parse_security_guardrails(catalog, root=REPO_ROOT)
