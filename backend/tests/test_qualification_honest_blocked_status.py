from __future__ import annotations

import ast
import importlib
from pathlib import Path
from typing import Any, cast

yaml = cast(Any, importlib.import_module("yaml"))

REPO_ROOT = Path(__file__).resolve().parents[2]
DOMAIN_DIR = REPO_ROOT / "config" / "qualification" / "domain_profiles"
SOURCE_DIR = REPO_ROOT / "config" / "qualification" / "source_profiles"
DOMAIN_ARCHIVE = REPO_ROOT / "archive" / "2026-06-21_eq3-domain-stubs"
SOURCE_ARCHIVE = REPO_ROOT / "archive" / "2026-06-21_eq3-source-stub"
OLD_DOMAIN_STUBS = {
    "environmental_context.yaml",
    "flood.yaml",
    "physical_road_access_proxy.yaml",
    "slope_terrain.yaml",
    "soils_septic_proxy.yaml",
    "source_availability_and_conflict.yaml",
    "wetlands.yaml",
    "zoning_context.yaml",
}


def _load_yaml(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], yaml.safe_load(path.read_text(encoding="utf-8")))


def _production_usage_fields() -> tuple[str, ...]:
    usage_rights = (
        REPO_ROOT / "backend" / "app" / "source_registry" / "usage_rights.py"
    ).read_text(encoding="utf-8")
    module = ast.parse(usage_rights)
    for node in module.body:
        if not isinstance(node, ast.AnnAssign):
            continue
        target = node.target
        if isinstance(target, ast.Name) and target.id == "PRODUCTION_USAGE_FIELDS":
            assert node.value is not None
            return tuple(cast(tuple[str, ...], ast.literal_eval(node.value)))
    raise AssertionError("PRODUCTION_USAGE_FIELDS not found")


def test_p0_is_honestly_blocked_without_result_artifact() -> None:
    status = _load_yaml(REPO_ROOT / "state" / "EMPIRICAL_QUALIFICATION_STATUS.yaml")
    p0 = status["qualifications"]["p0"]

    assert status["highest_valid_classification"] == "L9-R"
    assert p0["status"] == "BLOCKED"
    assert p0["result_path"] is None
    assert p0["expires_at"] is None
    assert p0["blocked_reason"].strip()
    assert p0["blocker_references"] == [
        "state/QUALIFICATION_PARAMETERIZATION_BACKLOG.md",
        "docs/qualification/PROJECT_PARAMETERIZATION_BLOCKERS.md",
    ]
    for reference in p0["blocker_references"]:
        assert (REPO_ROOT / reference).exists(), reference

    candidate = status["candidate"]
    assert candidate["commit"] is None
    assert candidate["artifact_digest"] is None


def test_active_domain_profiles_are_template_only_with_stubs_archived() -> None:
    active_profiles = sorted(path.name for path in DOMAIN_DIR.glob("*.yaml"))
    assert active_profiles == ["domain_profile.template.yaml"]

    template = _load_yaml(DOMAIN_DIR / "domain_profile.template.yaml")
    assert template["schema_version"] == "domain_qualification_profile_v3"
    assert template["domain_id"] == "domain_profile_template"
    assert template["status"] == "DRAFT"
    assert template["approved_by"] == []
    assert template["frozen_at"] is None

    archived = {path.name for path in DOMAIN_ARCHIVE.glob("*.yaml")}
    assert archived == OLD_DOMAIN_STUBS


def test_active_source_profile_is_real_ds002_and_maps_production_usage_fields() -> None:
    active_profiles = sorted(path.name for path in SOURCE_DIR.glob("*.yaml"))
    assert active_profiles == ["source_quality_profile.ds-002.yaml"]
    assert (SOURCE_ARCHIVE / "example_source.yaml").exists()

    profile = _load_yaml(SOURCE_DIR / "source_quality_profile.ds-002.yaml")
    assert profile["schema_version"] == "source_quality_profile_v3"
    assert profile["source_id"] == "DS-002"
    assert profile["status"] == "APPROVED"
    assert profile["approved_by"] == ["data-governance"]

    usage_field_mapping = profile["production_usage_field_mapping"]
    assert tuple(usage_field_mapping) == _production_usage_fields()
    assert usage_field_mapping == {
        "license_status": "authority.license_status",
        "commercial_use_status": "rights.commercial_use",
        "redistribution_status": "rights.redistribute",
        "cache_allowed": "rights.cache",
        "export_allowed": "rights.export",
        "raw_data_allowed": "rights.raw_data",
        "ai_use_allowed": "rights.ai_use",
    }
    assert profile["rights"]["raw_data"] != "UNKNOWN"

    assert "backend/app/source_registry/usage_rights.py" in profile["conditions_enforced_by"]
    assert "registers/license-reviews/ds-002-fema-nfhl.md" in profile[
        "conditions_enforced_by"
    ]
    source_review = (
        REPO_ROOT / "registers" / "license-reviews" / "ds-002-fema-nfhl.md"
    ).read_text(encoding="utf-8")
    assert "Approved for MVP production use? yes" in source_review
