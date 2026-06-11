# Testing

## Canonical gate

```bash
./scripts/verify.sh
```

On Windows PowerShell, use:

```powershell
.\scripts\verify.ps1
```

Both gates require Python 3.12+. The Windows wrapper selects `py -3.12` when
`python` on `PATH` points at an older interpreter.

## Test layers

| Layer | Purpose | Current / future |
|---|---|---|
| workspace validation | instruction/file invariants | current |
| domain contract tests | evidence/claim/source invariants | current |
| API smoke tests | health/version and future report endpoints | current/future |
| DB migration smoke | PostGIS schema applies and core tables exist | current optional Docker |
| connector fixture tests | source success/failure behavior | future |
| rule-engine tests | evidence-to-claim semantics | future |
| report reproducibility tests | run versions and outputs stable | future |

## Test-first expectations

- Behavior changes require tests.
- Bug fixes should reproduce the failure first where practical.
- Source connector tests must include unavailable/timeout/no-data cases.
- Rule tests must assert cautious output language and evidence links.
- DB tests must check reproducibility-critical fields, not just table creation.

## Local commands

```bash
./scripts/agent-context-check.sh
./scripts/validate_workspace.sh
cd backend && PYTHONPATH=. python -m pytest -q
```

Optional with Docker:

```bash
docker compose up -d db
./scripts/db_apply_migrations.sh
python scripts/db_smoke_check.py
```

Windows PowerShell equivalent:

```powershell
docker compose up -d db
.\scripts\db_apply_migrations.ps1
python scripts\db_smoke_check.py
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

If the local PostgreSQL client is not installed, the migration wrappers fall back to
the `postgis/postgis:16-3.4` Docker image for `psql`. When mapping Postgres to a
non-default host port, set both sync and app URLs before DB-backed tests:

```powershell
$env:DB_PORT='55432'
docker compose up -d db
$env:DATABASE_URL_SYNC='postgresql://land:land@localhost:55432/land_diligence'
$env:DATABASE_URL='postgresql+psycopg://land:land@localhost:55432/land_diligence'
$env:RUN_DB_SMOKE='1'
.\scripts\verify.ps1
```

CI has a separate PostGIS-backed job that runs the full gate with
`RUN_DB_SMOKE=1`. The default CI job remains the fast non-DB gate.
