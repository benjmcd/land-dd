# Lane D — Reports + API + Platform Infrastructure

## Goal

Build toward MILESTONE_MAP.md Level 7 (reproducible report vertical slice) and lay groundwork for Levels 8-10.

## Non-goals

- No live connectors (Level 8).
- No non-developer user workflow (Level 9).
- No production ops/security/observability (Level 10).
- Do not modify Lane A, B, or C module files.

## Current state

- `ReportRunContract` includes evidence, claims, unknowns, red flags, verification tasks, caveats, source manifest, and artifact metadata.
- `JobStatus` enum in `backend/app/domain/enums.py`.
- `backend/app/reports/` and `backend/app/api/` module directories exist.
- Thin API routers exist for sources, areas, evidence, and report runs, backed by per-app in-memory services.
- `backend/tests/reports/` and `backend/tests/api/` test directories exist.
- 16 Lane D report/API tests pass, including the persisted report-run repository round-trip.
- `docker-compose.yml` at repo root (Lane A owns; Lane D reads).
- Lane A's TA-060 (DB smoke) now passes; report persistence can use the live local Postgres/PostGIS stack.
- Lane D is a partial report-run harness, not a complete Level 7 vertical slice: default API wiring remains in-memory, and durable area/evidence/claim/rule-execution persistence is still lower-layer work.
- Session 2 split the unsupported-category work by lane ownership: Lane C owns C-002 rule/claim behavior; Lane D owns D-000 report/API surfacing after C-002.
- `backend/app/db/session.py` now provides D-001 pre-work by delegating `get_db_session()` to the shared `get_session()` factory; DB service wiring in `api/dependencies.py`/`main.py` remains blocked until C-002 and D-000 complete.

## Blockers at lane setup

Lane D has no blocking dependency for the report-run harness slice. Complete Level 7 still depends on Lane B area persistence, Lane C durable evidence/claim/rule-execution persistence, and shared-schema alignment before any `schemas/*.json` edit.

## Proposed design

Phase 1 (in-memory, available now): wire A/B/C in-memory repositories together via report service.
Phase 2 (DB): swap in SQLAlchemy repositories; report runs persisted to `reports.report_runs` and a machine-readable JSON artifact under `OBJECT_STORE_ROOT`.

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
7. Status: COMPLETE for the in-memory API scaffold. Endpoints are backed by isolated per-app in-memory services and do not require DB or live connectors.

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
6. Status: COMPLETE for the in-memory fixture scope. Report runs remain in app memory and are not durable.

### TD-040: Persisted report runs (COMPLETE)
1. Add `ReportRunModel` SQLAlchemy ORM model in `backend/app/reports/models.py`.
2. Add `SqlAlchemyReportRunRepository`.
3. Store report runs in `reports.report_runs` table.
4. Update integration test to use DB.
5. Status: COMPLETE for the repository harness. Report runs now persist through the repository abstraction, write a machine-readable artifact, and round-trip through a fresh DB session; underlying evidence/claim/rule-execution lineage remains lower-layer follow-up work.

### TD-050: Implement SourceExistsProtocol + AreaExistsProtocol adapters
1. Create `backend/app/reports/adapters.py` with:
   - `SourceServiceProtocolAdapter` implementing `SourceExistsProtocol`
   - `AreaServiceProtocolAdapter` implementing `AreaExistsProtocol`
2. Wire adapters into `EvidenceService` constructor in the report pipeline.
3. Tests confirm adapter-backed `EvidenceService` preserves production-use guardrails and still creates source-failure evidence for registered sources.
4. Status: COMPLETE for the in-memory protocol adapter wiring.

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
| `backend/app/reports/models.py` | New: SQLAlchemy ORM model |
| `backend/app/reports/report_repo.py` | New: in-memory and SQLAlchemy report repositories |
| `docs/adr/lane-d-0001-report-persistence.md` | New: report persistence ADR |
| `state/lane-d-state.md` | Update after each task |
| `state/VALIDATION_LOG.md` | DB connectivity and smoke results |

