# MVP API Demo

This demo exercises the current public API surface from fixture source setup to
report generation.

## In-Memory Demo

Use this path for a quick local API check without Docker:

```bash
./scripts/bootstrap.sh
./scripts/run_api.sh --memory
```

In another shell:

```bash
python scripts/demo_mvp.py
```

Windows PowerShell:

```powershell
.\scripts\bootstrap.ps1
.\scripts\run_api.ps1 -StorageBackend memory
```

In another PowerShell:

```powershell
python scripts\demo_mvp.py
```

Queued report jobs can be processed through the public API with the bounded
operator worker:

```powershell
python scripts\run_report_worker.py --workspace-id 11111111-1111-4111-8111-111111111111 --user-id 22222222-2222-4222-8222-222222222222 --max-jobs 5
```

## Postgres-Backed Demo

Use this path for the intended persistent local runtime:

```bash
docker compose up -d db
./scripts/db_apply_migrations.sh
python scripts/db_smoke_check.py
./scripts/run_api.sh --postgres
```

In another shell:

```bash
python scripts/demo_mvp.py
```

Windows PowerShell:

```powershell
docker compose up -d db
.\scripts\db_apply_migrations.ps1
python scripts\db_smoke_check.py
.\scripts\run_api.ps1 -StorageBackend postgres
```

In another PowerShell:

```powershell
python scripts\demo_mvp.py
```

The same bounded report worker command can be used after queueing report jobs
against the Postgres-backed API. It is an operator command, not an autonomous
scheduler or daemon.

## What The Demo Does

1. Checks `/health`.
2. Creates the packaged fixture source and area.
3. Runs static flood, zoning, and access connector fixtures.
4. Creates a `homestead_feasibility` report run using the demo
   `X-Workspace-Id` and `X-User-Id` identity headers.
5. Runs one source-failure fixture and approves its review queue item.
6. Lists report runs for the fixture area.

The demo is intentionally fixture-only. Live connectors remain disabled until a
source has a registry entry, license review, and fixture-backed tests.
The default report identity IDs are seeded for the local Postgres demo by
`db/seeds/003_seed_demo_identity.sql`; production identity must come from a
trusted gateway or token/session provider.
