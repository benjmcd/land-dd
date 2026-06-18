# Performance and Scalability Runbook

This runbook documents cache strategy, concurrency controls, spatial index coverage,
backpressure mechanisms, and the performance regression approach for the land-diligence
backend. It is a living document; update it whenever a relevant env var, index, or
policy changes.

---

## Cache strategy

- Report artifacts are immutable once generated. All artifacts are stored under the path
  configured by `OBJECT_STORE_ROOT` (default: `./local_artifacts/object_store`).
- There is no in-process application cache. Reports are identified and retrieved by
  `report_run_id`; repeated reads hit the object store directly.
- Cache invalidation is source-version aware: when new connector evidence is ingested the
  caller must start a fresh report run. Stale `report_run_id` values are never silently
  refreshed.
- Report reruns always generate fresh evidence evaluation — no memoisation of intermediate
  claim results across runs.
- Connector fixture workflows are idempotent: the same `ingest_run_id` always produces the
  same stored result, enabling safe replay without side-effects.

---

## Batch concurrency controls

- Live connector execution is gated behind `ENABLE_LIVE_CONNECTORS=true` (default: `false`).
  Production deployments must set this explicitly.
- Per-connector rate limits are enforced via `ConnectorPolicy.rate_limit_per_minute`:

  | Connector ID | rate_limit_per_minute |
  |---|---|
  | DS-001 | 60 |
  | DS-002 | 30 |
  | DS-003 | 30 |
  | DS-004 | 30 |

  The default fixture policy sets `rate_limit_per_minute=0` (no limit) for test connectors.
- The live connector worker processes one job per invocation (`--once` mode). It does not
  spawn threads or sub-processes internally.
- The Compose worker profile scales via supervisor restarts, not threads. Increase
  concurrency by adding worker containers, not by adding threads inside a single container.
- Report jobs are queued asynchronously. The background task executes one report job per
  incoming API request; no internal work queue exists yet.

---

## Spatial index coverage

All PostGIS geometry columns in the canonical schema carry GIST indexes to support
bounding-box and spatial containment queries. Current coverage is defined by
`db/migrations/0001_initial_spine.sql`, not by ORM declarations:

- `core.areas.geom` - `areas_geom_gix`
- `core.area_versions.geom` - `area_versions_geom_gix`
- `geo.parcels.geom` - `parcels_geom_gix`
- `geo.reference_features.geom` - `reference_features_geom_gix`
- `evidence.observations.geometry` - `observations_geom_gix`

Spatial query bounding boxes are capped by connector-level env vars to prevent runaway
queries:

- `FEMA_NFHL_MAX_BBOX_DEGREES=1.0` — maximum bounding box for FEMA NFHL flood-zone queries.
- `NWI_MAX_BBOX_DEGREES=1.0` — maximum bounding box for National Wetlands Inventory queries.

When adding a new geometry column, add a GIST index in the same migration and document it
here.

---

## Backpressure and degraded mode

- **Rate limiter** (`ENABLE_RATE_LIMIT`, default: `false`): when enabled, the API returns
  HTTP 429 once the request count exceeds `RATE_LIMIT_REQUESTS` within
  `RATE_LIMIT_WINDOW_SECONDS`. No distributed counter; limits are per-process.
- **Fail-closed source preflight**: a connector is blocked from running if its data-source
  rights have not been reviewed. Unreviewed sources never produce silent "no issue found"
  results.
- **Explicit source-failure evidence**: connector errors are recorded as first-class
  evidence records. No source failure is silently swallowed or omitted from the report.
- **DB connection pool**: the SQLAlchemy pool prevents connection exhaustion under load.
  Relevant settings:

  | Env var | Purpose |
  |---|---|
  | `DB_POOL_SIZE` | Number of persistent connections in the pool |
  | `DB_MAX_OVERFLOW` | Additional connections allowed above `DB_POOL_SIZE` |
  | `DB_POOL_TIMEOUT` | Seconds to wait for a connection before raising |
  | `DB_POOL_RECYCLE` | Seconds before a connection is recycled |

- **Audit sink failure**: the API responds with HTTP 503 if a configured audit-sink write
  fails. This is the fail-closed posture for audit integrity.

---

## Performance regression approach

### Automated test gate

`verify.ps1` / `verify.sh` is the canonical pre-release gate. The full test suite must
pass before any release artifact is cut. Test failures block release.

### Load test baseline

