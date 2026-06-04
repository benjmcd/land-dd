# Lane B — Area + Geometry Domain

## Goal

Complete MILESTONE_MAP.md Level 4: the system can represent, validate, store, and (eventually) spatially query areas of interest.

## Non-goals

- No source registry, evidence, claims, or report work.
- No broad or live-vendor spatial query layer; add only fixture-backed PostGIS queries after the repository contract is proven.
- No jurisdiction-specific geometry assumptions.

## Current state

- `AreaContract` in `backend/app/domain/area_contracts.py` includes area identity/type, GeoJSON payload, default SRID 4326, geometry source, confidence, and validated flag fields.
- `AreaMetricsContract` captures PostGIS-derived area, centroid, bbox, SRID, method, and measurement caveat.
- `AreaSpatialRelationContract` captures fixture-backed PostGIS intersects, contains, distance, intersection area, ratio, method, and caveat fields.
- `AreaVersionContract` captures immutable prior-geometry version rows from `core.area_versions`.
- `AreaType` and `ConfidenceBand` enums in `backend/app/domain/enums.py`.
- `AreaService`, `InMemoryAreaRepository`, `AreaModel`, `AreaVersionModel`, and `SqlAlchemyAreaRepository` exist in `backend/app/area_geometry/`.
- `geometry_validator.py` validates GeoJSON Polygon/MultiPolygon structure, SRID/CRS constraints, closed rings, finite coordinate values, and EPSG:4326 longitude/latitude bounds.
- `tests/fixtures/geometries/` contains valid, invalid, missing-type, wrong-SRID, open-ring, empty, and large GeoJSON fixtures.
- `backend/tests/area_geometry/` covers area contract defaults, metrics/relation/version contract behavior, service create/get behavior, duplicate rejection, parcel-like caveat behavior, fixture validation, PostGIS repository round-trips, all six Level 4 domain area types, PostGIS-derived metrics reads, PostGIS spatial relation helpers, and versioned geometry replacement.
- DB table `core.areas` exists in `db/migrations/0001_initial_spine.sql`.
- DB table `core.area_versions` exists in `db/migrations/0001_initial_spine.sql`.
- Post-PASS hardening: TB-100 closes the coordinate-sanity gap for non-finite values and out-of-range EPSG:4326 longitude/latitude positions.

## Proposed design

Current sequencing note: Level 4 is complete for the current fixture-backed DB repository path. Proceed to Lane C durable evidence-ledger/audit persistence before expanding spatial query breadth.

Build bottom-up: area contract -> in-memory repository -> geometry validation service -> fixture geometries -> PostGIS-backed repository -> area metrics/spatial queries -> area versioning.

## Bottom-up sequence

### TB-010: Area service and in-memory repository
1. Create `backend/app/area_geometry/area_repo.py` with `AreaRepository` Protocol + `InMemoryAreaRepository`.
2. Create `backend/app/area_geometry/service.py` with `AreaService`.
3. `AreaService.create(area: AreaContract)` validates basic geometry fields and stores.
4. `AreaService.get(area_id)` returns stored area.
5. Tests: create, get, get-missing. Run `pytest backend/tests/area_geometry/ -v`.

### TB-020: GeoJSON validation
1. Create `backend/app/area_geometry/geometry_validator.py` with `validate_geojson(geom: dict) -> list[str]`.
2. Validate: `type` must be `Polygon` or `MultiPolygon`; `coordinates` must be non-empty; basic ring closure check.
3. `AreaService.create` rejects invalid geometry with descriptive error.
4. Tests: valid polygon, valid multipolygon, wrong type, empty coordinates, missing type, nested invalid ring.

### TB-030: Fixture geometries
1. Create `tests/fixtures/geometries/` directory.
2. Add: `valid_polygon.geojson`, `valid_multipolygon.geojson`, `empty_coordinates.geojson`, `wrong_type.geojson`.
3. Tests load fixtures from files.

### TB-040: Geometry confidence and caveat
1. Add `geom_validated: bool = False` caveat behavior: parcel-like areas default to `geom_validated=False`.
2. Area service marks parcel-like geometry as NOT survey-quality (L4-007).
3. Tests: verify parcel-like area has geom_validated=False; drawn polygon can be validated.

