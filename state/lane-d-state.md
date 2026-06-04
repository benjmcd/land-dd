# Lane D State — Reports + API + Platform Infrastructure

```text
Current milestone: Level 7 - Reproducible Report Vertical Slice (partial report-run harness)
Target milestone: Level 7 (Reproducible Report Vertical Slice)
Milestone status: PARTIAL
Last verified: 2026-06-04
Verification command(s):
- cd backend; $env:PYTHONPATH='.'; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/reports tests/api
- .\scripts\verify.ps1
- cd backend; $env:PYTHONPATH='.'; py -3.12 -m pytest --collect-only -q
- docker info --format '{{.ServerVersion}}'
Verification result:
- 18 Lane D report/API tests pass
- Full verification passes locally with DB smoke enabled after C-002 merge: 250 tests; lint clean; mypy clean (89 source files)
- ReportRunService composes source, area, evidence, claim, and rule services behind the report-run API scaffold
- SqlAlchemyReportRunRepository persists report runs to `reports.report_runs`, writes a machine-readable artifact under `OBJECT_STORE_ROOT`, and round-trips through a fresh DB session
Failed or blocked gates:
- L7 is partial until Lane B area persistence, Lane C durable evidence/claim/rule-execution persistence, and DB-backed API workflow are wired underneath report runs
- Default API dependencies remain in-memory; DB report persistence is exercised through repository injection and DB-backed tests
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
- backend/app/main.py (router registration)
- backend/app/db/session.py (FastAPI-compatible DB session dependency; delegates to shared `get_session()`)
- backend/tests/reports/test_report_contracts.py (contract defaults)
- backend/tests/reports/test_report_service.py (4 report service tests)
- backend/tests/reports/test_adapters.py (4 adapter tests)
- backend/tests/reports/test_report_repository.py (DB-backed persistence round-trip)
- backend/tests/api/test_api_scaffold.py (7 passing API contract tests, including source-failure unknown surfacing through report-run API)
- backend/tests/api/test_db_session.py (DB session dependency delegation test)
Next lowest-dependency task:
- **D-000 (NEXT)**: Report surfacing for unsupported categories. C-002 is now merged on `main` with unsupported-category SOURCE_FAILURE evidence producing UNKNOWN claims and the four C-002 ruleset entries using `severity_on_fail: unknown`; Lane D now owns the report/API follow-up that creates or injects those source failures and surfaces soil/septic, environmental hazards, market context, and resource context in `ReportRunContract.unknowns`.
- **D-001 (PARTIAL PRE-WORK DONE; FULL TASK BLOCKED on D-000)**: `backend/app/db/session.py` now delegates `get_db_session()` to `get_session()` from `app.db.engine`; do not update `api/dependencies.py`, update `main.py`, or add/run the DB-backed report API integration test until D-000 is complete.
Do not work on yet:
- Live connectors (Level 8 - out of scope for this lane plan)
- Any Lane A/B/C module files (read only)
- D-001 DB service wiring beyond `backend/app/db/session.py` until D-000 is complete
```

## Known blockers

| Item | Status | Impact |
|---|---|---|
| Shared-schema alignment for `schemas/*.json` | Pending | Future payload changes need a coordinated contract pass |
| Lane A SourceExistsProtocol | Available for in-memory wiring | TD-030/TD-050 can adapt SourceService production-use checks |
| Lane B TB-010 AreaService | Available for in-memory wiring | TD-030 can use AreaService after Lane C ClaimService exists |
| Lane C TC-030 ClaimService | Available | TD-030 integration can use ClaimService and RuleEngine in-memory slices |
| Lane C C-002 not-evaluated severity metadata | Resolved in merged C-002 handoff | D-000 can now start from UNKNOWN claim behavior and `severity_on_fail: unknown` ruleset metadata for all four unsupported categories |
| docker-compose.yml changes | Lane A owns | Request via Lane A blocker process |

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
