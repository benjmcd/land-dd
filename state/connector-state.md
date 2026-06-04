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
- CON-006: DONE - concrete public-service workflow wiring handoff.
- CON-007: DONE - Lane A public provenance identity-preservation follow-up.
- CON-008: DONE - DB-backed fixture workflow smoke.
- CON-009: DONE - DB-backed source-failure fixture workflow smoke.
- CON-010: DONE - connector run/status review packet and human-review handoff projection.
- CON-011: DONE - connector review handoff consumer for review packets.
- CON-012: DONE - connector fixture quality profile for flood fixture output.
- CON-013: DONE - connector review status composition and API status surface.
- CON-014: DONE - durable connector review queue persistence.
- CON-015: DONE - connector review queue API retrieval.
- CON-016: DONE - connector review queue worker lease and finish semantics.
- CON-017: DONE - connector queue worker-state read model.
- CON-018: DONE - connector queue retry/requeue and cancel semantics.
- CON-019: DONE - connector adapter adoption of supplied source-failure evidence IDs.
- CON-020: DONE - connector fixture identity and timing quality checks.
- CON-021: DONE - connector human-review action semantics.
- CON-022: DONE - connector human-review API route/reviewer/auth semantics.
- CON-023: DONE - connector fixture evidence provenance quality checks.
- CON-024: DONE - connector review action API auth blocker decision.
- CON-025: DONE - connector reviewer principal boundary.
- CON-026: DONE - connector review action route subset decision.
- CON-027: DONE - connector fixture retrieval metric quality checks.
- CON-028: DONE - connector source-failure payload type quality checks.
- CON-029: DONE - connector source-failure reason consistency checks.
- CON-030: DONE - connector retrieval failure-reason metric quality checks.
- CON-031: DONE - connector succeeded-retrieval failure-metric quality checks.
Do not work on yet:
- Live connector behavior
- Long-running worker/scheduler/background loops
- Connector review mutation API routes beyond the subset supported by the tested reviewer principal and existing queue transitions
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
- `backend/app/connectors/public_wiring.py`
- `backend/tests/connectors/test_public_wiring.py`
- `backend/app/connectors/review_packet.py`
- `backend/tests/connectors/test_review_packet.py`
- `backend/app/connectors/review_handoff.py`
- `backend/tests/connectors/test_review_handoff.py`
- `backend/app/connectors/fixture_quality.py`
- `backend/tests/connectors/test_fixture_quality.py`
- `backend/app/connectors/review_status.py`
- `backend/tests/connectors/test_review_status.py`
- `backend/app/connectors/review_queue.py`
- `backend/tests/connectors/test_review_queue.py`
- `backend/app/api/connectors.py`
- `backend/tests/api/test_connector_review_status.py`
- `backend/tests/api/test_connector_review_queue_db.py`
- `docs/adr/lane-d-0003-connector-review-queue.md`
- `docs/adr/lane-d-0004-connector-queue-retrieval.md`
- `docs/adr/lane-d-0005-connector-queue-worker.md`
- `docs/adr/lane-d-0006-connector-queue-worker-read-model.md`
- `docs/adr/lane-d-0007-connector-queue-retry-cancel.md`
- `docs/adr/lane-d-0008-connector-source-failure-ids.md`
- `docs/adr/lane-d-0011-connector-human-review-actions.md`
- `docs/adr/lane-d-0012-connector-human-review-api-semantics.md`
- `docs/adr/lane-d-0014-connector-review-api-auth-blocker.md`
- `docs/adr/lane-d-0015-connector-reviewer-principal.md`
- `docs/adr/lane-d-0016-connector-review-action-route-subset.md`
- `backend/app/api/reviewer_auth.py`
- `backend/tests/api/test_reviewer_auth.py`
- `backend/app/source_registry/provenance_service.py`
- `backend/tests/source_registry/test_source_provenance.py`

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

2026-06-04 CON-006 result: targeted connector tests pass (23 tests); connector ruff clean; connector mypy clean; full PowerShell verification passes with 286 collected backend tests, lint clean, mypy clean (104 source files), and DB smoke skipped by default; whitespace check clean.

2026-06-04 CON-007 result: targeted DB-enabled source-provenance/connector tests pass (29 tests); targeted ruff clean; targeted mypy clean; full DB-enabled PowerShell verification passes with 289 collected backend tests, lint clean, mypy clean (104 source files), migrations/seeds apply, and DB smoke passes; whitespace check clean.

2026-06-04 CON-008 result: targeted connector public-wiring tests pass with DB smoke skipped by default (5 passed, 1 skipped); targeted DB-enabled connector public-wiring tests pass (6 tests); targeted ruff clean; targeted mypy clean; full DB-enabled PowerShell verification passes with 290 collected backend tests, lint clean, mypy clean (104 source files), migrations/seeds apply, and DB smoke passes; whitespace check clean.

