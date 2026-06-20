from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, cast

yaml = cast(Any, __import__("yaml"))

REPO_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_REQUIRED_FIELDS = {
    "vendor_entity",
    "dataset_name",
    "contract_or_terms_reference",
    "terms_effective_date",
    "allowed_geography",
    "license_status",
    "commercial_use_status",
    "redistribution_status",
    "cache_allowed",
    "export_allowed",
    "raw_data_allowed",
    "ai_use_allowed",
    "attribution_required",
    "field_allowlist",
    "field_denylist",
    "entitlement_owner",
    "workspace_entitlement_policy",
    "report_entitlement_policy",
    "export_entitlement_policy",
    "cost_meter",
    "billing_owner",
    "connector_scope",
    "failure_mode_mapping",
}
EXPECTED_BLOCKED_FIELDS = {
    "review_status",
    "license_status",
    "commercial_use_status",
    "redistribution_status",
    "cache_allowed",
    "export_allowed",
    "raw_data_allowed",
    "ai_use_allowed",
    "connector_implemented",
}
EXPECTED_OUTCOMES = {
    "approve_under_reviewed_contract",
    "defer_or_remove_from_must_scope",
    "substitute_public_official_sources",
}


def _load_validator() -> ModuleType:
    script_path = REPO_ROOT / "scripts" / "source_entitlement_check.py"
    spec = importlib.util.spec_from_file_location("source_entitlement_check", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_source_entitlement_packet_shape_is_ds017_specific() -> None:
    packet = yaml.safe_load(
        (REPO_ROOT / "config" / "source_entitlements.yaml").read_text(encoding="utf-8"),
    )

    assert packet["schema_version"] == "source_entitlements_v1"
    assert packet["operator_runbook"] == "docs/runbooks/source_entitlements.md"
    assert packet["status"] == "repo_local_validate_only"
    assert packet["validation"] == "scripts/run_source_entitlement_check.ps1"
    assert packet["limits"] == {
        "approves_sources": False,
        "selects_vendor": False,
        "implements_connector": False,
        "generates_artifacts": False,
        "calls_live_vendor": False,
        "changes_source_readiness": False,
    }

    sources = packet["sources"]
    assert [source["source_registry_id"] for source in sources] == ["DS-017"]
    ds017 = sources[0]
    assert ds017["mvp_priority"] == "Must"
    assert ds017["current_decision_state"] == "external_authority_required"
    assert ds017["current_readiness"] == "blocked"
    assert set(ds017["blocked_registry_fields"]) == EXPECTED_BLOCKED_FIELDS
    assert set(ds017["required_authority_fields"]) == EXPECTED_REQUIRED_FIELDS
    assert {outcome["id"] for outcome in ds017["acceptable_outcomes"]} == EXPECTED_OUTCOMES


def test_source_entitlement_packet_keeps_forbidden_outputs_blocked() -> None:
    packet = yaml.safe_load(
        (REPO_ROOT / "config" / "source_entitlements.yaml").read_text(encoding="utf-8"),
    )
    ds017 = packet["sources"][0]
    forbidden = set(ds017["forbidden_outputs_until_approved"])

    for field in (
        "owner_name",
        "owner_mailing_address",
        "situs_address",
        "raw_vendor_record",
        "assessed_value",
        "market_value",
        "sale_or_comps_data",
        "title_status",
        "legal_access",
        "buildability_conclusion",
        "appraisal_or_lending_suitability",
        "investment_recommendation",
    ):
        assert field in forbidden


def test_source_entitlement_validator_passes_and_cross_checks_ds017_readiness() -> None:
    validator = cast(Any, _load_validator())

    validator.main()

    ds017 = validator.ds017_readiness_record()
    assert ds017.source_registry_id == "DS-017"
    assert ds017.mvp_priority == "Must"
    assert ds017.connector_ready is False
    assert ds017.production_use_allowed is False
    assert set(ds017.blocked_fields) == EXPECTED_BLOCKED_FIELDS


def test_source_entitlement_script_and_wrappers_are_validate_only() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/source_entitlement_check.py"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == "source entitlement check: ok"
    ps1 = (REPO_ROOT / "scripts" / "run_source_entitlement_check.ps1").read_text(
        encoding="utf-8",
    )
    sh = (REPO_ROOT / "scripts" / "run_source_entitlement_check.sh").read_text(
        encoding="utf-8",
    )
    for script in (ps1, sh):
        assert "source_entitlement_check.py" in script
        assert "source entitlement check: ok" in script
    assert "New-Item" not in ps1
    assert "Remove-Item" not in ps1
    assert "mkdir" not in sh
    assert "rm " not in sh


def test_source_entitlement_runbook_preserves_external_authority_boundary() -> None:
    runbook = (REPO_ROOT / "docs" / "runbooks" / "source_entitlements.md").read_text(
        encoding="utf-8",
    )

    for phrase in (
        "run_source_entitlement_check.ps1",
        "validate-only",
        "DS-017 remains blocked",
        "approve_under_reviewed_contract",
        "defer_or_remove_from_must_scope",
        "substitute_public_official_sources",
        "No owner",
        "raw vendor record",
        "paid-source metering",
        "does not approve DS-017",
    ):
        assert phrase in runbook
