# Lane D State — Reports + API + Platform Infrastructure

```text
Current milestone: Level 7 - Reproducible Report Vertical Slice
Target milestone: Level 7 (Reproducible Report Vertical Slice)
Milestone status: PASS
Last verified: 2026-06-04
Verification command(s):
- cd backend; $env:PYTHONPATH='.'; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/reports tests/api
- cd backend; py -3.12 -m pytest -q tests/reports/test_report_regression.py
- cd backend; py -3.12 -m pytest -q tests/api tests/reports
- cd backend; ruff check app/api app/main.py app/reports tests/api tests/reports
- cd backend; mypy app/api app/main.py app/reports tests/api/test_report_runs_db.py
- .\scripts\verify.ps1
- cd backend; py -3.12 -m pytest -q tests/connectors/test_review_status.py tests/api/test_connector_review_status.py
- cd backend; py -3.12 -m pytest -q tests/connectors tests/api -rA
- cd backend; ruff check app/connectors app/api app/main.py tests/connectors tests/api
- cd backend; mypy app/connectors app/api app/main.py tests/connectors tests/api
- cd backend; $env:PYTHONPATH='.'; py -3.12 -m pytest --collect-only -q
- docker info --format '{{.ServerVersion}}'
Verification result:
- Connector/API review-status tests pass with 55 connector/API tests passing and 3 DB-gated skips when DB smoke is disabled
- Full verification passes locally with DB smoke enabled: 315 tests; lint clean; mypy clean (115 source files)
- ReportRunService composes source, area, evidence, claim, and rule services behind the report-run API scaffold
- ReportRunService now creates stored unsupported-category SOURCE_FAILURE evidence for missing not-evaluated domains before rule evaluation, and report/API output surfaces those claims in `unknowns`
- SqlAlchemyReportRunRepository persists report runs to `reports.report_runs`, writes a machine-readable artifact under `OBJECT_STORE_ROOT`, and round-trips through a fresh DB session
- API DB mode now builds SQLAlchemy-backed source, area, evidence, claim, and report services per request; successful requests commit and failures roll back through the API dependency
- `POST /areas`, `POST /report-runs`, and `GET /report-runs/{id}` pass in a DB-backed API integration test and the report row stores a non-null `intent_id`
- Generated fixture report artifact semantics are pinned by a normalized regression test that ignores dynamic UUID/timestamp/path fields
- Shared source/evidence/claim/job/report schema gaps are recorded in `plans/2026-06-04-l7-closeout-l8-entry.md` without editing shared schema files
- Level 8 connector gates are mapped to lane owners, and a fixture-only flood connector acceptance path is recorded before connector runtime code
- D-005 is complete: `LANE_OWNERSHIP.md` assigns the connector integration zone, the connector ownership ADR is accepted, and source retrieval runs are connector lifecycle/provenance authority
- CON-013 is complete: `GET /connector-runs/{ingest_run_id}/review-status` exposes in-memory connector review status that combines connector handoff and fixture quality profile data without durable queue persistence, connector status tables, schema edits, live I/O, claims, reports, or DB-backed connector status
Failed or blocked gates:
- No Level 7 blockers remain for the fixture-backed report/API vertical slice.
- Shared-schema alignment for `schemas/*.json` remains a future coordinated contract pass before schema edits.
Completion evidence:
- plans/lane-d-2026-06-03-reports-api-infra.md
- backend/app/domain/report_contracts.py (ReportRunContract with evidence, claims, unknowns, red flags, verification tasks, and artifact metadata)
- backend/app/reports/service.py (report-run composition service)
- backend/app/reports/models.py
- backend/app/reports/report_repo.py
- backend/app/reports/adapters.py (SourceServiceProtocolAdapter and AreaServiceProtocolAdapter)
- docs/adr/lane-d-0001-report-persistence.md
- backend/app/api/dependencies.py (per-app API service wiring)
- backend/app/api/sources.py (source router)
- backend/app/api/areas.py (area router)
- backend/app/api/evidence.py (evidence router)
- backend/app/api/reports.py (report-run router)
- backend/app/api/connectors.py (connector review-status router)
- backend/app/main.py (router registration)
- backend/app/db/session.py (FastAPI-compatible DB session dependency; delegates to shared `get_session()`)
- backend/tests/reports/test_report_contracts.py (contract defaults)
- backend/tests/reports/test_report_service.py (4 report service tests)
- backend/tests/reports/test_adapters.py (4 adapter tests)
- backend/tests/reports/test_report_repository.py (DB-backed persistence round-trip)
- backend/tests/api/test_api_scaffold.py (7 passing API contract tests, including source-failure unknown surfacing through report-run API)
- backend/tests/api/test_report_runs_db.py (DB-backed API create/retrieve/persistence integration test)
- backend/tests/api/test_connector_review_status.py (connector review-status API tests)
- backend/tests/api/test_db_session.py (DB session dependency delegation test)
- backend/tests/reports/test_report_regression.py (normalized fixture report artifact semantic regression)
Next lowest-dependency task:
- **D-001 (DONE)**: DB-backed API service wiring is complete behind explicit `create_app(use_db_services=True)`. Default API dependencies remain in-memory for cheap fixture tests, while DB mode wires SQLAlchemy repositories and report artifact persistence through request-scoped services.
- **D-000 (DONE)**: Report surfacing for unsupported categories is complete. C-002 is merged on `main`; report runs now create or inject stored unsupported-category SOURCE_FAILURE evidence and surface soil/septic, environmental hazards, market context, and resource context in `ReportRunContract.unknowns`.
- **D-002 (DONE)**: Normalized report artifact regression is complete.
- **D-003 (DONE)**: Schema-contract alignment note is complete; future schema ownership and edit order are recorded before any shared `schemas/*.json` edits.
- **D-004 (DONE)**: Level 8 ownership and fixture-only connector acceptance plan is complete.
- **D-005 (DONE)**: Connector integration-zone ownership and source-retrieval-run lifecycle decision are canonical in `LANE_OWNERSHIP.md` and `docs/adr/lane-d-0002-connector-entry-ownership.md`.
- **CON-013 (DONE)**: Connector review-status API surface is complete for in-memory status records that consume connector handoff and fixture quality profile data.
- **NEXT**: Select a coordinated Level 8 follow-up: durable `ingest_run_id` evidence linkage, exact source-failure evidence ID preservation, durable human-review queue persistence after ownership/schema planning, or another selected fixture category.
Do not work on yet:
- Live connectors (Level 8 - out of scope for this lane plan)
- UI and production workflow expansion before D-001 passes
- Any Lane A/B/C module files (read only)
```

## Known blockers

| Item | Status | Impact |
|---|---|---|
| Shared-schema alignment for `schemas/*.json` | Gap note complete; edits pending | Future payload changes need owner-specific schema edits after review scope is set |
| Lane A SourceExistsProtocol | Available for in-memory wiring | TD-030/TD-050 can adapt SourceService production-use checks |
| Lane B TB-010 AreaService | Available for in-memory wiring | TD-030 can use AreaService after Lane C ClaimService exists |
| Lane C TC-030 ClaimService | Available | TD-030 integration can use ClaimService and RuleEngine in-memory slices |
| Lane C C-002 not-evaluated severity metadata | Resolved in merged C-002 handoff | D-000 is complete; D-001 can now use report output that includes all four unsupported-category unknowns |
| docker-compose.yml changes | Lane A owns | Request via Lane A blocker process |
| Future `backend/app/connectors/` ownership | Resolved in `LANE_OWNERSHIP.md` | Connector runtime work belongs to the connector integration zone; Lane D may expose explicit API surfaces that consume connector-owned status records |

## Active plan

`plans/lane-d-2026-06-03-reports-api-infra.md`

## Lane-specific verification commands

```bash
# Lane D unit tests only:
cd backend && PYTHONPATH=. pytest tests/reports/ tests/api/ -v

# Lane D type check:
cd backend && mypy app/reports app/api

# Full workspace gate:
.\scripts\verify.ps1

# Full integration (when Docker available):
docker compose up -d db
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```
