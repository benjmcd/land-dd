"""
Shared load-test runner for sequential and concurrent scenarios.

Usage:
    python load_test_runner.py [--scenario sequential|concurrent] [--base-url URL]
        [--json-output PATH]

Environment overrides (all optional):
    LOAD_TEST_BASE_URL          default http://127.0.0.1:8000
    LOAD_TEST_TIMEOUT           per-request timeout in seconds (default 5.0)
    LOAD_TEST_SEQ_THRESHOLD     sequential per-request wall-clock limit in seconds (default 5.0)
    LOAD_TEST_CONC_WORKERS      number of parallel workers (default 8)
    LOAD_TEST_CONC_P95_LIMIT    concurrent p95 latency limit in seconds (default 3.0)
    LOAD_TEST_CONC_ERR_RATE     concurrent max error rate 0.0–1.0 (default 0.1)
"""
from __future__ import annotations

import argparse
import json
import os
import threading
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Configuration (env-overridable)
# ---------------------------------------------------------------------------

BASE_URL: str = os.environ.get("LOAD_TEST_BASE_URL", "http://127.0.0.1:8000")
TIMEOUT_SECONDS: float = float(os.environ.get("LOAD_TEST_TIMEOUT", "5.0"))
SEQ_THRESHOLD_SECONDS: float = float(os.environ.get("LOAD_TEST_SEQ_THRESHOLD", "5.0"))
CONC_WORKERS: int = int(os.environ.get("LOAD_TEST_CONC_WORKERS", "8"))
CONC_P95_LIMIT: float = float(os.environ.get("LOAD_TEST_CONC_P95_LIMIT", "3.0"))
CONC_ERR_RATE_LIMIT: float = float(os.environ.get("LOAD_TEST_CONC_ERR_RATE", "0.1"))
RESULT_SCHEMA_VERSION = "load_test_result_v1"
LAST_RESULT: dict[str, Any] | None = None

# ---------------------------------------------------------------------------
# Shared payloads
# ---------------------------------------------------------------------------

GEOJSON_POLYGON: dict[str, object] = {
    "type": "Polygon",
    "coordinates": [
        [
            [-105.0, 40.0],
            [-104.9, 40.0],
            [-104.9, 40.1],
            [-105.0, 40.1],
            [-105.0, 40.0],
        ]
    ],
}

AREA_CREATE_PAYLOAD = json.dumps(
    {
        "label": "load-test-area",
        "geom_geojson": GEOJSON_POLYGON,
        "geom_source": "load-test-fixture",
    }
)

# Shared request mix (same endpoints used by both scenarios)
REQUEST_MIX: list[tuple[str, str, str | None]] = [
    ("GET", "/health", None),
    ("GET", "/version", None),
    ("GET", "/metrics", None),
    ("POST", "/areas", AREA_CREATE_PAYLOAD),
    ("POST", "/report-runs", None),
]


def _utc_timestamp() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _record_result(result: dict[str, Any]) -> None:
    global LAST_RESULT
    LAST_RESULT = result


def write_json_result(path_text: str, result: dict[str, Any]) -> None:
    path = Path(path_text)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _is_runtime_error(status: int) -> bool:
    return status == 0 or status >= 500


def _expected_statuses(method: str, path: str) -> set[int]:
    if method == "GET" and path in {"/health", "/version", "/metrics"}:
        return {200}
    if method == "POST" and path == "/areas":
        return {201}
    if method == "POST" and path == "/report-runs":
        return {200, 202}
    return set(range(200, 300))


def _report_run_payload(area_id: str) -> str:
    return json.dumps({"area_id": area_id, "intent_code": "rural_land_purchase"})


def _area_id_from_response(body_text: str) -> tuple[str | None, str | None]:
    try:
        body = json.loads(body_text)
    except json.JSONDecodeError:
        return None, "area create response was not valid JSON"
    if not isinstance(body, dict):
        return None, "area create response was not a JSON object"
    area_id = body.get("area_id")
    if not isinstance(area_id, str) or not area_id.strip():
        return None, "area create response did not include area_id"
    return area_id, None


