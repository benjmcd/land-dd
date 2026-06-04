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
- Thin API routers exist for sources, areas, evidence, and report runs, backed by per-app in-memory services by default and by request-scoped SQLAlchemy services when `create_app(use_db_services=True)`.
- `backend/tests/reports/` and `backend/tests/api/` test directories exist.
- 20 Lane D report/API tests pass with DB smoke enabled, including the persisted report-run repository round-trip, DB-backed API create/retrieve workflow, report artifact semantic regression, API source-failure unknown surfacing regression, and D-000 unsupported-category report surfacing.
- `docker-compose.yml` at repo root (Lane A owns; Lane D reads).
- Lane A's TA-060 (DB smoke) now passes; report persistence can use the live local Postgres/PostGIS stack.
- Lane D now has a fixture-backed Level 7 report/API vertical slice: default API wiring remains in-memory for cheap scaffold tests, and explicit DB mode wires existing SQLAlchemy repositories through the API workflow.
- Session 2 split the unsupported-category work by lane ownership: Lane C owns C-002 rule/claim behavior; Lane D owns D-000 report/API surfacing after C-002.
- `backend/app/db/session.py` provides the DB session dependency by delegating `get_db_session()` to the shared `get_session()` factory; API DB mode commits successful requests and rolls back failed requests in `api/dependencies.py`.
- D-000 is complete: report runs create stored unsupported-category SOURCE_FAILURE evidence for missing not-evaluated domains before rule evaluation, and report/API output surfaces those claims in `unknowns`.
- D-001 is complete: `POST /areas`, `POST /report-runs`, and `GET /report-runs/{id}` work through SQLAlchemy-backed API services, persisted report artifacts, and non-null seeded `intent_id` linkage.
- D-002 is complete: a normalized Lane D regression test fixes the stable semantic shape of the generated fixture report artifact while ignoring dynamic UUID/timestamp/path fields.
- TD-080 is complete: `schemas/report_run_schema.json` represents serialized `ReportRunContract`, references Lane C evidence/claim schemas for nested arrays, and is guarded by report schema-contract parity tests.
- TD-081 is complete: `schemas/report_run_schema.json` now constrains stable generated `source_manifest`, `source_details`, `artifact_metadata`, and `cost_metrics` keys while preserving extension fields and avoiding runtime/API/DB behavior changes.
- TD-090 is complete: `docs/planning_pack/api/openapi_stub.yaml` is regenerated from the live FastAPI app, and a planning-pack test guards it against drift from `create_app().openapi()`.
- CON-021 is complete as a planning-only connector human-review action semantics slice. It defines future action vocabulary before any API mutation route, worker, scheduler, dashboard, or connector runtime change.

## Blockers at lane setup

Lane D has no blocking dependency for the fixture-backed Level 7 report/API slice. Source/evidence/claim/report root schemas are now aligned to serialized domain contracts, stable generated report manifest metadata is schema-constrained, the planning-pack OpenAPI reference is aligned to the generated FastAPI contract, and connector human-review action semantics are planned. Source provenance-family schemas, job schema, API mutation routes, and new report metadata extensions remain future coordinated work.

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

### TD-060: DB-backed API workflow (COMPLETE)
1. Add explicit DB service mode in `backend/app/api/dependencies.py` and `backend/app/main.py`.
2. Build SQLAlchemy-backed source, area, evidence, claim, and report services per request.
3. Commit successful DB API requests and roll back failed requests in the API dependency.
4. Keep default API wiring in-memory for fast fixture tests.
5. Add a DB-backed API integration test for `POST /areas`, `POST /report-runs`, `GET /report-runs/{id}`, persisted report row, non-null `intent_id`, unsupported-category unknowns, and report artifact path.
6. Status: COMPLETE for the fixture-backed Level 7 DB API workflow.

### TD-070: Level 7 report artifact regression (COMPLETE)
1. Add a Lane D report regression test for the generated fixture report artifact.
2. Project out dynamic UUIDs, timestamps, and path fields.
3. Assert stable report semantics: status, intent, source manifest, evidence, claims, unknowns, red flags, caveats, and artifact metadata.
4. Status: COMPLETE for the report artifact regression closeout slice.

### TD-080: Report-run schema contract (COMPLETE)
1. Add `schemas/report_run_schema.json` as the serialized `ReportRunContract` schema.
2. Reference Lane C evidence and claim schema IDs for nested report arrays instead of duplicating nested contracts in Lane D.
3. Keep `source_manifest` and `artifact_metadata` open objects for TD-080; TD-081 later tightens their stable generated report artifact keys while preserving extension fields.
4. Add schema-contract tests for field parity, required-field parity, enum parity, and nested schema references.
5. Status: COMPLETE for the Level 7 report JSON schema requirement.

### TD-081: Report manifest metadata schema tightening (COMPLETE)

