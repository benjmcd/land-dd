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
- cd backend; py -3.12 -m pytest -q tests/reports/test_report_schema_contract.py tests/reports/test_report_contracts.py
- cd backend; ruff check app/api app/main.py app/reports tests/api tests/reports
- cd backend; ruff check tests/reports/test_report_schema_contract.py
- cd backend; mypy tests/reports/test_report_schema_contract.py
- cd backend; mypy app/api app/main.py app/reports tests/api/test_report_runs_db.py
- .\scripts\verify.ps1
- cd backend; py -3.12 -m pytest -q tests/connectors/test_review_status.py tests/api/test_connector_review_status.py
- cd backend; py -3.12 -m pytest -q tests/connectors/test_review_queue.py
- cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/connectors/test_review_queue.py
- cd backend; py -3.12 -m pytest -q tests/api/test_connector_review_status.py tests/api/test_connector_review_queue_db.py
- cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/api/test_connector_review_queue_db.py
- cd backend; py -3.12 -m pytest -q tests/connectors tests/api -rA
- cd backend; ruff check app/connectors app/api app/main.py tests/connectors tests/api
- cd backend; mypy app/connectors app/api app/main.py tests/connectors tests/api
- cd backend; $env:PYTHONPATH='.'; py -3.12 -m pytest --collect-only -q
- docker info --format '{{.ServerVersion}}'
- cd backend; py -3.12 -m pytest -q tests/reports/test_report_schema_contract.py tests/reports/test_report_contracts.py
- cd backend; py -3.12 -m pytest -q tests/reports/test_report_schema_contract.py tests/reports/test_report_service.py tests/reports/test_report_regression.py
- cd backend; py -3.12 -m pytest -q tests/reports tests/api
- cd backend; ruff check tests/reports/test_report_schema_contract.py
- cd backend; ruff check app/reports tests/reports/test_report_schema_contract.py tests/reports/test_report_service.py tests/reports/test_report_regression.py
- cd backend; ruff check app/reports app/api app/main.py tests/reports tests/api
- cd backend; mypy tests/reports/test_report_schema_contract.py
- cd backend; mypy app/reports tests/reports/test_report_schema_contract.py tests/reports/test_report_service.py tests/reports/test_report_regression.py
- cd backend; mypy app/reports app/api app/main.py tests/reports tests/api
- git diff --check
- cd backend; py -3.12 -m pytest --collect-only
Verification result:
- Full verification passes locally with DB smoke enabled after TD-083 report validation metadata: 362 tests; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes
- Full verification passes locally with DB smoke enabled after CON-027 connector fixture retrieval metric quality: 363 tests; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes
- Full verification passes locally with DB smoke enabled after TD-084 job-schema boundary: 363 tests; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes
- Full verification passes locally with DB smoke enabled after CON-028 connector source-failure payload type quality: 364 tests; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes
- Full verification passes locally with DB smoke enabled after CON-029 connector source-failure reason consistency: 365 tests; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes
- Full verification passes locally with DB smoke enabled after CON-030 connector retrieval failure-reason metric quality: 365 tests; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes
- Full verification passes locally with DB smoke enabled after CON-031 connector succeeded-retrieval failure-metric quality: 365 tests; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes
- Full verification passes locally with DB smoke enabled after CON-032 connector fixture evidence domain quality: 366 tests; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes
- Full verification passes locally with DB smoke enabled after CON-033 connector fixture retrieval name quality: 367 tests; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes
- Full verification passes locally with DB smoke enabled after CON-034 connector fixture evidence source consistency: 368 tests; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes
- Full verification passes locally with DB smoke enabled after CON-035 connector fixture evidence area consistency: 369 tests; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes
- Full verification passes locally with DB smoke enabled after TD-082 report metadata extension boundary planning: 351 tests; lint clean; mypy clean (121 source files); migrations/seeds apply; DB smoke passes
- Full verification passes locally with DB smoke enabled after CON-024 connector review action API auth blocker decision: 351 tests; lint clean; mypy clean (121 source files); migrations/seeds apply; DB smoke passes
- Full verification passes locally with DB smoke enabled after CON-025 connector reviewer principal boundary: 362 tests; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes
- Full verification passes locally with DB smoke enabled after TD-081 report manifest metadata schema tightening: 343 tests; lint clean; mypy clean (120 source files); migrations/seeds apply; DB smoke passes
- Full verification passes locally with DB smoke enabled after rebasing TD-090 planning-pack OpenAPI refresh onto TD-081 report manifest metadata schema tightening: 344 tests; lint clean; mypy clean (120 source files); migrations/seeds apply; DB smoke passes
- Full verification passes locally with DB smoke enabled after CON-020: 337 tests; lint clean; mypy clean (119 source files); migrations/seeds apply; DB smoke passes
- Full verification passes locally with DB smoke enabled after CON-019 and root `ca10f85` reconciliation: 335 tests; lint clean; mypy clean (119 source files); migrations/seeds apply; DB smoke passes
- Full verification passes locally with DB smoke enabled after TD-080 report schema contract: 339 tests; lint clean; mypy clean (120 source files); migrations/seeds apply; DB smoke passes
- Full verification passes locally with DB smoke enabled after merging CON-020 and TD-080: 341 tests; lint clean; mypy clean (120 source files); migrations/seeds apply; DB smoke passes
- Full verification passes locally with DB smoke enabled after TD-090 planning-pack OpenAPI refresh: 342 tests; lint clean; mypy clean (120 source files); migrations/seeds apply; DB smoke passes
- Connector/API review-status tests pass with 55 connector/API tests passing and 3 DB-gated skips when DB smoke is disabled
- ReportRunService composes source, area, evidence, claim, and rule services behind the report-run API scaffold
- ReportRunService now creates stored unsupported-category SOURCE_FAILURE evidence for missing not-evaluated domains before rule evaluation, and report/API output surfaces those claims in `unknowns`
- SqlAlchemyReportRunRepository persists report runs to `reports.report_runs`, writes a machine-readable artifact under `OBJECT_STORE_ROOT`, and round-trips through a fresh DB session
- API DB mode now builds SQLAlchemy-backed source, area, evidence, claim, and report services per request; successful requests commit and failures roll back through the API dependency
- `POST /areas`, `POST /report-runs`, and `GET /report-runs/{id}` pass in a DB-backed API integration test and the report row stores a non-null `intent_id`
- Generated fixture report artifact semantics are pinned by a normalized regression test that ignores dynamic UUID/timestamp/path fields
- `schemas/report_run_schema.json` is aligned to serialized `ReportRunContract`, references Lane C evidence/claim schemas for nested arrays, and is guarded by schema-contract parity tests
- Stable generated report `source_manifest`, `source_details`, `artifact_metadata`, and `cost_metrics` schema keys are constrained with schema-contract tests and ADR `docs/adr/lane-d-0010-report-manifest-metadata.md`
- Planning-pack OpenAPI now matches the generated FastAPI contract.
- Job schema, durable evidence-row retrieval lineage, and API mutation/workflow implementation gaps remain recorded in `plans/2026-06-04-l7-closeout-l8-entry.md`.
- Level 8 connector gates are mapped to lane owners, and a fixture-only flood connector acceptance path is recorded before connector runtime code
- D-005 is complete: `LANE_OWNERSHIP.md` assigns the connector integration zone, the connector ownership ADR is accepted, and source retrieval runs are connector lifecycle/provenance authority
- CON-013 is complete: `GET /connector-runs/{ingest_run_id}/review-status` exposes in-memory connector review status that combines connector handoff and fixture quality profile data without durable queue persistence, connector status tables, schema edits, live I/O, claims, reports, or DB-backed connector status
- CON-014 is complete: connector review status can now be persisted as idempotent `connector_review_status` jobs in `jobs.job_queue`, referencing `source.ingest_runs.ingest_run_id` without replacing source retrieval provenance or adding worker/API queue retrieval behavior
- CON-015 is complete: `GET /connector-runs/{ingest_run_id}/review-queue` retrieves queued connector review items from in-memory or DB-backed API services without mutating, locking, retrying, cancelling, completing, or leasing jobs
- CON-016 is complete: connector review queue repositories can lease eligible connector review jobs, mark running jobs succeeded, and mark running jobs failed without adding a scheduler, API mutation route, retry/requeue policy, live I/O, claims, reports, schema edits, or provenance mutation
- CON-017 is complete: `GET /connector-runs/{ingest_run_id}/review-queue` now surfaces queue worker-state metadata without adding API-side job mutation, worker execution, retry/requeue policy, live I/O, claims, reports, schema edits, or provenance mutation
- CON-018 is complete: connector review queue repositories can requeue failed jobs only when attempts remain and cancel nonfinal jobs with reasons, without adding API-side mutation, automatic retry policy, scheduler, live I/O, claims, reports, schema edits, or provenance mutation
- CON-019 is complete in the Session 2 integration branch: connector evidence ingestion passes supplied deterministic source-failure evidence IDs through Lane C's public service boundary and DB-backed public wiring proves persistence without Lane C implementation/schema edits, live I/O, queue API mutation, claim/report changes, or durable `ingest_run_id` evidence-row linkage
- CON-020 is complete: connector fixture quality flags duplicate evidence IDs and evidence observed outside the retrieval-run time window without API mutation routes, persistence, live I/O, shared schema edits, claims, reports, or durable `ingest_run_id` evidence-row linkage
- TD-081 is complete: stable generated report `source_manifest`, `source_details`, `artifact_metadata`, and `cost_metrics` schema keys are constrained with schema-contract tests and ADR `docs/adr/lane-d-0010-report-manifest-metadata.md`, without runtime validation, API behavior changes, DB migrations, connector behavior, live I/O, hook config, or POSIX scripts
- TD-090 is complete: planning-pack OpenAPI now matches `create_app().openapi()`, and the planning-pack API spec distinguishes implemented routes from future roadmap routes without changing API behavior
- CON-021 is complete as a planning-only human-review action semantics slice. Future action vocabulary is defined before any API mutation route, worker, scheduler, dashboard, connector runtime change, schema, or migration.
- CON-022 is complete as a planning-only human-review API semantics slice. Future route/reviewer/auth/idempotency semantics are accepted before any API mutation route, OpenAPI change, queue code, auth code, schema, or migration.
- CON-023 is complete as a connector-local fixture-quality slice. Fixture evidence now fails closed when provenance text, caveats, or non-failure source dates are missing.
- TD-082 is complete as a planning-only report metadata extension boundary. Future extension families and promotion rules are accepted before any schema/runtime/API changes.
- CON-024 is complete as a connector review action API auth blocker decision. Current API mutation implementation remains blocked because no authenticated reviewer/operator principal dependency exists.
- CON-025 is complete as a local service-account reviewer principal dependency for future connector review mutation routes; no routes are registered and OpenAPI is unchanged.
- CON-026 is complete as a review-action route-subset decision for `request_fixture_fix`, `requeue_after_fix`, and `cancel_review`; route/OpenAPI implementation remains deferred.
- TD-083 is complete as the first report metadata extension implementation. Optional `artifact_metadata.validation` records report contract/profile and ruleset identity with schema/regression coverage, without claiming verification-command execution or changing routes, OpenAPI, DB schema, connector runtime, queue behavior, live I/O, hook config, POSIX scripts, or Lane A/B/C modules.
- CON-027 is complete as connector-local fixture retrieval metric quality. Succeeded retrievals must have matching row counts and zero errors; blocked/failed retrievals must have explicit zero row count and positive error count. No routes, OpenAPI, DB schema, queue behavior, connector runtime, live I/O, hook config, POSIX scripts, durable evidence-row lineage, or lane-owned modules outside connector quality changed.
- TD-084 is complete as a job-schema boundary decision. `schemas/job_schema.json` remains unedited and is not a live connector-run/API contract until a future schema/test slice chooses `jobs.job_queue`, `ConnectorReviewQueueItem`, or a new `JobContract` as authority; source retrieval runs remain connector provenance authority.
- CON-028 is complete as connector-local source-failure payload type quality. Source-failure payload values must have non-empty text failure reasons/error messages and boolean retry flags. No routes, OpenAPI, DB schema, queue behavior, connector runtime, live I/O, hook config, POSIX scripts, durable evidence-row lineage, or lane-owned modules outside connector quality changed.
- CON-029 is complete as connector-local source-failure reason consistency. Source-failure payload `failure_reason` must match retrieval `metrics.failure_reason` when present. No routes, OpenAPI, DB schema, queue behavior, connector runtime, live I/O, hook config, POSIX scripts, durable evidence-row lineage, or lane-owned modules outside connector quality changed.
- CON-030 is complete as connector-local retrieval failure-reason metric quality. Blocked/failed retrievals must carry non-empty `metrics.failure_reason`. No routes, OpenAPI, DB schema, queue behavior, connector runtime, live I/O, hook config, POSIX scripts, durable evidence-row lineage, or lane-owned modules outside connector quality changed.
- CON-031 is complete as connector-local succeeded-retrieval failure-metric quality. Succeeded retrievals must not carry non-empty `metrics.failure_reason`. No routes, OpenAPI, DB schema, queue behavior, connector runtime, live I/O, hook config, POSIX scripts, durable evidence-row lineage, or lane-owned modules outside connector quality changed.
- CON-032 is complete as connector-local fixture evidence domain quality. Flood fixture evidence must use `domain == "flood"`. No routes, OpenAPI, DB schema, queue behavior, connector runtime, live I/O, hook config, POSIX scripts, durable evidence-row lineage, or lane-owned modules outside connector quality changed.
- CON-033 is complete as connector-local fixture retrieval name quality. Flood fixture retrievals must use `connector_name == "fixture_flood_static"`. No routes, OpenAPI, DB schema, queue behavior, connector runtime, live I/O, hook config, POSIX scripts, durable evidence-row lineage, or lane-owned modules outside connector quality changed.
- CON-034 is complete as connector-local fixture evidence source consistency. One flood fixture retrieval must not emit evidence with mixed `source_id` values. No routes, OpenAPI, DB schema, queue behavior, connector runtime, live I/O, hook config, POSIX scripts, durable evidence-row lineage, or lane-owned modules outside connector quality changed.
- CON-035 is complete as connector-local fixture evidence area consistency. One flood fixture retrieval must not emit evidence with mixed `area_id` values. No routes, OpenAPI, DB schema, queue behavior, connector runtime, live I/O, hook config, POSIX scripts, durable evidence-row lineage, or lane-owned modules outside connector quality changed.
Failed or blocked gates:
- No Level 7 blockers remain for the fixture-backed report/API vertical slice.
- Source/evidence/claim/report root schemas are aligned to serialized domain contracts; source provenance-family schemas are aligned to serialized Lane A provenance contracts; stable generated report manifest metadata keys are tightened; planning-pack OpenAPI is aligned to the generated FastAPI contract; connector human-review action and route/reviewer/auth semantics are planned; local reviewer principal dependency is tested; review-action route subset is accepted; report metadata extension boundaries are accepted. Remaining gaps are job schema, durable `ingest_run_id` evidence-row linkage, production auth, reviewer ownership/action history, route/OpenAPI implementation, and broader API mutation/workflow implementation.
Completion evidence:
- plans/lane-d-2026-06-03-reports-api-infra.md
- backend/app/domain/report_contracts.py (ReportRunContract with evidence, claims, unknowns, red flags, verification tasks, and artifact metadata)
- backend/app/reports/service.py (report-run composition service)
- backend/app/reports/models.py
- backend/app/reports/report_repo.py
- backend/app/reports/adapters.py (SourceServiceProtocolAdapter and AreaServiceProtocolAdapter)
- docs/adr/lane-d-0001-report-persistence.md
- docs/adr/lane-d-0005-connector-queue-worker.md
- docs/adr/lane-d-0006-connector-queue-worker-read-model.md
- docs/adr/lane-d-0007-connector-queue-retry-cancel.md
- docs/adr/lane-d-0008-connector-source-failure-ids.md
- docs/adr/lane-d-0009-report-run-schema.md
- docs/adr/lane-d-0010-report-manifest-metadata.md
- docs/adr/lane-d-0013-report-metadata-extension-boundary.md
- docs/adr/lane-d-0011-connector-human-review-actions.md
- docs/adr/lane-d-0012-connector-human-review-api-semantics.md
- docs/adr/lane-d-0015-connector-reviewer-principal.md
- docs/adr/lane-d-0016-connector-review-action-route-subset.md
- docs/adr/lane-d-0017-report-validation-metadata.md
- docs/adr/lane-d-0018-job-schema-boundary.md
- backend/app/api/reviewer_auth.py
- backend/tests/api/test_reviewer_auth.py
- schemas/report_run_schema.json
- backend/app/api/dependencies.py (per-app API service wiring)
- backend/app/api/sources.py (source router)
- backend/app/api/areas.py (area router)
- backend/app/api/evidence.py (evidence router)
- backend/app/api/reports.py (report-run router)
- backend/app/api/connectors.py (connector review-status router)
- backend/app/connectors/review_queue.py (connector review queue adapter)
- backend/app/main.py (router registration)
- backend/app/db/session.py (FastAPI-compatible DB session dependency; delegates to shared `get_session()`)
- backend/tests/reports/test_report_contracts.py (contract defaults)
- backend/tests/reports/test_report_schema_contract.py (report schema-contract parity)
- backend/tests/reports/test_report_service.py (4 report service tests)
- backend/tests/reports/test_adapters.py (4 adapter tests)
- backend/tests/reports/test_report_repository.py (DB-backed persistence round-trip)
- backend/tests/api/test_api_scaffold.py (7 passing API contract tests, including source-failure unknown surfacing through report-run API)
- backend/tests/api/test_report_runs_db.py (DB-backed API create/retrieve/persistence integration test)
- backend/tests/api/test_connector_review_status.py (connector review-status API tests)
- backend/tests/api/test_connector_review_queue_db.py (DB-backed connector review queue API retrieval test)
- backend/tests/connectors/test_review_queue.py (connector review queue tests)
- backend/tests/connectors/test_fixture_quality.py (connector fixture quality tests)
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
- **CON-014 (DONE)**: Durable connector review queue persistence is complete using existing `jobs.job_queue`.
- **CON-015 (DONE)**: Connector review queue API retrieval is complete for read-only in-memory and DB-backed queued item lookup.
- **CON-016 (DONE)**: Connector review queue worker lease semantics are complete at repository level; no API mutation route, scheduler, retry/requeue policy, or live connector execution was added.
- **CON-017 (DONE)**: Connector queue worker-state read model is complete for read-only API surfacing of attempts, lock/start/finish metadata, and last error.
- **CON-018 (DONE)**: Connector queue retry/requeue/cancel semantics are complete at repository level; default connector review jobs remain single-attempt unless a future planned producer/operator permits additional attempts.
- **CON-019 (DONE)**: Connector adapter adoption of supplied source-failure evidence IDs is complete in the Session 2 integration branch; DB-backed public wiring proves deterministic source-failure IDs persist through Lane C public service calls.
- **CON-020 (DONE)**: Connector fixture identity/timing quality is complete for duplicate evidence IDs and evidence observed outside the retrieval-run time window.
- **TD-080 (DONE)**: Report-run schema contract is complete for serialized `ReportRunContract`.
- **TD-081 (DONE)**: Report manifest metadata schema tightening is complete for stable generated `source_manifest`, `source_details`, `artifact_metadata`, and `cost_metrics` keys.
- **TD-090 (DONE)**: Planning-pack OpenAPI refresh is complete and full DB-enabled verification passes.
- **CON-021 (DONE)**: Connector human-review action semantics are planned before API mutation or worker implementation.
- **CON-022 (DONE)**: Connector human-review API route/reviewer/auth semantics are planned before mutation implementation.
- **CON-023 (DONE)**: Connector fixture evidence provenance quality is complete for missing evidence text, caveat, and non-failure source-date checks.
- **TD-082 (DONE)**: Report metadata extension boundary is planned before schema/runtime/API implementation.
- **CON-024 (DONE)**: Connector review action API auth blocker is recorded; mutation routes must wait for an authenticated reviewer/operator principal dependency or accepted service-account delegation rule.
- **CON-025 (DONE)**: Connector reviewer principal boundary is implemented as a local service-account dependency with focused API tests; no mutation route is registered.
- **CON-026 (DONE)**: Connector review action route subset is accepted for `request_fixture_fix`, `requeue_after_fix`, and `cancel_review`; route/OpenAPI implementation remains deferred.
- **TD-083 (DONE)**: Report validation metadata is implemented as optional `artifact_metadata.validation` for contract/profile/ruleset identity.
- **CON-027 (DONE)**: Connector fixture retrieval metric quality now checks success/failure row and error count consistency.
- **TD-084 (DONE)**: Job schema boundary is accepted before any shared job schema edit.
- **CON-028 (DONE)**: Connector source-failure payload type quality now checks non-empty text and boolean retry fields.
- **CON-029 (DONE)**: Connector source-failure reason consistency now checks payload reason against retrieval metrics.
- **CON-030 (DONE)**: Connector retrieval failure-reason metric quality now requires blocked/failed retrieval failure reasons.
- **CON-031 (DONE)**: Connector succeeded-retrieval failure-metric quality now rejects success runs with failure reason metrics.
- **CON-032 (DONE)**: Connector fixture evidence domain quality now rejects flood fixture evidence outside the `flood` domain.
- **CON-033 (DONE)**: Connector fixture retrieval name quality now rejects flood fixture retrievals outside the `fixture_flood_static` connector.
- **CON-034 (DONE)**: Connector fixture evidence source consistency now rejects mixed `source_id` values inside one flood fixture run.
- **CON-035 (DONE)**: Connector fixture evidence area consistency now rejects mixed `area_id` values inside one flood fixture run.
- **NEXT**: After Session 1's Lane C evidence-linkage/OpenAPI branch reaches a clean merge point, implement the accepted review-action mutation route subset with OpenAPI refresh, or choose broader fixture-quality/report metadata work if route work would conflict.
Do not work on yet:
- Live connectors (Level 8 - out of scope for this lane plan)
- UI and production workflow expansion before D-001 passes
- Any Lane A/B/C module files (read only)
```

## Known blockers

| Item | Status | Impact |
|---|---|---|
| Shared-schema alignment for `schemas/*.json` | Source/evidence/claim/report root schemas aligned; source provenance-family schemas aligned; stable generated report manifest metadata tightened; planning-pack OpenAPI aligned to generated FastAPI contract; report metadata extension boundary accepted | Job schema, durable evidence-row retrieval lineage, and API mutation/workflow implementation remain future coordinated passes |
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
