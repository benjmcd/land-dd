$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $root

$requiredFiles = @(
    'config\ops_cost_monitoring.yaml',
    'docs\runbooks\cost_monitoring.md',
    'schemas\report_run_schema.json',
    'docs\planning_pack\registers\cost_model_inputs.csv',
    'registers\data_source_registry.csv',
    'scripts\source_readiness.py'
)

foreach ($file in $requiredFiles) {
    if (-not (Test-Path -Path (Join-Path $root $file) -PathType Leaf)) {
        throw "required cost-monitoring artifact missing: $file"
    }
}

$python = @'
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path.cwd()
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


def require_existing(path_text: str) -> None:
    normalized = path_text.replace("\\", "/")
    require((ROOT / normalized).exists(), f"referenced cost artifact missing: {normalized}")


def validate_catalog() -> None:
    payload = yaml.safe_load((ROOT / "config" / "ops_cost_monitoring.yaml").read_text(encoding="utf-8"))
    require(isinstance(payload, dict), "cost monitoring catalog must be a mapping")
    require(payload.get("schema_version") == "ops_cost_monitoring_v1", "unexpected cost monitoring schema")
    require(payload.get("incident_runbook") == "docs/runbooks/incident_response.md", "incident runbook mismatch")
    require(payload.get("operator_runbook") == "docs/runbooks/cost_monitoring.md", "operator runbook mismatch")
    require_existing(str(payload.get("report_cost_metrics_authority", "")))
    require_existing(str(payload.get("planning_cost_inputs", "")))
    categories = payload.get("categories")
    require(isinstance(categories, list) and categories, "cost monitoring categories missing")
    ids = set()
    for category in categories:
        require(isinstance(category, dict), "each cost category must be a mapping")
        category_id = category.get("id")
        require(isinstance(category_id, str) and category_id, "cost category id missing")
        require(category_id not in ids, f"duplicate cost category id: {category_id}")
        ids.add(category_id)
        for field in ("status", "meter", "source_of_truth", "threshold", "action", "validation"):
            require(field in category and category[field], f"{category_id} missing {field}")
        source_paths = category["source_of_truth"]
        require(isinstance(source_paths, list) and source_paths, f"{category_id} source_of_truth must be a list")
        for source_path in source_paths:
            if isinstance(source_path, str) and source_path.startswith(("backend/", "config/", "docs/", "registers/", "schemas/", "scripts/")):
                require_existing(source_path)
        validation = category["validation"]
        require(isinstance(validation, str), f"{category_id} validation must be a string")
        require_existing(validation)
    require(REQUIRED_CATEGORIES.issubset(ids), f"missing cost categories: {sorted(REQUIRED_CATEGORIES - ids)}")


def validate_report_cost_metrics_schema() -> None:
    schema = json.loads((ROOT / "schemas" / "report_run_schema.json").read_text(encoding="utf-8"))
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
    require(
        REQUIRED_COST_INPUT_CATEGORIES.issubset(categories),
        f"planning cost input categories missing: {sorted(REQUIRED_COST_INPUT_CATEGORIES - categories)}",
    )


def validate_vendor_sources_stay_blocked() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/source_readiness.py", "--priority", "Must", "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    require(payload.get("schema_version") == "source_readiness_v1", "source readiness schema mismatch")
    commercial = [
        source
        for source in payload.get("sources", [])
        if str(source.get("source_registry_id")) == "DS-017"
    ]
    require(commercial, "DS-017 commercial parcel vendor missing from Must source readiness")
    ds017 = commercial[0]
    require(ds017.get("connector_ready") is False, "DS-017 must remain blocked without vendor cost/license review")
    blocked_fields = set(ds017.get("blocked_fields", []))
    require("license_status" in blocked_fields, "DS-017 must remain license-blocked")


def validate_runbook() -> None:
    runbook = (ROOT / "docs" / "runbooks" / "cost_monitoring.md").read_text(encoding="utf-8")
    for phrase in (
        "compute",
        "storage",
        "LLM",
        "Maps",
        "Geocoding",
        "Data vendors",
        "cost_metrics",
        "docs/runbooks/incident_response.md",
        "No billing feature or hosted cloud billing integration is planned",
        "zero-dollar attribution",
        "human_review_minutes",
    ):
        require(phrase in runbook, f"cost monitoring runbook missing phrase: {phrase}")


def main() -> int:
    validate_catalog()
    validate_report_cost_metrics_schema()
    validate_planning_cost_inputs()
    validate_vendor_sources_stay_blocked()
    validate_runbook()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'@

$python | py -3.12 -
if ($LASTEXITCODE -ne 0) {
    throw "cost monitoring validation failed with exit code $LASTEXITCODE"
}

Write-Host 'cost monitoring check: ok'
