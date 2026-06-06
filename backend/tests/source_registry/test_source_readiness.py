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
    assert county_gis.blocked_fields == (
        "review_status",
        "license_status",
        "commercial_use_status",
        "redistribution_status",
        "cache_allowed",
        "export_allowed",
        "raw_data_allowed",
        "ai_use_allowed",
    )


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
    assert payload["ready_count"] == 4
    assert payload["blocked_count"] == 4
    ready_sources = [
        source for source in payload["sources"] if source["connector_ready"] is True
    ]
    assert [source["source_registry_id"] for source in ready_sources] == [
        "DS-001",
        "DS-002",
        "DS-003",
        "DS-004",
    ]


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
    assert "ready=4" in result.stdout


def test_source_readiness_require_ready_fails_when_selected_scope_has_none_ready() -> None:
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

    assert result.returncode == 2
    assert "ready=0" in result.stdout
