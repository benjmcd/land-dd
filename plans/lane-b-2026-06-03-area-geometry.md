# Lane B — Area + Geometry Domain

## Goal

Complete MILESTONE_MAP.md Level 4: the system can represent, validate, store, and (eventually) spatially query areas of interest.

## Non-goals

- No source registry, evidence, claims, or report work.
- No live PostGIS spatial queries until DB is running (use in-memory validation).
- No jurisdiction-specific geometry assumptions.

## Current state

- `AreaContract` stub in `backend/app/domain/area_contracts.py` (fields: area_id, area_type, label, geom_geojson, geom_source, geom_confidence, geom_validated).
- `AreaType` and `ConfidenceBand` enums in `backend/app/domain/enums.py`.
- `backend/app/area_geometry/` module directory exists (empty `__init__.py`).
- `backend/tests/area_geometry/` test directory exists (empty `__init__.py`).
- DB table `core.areas` exists in `db/migrations/0001_initial_spine.sql`.

## Proposed design

Build bottom-up: area contract → in-memory repository → geometry validation service → fixture geometries → PostGIS-backed repository (deferred until Docker available).

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

### TB-050: SQLAlchemy ORM model (BLOCKED on Lane A DB work)
1. Create `backend/app/area_geometry/models.py` with `AreaModel`.
2. Add `SqlAlchemyAreaRepository` (depends on Lane A's migration applying).
3. Record blocker until Lane A completes TA-060.

## Files likely to change

| File | Expected change |
|---|---|
| `backend/app/area_geometry/area_repo.py` | New: AreaRepository Protocol + InMemoryAreaRepository |
| `backend/app/area_geometry/service.py` | New: AreaService |
| `backend/app/area_geometry/geometry_validator.py` | New: GeoJSON validation |
| `backend/app/domain/area_contracts.py` | Possible additions (new fields) |
| `tests/fixtures/geometries/` | New: GeoJSON fixture files |
| `state/lane-b-state.md` | Update after each task |

## Tests / verification

```bash
pytest backend/tests/area_geometry/ -v
mypy backend/app/area_geometry backend/app/domain/area_contracts.py
./scripts/verify.sh
```

## Risks and blockers

| Blocker | Status | Impact |
|---|---|---|
| PostGIS spatial queries | Blocked until Docker+Lane A | TB-050 deferred |
| `AreaType` new values | Shared enum — needs cross-lane PR | Stop if new type needed |

## Decision log

- 2026-06-03: Lane B owns area geometry domain (MILESTONE Level 4).
- 2026-06-03: In-memory validation first; PostGIS deferred until DB ready.
- 2026-06-03: Parcel-like geometry always caveated as non-survey (L4-007).

## Progress log

- 2026-06-03: Lane scaffold created. `AreaContract` stub defined. Test directory created.
