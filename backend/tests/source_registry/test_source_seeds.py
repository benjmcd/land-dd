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
    assert {source.review_status for source in seeds} == {
        "approved-with-restrictions",
        "pending",
    }
    assert {source.freshness_class for source in seeds} == {
        "current-effective",
        "unreviewed",
    }


def test_fema_nfhl_seed_preserves_reviewed_restricted_rights() -> None:
    module = _load_seed_module()

    seeds = module.load_seed_sources()
    fema = next(
        source for source in seeds if source.metadata["source_registry_id"] == "DS-002"
    )

    assert fema.license_status == "approved-with-restrictions"
    assert fema.commercial_use_status == "restricted"
    assert fema.redistribution_status == "restricted"
    assert fema.cache_allowed == "restricted"
    assert fema.export_allowed == "approved-with-restrictions"
    assert fema.ai_use_allowed == "restricted"
    assert fema.raw_data_allowed == "restricted"
    assert fema.attribution_required is True
    assert fema.review_status == "approved-with-restrictions"
    assert fema.last_checked_at == "2026-06-05"


def test_usgs_national_map_seed_preserves_reviewed_restricted_rights() -> None:
    module = _load_seed_module()

    seeds = module.load_seed_sources()
    usgs = next(
        source for source in seeds if source.metadata["source_registry_id"] == "DS-001"
    )

    assert str(usgs.homepage_url) == "https://www.usgs.gov/nationalmap"
    assert usgs.license_status == "approved-with-restrictions"
    assert usgs.commercial_use_status == "approved-with-restrictions"
    assert usgs.redistribution_status == "approved-with-restrictions"
    assert usgs.cache_allowed == "approved-with-restrictions"
    assert usgs.export_allowed == "approved-with-restrictions"
    assert usgs.ai_use_allowed == "restricted"
    assert usgs.raw_data_allowed == "approved-with-restrictions"
    assert usgs.attribution_required is True
    assert usgs.update_cadence == "dynamic"
    assert usgs.freshness_class == "current-effective"
    assert usgs.review_status == "approved-with-restrictions"
    assert usgs.last_checked_at == "2026-06-05"


def test_usda_ssurgo_seed_preserves_reviewed_restricted_rights() -> None:
    module = _load_seed_module()

    seeds = module.load_seed_sources()
    usda = next(
        source for source in seeds if source.metadata["source_registry_id"] == "DS-003"
    )

    assert str(usda.homepage_url) == "https://websoilsurvey.nrcs.usda.gov/"
    assert usda.license_status == "approved-with-restrictions"
    assert usda.commercial_use_status == "approved-with-restrictions"
    assert usda.redistribution_status == "approved-with-restrictions"
    assert usda.cache_allowed == "approved-with-restrictions"
    assert usda.export_allowed == "approved-with-restrictions"
    assert usda.ai_use_allowed == "restricted"
    assert usda.raw_data_allowed == "approved-with-restrictions"
    assert usda.attribution_required is True
    assert usda.update_cadence == "annual"
    assert usda.freshness_class == "current-effective"
    assert usda.review_status == "approved-with-restrictions"
    assert usda.last_checked_at == "2026-06-05"


def test_nwi_seed_preserves_reviewed_restricted_rights() -> None:
    module = _load_seed_module()

    seeds = module.load_seed_sources()
    nwi = next(
        source for source in seeds if source.metadata["source_registry_id"] == "DS-004"
    )

    assert str(nwi.homepage_url) == "https://www.fws.gov/program/national-wetlands-inventory"
    assert nwi.license_status == "approved-with-restrictions"
    assert nwi.commercial_use_status == "approved-with-restrictions"
    assert nwi.redistribution_status == "approved-with-restrictions"
    assert nwi.cache_allowed == "approved-with-restrictions"
    assert nwi.export_allowed == "approved-with-restrictions"
    assert nwi.ai_use_allowed == "restricted"
    assert nwi.raw_data_allowed == "approved-with-restrictions"
    assert nwi.attribution_required is True
    assert nwi.update_cadence == "biannual"
    assert nwi.freshness_class == "current-effective"
    assert nwi.review_status == "approved-with-restrictions"
    assert nwi.last_checked_at == "2026-06-05"


def test_sql_seed_refreshes_first_class_usage_rights() -> None:
    sql_path = Path(__file__).resolve().parents[3] / "db" / "seeds" / (
        "002_seed_source_registry.sql"
    )
    sql = sql_path.read_text(encoding="utf-8")

    assert "attribution_required" in sql
    assert "'USGS The National Map', 'USGS'" in sql
    assert "'FEMA NFHL', 'FEMA'" in sql
    assert "'USDA Web Soil Survey/SSURGO', 'USDA NRCS'" in sql
    assert "'National Wetlands Inventory', 'USFWS'" in sql
    assert (
        "true, 'restricted', 'approved-with-restrictions', "
        "'approved-with-restrictions'"
    ) in sql
    assert "true, 'restricted', 'restricted', 'approved-with-restrictions'" in sql
    for column_name in (
        "commercial_use_status",
        "attribution_required",
        "ai_use_allowed",
        "cache_allowed",
        "export_allowed",
        "raw_data_allowed",
    ):
        assert f"{column_name} = EXCLUDED.{column_name}" in sql


def test_seed_metadata_preserves_registry_context() -> None:
    module = _load_seed_module()

    seeds = module.load_seed_sources()
    county_gis = next(
        source for source in seeds if source.metadata["source_registry_id"] == "DS-010"
    )

    assert county_gis.homepage_url is None
    assert county_gis.metadata["raw_url"] == "Varies"
    assert county_gis.source_type == "Local official/varies"
    assert county_gis.license_status == "approved-with-restrictions"
    assert county_gis.redistribution_status == "approved-with-restrictions"
    assert county_gis.metadata["review_owner"] == "operator"
    assert county_gis.license_summary.startswith("Parcel screening only")


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
