from __future__ import annotations

import importlib
import importlib.util
from copy import deepcopy
from pathlib import Path
from types import ModuleType
from typing import Any, cast

import pytest

yaml = cast(Any, importlib.import_module("yaml"))

REPO_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_RISKS = {
    "protected_class_demographic_inputs",
    "residential_steering_proxy",
    "ranking_recommendation_suitability",
    "legal_financial_overclaim",
    "source_rights_sensitive_exposure",
    "auth_access_control",
    "production_error_leakage",
}
REQUIRED_BLOCKERS = {
    "external_security_review",
    "legal_fair_housing_review",
    "hosted_idp_rbac",
    "production_error_log_review",
    "ds017_vendor_entitlement",
    "hosted_monitoring_alerting",
}
EXPECTED_LIMITS = {
    "validate_only_catalog": True,
    "adds_product_semantics": False,
    "uses_demographic_inputs": False,
    "creates_recommendations": False,
    "claims_security_review_complete": False,
    "claims_legal_review_complete": False,
    "claims_hosted_production_ready": False,
}
REQUIRED_RESIDUAL_REVIEW_ITEMS = {
    "bandit_medium_findings",
}


def _load_validator() -> ModuleType:
    script_path = REPO_ROOT / "scripts" / "threat_proxy_audit_check.py"
    spec = importlib.util.spec_from_file_location("threat_proxy_audit_check", script_path)
    assert spec is not None
    loader = spec.loader
    assert loader is not None
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def _catalog() -> dict[str, Any]:
    catalog = yaml.safe_load(
        (REPO_ROOT / "config" / "threat_proxy_audit.yaml").read_text(
            encoding="utf-8",
        ),
    )
    assert isinstance(catalog, dict)
    return cast(dict[str, Any], catalog)


def test_threat_proxy_catalog_covers_required_risks_and_blockers() -> None:
    catalog = _catalog()

    assert catalog["schema_version"] == "threat_proxy_audit_v1"
    assert catalog["operator_runbook"] == "docs/runbooks/threat_proxy_audit.md"
    assert catalog["status"] == "repo_local_validate_only"
    assert catalog["validation"] == "scripts/run_threat_proxy_audit_check.ps1"

    risks = {risk["id"]: risk for risk in catalog["risk_register"]}
    assert REQUIRED_RISKS == set(risks)
    for risk in risks.values():
        assert risk["status"].endswith("repo_local")
        assert risk["controls"]
        for control_path in risk["controls"]:
            assert (REPO_ROOT / control_path).exists()

    blockers = {blocker["id"]: blocker for blocker in catalog["external_blockers"]}
    assert REQUIRED_BLOCKERS == set(blockers)
    for blocker in blockers.values():
        assert blocker["status"] == "blocked"
        assert (REPO_ROOT / blocker["authority"]).exists()

    residual_items = {
        item["id"]: item for item in catalog["residual_review_items"]
    }
    assert REQUIRED_RESIDUAL_REVIEW_ITEMS == set(residual_items)
    for item in residual_items.values():
        assert item["status"] == "review_debt_not_release_blocking"
        assert (REPO_ROOT / item["authority"]).exists()

    assert catalog["limits"] == EXPECTED_LIMITS


def test_threat_proxy_validator_fails_closed_for_missing_risk(monkeypatch: Any) -> None:
    validator = cast(Any, _load_validator())
    catalog = deepcopy(_catalog())
    catalog["risk_register"] = [
        risk
        for risk in catalog["risk_register"]
        if risk["id"] != "residential_steering_proxy"
    ]

    monkeypatch.setattr(
        validator,
        "read_text",
        lambda path: yaml.safe_dump(catalog)
        if path == "config/threat_proxy_audit.yaml"
        else (REPO_ROOT / path).read_text(encoding="utf-8"),
    )

    with pytest.raises(SystemExit, match="risk set mismatch"):
        validator.validate_catalog()


