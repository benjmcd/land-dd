from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from app.domain.source_contracts import SourceContract
from app.source_registry.readiness import SourceReadinessRecord, build_readiness_records

EXPECTED_SCHEMA = "private_mvp_beta_readiness_v1"
EXPECTED_COUNTY_KEYS = ("brunswick_nc", "buncombe_nc", "chatham_nc")
EXPECTED_SELECTED_SOURCE_IDS = ("DS-010", "DS-011", "DS-023")
EXPECTED_DS017_BLOCKER = "DS-017"
EXPECTED_ENUMS = {
    "dataset": {
        "county_source_dataset",
        "not_evaluated_sentinel",
        "recorded_fixture_dataset",
        "not_required_out_of_scope",
    },
    "version": {
        "source_version_or_access_date",
        "static_sentinel_version",
        "recorded_fixture_version",
        "not_required_out_of_scope",
    },
    "retrieval": {
        "connector_retrieval_metadata",
        "source_failure_metadata",
        "fixture_retrieval_metadata",
        "not_required_out_of_scope",
    },
}


class SourceProvenanceError(RuntimeError):
    """Raised when source-provenance artifacts cannot be trusted for UI rendering."""


@dataclass(frozen=True)
class SourceReadinessSummary:
    source_registry_id: str
    name: str
    domain: str
    review_status: str
    license_status: str
    connector_ready: bool
    connector_names: tuple[str, ...]
    blocked_fields: tuple[str, ...]


@dataclass(frozen=True)
class CountySourceProvenance:
    source_registry_id: str
    source_name: str
    connector_names: tuple[str, ...]
    dataset_expectation: str
    version_expectation: str
    retrieval_expectation: str
    out_of_scope: bool
    out_of_scope_reason: str
    readiness_connector_ready: bool
    readiness_blocked_fields: tuple[str, ...]


@dataclass(frozen=True)
class CountyProvenance:
    county_key: str
    county_label: str
    source_manifest: str
    sources: tuple[CountySourceProvenance, ...]


@dataclass(frozen=True)
class SourceProvenanceReadiness:
    schema_version: str
    expectation_enums: dict[str, tuple[str, ...]]
    selected_source_ids: tuple[str, ...]
    must_source_count: int
    must_ready_count: int
    must_blocked_source_ids: tuple[str, ...]
    ds017_blocker: SourceReadinessSummary | None
    counties: tuple[CountyProvenance, ...]


def repo_root_from_app() -> Path:
    return Path(__file__).resolve().parents[2]


def load_source_provenance(
    repo_root: Path | None = None,
    *,
    as_of: date | None = None,
) -> SourceProvenanceReadiness:
    root = repo_root or repo_root_from_app()
    catalog = _read_yaml(root / "config" / "private_mvp_beta_readiness.yaml")
    rows = _read_registry(root / "registers" / "data_source_registry.csv")
    return parse_source_provenance(catalog, rows, root=root, as_of=as_of)


