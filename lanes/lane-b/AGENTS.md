# Lane B — Area + Geometry Domain

You are the Lane B agent. Read this file first, then read the files listed below.

## Required startup reads

1. `../../AGENTS.md` — root operating contract (always applies)
2. `../../MILESTONE_MAP.md` — authoritative maturity gates
3. `../../LANE_OWNERSHIP.md` — file ownership and isolation rules
4. `../../state/lane-b-state.md` — current Lane B state and next task
5. The active plan referenced in `state/lane-b-state.md`

## Your scope

You own MILESTONE_MAP.md Level 4: Area + Geometry Domain.

## Your milestone gates

| Level | Gates | Pass condition |
|---|---|---|
| L4 | L4-001 to L4-010 | Valid GeoJSON creates area; invalid geometry handled; SRID explicit; area/bounds/centroid computable; spatial predicates via PostGIS |

## Your owned directories and files

See `LANE_OWNERSHIP.md` Lane B section for the full list.

Key directories:
- `backend/app/area_geometry/` — ALL area/geometry code lives here
- `backend/app/domain/area_contracts.py` — AreaContract (you own this)
- `backend/tests/area_geometry/` — all Lane B tests
- `db/seeds/area_*.py` — area fixture seed data
- Any GeoJSON fixture files under `tests/fixtures/geometries/`

## What you MUST NOT touch

- `backend/app/source_registry/` (Lane A)
- `backend/app/evidence_ledger/` or `claims_engine/` (Lane C)
- `backend/app/reports/` or `api/` (Lane D)
- `docker-compose.yml` — read only for Lane B; changes go through Lane A
- Any other lane's plans, state, or ADR files

## Import constraint

You may import from: `app.domain.*`, `app.db.*`, `app.core.*`, `app.area_geometry.*`.
Do NOT import from: `app.source_registry`, `app.evidence_ledger`, `app.claims_engine`, `app.reports`.

## Implementation notes

- Area geometry is stored in `core.areas` with a PostGIS `geometry(MultiPolygon, 4326)` column.
- For in-memory tests, store GeoJSON as a dict. Validate type (Polygon/MultiPolygon), coordinate count, and SRID.
- Do NOT perform PostGIS spatial queries in in-memory tests — test the service contract only.
- When DB is available (Lane A has run migrations), add PostGIS-backed AreaRepository.
- Parcel-like geometry must always be caveated as non-survey (L4-007).
- Geometry source and confidence must be stored (L4-006).

## Verification commands (Lane B specific)

```bash
pytest backend/tests/area_geometry/ -v
mypy backend/app/area_geometry backend/app/domain/area_contracts.py
./scripts/verify.sh
```

## Stop conditions

Stop and record a blocker in `state/lane-b-state.md` if:
- Geometry validation requires a live PostGIS connection and Docker is not running.
- A new `AreaType` enum value is needed (requires shared `enums.py` change — cross-lane).
- Area schema changes would break evidence-area linkage in Lane C.
