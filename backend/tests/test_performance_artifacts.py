from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any, cast

yaml = cast(Any, importlib.import_module("yaml"))

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK_PATH = REPO_ROOT / "docs" / "runbooks" / "performance.md"
BASELINE_CONFIG_PATH = REPO_ROOT / "config" / "performance_baseline.yaml"
BASELINE_CHECK_PATH = REPO_ROOT / "scripts" / "performance_baseline_check.py"
EXPECTED_RESULT_FIELDS = {
    "schema_version",
    "scenario",
    "base_url",
    "thresholds",
    "total_requests",
    "ok",
    "failures",
    "requests",
    "summary",
}
EXPECTED_REQUEST_MIX = {
    ("GET", "/health"),
    ("GET", "/version"),
    ("GET", "/metrics"),
    ("POST", "/areas"),
    ("POST", "/report-runs"),
}


def _runbook_text() -> str:
    return RUNBOOK_PATH.read_text(encoding="utf-8")


def _load_baseline_checker() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "performance_baseline_check_under_test",
        BASELINE_CHECK_PATH,
    )
    assert spec is not None
    loader = spec.loader
    assert loader is not None
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def _baseline_config() -> dict[str, Any]:
    payload = yaml.safe_load(BASELINE_CONFIG_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_performance_runbook_exists_and_is_not_empty() -> None:
    assert RUNBOOK_PATH.exists(), f"performance.md not found at {RUNBOOK_PATH}"
    text = _runbook_text()
    assert text.strip(), "performance.md must not be empty"


def test_performance_runbook_contains_cache() -> None:
    assert "cache" in _runbook_text().lower(), (
        "performance.md must contain a cache strategy section"
    )


def test_performance_runbook_contains_backpressure_or_degraded() -> None:
    text = _runbook_text().lower()
    assert "backpressure" in text or "degraded" in text, (
        "performance.md must contain a backpressure or degraded-mode section"
    )


def test_performance_runbook_contains_spatial() -> None:
    text = _runbook_text()
    assert "spatial" in text.lower(), "performance.md must contain spatial documentation"
    assert "config/spatial_query_plan.yaml" in text
    assert "run_spatial_query_plan_check.ps1" in text
    assert "No automated live spatial query-plan gate in CI" in text


def test_performance_runbook_contains_db_pool_size() -> None:
    assert "DB_POOL_SIZE" in _runbook_text(), (
        "performance.md must document the DB_POOL_SIZE setting"
    )


def test_performance_runbook_contains_load_test() -> None:
    text = _runbook_text().lower()
    assert "load_test" in text or "run_load_test" in text, (
        "performance.md must reference load_test or run_load_test"
    )


def test_performance_baseline_config_pins_local_evidence_contract() -> None:
    config = _baseline_config()

    assert config["schema_version"] == "performance_baseline_v1"
    assert config["scope"] == "selected_county_private_mvp_local"
    assert config["status"] == "release_candidate_local_only"
    assert config["runner"] == "scripts/load_test_runner.py"
    assert config["wrappers"] == {
        "windows": "scripts/run_load_test.ps1",
        "posix": "scripts/run_load_test.sh",
    }

    evidence = config["evidence"]
    assert evidence["result_schema_version"] == "load_test_result_v1"
    assert set(evidence["required_fields"]) == EXPECTED_RESULT_FIELDS

    limits = config["limits"]
    assert limits["hosted_production_claim"] is False
    assert limits["ci_live_load_gate"] is False
    assert limits["committed_measured_results"] is False


def test_performance_baseline_config_pins_exact_scenarios() -> None:
    config = _baseline_config()
    scenarios = config["scenarios"]
    assert isinstance(scenarios, list)
    by_id = {scenario["id"]: scenario for scenario in scenarios}

    assert set(by_id) == {"sequential", "concurrent"}

    sequential = by_id["sequential"]
    assert sequential["request_count"] == 20
    assert sequential["thresholds"] == {"max_request_seconds": 5.0}
    assert {
        (entry["method"], entry["path"])
        for entry in sequential["request_mix"]
    } == EXPECTED_REQUEST_MIX
    assert sum(entry["count"] for entry in sequential["request_mix"]) == 20

    concurrent = by_id["concurrent"]
    assert concurrent["workers"] == 8
    assert concurrent["request_count"] == 40
    assert concurrent["thresholds"] == {"p95_seconds": 3.0, "max_error_rate": 0.1}
    assert {
        (entry["method"], entry["path"])
        for entry in concurrent["request_mix"]
    } == EXPECTED_REQUEST_MIX
    assert sum(entry["count_per_worker"] for entry in concurrent["request_mix"]) == 5


def test_performance_baseline_checker_imports_and_passes() -> None:
    checker = cast(Any, _load_baseline_checker())

    checker.validate_config()
    assert checker.main() == 0
