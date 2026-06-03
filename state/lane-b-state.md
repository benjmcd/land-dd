# Lane B State — Area + Geometry Domain

```text
Current milestone: Level 4 - Area + Geometry Domain (in-memory fixture slice)
Target milestone: Level 4 (Area + Geometry Domain)
Milestone status: PARTIAL
Last verified: 2026-06-03
Verification command(s):
- pytest backend/tests/area_geometry/ -v
- mypy backend/app/area_geometry backend/app/domain/area_contracts.py
- ./scripts/verify.sh
Verification result:
- 16 Lane B tests passing
- Lane B targeted mypy passes for area geometry service/tests
- Full verification passes: 64 tests; lint clean; mypy clean (51 source files)
Failed or blocked gates:
- L4-001/L4-002: Basic polygon/multipolygon validation passes in memory
- L4-006/L4-007: Geometry source/confidence fields exist; parcel-like areas are caveated as non-survey in service behavior
- L4-008: PASS for current fixture scope (polygon, multipolygon, invalid, empty, wrong SRID, and large geometry)
- L4-003: PARTIAL (AreaContract defaults to SRID 4326; persisted SRID still pending)
- L4-004/L4-005/L4-010: BLOCKED/PENDING until PostGIS-backed area storage, metrics, spatial queries, and versioned geometry exist
Completion evidence:
- plans/lane-b-2026-06-03-area-geometry.md
- backend/app/domain/area_contracts.py (AreaContract with default SRID 4326)
- backend/tests/area_geometry/test_area_contracts.py (scaffold contract test)
- backend/app/area_geometry/area_repo.py (AreaRepository Protocol + InMemoryAreaRepository)
- backend/app/area_geometry/service.py (AreaService)
- backend/app/area_geometry/geometry_validator.py (GeoJSON polygon/multipolygon, SRID, CRS, and ring validation)
- backend/tests/area_geometry/test_area_service.py (service and validator tests)
- tests/fixtures/geometries/ (valid and invalid GeoJSON fixtures)
Next lowest-dependency task:
- TB-050: SQLAlchemy/PostGIS area model and repository (blocked until Lane A TA-060 DB smoke is available)
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
