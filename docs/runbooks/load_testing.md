# Load Testing Runbook

## Purpose

Validate that the local server handles both a sequential baseline and a concurrent
expected-workload scenario without exceeding latency or error-rate thresholds. This
is release-candidate/local evidence, not a production SLO, hosted production proof,
performance SLA, or capacity benchmark. `config/performance_baseline.yaml` is the
canonical local performance baseline contract. Live JSON result files use the
`load_test_result_v1` schema.

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

Run both scenarios (sequential then concurrent) from the repository root:

```powershell
.\scripts\run_load_test.ps1
```

Run a single scenario:

```powershell
.\scripts\run_load_test.ps1 -Scenario sequential
.\scripts\run_load_test.ps1 -Scenario concurrent
```

Override the target URL (useful when the server is not on the default port):

```powershell
.\scripts\run_load_test.ps1 -BaseUrl http://127.0.0.1:8102
# or via environment variable
$env:LOAD_TEST_BASE_URL = "http://127.0.0.1:8102"
.\scripts\run_load_test.ps1
```

To check that all script files and this runbook exist without sending any live HTTP
requests or creating measured result artifacts, use `-ValidateOnly`:

```powershell
.\scripts\run_load_test.ps1 -ValidateOnly
```

To write release-candidate JSON result evidence for a live local run, pass a local
result directory:

```powershell
.\scripts\run_load_test.ps1 -ResultDir .\local_artifacts\performance-baseline\<release-id>
```

### Bash (Linux / macOS / WSL)

Run both scenarios:

```bash
bash scripts/run_load_test.sh
```

Run a single scenario:

```bash
bash scripts/run_load_test.sh --scenario sequential
bash scripts/run_load_test.sh --scenario concurrent
```

Override the target URL:

```bash
bash scripts/run_load_test.sh --base-url http://127.0.0.1:8102
# or via environment variable
LOAD_TEST_BASE_URL=http://127.0.0.1:8102 bash scripts/run_load_test.sh
```

To use the safe validation mode that checks artifacts without live requests or measured
result artifacts:

```bash
bash scripts/run_load_test.sh --validate-only
```

To write release-candidate JSON result evidence for a live local run, pass a local
result directory:

```bash
bash scripts/run_load_test.sh --result-dir ./local_artifacts/performance-baseline/<release-id>
```

## Scenarios

### Sequential (baseline)

Sends **20 sequential requests** (4 each to `/health`, `/version`, `/metrics`,
`POST /areas`, `POST /report-runs`) from a single thread, one after the other.

**Pass condition:** every request completes within 5 seconds.

This baseline ensures the server responds to each endpoint type without timing out
under zero concurrency.

### Concurrent (expected-workload)

Spins up **N parallel worker threads** (default 8, each sending the 5-endpoint
request mix once), all launched simultaneously, to model a burst of concurrent users.

- **Total requests:** `N workers × 5 requests = 40` by default.
- **Measured metrics:** p50, p95, and max latency; per-request error count; overall
  throughput (req/s); total wall-clock time.
- **Pass conditions (both must hold):**
  - p95 latency ≤ 3.0 seconds
  - Error rate ≤ 10 % (errors are HTTP 5xx responses and connection failures; 4xx
    responses are not counted as errors)

## Environment Overrides

All thresholds and parameters are overridable via environment variables:

| Variable | Default | Description |
|---|---|---|
| `LOAD_TEST_BASE_URL` | `http://127.0.0.1:8000` | Server base URL |
| `LOAD_TEST_TIMEOUT` | `5.0` | Per-request socket timeout (seconds) |
| `LOAD_TEST_SEQ_THRESHOLD` | `5.0` | Sequential per-request wall-clock limit (seconds) |
| `LOAD_TEST_CONC_WORKERS` | `8` | Number of parallel workers for concurrent scenario |
| `LOAD_TEST_CONC_P95_LIMIT` | `3.0` | Concurrent p95 latency limit (seconds) |
| `LOAD_TEST_CONC_ERR_RATE` | `0.1` | Concurrent max error rate (0.0–1.0) |

