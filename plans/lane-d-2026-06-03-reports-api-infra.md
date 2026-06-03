# Lane D — Reports + API + Platform Infrastructure

## Goal

Complete MILESTONE_MAP.md Level 7 (reproducible report vertical slice) and lay groundwork for Levels 8-10.

## Non-goals

- No live connectors (Level 8).
- No non-developer user workflow (Level 9).
- No production ops/security/observability (Level 10).
- Do not modify Lane A, B, or C module files.

## Current state

- `ReportRunContract` stub in `backend/app/domain/report_contracts.py`.
- `JobStatus` enum in `backend/app/domain/enums.py`.
- `backend/app/reports/` and `backend/app/api/` module directories exist (empty `__init__.py`).
- `backend/tests/reports/` and `backend/tests/api/` test directories exist.
- `docker-compose.yml` at repo root (Lane A owns; Lane D reads).
- Lane A's TA-060 (DB smoke) is a hard prerequisite for integration wiring.

## Blockers at lane setup

Lane D's integration work is BLOCKED until:
1. Lane A completes TA-060 (DB smoke passes, migrations applied).
2. Lane B completes TB-010 (AreaService + InMemoryAreaRepository ready).
3. Lane C completes TC-030 (ClaimService ready).

**During the blocking period**, Lane D should work on:
- docker-compose confirmation (can Lane D start the DB?).
- API scaffold (thin FastAPI routers for sources, areas, evidence, reports).
- Report contract finalization (`ReportRunContract` fields complete).
- Integration tests using ALL in-memory repositories (no real DB).

## Proposed design

Phase 1 (in-memory, available now): wire A/B/C in-memory repositories together via report service.
Phase 2 (DB): swap in SQLAlchemy repositories; report runs persisted to `reports.report_runs`.

## Bottom-up sequence

### TD-010: Database infrastructure confirmation
1. Confirm Docker is running: `docker compose up -d db`.
2. If running: record DB smoke result in `state/VALIDATION_LOG.md`.
3. If not running: record blocker in `state/lane-d-state.md`. Continue with in-memory work.

### TD-020: API scaffold — thin FastAPI routers
1. Create `backend/app/api/sources.py` router (GET /sources, POST /sources — delegates to Lane A's SourceService).
2. Create `backend/app/api/areas.py` router (GET /areas, POST /areas — delegates to Lane B's AreaService).
3. Create `backend/app/api/evidence.py` router (GET /evidence — delegates to Lane C's EvidenceService).
4. Create `backend/app/api/reports.py` router (POST /report-runs, GET /report-runs/{id}).
5. Register all routers in `backend/app/main.py`.
6. Tests: 2xx response for each endpoint; 422 for bad input.

### TD-030: ReportRunService (in-memory)
1. Create `backend/app/reports/service.py` with `ReportRunService`.
2. `ReportRunService` accepts lane A/B/C service instances.
3. `create_report_run(area_id, intent_code) -> ReportRunContract`:
   - Validates area exists (via AreaExistsProtocol).
   - Collects evidence for area from EvidenceService.
   - Runs ClaimService to generate claims.
   - Returns populated ReportRunContract with claims, unknowns, caveats.
4. Uses only in-memory repositories — no live DB needed.
5. Tests: fixture area + fixture evidence → report run with claims + unknowns.

### TD-040: Persisted report runs (BLOCKED on Lane A TA-060)
1. Add `ReportRunModel` SQLAlchemy ORM model in `backend/app/reports/models.py`.
2. Add `SqlAlchemyReportRunRepository`.
3. Store report runs in `reports.report_runs` table.
4. Update integration test to use DB.

### TD-050: Implement SourceExistsProtocol + AreaExistsProtocol adapters
1. Create `backend/app/reports/adapters.py` with:
   - `SourceServiceProtocolAdapter(source_service: SourceService)` implementing `SourceExistsProtocol`
   - `AreaServiceProtocolAdapter(area_service: AreaService)` implementing `AreaExistsProtocol`
2. Wire adapters into `EvidenceService` constructor in the report pipeline.
3. Tests confirm source-failure evidence is created when source is not registered.

## Files likely to change

| File | Expected change |
|---|---|
| `backend/app/api/sources.py` | New: FastAPI router |
| `backend/app/api/areas.py` | New: FastAPI router |
| `backend/app/api/evidence.py` | New: FastAPI router |
| `backend/app/api/reports.py` | New: FastAPI router |
| `backend/app/main.py` | Register new routers |
| `backend/app/reports/service.py` | New: ReportRunService |
| `backend/app/reports/adapters.py` | New: Protocol adapters |
| `backend/app/reports/models.py` | New: SQLAlchemy ORM model (deferred) |
| `state/lane-d-state.md` | Update after each task |
| `state/VALIDATION_LOG.md` | DB connectivity and smoke results |

## Tests / verification

```bash
pytest backend/tests/reports/ backend/tests/api/ -v
mypy backend/app/reports backend/app/api
./scripts/verify.sh
# Full integration:
docker compose up -d db && RUN_DB_SMOKE=1 ./scripts/verify.sh
```

## Risks and blockers

| Blocker | Status | Impact |
|---|---|---|
| Lane A TA-060 DB smoke | Blocked | TD-040 cannot proceed |
| Lane B TB-010 AreaService | Pending | TD-030 uses stub until done |
| Lane C TC-030 ClaimService | Pending | TD-030 uses stub until done |
| docker-compose.yml changes | Lane A owns | Request changes through Lane A |

## Decision log

- 2026-06-03: Lane D owns reports, API, and integration (MILESTONE Levels 7+).
- 2026-06-03: Phase 1 (in-memory integration) does not need DB. Phase 2 does.
- 2026-06-03: docker-compose.yml owned by Lane A; Lane D reads only.

## Progress log

- 2026-06-03: Lane scaffold created. ReportRunContract stub defined. Test directories ready.