def parse_source_provenance(
    catalog: dict[str, Any],
    registry_rows: list[dict[str, str]],
    *,
    root: Path,
    as_of: date | None = None,
) -> SourceProvenanceReadiness:
    schema_version = _require_exact_text(
        catalog.get("schema_version"),
        EXPECTED_SCHEMA,
        "private MVP readiness schema_version",
    )
    readiness_records = build_readiness_records(
        [_row_to_source(row) for row in registry_rows if row.get("MVP Priority") == "Must"],
        as_of=as_of,
    )
    record_by_source_id = {record.source_registry_id: record for record in readiness_records}
    ds017 = _ds017_blocker(record_by_source_id)
    must_blocked = tuple(
        sorted(
            record.source_registry_id
            for record in readiness_records
            if not record.connector_ready
        )
    )
    if must_blocked != (EXPECTED_DS017_BLOCKER,):
        raise SourceProvenanceError("Must-source blocked set must remain DS-017")

    provenance_scope = _require_mapping(
        catalog.get("selected_county_source_provenance_scope"),
        "selected_county_source_provenance_scope section missing",
    )
    expectation_enums = _expectation_enums(provenance_scope)
    manifest_scope = _require_mapping(
        catalog.get("selected_county_manifest_scope"),
        "selected_county_manifest_scope section missing",
    )
    manifest_counties = _require_mapping(
        manifest_scope.get("counties"),
        "selected_county_manifest_scope.counties missing",
    )
    provenance_counties = _require_mapping(
        provenance_scope.get("counties"),
        "selected_county_source_provenance_scope.counties missing",
    )
    if set(manifest_counties) != set(EXPECTED_COUNTY_KEYS):
        raise SourceProvenanceError("selected county manifest keys mismatch")
    if set(provenance_counties) != set(EXPECTED_COUNTY_KEYS):
        raise SourceProvenanceError("selected county provenance keys mismatch")

    counties = tuple(
        _county_provenance(
            county_key,
            manifest_counties[county_key],
            provenance_counties[county_key],
            record_by_source_id,
            root=root,
        )
        for county_key in EXPECTED_COUNTY_KEYS
    )
    return SourceProvenanceReadiness(
        schema_version=schema_version,
        expectation_enums=expectation_enums,
        selected_source_ids=tuple(sorted(EXPECTED_SELECTED_SOURCE_IDS)),
        must_source_count=len(readiness_records),
        must_ready_count=sum(1 for record in readiness_records if record.connector_ready),
        must_blocked_source_ids=must_blocked,
        ds017_blocker=_summary(ds017),
        counties=counties,
    )


def _county_provenance(
    county_key: str,
    manifest_payload: Any,
    provenance_payload: Any,
    record_by_source_id: dict[str, SourceReadinessRecord],
    *,
    root: Path,
) -> CountyProvenance:
    manifest = _require_mapping(
        manifest_payload,
        f"selected_county_manifest_scope.counties.{county_key} missing",
    )
    provenance = _require_mapping(
        provenance_payload,
        f"selected_county_source_provenance_scope.counties.{county_key} missing",
    )
    county_label = _require_text(manifest.get("county_label"), f"{county_key} label missing")
    source_manifest = _require_text(
        manifest.get("source_manifest"),
        f"{county_key} source manifest missing",
    )
    _require_existing(root, source_manifest)
    source_map = _require_mapping(
        provenance.get("sources"),
        f"selected_county_source_provenance_scope.counties.{county_key}.sources missing",
    )
    if set(source_map) != set(EXPECTED_SELECTED_SOURCE_IDS):
        unknown = sorted(set(source_map) - set(EXPECTED_SELECTED_SOURCE_IDS))
        missing = sorted(set(EXPECTED_SELECTED_SOURCE_IDS) - set(source_map))
        raise SourceProvenanceError(
            f"{county_key} selected source keys mismatch; unknown={unknown} missing={missing}"
        )
    sources = tuple(
        _county_source(source_id, source_map[source_id], record_by_source_id, county_key)
        for source_id in EXPECTED_SELECTED_SOURCE_IDS
    )
    return CountyProvenance(
        county_key=county_key,
        county_label=county_label,
        source_manifest=source_manifest,
        sources=sources,
    )


