from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "config/ops_cost_monitoring.yaml",
    "docs/runbooks/cost_monitoring.md",
    "schemas/report_run_schema.json",
    "docs/planning_pack/registers/cost_model_inputs.csv",
    "registers/data_source_registry.csv",
    "scripts/source_readiness.py",
    "scripts/cost_monitoring_check.py",
    "scripts/run_cost_monitoring_check.ps1",
    "scripts/run_cost_monitoring_check.sh",
)
REQUIRED_CATEGORIES = {"compute", "storage", "llm", "maps", "geocoding", "data_vendors"}
REQUIRED_COST_INPUT_CATEGORIES = {"Data", "Compute", "LLM", "Human QA", "Map", "Storage"}
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


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def read_text(path_text: str) -> str:
    return (ROOT / path_text).read_text(encoding="utf-8")


def require_existing(path_text: str) -> None:
    normalized = path_text.replace("\\", "/")
    require((ROOT / normalized).exists(), f"referenced cost artifact missing: {normalized}")


def require_source_paths(category_id: str, payload: dict[str, Any]) -> None:
    source_paths = payload.get("source_of_truth")
    if not isinstance(source_paths, list) or not source_paths:
        raise SystemExit(f"{category_id} source_of_truth must be a list")

    for source_path in source_paths:
        if isinstance(source_path, str) and source_path.startswith(
            ("backend/", "config/", "docs/", "registers/", "schemas/", "scripts/"),
        ):
            require_existing(source_path)


def validate_required_files() -> None:
    for path_text in REQUIRED_FILES:
        require(
            (ROOT / path_text).is_file(),
            f"required cost-monitoring artifact missing: {path_text}",
        )


def validate_catalog() -> None:
    payload = yaml.safe_load(read_text("config/ops_cost_monitoring.yaml"))
    require(isinstance(payload, dict), "cost monitoring catalog must be a mapping")
    require(
        payload.get("schema_version") == "ops_cost_monitoring_v1",
        "unexpected cost monitoring schema",
    )
    require(
        payload.get("incident_runbook") == "docs/runbooks/incident_response.md",
        "incident runbook mismatch",
    )
    require(
        payload.get("operator_runbook") == "docs/runbooks/cost_monitoring.md",
        "operator runbook mismatch",
    )
    require_existing(str(payload.get("report_cost_metrics_authority", "")))
    require_existing(str(payload.get("planning_cost_inputs", "")))

    categories = payload.get("categories")
    if not isinstance(categories, list) or not categories:
        raise SystemExit("cost monitoring categories missing")

    ids: set[str] = set()
    for category in categories:
        require(isinstance(category, dict), "each cost category must be a mapping")
        category_id = category.get("id")
        require(isinstance(category_id, str) and bool(category_id), "cost category id missing")
        require(category_id not in ids, f"duplicate cost category id: {category_id}")
        ids.add(category_id)
        for field in (
            "status",
            "meter",
            "source_of_truth",
            "threshold",
            "action",
            "validation",
        ):
            require(field in category and bool(category[field]), f"{category_id} missing {field}")
        require_source_paths(category_id, category)
        validation = category["validation"]
        require(isinstance(validation, str), f"{category_id} validation must be a string")
        require_existing(validation)

    missing_categories = sorted(REQUIRED_CATEGORIES - ids)
    require(not missing_categories, f"missing cost categories: {missing_categories}")


def validate_report_cost_metrics_schema() -> None:
    schema = json.loads(read_text("schemas/report_run_schema.json"))
    artifact = schema["properties"]["artifact_metadata"]
    cost_metrics = artifact["properties"]["cost_metrics"]
    required = set(cost_metrics["required"])
    require(REQUIRED_COST_METRICS.issubset(required), "report cost_metrics required fields missing")
    for name in REQUIRED_COST_METRICS:
        metric = cost_metrics["properties"][name]
        require(metric.get("type") == "integer", f"{name} must be integer")
        require(metric.get("minimum") == 0, f"{name} must be non-negative")


def validate_planning_cost_inputs() -> None:
    with (ROOT / "docs" / "planning_pack" / "registers" / "cost_model_inputs.csv").open(
        newline="",
        encoding="utf-8",
    ) as handle:
        rows = list(csv.DictReader(handle))

    categories = {row.get("Category", "") for row in rows}
    missing_categories = sorted(REQUIRED_COST_INPUT_CATEGORIES - categories)
    require(
        not missing_categories,
        f"planning cost input categories missing: {missing_categories}",
    )


def validate_vendor_sources_stay_blocked() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/source_readiness.py", "--priority", "Must", "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    require(
        payload.get("schema_version") == "source_readiness_v1",
        "source readiness schema mismatch",
    )
    commercial = [
        source
        for source in payload.get("sources", [])
        if str(source.get("source_registry_id")) == "DS-017"
    ]
    require(
        bool(commercial),
        "DS-017 commercial parcel vendor missing from Must source readiness",
    )
    ds017 = commercial[0]
    require(
        ds017.get("connector_ready") is False,
        "DS-017 must remain blocked without vendor cost/license review",
    )
    blocked_fields = set(ds017.get("blocked_fields", []))
    require("license_status" in blocked_fields, "DS-017 must remain license-blocked")


def validate_runbook() -> None:
    runbook = read_text("docs/runbooks/cost_monitoring.md")
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
        "docs/runbooks/incident_response.md",
        "No hosted cloud billing integration",
        "zero-dollar attribution",
        "human_review_minutes",
    ):
        require(phrase in runbook, f"cost monitoring runbook missing phrase: {phrase}")


def main() -> int:
    validate_required_files()
    validate_catalog()
    validate_report_cost_metrics_schema()
    validate_planning_cost_inputs()
    validate_vendor_sources_stay_blocked()
    validate_runbook()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
