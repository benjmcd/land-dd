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
    "Operator path execution qualifiers",
    "Packaged selected-county fixture case slug (not an AOI UUID)",
    "Connector evidence/review run ID",
    (
        "code-level integration pattern over an existing `{area_id}` plus "
        "whatever evidence is already ingested/reviewed"
    ),
    "not the packaged selected-county corpus path",
    "the `/ui/operator-cases/report` launcher",
    "approved UI delivery links",
    "follows the approved report lineage route",
    "selected-county launcher table and form contract",
    "all nine packaged selected-county operator DB smoke cases",
    "--reviewer-id fixture-reviewer",
    "--reviewer-token fixture-token-123",
    "--expect-artifact-persistence postgres+object_store",
    "artifact_metadata.persistence",
    (
        "It does not prove the HTTP `POST /report-runs` surface, "
        "`/operator-cases/{case_id}/report`, or DB artifact persistence"
    ),
)
RUNBOOK_STALE_PHRASES = (
    "County/vendor sources not ready",
    "Parcel, assessor, commercial parcel, and local zoning sources still require",
    "No machine-queryable county parcel connector",
    "No machine-queryable assessor connector; recorded as unknown",
    "| `terrain/slope` | live-connector only |",
    "| `wetlands` | live-connector only |",
    "emits the same JSON serialization the API serves",
    "generic report creation loads the packaged selected-county connector fixtures",
    "/report-runs/{id}",
    "/ui/report-runs/{id}",
    "representative selected-county operator DB smoke cases",
    "representative selected-county operator cases",
)
CATALOG_STALE_PHRASES = (
    "Chatham parcels/zoning, Brunswick coastal/wetlands",
    "DS-010 (county GIS parcels) and DS-011 (county assessor): added to",
    "DS-023 (local zoning PDFs): covered by fixture-backed zoning connector",
    "terrain/wetlands as live-connector-only",
    "parcels/assessor as NOT_EVALUATED for fixture regression",
)
REQUIRED_SELECTED_COUNTY_SOURCE_IDS = {"DS-010", "DS-011", "DS-023"}
REQUIRED_SELECTED_COUNTY_MANIFEST_KEYS = {
    "buncombe_nc",
    "chatham_nc",
    "brunswick_nc",
}
EXPECTED_SOURCE_PROVENANCE_ENUMS = {
    "dataset": (
        "county_source_dataset",
        "not_evaluated_sentinel",
        "recorded_fixture_dataset",
        "not_required_out_of_scope",
    ),
    "version": (
        "source_version_or_access_date",
        "static_sentinel_version",
        "recorded_fixture_version",
        "not_required_out_of_scope",
    ),
    "retrieval": (
        "connector_retrieval_metadata",
        "source_failure_metadata",
        "fixture_retrieval_metadata",
        "not_required_out_of_scope",
    ),
}
OUT_OF_SCOPE_PROVENANCE_EXPECTATION = "not_required_out_of_scope"
EXPECTED_SELECTED_COUNTY_PROVENANCE_BINDINGS: dict[str, dict[str, dict[str, Any]]] = {
    "buncombe_nc": {
        "DS-010": {
            "connector_names": ("buncombe_parcels_live",),
            "dataset_expectation": "county_source_dataset",
            "version_expectation": "source_version_or_access_date",
            "retrieval_expectation": "connector_retrieval_metadata",
            "out_of_scope": False,
        },
        "DS-011": {
            "connector_names": ("county_assessor_not_evaluated",),
            "dataset_expectation": "not_evaluated_sentinel",
            "version_expectation": "static_sentinel_version",
            "retrieval_expectation": "source_failure_metadata",
            "out_of_scope": False,
        },
        "DS-023": {
            "connector_names": (),
            "dataset_expectation": OUT_OF_SCOPE_PROVENANCE_EXPECTATION,
            "version_expectation": OUT_OF_SCOPE_PROVENANCE_EXPECTATION,
            "retrieval_expectation": OUT_OF_SCOPE_PROVENANCE_EXPECTATION,
            "out_of_scope": True,
        },
    },
    "chatham_nc": {
        "DS-010": {
            "connector_names": ("chatham_parcels_live",),
            "dataset_expectation": "county_source_dataset",
            "version_expectation": "source_version_or_access_date",
            "retrieval_expectation": "connector_retrieval_metadata",
            "out_of_scope": False,
        },
        "DS-011": {
            "connector_names": ("county_assessor_not_evaluated",),
            "dataset_expectation": "not_evaluated_sentinel",
            "version_expectation": "static_sentinel_version",
            "retrieval_expectation": "source_failure_metadata",
            "out_of_scope": False,
        },
        "DS-023": {
            "connector_names": ("chatham_zoning_udo_recorded",),
            "dataset_expectation": "recorded_fixture_dataset",
            "version_expectation": "recorded_fixture_version",
            "retrieval_expectation": "fixture_retrieval_metadata",
            "out_of_scope": False,
        },
    },
    "brunswick_nc": {
        "DS-010": {
            "connector_names": ("brunswick_parcels_live",),
            "dataset_expectation": "county_source_dataset",
            "version_expectation": "source_version_or_access_date",
            "retrieval_expectation": "connector_retrieval_metadata",
            "out_of_scope": False,
        },
        "DS-011": {
            "connector_names": ("county_assessor_not_evaluated",),
            "dataset_expectation": "not_evaluated_sentinel",
            "version_expectation": "static_sentinel_version",
            "retrieval_expectation": "source_failure_metadata",
            "out_of_scope": False,
        },
        "DS-023": {
            "connector_names": ("brunswick_zoning_udo_recorded",),
            "dataset_expectation": "recorded_fixture_dataset",
            "version_expectation": "recorded_fixture_version",
            "retrieval_expectation": "fixture_retrieval_metadata",
            "out_of_scope": False,
        },
    },
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def _duplicates(values: tuple[str, ...]) -> list[str]:
    return sorted({value for value in values if values.count(value) > 1})


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


def require_text_list(value: Any, message: str) -> tuple[str, ...]:
    values = require_list(value, message)
    text_values: list[str] = []
    for index, item in enumerate(values):
        if not isinstance(item, str) or not item.strip():
            raise SystemExit(f"{message} item {index} must be non-empty text")
        text_values.append(item)
    return tuple(text_values)


def require_text_tuple(value: Any, message: str) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise SystemExit(message)
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise SystemExit(f"{message} item {index} must be non-empty text")
    return value


def validate_expected_county_source_provenance_binding(
    county_key: str,
    source_id: str,
    connector_names: tuple[str, ...],
    dataset_expectation: str,
    version_expectation: str,
    retrieval_expectation: str,
    out_of_scope: bool,
) -> None:
    expected_county = require_mapping(
        EXPECTED_SELECTED_COUNTY_PROVENANCE_BINDINGS.get(county_key),
        f"selected_county_source_provenance_scope.counties.{county_key} expectation missing",
    )
    expected = require_mapping(
        expected_county.get(source_id),
        (
            "selected_county_source_provenance_scope.counties."
            f"{county_key}.sources.{source_id} expectation missing"
        ),
    )
    expected_connector_names = require_text_tuple(
        expected.get("connector_names"),
        (
            "selected_county_source_provenance_scope.counties."
            f"{county_key}.sources.{source_id}.connector_names expectation invalid"
        ),
    )
    require(
        connector_names == expected_connector_names,
        (
            f"selected_county_source_provenance_scope {source_id} connector_names "
            f"mismatch at {county_key}.sources.{source_id}.connector_names; "
            f"expected={list(expected_connector_names)}, got={list(connector_names)}"
        ),
    )
    actual_expectations = {
        "dataset_expectation": dataset_expectation,
        "version_expectation": version_expectation,
        "retrieval_expectation": retrieval_expectation,
    }
    expected_expectations = {
        key: require_text(
            expected.get(key),
            (
                "selected_county_source_provenance_scope.counties."
                f"{county_key}.sources.{source_id}.{key} expectation invalid"
            ),
        )
        for key in actual_expectations
    }
    require(
        actual_expectations == expected_expectations,
        (
            "selected_county_source_provenance_scope.counties."
            f"{county_key}.sources.{source_id} provenance expectations mismatch; "
            f"expected={expected_expectations}, got={actual_expectations}"
        ),
    )
    expected_out_of_scope = expected.get("out_of_scope")
    require(
        isinstance(expected_out_of_scope, bool),
        (
            "selected_county_source_provenance_scope.counties."
            f"{county_key}.sources.{source_id}.out_of_scope expectation invalid"
        ),
    )
    require(
        out_of_scope is expected_out_of_scope,
        (
            "selected_county_source_provenance_scope.counties."
            f"{county_key}.sources.{source_id}.out_of_scope mismatch; "
            f"expected={expected_out_of_scope}, got={out_of_scope}"
        ),
    )


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
    for phrase in CATALOG_STALE_PHRASES:
        require(
            phrase not in catalog_text,
            f"private MVP catalog has stale phrase: {phrase}",
        )


def validate_selected_county_source_scope_catalog(
    catalog: dict[str, Any],
) -> dict[str, dict[str, tuple[str, ...]]]:
    raw_scope = require_mapping(
        catalog.get("selected_county_source_scope"),
        "selected_county_source_scope section missing",
    )
    missing = REQUIRED_SELECTED_COUNTY_SOURCE_IDS - set(raw_scope)
    unexpected = set(raw_scope) - REQUIRED_SELECTED_COUNTY_SOURCE_IDS
    require(
        not missing and not unexpected,
        (
            "selected_county_source_scope source IDs mismatch; "
            f"missing={sorted(missing)}, unexpected={sorted(unexpected)}"
        ),
    )

    scope: dict[str, dict[str, tuple[str, ...]]] = {}
    for source_id in sorted(REQUIRED_SELECTED_COUNTY_SOURCE_IDS):
        raw_entry = require_mapping(
            raw_scope.get(source_id),
            f"selected_county_source_scope.{source_id} must be a mapping",
        )
        require(
            raw_entry.get("source_registry_id") == source_id,
            f"selected_county_source_scope.{source_id}.source_registry_id mismatch",
        )
        connector_names = require_text_list(
            raw_entry.get("connector_names"),
            f"selected_county_source_scope.{source_id}.connector_names missing",
        )
        required_surfaces = require_text_list(
            raw_entry.get("required_surfaces"),
            f"selected_county_source_scope.{source_id}.required_surfaces missing",
        )
        scope_note_fragments = require_text_list(
            raw_entry.get("scope_note_fragments"),
            f"selected_county_source_scope.{source_id}.scope_note_fragments missing",
        )
        out_of_scope = require_text_list(
            raw_entry.get("out_of_scope"),
            f"selected_county_source_scope.{source_id}.out_of_scope missing",
        )
        for field_name, values in (
            ("connector_names", connector_names),
            ("required_surfaces", required_surfaces),
            ("scope_note_fragments", scope_note_fragments),
            ("out_of_scope", out_of_scope),
        ):
            duplicates = _duplicates(values)
            require(
                not duplicates,
                (
                    f"selected_county_source_scope.{source_id}.{field_name} "
                    f"must not contain duplicates: {duplicates}"
                ),
            )
        scope[source_id] = {
            "connector_names": connector_names,
            "required_surfaces": required_surfaces,
            "scope_note_fragments": scope_note_fragments,
            "out_of_scope": out_of_scope,
        }
    return scope


def validate_selected_county_manifest_scope_catalog(
    catalog: dict[str, Any],
) -> dict[str, Any]:
    raw_scope = require_mapping(
        catalog.get("selected_county_manifest_scope"),
        "selected_county_manifest_scope section missing",
    )
    stale_fragments = require_text_list(
        raw_scope.get("stale_fragments"),
        "selected_county_manifest_scope.stale_fragments missing",
    )
    duplicates = _duplicates(stale_fragments)
    require(
        not duplicates,
        (
            "selected_county_manifest_scope.stale_fragments must not contain "
            f"duplicates: {duplicates}"
        ),
    )

    raw_counties = require_mapping(
        raw_scope.get("counties"),
        "selected_county_manifest_scope.counties missing",
    )
    missing = REQUIRED_SELECTED_COUNTY_MANIFEST_KEYS - set(raw_counties)
    unexpected = set(raw_counties) - REQUIRED_SELECTED_COUNTY_MANIFEST_KEYS
    require(
        not missing and not unexpected,
        (
            "selected_county_manifest_scope county keys mismatch; "
            f"missing={sorted(missing)}, unexpected={sorted(unexpected)}"
        ),
    )

    counties: dict[str, dict[str, Any]] = {}
    for county_key in sorted(REQUIRED_SELECTED_COUNTY_MANIFEST_KEYS):
        raw_county = require_mapping(
            raw_counties.get(county_key),
            f"selected_county_manifest_scope.counties.{county_key} must be a mapping",
        )
        county_label = require_text(
            raw_county.get("county_label"),
            f"selected_county_manifest_scope.counties.{county_key}.county_label missing",
        )
        source_manifest = require_text(
            raw_county.get("source_manifest"),
            f"selected_county_manifest_scope.counties.{county_key}.source_manifest missing",
        )
        raw_fragments = require_mapping(
            raw_county.get("source_fragments"),
            (
                "selected_county_manifest_scope.counties."
                f"{county_key}.source_fragments missing"
            ),
        )
        missing_sources = REQUIRED_SELECTED_COUNTY_SOURCE_IDS - set(raw_fragments)
        unexpected_sources = set(raw_fragments) - REQUIRED_SELECTED_COUNTY_SOURCE_IDS
        require(
            not missing_sources and not unexpected_sources,
            (
                "selected_county_manifest_scope.counties."
                f"{county_key}.source_fragments source IDs mismatch; "
                f"missing={sorted(missing_sources)}, "
                f"unexpected={sorted(unexpected_sources)}"
            ),
        )

        source_fragments: dict[str, tuple[str, ...]] = {}
        for source_id in sorted(REQUIRED_SELECTED_COUNTY_SOURCE_IDS):
            fragments = require_text_list(
                raw_fragments.get(source_id),
                (
                    "selected_county_manifest_scope.counties."
                    f"{county_key}.source_fragments.{source_id} missing"
                ),
            )
            duplicates = _duplicates(fragments)
            require(
                not duplicates,
                (
                    "selected_county_manifest_scope.counties."
                    f"{county_key}.source_fragments.{source_id} "
                    f"must not contain duplicates: {duplicates}"
                ),
            )
            source_fragments[source_id] = fragments

        counties[county_key] = {
            "county_label": county_label,
            "source_manifest": source_manifest,
            "source_fragments": source_fragments,
        }

    return {
        "stale_fragments": stale_fragments,
        "counties": counties,
    }


def validate_selected_county_source_provenance_scope_catalog(
    catalog: dict[str, Any],
    selected_county_scope: dict[str, dict[str, tuple[str, ...]]],
    manifest_scope: dict[str, Any],
) -> dict[str, Any]:
    raw_scope = require_mapping(
        catalog.get("selected_county_source_provenance_scope"),
        "selected_county_source_provenance_scope section missing",
    )
    raw_enums = require_mapping(
        raw_scope.get("expectation_enums"),
        "selected_county_source_provenance_scope.expectation_enums missing",
    )
    missing_enum_keys = set(EXPECTED_SOURCE_PROVENANCE_ENUMS) - set(raw_enums)
    unexpected_enum_keys = set(raw_enums) - set(EXPECTED_SOURCE_PROVENANCE_ENUMS)
    require(
        not missing_enum_keys and not unexpected_enum_keys,
        (
            "selected_county_source_provenance_scope.expectation_enums keys mismatch; "
            f"missing={sorted(missing_enum_keys)}, "
            f"unexpected={sorted(unexpected_enum_keys)}"
        ),
    )
    for expectation_name, expected_values in EXPECTED_SOURCE_PROVENANCE_ENUMS.items():
        values = require_text_list(
            raw_enums.get(expectation_name),
            (
                "selected_county_source_provenance_scope.expectation_enums."
                f"{expectation_name} missing"
            ),
        )
        require(
            values == expected_values,
            (
                "selected_county_source_provenance_scope.expectation_enums."
                f"{expectation_name} must be {list(expected_values)}, got {list(values)}"
            ),
        )

    raw_counties = require_mapping(
        raw_scope.get("counties"),
        "selected_county_source_provenance_scope.counties missing",
    )
    manifest_counties = require_mapping(
        manifest_scope.get("counties"),
        "selected_county_manifest_scope.counties missing",
    )
    missing_counties = set(manifest_counties) - set(raw_counties)
    unexpected_counties = set(raw_counties) - set(manifest_counties)
    require(
        not missing_counties and not unexpected_counties,
        (
            "selected_county_source_provenance_scope county keys mismatch; "
            f"missing={sorted(missing_counties)}, "
            f"unexpected={sorted(unexpected_counties)}"
        ),
    )

    connector_names_by_source: dict[str, list[str]] = {
        source_id: [] for source_id in selected_county_scope
    }
    counties: dict[str, dict[str, Any]] = {}
    for county_key in sorted(manifest_counties):
        raw_county = require_mapping(
            raw_counties.get(county_key),
            (
                "selected_county_source_provenance_scope.counties."
                f"{county_key} must be a mapping"
            ),
        )
        raw_sources = require_mapping(
            raw_county.get("sources"),
            (
                "selected_county_source_provenance_scope.counties."
                f"{county_key}.sources missing"
            ),
        )
        manifest_county = require_mapping(
            manifest_counties.get(county_key),
            f"selected_county_manifest_scope.counties.{county_key} invalid",
        )
        manifest_sources = require_mapping(
            manifest_county.get("source_fragments"),
            (
                "selected_county_manifest_scope.counties."
                f"{county_key}.source_fragments missing"
            ),
        )
        missing_sources = set(manifest_sources) - set(raw_sources)
        unexpected_sources = set(raw_sources) - set(manifest_sources)
        require(
            not missing_sources and not unexpected_sources,
            (
                "selected_county_source_provenance_scope.counties."
                f"{county_key}.sources source IDs mismatch; "
                f"missing={sorted(missing_sources)}, "
                f"unexpected={sorted(unexpected_sources)}"
            ),
        )

        sources: dict[str, dict[str, Any]] = {}
        for source_id in sorted(manifest_sources):
            raw_entry = require_mapping(
                raw_sources.get(source_id),
                (
                    "selected_county_source_provenance_scope.counties."
                    f"{county_key}.sources.{source_id} must be a mapping"
                ),
            )
            require(
                raw_entry.get("source_registry_id") == source_id,
                (
                    "selected_county_source_provenance_scope.counties."
                    f"{county_key}.sources.{source_id}.source_registry_id mismatch"
                ),
            )
            connector_names = require_text_list(
                raw_entry.get("connector_names"),
                (
                    "selected_county_source_provenance_scope.counties."
                    f"{county_key}.sources.{source_id}.connector_names missing"
                ),
            )
            duplicates = _duplicates(connector_names)
            require(
                not duplicates,
                (
                    "selected_county_source_provenance_scope.counties."
                    f"{county_key}.sources.{source_id}.connector_names "
                    f"must not contain duplicates: {duplicates}"
                ),
            )
            allowed_connector_names = set(
                selected_county_scope[source_id]["connector_names"],
            )
            unexpected_connector_names = sorted(
                set(connector_names) - allowed_connector_names,
            )
            require(
                not unexpected_connector_names,
                (
                    "selected_county_source_provenance_scope.counties."
                    f"{county_key}.sources.{source_id}.connector_names "
                    f"not declared in selected_county_source_scope: "
                    f"{unexpected_connector_names}"
                ),
            )

            dataset_expectation = require_text(
                raw_entry.get("dataset_expectation"),
                (
                    "selected_county_source_provenance_scope.counties."
                    f"{county_key}.sources.{source_id}.dataset_expectation missing"
                ),
            )
            version_expectation = require_text(
                raw_entry.get("version_expectation"),
                (
                    "selected_county_source_provenance_scope.counties."
                    f"{county_key}.sources.{source_id}.version_expectation missing"
                ),
            )
            retrieval_expectation = require_text(
                raw_entry.get("retrieval_expectation"),
                (
                    "selected_county_source_provenance_scope.counties."
                    f"{county_key}.sources.{source_id}.retrieval_expectation missing"
                ),
            )
            for field_name, expectation, allowed_values in (
                (
                    "dataset_expectation",
                    dataset_expectation,
                    EXPECTED_SOURCE_PROVENANCE_ENUMS["dataset"],
                ),
                (
                    "version_expectation",
                    version_expectation,
                    EXPECTED_SOURCE_PROVENANCE_ENUMS["version"],
                ),
                (
                    "retrieval_expectation",
                    retrieval_expectation,
                    EXPECTED_SOURCE_PROVENANCE_ENUMS["retrieval"],
                ),
            ):
                require(
                    expectation in allowed_values,
                    (
                        "selected_county_source_provenance_scope.counties."
                        f"{county_key}.sources.{source_id}.{field_name} invalid: "
                        f"{expectation!r}"
                    ),
                )

            out_of_scope_value = raw_entry.get("out_of_scope")
            require(
                isinstance(out_of_scope_value, bool),
                (
                    "selected_county_source_provenance_scope.counties."
                    f"{county_key}.sources.{source_id}.out_of_scope must be boolean"
                ),
            )
            out_of_scope = bool(out_of_scope_value)
            validate_expected_county_source_provenance_binding(
                county_key,
                source_id,
                connector_names,
                dataset_expectation,
                version_expectation,
                retrieval_expectation,
                out_of_scope,
            )
            if out_of_scope:
                require(
                    not connector_names,
                    (
                        "selected_county_source_provenance_scope.counties."
                        f"{county_key}.sources.{source_id}.connector_names must be "
                        "empty when out_of_scope=true"
                    ),
                )
                require(
                    dataset_expectation == OUT_OF_SCOPE_PROVENANCE_EXPECTATION
                    and version_expectation == OUT_OF_SCOPE_PROVENANCE_EXPECTATION
                    and retrieval_expectation == OUT_OF_SCOPE_PROVENANCE_EXPECTATION,
                    (
                        "selected_county_source_provenance_scope.counties."
                        f"{county_key}.sources.{source_id} out-of-scope entries "
                        "must use not_required_out_of_scope expectations"
                    ),
                )
                require_text(
                    raw_entry.get("out_of_scope_reason"),
                    (
                        "selected_county_source_provenance_scope.counties."
                        f"{county_key}.sources.{source_id}.out_of_scope_reason missing"
                    ),
                )
            else:
                require(
                    bool(connector_names),
                    (
                        "selected_county_source_provenance_scope.counties."
                        f"{county_key}.sources.{source_id}.connector_names missing "
                        "for in-scope source"
                    ),
                )
                require(
                    OUT_OF_SCOPE_PROVENANCE_EXPECTATION
                    not in {
                        dataset_expectation,
                        version_expectation,
                        retrieval_expectation,
                    },
                    (
                        "selected_county_source_provenance_scope.counties."
                        f"{county_key}.sources.{source_id} in-scope entries "
                        "must not use not_required_out_of_scope expectations"
                    ),
                )

            if county_key == "buncombe_nc" and source_id == "DS-023":
                reason = str(raw_entry.get("out_of_scope_reason", ""))
                require(
                    out_of_scope and "Buncombe" in reason,
                    "Buncombe DS-023 provenance scope must remain explicitly out of scope",
                )

            connector_names_by_source[source_id].extend(connector_names)
            sources[source_id] = {
                "source_registry_id": source_id,
                "connector_names": connector_names,
                "dataset_expectation": dataset_expectation,
                "version_expectation": version_expectation,
                "retrieval_expectation": retrieval_expectation,
                "out_of_scope": out_of_scope,
            }

        counties[county_key] = {"sources": sources}

    for source_id, expected in selected_county_scope.items():
        actual_names = set(connector_names_by_source[source_id])
        expected_names = set(expected["connector_names"])
        missing_names = sorted(expected_names - actual_names)
        unexpected_names = sorted(actual_names - expected_names)
        require(
            not missing_names and not unexpected_names,
            (
                "selected_county_source_provenance_scope "
                f"{source_id} connector_names mismatch; "
                f"missing={missing_names}, unexpected={unexpected_names}"
            ),
        )

    return {
        "expectation_enums": EXPECTED_SOURCE_PROVENANCE_ENUMS,
        "counties": counties,
    }


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


def validate_full_release_stays_blocked(
    selected_county_scope: dict[str, dict[str, tuple[str, ...]]],
) -> None:
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
    validate_selected_county_source_scopes(sources, selected_county_scope)


def validate_selected_county_source_scopes(
    sources: list[Any],
    selected_county_scope: dict[str, dict[str, tuple[str, ...]]],
) -> None:
    sources_by_id = {
        str(source.get("source_registry_id")): source
        for source in sources
        if isinstance(source, dict)
    }
    for source_id, expected in selected_county_scope.items():
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
        connector_surfaces = require_list(
            source.get("connector_surfaces"),
            f"{source_id} connector_surfaces missing from source readiness output",
        )
        missing_surfaces = sorted(
            set(expected["required_surfaces"])
            - {str(surface) for surface in connector_surfaces}
        )
        require(
            not missing_surfaces,
            f"{source_id} connector_surfaces missing required values: {missing_surfaces}",
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


def validate_county_source_manifests(manifest_scope: dict[str, Any]) -> None:
    stale_fragments = require_text_tuple(
        manifest_scope.get("stale_fragments"),
        "selected_county_manifest_scope.stale_fragments missing",
    )
    counties = require_mapping(
        manifest_scope.get("counties"),
        "selected_county_manifest_scope.counties missing",
    )
    for county_key, raw_county in counties.items():
        county = require_mapping(
            raw_county,
            f"selected_county_manifest_scope.counties.{county_key} invalid",
        )
        path_text = require_text(
            county.get("source_manifest"),
            f"selected_county_manifest_scope.counties.{county_key}.source_manifest missing",
        )
        source_fragments = require_mapping(
            county.get("source_fragments"),
            (
                "selected_county_manifest_scope.counties."
                f"{county_key}.source_fragments missing"
            ),
        )
        path = ROOT / path_text
        require(path.is_file(), f"county source manifest missing: {path_text}")
        manifest = path.read_text(encoding="utf-8")
        for source_id, raw_fragments in source_fragments.items():
            fragments = require_text_tuple(
                raw_fragments,
                (
                    "selected_county_manifest_scope.counties."
                    f"{county_key}.source_fragments.{source_id} missing"
                ),
            )
            for phrase in fragments:
                require(
                    phrase in manifest,
                    f"county source manifest {path_text} missing phrase: {phrase}",
                )
        for phrase in stale_fragments:
            require(
                phrase not in manifest,
                f"county source manifest {path_text} has stale phrase: {phrase}",
            )


def main() -> int:
    validate_required_files()
    catalog = load_catalog()
    validate_catalog_metadata(catalog)
    selected_county_scope = validate_selected_county_source_scope_catalog(catalog)
    manifest_scope = validate_selected_county_manifest_scope_catalog(catalog)
    validate_selected_county_source_provenance_scope_catalog(
        catalog,
        selected_county_scope,
        manifest_scope,
    )
    validate_private_mvp_gates(catalog)
    validate_hosted_production_scope(catalog)
    validate_ds017_boundary(catalog)
    validate_full_release_stays_blocked(selected_county_scope)
    validate_operator_runbook()
    validate_county_source_manifests(manifest_scope)
    return 0


if __name__ == "__main__":
    from pathlib import Path as _QualificationPath
    import sys as _qualification_sys
    _qualification_sys.path.insert(0, str(_QualificationPath(__file__).resolve().parent))
    from qualification_checker_advertisement import maybe_emit_qualification_criteria

    maybe_emit_qualification_criteria(__file__)
    raise SystemExit(main())
