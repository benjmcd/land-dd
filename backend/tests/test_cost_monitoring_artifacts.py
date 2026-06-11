from __future__ import annotations

import csv
import importlib
import json
from pathlib import Path
from typing import Any, cast

yaml = cast(Any, importlib.import_module("yaml"))

REPO_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_CATEGORIES = {"compute", "storage", "llm", "maps", "geocoding", "data_vendors"}
REQUIRED_COST_METRICS = {
    "evidence_count",
    "claim_count",
    "unknown_count",
    "red_flag_count",
    "verification_task_count",
    "estimated_total_usd_cents",
    "compute_usd_cents",
    "storage_usd_cents",
    "llm_usd_cents",
    "map_tile_usd_cents",
    "geocoding_usd_cents",
    "paid_data_usd_cents",
    "human_review_usd_cents",
    "human_review_minutes",
}


def test_cost_monitoring_catalog_covers_l10_cost_categories() -> None:
    catalog = yaml.safe_load(
        (REPO_ROOT / "config" / "ops_cost_monitoring.yaml").read_text(encoding="utf-8"),
    )

    assert catalog["schema_version"] == "ops_cost_monitoring_v1"
    assert catalog["incident_runbook"] == "docs/runbooks/incident_response.md"
    assert catalog["operator_runbook"] == "docs/runbooks/cost_monitoring.md"
    categories = catalog["categories"]
    category_ids = {category["id"] for category in categories}
    assert REQUIRED_CATEGORIES.issubset(category_ids)

    for category in categories:
        assert category["status"]
        assert category["meter"]
        assert category["source_of_truth"]
        assert category["threshold"]
        assert category["action"]
        assert category["validation"] == "scripts/run_cost_monitoring_check.ps1"


def test_report_schema_cost_metrics_remain_required_and_non_negative() -> None:
    schema = json.loads(
        (REPO_ROOT / "schemas" / "report_run_schema.json").read_text(encoding="utf-8"),
    )
    cost_metrics = schema["properties"]["artifact_metadata"]["properties"]["cost_metrics"]

    assert REQUIRED_COST_METRICS.issubset(set(cost_metrics["required"]))
    for name in REQUIRED_COST_METRICS:
        metric = cost_metrics["properties"][name]
        assert metric["type"] == "integer"
        assert metric["minimum"] == 0


def test_planning_cost_inputs_cover_current_monitoring_categories() -> None:
    with (REPO_ROOT / "docs" / "planning_pack" / "registers" / "cost_model_inputs.csv").open(
        newline="",
        encoding="utf-8",
    ) as handle:
        rows = list(csv.DictReader(handle))

    categories = {row["Category"] for row in rows}
    assert {"Data", "Compute", "LLM", "Human QA", "Map", "Storage"}.issubset(categories)


def test_cost_monitoring_runbook_records_limits_and_validation() -> None:
    runbook = (REPO_ROOT / "docs" / "runbooks" / "cost_monitoring.md").read_text(
        encoding="utf-8",
    )

    for phrase in (
        "run_cost_monitoring_check.ps1",
        "scripts/cost_monitoring_check.py",
        "cost_metrics",
        "compute",
        "storage",
        "LLM",
        "Maps",
        "Geocoding",
        "Data vendors",
        "No hosted cloud billing integration",
        "zero-dollar attribution",
        "human_review_minutes",
    ):
        assert phrase in runbook


def test_cost_monitoring_scripts_exist_for_windows_and_posix() -> None:
    assert (REPO_ROOT / "scripts" / "cost_monitoring_check.py").is_file()
    assert (REPO_ROOT / "scripts" / "run_cost_monitoring_check.ps1").is_file()
    assert (REPO_ROOT / "scripts" / "run_cost_monitoring_check.sh").is_file()


def test_cost_monitoring_wrappers_delegate_to_shared_validator() -> None:
    for script_name in ("run_cost_monitoring_check.ps1", "run_cost_monitoring_check.sh"):
        script = (REPO_ROOT / "scripts" / script_name).read_text(encoding="utf-8")

        assert "cost_monitoring_check.py" in script
