# Land DD

This repository is a Codex + Claude Code compatible execution workspace for building an intent-aware land/locality due-diligence compiler.

Target GitHub repository: `benjmcd/land-dd`.

The product target is a Postgres/PostGIS-first backend that accepts an area and intent, stores source-linked evidence, generates cautious interpreted claims, records red flags/unknowns, and produces reproducible report runs. The initial MVP is a United States rural land / homestead diligence dossier for a limited geography.

## Start here

For agents:
1. Read `AGENTS.md` / `CLAUDE.md`.
2. Read `MANIFEST.md`.
3. Read `state/PROJECT_STATE.md`.
4. Read the active plan named in `state/PROJECT_STATE.md`.
5. Run `./scripts/verify.sh` before and after material changes.

For humans:
```bash
./scripts/bootstrap.sh
./scripts/verify.sh
docker compose up -d db
./scripts/db_apply_migrations.sh
python scripts/db_smoke_check.py
```

## Current locked scope

```text
MVP intent: rural land purchase / homestead feasibility
MVP geography: 3-5 counties in one selected U.S. state, not national/global legal-grade diligence
Core storage: PostgreSQL + PostGIS
Core workflow: source registry -> area -> evidence -> claim -> report run -> API
```

## Primary docs

- `AGENTS.md`: canonical agent operating contract.
- `CLAUDE.md`: Claude Code adapter importing `AGENTS.md`.
- `MANIFEST.md`: routing map to avoid context bloat.
- `docs/ARCHITECTURE.md`: durable design and invariants.
- `docs/PRODUCT_SPEC.md`: product scope and non-goals.
- `docs/POSTGRES_FIRST_STORAGE.md`: storage policy and schema direction.
- `plans/`: active implementation plans.
- `state/`: session-resilient state, worklog, validation log.
- `docs/planning_pack/`: comprehensive planning reference from the earlier specification pass; not startup context.

## Non-goals

- No legal/title/survey/wetland/appraisal/insurance/lending/investment advice.
- No residential steering, protected-class scoring, or demographic desirability ranking.
- No opaque universal land score.
- No live connector before a source registry entry, license review, and fixture-backed tests.
- No UI-first implementation.