`scripts/run_load_test.ps1` and `scripts/run_load_test.sh` first validate that the
load-test artifacts exist, then run both local live scenarios by default: the 20-request
sequential baseline and the concurrent expected-workload scenario documented in
`docs/runbooks/load_testing.md`. The default target is `http://127.0.0.1:8000`; override
it with `-BaseUrl` or `LOAD_TEST_BASE_URL` when the local server uses another port.
`config/performance_baseline.yaml` is the canonical local performance baseline
contract. Live result artifacts written for a release candidate use the
`load_test_result_v1` JSON schema.
Run the live scenarios before any change that touches report generation, connector
execution, or DB query paths:

```powershell
.\scripts\run_load_test.ps1
```

For release-candidate local evidence, write live results under a candidate-specific
local artifact directory:

```powershell
.\scripts\run_load_test.ps1 -ResultDir .\local_artifacts\performance-baseline\<release-id>
```

POSIX operators can use the matching result-directory flag:

```bash
bash scripts/run_load_test.sh --result-dir ./local_artifacts/performance-baseline/<release-id>
```

Use `.\scripts\run_load_test.ps1 -ValidateOnly` when you only need the fail-closed
artifact check and do not want to send HTTP traffic or create measured result artifacts.
Release-readiness/CI validation composes the performance baseline checker as
validate-only proof of the contract and docs, but live load scenarios remain
local/manual unless an operator explicitly runs the wrapper against a running server.

### Spatial query plan review

`config/spatial_query_plan.yaml` is the repo-local spatial query-plan contract for the
selected-county private-MVP workload. `scripts/spatial_query_plan_check.py` validates
that the contract, wrapper scripts, this runbook, and the authoritative migration agree
on the required GIST indexes. This check opens no database connection by default. It is
validate-only, reads only repo files, seeds no runtime state, sends no network traffic,
and generates no artifacts:

```powershell
.\scripts\run_spatial_query_plan_check.ps1
```

For every new database migration that adds or modifies a geometry column or spatial
query, keep the static contract current and then perform read-only runtime review
against a representative local or release-candidate database. The opt-in runtime harness
requires `DATABASE_URL_SYNC` or `--db-url` and `SPATIAL_QUERY_PLAN_AREA_ID` or
`--area-id`; it validates the static contract before connecting, opens a read-only
transaction, sets a local statement timeout, rolls back, and writes JSON only when `--output-json` is supplied:

```powershell
.\scripts\run_spatial_query_plan_runtime_check.ps1 --area-id <area-id>
```

The POSIX wrapper forwards the same runtime-checker flags:

```bash
bash scripts/run_spatial_query_plan_runtime_check.sh --area-id <area-id>
```

Manual review steps:

1. Apply the migration to a local Postgres instance.
2. Run the configured runtime checker or the relevant `EXPLAIN ANALYZE` query from
   `config/spatial_query_plan.yaml`.
3. Confirm the query plan uses the target-table GIST index (look for
   `Index Scan using <idx>` or the JSON `Index Name`).
4. Record the plan in the PR description or in `docs/adr/` if the change is
   architecture-level.

Release readiness validates the static `spatial_query_plan_v1` contract, not a live DB
query plan. Runtime `EXPLAIN ANALYZE` evidence remains manual/read-only until a
representative candidate database exists and an explicit DB-enabled plan gate is added.

---

## Limitations and future work

- **No horizontal scaling tested.** The service runs as a single Uvicorn process inside a
  single Compose node. Multi-node deployment is not validated.
- **No distributed cache.** `OBJECT_STORE_ROOT` is a local filesystem path. Sharing
  artifacts across nodes requires replacing it with a shared volume or object storage
  (S3-compatible) backend.
- **No shared-memory rate limiter.** `ENABLE_RATE_LIMIT` uses an in-process counter. A
  Redis-backed limiter is needed before horizontal scaling is safe.
- **No automated live load-test regression gate in CI.** Release readiness validates
  the baseline contract, checker, scripts, and runbooks as validate-only proof. The
  `run_load_test` wrappers can run live sequential and concurrent scenarios locally,
  but CI does not start a server or fail builds on latency thresholds.
- **No automated live spatial query-plan gate in CI.** Release readiness validates
  `spatial_query_plan_v1` and the canonical DDL/index contract, but it does not run
  `EXPLAIN ANALYZE` against a live or hosted database by default.
- **DB pool settings not yet tuned for production.** `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`,
  `DB_POOL_TIMEOUT`, and `DB_POOL_RECYCLE` use SQLAlchemy defaults in local mode. Set
  explicit values in production `.env`.
- **p99 latency target is informal.** The 5-second-per-request target from the load test
  baseline is a development heuristic, not a contractual SLO or hosted production
  readiness claim. Define a formal SLO before production launch.
