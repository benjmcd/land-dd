from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

from app.domain.source_contracts import SourceContract


def _load_seed_module() -> ModuleType:
    root_dir = Path(__file__).resolve().parents[3]
    module_path = root_dir / "db" / "seeds" / "source_registry_seeds.py"
    spec = importlib.util.spec_from_file_location("source_registry_seeds", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_must_priority_seed_sources_match_registry_rows() -> None:
    module = _load_seed_module()

    seeds = module.load_seed_sources()

    assert len(seeds) == 8
    assert {source.metadata["source_registry_id"] for source in seeds} == {
        "DS-001",
        "DS-002",
        "DS-003",
        "DS-004",
        "DS-010",
        "DS-011",
        "DS-017",
        "DS-023",
    }


def test_seed_sources_are_valid_source_contracts() -> None:
    module = _load_seed_module()

    seeds = module.load_seed_sources()

    assert all(isinstance(source, SourceContract) for source in seeds)
    assert all(source.metadata["mvp_priority"] == "Must" for source in seeds)

    by_registry_id = {
        str(source.metadata["source_registry_id"]): source for source in seeds
    }
    assert by_registry_id["DS-002"].review_status == "approved"
    assert by_registry_id["DS-002"].freshness_class == "reviewed"
    assert all(
        source.review_status == "pending"
        for source_id, source in by_registry_id.items()
        if source_id != "DS-002"
    )
    assert all(
        source.freshness_class == "unreviewed"
        for source_id, source in by_registry_id.items()
        if source_id != "DS-002"
    )


def test_fema_nfhl_seed_preserves_reviewed_usage_status() -> None:
    module = _load_seed_module()

    seeds = module.load_seed_sources()
    fema = next(
        source for source in seeds if source.metadata["source_registry_id"] == "DS-002"
    )

    assert fema.license_status == "approved"
    assert fema.commercial_use_status == "approved"
    assert fema.redistribution_status == "approved"
    assert fema.cache_allowed == "approved"
    assert fema.export_allowed == "approved"
    assert fema.ai_use_allowed == "approved"
    assert fema.raw_data_allowed == "approved"
    assert fema.attribution_required is True
    assert fema.last_checked_at == "2026-06-05"
    assert fema.review_owner == "data-governance"


def test_seed_metadata_preserves_registry_context() -> None:
    module = _load_seed_module()

    seeds = module.load_seed_sources()
    county_gis = next(
        source for source in seeds if source.metadata["source_registry_id"] == "DS-010"
    )

    assert county_gis.homepage_url is None
    assert county_gis.metadata["raw_url"] == "Varies"
    assert county_gis.source_type == "Local official/varies"
    assert county_gis.license_status == "unknown"
    assert county_gis.redistribution_status == "unknown"
    assert county_gis.metadata["review_owner"] == "unassigned"
    assert county_gis.license_summary == "Approximate; not survey"


def test_commercial_blocker_seed_fails_closed_for_usage_statuses() -> None:
    module = _load_seed_module()

    seeds = module.load_seed_sources()
    vendor = next(
        source for source in seeds if source.metadata["source_registry_id"] == "DS-017"
    )

    assert vendor.license_status == "blocked"
    assert vendor.commercial_use_status == "blocked"
    assert vendor.cache_allowed == "blocked"
    assert vendor.export_allowed == "blocked"
    assert vendor.ai_use_allowed == "blocked"
    assert vendor.raw_data_allowed == "blocked"


def test_seed_sources_have_unique_name_organization_pairs() -> None:
    module = _load_seed_module()

    seeds = module.load_seed_sources()
    pairs = {(source.name, source.organization) for source in seeds}

    assert len(pairs) == len(seeds)
