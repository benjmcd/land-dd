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
| workspace validation | instruction/file/source-registry/private-MVP invariants | current |
| domain contract tests | evidence/claim/source invariants | current |
| API smoke tests | health/version and future report endpoints | current/future |
| DB migration smoke | PostGIS schema applies and core tables exist | current optional Docker |
| connector fixture tests | source success/failure behavior | current |
| rule-engine tests | evidence-to-claim semantics | current |
| report reproducibility tests | run versions and outputs stable + cross-run byte-identical artifact projection | current |
| DB-spine regression | fixture ingest → persisted claim_evidence → DB-loaded dossier | current (RUN_DB_SMOKE) |

Report-reproducibility and DB-spine coverage landed 2026-07-06 (PR #188): a
`RUN_DB_SMOKE=1` regression ingests a committed domain fixture, asserts the persisted
`claims.claim_evidence` row cites the ingested `evidence_id`, and the DB-loaded dossier
renders the domain finding plus caveats; a separate in-memory test asserts two independent
report runs over identical inputs produce a byte-identical stable artifact projection.

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

CI splits the gate across two jobs. The `verify` job runs the full non-DB gate
(workspace validation, qualification/authority validators, backend tests, ruff, mypy).
The `db-verify` job runs the PostGIS-backed slice with `RUN_DB_SMOKE=1` (the same backend
tests against real Postgres, plus DB migrations and DB smoke) under `CI_DB_SLICE_ONLY=1`,
which skips the ruff/mypy/qualification-validator checks that `verify` already covers so
they are not duplicated. Both jobs run in parallel; neither is a strict superset of the other.