def _county_source(
    source_id: str,
    payload: Any,
    record_by_source_id: dict[str, SourceReadinessRecord],
    county_key: str,
) -> CountySourceProvenance:
    entry = _require_mapping(
        payload,
        f"selected_county_source_provenance_scope.counties.{county_key}.{source_id} missing",
    )
    _require_exact_text(
        entry.get("source_registry_id"),
        source_id,
        f"{county_key} {source_id} source_registry_id",
    )
    record = record_by_source_id.get(source_id)
    if record is None:
        raise SourceProvenanceError(f"{source_id} missing from Must-source readiness")
    connector_names = _require_text_tuple(
        entry.get("connector_names"),
        f"{county_key} {source_id} connector_names missing",
        allow_empty=True,
    )
    dataset_expectation = _enum_value(entry, "dataset_expectation", "dataset")
    version_expectation = _enum_value(entry, "version_expectation", "version")
    retrieval_expectation = _enum_value(entry, "retrieval_expectation", "retrieval")
    out_of_scope = _require_bool(
        entry.get("out_of_scope"),
        f"{county_key} {source_id} out_of_scope missing",
    )
    out_of_scope_reason = _optional_text(entry.get("out_of_scope_reason")) or ""

    if out_of_scope:
        if connector_names:
            raise SourceProvenanceError(f"{county_key} {source_id} out-of-scope has connectors")
        if not out_of_scope_reason:
            raise SourceProvenanceError(f"{county_key} {source_id} out-of-scope reason missing")
        if {
            dataset_expectation,
            version_expectation,
            retrieval_expectation,
        } != {"not_required_out_of_scope"}:
            raise SourceProvenanceError(
                f"{county_key} {source_id} out-of-scope expectations must be not_required"
            )
    else:
        if not connector_names:
            raise SourceProvenanceError(f"{county_key} {source_id} connector_names empty")
        if "not_required_out_of_scope" in {
            dataset_expectation,
            version_expectation,
            retrieval_expectation,
        }:
            raise SourceProvenanceError(
                f"{county_key} {source_id} in-scope expectations cannot be not_required"
            )
        if not set(connector_names).issubset(set(record.connector_names)):
            raise SourceProvenanceError(f"{county_key} {source_id} connector_names mismatch")

    if county_key == "buncombe_nc" and source_id == "DS-023" and not out_of_scope:
        raise SourceProvenanceError("Buncombe DS-023 must remain explicitly out of scope")

    return CountySourceProvenance(
        source_registry_id=source_id,
        source_name=record.name,
        connector_names=tuple(connector_names),
        dataset_expectation=dataset_expectation,
        version_expectation=version_expectation,
        retrieval_expectation=retrieval_expectation,
        out_of_scope=out_of_scope,
        out_of_scope_reason=out_of_scope_reason,
        readiness_connector_ready=record.connector_ready,
        readiness_blocked_fields=record.blocked_fields,
    )


def _expectation_enums(payload: dict[str, Any]) -> dict[str, tuple[str, ...]]:
    raw = _require_mapping(payload.get("expectation_enums"), "expectation_enums missing")
    if set(raw) != set(EXPECTED_ENUMS):
        raise SourceProvenanceError("expectation enum keys mismatch")
    parsed: dict[str, tuple[str, ...]] = {}
    for key, expected_values in EXPECTED_ENUMS.items():
        values = _require_text_tuple(raw.get(key), f"expectation_enums.{key} missing")
        if set(values) != expected_values:
            raise SourceProvenanceError(f"expectation_enums.{key} values mismatch")
        parsed[key] = tuple(sorted(values))
    return parsed


def _ds017_blocker(
    record_by_source_id: dict[str, SourceReadinessRecord],
) -> SourceReadinessRecord:
    record = record_by_source_id.get(EXPECTED_DS017_BLOCKER)
    if record is None:
        raise SourceProvenanceError("DS-017 missing from Must-source readiness")
    if record.connector_ready:
        raise SourceProvenanceError("DS-017 must remain blocked")
    required_blockers = {"license_status", "connector_implemented"}
    if not required_blockers.issubset(set(record.blocked_fields)):
        raise SourceProvenanceError("DS-017 blocker fields changed")
    return record


def _summary(record: SourceReadinessRecord) -> SourceReadinessSummary:
    return SourceReadinessSummary(
        source_registry_id=record.source_registry_id,
        name=record.name,
        domain=record.domain,
        review_status=record.review_status,
        license_status=record.license_status,
        connector_ready=record.connector_ready,
        connector_names=record.connector_names,
        blocked_fields=record.blocked_fields,
    )


