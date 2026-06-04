# Connector Integration Zone State

```text
Current milestone: Level 8 - Fixture Connectors and Data Quality
Milestone status: IN PROGRESS
Last verified: 2026-06-04
Current task:
- CON-001: DONE - Level 8 fixture-only flood connector contract slice.
- CON-002: DONE - connector evidence-ingestion handoff plan.
- CON-003: DONE - connector-zone evidence ingestion adapter.
- CON-004: DONE - connector retrieval-run provenance adapter.
- CON-005: DONE - fixture-only connector ingest workflow composition.
- CON-006: NEXT - concrete public-service workflow wiring handoff.
Do not work on yet:
- Live connector behavior
- Credentials, browser/download steps, paid APIs, or network-backed ingestion
- Shared schema edits
- Lane A/B/C/D implementation changes unless explicitly coordinated with the owning lane
```

## Completion evidence

- `LANE_OWNERSHIP.md` connector integration zone
- `docs/adr/lane-d-0002-connector-entry-ownership.md`
- `plans/connector-2026-06-04-fixture-flood.md`
- `backend/app/connectors/flood_fixture.py`
- `backend/tests/connectors/test_flood_fixture_connector.py`
- `tests/fixtures/connectors/flood_success.json`
- `tests/fixtures/connectors/flood_failure.json`
- `plans/connector-2026-06-04-fixture-flood.md` CON-002 evidence-ingestion handoff section
- `backend/app/connectors/evidence_ingestion.py`
- `backend/tests/connectors/test_evidence_ingestion_adapter.py`
- `backend/app/connectors/retrieval_provenance.py`
- `backend/tests/connectors/test_retrieval_provenance_adapter.py`
- `backend/app/connectors/fixture_workflow.py`
- `backend/tests/connectors/test_fixture_workflow.py`

## Verification

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/connectors
ruff check app/connectors tests/connectors
mypy app/connectors tests/connectors
py -3.12 -m pytest --collect-only -q
Set-Location ..
.\scripts\verify.ps1
git diff --check
```

Result: targeted connector tests pass (5 tests); connector ruff clean; connector mypy clean; full PowerShell verification passes with 260 collected backend tests, lint clean, mypy clean (94 source files), and DB smoke skipped by default; whitespace check clean.

2026-06-04 CON-003 result: targeted connector tests pass (11 tests); connector ruff clean; connector mypy clean; full PowerShell verification passes with 274 collected backend tests, lint clean, mypy clean (98 source files), and DB smoke skipped by default; whitespace check clean.

2026-06-04 CON-004 result: targeted connector tests pass (15 tests); connector ruff clean; connector mypy clean; full PowerShell verification passes with 278 collected backend tests, lint clean, mypy clean (100 source files), and DB smoke skipped by default; whitespace check clean.

2026-06-04 CON-005 result: targeted connector tests pass (19 tests); connector ruff clean; connector mypy clean; full PowerShell verification passes with 282 collected backend tests, lint clean, mypy clean (102 source files), and DB smoke skipped by default; whitespace check clean.

## Known blockers

| Item | Status | Impact |
|---|---|---|
| Live connector gates | Not satisfied | CON-001 must remain fixture-only |
| Durable retrieval-run/evidence linkage | Gap recorded | Current `EvidenceContract` lacks `ingest_run_id`; coordinate Lane C/schema before claiming durable linkage |
| Exact source-failure field preservation | Gap recorded | Current public Lane C source-failure API creates the persisted evidence record; connector-provided source-failure IDs are templates unless Lane C adds a public method |
| Lane A concrete retrieval-run wiring | Gap recorded | Connector provenance adapter defines the injected port; concrete production wiring needs a Lane A public method or Lane A-owned adapter that preserves supplied `SourceRetrievalRunContract.ingest_run_id` |
| DB-backed workflow wiring | Not implemented in CON-005 | Fixture workflow composes injected ports only; durable DB-backed production ingestion needs concrete public-service wiring and DB-smoke verification |