1. Tighten `source_manifest` around the stable generated report keys: source IDs, source/evidence/claim counts, ruleset identity, source names, and per-source details.
2. Tighten `source_details` around source governance fields emitted by `ReportRunService`, including parity with the current Lane A `AuthorityLevel` enum values.
3. Tighten `artifact_metadata` around report artifact identity, schema identity, optional persistence/output URIs, and non-negative cost metrics.
4. Keep `additionalProperties: true` for nested metadata maps so future report artifact extensions remain additive.
5. Record ADR `docs/adr/lane-d-0010-report-manifest-metadata.md`; no API route behavior, runtime validation, DB schema, connector behavior, source provenance-family schema, job schema, OpenAPI, live I/O, hook config, or POSIX script change is introduced.
6. Status: COMPLETE for generated report manifest metadata schema tightening.

### TD-090: Planning-pack OpenAPI refresh (COMPLETE)
1. Treat `backend/app/main.py` and `create_app().openapi()` as the live API authority.
2. Regenerate `docs/planning_pack/api/openapi_stub.yaml` from the FastAPI app instead of hand-editing route claims.
3. Update planning-pack API docs to separate implemented endpoints from future roadmap endpoints.
4. Add a parity test so future route/model changes fail closed when the planning-pack OpenAPI reference drifts.
5. Status: COMPLETE for the planning-pack current API reference refresh.

## Files likely to change

| File | Expected change |
|---|---|
| `backend/app/api/sources.py` | New: FastAPI router |
| `backend/app/api/areas.py` | New: FastAPI router |
| `backend/app/api/evidence.py` | New: FastAPI router |
| `backend/app/api/reports.py` | New: FastAPI router |
| `backend/app/main.py` | Register new routers |
| `backend/app/api/dependencies.py` | DB-backed API service factory and request-scoped dependency |
| `backend/app/reports/service.py` | New: ReportRunService |
| `backend/app/reports/adapters.py` | New: Protocol adapters |
| `backend/app/reports/models.py` | New: SQLAlchemy ORM model |
| `backend/app/reports/report_repo.py` | New: in-memory and SQLAlchemy report repositories |
| `backend/tests/api/test_report_runs_db.py` | DB-backed report-run API integration test |
| `backend/tests/reports/test_report_regression.py` | Normalized fixture report artifact regression |
| `schemas/report_run_schema.json` | Report-run JSON schema contract |
| `backend/tests/reports/test_report_schema_contract.py` | Report schema-contract parity tests |
| `docs/planning_pack/api/openapi_stub.yaml` | FastAPI-generated current API reference |
| `backend/tests/test_planning_pack_schema_copies.py` | Planning-pack schema/OpenAPI parity tests |
| `docs/adr/lane-d-0009-report-run-schema.md` | Report-run schema decision |
| `docs/adr/lane-d-0010-report-manifest-metadata.md` | Report manifest metadata schema decision |
| `docs/adr/lane-d-0011-connector-human-review-actions.md` | Connector human-review action semantics decision |
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
| Shared-schema alignment for `schemas/*.json` | Source/evidence/claim/report root schemas aligned; stable generated report manifest metadata tightened; planning-pack OpenAPI aligned to generated FastAPI contract | Source provenance-family schemas, job schema, API mutation routes, and new report metadata extensions remain future coordinated passes |
| Lane A SourceExistsProtocol | Available for in-memory wiring | TD-030/TD-050 can adapt SourceService production-use checks |
| Lane B TB-010 AreaService | Available for in-memory wiring | TD-030 can use AreaService after Lane C ClaimService exists |
| Lane C TC-030 ClaimService | Available | TD-030 can use ClaimService and RuleEngine in-memory slices |
| Lane C C-002 unsupported-category claims | Complete on `main` | D-000 report surfacing is complete; D-001 DB-backed API workflow is now next |
| DB-backed API workflow | Complete | D-001 wires SQLAlchemy repositories through the API workflow without changing default in-memory tests |
| docker-compose.yml changes | Lane A owns | Request changes through Lane A |

## Decision log

- 2026-06-03: Lane D owns reports, API, and integration (MILESTONE Levels 7+).
- 2026-06-03: Phase 1 (in-memory integration) does not need DB. Phase 2 does.
- 2026-06-03: docker-compose.yml owned by Lane A; Lane D reads only.
- 2026-06-03: Persisted report runs use the existing `reports.report_runs` table plus `OBJECT_STORE_ROOT` JSON artifacts. The in-memory scaffold remains available for fixture tests.
- 2026-06-04: API DB mode is explicit (`create_app(use_db_services=True)`) so default scaffold tests remain in-memory while DB integration tests exercise the Postgres/PostGIS system of record.
- 2026-06-04: `schemas/report_run_schema.json` is the serialized `ReportRunContract` schema. Nested evidence and claim arrays reference the lane-owned schemas; ADR Lane D 0010 tightens stable generated `source_manifest`, `source_details`, `artifact_metadata`, and `cost_metrics` keys while keeping extension fields open.

## Progress log