def test_threat_proxy_validator_fails_closed_for_missing_blocker(monkeypatch: Any) -> None:
    validator = cast(Any, _load_validator())
    catalog = deepcopy(_catalog())
    catalog["external_blockers"] = [
        blocker
        for blocker in catalog["external_blockers"]
        if blocker["id"] != "legal_fair_housing_review"
    ]

    monkeypatch.setattr(
        validator,
        "read_text",
        lambda path: yaml.safe_dump(catalog)
        if path == "config/threat_proxy_audit.yaml"
        else (REPO_ROOT / path).read_text(encoding="utf-8"),
    )

    with pytest.raises(SystemExit, match="external blocker set mismatch"):
        validator.validate_catalog()


def test_threat_proxy_validator_fails_closed_for_flipped_limit(monkeypatch: Any) -> None:
    validator = cast(Any, _load_validator())
    catalog = deepcopy(_catalog())
    catalog["limits"]["creates_recommendations"] = True

    monkeypatch.setattr(
        validator,
        "read_text",
        lambda path: yaml.safe_dump(catalog)
        if path == "config/threat_proxy_audit.yaml"
        else (REPO_ROOT / path).read_text(encoding="utf-8"),
    )

    with pytest.raises(SystemExit, match="limits changed"):
        validator.validate_catalog()


def test_threat_proxy_runbook_records_validate_only_limits() -> None:
    runbook = (REPO_ROOT / "docs" / "runbooks" / "threat_proxy_audit.md").read_text(
        encoding="utf-8",
    )

    for phrase in (
        "run_threat_proxy_audit_check.ps1",
        "validate-only",
        "threat_proxy_audit_v1",
        "census_demographics_used=false",
        "ranking/recommendation",
        "external security review",
        "legal fair-housing review",
        "hosted IdP/RBAC",
        "DS-017 entitlement",
        "hosted alerting",
    ):
        assert phrase in runbook


def test_threat_proxy_validator_tracks_current_guard_surfaces() -> None:
    validator = (REPO_ROOT / "scripts" / "threat_proxy_audit_check.py").read_text(
        encoding="utf-8",
    )

    for phrase in (
        "protected_class_demographic_inputs",
        "residential_steering_proxy",
        "ranking_recommendation_suitability",
        "legal_financial_overclaim",
        "source_rights_sensitive_exposure",
        "auth_access_control",
        "production_error_leakage",
        "bandit_medium_findings",
        "does not use ACS",
        "demographic variables",
        "compare API exposed ranking/recommendation keys",
        "FORBIDDEN_PHRASES",
        "identity_rbac_contract",
        "test_error_page_escapes_content_and_includes_viewport_meta",
    ):
        assert phrase in validator


def test_threat_proxy_scripts_exist_and_delegate_to_shared_validator() -> None:
    for script_name in (
        "run_threat_proxy_audit_check.ps1",
        "run_threat_proxy_audit_check.sh",
    ):
        script = (REPO_ROOT / "scripts" / script_name).read_text(encoding="utf-8")
        assert "threat_proxy_audit_check.py" in script
        assert "threat/proxy audit check: ok" in script


def test_release_readiness_composes_threat_proxy_audit() -> None:
    release_catalog = yaml.safe_load(
        (REPO_ROOT / "config" / "release_readiness.yaml").read_text(
            encoding="utf-8",
        ),
    )
    check_ids = {check["id"] for check in release_catalog["required_checks"]}

    assert "threat_proxy_audit" in check_ids
    assert (
        REPO_ROOT / "scripts" / "run_threat_proxy_audit_check.ps1"
    ).exists()

    validator = (REPO_ROOT / "scripts" / "release_readiness_check.py").read_text(
        encoding="utf-8",
    )
    runbook = (REPO_ROOT / "docs" / "runbooks" / "release_readiness.md").read_text(
        encoding="utf-8",
    )
    assert "scripts/threat_proxy_audit_check.py" in validator
    assert "run_threat_proxy_audit_check.ps1" in runbook
