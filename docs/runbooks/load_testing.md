# Load Testing Runbook

## Purpose

Validate that the local server handles a baseline sequential load without exceeding
per-request time thresholds. This is a development and CI-readiness check, not a
performance SLA or capacity benchmark.

## Required Setup

The server must be running before executing the load test. Start it with one of:

```powershell
# via Docker Compose (recommended for full-stack local testing)
docker compose up -d

# or via uvicorn directly
cd backend
py -3.12 -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Confirm the server is healthy before running the test:

```powershell
Invoke-WebRequest -Uri http://127.0.0.1:8000/health -UseBasicParsing
```

## Commands

### PowerShell (Windows)

Run from the repository root:

```powershell
.\scripts\run_load_test.ps1
```

To check that all script files and this runbook exist without sending any live HTTP
requests, use `--validate-only`:

```powershell
.\scripts\run_load_test.ps1 --validate-only
```

### Bash (Linux / macOS / WSL)

```bash
bash scripts/run_load_test.sh
```

To use the safe validation mode that checks artifacts without live requests:

```bash
bash scripts/run_load_test.sh --validate-only
```

## Thresholds

- **Request count**: 20 sequential requests total (4 each to `/health`, `/version`,
  `/metrics`, `POST /areas`, `POST /report-runs`).
- **Per-request time limit**: each request must complete within 5 seconds.
- **Pass condition**: all 20 requests complete within the 5-second threshold.
- The script exits 0 on success and 1 if any request exceeds the threshold.

## Scope Limitations

This test is **single-node and sequential**. It does not model:

- Multi-user or concurrent load
- Sustained throughput over time
- Resource exhaustion or memory pressure
- Network latency outside of localhost
- Database connection pool saturation

It is not a performance SLA. Passing this test means the server responds within 5 seconds
per request under single-threaded sequential access on localhost. It does not imply the
server will perform acceptably under production concurrency.

Full load testing with concurrency and ramp-up requires external tooling such as
[Locust](https://locust.io/) or [k6](https://k6.io/). Those tools are not currently
integrated and must be run manually outside of this script.

## How to Interpret Results

The script prints one line per request:

```
  PASS  [01/20] GET /health  status=200  elapsed=0.012s
  PASS  [02/20] GET /version  status=200  elapsed=0.008s
  ...
```

After all requests it prints a summary line with min/max/avg elapsed times and a
pass/fail count.

- A `FAIL` line means that request exceeded 5 seconds. The server may be under load,
  starting up, or experiencing a slow database query.
- A `status=4xx` or `status=5xx` does not itself count as a failure for threshold
  purposes — only elapsed time is evaluated. Review server logs if unexpected status
  codes appear.
- If the script cannot connect at all, it will raise a connection error before printing
  any results. Confirm the server is running at `http://127.0.0.1:8000`.

## Notes

- The `--validate-only` flag checks that `scripts/run_load_test.ps1`,
  `scripts/run_load_test.sh`, and `docs/runbooks/load_testing.md` exist and are non-empty.
  Use this in CI pipelines that do not have a live server available.
- The script uses only Python standard library (`urllib.request`). No extra packages
  are required.
- POST payloads are minimal fixtures. The server may return 4xx for validation failures
  on those endpoints; that is expected and does not affect the timing threshold check.
