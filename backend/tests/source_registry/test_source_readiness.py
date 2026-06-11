from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_readiness_module() -> ModuleType:
    module_path = _repo_root() / "scripts" / "source_readiness.py"
    spec = importlib.util.spec_from_file_location("source_readiness", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_seed_module() -> ModuleType:
    module_path = _repo_root() / "db" / "seeds" / "source_registry_seeds.py"
    spec = importlib.util.spec_from_file_location("source_registry_seeds", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


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

    records = readiness.build_readiness_records(seed_module.load_registry_sources())

    assert len(records) == 25
    ready = [record for record in records if record.connector_ready]
    assert [record.source_registry_id for record in ready] == [
        "DS-001",
        "DS-002",
        "DS-003",
        "DS-004",
        "DS-005",
        "DS-006",
        "DS-010",
        "DS-011",
        "DS-016",
        "DS-020",
        "DS-021",
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

    record = readiness.build_readiness_records([source])[0]

    assert record.production_use_allowed is True
    assert record.connector_implemented is True
    assert record.connector_surfaces == (
        "immediate_operator_api",
        "request_time_orchestration",
    )
    assert record.connector_ready is True
    assert record.blocked_fields == ()


def test_source_readiness_json_reports_blocked_sources() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/source_readiness.py",
            "--priority",
            "Must",
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
    assert ds011["connector_implemented"] is True
    assert "immediate_operator_api" in ds011["connector_surfaces"]
    assert ds011["connector_ready"] is True
    ds023 = next(
        source
        for source in payload["sources"]
        if source["source_registry_id"] == "DS-023"
    )
    assert ds023["connector_implemented"] is True
    assert "immediate_operator_api" in ds023["connector_surfaces"]
    assert ds023["connector_ready"] is True


def test_source_readiness_require_ready_passes_when_candidate_is_ready() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/source_readiness.py",
            "--priority",
            "Must",
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
