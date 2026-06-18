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

GEOJSON_POLYGON = json.dumps(
    {
        "type": "Feature",
        "geometry": {
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
        },
        "properties": {},
    }
)

REPORT_RUN_PAYLOAD = json.dumps(
    {
        "area_id": "test-area-001",
        "requested_by": "load-test",
    }
)

# Shared request mix (same endpoints used by both scenarios)
REQUEST_MIX: list[tuple[str, str, str | None]] = [
    ("GET", "/health", None),
    ("GET", "/version", None),
    ("GET", "/metrics", None),
    ("POST", "/areas", GEOJSON_POLYGON),
    ("POST", "/report-runs", REPORT_RUN_PAYLOAD),
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


# ---------------------------------------------------------------------------
# Core HTTP helper
# ---------------------------------------------------------------------------


def send_request(
    base_url: str,
    method: str,
    path: str,
    body: str | None = None,
    timeout: float = TIMEOUT_SECONDS,
) -> tuple[int, float]:
    """Send one HTTP request; return (status_code, elapsed_seconds)."""
    url = base_url + path
    data: bytes | None = body.encode("utf-8") if body is not None else None
    headers: dict[str, str] = {"Content-Type": "application/json"} if data else {}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            resp.read()
            status = resp.status
    except urllib.error.HTTPError as exc:
        status = exc.code
    except Exception:
        status = 0  # connection-level failure
    elapsed = time.monotonic() - t0
    return status, elapsed


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
        requests.append(("POST", "/areas", GEOJSON_POLYGON))
    for _ in range(4):
        requests.append(("POST", "/report-runs", REPORT_RUN_PAYLOAD))

    total = len(requests)
    assert total == 20, f"expected 20 requests, got {total}"  # noqa: S101

    results: list[dict[str, Any]] = []
    failures: list[str] = []

    print(f"load test [sequential]: sending {total} sequential requests to {base_url}")

    for i, (method, path, body) in enumerate(requests, start=1):
        status, elapsed = send_request(base_url, method, path, body)
        label = f"[{i:02d}/{total}] {method} {path}"
        failure_reasons: list[str] = []
        if elapsed > SEQ_THRESHOLD_SECONDS:
            failure_reasons.append(
                f"elapsed {elapsed:.3f}s > {SEQ_THRESHOLD_SECONDS}s"
            )
        if _is_runtime_error(status):
            failure_reasons.append(f"runtime status {status}")
        passed = not failure_reasons
        flag = "PASS" if passed else "FAIL"
        print(f"  {flag}  {label}  status={status}  elapsed={elapsed:.3f}s")
        results.append(
            {
                "method": method,
                "path": path,
                "status": status,
                "elapsed": elapsed,
                "passed": passed,
                "failure_reasons": failure_reasons,
            }
        )
        for reason in failure_reasons:
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
    for method, path, body in REQUEST_MIX:
        status, elapsed = send_request(base_url, method, path, body)
        record = {
            "worker": worker_id,
            "method": method,
            "path": path,
            "status": status,
            "elapsed": elapsed,
            "runtime_error": _is_runtime_error(status),
        }
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
        f"error rate <= {CONC_ERR_RATE_LIMIT * 100:.0f}%"
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

    error_count = sum(
        1
        for r in results
        if r["status"] == 0 or (r["status"] >= 500)
    )
    error_rate = error_count / total

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
        f"errors={error_count}  error_rate={error_rate:.1%}  "
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
            f"error rate {error_rate:.1%} exceeds limit "
            f"{CONC_ERR_RATE_LIMIT * 100:.0f}%"
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
