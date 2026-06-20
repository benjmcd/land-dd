from __future__ import annotations

import importlib
import importlib.util
import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from types import ModuleType
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_readiness_module() -> ModuleType:
    return importlib.import_module("app.source_registry.readiness")


def _load_seed_module() -> ModuleType:
    module_path = _repo_root() / "db" / "seeds" / "source_registry_seeds.py"
    spec = importlib.util.spec_from_file_location("source_registry_seeds", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _must_source(source_id: str) -> Any:
    seed_module = _load_seed_module()
    return next(
        source
        for source in seed_module.load_registry_sources(priority="Must")
        if source.metadata["source_registry_id"] == source_id
    )


def _with_review_metadata(
    source: Any,
    *,
    freshness_class: str = "current-effective",
    last_checked_at: str | None = "2026-06-05",
    review_owner: str | None = "operator",
) -> Any:
    metadata = {
        **source.metadata,
        "freshness_class": freshness_class,
        "last_checked_at": last_checked_at,
        "review_owner": review_owner,
    }
    return source.model_copy(
        update={
            "freshness_class": freshness_class,
            "last_checked_at": last_checked_at,
            "review_owner": review_owner,
            "metadata": metadata,
        }
    )


def _single_record(source: Any) -> Any:
    readiness = _load_readiness_module()
    return readiness.build_readiness_records(
        [source],
        as_of=date(2026, 6, 18),
    )[0]


def test_source_readiness_records_are_owned_by_packaged_module() -> None:
    readiness = _load_readiness_module()

    assert readiness.__file__ is not None
    assert Path(readiness.__file__).as_posix().endswith(
        "backend/app/source_registry/readiness.py"
    )
    assert hasattr(readiness, "build_readiness_records")


def test_load_registry_sources_defaults_to_all_registry_rows() -> None:
    seed_module = _load_seed_module()

    sources = seed_module.load_registry_sources()

    assert len(sources) == 25
    assert {source.metadata["source_registry_id"] for source in sources} >= {
        "DS-001",
        "DS-025",
    }


def test_readiness_records_surface_current_ready_and_blocked_sources() -> None:
    readiness = _load_readiness_module()
    seed_module = _load_seed_module()

    records = readiness.build_readiness_records(
        seed_module.load_registry_sources(),
        as_of=date(2026, 6, 18),
    )

    assert len(records) == 25
    ready = [record for record in records if record.connector_ready]
    assert [record.source_registry_id for record in ready] == [
        "DS-001",
        "DS-002",
        "DS-003",
        "DS-004",
        "DS-005",
        "DS-006",
        "DS-007",
        "DS-008",
        "DS-010",
        "DS-011",
        "DS-015",
        "DS-016",
        "DS-020",
        "DS-021",
        "DS-022",
        "DS-023",
    ]
    usgs = next(record for record in records if record.source_registry_id == "DS-001")
    assert usgs.blocked_fields == ()
    fema = next(record for record in records if record.source_registry_id == "DS-002")
    assert fema.blocked_fields == ()
    usda = next(record for record in records if record.source_registry_id == "DS-003")
    assert usda.blocked_fields == ()
    nwi = next(record for record in records if record.source_registry_id == "DS-004")
    assert nwi.blocked_fields == ()
    county_gis = next(record for record in records if record.source_registry_id == "DS-010")
    assert county_gis.blocked_fields == ()
    assert county_gis.production_use_allowed is True
    assert county_gis.connector_implemented is True
    assert county_gis.connector_surfaces == (
        "immediate_operator_api",
        "request_time_orchestration",
    )
    assert "durable_live_job" not in county_gis.connector_surfaces
    blm_mlrs = next(record for record in records if record.source_registry_id == "DS-007")
    assert blm_mlrs.blocked_fields == ()
    assert blm_mlrs.production_use_allowed is True
    assert blm_mlrs.connector_implemented is True
    assert blm_mlrs.connector_surfaces == (
        "immediate_operator_api",
        "request_time_orchestration",
    )
    assert blm_mlrs.connector_ready is True
    mrds = next(record for record in records if record.source_registry_id == "DS-008")
    assert mrds.blocked_fields == ()
    assert mrds.production_use_allowed is True
    assert mrds.connector_implemented is True
    assert mrds.connector_surfaces == (
        "immediate_operator_api",
        "request_time_orchestration",
    )
    assert mrds.connector_ready is True
    nc_geology = next(record for record in records if record.source_registry_id == "DS-015")
    assert nc_geology.blocked_fields == ()
    assert nc_geology.production_use_allowed is True
    assert nc_geology.connector_implemented is True
    assert nc_geology.connector_surfaces == (
        "immediate_operator_api",
        "request_time_orchestration",
    )
    assert nc_geology.connector_ready is True
    census_tiger = next(record for record in records if record.source_registry_id == "DS-022")
    assert census_tiger.blocked_fields == ()
    assert census_tiger.production_use_allowed is True
    assert census_tiger.connector_implemented is True
    assert census_tiger.connector_surfaces == (
        "immediate_operator_api",
        "request_time_orchestration",
    )
    assert census_tiger.connector_ready is True


def test_must_source_readiness_baseline_preserves_review_freshness_fields() -> None:
    readiness = _load_readiness_module()
    seed_module = _load_seed_module()

    records = readiness.build_readiness_records(
        seed_module.load_registry_sources(priority="Must"),
        as_of=date(2026, 6, 18),
    )

    assert len(records) == 8
    assert sum(1 for record in records if record.connector_ready) == 7
    blocked = [record for record in records if not record.connector_ready]
    assert [record.source_registry_id for record in blocked] == ["DS-017"]

    ds001 = next(record for record in records if record.source_registry_id == "DS-001")
    assert ds001.freshness_class == "current-effective"
    assert ds001.last_checked_at == "2026-06-05"
    assert ds001.last_checked_age_days == 13
    assert ds001.stale_after_days == 90
    assert ds001.review_owner == "operator"
    assert ds001.review_freshness_allowed is True
    assert ds001.review_freshness_blocked_fields == ()

    ds017 = blocked[0]
    assert ds017.source_registry_id == "DS-017"
    assert ds017.connector_ready is False
    assert ds017.review_freshness_blocked_fields == ()
    assert "last_checked_at" not in ds017.blocked_fields


def test_must_current_effective_source_blocks_stale_last_checked_at() -> None:
    source = _with_review_metadata(_must_source("DS-001"), last_checked_at="2026-03-19")

    record = _single_record(source)

    assert record.connector_ready is False
    assert record.review_freshness_allowed is False
    assert record.last_checked_age_days == 91
    assert record.review_freshness_blocked_fields == ("last_checked_at",)
    assert record.blocked_fields == ("last_checked_at",)


def test_must_current_effective_source_allows_exactly_90_day_last_checked_at() -> None:
    source = _with_review_metadata(_must_source("DS-001"), last_checked_at="2026-03-20")

    record = _single_record(source)

    assert record.connector_ready is True
    assert record.review_freshness_allowed is True
    assert record.last_checked_age_days == 90
    assert record.review_freshness_blocked_fields == ()
    assert record.blocked_fields == ()


def test_must_current_effective_source_blocks_missing_last_checked_at() -> None:
    source = _with_review_metadata(_must_source("DS-001"), last_checked_at=None)

    record = _single_record(source)

    assert record.connector_ready is False
    assert record.review_freshness_allowed is False
    assert record.last_checked_age_days is None
    assert record.review_freshness_blocked_fields == ("last_checked_at",)


def test_must_current_effective_source_blocks_malformed_last_checked_at() -> None:
    source = _with_review_metadata(_must_source("DS-001"), last_checked_at="not-a-date")

    record = _single_record(source)

    assert record.connector_ready is False
    assert record.review_freshness_allowed is False
    assert record.last_checked_age_days is None
    assert record.review_freshness_blocked_fields == ("last_checked_at",)


def test_must_current_effective_source_blocks_future_last_checked_at() -> None:
    source = _with_review_metadata(_must_source("DS-001"), last_checked_at="2026-06-19")

    record = _single_record(source)

    assert record.connector_ready is False
    assert record.review_freshness_allowed is False
    assert record.last_checked_age_days is None
    assert record.review_freshness_blocked_fields == ("last_checked_at",)


def test_must_current_effective_source_blocks_blank_or_unassigned_review_owner() -> None:
    blank_owner = _with_review_metadata(_must_source("DS-001"), review_owner=" ")
    unassigned_owner = _with_review_metadata(_must_source("DS-001"), review_owner="unassigned")

    blank_record = _single_record(blank_owner)
    unassigned_record = _single_record(unassigned_owner)

    assert blank_record.connector_ready is False
    assert blank_record.review_freshness_blocked_fields == ("review_owner",)
    assert unassigned_record.connector_ready is False
    assert unassigned_record.review_freshness_blocked_fields == ("review_owner",)


def test_otherwise_approved_must_source_blocks_unreviewed_freshness_class() -> None:
    source = _with_review_metadata(_must_source("DS-001"), freshness_class="unreviewed")

    record = _single_record(source)

    assert record.production_use_allowed is True
    assert record.connector_implemented is True
    assert record.connector_ready is False
    assert record.review_freshness_allowed is False
    assert record.review_freshness_blocked_fields == ("freshness_class",)
    assert record.blocked_fields == ("freshness_class",)


def test_ds017_stays_blocked_without_current_effective_last_checked_error() -> None:
    record = _single_record(_must_source("DS-017"))

    assert record.connector_ready is False
    assert record.production_use_allowed is False
    assert record.connector_implemented is False
    assert record.freshness_class == "unreviewed"
    assert record.last_checked_at is None
    assert record.review_owner == "unassigned"
    assert record.review_freshness_blocked_fields == ()
    assert "last_checked_at" not in record.blocked_fields


def test_ds011_assessor_not_evaluated_connector_is_implemented() -> None:
    readiness = _load_readiness_module()
    seed_module = _load_seed_module()

    # DS-011 now has an explicit NOT_EVALUATED connector (county_assessor_not_evaluated)
    # that records the absence of assessor data as auditable evidence.
    source = next(
        source
        for source in seed_module.load_registry_sources()
        if source.metadata["source_registry_id"] == "DS-011"
    )

    record = readiness.build_readiness_records(
        [source],
        as_of=date(2026, 6, 18),
    )[0]

    assert record.production_use_allowed is True
    assert record.connector_implemented is True
    assert record.connector_surfaces == (
        "immediate_operator_api",
        "request_time_orchestration",
    )
    assert record.connector_ready is True
    assert record.blocked_fields == ()


def test_readiness_records_expose_aggregate_selected_county_connector_scopes() -> None:
    readiness = _load_readiness_module()
    seed_module = _load_seed_module()

    records = readiness.build_readiness_records(
        seed_module.load_registry_sources(),
        as_of=date(2026, 6, 18),
    )
    county_gis = next(record for record in records if record.source_registry_id == "DS-010")
    zoning = next(record for record in records if record.source_registry_id == "DS-023")

    assert county_gis.connector_names == (
        "chatham_parcels_live",
        "buncombe_parcels_live",
        "brunswick_parcels_live",
    )
    assert county_gis.connector_scope_notes == (
        "Chatham County NC parcel screening only; no owner/value/title fields; "
        "durable live-job support not claimed.",
        "Buncombe County NC parcel screening only; no owner/value/title fields; "
        "durable live-job support not claimed.",
        "Brunswick County NC parcel screening only; no owner/value/title fields; "
        "durable live-job support not claimed.",
    )
    assert county_gis.connector_surfaces == (
        "immediate_operator_api",
        "request_time_orchestration",
    )

    assert zoning.connector_names == (
        "chatham_zoning_udo_recorded",
        "brunswick_zoning_udo_recorded",
    )
    assert zoning.connector_scope_notes == (
        "Chatham County NC recorded-fixture UDO district lookup only; not live "
        "PDF ingestion or legal zoning advice.",
        "Brunswick County NC recorded-fixture UDO district lookup only; not live "
        "PDF ingestion or legal zoning advice.",
    )
    assert zoning.connector_surfaces == (
        "immediate_operator_api",
        "request_time_orchestration",
    )


def test_source_readiness_json_reports_blocked_sources() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/source_readiness.py",
            "--priority",
            "Must",
            "--as-of",
            "2026-06-18",
            "--json",
        ],
        cwd=_repo_root(),
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["schema_version"] == "source_readiness_v1"
    assert payload["priority"] == "Must"
    assert payload["source_count"] == 8
    assert payload["ready_count"] == 7
    assert payload["blocked_count"] == 1
    ready_sources = [
        source for source in payload["sources"] if source["connector_ready"] is True
    ]
    assert [source["source_registry_id"] for source in ready_sources] == [
        "DS-001",
        "DS-002",
        "DS-003",
        "DS-004",
        "DS-010",
        "DS-011",
        "DS-023",
    ]
    ds011 = next(
        source
        for source in payload["sources"]
        if source["source_registry_id"] == "DS-011"
    )
    assert ds011["freshness_class"] == "current-effective"
    assert ds011["last_checked_at"] == "2026-06-10"
    assert ds011["last_checked_age_days"] == 8
    assert ds011["stale_after_days"] == 90
    assert ds011["review_owner"] == "operator"
    assert ds011["review_freshness_allowed"] is True
    assert ds011["review_freshness_blocked_fields"] == []
    assert ds011["connector_implemented"] is True
    assert "immediate_operator_api" in ds011["connector_surfaces"]
    assert ds011["connector_ready"] is True
    ds010 = next(
        source
        for source in payload["sources"]
        if source["source_registry_id"] == "DS-010"
    )
    assert ds010["connector_names"] == [
        "chatham_parcels_live",
        "buncombe_parcels_live",
        "brunswick_parcels_live",
    ]
    assert len(ds010["connector_scope_notes"]) == 3
    ds023 = next(
        source
        for source in payload["sources"]
        if source["source_registry_id"] == "DS-023"
    )
    assert ds023["connector_implemented"] is True
    assert "immediate_operator_api" in ds023["connector_surfaces"]
    assert ds023["connector_names"] == [
        "chatham_zoning_udo_recorded",
        "brunswick_zoning_udo_recorded",
    ]
    assert len(ds023["connector_scope_notes"]) == 2
    assert ds023["connector_ready"] is True
    ds017 = next(
        source
        for source in payload["sources"]
        if source["source_registry_id"] == "DS-017"
    )
    assert ds017["connector_ready"] is False
    assert ds017["freshness_class"] == "unreviewed"
    assert ds017["last_checked_at"] is None
    assert ds017["review_freshness_blocked_fields"] == []
    assert "last_checked_at" not in ds017["blocked_fields"]


def test_source_readiness_require_ready_passes_when_candidate_is_ready() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/source_readiness.py",
            "--priority",
            "Must",
            "--as-of",
            "2026-06-18",
            "--require-ready",
        ],
        cwd=_repo_root(),
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "ready=7" in result.stdout


def test_source_readiness_require_ready_passes_for_should_with_ds005_ds006_ds016() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/source_readiness.py",
            "--priority",
            "Should",
            "--require-ready",
        ],
        cwd=_repo_root(),
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "ready=3" in result.stdout
