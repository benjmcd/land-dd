param(
    [switch]$ValidateOnly
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $root

$requiredFiles = @(
    'scripts\run_load_test.ps1',
    'scripts\run_load_test.sh',
    'docs\runbooks\load_testing.md'
)

foreach ($file in $requiredFiles) {
    $fullPath = Join-Path $root $file
    if (-not (Test-Path -Path $fullPath -PathType Leaf)) {
        Write-Error "load test artifact missing: $file"
        exit 1
    }
    $content = Get-Content -Path $fullPath -Raw
    if (-not $content -or $content.Trim().Length -eq 0) {
        Write-Error "load test artifact is empty: $file"
        exit 1
    }
}

Write-Host 'load test: artifact validation ok'

if ($ValidateOnly) {
    Write-Host 'load test: --validate-only requested; skipping live HTTP requests'
    exit 0
}

$python = @'
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
'@

$python | py -3.12 -
if ($LASTEXITCODE -ne 0) {
    Write-Error "load test failed with exit code $LASTEXITCODE"
    exit 1
}
