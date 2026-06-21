from __future__ import annotations


import importlib
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(ROOT))

CONFIG_PATH = "config/source_entitlements.yaml"
RUNBOOK_PATH = "docs/runbooks/source_entitlements.md"
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
EXPECTED_OUTCOMES = {
    "approve_under_reviewed_contract",
    "defer_or_remove_from_must_scope",
    "substitute_public_official_sources",
}
EXPECTED_FORBIDDEN_OUTPUTS = {
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
}
EXPECTED_FAILURE_MODES = {
    "auth_failure",
    "license_blocked",
    "quota_exceeded",
    "rate_limited",
    "stale_data",
    "vendor_outage",
    "no_coverage",
    "ambiguous_parcel_match",
    "partial_response",
    "schema_drift",
    "no_data",
}
EXPECTED_LIMITS = {
    "approves_sources": False,
    "selects_vendor": False,
    "implements_connector": False,
    "generates_artifacts": False,
    "calls_live_vendor": False,
    "changes_source_readiness": False,
}
REQUIRED_FILES = (
    CONFIG_PATH,
    RUNBOOK_PATH,
    "registers/data_source_registry.csv",
    "scripts/source_readiness.py",
    "state/PRODUCTION_AUTHORITY_PACKET.md",
    "backend/app/source_registry/usage_rights.py",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def require_mapping(value: Any, message: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SystemExit(message)
    return value


def require_non_empty_list(value: Any, message: str) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise SystemExit(message)
    return value


def require_text(value: Any, message: str) -> str:
    if not isinstance(value, str) or not value:
        raise SystemExit(message)
    return value


def read_text(path_text: str) -> str:
    return (ROOT / path_text).read_text(encoding="utf-8")


def require_existing(path_text: str) -> None:
    require(
        (ROOT / path_text).exists(),
        f"required source-entitlement artifact missing: {path_text}",
    )


def load_packet() -> dict[str, Any]:
    return require_mapping(
        yaml.safe_load(read_text(CONFIG_PATH)),
        "source-entitlement packet must be a mapping",
    )


def ds017_readiness_record() -> Any:
    readiness = importlib.import_module("app.source_registry.readiness")
    seed_module = importlib.import_module("db.seeds.source_registry_seeds")

    records = readiness.build_readiness_records(
        seed_module.load_registry_sources(priority="Must"),
    )
    for record in records:
        if record.source_registry_id == "DS-017":
            return record
    raise SystemExit("DS-017 missing from Must source readiness")


def validate_required_files() -> None:
    for path_text in REQUIRED_FILES:
        require_existing(path_text)


def validate_packet() -> None:
    packet = load_packet()
    require(
        packet.get("schema_version") == "source_entitlements_v1",
        "unexpected source-entitlement schema",
    )
    require(packet.get("operator_runbook") == RUNBOOK_PATH, "source-entitlement runbook mismatch")
    require(
        packet.get("status") == "repo_local_validate_only",
        "source-entitlement packet must remain validate-only",
    )
    require(
        packet.get("validation") == "scripts/run_source_entitlement_check.ps1",
        "source-entitlement validation wrapper mismatch",
    )
    require(
        require_mapping(packet.get("limits"), "source-entitlement limits missing")
        == EXPECTED_LIMITS,
        "source-entitlement limits changed without validator update",
    )

    sources = require_non_empty_list(packet.get("sources"), "source-entitlement sources missing")
    require(len(sources) == 1, "source-entitlement packet must only cover DS-017 for now")
    ds017 = require_mapping(sources[0], "DS-017 entitlement entry must be a mapping")
    readiness = ds017_readiness_record()
    require(ds017.get("source_registry_id") == "DS-017", "DS-017 entitlement entry missing")
    require(ds017.get("mvp_priority") == "Must", "DS-017 must remain a Must source in packet")
    require(
        ds017.get("current_decision_state") == "external_authority_required",
        "DS-017 decision state mismatch",
    )
    require(
        ds017.get("current_readiness") == "blocked",
        "DS-017 current readiness must remain blocked",
    )
    require(readiness.connector_ready is False, "DS-017 readiness unexpectedly ready")
    require(readiness.production_use_allowed is False, "DS-017 production use unexpectedly allowed")
    require(
        set(
            require_non_empty_list(
                ds017.get("blocked_registry_fields"),
                "DS-017 blocked fields missing",
            )
        )
        == set(readiness.blocked_fields),
        "DS-017 packet blocked fields must match source readiness",
    )
    require(
        set(
            require_non_empty_list(
                ds017.get("required_authority_fields"),
                "DS-017 required authority fields missing",
            )
        )
        == EXPECTED_REQUIRED_FIELDS,
        "DS-017 required authority fields changed without validator update",
    )
    outcomes = require_non_empty_list(
        ds017.get("acceptable_outcomes"),
        "DS-017 acceptable outcomes missing",
    )
    outcome_ids: set[str] = set()
    for outcome_raw in outcomes:
        outcome = require_mapping(outcome_raw, "each DS-017 outcome must be a mapping")
        outcome_id = require_text(outcome.get("id"), "DS-017 outcome id missing")
        outcome_ids.add(outcome_id)
        require_text(outcome.get("meaning"), f"DS-017 outcome {outcome_id} meaning missing")
    require(outcome_ids == EXPECTED_OUTCOMES, "DS-017 acceptable outcome set mismatch")
    require(
        EXPECTED_FORBIDDEN_OUTPUTS.issubset(
            set(
                require_non_empty_list(
                    ds017.get("forbidden_outputs_until_approved"),
                    "DS-017 forbidden outputs missing",
                )
            )
        ),
        "DS-017 forbidden outputs missing required sensitive fields",
    )
    require(
        set(
            require_non_empty_list(
                ds017.get("failure_modes_required"),
                "DS-017 failure modes missing",
            )
        )
        == EXPECTED_FAILURE_MODES,
        "DS-017 failure modes changed without validator update",
    )
    for path_key in (
        "source_registry_authority",
        "source_readiness_authority",
        "production_authority_packet",
    ):
        require_existing(require_text(ds017.get(path_key), f"DS-017 {path_key} missing"))


def validate_runbook() -> None:
    runbook = read_text(RUNBOOK_PATH)
    for phrase in (
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
        require(phrase in runbook, f"source-entitlement runbook missing phrase: {phrase}")


def validate_production_packet_alignment() -> None:
    packet = read_text("state/PRODUCTION_AUTHORITY_PACKET.md")
    for phrase in (
        "DS-017 Commercial Parcel Vendor Authority",
        "Vendor/source selection",
        "License approval",
        "Entitlement policy",
        "Cost model and billing owner",
        "Field-level policy",
        "Alternative unblock: DS-017 is removed or deferred from full-release Must scope",
    ):
        require(phrase in packet, f"production authority packet missing DS-017 phrase: {phrase}")


def main() -> int:
    validate_required_files()
    validate_packet()
    validate_runbook()
    validate_production_packet_alignment()
    print("source entitlement check: ok")
    return 0


if __name__ == "__main__":
    from pathlib import Path as _QualificationPath
    import sys as _qualification_sys
    _qualification_sys.path.insert(0, str(_QualificationPath(__file__).resolve().parent))
    from qualification_checker_advertisement import maybe_emit_qualification_criteria

    maybe_emit_qualification_criteria(__file__)
    raise SystemExit(main())