### TB-050: SQLAlchemy ORM model
1. Create `backend/app/area_geometry/models.py` with `AreaModel`.
2. Add `SqlAlchemyAreaRepository` (depends on Lane A's migration applying).
3. Record DB-backed area repository progress in the lane state and validation log.

### TB-060: Area metrics/read model
1. Add a narrow contract for derived area geometry values that can be read from `core.areas`.
2. Use PostGIS generated `centroid` and `bbox` columns and explicit area calculation SQL without overwriting canonical geometry.
3. Tests: fixture polygon/multipolygon rows return deterministic SRID, centroid/bbox GeoJSON, and area measurement caveats.

### TB-070: Spatial query helpers
1. Add narrowly scoped repository methods for intersection/contains/distance checks needed by fixture evidence.
2. Keep query semantics in PostGIS and return conservative typed results, not claims.
3. Tests: positive, negative, empty, and wrong-SRID/invalid-input behavior.

### TB-080: Area versioning
1. Add repository behavior for inserting immutable `core.area_versions` rows.
2. Preserve prior geometry when an area geometry changes.
3. Tests: version number sequencing, no destructive overwrite, and rollback behavior.

### TB-090: Supported domain area-type mapping
1. Support `parcel_like`, `drawn_polygon`, `multi_polygon`, `locality`, `buffer`, and `generated_candidate` without changing the shared enum or DB enum.
2. Preserve exact domain area type in `core.areas.metadata.domain_area_type` when the DB enum bucket is broader than the domain term.
3. Fail closed if stored DB area type conflicts with metadata domain type.
4. Tests: all six domain area types round-trip and corrupt metadata is rejected.

### TB-100: Coordinate bounds and finite-value hardening
1. Keep the existing GeoJSON type/ring/SRID validation behavior.
2. Reject non-finite longitude/latitude values.
3. Reject longitude outside `-180..180` and latitude outside `-90..90`.
4. Add fixture-backed invalid-range coverage plus direct non-finite regression coverage.

## Files likely to change

| File | Expected change |
|---|---|
| `backend/app/area_geometry/area_repo.py` | New: AreaRepository Protocol + InMemoryAreaRepository |
| `backend/app/area_geometry/models.py` | New: AreaModel for `core.areas` |
| `backend/app/area_geometry/service.py` | New: AreaService |
| `backend/app/area_geometry/geometry_validator.py` | New: GeoJSON validation |
| `backend/app/domain/area_contracts.py` | Area and area-metrics contracts |
| `tests/fixtures/geometries/` | New: GeoJSON fixture files |
| `state/lane-b-state.md` | Update after each task |
| `backend/app/area_geometry/geometry_validator.py` | TB-100 coordinate bounds and finite-value checks |
| `backend/tests/area_geometry/test_area_service.py` | TB-100 validator/service regressions |
| `tests/fixtures/geometries/` | TB-100 invalid coordinate fixtures |

## Tests / verification

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/area_geometry
ruff check app/area_geometry app/domain/area_contracts.py tests/area_geometry
mypy app/area_geometry app/domain/area_contracts.py tests/area_geometry
Set-Location ..
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

## Risks and blockers

| Blocker | Status | Impact |
|---|---|---|
| Further spatial query breadth | Deferred | Current helper intentionally supports polygon/multipolygon fixture comparisons only |
| Domain/DB area-type mapping | Complete for current repository path | Exact domain type is preserved in `metadata.domain_area_type`; broader DB buckets are explicit |
| Full Level 4 maturity claim | Complete for current fixture-backed DB repository path | Lane B tests and full verification pass after all L4 gate fixes |
| `AreaType` new values | Shared enum — needs cross-lane PR | Stop if new type needed |

## Decision log

- 2026-06-03: Lane B owns area geometry domain (MILESTONE Level 4).
- 2026-06-03: In-memory validation first; PostGIS deferred until DB ready.
- 2026-06-03: Parcel-like geometry always caveated as non-survey (L4-007).
- 2026-06-04: Domain `multi_polygon` and `buffer` area types are not mapped to `core.area_type` until the schema/domain semantics are aligned.
- 2026-06-04: Area metrics are derived from PostGIS stored geometry; the read model must not overwrite canonical geometry or imply survey-quality acreage.
- 2026-06-04: Spatial relation helpers are repository-level screening facts only; they must not emit claims or legal boundary determinations.
- 2026-06-04: Geometry replacement must store the prior canonical geometry in `core.area_versions` before updating `core.areas`; version rows are immutable history, not claims.
- 2026-06-04: Exact domain area type is preserved in `core.areas.metadata.domain_area_type` when DB enum buckets are broader than domain names. `multi_polygon` stores in DB bucket `polygon`; `buffer` stores in DB bucket `generated_candidate`.
- 2026-06-04: Coordinate sanity belongs at the Lane B validator boundary. It is a screening validity check, not a claim or survey-quality assertion.

## Progress log

- 2026-06-03: Lane scaffold created. `AreaContract` stub defined. Test directory created.
- 2026-06-03: TB-010 through TB-040 complete for the in-memory fixture slice. Added `AreaRepository`, `InMemoryAreaRepository`, `AreaService`, GeoJSON/SRID validator, fixtures, and tests. Lane B tests: 16 passing. Full verification at TB-040: 49 tests, ruff clean, mypy clean (48 source files); DB smoke skipped.
- 2026-06-04: TB-050 complete for the DB-backed area repository slice. Added `AreaModel`, `SqlAlchemyAreaRepository`, PostGIS Polygon/MultiPolygon round-trip tests, and fail-closed domain/DB area-type mapping tests. Lane B tests: 22 passing with DB smoke enabled. Full PowerShell verification: 192 tests, ruff clean, mypy clean (78 source files), DB smoke passes.
- 2026-06-04: TB-060 complete for the PostGIS metrics read-model slice. Added `AreaMetricsContract`, `SqlAlchemyAreaRepository.get_metrics`, PostGIS geodesic area/centroid/bbox tests for Polygon and MultiPolygon fixtures, and negative-area contract validation. Lane B tests: 27 passing with DB smoke enabled. Full PowerShell verification: 197 tests, ruff clean, mypy clean (78 source files), DB smoke passes.
- 2026-06-04: TB-070 complete for the PostGIS spatial relation helper slice. Added `AreaSpatialRelationContract`, `SqlAlchemyAreaRepository.get_spatial_relation`, DB tests for contained/disjoint/missing/wrong-SRID/invalid comparison geometry, and screening-only caveats. Lane B tests: 35 passing with DB smoke enabled. Full PowerShell verification: 205 tests, ruff clean, mypy clean (78 source files), DB smoke passes.
- 2026-06-04: TB-080 complete for the current DB-backed area versioning slice. Added `AreaVersionContract`, `AreaVersionModel`, `SqlAlchemyAreaRepository.replace_geometry`, `SqlAlchemyAreaRepository.list_versions`, and DB tests for immutable prior-geometry storage, version sequencing, missing-area no-op, invalid replacement rejection, and rollback behavior. Lane B tests: 41 passing with DB smoke enabled. Full PowerShell verification: 211 tests, ruff clean, mypy clean (78 source files), DB smoke passes.
- 2026-06-04: TB-090 complete for supported domain area-type mapping. `SqlAlchemyAreaRepository` now stores exact domain type in `core.areas.metadata.domain_area_type`, maps `multi_polygon` to DB `polygon`, maps `buffer` to DB `generated_candidate`, and fails closed on conflicting metadata. Lane B tests: 46 passing with DB smoke enabled. Full PowerShell verification: 216 tests, ruff clean, mypy clean (78 source files), DB smoke passes.
- 2026-06-04: TB-100 selected as a low-conflict Session 1 Lane B hardening slice while Session 2 owns Lane D D-001. Scope is limited to finite/range coordinate validation and tests.
- 2026-06-04: TB-100 complete and reconciled with root `main` D-003. `validate_geojson` now rejects non-finite longitude/latitude values, longitude outside `-180..180`, and latitude outside `-90..90`; added fixture and inline regression coverage. Lane B tests: 49 passing with DB smoke enabled. Full post-D-003 PowerShell verification: 255 tests, ruff clean, mypy clean (91 source files), DB smoke passes.
