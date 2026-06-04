# Lane A — Source Registry + DB Infrastructure

You are the Lane A agent. Read this file first, then read the files listed below.

## Required startup reads

1. `../../AGENTS.md` — root operating contract (always applies)
2. `../../MILESTONE_MAP.md` — authoritative maturity gates
3. `../../LANE_OWNERSHIP.md` — file ownership and isolation rules
4. `../../state/lane-a-state.md` — current Lane A state and next task
5. The active plan referenced in `state/lane-a-state.md`

## Your scope

You own MILESTONE_MAP.md Levels 2-3: Postgres/PostGIS storage spine and source registry provenance core.

## Your milestone gates

| Level | Gates | Pass condition |
|---|---|---|
| L2 | L2-001 to L2-010 | Postgres/PostGIS migrations apply cleanly; DB smoke passes; core schema exists |
| L3 | L3-001 to L3-010 | Source registry seeded; license/terms tracked; retrieval lifecycle; caveats machine-readable |

## Your owned directories and files

See `LANE_OWNERSHIP.md` Lane A section for the full list.

Key directories:
- `backend/app/source_registry/` — ALL source registry code lives here
- `backend/app/domain/source_contracts.py` — SourceContract (you own this)
- `backend/tests/source_registry/` — all Lane A tests
- `db/migrations/` — you steward migration file numbering
- `docker-compose.yml` — you own the local DB setup

## What you MUST NOT touch

- `backend/app/area_geometry/` (Lane B)
- `backend/app/evidence_ledger/` or `claims_engine/` (Lane C)
- `backend/app/reports/` or `api/` (Lane D)
- `backend/app/domain/area_contracts.py`, `evidence_contracts.py`, `claim_contracts.py`, `report_contracts.py`
- Any other lane's plans, state, or ADR files

## Import constraint

You may import from: `app.domain.*`, `app.db.*`, `app.core.*`, `app.source_registry.*`.
Do NOT import from: `app.area_geometry`, `app.evidence_ledger`, `app.claims_engine`, `app.reports`.

## Cleanup tasks (do these before new feature work)

1. Archive `backend/app/repositories/` and `backend/app/services/` — these are shims that re-export from your module. First confirm nothing outside those directories imports from them (grep), then move both to `archive/<today>_source-registry-lane-migration/backend/app/`. Verify tests still pass afterward.

## Verification commands (Lane A specific)

```bash
pytest backend/tests/source_registry/ -v
mypy backend/app/source_registry backend/app/domain/source_contracts.py
.\scripts\verify.ps1
# Once Docker running:
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

## Stop conditions

Stop and record a blocker in `state/lane-a-state.md` if:
- A data source license/terms status is unknown or possibly incompatible.
- A schema change would break evidence/claim/report reproducibility.
- A migration requires coordination with another lane.
- The first MVP state/county needs to be decided (do not hard-code).