def _request_failure_reasons(
    *,
    status: int,
    elapsed: float,
    expected_statuses: set[int],
    max_seconds: float | None = None,
) -> list[str]:
    failure_reasons: list[str] = []
    if max_seconds is not None and elapsed > max_seconds:
        failure_reasons.append(f"elapsed {elapsed:.3f}s > {max_seconds}s")
    if _is_runtime_error(status):
        failure_reasons.append(f"runtime status {status}")
    elif status not in expected_statuses:
        expected = ", ".join(str(value) for value in sorted(expected_statuses))
        failure_reasons.append(f"unexpected status {status}; expected {expected}")
    return failure_reasons


def _request_record(
    *,
    method: str,
    path: str,
    status: int,
    elapsed: float,
    failure_reasons: list[str],
    worker_id: int | None = None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "method": method,
        "path": path,
        "status": status,
        "elapsed": elapsed,
        "passed": not failure_reasons,
        "failure_reasons": failure_reasons,
        "runtime_error": _is_runtime_error(status),
    }
    if worker_id is not None:
        record["worker"] = worker_id
    return record


def _skipped_report_record(worker_id: int | None = None) -> dict[str, Any]:
    return _request_record(
        method="POST",
        path="/report-runs",
        status=0,
        elapsed=0.0,
        failure_reasons=["skipped because /areas did not return a valid area_id"],
        worker_id=worker_id,
    )


# ---------------------------------------------------------------------------
# Core HTTP helper
# ---------------------------------------------------------------------------


def send_request(
    base_url: str,
    method: str,
    path: str,
    body: str | None = None,
    timeout: float = TIMEOUT_SECONDS,
) -> tuple[int, float, str]:
    """Send one HTTP request; return (status_code, elapsed_seconds, response_body)."""
    url = base_url + path
    data: bytes | None = body.encode("utf-8") if body is not None else None
    headers: dict[str, str] = {"Content-Type": "application/json"} if data else {}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body_text = resp.read().decode("utf-8", errors="replace")
            status = resp.status
    except urllib.error.HTTPError as exc:
        status = exc.code
        body_text = exc.read().decode("utf-8", errors="replace")
    except Exception:
        status = 0  # connection-level failure
        body_text = ""
    elapsed = time.monotonic() - t0
    return status, elapsed, body_text


# ---------------------------------------------------------------------------
# Sequential scenario
# ---------------------------------------------------------------------------


def run_sequential(base_url: str) -> int:
    requests: list[tuple[str, str, str | None]] = []
    for _ in range(4):
        requests.append(("GET", "/health", None))
    for _ in range(4):
        requests.append(("GET", "/version", None))
    for _ in range(4):
        requests.append(("GET", "/metrics", None))
    for _ in range(4):
        requests.append(("POST", "/areas", AREA_CREATE_PAYLOAD))
        requests.append(("POST", "/report-runs", None))

    total = len(requests)
    assert total == 20, f"expected 20 requests, got {total}"  # noqa: S101

    results: list[dict[str, Any]] = []
    failures: list[str] = []

    print(f"load test [sequential]: sending {total} sequential requests to {base_url}")

    pending_area_id: str | None = None
    for i, (method, path, body) in enumerate(requests, start=1):
        label = f"[{i:02d}/{total}] {method} {path}"
        if method == "POST" and path == "/report-runs":
            if pending_area_id is None:
                record = _skipped_report_record()
                results.append(record)
                print(f"  FAIL  {label}  status=0  elapsed=0.000s")
                failures.append(f"{label} failed: {record['failure_reasons'][0]}")
                continue
            body = _report_run_payload(pending_area_id)
            pending_area_id = None

        status, elapsed, body_text = send_request(base_url, method, path, body)
        failure_reasons = _request_failure_reasons(
            status=status,
            elapsed=elapsed,
            expected_statuses=_expected_statuses(method, path),
            max_seconds=SEQ_THRESHOLD_SECONDS,
        )
        record = _request_record(
            method=method,
            path=path,
            status=status,
            elapsed=elapsed,
            failure_reasons=failure_reasons,
        )
        if method == "POST" and path == "/areas" and record["passed"]:
            pending_area_id, parse_error = _area_id_from_response(body_text)
            if parse_error is not None:
                record["failure_reasons"].append(parse_error)
                record["passed"] = False
                pending_area_id = None
        flag = "PASS" if record["passed"] else "FAIL"
        print(f"  {flag}  {label}  status={status}  elapsed={elapsed:.3f}s")
        results.append(record)
        for reason in failure_reasons:
            failures.append(f"{label} failed: {reason}")
        if not record["passed"]:
            for reason in record["failure_reasons"][len(failure_reasons):]:
                failures.append(f"{label} failed: {reason}")

    times = [r["elapsed"] for r in results]
    passed_count = sum(1 for r in results if r["passed"])
    failed_count = total - passed_count
    summary = {
        "min_seconds": min(times),
        "max_seconds": max(times),
        "avg_seconds": sum(times) / len(times),
        "passed": passed_count,
        "failed": failed_count,
    }
    _record_result(
        {
            "schema_version": RESULT_SCHEMA_VERSION,
            "runner_timestamp": _utc_timestamp(),
            "scenario": "sequential",
            "base_url": base_url,
            "thresholds": {"max_request_seconds": SEQ_THRESHOLD_SECONDS},
            "total_requests": total,
            "ok": not failures,
            "failures": failures,
            "requests": results,
            "summary": summary,
        }
    )
    print(
        f"\nload test [sequential] summary: total={total}  "
        f"min={summary['min_seconds']:.3f}s  max={summary['max_seconds']:.3f}s  "
        f"avg={summary['avg_seconds']:.3f}s  "
        f"passed={passed_count}  "
        f"failed={failed_count}"
    )

    if failures:
        print("\nFAILURES:")
        for msg in failures:
            print(f"  {msg}")
        return 1

    print("\nload test [sequential]: ok")
    return 0


