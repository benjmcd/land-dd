from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any, cast

yaml = cast(Any, importlib.import_module("yaml"))

REPO_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_IDS = {"report_runs", "evidence_observations", "audit_events", "source_ingest_runs"}
REQUIRED_FIELDS = {"id", "description", "retention_period", "deletion_approach", "blocker"}


def test_data_retention_catalog_exists() -> None:
    assert (REPO_ROOT / "config" / "data_retention.yaml").is_file()


def test_data_retention_catalog_schema_version() -> None:
    catalog = yaml.safe_load(
        (REPO_ROOT / "config" / "data_retention.yaml").read_text(encoding="utf-8"),
    )
    assert catalog["schema_version"] == "data_retention_v1"


def test_data_retention_catalog_has_at_least_six_classes() -> None:
    catalog = yaml.safe_load(
        (REPO_ROOT / "config" / "data_retention.yaml").read_text(encoding="utf-8"),
    )
    classes = catalog["retention_classes"]
    assert isinstance(classes, list)
    assert len(classes) >= 6


def test_data_retention_classes_have_required_fields() -> None:
    catalog = yaml.safe_load(
        (REPO_ROOT / "config" / "data_retention.yaml").read_text(encoding="utf-8"),
    )
    for cls in catalog["retention_classes"]:
        missing = REQUIRED_FIELDS - set(cls.keys())
        cls_id = cls.get("id", "?")
        assert not missing, f"retention class {cls_id} missing fields: {sorted(missing)}"


def test_data_retention_catalog_includes_required_ids() -> None:
    catalog = yaml.safe_load(
        (REPO_ROOT / "config" / "data_retention.yaml").read_text(encoding="utf-8"),
    )
    ids = {cls["id"] for cls in catalog["retention_classes"]}
    missing = REQUIRED_IDS - ids
    assert not missing, f"retention_classes missing required ids: {sorted(missing)}"


def test_data_retention_runbook_exists_and_mentions_90_days() -> None:
    runbook_path = REPO_ROOT / "docs" / "runbooks" / "data_retention.md"
    assert runbook_path.is_file()
    content = runbook_path.read_text(encoding="utf-8")
    assert "90" in content


def test_data_retention_check_ps1_exists() -> None:
    assert (REPO_ROOT / "scripts" / "run_data_retention_check.ps1").is_file()
