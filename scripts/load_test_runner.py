"""
Shared load-test runner for sequential and concurrent scenarios.

Usage:
    python load_test_runner.py [--scenario sequential|concurrent] [--base-url URL]

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
# Sequential scenario (unchanged semantics from original)
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
        passed = elapsed <= SEQ_THRESHOLD_SECONDS
        flag = "PASS" if passed else "FAIL"
        print(f"  {flag}  {label}  status={status}  elapsed={elapsed:.3f}s")
        results.append(
            {
                "method": method,
                "path": path,
                "status": status,
                "elapsed": elapsed,
                "passed": passed,
            }
        )
        if not passed:
            failures.append(
                f"{label} exceeded threshold: {elapsed:.3f}s > {SEQ_THRESHOLD_SECONDS}s"
            )

    times = [r["elapsed"] for r in results]
    print(
        f"\nload test [sequential] summary: total={total}  "
        f"min={min(times):.3f}s  max={max(times):.3f}s  "
        f"avg={sum(times) / len(times):.3f}s  "
        f"passed={sum(1 for r in results if r['passed'])}  "
        f"failed={len(failures)}"
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
    args = parser.parse_args()

    base_url = args.base_url if args.base_url else BASE_URL

    if args.scenario == "sequential":
        return run_sequential(base_url)
    else:
        return run_concurrent(base_url, n_workers=CONC_WORKERS)


if __name__ == "__main__":
    raise SystemExit(main())
