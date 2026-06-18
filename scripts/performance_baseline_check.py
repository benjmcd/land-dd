from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = "config/performance_baseline.yaml"
RUNNER_PATH = "scripts/load_test_runner.py"
WINDOWS_WRAPPER = "scripts/run_load_test.ps1"
POSIX_WRAPPER = "scripts/run_load_test.sh"
LOAD_RUNBOOK = "docs/runbooks/load_testing.md"
PERFORMANCE_RUNBOOK = "docs/runbooks/performance.md"

EXPECTED_FIELDS = {
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
EXPECTED_REQUESTS = {
    ("GET", "/health"),
    ("GET", "/version"),
    ("GET", "/metrics"),
    ("POST", "/areas"),
    ("POST", "/report-runs"),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def require_mapping(value: Any, message: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SystemExit(message)
    return value


def require_list(value: Any, message: str) -> list[Any]:
    if not isinstance(value, list):
        raise SystemExit(message)
    return value


def read_text(path_text: str) -> str:
    return (ROOT / path_text).read_text(encoding="utf-8")


def require_existing_file(path_text: str) -> None:
    require((ROOT / path_text).is_file(), f"missing performance artifact: {path_text}")


def load_config() -> dict[str, Any]:
    require_existing_file(CONFIG_PATH)
    return require_mapping(
        yaml.safe_load(read_text(CONFIG_PATH)),
        "performance baseline config must be a mapping",
    )


def validate_config() -> None:
    config = load_config()
    require(
        config.get("schema_version") == "performance_baseline_v1",
        "unexpected performance baseline schema",
    )
    require(
        config.get("scope") == "selected_county_private_mvp_local",
        "performance baseline scope must stay selected-county private-MVP local",
    )
    require(
        config.get("status") == "release_candidate_local_only",
        "performance baseline status must stay release-candidate local only",
    )
    require(config.get("runner") == RUNNER_PATH, "performance baseline runner mismatch")

    wrappers = require_mapping(config.get("wrappers"), "performance wrappers missing")
    require(wrappers.get("windows") == WINDOWS_WRAPPER, "Windows wrapper mismatch")
    require(wrappers.get("posix") == POSIX_WRAPPER, "POSIX wrapper mismatch")

    evidence = require_mapping(config.get("evidence"), "performance evidence missing")
    require(
        evidence.get("result_schema_version") == "load_test_result_v1",
        "load-test result schema mismatch",
    )
    fields = set(require_list(evidence.get("required_fields"), "required fields missing"))
    require(fields == EXPECTED_FIELDS, f"unexpected result fields: {sorted(fields)}")

    scenarios = require_list(config.get("scenarios"), "performance scenarios missing")
    by_id = {
        require_mapping(scenario, "each performance scenario must be a mapping").get("id"):
        scenario
        for scenario in scenarios
    }
    require(set(by_id) == {"sequential", "concurrent"}, "unexpected scenario set")

    sequential = require_mapping(by_id["sequential"], "sequential scenario missing")
    require(sequential.get("request_count") == 20, "sequential request count mismatch")
    seq_thresholds = require_mapping(
        sequential.get("thresholds"),
        "sequential thresholds missing",
    )
    require(
        seq_thresholds.get("max_request_seconds") == 5.0,
        "sequential threshold mismatch",
    )
    validate_request_mix(sequential, per_worker=False)

    concurrent = require_mapping(by_id["concurrent"], "concurrent scenario missing")
    require(concurrent.get("workers") == 8, "concurrent worker count mismatch")
    require(concurrent.get("request_count") == 40, "concurrent request count mismatch")
    conc_thresholds = require_mapping(
        concurrent.get("thresholds"),
        "concurrent thresholds missing",
    )
    require(conc_thresholds.get("p95_seconds") == 3.0, "concurrent p95 mismatch")
    require(
        conc_thresholds.get("max_error_rate") == 0.1,
        "concurrent error-rate mismatch",
    )
    validate_request_mix(concurrent, per_worker=True)

    limits = require_mapping(config.get("limits"), "performance limits missing")
    require(limits.get("hosted_production_claim") is False, "hosted claim must be false")
    require(limits.get("ci_live_load_gate") is False, "CI live-load gate must be false")
    require(
        limits.get("committed_measured_results") is False,
        "committed measured results must be false",
    )


def validate_request_mix(scenario: dict[str, Any], *, per_worker: bool) -> None:
    request_mix = require_list(scenario.get("request_mix"), "request mix missing")
    seen: set[tuple[str, str]] = set()
    total = 0
    count_key = "count_per_worker" if per_worker else "count"
    for entry in request_mix:
        entry = require_mapping(entry, "each request-mix entry must be a mapping")
        key = (str(entry.get("method")), str(entry.get("path")))
        seen.add(key)
        count = entry.get(count_key)
        if not isinstance(count, int) or count <= 0:
            raise SystemExit(f"{key} count must be positive")
        total += count
    require(seen == EXPECTED_REQUESTS, f"unexpected request mix: {sorted(seen)}")
    expected_total = 5 if per_worker else scenario.get("request_count")
    require(total == expected_total, f"request mix count mismatch for {scenario.get('id')}")


def validate_runner_and_wrappers() -> None:
    for path_text in (
        RUNNER_PATH,
        WINDOWS_WRAPPER,
        POSIX_WRAPPER,
        LOAD_RUNBOOK,
        PERFORMANCE_RUNBOOK,
    ):
        require_existing_file(path_text)

    runner = read_text(RUNNER_PATH)
    for phrase in (
        "load_test_result_v1",
        "--json-output",
        "write_json_result",
        "SEQ_THRESHOLD_SECONDS",
        "CONC_P95_LIMIT",
        "CONC_ERR_RATE_LIMIT",
    ):
        require(phrase in runner, f"load-test runner missing phrase: {phrase}")

    windows = read_text(WINDOWS_WRAPPER)
    for phrase in (CONFIG_PATH.replace("/", "\\"), "ResultDir", "--json-output"):
        require(phrase in windows, f"Windows load-test wrapper missing phrase: {phrase}")

    posix = read_text(POSIX_WRAPPER)
    for phrase in (CONFIG_PATH, "--result-dir", "--json-output"):
        require(phrase in posix, f"POSIX load-test wrapper missing phrase: {phrase}")


def validate_runbooks() -> None:
    text = read_text(LOAD_RUNBOOK) + "\n" + read_text(PERFORMANCE_RUNBOOK)
    for phrase in (
        "config/performance_baseline.yaml",
        "load_test_result_v1",
        "ResultDir",
        "--result-dir",
        "release-candidate",
        "not a production SLO",
        "hosted production",
    ):
        require(phrase in text, f"performance runbooks missing phrase: {phrase}")


def main() -> int:
    validate_config()
    validate_runner_and_wrappers()
    validate_runbooks()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