# ---------------------------------------------------------------------------
# Concurrent scenario
# ---------------------------------------------------------------------------


def _worker(
    worker_id: int,
    base_url: str,
    results: list[dict[str, Any]],
    lock: threading.Lock,
) -> None:
    """Each worker issues one full REQUEST_MIX cycle."""
    pending_area_id: str | None = None
    for method, path, body in REQUEST_MIX:
        if method == "POST" and path == "/report-runs":
            if pending_area_id is None:
                with lock:
                    results.append(_skipped_report_record(worker_id))
                continue
            body = _report_run_payload(pending_area_id)
            pending_area_id = None

        status, elapsed, body_text = send_request(base_url, method, path, body)
        failure_reasons = _request_failure_reasons(
            status=status,
            elapsed=elapsed,
            expected_statuses=_expected_statuses(method, path),
        )
        record = _request_record(
            method=method,
            path=path,
            status=status,
            elapsed=elapsed,
            failure_reasons=failure_reasons,
            worker_id=worker_id,
        )
        if method == "POST" and path == "/areas" and record["passed"]:
            pending_area_id, parse_error = _area_id_from_response(body_text)
            if parse_error is not None:
                record["failure_reasons"].append(parse_error)
                record["passed"] = False
                pending_area_id = None
        with lock:
            results.append(record)