- 2026-06-03: Lane scaffold created. ReportRunContract stub defined. Test directories ready.
- 2026-06-03: TD-020 complete for the in-memory API scaffold. Added per-app in-memory API services, source/area/evidence/report-run routers, router registration, and API contract tests for happy paths and representative 422 cases. Lane D tests: 7 passing. Full verification: 122 tests, ruff clean, mypy clean (65 source files); DB smoke skipped.
- 2026-06-03: TD-030 complete for the in-memory report-run service. Added ReportRunService, populated ReportRunContract fields, API report-run service wiring, and fixture tests for evidence-linked claims/unknowns/caveats, no-evidence caveat handling, and repeatable claim reuse. Lane D tests: 11 passing. Full verification: 126 tests, ruff clean, mypy clean (67 source files); DB smoke skipped because Docker Desktop Linux engine is unavailable.
- 2026-06-03: TD-050 complete for the in-memory protocol adapter wiring. Added `backend/app/reports/adapters.py`, wired `SourceServiceProtocolAdapter` and `AreaServiceProtocolAdapter` into `EvidenceService` construction, and added adapter-focused tests for delegation plus production-use/source-failure guardrails. Lane D tests: 15 passing. Full verification: 172 tests, ruff clean, mypy clean (69 source files); DB smoke skipped because Docker Desktop Linux engine is unavailable.
- 2026-06-03: TD-040 complete for persisted report runs. Added `backend/app/reports/models.py`, `backend/app/reports/report_repo.py`, a SQLAlchemy-backed `reports.report_runs` round-trip test, and `docs/adr/lane-d-0001-report-persistence.md`. Lane D tests: 16 passing. Full verification: 173 tests, ruff clean, mypy clean (72 source files); DB smoke passes on the local Postgres/PostGIS container.
- 2026-06-04: Session 2 D-001 pre-work complete for the DB session dependency. Added `backend/app/db/session.py` and `backend/tests/api/test_db_session.py`; split D-000 report surfacing from Lane C C-002 in coordination docs. Lane D tests: 17 passing. Full verification: 243 tests, ruff clean, mypy clean (87 source files); DB smoke passes.
- 2026-06-04: Added API regression proving existing source-failure UNKNOWN claims appear in `POST /report-runs` response unknowns and cost metrics. This supports D-000 report surfacing once Lane C C-002 provides unsupported-category unknown claims. Lane D tests: 18 passing. Full verification: 244 tests, ruff clean, mypy clean (87 source files); DB smoke passes.
- 2026-06-04: Session 2 read-only coordination check found C-002 is still not canonical on root `main`; the Session 1 worktree is mid-conflict in state logs, and the draft branch still marks the four unsupported-category rules as `informational`. Sent Session 1 a coordination note and kept D-000/D-001 blocked until C-002 lands with `unknown` ruleset metadata.
- 2026-06-04: Merged Session 1 C-002 into root `main` after the severity metadata issue was corrected. Full verification with DB smoke enabled passes: 250 tests, lint clean, mypy clean (89 source files). D-000 is now the next Lane D task.
- 2026-06-04: D-000 complete. `ReportRunService` now creates stored unsupported-category SOURCE_FAILURE evidence for missing not-evaluated domains before rule evaluation, reuses the sentinel source on repeat report runs, and surfaces soil/septic, environmental hazards, resource context, and market context as UNKNOWN report/API claims. Lane D tests pass with DB smoke enabled: 18 tests; full verification passes with DB smoke enabled: 250 tests, lint clean, mypy clean (89 source files).
- 2026-06-04: D-001 complete. Added explicit DB-backed API service wiring, request-scoped DB service construction, successful-request commit/failed-request rollback, and a DB-backed API integration test proving `POST /areas`, `POST /report-runs`, `GET /report-runs/{id}`, persisted report row, non-null `intent_id`, unsupported-category UNKNOWNs, and artifact path. Lane D tests pass with DB smoke enabled: 19 tests.
- 2026-06-04: D-002 complete. Added `backend/tests/reports/test_report_regression.py` to assert the stable semantic shape of the generated fixture report artifact while ignoring dynamic IDs/timestamps/paths. Lane D report/API tests pass with DB smoke enabled: 20 tests.
- 2026-06-04: TD-080 complete. Added `schemas/report_run_schema.json`, report schema-contract parity tests, and ADR `lane-d-0009-report-run-schema`. Lane D report/API collection: 33 tests; full DB-enabled PowerShell verification: 339 tests, lint clean, mypy clean (120 source files), migrations/seeds apply, DB smoke passes.
- 2026-06-04: TD-081 complete. Tightened generated report manifest metadata schema keys, added ADR `lane-d-0010-report-manifest-metadata`, and extended report schema-contract tests without changing API, DB, connector behavior, runtime validation, live I/O, hook config, or POSIX scripts.
- 2026-06-04: TD-090 complete. Regenerated the planning-pack OpenAPI reference from `create_app().openapi()`, updated the planning-pack API spec to distinguish implemented routes from future roadmap routes, and added a parity test that fails closed on future OpenAPI drift.
- 2026-06-04: CON-021 complete as a planning-only human-review action semantics pass. Added ADR `lane-d-0011-connector-human-review-actions` without changing API behavior, connector runtime, queue code, schemas, migrations, live I/O, hook config, or POSIX scripts.
