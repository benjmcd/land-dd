from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_PRIVATE_MVP_GATES = {
    "geography_selected",
    "county_manifests_present",
    "golden_aoi_fixture_manifest",
    "fixture_regression_path",
    "db_backed_regression_path",
    "ds010_011_023_selected_county_behavior",
    "ds010_source_review_gate",
    "unauthenticated_workspace_isolation",
    "sync_async_create_divergence",
    "ds017_not_required",
    "markdown_dossier_delivery",
    "overclaim_checks",
    "evidence_lineage_checks",
    "unknowns_visible",
    "operator_runbook_current",
}
HOSTED_PRODUCTION_ONLY_ITEMS = {
    "hosted_deployment",
    "oauth_oidc",
    "registry_publication",
    "billing",
    "external_secret_manager",
}
REQUIRED_FILES = (
    "config/private_mvp_beta_readiness.yaml",
    "config/release_readiness.yaml",
    "docs/runbooks/mvp_operator.md",
    "registers/data_source_registry.csv",
    "scripts/source_readiness.py",
    "scripts/run_mvp_regression.ps1",
)
RUNBOOK_REQUIRED_CURRENT_PHRASES = (
    "Private MVP Utility Proof",
    "fixture-backed, no paid vendors",
    "Buncombe, Chatham, Brunswick",
    "NOT_EVALUATED domains",
    "No API keys, paid vendors, or live DB are required",
    ".\\scripts\\run_mvp_regression.ps1",
    "County/vendor coverage is intentionally scoped",
    "DS-010 parcel connectors are limited to Buncombe/Chatham/Brunswick",
    "DS-011 assessor remains explicit NOT_EVALUATED evidence",
    "DS-023 covers Chatham/Brunswick recorded-fixture zoning only",
)
RUNBOOK_STALE_PHRASES = (
    "County/vendor sources not ready",
    "Parcel, assessor, commercial parcel, and local zoning sources still require",
    "No machine-queryable county parcel connector",
    "No machine-queryable assessor connector; recorded as unknown",
    "| `terrain/slope` | live-connector only |",
    "| `wetlands` | live-connector only |",
)
CATALOG_REQUIRED_CURRENT_PHRASES = (
    "backend/tests/private_mvp/test_utility_closure.py",
    "DS-010 selected-county parcel connectors are ready",
    "AssessorNotEvaluatedConnector sentinel",
    "DS-023 is ready only for Chatham/Brunswick recorded-fixture UDO district",
    "selected-county DS-010/DS-023 scope",
)
CATALOG_STALE_PHRASES = (
    "Chatham parcels/zoning, Brunswick coastal/wetlands",
    "DS-010 (county GIS parcels) and DS-011 (county assessor): added to",
    "DS-023 (local zoning PDFs): covered by fixture-backed zoning connector",
    "terrain/wetlands as live-connector-only",
    "parcels/assessor as NOT_EVALUATED for fixture regression",
)
EXPECTED_SELECTED_COUNTY_SOURCE_SCOPES: dict[str, dict[str, tuple[str, ...]]] = {
    "DS-010": {
        "connector_names": (
            "chatham_parcels_live",
            "buncombe_parcels_live",
            "brunswick_parcels_live",
        ),
        "scope_note_fragments": (
            "Chatham County NC parcel screening only",
            "Buncombe County NC parcel screening only",
            "Brunswick County NC parcel screening only",
            "no owner/value/title fields",
            "durable live-job support not claimed",
        ),
    },
    "DS-023": {
        "connector_names": (
            "chatham_zoning_udo_recorded",
            "brunswick_zoning_udo_recorded",
        ),
        "scope_note_fragments": (
            "Chatham County NC recorded-fixture UDO district lookup only",
            "Brunswick County NC recorded-fixture UDO district lookup only",
            "not live PDF ingestion or legal zoning advice",
        ),
    },
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def require_mapping(value: Any, message: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SystemExit(message)
    return value


def require_text(value: Any, message: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SystemExit(message)
    return value


def require_list(value: Any, message: str) -> list[Any]:
    if not isinstance(value, list):
        raise SystemExit(message)
    return value


def require_file(path_text: str) -> None:
    require((ROOT / path_text).is_file(), f"required private MVP artifact missing: {path_text}")


def load_catalog() -> dict[str, Any]:
    return require_mapping(
        yaml.safe_load(
            (ROOT / "config" / "private_mvp_beta_readiness.yaml").read_text(
                encoding="utf-8",
            ),
        ),
        "private MVP readiness catalog must be a mapping",
    )


def load_release_catalog() -> dict[str, Any]:
    return require_mapping(
        yaml.safe_load(
            (ROOT / "config" / "release_readiness.yaml").read_text(encoding="utf-8"),
        ),
        "release readiness catalog must be a mapping",
    )


def load_registry_row(source_registry_id: str) -> dict[str, str]:
    with (ROOT / "registers" / "data_source_registry.csv").open(
        newline="",
        encoding="utf-8",
    ) as csv_file:
        for row in csv.DictReader(csv_file):
            if row["Source ID"] == source_registry_id:
                return dict(row)
    raise SystemExit(f"{source_registry_id} missing from source registry")


def validate_required_files() -> None:
    for path_text in REQUIRED_FILES:
        require_file(path_text)


def validate_catalog_metadata(catalog: dict[str, Any]) -> None:
    require(
        catalog.get("schema_version") == "private_mvp_beta_readiness_v1",
        "unexpected private MVP readiness schema_version",
    )
    require(
        catalog.get("operator_runbook") == "docs/runbooks/mvp_operator.md",
        "private MVP operator_runbook mismatch",
    )
    require(
        catalog.get("validation") == "scripts/run_private_mvp_readiness_check.ps1",
        "private MVP validation command mismatch",
    )
    catalog_text = (ROOT / "config" / "private_mvp_beta_readiness.yaml").read_text(
        encoding="utf-8",
    )
    for phrase in CATALOG_REQUIRED_CURRENT_PHRASES:
        require(phrase in catalog_text, f"private MVP catalog missing phrase: {phrase}")
    for phrase in CATALOG_STALE_PHRASES:
        require(
            phrase not in catalog_text,
            f"private MVP catalog has stale phrase: {phrase}",
        )


def validate_private_mvp_gates(catalog: dict[str, Any]) -> None:
    private_gates = require_mapping(
        catalog.get("private_mvp_beta"),
        "private_mvp_beta section missing",
    )
    missing = EXPECTED_PRIVATE_MVP_GATES - set(private_gates)
    require(not missing, f"private_mvp_beta gates missing: {sorted(missing)}")

    for gate_name, raw_gate in private_gates.items():
        gate = require_mapping(raw_gate, f"private_mvp_beta.{gate_name} must be a mapping")
        status = require_text(gate.get("status"), f"{gate_name} status missing")
        require(
            status in {"complete", "accepted_with_risk"},
            f"{gate_name} must be complete or accepted_with_risk, got {status!r}",
        )
        require_text(gate.get("note"), f"{gate_name} note missing")
        if status == "complete":
            require_text(gate.get("evidence"), f"{gate_name} complete gate evidence missing")
        if status == "accepted_with_risk":
            require_text(gate.get("risk"), f"{gate_name} accepted risk text missing")


def validate_hosted_production_scope(catalog: dict[str, Any]) -> None:
    hosted = require_mapping(
        catalog.get("hosted_production"),
        "hosted_production section missing",
    )
    require(
        hosted.get("_not_required_for_private_mvp") is True,
        "hosted_production must be explicitly out of scope for private MVP",
    )
    missing = HOSTED_PRODUCTION_ONLY_ITEMS - set(hosted)
    require(not missing, f"hosted_production items missing: {sorted(missing)}")
    for item_name in HOSTED_PRODUCTION_ONLY_ITEMS:
        item = require_mapping(hosted[item_name], f"hosted_production.{item_name} invalid")
        require(
            item.get("status") == "blocked",
            f"hosted_production.{item_name} must remain blocked",
        )
        require_text(item.get("note"), f"hosted_production.{item_name} note missing")


def validate_ds017_boundary(catalog: dict[str, Any]) -> None:
    gate = require_mapping(
        require_mapping(catalog.get("private_mvp_beta"), "private_mvp_beta missing").get(
            "ds017_not_required",
        ),
        "ds017_not_required gate missing",
    )
    require(gate.get("status") == "complete", "ds017_not_required gate must be complete")

    row = load_registry_row("DS-017")
    require(row["MVP Priority"] == "Must", "DS-017 priority must stay Must for full readiness")
    for column in (
        "License Status",
        "Commercial Use Status",
        "Redistribution Status",
        "Cache Allowed",
        "Export Allowed",
        "AI Use Status",
        "Raw Data Allowed",
    ):
        require(row[column] == "blocked", f"DS-017 {column} must remain blocked")

    caveats = row["Caveats"].lower()
    require("private-mvp" in caveats, "DS-017 caveats must mention private-MVP scope")
    require("not required" in caveats, "DS-017 caveats must record not-required stance")


def validate_full_release_stays_blocked() -> None:
    release_catalog = load_release_catalog()
    blockers = require_mapping(
        {
            str(blocker.get("id")): blocker
            for blocker in release_catalog.get("release_blockers", [])
            if isinstance(blocker, dict)
        },
        "release blockers must be mappings",
    )
    non_ready = require_mapping(
        blockers.get("non_ready_must_sources"),
        "non_ready_must_sources release blocker missing",
    )
    require(
        non_ready.get("status") == "blocked",
        "non_ready_must_sources must remain blocked for full release readiness",
    )

    result = subprocess.run(
        [sys.executable, "scripts/source_readiness.py", "--priority", "Must", "--json"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = require_mapping(json.loads(result.stdout), "source readiness output invalid")
    require(payload.get("source_count") == 8, "Must source count changed")
    require(payload.get("ready_count") == 7, "Must ready count changed")
    require(payload.get("blocked_count") == 1, "Must blocked count changed")
    sources = require_list(payload.get("sources"), "source readiness sources missing")
    blocked = {
        str(source.get("source_registry_id"))
        for source in sources
        if isinstance(source, dict) and source.get("connector_ready") is False
    }
    require(blocked == {"DS-017"}, "full release Must blocker set must remain DS-017")
    validate_selected_county_source_scopes(sources)


def validate_selected_county_source_scopes(sources: list[Any]) -> None:
    sources_by_id = {
        str(source.get("source_registry_id")): source
        for source in sources
        if isinstance(source, dict)
    }
    for source_id, expected in EXPECTED_SELECTED_COUNTY_SOURCE_SCOPES.items():
        source = require_mapping(
            sources_by_id.get(source_id),
            f"{source_id} missing from Must source readiness output",
        )
        connector_names = require_list(
            source.get("connector_names"),
            f"{source_id} connector_names missing from source readiness output",
        )
        actual_names = [str(name) for name in connector_names]
        expected_names = set(expected["connector_names"])
        missing_names = sorted(expected_names - set(actual_names))
        unexpected_names = sorted(set(actual_names) - expected_names)
        duplicate_names = sorted(
            name
            for name in set(actual_names)
            if actual_names.count(name) > 1
        )
        require(
            not duplicate_names,
            f"{source_id} connector_names must not contain duplicates: {duplicate_names}",
        )
        require(
            not missing_names and not unexpected_names,
            (
                f"{source_id} connector_names mismatch; "
                f"missing={missing_names}, unexpected={unexpected_names}"
            ),
        )
        scope_notes = require_list(
            source.get("connector_scope_notes"),
            f"{source_id} connector_scope_notes missing from source readiness output",
        )
        scope_note_text = "\n".join(str(note) for note in scope_notes)
        for fragment in expected["scope_note_fragments"]:
            require(
                str(fragment) in scope_note_text,
                f"{source_id} connector_scope_notes missing fragment: {fragment}",
            )


def validate_operator_runbook() -> None:
    runbook = (ROOT / "docs" / "runbooks" / "mvp_operator.md").read_text(
        encoding="utf-8",
    )
    for phrase in RUNBOOK_REQUIRED_CURRENT_PHRASES:
        require(phrase in runbook, f"MVP operator runbook missing phrase: {phrase}")
    for phrase in RUNBOOK_STALE_PHRASES:
        require(
            phrase not in runbook,
            f"MVP operator runbook has stale phrase: {phrase}",
        )


def main() -> int:
    validate_required_files()
    catalog = load_catalog()
    validate_catalog_metadata(catalog)
    validate_private_mvp_gates(catalog)
    validate_hosted_production_scope(catalog)
    validate_ds017_boundary(catalog)
    validate_full_release_stays_blocked()
    validate_operator_runbook()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