def run_concurrent(base_url: str, n_workers: int = CONC_WORKERS) -> int:
    results: list[dict[str, Any]] = []
    lock = threading.Lock()

    print(
        f"load test [concurrent]: {n_workers} parallel workers × {len(REQUEST_MIX)} "
        f"requests each = {n_workers * len(REQUEST_MIX)} total requests to {base_url}"
    )
    print(
        f"  thresholds: p95 <= {CONC_P95_LIMIT}s, "
        f"failure rate <= {CONC_ERR_RATE_LIMIT * 100:.0f}%"
    )

    wall_start = time.monotonic()

    threads = [
        threading.Thread(
            target=_worker,
            args=(wid, base_url, results, lock),
            daemon=True,
        )
        for wid in range(1, n_workers + 1)
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    wall_elapsed = time.monotonic() - wall_start

    # ---- compute stats ----
    total = len(results)
    if total == 0:
        print("load test [concurrent]: no results — something went wrong")
        _record_result(
            {
                "schema_version": RESULT_SCHEMA_VERSION,
                "runner_timestamp": _utc_timestamp(),
                "scenario": "concurrent",
                "base_url": base_url,
                "thresholds": {
                    "p95_seconds": CONC_P95_LIMIT,
                    "max_error_rate": CONC_ERR_RATE_LIMIT,
                },
                "workers": n_workers,
                "total_requests": 0,
                "ok": False,
                "failures": ["no request results were recorded"],
                "requests": [],
                "summary": {
                    "p50_seconds": 0.0,
                    "p95_seconds": 0.0,
                    "max_seconds": 0.0,
                    "error_count": 0,
                    "error_rate": 1.0,
                    "workflow_failure_count": 0,
                    "throughput_requests_per_second": 0.0,
                    "wall_seconds": wall_elapsed,
                },
            }
        )
        return 1

    times = [r["elapsed"] for r in results]
    sorted_times = sorted(times)

    def percentile(data: list[float], pct: float) -> float:
        idx = int(len(data) * pct / 100)
        idx = min(idx, len(data) - 1)
        return data[idx]

    p50 = percentile(sorted_times, 50)
    p95 = percentile(sorted_times, 95)
    p_max = max(sorted_times)

    error_count = sum(1 for r in results if not r["passed"])
    error_rate = error_count / total
    workflow_failure_count = sum(
        1
        for r in results
        for reason in r.get("failure_reasons", [])
        if reason.startswith("unexpected status")
        or reason.startswith("skipped because")
        or reason.startswith("area create response")
    )

    throughput = total / wall_elapsed if wall_elapsed > 0 else 0.0

    # ---- per-request output ----
    for r in sorted(results, key=lambda x: (x["worker"], x["path"])):
        print(
            f"  worker={r['worker']:02d}  {r['method']:4s} {r['path']:<20s}  "
            f"status={r['status']}  elapsed={r['elapsed']:.3f}s"
        )

    print(
        f"\nload test [concurrent] summary: "
        f"workers={n_workers}  total={total}  "
        f"p50={p50:.3f}s  p95={p95:.3f}s  max={p_max:.3f}s  "
        f"failures={error_count}  failure_rate={error_rate:.1%}  "
        f"throughput={throughput:.1f} req/s  "
        f"wall={wall_elapsed:.3f}s"
    )

    failures: list[str] = []

    if p95 > CONC_P95_LIMIT:
        failures.append(
            f"p95 latency {p95:.3f}s exceeds limit {CONC_P95_LIMIT}s"
        )
    if error_rate > CONC_ERR_RATE_LIMIT:
        failures.append(
            f"failure rate {error_rate:.1%} exceeds limit "
            f"{CONC_ERR_RATE_LIMIT * 100:.0f}%"
        )
    if workflow_failure_count:
        failures.append(
            f"workflow request failures {workflow_failure_count}; "
            "expected successful area creation and report-run admission"
        )

    _record_result(
        {
            "schema_version": RESULT_SCHEMA_VERSION,
            "runner_timestamp": _utc_timestamp(),
            "scenario": "concurrent",
            "base_url": base_url,
            "thresholds": {
                "p95_seconds": CONC_P95_LIMIT,
                "max_error_rate": CONC_ERR_RATE_LIMIT,
            },
            "workers": n_workers,
            "total_requests": total,
            "ok": not failures,
            "failures": failures,
            "requests": results,
            "summary": {
                "p50_seconds": p50,
                "p95_seconds": p95,
                "max_seconds": p_max,
                "error_count": error_count,
                "error_rate": error_rate,
                "workflow_failure_count": workflow_failure_count,
                "throughput_requests_per_second": throughput,
                "wall_seconds": wall_elapsed,
            },
        }
    )

    if failures:
        print("\nFAILURES:")
        for msg in failures:
            print(f"  {msg}")
        return 1

    print("\nload test [concurrent]: ok")
    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="Land-diligence load test runner")
    parser.add_argument(
        "--scenario",
        choices=["sequential", "concurrent"],
        default="sequential",
        help="which load scenario to run (default: sequential)",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="override base URL (default: LOAD_TEST_BASE_URL env or http://127.0.0.1:8000)",
    )
    parser.add_argument(
        "--json-output",
        default=None,
        help="optional path for writing structured load_test_result_v1 JSON evidence",
    )
    args = parser.parse_args()

    base_url = args.base_url if args.base_url else BASE_URL

    if args.scenario == "sequential":
        exit_code = run_sequential(base_url)
    else:
        exit_code = run_concurrent(base_url, n_workers=CONC_WORKERS)

    if args.json_output is not None:
        if LAST_RESULT is None:
            raise RuntimeError("load-test result was not recorded")
        write_json_result(args.json_output, LAST_RESULT)

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
