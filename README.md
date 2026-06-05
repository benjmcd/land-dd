# Land DD

This repository contains an intent-aware land/locality due-diligence compiler.

Target GitHub repository: `benjmcd/land-dd`.

The product target is a Postgres/PostGIS-first backend that accepts an area and intent, stores source-linked evidence, generates cautious interpreted claims, records red flags/unknowns, and produces reproducible report runs. The initial MVP is a United States rural land / homestead diligence dossier for a limited geography.

## Start here

Install backend dev dependencies and run the fast local gate:

```bash
./scripts/bootstrap.sh
./scripts/verify.sh
```

Windows PowerShell:

```powershell
.\scripts\bootstrap.ps1
.\scripts\verify.ps1
```

Run the API with isolated in-memory state:

```bash
./scripts/run_api.sh --memory
```

```powershell
.\scripts\run_api.ps1 -StorageBackend memory
```

Run the intended Postgres-backed local API:

```bash
docker compose up -d db
./scripts/db_apply_migrations.sh
python scripts/db_smoke_check.py
APP_STORAGE_BACKEND=postgres ./scripts/run_api.sh --postgres
```

```powershell
docker compose up -d db
.\scripts\db_apply_migrations.ps1
python scripts\db_smoke_check.py
.\scripts\run_api.ps1 -StorageBackend postgres
```

Exercise the MVP fixture-to-report workflow against a running API:

```bash
python scripts/demo_mvp.py
```

```powershell
python scripts\demo_mvp.py
```

Export the runtime OpenAPI authority for inspection:

```bash
python scripts/export_openapi.py
```

```powershell
python scripts\export_openapi.py
```

For the full Postgres verification gate, run `RUN_DB_SMOKE=1 ./scripts/verify.sh`
or `$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1` after the local database is up
and migrations have been applied.

## Runtime storage modes

- `memory`: isolated process-local state for quick API demos and tests.
- `postgres`: database-backed services using `DATABASE_URL` and report artifacts under
  `OBJECT_STORE_ROOT`.

The exported `app.main:app` runtime reads `APP_STORAGE_BACKEND`. Tests that call
`create_app()` directly stay in memory mode unless they explicitly opt into DB services.
Migration and DB-smoke scripts use `DATABASE_URL_SYNC`, because `psql` expects a
synchronous PostgreSQL URL.

## Current locked scope

```text
MVP intent: rural land purchase / homestead feasibility
MVP geography: 3-5 counties in one selected U.S. state, not national/global legal-grade diligence
Core storage: PostgreSQL + PostGIS
Core workflow: source registry -> area -> evidence -> claim -> report run -> API
```

Before starting live-source, user-facing, or other impact-heavy implementation,
read `docs/IMPLEMENTATION_READINESS.md` and resolve the gates that apply to the
planned slice.

## Primary docs

- `MILESTONE_MAP.md`: current milestone status and readiness gates.
- `LANE_OWNERSHIP.md`: lane boundaries and connector integration ownership.
- `docs/ARCHITECTURE.md`: durable design and invariants.
- `docs/PRODUCT_SPEC.md`: product scope and non-goals.
- `docs/POSTGRES_FIRST_STORAGE.md`: storage policy and schema direction.
- `docs/DATA_SOURCE_STRATEGY.md`: data source, licensing, and provenance direction.
- `docs/IMPLEMENTATION_READINESS.md`: next-pass gates before high-impact work.
- `docs/TESTING.md`: verification and test guidance.
- `docs/DEMO.md`: public API fixture-to-report demo flow.
- `state/PROJECT_STATE.md`: current working state and known limits.
- `state/OPEN_QUESTIONS.md`: decisions that block heavier implementation.
- `state/VALIDATION_LOG.md`: recent verification evidence and local caveats.

## Non-goals

- No legal/title/survey/wetland/appraisal/insurance/lending/investment advice.
- No residential steering, protected-class scoring, or demographic desirability ranking.
- No opaque universal land score.
- No live connector before a source registry entry, license review, and fixture-backed tests.
- No UI-first implementation.