## Tests / verification

```bash
pytest backend/tests/reports/ backend/tests/api/ -v
mypy backend/app/reports backend/app/api
.\scripts\verify.ps1
# Full integration:
docker compose up -d db
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

## Risks and blockers

| Blocker | Status | Impact |
|---|---|---|
| Shared-schema alignment for `schemas/*.json` | Pending | Future payload changes need a coordinated contract pass |
| Lane A SourceExistsProtocol | Available for in-memory wiring | TD-030/TD-050 can adapt SourceService production-use checks |
| Lane B TB-010 AreaService | Available for in-memory wiring | TD-030 can use AreaService after Lane C ClaimService exists |
| Lane C TC-030 ClaimService | Available | TD-030 can use ClaimService and RuleEngine in-memory slices |
| Lane C C-002 unsupported-category claims | Pending | D-000 report surfacing and full D-001 DB-backed API workflow must wait for this |
| docker-compose.yml changes | Lane A owns | Request changes through Lane A |

## Decision log

- 2026-06-03: Lane D owns reports, API, and integration (MILESTONE Levels 7+).
- 2026-06-03: Phase 1 (in-memory integration) does not need DB. Phase 2 does.
- 2026-06-03: docker-compose.yml owned by Lane A; Lane D reads only.
- 2026-06-03: Persisted report runs use the existing `reports.report_runs` table plus `OBJECT_STORE_ROOT` JSON artifacts. The in-memory scaffold remains available for fixture tests.

## Progress log

- 2026-06-03: Lane scaffold created. ReportRunContract stub defined. Test directories ready.
- 2026-06-03: TD-020 complete for the in-memory API scaffold. Added per-app in-memory API services, source/area/evidence/report-run routers, router registration, and API contract tests for happy paths and representative 422 cases. Lane D tests: 7 passing. Full verification: 122 tests, ruff clean, mypy clean (65 source files); DB smoke skipped.
- 2026-06-03: TD-030 complete for the in-memory report-run service. Added ReportRunService, populated ReportRunContract fields, API report-run service wiring, and fixture tests for evidence-linked claims/unknowns/caveats, no-evidence caveat handling, and repeatable claim reuse. Lane D tests: 11 passing. Full verification: 126 tests, ruff clean, mypy clean (67 source files); DB smoke skipped because Docker Desktop Linux engine is unavailable.
- 2026-06-03: TD-050 complete for the in-memory protocol adapter wiring. Added `backend/app/reports/adapters.py`, wired `SourceServiceProtocolAdapter` and `AreaServiceProtocolAdapter` into `EvidenceService` construction, and added adapter-focused tests for delegation plus production-use/source-failure guardrails. Lane D tests: 15 passing. Full verification: 172 tests, ruff clean, mypy clean (69 source files); DB smoke skipped because Docker Desktop Linux engine is unavailable.
- 2026-06-03: TD-040 complete for persisted report runs. Added `backend/app/reports/models.py`, `backend/app/reports/report_repo.py`, a SQLAlchemy-backed `reports.report_runs` round-trip test, and `docs/adr/lane-d-0001-report-persistence.md`. Lane D tests: 16 passing. Full verification: 173 tests, ruff clean, mypy clean (72 source files); DB smoke passes on the local Postgres/PostGIS container.
- 2026-06-04: Session 2 D-001 pre-work complete for the DB session dependency. Added `backend/app/db/session.py` and `backend/tests/api/test_db_session.py`; split D-000 report surfacing from Lane C C-002 in coordination docs. Lane D tests: 17 passing. Full verification: 243 tests, ruff clean, mypy clean (87 source files); DB smoke passes.
- 2026-06-04: Added API regression proving existing source-failure UNKNOWN claims appear in `POST /report-runs` response unknowns and cost metrics. This supports D-000 report surfacing once Lane C C-002 provides unsupported-category unknown claims. Lane D tests: 18 passing. Full verification: 244 tests, ruff clean, mypy clean (87 source files); DB smoke passes.
