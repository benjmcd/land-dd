# Lane B State — Area + Geometry Domain

```text
Current milestone: Level 1 — Governed Repo Scaffold (Lane B scaffold complete)
Target milestone: Level 4 (Area + Geometry Domain)
Milestone status: NOT_STARTED
Last verified: 2026-06-03
Verification command(s):
- pytest backend/tests/area_geometry/ -v
- mypy backend/app/area_geometry backend/app/domain/area_contracts.py
- ./scripts/verify.sh
Verification result:
- Lane B scaffold contract test passes; no AreaService feature tests yet; overall verify.sh passes
Failed or blocked gates:
- All L4 gates: NOT_STARTED (AreaService not yet implemented)
- L4-005: Spatial queries blocked until PostGIS available (Lane A DB dependency)
Completion evidence:
- plans/lane-b-2026-06-03-area-geometry.md
- backend/app/domain/area_contracts.py (stub)
- backend/tests/area_geometry/test_area_contracts.py (scaffold contract test)
Next lowest-dependency task:
- TB-010: Implement AreaService + InMemoryAreaRepository
Do not work on yet:
- PostGIS spatial queries (needs Lane A DB smoke to pass first)
- Any Lane A/C/D files
```

## Known blockers

| Item | Status | Impact |
|---|---|---|
| PostGIS spatial queries | Blocked on Lane A TA-060 | TB-050 (ORM model) deferred |
| New AreaType enum values | Requires shared enums.py change | Stop if needed |

## Active plan

`plans/lane-b-2026-06-03-area-geometry.md`

## Lane-specific verification commands

```bash
# Lane B unit tests only:
cd backend && PYTHONPATH=. pytest tests/area_geometry/ -v

# Lane B type check only:
cd backend && mypy app/area_geometry app/domain/area_contracts.py

# Full workspace gate:
./scripts/verify.sh
```