2026-06-04 CON-009 result: targeted connector public-wiring tests pass with DB smoke skipped by default (5 passed, 2 skipped); targeted DB-enabled connector public-wiring tests pass (7 tests); targeted ruff clean; targeted mypy clean; full DB-enabled PowerShell verification passes with 291 collected backend tests, lint clean, mypy clean (104 source files), migrations/seeds apply, and DB smoke passes; whitespace check clean.

2026-06-04 CON-010 result: focused review-packet/fixture-workflow tests pass (8 tests); full connector tests pass with DB smoke skipped by default (28 passed, 2 skipped); connector ruff clean; connector mypy clean over 13 source/test files. Full workspace verification result is recorded in `state/VALIDATION_LOG.md`.

2026-06-04 CON-011 result: focused review-handoff/review-packet tests pass (8 tests); full connector tests pass with DB smoke skipped by default (32 passed, 2 skipped); connector ruff clean; connector mypy clean over 15 source/test files; full DB-enabled PowerShell verification passes with 300 backend tests, lint clean, mypy clean over 109 source files, migrations/seeds apply, and DB smoke passes.

2026-06-04 CON-012 result: focused fixture-quality tests pass (7 tests); full connector tests pass with DB smoke skipped by default (39 passed, 2 skipped); connector ruff clean; connector mypy clean over 17 source/test files; full DB-enabled PowerShell verification passes with 307 backend tests, lint clean, mypy clean over 111 source files, migrations/seeds apply, and DB smoke passes.

2026-06-04 CON-013 result: focused review-status/API tests pass (8 tests); connector/API tests pass with DB smoke skipped by default (55 passed, 3 skipped); connector/API ruff clean; connector/API mypy clean over 33 source/test files; full DB-enabled PowerShell verification passes with 315 backend tests, lint clean, mypy clean over 115 source files, migrations/seeds apply, and DB smoke passes.

2026-06-04 CON-014 result: focused queue tests pass with DB smoke skipped by default (2 passed, 1 skipped); DB-enabled queue tests pass (3 tests); connector tests pass with DB smoke skipped by default (45 passed, 3 skipped); connector ruff clean; connector mypy clean over 21 source/test files; full DB-enabled PowerShell verification passes with 318 backend tests, lint clean, mypy clean over 117 source files, migrations/seeds apply, and DB smoke passes.

2026-06-04 CON-015 result: focused queue-retrieval API tests pass with DB smoke skipped by default (6 passed, 1 skipped); DB-enabled queue-retrieval API test passes (1 test); connector/API tests pass with DB smoke skipped by default (59 passed, 5 skipped); connector/API ruff clean; connector/API mypy clean over 36 source/test files; full DB-enabled PowerShell verification passes with 321 backend tests, lint clean, mypy clean over 118 source files, migrations/seeds apply, and DB smoke passes.

2026-06-04 CON-016 result: focused queue tests pass with DB smoke skipped by default (4 passed, 2 skipped); DB-enabled queue tests pass (6 tests); connector tests pass with DB smoke skipped by default (47 passed, 4 skipped); connector ruff clean; connector mypy clean over 21 source/test files; full DB-enabled PowerShell verification passes with 324 backend tests, lint clean, mypy clean over 118 source files, migrations/seeds apply, and DB smoke passes.

2026-06-04 CON-017 result: focused queue API tests pass with DB smoke skipped by default (7 passed, 2 skipped); DB-enabled queue API tests pass (2 tests); connector/API tests pass with DB smoke skipped by default (62 passed, 7 skipped); connector/API ruff clean; connector/API mypy clean over 36 source files; full DB-enabled PowerShell verification passes with 326 backend tests, lint clean, mypy clean over 118 source files, migrations/seeds apply, and DB smoke passes.

2026-06-04 CON-018 result: focused queue tests pass with DB smoke skipped by default (6 passed, 3 skipped); DB-enabled queue tests pass (9 tests); connector/API tests pass with DB smoke skipped by default (64 passed, 8 skipped); connector/API ruff clean; connector/API mypy clean over 36 source files; full DB-enabled PowerShell verification passes with 329 backend tests, lint clean, mypy clean over 118 source files, migrations/seeds apply, and DB smoke passes.

2026-06-04 CON-019 result: focused connector adoption tests pass with DB smoke skipped by default (15 passed, 2 skipped); DB-backed public wiring source-failure ID test passes (1 test); targeted ruff clean; targeted mypy clean over 10 source/test files; connector/API tests pass with DB smoke skipped by default (64 passed, 8 skipped); connector/API ruff clean; connector/API mypy clean over 36 source/test files; full DB-enabled PowerShell verification passes after merging root `ca10f85` with 335 backend tests, lint clean, mypy clean over 119 source files, migrations/seeds apply, and DB smoke passes.

