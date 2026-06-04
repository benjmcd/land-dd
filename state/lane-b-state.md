# Lane B State — Area + Geometry Domain

```text
Current milestone: Level 4 - Area + Geometry Domain
Target milestone: Level 4 (Area + Geometry Domain)
Milestone status: PASS
Last verified: 2026-06-04
Verification command(s):
- py -3.12 -m pytest -q tests/area_geometry/test_area_service.py
- py -3.12 -m pytest -q tests/area_geometry
- $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/area_geometry
- ruff check app/area_geometry app/domain/area_contracts.py tests/area_geometry
- mypy app/area_geometry app/domain/area_contracts.py tests/area_geometry
- $env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
Verification result:
- 49 Lane B tests passing with DB smoke enabled
- Lane B targeted ruff passes
- Lane B targeted mypy passes for 10 area source/test files
- Full PowerShell verification passes after landing TB-100 on root `main`: 255 tests; lint clean; mypy clean (91 source files); DB smoke passes
Failed or blocked gates:
- No Level 4 blockers remain in the current fixture-backed DB repository path.
- L4-001/L4-002: Polygon/multipolygon validation passes in memory and DB-backed repository round-trips both fixture shapes through PostGIS
- L4-003: PASS for current repository path (`core.areas` stores and returns SRID 4326)
- L4-004: PASS for current repository path (PostGIS-derived geodesic area, centroid, bbox, and SRID read model is DB-tested)
- L4-005: PASS for current fixture-backed repository path (PostGIS intersects/contains/distance/intersection-area relation helper is DB-tested for polygon/multipolygon comparison geometry)
- L4-006/L4-007: Geometry source/confidence fields exist and round-trip through PostGIS; parcel-like areas are caveated as non-survey in service behavior
- L4-008: PASS for current fixture scope (polygon, multipolygon, invalid, empty, wrong SRID, and large geometry)
- L4-008 hardening: PASS for coordinate sanity in current fixture scope; non-finite coordinates and out-of-range EPSG:4326 longitude/latitude positions now fail validation before persistence
- L4-009: PASS/N/A for current scope because no geometry simplification path exists; canonical PostGIS geometry is not simplified or overwritten for display
- L4-010: PASS for current repository path (geometry replacement stores immutable prior-geometry rows in `core.area_versions`; version sequencing and rollback behavior are DB-tested)
- Level 4 supported-area-type coverage: PASS for current repository path. `parcel_like`, `drawn_polygon`, `multi_polygon`, `locality`, `buffer`, and `generated_candidate` round-trip through `core.areas`; exact domain type is preserved in `metadata.domain_area_type` when DB buckets are broader than domain names.
Completion evidence:
- plans/lane-b-2026-06-03-area-geometry.md
- backend/app/domain/area_contracts.py (AreaContract + AreaMetricsContract + AreaSpatialRelationContract + AreaVersionContract)
- backend/tests/area_geometry/test_area_contracts.py (scaffold contract test)
- backend/app/area_geometry/area_repo.py (AreaRepository Protocol + InMemoryAreaRepository + SqlAlchemyAreaRepository)
- backend/app/area_geometry/models.py (AreaModel for `core.areas`, AreaVersionModel for `core.area_versions`)
- backend/app/area_geometry/service.py (AreaService)
- backend/app/area_geometry/geometry_validator.py (GeoJSON polygon/multipolygon, SRID, CRS, ring, finite coordinate, and EPSG:4326 bounds validation)
- backend/tests/area_geometry/test_area_service.py (service and validator tests)
- backend/tests/area_geometry/test_sqlalchemy_area_repo.py (PostGIS repository/model tests)
- tests/fixtures/geometries/ (valid and invalid GeoJSON fixtures)
Next lowest-dependency task:
- No Lane B-owned blocker remains; repo-wide next dependency is Lane D D-004 Level 8 connector ownership and fixture-only acceptance planning before connector runtime code
Do not work on yet:
- Broader spatial query/source-feature geometry support without a scoped plan
- Any Lane A/C/D files
```

## Known blockers

| Item | Status | Impact |
|---|---|---|
| Area versioning | Complete for current repository path | Immutable prior-geometry rows, version sequencing, and rollback behavior are DB-tested |
| New AreaType enum values | Requires shared enums.py change | Stop if needed |
| Domain/DB area-type mapping | Complete for current repository path | Exact domain area type is stored in `metadata.domain_area_type`; `multi_polygon` uses DB `polygon`, and `buffer` uses DB `generated_candidate` |

## Active plan

`plans/lane-b-2026-06-03-area-geometry.md`

## Lane-specific verification commands

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/area_geometry
ruff check app/area_geometry app/domain/area_contracts.py tests/area_geometry
mypy app/area_geometry app/domain/area_contracts.py tests/area_geometry
Set-Location ..
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```
