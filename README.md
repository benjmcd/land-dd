# Land DD

This repository contains an intent-aware land/locality due-diligence compiler.

Target GitHub repository: `benjmcd/land-dd`.

The product target is a Postgres/PostGIS-first backend that accepts an area and intent, stores source-linked evidence, generates cautious interpreted claims, records red flags/unknowns, and produces reproducible report runs. The initial MVP is a United States rural land / homestead diligence dossier for a limited geography.

## Start here

```bash
./scripts/bootstrap.sh
./scripts/verify.sh
docker compose up -d db
./scripts/db_apply_migrations.sh
python scripts/db_smoke_check.py
```

Windows PowerShell equivalents avoid launching a separate Git Bash window:
```powershell
.\scripts\bootstrap.ps1
.\scripts\verify.ps1
docker compose up -d db
.\scripts\db_apply_migrations.ps1
python scripts\db_smoke_check.py
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

## Current locked scope

```text
MVP intent: rural land purchase / homestead feasibility
MVP geography: 3-5 counties in one selected U.S. state, not national/global legal-grade diligence
Core storage: PostgreSQL + PostGIS
Core workflow: source registry -> area -> evidence -> claim -> report run -> API
```

## Primary docs

- `docs/ARCHITECTURE.md`: durable design and invariants.
- `docs/PRODUCT_SPEC.md`: product scope and non-goals.
- `docs/POSTGRES_FIRST_STORAGE.md`: storage policy and schema direction.
- `docs/DATA_SOURCE_STRATEGY.md`: data source, licensing, and provenance direction.
- `docs/TESTING.md`: verification and test guidance.

## Non-goals

- No legal/title/survey/wetland/appraisal/insurance/lending/investment advice.
- No residential steering, protected-class scoring, or demographic desirability ranking.
- No opaque universal land score.
- No live connector before a source registry entry, license review, and fixture-backed tests.
- No UI-first implementation.