2026-06-04 CON-020 result: focused fixture-quality tests pass (9 tests); connector tests pass with DB smoke skipped by default (51 passed, 5 skipped); targeted and connector ruff clean; targeted mypy clean over 2 source/test files; connector mypy clean over 21 source/test files; full DB-enabled PowerShell verification passes with 337 backend tests, lint clean, mypy clean over 119 source files, migrations/seeds apply, and DB smoke passes.

2026-06-04 CON-024 result: whitespace check clean; default Windows PowerShell verification passes with 351 backend tests, lint clean, mypy clean over 121 source files, and DB smoke skipped by default; full DB-enabled PowerShell verification passes with 351 backend tests, lint clean, mypy clean over 121 source files, migrations/seeds apply, and DB smoke passes.

2026-06-04 CON-025 result: focused reviewer auth tests pass (11 tests); focused ruff clean; focused mypy clean over 2 source files; backend collection reports 362 tests; whitespace check clean; default and DB-enabled Windows PowerShell verification passes with 362 backend tests, lint clean, mypy clean over 123 source files, migrations/seeds apply, and DB smoke passes.

2026-06-04 CON-026 result: whitespace check clean; default Windows PowerShell verification passes with 362 backend tests, lint clean, mypy clean over 123 source files, and DB smoke skipped by default; full DB-enabled Windows PowerShell verification passes with 362 backend tests, lint clean, mypy clean over 123 source files, migrations/seeds apply, and DB smoke passes. Decision-only route subset; no route/OpenAPI/runtime mutation.

2026-06-04 CON-027 result: focused fixture-quality tests pass (11 tests); focused ruff clean; focused mypy clean over 2 source files. Full final Windows PowerShell verification is recorded in `state/VALIDATION_LOG.md`. Scope is connector-local fixture retrieval metric validation; no route/OpenAPI/runtime/schema/queue mutation.

2026-06-04 CON-028 result: focused fixture-quality tests pass (12 tests); focused ruff clean; focused mypy clean over 2 source files. Full final Windows PowerShell verification is recorded in `state/VALIDATION_LOG.md`. Scope is connector-local source-failure payload type validation; no route/OpenAPI/runtime/schema/queue mutation.

2026-06-04 CON-029 result: focused fixture-quality tests pass (13 tests); focused ruff clean; focused mypy clean over 2 source files. Full final Windows PowerShell verification is recorded in `state/VALIDATION_LOG.md`. Scope is connector-local source-failure reason consistency validation; no route/OpenAPI/runtime/schema/queue mutation.

2026-06-04 CON-030 result: focused fixture-quality tests pass (13 tests); focused ruff clean; focused mypy clean over 2 source files. Full final Windows PowerShell verification is recorded in `state/VALIDATION_LOG.md`. Scope is connector-local retrieval failure-reason metric validation; no route/OpenAPI/runtime/schema/queue mutation.

2026-06-04 CON-031 result: focused fixture-quality tests pass (13 tests); focused ruff clean; focused mypy clean over 2 source files. Full final Windows PowerShell verification is recorded in `state/VALIDATION_LOG.md`. Scope is connector-local succeeded-retrieval failure-metric validation; no route/OpenAPI/runtime/schema/queue mutation.

## Known blockers

