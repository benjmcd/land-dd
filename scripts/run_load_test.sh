#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

VALIDATE_ONLY=0
for arg in "$@"; do
  if [[ "$arg" == "--validate-only" ]]; then
    VALIDATE_ONLY=1
  fi
done

required_files=(
  "scripts/run_load_test.ps1"
  "scripts/run_load_test.sh"
  "docs/runbooks/load_testing.md"
)

for file in "${required_files[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "load test artifact missing: $file" >&2
    exit 1
  fi
  if [[ ! -s "$file" ]]; then
    echo "load test artifact is empty: $file" >&2
    exit 1
  fi
done

echo "load test: artifact validation ok"

if [[ "$VALIDATE_ONLY" -eq 1 ]]; then
  echo "load test: --validate-only requested; skipping live HTTP requests"
  exit 0
fi

python3 - <<'PY'
from __future__ import annotations

import sys
import time
import json
from typing import Any

try:
    import urllib.request
    import urllib.error
except ImportError as exc:
    raise SystemExit(f"stdlib import failed: {exc}") from exc

BASE_URL = "http://127.0.0.1:8000"
TIMEOUT_SECONDS = 5.0
THRESHOLD_SECONDS = 5.0

GEOJSON_POLYGON = json.dumps({
    "type": "Feature",
    "geometry": {
        "type": "Polygon",
        "coordinates": [[
            [-105.0, 40.0],
            [-104.9, 40.0],
            [-104.9, 40.1],
            [-105.0, 40.1],
            [-105.0, 40.0],
        ]],
    },
    "properties": {},
})

REPORT_RUN_PAYLOAD = json.dumps({
    "area_id": "test-area-001",
    "requested_by": "load-test",
})


def send_request(method: str, path: str, body: str | None = None) -> tuple[int, float]:
    url = BASE_URL + path
    data: bytes | None = body.encode("utf-8") if body is not None else None
    headers: dict[str, str] = {"Content-Type": "application/json"} if data else {}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            resp.read()
            status = resp.status
    except urllib.error.HTTPError as exc:
        status = exc.code
    elapsed = time.monotonic() - t0
    return status, elapsed


def main() -> int:
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
    assert total == 20, f"expected 20 requests, got {total}"

    results: list[dict[str, Any]] = []
    failures: list[str] = []

    print(f"load test: sending {total} sequential requests to {BASE_URL}")

    for i, (method, path, body) in enumerate(requests, start=1):
        status, elapsed = send_request(method, path, body)
        label = f"[{i:02d}/{total}] {method} {path}"
        passed = elapsed <= THRESHOLD_SECONDS
        flag = "PASS" if passed else "FAIL"
        print(f"  {flag}  {label}  status={status}  elapsed={elapsed:.3f}s")
        results.append({"method": method, "path": path, "status": status, "elapsed": elapsed, "passed": passed})
        if not passed:
            failures.append(f"{label} exceeded threshold: {elapsed:.3f}s > {THRESHOLD_SECONDS}s")

    times = [r["elapsed"] for r in results]
    print(
        f"\nload test summary: total={total}  "
        f"min={min(times):.3f}s  max={max(times):.3f}s  "
        f"avg={sum(times)/len(times):.3f}s  "
        f"passed={sum(1 for r in results if r['passed'])}  "
        f"failed={len(failures)}"
    )

    if failures:
        print("\nFAILURES:")
        for msg in failures:
            print(f"  {msg}")
        return 1

    print("\nload test: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
PY