def _row_to_source(row: dict[str, str]) -> SourceContract:
    return SourceContract(
        name=row["Name"],
        organization=_optional_text(row.get("Organization")),
        source_type=_optional_text(row.get("Source Type")),
        domain=row["Domain"],
        geographic_scope=_optional_text(row.get("Geography")),
        update_cadence=_optional_text(row.get("Update Cadence")),
        license_status=row["License Status"],
        commercial_use_status=row["Commercial Use Status"],
        redistribution_status=row["Redistribution Status"],
        license_summary=_optional_text(row.get("Caveats")),
        attribution_required=row.get("Attribution Required", "").strip().lower() == "yes",
        cache_allowed=row["Cache Allowed"],
        export_allowed=row["Export Allowed"],
        ai_use_allowed=row["AI Use Status"],
        raw_data_allowed=row["Raw Data Allowed"],
        freshness_class=row["Freshness Class"],
        last_checked_at=_optional_text(row.get("Last Checked At")),
        review_owner=_optional_text(row.get("Review Owner")),
        review_status=row["Review Status"],
        notes=_optional_text(row.get("Use")),
        metadata={
            "source_registry_id": row["Source ID"],
            "mvp_priority": row["MVP Priority"],
        },
    )


def _read_yaml(path: Path) -> dict[str, Any]:
    label = _catalog_label(path)
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise SourceProvenanceError(f"cannot read {label}") from exc
    return _require_mapping(payload, f"{label} must be a mapping")


def _read_registry(path: Path) -> list[dict[str, str]]:
    label = _catalog_label(path)
    try:
        with path.open(newline="", encoding="utf-8") as csv_file:
            rows = [dict(row) for row in csv.DictReader(csv_file)]
    except OSError as exc:
        raise SourceProvenanceError(f"cannot read {label}") from exc
    if not rows:
        raise SourceProvenanceError(f"{label} has no source rows")
    return rows


def _require_existing(root: Path, path_text: str) -> None:
    path = _resolved_repo_path(root, path_text)
    if not path.exists():
        raise SourceProvenanceError(f"referenced source-provenance artifact missing: {path_text}")


def _resolved_repo_path(root: Path, path_text: str) -> Path:
    if not path_text:
        raise SourceProvenanceError("empty path reference")
    candidate = Path(path_text.replace("\\", "/"))
    if candidate.is_absolute():
        raise SourceProvenanceError(f"path must be repo-relative: {path_text}")
    root_resolved = root.resolve()
    resolved = (root_resolved / candidate).resolve()
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise SourceProvenanceError(f"path escapes repo root: {path_text}") from exc
    return resolved


def _require_mapping(value: Any, message: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SourceProvenanceError(message)
    return value


def _require_list(value: Any, message: str, *, allow_empty: bool = False) -> list[Any]:
    if not isinstance(value, list):
        raise SourceProvenanceError(message)
    if not allow_empty and not value:
        raise SourceProvenanceError(message)
    return value


def _require_text(value: Any, message: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SourceProvenanceError(message)
    return value.strip()


def _require_exact_text(value: Any, expected: str, label: str) -> str:
    text = _require_text(value, f"{label} missing")
    if text != expected:
        raise SourceProvenanceError(f"{label} must be {expected}")
    return text


def _require_text_tuple(
    value: Any,
    message: str,
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    values = _require_list(value, message, allow_empty=allow_empty)
    return tuple(_require_text(item, message) for item in values)


def _require_bool(value: Any, message: str) -> bool:
    if not isinstance(value, bool):
        raise SourceProvenanceError(message)
    return value


def _enum_value(payload: dict[str, Any], field: str, enum_key: str) -> str:
    value = _require_text(payload.get(field), f"{field} missing")
    if value not in EXPECTED_ENUMS[enum_key]:
        raise SourceProvenanceError(f"{field} value mismatch")
    return value


def _optional_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _catalog_label(path: Path) -> str:
    parts = path.parts
    if len(parts) >= 2:
        return f"{parts[-2]}/{parts[-1]}"
    return path.name
