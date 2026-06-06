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

All PostGIS geometry columns carry GIST indexes to support bounding-box and spatial
containment queries. Current coverage (see `db/migrations/` for the authoritative DDL):

- `area_geometry.areas.geometry` — GIST index for bounding-box queries against parcel and
  area geometries.
- `evidence.observations.geometry` — GIST index for spatial evidence queries (flood zone,
  wetland, etc.).

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

`scripts/run_load_test.ps1` runs a baseline load test of 20 sequential requests. Each
request must complete in 5 seconds or less. Run it locally before any change that touches
report generation, connector execution, or DB query paths:

```powershell
.\scripts\run_load_test.ps1
```

No automated load-test regression gate exists in CI yet; the script is validate-only for
now (see Limitations).

### Spatial query plan review

For every new database migration that adds or modifies a geometry column or spatial query:

1. Apply the migration to a local Postgres instance.
2. Run `EXPLAIN ANALYZE` on the affected queries.
3. Confirm the query plan uses the GIST index (look for `Index Scan using <idx>`).
4. Record the plan in the PR description or in `docs/adr/` if the change is architecture-level.

There is no automated plan-regression gate; validation is manual at this stage.

---

## Limitations and future work

- **No horizontal scaling tested.** The service runs as a single Uvicorn process inside a
  single Compose node. Multi-node deployment is not validated.
- **No distributed cache.** `OBJECT_STORE_ROOT` is a local filesystem path. Sharing
  artifacts across nodes requires replacing it with a shared volume or object storage
  (S3-compatible) backend.
- **No shared-memory rate limiter.** `ENABLE_RATE_LIMIT` uses an in-process counter. A
  Redis-backed limiter is needed before horizontal scaling is safe.
- **No automated load-test regression gate in CI.** The `run_load_test` script is
  validate-only. A future CI job should fail the build when p99 latency exceeds the
  5-second threshold.
- **DB pool settings not yet tuned for production.** `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`,
  `DB_POOL_TIMEOUT`, and `DB_POOL_RECYCLE` use SQLAlchemy defaults in local mode. Set
  explicit values in production `.env`.
- **p99 latency target is informal.** The 5-second-per-request target from the load test
  baseline is a development heuristic, not a contractual SLO. Define a formal SLO before
  production launch.