Example — tighter thresholds for a fast local machine:

```powershell
$env:LOAD_TEST_CONC_P95_LIMIT = "1.5"
$env:LOAD_TEST_CONC_WORKERS   = "16"
.\scripts\run_load_test.ps1 -Scenario concurrent
```

## How to Interpret Results

### Sequential output

The script prints one line per request:

```
  PASS  [01/20] GET /health  status=200  elapsed=0.012s
  PASS  [02/20] GET /version  status=200  elapsed=0.008s
  ...
```

A summary line follows with min/max/avg elapsed times and a pass/fail count.

- A `FAIL` line means that request exceeded the 5-second threshold. The server may be
  starting up, under other load, or experiencing a slow database query.
- `status=4xx` does not count as a sequential failure — only elapsed time is evaluated.

### Concurrent output

The script prints one line per completed request (sorted by worker, then path):

```
  worker=01  GET  /health               status=200  elapsed=0.014s
  worker=01  POST /areas                status=422  elapsed=0.021s
  ...
```

A summary line follows with p50/p95/max latency, error count, error rate, throughput,
and total wall-clock time:

```
load test [concurrent] summary: workers=8  total=40  p50=0.018s  p95=0.045s
  max=0.098s  errors=0  error_rate=0.0%  throughput=112.3 req/s  wall=0.356s
```

- **p95 > limit**: the slowest 5 % of requests are too slow — investigate slow
  endpoints (often `POST /areas` or `POST /report-runs` which touch the DB).
- **error_rate > limit**: too many 5xx/connection failures — check server logs for
  panics, DB pool exhaustion, or unhandled exceptions.
- **4xx responses** (validation errors on POST payloads) are expected and are not
  counted as errors.

### JSON result artifacts

When a live run is given a result directory, each measured result is written as
`load_test_result_v1` JSON under that local artifact path. Use
`.\local_artifacts\performance-baseline\<release-id>` on Windows or
`./local_artifacts/performance-baseline/<release-id>` on POSIX for release-candidate
evidence. Do not commit measured result files; they are machine-local evidence for the
candidate run.

## Scope Limitations and Single-Node Caveat

Both scenarios run **entirely on localhost against a single server process**. They do
not model:

- Multi-node or load-balanced deployments
- Sustained throughput ramp-up over minutes
- Resource exhaustion, memory pressure, or GC pauses under prolonged load
- Network latency outside localhost
- Database connection pool saturation under prolonged concurrent writes

A passing concurrent scenario means the server handles a short burst of N simultaneous
users within the p95 and error-rate thresholds on a single development node. It does
**not** imply the server will meet those thresholds under production-scale concurrency,
sustained load, or across a network with real latency.

For sustained load testing, ramp-up curves, and multi-node scenarios, use external
tooling such as [Locust](https://locust.io/) or [k6](https://k6.io/). Those tools
are not currently integrated and must be run manually outside of this script.

## Notes

- The `-ValidateOnly` / `--validate-only` flag checks that required script, runbook,
  and baseline-contract artifacts exist and are non-empty. It must not send HTTP
  requests or create measured result artifacts. Use this in CI pipelines that do not
  have a live server available.
- The canonical local baseline contract is `config/performance_baseline.yaml`.
- The Python runner (`scripts/load_test_runner.py`) uses only Python standard library
  (`urllib.request`, `threading`, `statistics`). No extra packages are required.
- Both wrappers (`run_load_test.ps1` and `run_load_test.sh`) delegate to the same
  Python runner, so scenario logic stays in one place and the two wrappers cannot drift.
- POST payloads are minimal fixtures. The server may return 4xx for validation failures
  on those endpoints; that is expected and does not affect threshold evaluation.
