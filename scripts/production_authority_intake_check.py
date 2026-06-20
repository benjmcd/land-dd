from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]

CONFIG_PATH = "config/production_authority_intake.yaml"
RUNBOOK_PATH = "docs/runbooks/production_authority_intake.md"

EXPECTED_LIMITS = {
    "validate_only_intake": True,
    "approves_sources": False,
    "selects_vendor": False,
    "provisions_hosted_platform": False,
    "provisions_identity_provider": False,
    "provisions_secret_manager": False,
    "publishes_registry_image": False,
    "creates_billing_integration": False,
    "creates_hosted_observability": False,
    "selects_bologna_aoi": False,
    "creates_runtime_artifacts": False,
    "mutates_database": False,
    "writes_secrets": False,
    "changes_source_readiness": False,
    "claims_level_10": False,
}
EXPECTED_STREAMS = {
    "ds017_source_entitlement",
    "hosted_platform",
    "secrets_manager",
    "identity_rbac",
    "image_publication",
    "billing_cost",
    "hosted_observability",
    "bologna_recorded_source",
}
REQUIRED_FILES = (
    CONFIG_PATH,
    RUNBOOK_PATH,
    "state/PRODUCTION_AUTHORITY_PACKET.md",
    "state/LEVEL_9_10_GATE_MATRIX.md",
    "config/source_entitlements.yaml",
    "config/hosted_deployment.yaml",
    "config/access_control.yaml",
    "config/image_publication.yaml",
    "config/ops_cost_monitoring.yaml",
    "config/observability_readiness.yaml",
    "config/bologna_source_authority_intake.yaml",
    "scripts/run_production_authority_intake_check.ps1",
    "scripts/run_production_authority_intake_check.sh",
)
RUNBOOK_PHRASES = (
    "production_authority_intake_v1",
    "validate-only",
    "does not approve sources",
    "authority_references",
    "decision_updates_allowed",
    "Level 10 authority",
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
    if not isinstance(value, str) or not value.strip():
        raise SystemExit(message)
    return value.strip()


def normalize_path(path_text: str) -> str:
    return path_text.replace("\\", "/")


def require_existing(path_text: str) -> None:
    normalized = normalize_path(path_text)
    require((ROOT / normalized).exists(), f"authority intake artifact missing: {normalized}")


def read_text(path_text: str) -> str:
    return (ROOT / normalize_path(path_text)).read_text(encoding="utf-8")


def load_yaml(path_text: str) -> dict[str, Any]:
    return require_mapping(yaml.safe_load(read_text(path_text)), f"{path_text} must be a mapping")


def list_set(value: Any, message: str) -> set[str]:
    return {str(item) for item in require_non_empty_list(value, message)}


def validate_required_files() -> None:
    for path_text in REQUIRED_FILES:
        require_existing(path_text)


def validate_stream_common(stream: dict[str, Any], stream_id: str, catalog_path: str) -> None:
    require(stream.get("status") == "blocked", f"{stream_id} must remain blocked")
    require(stream.get("source_catalog") == catalog_path, f"{stream_id} catalog mismatch")
    require(stream.get("evidence_status") == "missing", f"{stream_id} evidence status changed")
    require(stream.get("authority_references") == [], f"{stream_id} authority references changed")
    require(
        stream.get("decision_updates_allowed") is False,
        f"{stream_id} decision updates unexpectedly allowed",
    )


def validate_ds017(stream: dict[str, Any]) -> None:
    validate_stream_common(stream, "ds017_source_entitlement", "config/source_entitlements.yaml")
    catalog = load_yaml("config/source_entitlements.yaml")
    source = require_mapping(
        require_non_empty_list(catalog.get("sources"), "source entitlement sources missing")[0],
        "DS-017 entitlement entry must be a mapping",
    )
    require(source.get("source_registry_id") == "DS-017", "source entitlement must cover DS-017")
    require(
        list_set(stream.get("required_evidence"), "DS-017 intake evidence missing")
        == list_set(source.get("required_external_evidence"), "DS-017 external evidence missing"),
        "DS-017 intake evidence drifted",
    )


def validate_hosted(stream: dict[str, Any]) -> None:
    validate_stream_common(stream, "hosted_platform", "config/hosted_deployment.yaml")
    catalog = load_yaml("config/hosted_deployment.yaml")
    require(
        list_set(stream.get("required_evidence"), "hosted intake evidence missing")
        == list_set(catalog.get("blocked_until"), "hosted blockers missing"),
        "hosted intake blockers drifted",
    )


def validate_secrets(stream: dict[str, Any]) -> None:
    validate_stream_common(stream, "secrets_manager", "config/access_control.yaml")
    access = load_yaml("config/access_control.yaml")
    contract = require_mapping(
        access.get("secret_management_contract"),
        "secret management contract missing",
    )
    require(
        list_set(stream.get("required_evidence"), "secret intake evidence missing")
        == list_set(contract.get("handoff_requirements"), "secret handoff requirements missing"),
        "secret intake evidence drifted",
    )


def validate_identity(stream: dict[str, Any]) -> None:
    validate_stream_common(stream, "identity_rbac", "config/access_control.yaml")
    access = load_yaml("config/access_control.yaml")
    contract = require_mapping(access.get("identity_rbac_contract"), "identity contract missing")
    roles = require_mapping(contract.get("role_mappings"), "identity role mappings missing")
    require(
        list_set(stream.get("required_evidence"), "identity intake evidence missing")
        == list_set(contract.get("required_identity_claims"), "identity claims missing"),
        "identity intake evidence drifted",
    )
    require(
        list_set(stream.get("required_roles"), "identity intake roles missing") == set(roles),
        "identity intake roles drifted",
    )


def validate_image(stream: dict[str, Any]) -> None:
    validate_stream_common(stream, "image_publication", "config/image_publication.yaml")
    catalog = load_yaml("config/image_publication.yaml")
    require(
        list_set(stream.get("required_evidence"), "image intake evidence missing")
        == list_set(catalog.get("blocked_until"), "image publication blockers missing"),
        "image intake blockers drifted",
    )
    require(
        list_set(stream.get("required_attestations"), "image intake attestations missing")
        == list_set(catalog.get("required_attestations"), "image required attestations missing"),
        "image intake attestations drifted",
    )


def validate_billing(stream: dict[str, Any]) -> None:
    validate_stream_common(stream, "billing_cost", "config/ops_cost_monitoring.yaml")
    catalog = load_yaml("config/ops_cost_monitoring.yaml")
    categories = require_non_empty_list(catalog.get("categories"), "cost categories missing")
    category_mappings = [
        require_mapping(raw, "cost category must be a mapping") for raw in categories
    ]
    blocked = {
        require_text(category.get("id"), "cost category id missing")
        for category in category_mappings
        if category.get("status") in {"blocked_until_reviewed", "disabled_until_metered"}
    }
    require(
        list_set(stream.get("blocked_categories"), "billing blocked categories missing") == blocked,
        "billing blocked categories drifted",
    )
    require_non_empty_list(stream.get("required_evidence"), "billing intake evidence missing")


def validate_observability(stream: dict[str, Any]) -> None:
    validate_stream_common(stream, "hosted_observability", "config/observability_readiness.yaml")
    catalog = load_yaml("config/observability_readiness.yaml")
    blockers = {
        require_text(blocker.get("id"), "observability blocker id missing")
        for blocker in (
            require_mapping(raw, "observability blocker must be a mapping")
            for raw in require_non_empty_list(
                catalog.get("hosted_blockers"),
                "observability hosted blockers missing",
            )
        )
    }
    require(
        list_set(stream.get("required_evidence"), "observability intake evidence missing")
        == blockers,
        "observability intake blockers drifted",
    )


def validate_bologna(stream: dict[str, Any]) -> None:
    validate_stream_common(
        stream,
        "bologna_recorded_source",
        "config/bologna_source_authority_intake.yaml",
    )
    catalog = load_yaml("config/bologna_source_authority_intake.yaml")
    require(
        list_set(stream.get("required_evidence"), "Bologna intake evidence missing")
        == list_set(catalog.get("promotion_blockers"), "Bologna promotion blockers missing"),
        "Bologna intake blockers drifted",
    )


VALIDATORS = {
    "ds017_source_entitlement": validate_ds017,
    "hosted_platform": validate_hosted,
    "secrets_manager": validate_secrets,
    "identity_rbac": validate_identity,
    "image_publication": validate_image,
    "billing_cost": validate_billing,
    "hosted_observability": validate_observability,
    "bologna_recorded_source": validate_bologna,
}


def validate_catalog() -> None:
    payload = load_yaml(CONFIG_PATH)
    require(payload.get("schema_version") == "production_authority_intake_v1", "unexpected schema")
    require(payload.get("operator_runbook") == RUNBOOK_PATH, "runbook mismatch")
    require(payload.get("status") == "blocked_no_external_authority", "intake must stay blocked")
    require(
        payload.get("validation") == "scripts/run_production_authority_intake_check.ps1",
        "validation wrapper mismatch",
    )
    require(
        require_mapping(payload.get("limits"), "limits missing") == EXPECTED_LIMITS,
        "production authority limits changed",
    )
    for path_text in require_non_empty_list(payload.get("authority"), "authority paths missing"):
        require(isinstance(path_text, str), "authority paths must be strings")
        require_existing(path_text)

    streams = require_non_empty_list(payload.get("authority_streams"), "authority streams missing")
    by_id: dict[str, dict[str, Any]] = {}
    for raw_stream in streams:
        stream = require_mapping(raw_stream, "each authority stream must be a mapping")
        stream_id = require_text(stream.get("id"), "authority stream id missing")
        require(stream_id not in by_id, f"duplicate authority stream: {stream_id}")
        by_id[stream_id] = stream
    require(set(by_id) == EXPECTED_STREAMS, "authority stream set mismatch")
    for stream_id, validator in VALIDATORS.items():
        validator(by_id[stream_id])
    require_text(payload.get("unlock_rule"), "unlock rule missing")


def validate_runbook() -> None:
    runbook = read_text(RUNBOOK_PATH)
    for phrase in RUNBOOK_PHRASES:
        require(phrase in runbook, f"production authority runbook missing phrase: {phrase}")


def main() -> int:
    validate_required_files()
    validate_catalog()
    validate_runbook()
    print("production authority intake check: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