| Item | Status | Impact |
|---|---|---|
| Live connector gates | Not satisfied | CON-001 must remain fixture-only |
| Durable retrieval-run/evidence linkage | Gap recorded | Current `EvidenceContract` lacks `ingest_run_id`; coordinate Lane C/schema before claiming durable linkage |
| Exact source-failure field preservation | Satisfied for connector adapter/public service scope | Lane C TC-180 plus CON-019 preserve connector-supplied source-failure evidence IDs through public service wiring; durable `ingest_run_id` evidence-row linkage remains separate |
| Lane A concrete retrieval-run wiring | Satisfied for public service | `SourceProvenanceService.record_retrieval_run_contract(...)` preserves supplied `SourceRetrievalRunContract.ingest_run_id`; connector wiring uses it through a public-service adapter |
| DB-backed workflow wiring | Satisfied for fixture success and source-failure smoke | Fixture workflow now records retrieval provenance and persists normal/source-failure evidence through DB-backed public Lane A and Lane C services; broader production ingestion remains unclaimed |
| Connector run/status review handoff | Satisfied for fixture workflow projection | `build_connector_run_review_packet(...)` summarizes workflow status and review signals without adding API, claims, reports, schema edits, or persistence changes |
| Connector review handoff consumer | Satisfied for connector-local projection | `build_connector_review_handoff(...)` classifies review packets into deterministic handoff dispositions without adding API, persistence, reports, claims, schema edits, or live I/O |
| Connector fixture quality profile | Satisfied for flood fixture output | `evaluate_flood_fixture_quality(...)` flags fixture-local provenance, dataset-version, retrieval metric, row-count, spatial evidence, and source-failure payload inconsistencies without adding API, persistence, reports, claims, schema edits, or live I/O |
| Connector review status API | Satisfied for in-memory status surface | `build_connector_run_review_status(...)` composes handoff and quality data, and `GET /connector-runs/{ingest_run_id}/review-status` returns stored status without durable queue persistence, schema edits, reports, claims, or live I/O |
| Durable connector review queue | Satisfied for connector review status items | `SqlAlchemyConnectorReviewQueueRepository` writes idempotent `connector_review_status` jobs to `jobs.job_queue` with payload references to `source.ingest_runs.ingest_run_id`; workers/API DB retrieval remain future work |
| Connector review queue API retrieval | Satisfied for read-only queue item lookup | `GET /connector-runs/{ingest_run_id}/review-queue` reads stored queue items without job mutation, worker execution, claims, reports, schema edits, or live I/O |
| Connector review queue worker lease semantics | Satisfied for repository-level lease/finish methods | `ConnectorReviewQueueRepository` implementations can lease eligible connector review jobs, mark running jobs succeeded, and mark running jobs failed without adding a scheduler, API mutation route, retry/requeue policy, live I/O, claims, reports, schema edits, or provenance mutation |
| Connector queue worker-state read model | Satisfied for read-only API surfacing | `GET /connector-runs/{ingest_run_id}/review-queue` now surfaces attempts, lock/start/finish metadata, and last error without leasing, completing, failing, retrying, requeueing, cancelling, creating, or executing jobs |
| Connector queue retry/requeue/cancel semantics | Satisfied for repository-level orchestration methods | `ConnectorReviewQueueRepository` implementations can requeue failed jobs only when attempts remain and cancel nonfinal jobs with reasons; no API mutation route, automatic retry policy, scheduler, live I/O, claims, reports, schema edits, or provenance mutation was added |
| Connector source-failure evidence ID adoption | Satisfied for connector adapter/public wiring scope | `ConnectorEvidenceIngestionAdapter` passes deterministic source-failure `EvidenceContract.evidence_id` values into Lane C's public source-failure creation method and DB-backed public wiring proves the ID persists; durable `ingest_run_id` evidence-row linkage remains a future coordinated schema/service pass |
| Connector fixture identity/timing quality | Satisfied for fixture-local review scope | `evaluate_flood_fixture_quality(...)` now flags duplicate evidence IDs and evidence observations outside the retrieval-run time window without adding API, persistence, schema edits, live I/O, claims, or reports |
| Connector source-failure payload quality | Satisfied for fixture-local review scope | `evaluate_flood_fixture_quality(...)` now requires source-failure payload keys and type/non-empty value checks without adding API, persistence, schema edits, live I/O, claims, or reports |
| Connector source-failure reason consistency | Satisfied for fixture-local review scope | `evaluate_flood_fixture_quality(...)` now requires source-failure payload reasons to match retrieval failure metrics when present, without adding API, persistence, schema edits, live I/O, claims, or reports |
| Connector retrieval failure-reason metric quality | Satisfied for fixture-local review scope | `evaluate_flood_fixture_quality(...)` now requires blocked/failed retrievals to carry a non-empty `metrics.failure_reason` value without adding API, persistence, schema edits, live I/O, claims, or reports |
| Connector succeeded-retrieval failure-metric quality | Satisfied for fixture-local review scope | `evaluate_flood_fixture_quality(...)` now rejects succeeded retrievals that carry non-empty `metrics.failure_reason` values without adding API, persistence, schema edits, live I/O, claims, or reports |
| Connector review action API auth boundary | Satisfied for local service-account substrate | ADR Lane D 0015 adds the tested reviewer principal dependency required by ADR Lane D 0014; production auth, route wiring, reviewer ownership persistence, and action history remain separate |
| Connector reviewer principal dependency | Satisfied for local service-account fixture/developer substrate | `LocalServiceAccountReviewerAuth` validates configured reviewer IDs and tokens, fails closed when unconfigured, and returns `ReviewerPrincipal`; production auth, route wiring, reviewer ownership persistence, and action history remain separate |
| Connector review action route subset | Satisfied for implementation planning | ADR Lane D 0016 accepts only `request_fixture_fix`, `requeue_after_fix`, and `cancel_review` for the next route implementation; route/OpenAPI changes remain future coordinated work |
