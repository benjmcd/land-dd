# Worklog

Append concise entries. Do not rely on chat history.

## 2026-06-04 (Connector CON-032 fixture evidence domain quality)

- Tightened connector-local fixture quality for flood evidence domain consistency.
- Flood fixture evidence now fails closed unless `domain` is `flood`.
- Preserved boundary: no API route, OpenAPI change, DB schema change, queue behavior, connector runtime, live I/O, hook config, POSIX script, durable evidence-row lineage, or lane-owned module outside connector quality changed.
- Verification passed with DB smoke: 366 backend tests collected/passing, lint clean, mypy clean over 123 source files, migrations/seeds applied, and DB smoke passed.

## 2026-06-04 (Connector CON-031 succeeded-retrieval failure-metric quality)

- Tightened connector-local fixture quality for succeeded retrieval failure metrics.
- Succeeded fixture retrievals now fail closed if `metrics.failure_reason` is non-empty.
- Preserved boundary: no API route, OpenAPI change, DB schema change, queue behavior, connector runtime, live I/O, hook config, POSIX script, durable evidence-row lineage, or lane-owned module outside connector quality changed.
- Verification passed with DB smoke: 365 backend tests collected/passing, lint clean, mypy clean over 123 source files, migrations/seeds applied, and DB smoke passed.

## 2026-06-04 (Connector CON-030 retrieval failure-reason metric quality)

- Tightened connector-local fixture quality for retrieval-level failure reasons.
- Blocked or failed fixture retrievals now fail closed unless `metrics.failure_reason` is non-empty.
- Preserved boundary: no API route, OpenAPI change, DB schema change, queue behavior, connector runtime, live I/O, hook config, POSIX script, durable evidence-row lineage, or lane-owned module outside connector quality changed.
- Verification passed with DB smoke: 365 backend tests collected/passing, lint clean, mypy clean over 123 source files, migrations/seeds applied, and DB smoke passed.

## 2026-06-04 (Connector CON-029 source-failure reason consistency)

- Tightened connector-local fixture quality for source-failure reason consistency.
- Source-failure fixture payload `failure_reason` now fails closed when it disagrees with retrieval `metrics.failure_reason`.
- Preserved boundary: no API route, OpenAPI change, DB schema change, queue behavior, connector runtime, live I/O, hook config, POSIX script, durable evidence-row lineage, or lane-owned module outside connector quality changed.
- Verification passed with DB smoke: 365 backend tests collected/passing, lint clean, mypy clean over 123 source files, migrations/seeds applied, and DB smoke passed.

## 2026-06-04 (Connector CON-028 source-failure payload type quality)

- Tightened connector-local fixture quality for source-failure payload value types.
- Source-failure fixture payloads now fail closed unless `failure_reason` and `error_message` are non-empty text and `retryable` is boolean.
- Preserved boundary: no API route, OpenAPI change, DB schema change, queue behavior, connector runtime, live I/O, hook config, POSIX script, durable evidence-row lineage, or lane-owned module outside connector quality changed.
- Verification passed with DB smoke: 364 backend tests collected/passing, lint clean, mypy clean over 123 source files, migrations/seeds applied, and DB smoke passed.

## 2026-06-04 (Lane D TD-084 job schema boundary)

- Added ADR `docs/adr/lane-d-0018-job-schema-boundary.md` before any shared job schema edit.
- Recorded that `schemas/job_schema.json` is not a live connector-run/API contract until future schema/test work chooses `jobs.job_queue`, `ConnectorReviewQueueItem`, or a new `JobContract` as authority.
- Preserved source retrieval runs as connector provenance authority and jobs as orchestration state.
- Preserved boundary: no schema edit, API route, OpenAPI change, queue code, migration, connector runtime, live I/O, hook config, POSIX script, durable evidence-row lineage, or Lane A/B/C module changed.
- Verification passed with DB smoke: 363 backend tests collected/passing, lint clean, mypy clean over 123 source files, migrations/seeds applied, and DB smoke passed.

## 2026-06-04 (Connector CON-027 fixture retrieval metric quality)

- Tightened connector-local fixture quality around retrieval-run metric consistency.
- Succeeded fixture retrievals now fail closed unless `row_count` matches non-failure evidence count and `error_count` is zero.
- Blocked or failed fixture retrievals now fail closed unless `row_count` is explicit zero and `error_count` is positive.
- Preserved boundary: no API route, OpenAPI change, DB schema change, queue behavior, connector runtime, live I/O, hook config, POSIX script, durable evidence-row lineage, or lane-owned module outside connector quality changed.
- Verification passed with DB smoke: 363 backend tests collected/passing, lint clean, mypy clean over 123 source files, migrations/seeds applied, and DB smoke passed.

## 2026-06-04 (Lane D TD-083 report validation metadata)

- Implemented optional `artifact_metadata.validation` in generated report runs with report contract/profile and ruleset identity.
- Tightened `schemas/report_run_schema.json` for the optional validation metadata object and updated report schema/service/regression tests.
- Added ADR `docs/adr/lane-d-0017-report-validation-metadata.md` to record that the metadata does not claim verification-command execution or durable evidence-row `ingest_run_id` lineage.
- Preserved boundary: no API route, OpenAPI change, DB schema change, queue behavior, connector runtime, live I/O, hook config, POSIX script, durable evidence-row lineage, or Lane A/B/C module changed.
- Verification passed with DB smoke: 362 backend tests collected/passing, lint clean, mypy clean over 123 source files, migrations/seeds applied, and DB smoke passed.

## 2026-06-04 (Connector CON-026 review action route subset)

- Added ADR `docs/adr/lane-d-0016-connector-review-action-route-subset.md` to accept the next connector review mutation route subset before implementation.
- Accepted only `request_fixture_fix`, `requeue_after_fix`, and `cancel_review` because they map to existing queue repository transitions plus the tested reviewer principal.
- Kept `acknowledge`, `approve_for_connector_qa`, durable idempotency, reviewer ownership persistence, reviewer action history, production auth, dashboard workflow, and route implementation out of scope.
- Preserved boundary: no route registration, OpenAPI change, queue code, repository method, schema, migration, connector runtime behavior, live I/O, hook config, POSIX script, evidence behavior, claim behavior, or report behavior changed.

## 2026-06-04 (Connector CON-025 reviewer principal boundary)

- Added `backend/app/api/reviewer_auth.py` with a local service-account reviewer principal dependency for future connector review mutation routes.
- Added `backend/tests/api/test_reviewer_auth.py` covering accepted credentials, missing credentials, invalid credentials, unconfigured fail-closed behavior, and blank configuration rejection.
- Added ADR `docs/adr/lane-d-0015-connector-reviewer-principal.md` to accept the local service-account boundary while keeping production auth, route wiring, reviewer ownership persistence, and action history separate.
- Preserved boundary: no API route, OpenAPI change, queue mutation, settings/secrets, schema, migration, connector runtime behavior, live I/O, hook config, POSIX script, evidence behavior, claim behavior, or report behavior changed.
- Verification passed with DB smoke: 362 backend tests collected/passing, lint clean, mypy clean over 123 source files, migrations/seeds applied, and DB smoke passed.

## 2026-06-04 (Connector CON-024 review action API auth blocker)

- Added ADR `docs/adr/lane-d-0014-connector-review-api-auth-blocker.md` to record that connector review mutation API implementation is blocked by the absence of an authenticated reviewer/operator principal dependency.
- Rejected header-only reviewer identity as insufficient unless a future ADR defines a documented local service-account delegation rule with explicit limits.
- Preserved boundary: no API route, OpenAPI change, queue code, repository method, schema, migration, connector runtime behavior, live I/O, hook config, POSIX script, evidence behavior, claim behavior, or report behavior changed.
- Verification passed with DB smoke: 351 backend tests collected/passing, lint clean, mypy clean over 121 source files, migrations/seeds applied, and DB smoke passed.

## 2026-06-04 (Lane D TD-082 report metadata extension boundary)

- Added ADR `docs/adr/lane-d-0013-report-metadata-extension-boundary.md` to define accepted future report metadata extension families and promotion rules.
- Recorded that future metadata extensions must be additive, namespaced, and unable to assert evidence-row `ingest_run_id` lineage before lower-layer storage support exists.
- Preserved boundary: no report runtime behavior, API behavior, OpenAPI change, schema change, migration, queue behavior, live I/O, hook config, or POSIX script changed.
- Verification passed with DB smoke: 351 backend tests collected/passing, lint clean, mypy clean over 121 source files, migrations/seeds applied, and DB smoke passed.

## 2026-06-04 (Connector CON-023 fixture evidence provenance quality)

- Extended connector-local fixture quality with blocking checks for missing evidence provenance text, missing caveats, and missing non-failure source dates.
- Added focused fixture-quality coverage proving those gaps fail closed while source-failure evidence can still omit `source_date`.
- Preserved boundary: no API route, OpenAPI change, durable queue behavior, repository method, source/evidence/claim/report behavior, schema, migration, live I/O, hook config, or POSIX script changed.
- Verification passed with DB smoke: 351 backend tests collected/passing, lint clean, mypy clean over 121 source files, migrations/seeds applied, and DB smoke passed.

## 2026-06-04 (TA-080 plus CON-022 merge reconciliation)

- Resolved shared state/task merge records by preserving both CON-022 connector human-review API semantics and TA-080 Lane A source provenance-family schema parity.
- Removed source provenance-family schema planning from current future-work pointers now that TA-080 is present in root.
- Verification passed with DB smoke after reconciliation: 350 backend tests collected/passing, lint clean, mypy clean over 121 source files, migrations/seeds applied, and DB smoke passed.

## 2026-06-04 (Connector CON-022 human-review API semantics)

- Added ADR `docs/adr/lane-d-0012-connector-human-review-api-semantics.md` to accept future route, reviewer identity, auth, idempotency, request, response, and fail-closed transition semantics.
- Accepted future route shape: `POST /connector-runs/{ingest_run_id}/review-actions`.
- Recorded that implementation remains separate because auth/reviewer identity enforcement and any needed queue transition or reviewer-ownership persistence must be planned before code.
- Preserved the boundary: no API route, OpenAPI change, connector runtime, repository method, queue code, schema, migration, evidence, claim, report, live I/O, hook config, or POSIX script changed.
- Verification passed with DB smoke: 344 backend tests collected/passing, lint clean, mypy clean over 120 source files, migrations/seeds applied, and DB smoke passed.

## 2026-06-04 (Lane A TA-080 source provenance-family schema parity)

- Created isolated worktree `worktrees/lane-a-provenance-schemas` on branch `lane-a/provenance-schemas` from root `main` at `a1ae1b5` to avoid Session 2 connector review workflow/API mutation work.
- Added `schemas/source_provenance_schema.json` as the separate source provenance-family schema for `SourceDatasetContract`, `SourceDatasetVersionContract`, and `SourceRetrievalRunContract`.
- Added source provenance-family schema parity tests that track contract field sets, `SourceRetrievalStatus` values, and non-negative retrieval row/error/warning counts.
- Updated Lane A ADR/plan/state plus project state to close the source provenance-family schema gap while leaving runtime validation, migrations, connector behavior, queue semantics, live I/O, and durable `ingest_run_id` evidence-row linkage as separate future work.
- Verification passed: focused source provenance-family schema tests; focused ruff/mypy; backend collection; full DB-enabled PowerShell verification with 350 backend tests passing, lint clean, mypy clean over 121 source files, migrations/seeds apply, and DB smoke passes.

## 2026-06-04 (Connector CON-021 human-review action semantics)

- Added ADR `docs/adr/lane-d-0011-connector-human-review-actions.md` to define future connector human-review action vocabulary before any mutation API or worker workflow.
- Recorded planned actions: `acknowledge`, `approve_for_connector_qa`, `request_fixture_fix`, `requeue_after_fix`, and `cancel_review`.
- Updated connector and Lane D planning/state records to keep human review as orchestration over `connector_review_status` queue rows, with `source.ingest_runs` remaining provenance authority and `jobs.job_queue` remaining review orchestration state.
- Preserved the boundary: no connector runtime, API route, repository method, queue code, schema, migration, evidence, claim, report, live I/O, hook config, or POSIX script changed.
- Verification passed: full DB-enabled PowerShell verification with 344 backend tests, lint clean, mypy clean over 120 source files, migrations/seeds apply, and DB smoke passes.

## 2026-06-04 (Lane D TD-090 planning-pack OpenAPI refresh)

- Created isolated worktree `worktrees/lane-d-openapi` on branch `lane-d/openapi-refresh` from root `main` at `7ee5f8b` to avoid Session 2's active connector work.
- Regenerated `docs/planning_pack/api/openapi_stub.yaml` from the live FastAPI app via `create_app().openapi()`.
- Updated `docs/planning_pack/11_API_AND_INTEGRATION_SPEC.md` so implemented endpoints are separated from future product-roadmap endpoints.
- Updated `docs/planning_pack/README.md`, Lane D plans, task queue, and state records to mark the OpenAPI refresh as TD-090.
- Added `backend/tests/test_planning_pack_schema_copies.py` coverage that fails closed if the planning-pack OpenAPI reference drifts from the generated FastAPI contract.
- Preserved the boundary: no API behavior, connector runtime, connector queue mutation, report behavior, schemas, migrations, live I/O, hook config, or POSIX scripts were changed.
- Verification passed before TD-081 integration: planning-pack parity tests; focused ruff/mypy; backend collection; full DB-enabled PowerShell verification with 342 backend tests, lint clean, mypy clean over 120 source files, migrations/seeds apply, and DB smoke passes.
- Rebased TD-090 onto TD-081 (`ea0d69a`), preserving TD-081 report metadata schema records and TD-090 OpenAPI records. Full DB-enabled PowerShell verification passes with 344 backend tests, lint clean, mypy clean over 120 source files, migrations/seeds apply, and DB smoke passes.

## 2026-06-04 (Lane D TD-081 report manifest metadata schema)

- Tightened `schemas/report_run_schema.json` for stable generated report metadata: `source_manifest`, `source_details`, `artifact_metadata`, and `cost_metrics`.
- Extended `backend/tests/reports/test_report_schema_contract.py` to guard nested manifest required keys, source governance detail shape, `AuthorityLevel` enum parity, artifact identity, optional persistence/output fields, and non-negative cost metrics.
- Added ADR `docs/adr/lane-d-0010-report-manifest-metadata.md` and amended ADR `lane-d-0009-report-run-schema` to record TD-081 as the separate manifest metadata follow-up it had deferred.
- Updated Lane D and Level 7/8 planning/state records so report manifest metadata tightening is no longer listed as an open schema gap; source provenance-family schemas, job schema, new report metadata extensions, live connectors, and durable `ingest_run_id` evidence-row linkage remain future work. Planning-pack OpenAPI is resolved separately by TD-090.
- Preserved the boundary: no API route behavior, runtime JSON Schema validation, DB migration, connector behavior, Lane A/B/C implementation, live I/O, hook config, or POSIX scripts were changed.
- Verification passed: focused report schema/default contract tests; focused report schema ruff/mypy; broader report/API pytest/ruff/mypy; full DB-enabled PowerShell verification with 343 backend tests, lint clean, mypy clean over 120 source files, migrations/seeds apply, and DB smoke passes.

## 2026-06-04 (Lane D TD-080 report-run schema contract)

- Created isolated worktree `worktrees/lane-d-report-schema` on branch `lane-d/report-schema` from root `main` at `3001c65` to avoid Session 2's active connector fixture-quality work.
- Added `schemas/report_run_schema.json` as the serialized `ReportRunContract` schema, with `intent_code`/`status` enum constraints and Lane C evidence/claim schema references for nested arrays.
- Added `backend/tests/reports/test_report_schema_contract.py` to guard field/required parity, enum parity, nested schema references, and serialized contract field set.
- Added ADR `docs/adr/lane-d-0009-report-run-schema.md` to record that `source_manifest` and `artifact_metadata` remain open objects pending future manifest metadata decisions.
- Updated Lane D plan/state, D-003 schema-contract note, manifest routing, project state, validation log, and worklog.
- Preserved the boundary: no connector implementation/tests/fixtures, Lane A/B/C module files, migrations, API route behavior, live I/O, hook config, or POSIX scripts were changed.
- Verification passed: focused report schema/default contract tests; Lane D report/API collection; focused report schema ruff/mypy; `git diff --check`; full DB-enabled PowerShell verification with 339 backend tests, lint clean, mypy clean over 120 source files, migrations/seeds apply, and DB smoke passes.
- Merged TD-080 into root after CON-020 and preserved both CON-020 and TD-080 state records. Combined full DB-enabled PowerShell verification passes with 341 backend tests, lint clean, mypy clean over 120 source files, migrations/seeds apply, and DB smoke passes.

## 2026-06-04 (integration rehearsal TC-180 plus CON-017/CON-018)

- Created isolated branch `codex/session2-lane-c-con018-rehearsal` from rebased Lane C TC-180 at `6dde79e` and merged Session 2 branch `codex/con-017-queue-read-model`.
- Resolved only append-style shared state conflicts in `state/PROJECT_STATE.md`, `state/VALIDATION_LOG.md`, and `state/WORKLOG.md`, preserving both TC-180 and CON-017/CON-018 records.
- Verified the combined branch with focused connector/API/Lane C checks, DB-enabled focused queue/API/evidence persistence checks, ruff/mypy, backend collection, and full DB-enabled Windows PowerShell verification with 331 backend tests passing.
- Preserved root `main` during the rehearsal; root landing remains a separate clean checkpoint.

## 2026-06-04 (Lane A TA-070 source schema-contract parity)

- Created isolated worktree `worktrees/lane-a-source-schema` on branch `lane-a/source-schema-contract` from root `main` at `6dde79e` to avoid Session 2's connector-zone work.
- Decided and recorded that `schemas/source_schema.json` represents serialized `SourceContract` only, not the broader source dataset/version/retrieval-run provenance family.
- Aligned `schemas/source_schema.json` to `SourceContract.model_fields`, including optional fields that still appear in serialized contract output, and constrained `authority_level` to the Lane A enum values.
- Added `backend/tests/source_registry/test_source_schema_contract.py` to guard schema property/required-field parity, authority-level enum parity, and exclusion of dataset/version/retrieval-run fields.
- Updated Lane A ADR/plan/state plus the D-003 schema-contract note to close the source schema gap while leaving source provenance-family schemas, job schema, report-run schema, and OpenAPI refresh as future work.
- Preserved the boundary: no connector implementation, connector tests, connector fixtures, Lane C evidence/claim code, Lane D API/report code, migrations, live I/O, hook config, or POSIX scripts were changed.
- Verification passed: focused source schema-contract tests; Lane A source-registry collection/default test run; targeted ruff/mypy; `git diff --check`; full DB-enabled PowerShell verification with 330 backend tests, lint clean, mypy clean over 119 source files, migrations/seeds apply, and DB smoke passes.

## 2026-06-04 (Lane C TC-180 source-failure evidence ID preservation)

- Created isolated worktree `worktrees/lane-c-failure-id` on branch `lane-c/failure-id-preservation` from root `main` at `e8f13fd` to avoid Session 2's connector-zone work.
- Extended `EvidenceService.create_source_failure(...)` with optional `evidence_id` support so Lane C's public service can preserve caller-supplied source-failure evidence identity.
- Added in-memory evidence-service tests proving supplied source-failure IDs are preserved and duplicate supplied IDs are rejected without overwrite.
- Updated the DB-gated SQLAlchemy evidence-service persistence test to prove a supplied source-failure ID round-trips through `evidence.observations`.
- Preserved the boundary: no connector implementation, connector tests, connector fixtures, API queue/status code, migrations, shared schemas, live I/O, claims, or reports were changed in TC-180. CON-019 later completes connector-zone adapter adoption in the Session 2 integration branch.
- Rebased onto root `main` at `6777134` after CON-016 landed, preserving connector queue worker state, task, validation, and worklog records.
- Verification passed: focused evidence-service tests; DB-gated source-failure persistence assertion; targeted ruff/mypy; Lane C evidence/claims tests with DB smoke; Lane C ruff/mypy; import-isolation scan; `git diff --check`; full DB-enabled PowerShell verification with 326 backend tests, lint clean, mypy clean over 118 source files, migrations/seeds apply, and DB smoke passes.

## 2026-06-04 (connector CON-018)

- Completed CON-018 as repository-level connector queue retry/requeue/cancel semantics.
- Added `docs/adr/lane-d-0007-connector-queue-retry-cancel.md` to define retry and cancellation boundaries.
- Extended connector review queue repositories with `requeue_failed(...)` and `cancel(...)`.
- Requeue is limited to failed connector review jobs with remaining attempts, preserves attempt count, clears lock/finish metadata, schedules `not_before`, and records a reason.
- Cancellation is limited to non-succeeded/non-cancelled connector review jobs and records a reason.
- Preserved the existing boundary: no API-side mutation, automatic retry policy, timeout handling, scheduler, background loop, queue dashboard, live connector execution, evidence persistence, claims, reports, schema/migration edit, durable `ingest_run_id` evidence-row linkage claim, or exact source-failure evidence ID preservation claim was introduced.

## 2026-06-04 (connector CON-017)

- Completed CON-017 as read-only connector queue worker-state API surfacing.
- Added `docs/adr/lane-d-0006-connector-queue-worker-read-model.md` to define the read-model boundary after CON-016 queue lease semantics.
- Extended `GET /connector-runs/{ingest_run_id}/review-queue` responses with attempts, max attempts, lock/start/finish timestamps, lock owner, and last error.
- Added in-memory and DB-backed API tests proving queued defaults and leased running worker state are surfaced through the existing endpoint.
- Preserved the existing boundary: no API-side job mutation, worker execution, scheduler, background loop, retry/requeue/cancel policy, queue dashboard, live connector execution, evidence persistence, claims, reports, schema/migration edit, durable `ingest_run_id` evidence-row linkage claim, or exact source-failure evidence ID preservation claim was introduced.

## 2026-06-04 (connector CON-016)

- Completed CON-016 as repository-level connector review queue worker lease and finish semantics.
- Added `docs/adr/lane-d-0005-connector-queue-worker.md` to accept queue mutation rules before worker-facing behavior.
- Extended `ConnectorReviewQueueRepository`, `InMemoryConnectorReviewQueueRepository`, and `SqlAlchemyConnectorReviewQueueRepository` with `lease_next(...)`, `mark_succeeded(...)`, and `mark_failed(...)`.
- Lease behavior is limited to `connector_review_status` jobs in `queued` or `needs_review` state, respects attempts/not-before state, increments attempts, and records lock/start metadata.
- Finish behavior only completes running connector review queue jobs and records success or failure metadata.
- Preserved the existing boundary: no long-running worker process, scheduler, background loop, API mutation route, retry/requeue policy, queue dashboard, live connector execution, evidence persistence, claims, reports, schema/migration edit, durable `ingest_run_id` evidence-row linkage claim, or exact source-failure evidence ID preservation claim was introduced.

## 2026-06-04 (connector CON-015)

- Completed CON-015 as read-only connector review queue API retrieval.
- Added `GET /connector-runs/{ingest_run_id}/review-queue` in `backend/app/api/connectors.py`.
- Wired `ApiServices.connector_review_queue` to `InMemoryConnectorReviewQueueRepository` for default API services and `SqlAlchemyConnectorReviewQueueRepository` for DB-backed API services.
- Added `docs/adr/lane-d-0004-connector-queue-retrieval.md` to define read-only retrieval semantics before exposing queue data.
- Added API tests proving in-memory queue retrieval, unknown queue 404 behavior, and DB-backed API retrieval of persisted `jobs.job_queue` rows.
- Preserved the existing boundary: no live I/O, worker execution, job mutation, queue dashboard, schema/migration edit, claim/report shortcut, durable `ingest_run_id` evidence-row linkage claim, or exact source-failure evidence ID preservation claim was introduced.

## 2026-06-04 (connector CON-014)

- Completed CON-014 as durable connector review queue persistence using existing `jobs.job_queue`.
- Added `ConnectorReviewQueueItem`, `InMemoryConnectorReviewQueueRepository`, and `SqlAlchemyConnectorReviewQueueRepository` in `backend/app/connectors/review_queue.py`.
- Queue rows use `job_type = "connector_review_status"`, idempotency key `connector_review_status:<ingest_run_id>`, and payload references to `source.ingest_runs.ingest_run_id` so `jobs.job_queue` does not replace source retrieval provenance.
- Added `docs/adr/lane-d-0003-connector-review-queue.md` to record queue ownership/semantics before durable queue usage.
- Added connector tests for idempotent in-memory queueing, human-review prioritization, and DB-backed persistence into `jobs.job_queue`.
- Preserved the existing boundary: no live I/O, worker execution, queue dashboard, API DB queue retrieval, schema/migration edit, claim/report shortcut, durable `ingest_run_id` evidence-row linkage claim, or exact source-failure evidence ID preservation claim was introduced.

## 2026-06-04 (connector CON-013)

- Completed CON-013 as a connector review status composition plus Lane D API status surface.
- Added `ConnectorRunReviewStatus` and `build_connector_run_review_status(...)` in `backend/app/connectors/review_status.py` to combine a connector review handoff with a fixture quality profile.
- Added `GET /connector-runs/{ingest_run_id}/review-status` in `backend/app/api/connectors.py`, backed by an in-memory `ApiServices.connector_review_statuses` store.
- Added connector/API tests proving success status, source-failure human-review status, fixture-quality blocking issues, connector-name mismatch fail-closed behavior, and 404 behavior for unknown connector runs.
- Preserved the existing boundary: no live I/O, durable queue persistence, connector status DB table, schema/migration edit, claim/report shortcut, durable `ingest_run_id` evidence-row linkage claim, or exact source-failure evidence ID preservation claim was introduced.
- Verification passed: focused review-status/API tests; connector/API tests; connector/API ruff/mypy; full DB-enabled `.\scripts\verify.ps1`.

## 2026-06-04 (connector CON-012)

- Completed CON-012 in the connector integration zone as a deterministic fixture quality profile for flood fixture connector output.
- Added `evaluate_flood_fixture_quality(...)`, `ConnectorFixtureQualityProfile`, and fixture quality issue codes in `backend/app/connectors/fixture_quality.py`.
- The evaluator flags fixture-local provenance, dataset-version, row-count, spatial evidence geometry/precision, retrieval-status/evidence consistency, and source-failure payload/confidence gaps.
- Added connector tests proving the success and source-failure fixtures pass, synthetic fixture mutations fail closed with explicit issue codes, and the module avoids API, persistence, reports, claims, Lane A/C implementation, and live I/O imports.
- Preserved the existing boundary: no live I/O, API route, durable queue persistence, claim/report shortcut, schema edit, Lane A/B/C/D implementation change, durable `ingest_run_id` evidence-row linkage claim, or exact source-failure evidence ID preservation claim was introduced.
- Verification passed: focused fixture-quality tests; full connector tests; connector ruff/mypy; full DB-enabled `.\scripts\verify.ps1`.

## 2026-06-04 (connector CON-011)

- Completed CON-011 in the connector integration zone as a pure consumer for CON-010 review packets.
- Added `build_connector_review_handoff(...)`, `ConnectorReviewHandoff`, `ConnectorReviewDisposition`, and `ConnectorReviewPriority` in `backend/app/connectors/review_handoff.py`.
- The handoff classifies packets into `needs_human_review`, `ready_for_connector_qa`, or `idempotent_noop`, and exposes `to_review_record()` for JSON-safe future consumers.
- Added connector tests proving successful fixture workflow packets route to connector QA, blocked/source-failure packets route to high-priority human review, repeated fixture runs route to an idempotency log, and the handoff module avoids API, persistence, reports, claims, Lane A/C implementation, and live I/O imports.
- Preserved the existing boundary: no live I/O, API route, durable queue persistence, claim/report shortcut, schema edit, Lane A/B/C/D implementation change, durable `ingest_run_id` evidence-row linkage claim, or exact source-failure evidence ID preservation claim was introduced.
- Verification passed: focused review-handoff/review-packet tests; full connector tests; connector ruff/mypy; full DB-enabled `.\scripts\verify.ps1`.

## 2026-06-04 (connector CON-010)

- Completed CON-010 in the connector integration zone as a pure run/status review packet and human-review handoff projection.
- Added `build_connector_run_review_packet(...)`, `ConnectorRunReviewPacket`, `ConnectorReviewSignal`, and `ConnectorReviewSignalCode` in `backend/app/connectors/review_packet.py`.
- The packet summarizes connector retrieval status, provenance recorded/skipped state, evidence input/created/skipped counts, source-failure counts, evidence IDs, review signals, and deterministic human-review tasks.
- Added connector tests proving successful fixture workflow packets do not require human review, blocked/source-failure workflow packets do require review, repeated fixture runs emit idempotent skip signals without requiring review, and the review packet module avoids API, reports, claims, DB/session, Lane A/C implementation, and live I/O imports.
- Preserved the existing boundary: no live I/O, API route, claim/report shortcut, persistence change, schema edit, Lane A/B/C/D implementation change, durable `ingest_run_id` evidence-row linkage claim, or exact source-failure evidence ID preservation claim was introduced.
- Verification passed: focused review-packet/fixture-workflow tests; full connector tests; connector ruff/mypy; full DB-enabled `.\scripts\verify.ps1`.

## 2026-06-04 (Session 1 planning-pack schema-copy reconciliation)

- Created isolated worktree `worktrees/session1-pack-schemas` on branch `lane-c/session1-pack-schemas` to avoid Session 2's active connector-zone work.
- Rebased the worktree onto root `main` at `56d53c8` after CON-009 landed, preserving CON-003/CON-004/CON-005/CON-006/CON-007/CON-008/CON-009 connector state/task records.
- Synced `docs/planning_pack/schemas/evidence_schema.json` and `docs/planning_pack/schemas/claim_schema.json` to the canonical root Lane C schemas.
- Added `backend/tests/test_planning_pack_schema_copies.py` so the planning-pack evidence/claim schema copies cannot silently drift from the root contract schemas.
- Updated Lane C schema ADR/plan/state wording to close the docs-packaging follow-up while keeping source/job/report/OpenAPI schema work out of scope.
- Verified focused planning-pack schema-copy parity, targeted ruff/mypy, full backend collection from `backend`, exact schema-copy equality, whitespace, and full DB-enabled PowerShell verification. Result: 292 backend tests; lint clean; mypy clean over 105 source files; migrations/seeds apply; DB smoke passes.

## 2026-06-04 (connector CON-009)

- Completed CON-009 in the connector integration zone as a DB-backed fixture source-failure workflow smoke.
- Added a DB-enabled public-wiring test that runs `flood_failure.json` through SQLAlchemy-backed public Lane A provenance and public Lane C evidence services, then repeats the run to prove idempotency.
- Verified first-run behavior records the blocked retrieval run with the connector-supplied `ingest_run_id` and persists source-failure evidence through `EvidenceService.create_source_failure(...)`.
- Verified second-run behavior skips the existing retrieval run and the matching persisted source-failure fingerprint.
- Preserved the existing boundary: no live I/O, claims, reports, schema changes, production connector behavior, or exact source-failure evidence ID preservation claim was introduced.
- Verification passed: `py -3.12 -m pytest -q tests/connectors/test_public_wiring.py`; `$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/connectors/test_public_wiring.py`; `ruff check tests/connectors/test_public_wiring.py`; `mypy tests/connectors/test_public_wiring.py`; `$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1`; `git diff --check`.

## 2026-06-04 (connector CON-008)

- Completed CON-008 in the connector integration zone as a DB-backed fixture success workflow smoke.
- Added a DB-enabled public-wiring test that seeds the local fixture area/source/dataset/version, runs the fixture workflow through SQLAlchemy-backed public Lane A provenance and public Lane C evidence services, and cleans fixture-owned DB rows before and after execution.
- Verified first-run behavior records the connector-supplied `ingest_run_id` and persists evidence through public Lane C methods; verified second-run behavior skips the existing retrieval run and deterministic evidence ID.
- Preserved the existing boundary: no live I/O, claims, reports, schema changes, or durable `ingest_run_id` evidence-row linkage claim was introduced.
- Verification passed: `py -3.12 -m pytest -q tests/connectors/test_public_wiring.py`; `$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/connectors/test_public_wiring.py`; `ruff check tests/connectors/test_public_wiring.py`; `mypy tests/connectors/test_public_wiring.py`; `$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1`; `git diff --check`.

## 2026-06-04 (connector CON-007)

- Completed CON-007 as a coordinated Lane A public provenance follow-up plus connector public wiring.
- Added `SourceProvenanceService.record_retrieval_run_contract(...)` and `retrieval_run_exists(...)`, preserving supplied `SourceRetrievalRunContract.ingest_run_id` while validating referenced dataset versions.
- Added `SourceProvenanceServiceRetrievalPort` and `build_fixture_workflow_with_public_lane_services(...)` so connector workflows can use the public Lane A provenance service without importing Lane A repositories.
- Added source provenance and connector tests proving identity preservation, duplicate failure, SQLAlchemy round-trip with DB smoke enabled, and connector public-service wiring without repository imports.
- Verification passed: `$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/source_registry/test_source_provenance.py tests/connectors`; targeted ruff/mypy; `$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1`; `git diff --check`.

## 2026-06-04 (connector CON-006)

- Completed CON-006 in the connector integration zone: added `build_fixture_workflow_with_public_services` in `backend/app/connectors/public_wiring.py`.
- Public-service wiring now composes fixture workflows with public Lane C `EvidenceService` methods for normal evidence, source failures, duplicate checks, and source-failure fingerprinting, while still requiring an identity-preserving retrieval provenance port.
- Aligned `tests/fixtures/connectors/flood_failure.json` to Lane C's controlled source-failure payload keys (`failure_reason`, `error_message`, `retryable`) so fixture failures pass public evidence validation without relaxing Lane C rules.
- Recorded the remaining Lane A follow-up: current `SourceProvenanceService.record_retrieval_run(...)` cannot preserve a supplied `SourceRetrievalRunContract.ingest_run_id`, so DB-backed connector workflow ingestion is still not claimed until a Lane A-compatible public provenance method/adapter is coordinated and DB-smoke verified.
- Verification passed: `py -3.12 -m pytest -q tests/connectors`; `ruff check app/connectors tests/connectors`; `mypy app/connectors tests/connectors`; `.\scripts\verify.ps1`; `git diff --check`.

## 2026-06-04 (connector CON-005)

- Completed CON-005 in the connector integration zone: added `FixtureConnectorIngestWorkflow` in `backend/app/connectors/fixture_workflow.py`.
- Added connector workflow tests proving retrieval provenance is recorded before evidence ingestion for success and blocked/source-failure fixtures, repeated fixture workflow runs are idempotent across retrieval and evidence stages, and workflow code does not import live I/O modules, Lane A source registry, Lane C evidence/claims, reports, schemas, or DB sessions.
- Recorded the remaining concrete wiring gap: CON-005 composes injected ports only; DB-backed production workflow wiring needs a public Lane A-compatible provenance port that preserves supplied `SourceRetrievalRunContract.ingest_run_id`, plus public Lane C evidence-ingestion service wiring.
- Verification passed: `py -3.12 -m pytest -q tests/connectors`; `ruff check app/connectors tests/connectors`; `mypy app/connectors tests/connectors`; `.\scripts\verify.ps1`; `git diff --check`.

## 2026-06-04 (connector CON-004)

- Completed CON-004 in the connector integration zone: added `ConnectorRetrievalProvenanceAdapter` and `SourceRetrievalProvenancePort` in `backend/app/connectors/retrieval_provenance.py`.
- Added connector tests proving retrieval runs are recorded with supplied `ingest_run_id`/`dataset_version_id`, duplicate retrieval runs are skipped, provenance recording can run before evidence ingestion, and the adapter does not import Lane A services/repositories, evidence, claims, reports, or live I/O modules.
- Recorded the remaining concrete wiring gap: current Lane A `SourceProvenanceService.record_retrieval_run(...)` creates a new retrieval run and does not accept a supplied `SourceRetrievalRunContract`, so production wiring needs a Lane A public method or Lane A-owned adapter that preserves connector run identity.
- Verification passed: `py -3.12 -m pytest -q tests/connectors`; `ruff check app/connectors tests/connectors`; `mypy app/connectors tests/connectors`; `.\scripts\verify.ps1`; `git diff --check`.

## 2026-06-04 (connector CON-003)

- Completed CON-003 in the connector integration zone: added `ConnectorEvidenceIngestionAdapter` and `EvidenceIngestionPort` in `backend/app/connectors/evidence_ingestion.py`.
- Added connector tests proving normal evidence routes to `create_observation`, source-failure templates route to `create_source_failure`, deterministic duplicate evidence IDs are skipped, source-failure fingerprints prevent repeated fixture duplicates, inconsistent source-failure flags fail closed, and connector ingestion stays before claims/reports/live I/O.
- Updated connector plan/state/task records. CON-004 is now the next recorded connector task: retrieval-run provenance adapter or handoff before claiming a complete connector ingest workflow.
- Verification passed: `py -3.12 -m pytest -q tests/connectors`; `ruff check app/connectors tests/connectors`; `mypy app/connectors tests/connectors`; `.\scripts\verify.ps1`; `git diff --check`.

## 2026-06-04 (Session 1 Lane C TC-170 schema-contract alignment)

- Created isolated worktree `worktrees/session1-lane-c-schema` on branch `lane-c/session1-schema-contracts` from root `main` at `cf9897e` because Session 2 was actively editing D-004 shared plan/state files in the root checkout.
- Rebased the Lane C branch onto root `main` at `a43b3e3` before landing so D-004, D-005, CON-001, CON-002, connector ownership, task, and state updates remain current.
- Aligned canonical `schemas/evidence_schema.json` to serialized `EvidenceContract` fields and enums; removed stale DB/doc fields (`retrieved_at`, `geometry_wkt`, `metadata`, `authority_level`).
- Aligned canonical `schemas/claim_schema.json` to serialized `ClaimContract` fields and enums; removed stale fields (`intent`, `contradiction_group_ids`, `metadata`) and added rule metadata fields.
- Added schema-contract parity tests for evidence and claim schemas without adding a JSON-schema dependency.
- Added `docs/adr/lane-c-schemas.md` to record the shared-schema contract decision required for `schemas/*.json` edits.
- Verified focused schema-contract tests, DB-enabled Lane C tests, targeted Lane C lint/type checks, import-isolation scan, full collection, and full PowerShell verification with DB smoke enabled. Result: 268 tests pass; lint clean; mypy clean (96 source files); DB smoke passes.
- Deferred stale `docs/planning_pack/schemas/*.json` alignment to a separate docs/packaging pass.

## 2026-06-04 (Session 2 CON-001 fixture flood connector)

- Implemented `StaticFloodFixtureConnector` in the connector integration zone only.
- Added local success and failure fixtures under `tests/fixtures/connectors/`.
- Added connector tests proving source retrieval provenance, flood spatial evidence output, blocked source-failure output, idempotent fixture IDs, URI-like path rejection, and no claim/report/live-IO imports.
- Kept Lane A/B/C/D implementation files, shared schemas, migrations, API/report wiring, credentials, browser/download steps, and live network behavior out of scope.
- Completed CON-002 as a handoff decision: connector-zone ingestion adapters must call injected public Lane C evidence service methods, not Lane C repositories/private helpers. Normal evidence routes to `create_observation`; source-failure templates route to `create_source_failure`; durable `ingest_run_id` linkage and exact source-failure field preservation remain future Lane C/schema coordination gaps.

## 2026-06-04 (Session 2 D-005 connector ownership decision packet)

- Prepared D-005 without editing `LANE_OWNERSHIP.md`, because that file is canonical but reserves updates for the human coordinator.
- Added proposed ADR `docs/adr/lane-d-0002-connector-entry-ownership.md`.
- Recommended a coordinator-owned connector integration zone for future `backend/app/connectors/`, `backend/tests/connectors/`, and `tests/fixtures/connectors/`, instead of assigning connector ingestion to Lane A, C, or D by default.
- Recommended `SourceRetrievalRunContract` / `source.ingest_runs` as connector lifecycle and provenance authority, with `jobs.job_queue` reserved for future async orchestration that references retrieval runs rather than replacing them.
- Kept runtime code, shared schemas, migrations, `LANE_OWNERSHIP.md`, and Lane A/B/C implementation files unchanged.
- Resolved D-005 by adding the connector integration zone to `LANE_OWNERSHIP.md`, accepting the connector ownership ADR, and assigning the first fixture-only flood connector pass to the connector integration zone. No runtime connector code was created.

## 2026-06-04 (Session 2 D-004 Level 8 ownership and fixture acceptance)

- Completed Lane D D-004 from root `main` after Session 1 landed Lane B TB-100 at `cf9897e`.
- Mapped Level 8 connector gates L8-001 through L8-010 to lane owners and supporting owners before connector runtime code.
- Defined the first fixture-only connector acceptance path as a static local flood fixture: no live network, no browser/download step, no vendor credential, and no paid/live API dependency.
- Recorded pre-code decisions for future `backend/app/connectors/` ownership, connector run lifecycle authority, idempotency identity, success evidence shape, failure taxonomy, and geometry fixture needs.
- Preserved D-003 schema-contract boundaries: no shared schemas, migrations, connector runtime code, or Lane A/B/C implementation files were edited.
- Set D-005 as the next safe step: resolve connector module ownership and run lifecycle authority before any fixture connector implementation.

## 2026-06-04 (Session 1 Lane B TB-100 coordinate validation hardening)

- Created isolated worktree `worktrees/session1-lane-b` on branch `lane-b/session1-geometry-hardening` from root `main` at `04d0a8f` to avoid Session 2's active Lane D D-001 checkout edits.
- Implemented a Lane B-only validator hardening slice: non-finite longitude/latitude values and out-of-range EPSG:4326 longitude/latitude positions now fail `validate_geojson`.
- Added one invalid coordinate fixture plus inline non-finite coordinate regression coverage in `backend/tests/area_geometry/test_area_service.py`.
- Verified focused service/validator checks, DB-enabled Lane B tests, targeted Lane B lint/type checks, and full PowerShell verification with DB smoke enabled. Pre-merge result: 253 tests pass; lint clean; mypy clean (89 source files); DB smoke passes.
- Merged root `main` at D-001 into the Lane B worktree, resolving conflicts only in shared state files by preserving both Session 2 D-001 state and Session 1 TB-100 state.
- Verified post-merge focused Lane B/report/API checks and full PowerShell verification with DB smoke enabled. Result: 254 tests pass; lint clean; mypy clean (90 source files); DB smoke passes.
- Merged root `main` at D-002 into the Lane B worktree after `main` advanced again; conflicts were again limited to shared state files and resolved by preserving D-002 as current repo-wide authority and TB-100 as the isolated Lane B contribution.
- Verified post-D-002 focused Lane B/report/API checks and full PowerShell verification with DB smoke enabled. Result: 255 tests pass; lint clean; mypy clean (91 source files); DB smoke passes.
- Merged root `main` at D-003 into the Lane B worktree after coordination; conflicts were again limited to shared state files and resolved by preserving D-003 as current repo-wide authority and TB-100 as the isolated Lane B contribution.
- Verified post-D-003 full PowerShell verification with DB smoke enabled. Result: 255 tests pass; lint clean; mypy clean (91 source files); DB smoke passes.
- Squash-merged the verified Lane B TB-100 branch onto root `main` so coordinate hardening is now mainline without carrying temporary cross-session merge commits.
- Verified root `main` after squash merge: Lane B targeted tests pass with DB smoke enabled; targeted Lane B ruff/mypy pass; full PowerShell verification with DB smoke enabled passes with 255 tests, lint clean, mypy clean (91 source files), migrations/seeds, and DB smoke.
- Coordination note sent to Session 2 without changing its reasoning level; no action requested.

## 2026-06-04 (Session 2 D-000 report surfacing)

- Completed Lane D D-000 by updating `ReportRunService` to create stored unsupported-category SOURCE_FAILURE evidence for missing not-evaluated domains before rule evaluation.
- Preserved Lane C ownership: no Lane C implementation or state files were modified. The report service uses Lane C's not-evaluated helper, then normalizes the helper payload to the evidence ledger's controlled source-failure payload shape before storage.
- Updated report service, API scaffold, and DB-backed report repository tests so unsupported soil/septic, environmental hazards, resource context, and market context appear in report/API `unknowns`, source manifests, caveats, and cost metrics.
- Verified Lane D targeted checks: report/API tests pass with DB smoke enabled; targeted ruff and mypy pass.
- Verified full gate: `$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1` passes with 250 backend tests, lint clean, mypy clean (89 source files), migrations/seeds, and DB smoke.
- Updated Lane D plan/state, project state, deferred task plan, and task queue. D-000 is done; D-001 DB-backed API workflow wiring is now the next Lane D task.

## 2026-06-04 (Session 2 merged C-002 handoff)

- Merged Session 1's clean `codex/session1-lane-c` C-002 branch into root `main` after confirming the unsupported-category ruleset metadata now uses `severity_on_fail: unknown`.
- Resolved merge conflicts only in append-only state logs; no Lane C implementation logic was changed during conflict resolution.
- Verified the merged tree with targeted C-002/report/API tests, targeted ruff and mypy, full DB-gated PowerShell verification, and full test collection. Result: 250 tests collected and full DB-gated verification passes with lint clean and mypy clean (89 source files).
- Updated Lane D state and plan: C-002 is canonical, D-000 is the next Lane D task, and D-001 remains blocked until D-000 completes.

## 2026-06-04 (Session 1 C-002 not-evaluated rule categories)

- Implemented the Lane C-owned C-002 slice: added `backend/app/claims_engine/not_evaluated.py`, four unsupported-domain hard gates in `config/ruleset_homestead_mvp.yaml`, and rule-engine emission of deterministic `SeverityBand.UNKNOWN` claims from source-failure evidence for soil/septic, environmental hazard, resource context, and market context.
- Preserved the evidence-before-claim invariant: not-evaluated claims are generated only from source-failure evidence IDs; non-failure records for unsupported domains do not produce claims.
- Added `backend/tests/claims_engine/test_not_evaluated_claims.py` for ruleset declarations, helper-generated source-failure evidence, evidence-linked unknown claims, deterministic ordering, non-failure ignore behavior, and market-context safe language.
- Updated Lane C plan/state, project state, and task queue. C-002 is complete for Lane C claim/rule scope; Session 2/Lane D should wire report-run auto-creation/registration of unsupported-domain source-failure evidence in D-000 before D-001 completion.
- Verified before final rebase: Lane C claims tests pass with DB smoke enabled; report/API tests pass; full DB-gated backend pytest passes; direct DB smoke passes; targeted ruff/mypy pass; default PowerShell verification passes.

## 2026-06-04 (Session 2 C-002 handoff risk check)

- Rechecked root `main`, Session 1's worktree, and the Session 1 log before advancing Lane D. Root `main` remained clean and did not contain C-002 at the time of the check.
- Found Session 1's C-002 worktree still in a detached rebase state with unresolved conflict markers in `state/VALIDATION_LOG.md`.
- Read-only validation of the draft C-002 branch found the emitted not-evaluated claims were UNKNOWN, but the four unsupported-category ruleset entries and unit test still declared `severity_on_fail: informational`.
- Sent Session 1 a coordination note because D-000 depends on a canonical C-002 handoff whose claim behavior and ruleset metadata both use UNKNOWN for unsupported categories.
- Non-mutating merge simulation showed the C-002 branch conflicted with root `main` only in state files; no report/API code conflicts were identified.

## 2026-06-04 (Session 2 API unknown surfacing regression)

- Added a Lane D API regression proving `POST /report-runs` surfaces `SeverityBand.UNKNOWN` claims generated from stored source-failure evidence in the response `unknowns` list and cost metrics.
- This does not implement D-000 unsupported-category injection before C-002; it hardens the existing report/API behavior D-000 will rely on after Lane C emits unsupported-category unknown claims.
- Verified focused API checks: 8 API tests pass; targeted ruff and mypy pass.
- Verified Lane D checks: 18 report/API tests pass with DB smoke enabled.
- Verified `$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1`: 244 tests; lint clean; mypy clean (87 source files); migrations/seeds and DB smoke pass.

## 2026-06-04 (Session 2 Lane D boundary split + DB session pre-work)

- Resolved the C-002 report-surfacing ownership conflict in planning/coordination docs: Lane C owns unsupported-category claim/rule behavior; Lane D owns report/API surfacing as D-000 after C-002.
- Corrected the C-002 spec so unsupported-category rules use `unknown` severity, not `informational`, preserving report unknowns and the source-failure pattern.
- Added `backend/app/db/session.py` with `get_db_session()` delegating to the shared `get_session()` engine/session factory path.
- Added `backend/tests/api/test_db_session.py` to verify `get_db_session()` delegates without creating a new engine or requiring a live DB.
- Verified Lane D targeted checks: 17 report/API tests pass with DB smoke enabled; targeted ruff and mypy pass.
- Verified `$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1`: 243 tests; lint clean; mypy clean (87 source files); migrations/seeds and DB smoke pass.
- Re-audit note: D-001 pre-work is partially complete, but full DB-backed API wiring remains blocked until Lane C C-002 and Lane D D-000 are complete.

## 2026-06-04 (Session 1 C-001 ORM stabilization)

- Re-verified the C-001 handoff from the external session export against live repo state and found the full DB-smoke gate failed in the four DB-backed claim repository tests.
- Root cause: `ClaimModel` and dependent claim models declared ORM `ForeignKey(...)` constraints to cross-schema tables that were not all present in the active SQLAlchemy metadata, then claim/evidence links could flush before the parent claim row.
- Fixed `backend/app/claims_engine/models.py` so cross-schema DB FKs remain database-migration authority while the Lane C ORM maps those references as scalar UUID columns; internal `claims.claims` FKs remain for claim-local dependencies.
- Fixed `SqlAlchemyClaimRepository.add()` to flush the parent claim before adding claim/evidence links and verification tasks.
- Verified: failing claim DB test file passes (4 tests); Lane C evidence/claims tests pass (137 tests with DB smoke enabled); targeted ruff and mypy pass; Lane C import-isolation scan returns 0 matches; full collection reports 242 tests; `$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1` passes with lint clean, mypy clean (85 source files), migrations/seeds, and DB smoke.
- Re-audit note: C-001 is now live-verified after repair; Level 6 remains partial until C-002 not-evaluated categories are implemented by Lane C and surfaced through Lane D without violating ownership boundaries.

## 2026-06-04 (C-001 Claims ORM models + coordination infra)

- Implemented C-001: created `backend/app/claims_engine/models.py` with `ClaimModel`, `ClaimEvidenceLinkModel`, and `VerificationTaskModel` (all inheriting `AppBase`). All three ORM models verified against `db/migrations/0001_initial_spine.sql`. `ClaimModel.claim_metadata` is mapped with Python attribute name to avoid `DeclarativeBase.metadata` collision (actual DB column name is `metadata`). `rule_execution_run_id` and `intent_id` nullable FKs are mapped but not yet populated by the current rule engine path.
- Refactored `SqlAlchemyClaimRepository` in `claim_repo.py` from raw `text()` SQL to SQLAlchemy 2.x ORM (`session.add()`, `session.get()`, `select()`). All raw SQL and `_row_to_claim()`/`_claim_params()`/`_select_claim_statement()` helpers replaced by ORM equivalents. `_claim_metadata()`, `_metadata_evidence_ids()`, `_validate_claim_for_persistence()`, and `_verification_priority()` preserved unchanged.
- Updated `state/lane-c-state.md` and `state/lane-d-state.md` with C-001/C-002/D-001 as explicit next tasks.
- Created `CODEX_PARALLEL.md` — parallel session coordination protocol with file ownership map, pre-condition checks, and safe parallel execution rules.
- Updated `PROMPT_LANE_*.md` files to reflect current done/pending state for all four lanes.
- Updated `tasks/task_queue.yaml` — all T000-T060 now `done`; C-001 `pending`, C-002/D-001 `blocked`.
- Updated `LANE_OWNERSHIP.md` — added `db/base.py`, `db/types.py`, `validate_workspace.ps1`, `verify.ps1`, and `CODEX_PARALLEL.md` to the Shared Interface Zone.
- Verified: 201 tests pass; structural invariants ok; lint clean; mypy clean (85 source files).

## 2026-06-03 (non-fragility audit + invariant enforcement)

- Found and fixed critical non-negotiable violation: `forbidden_language` block in `ruleset_homestead_mvp.yaml` was silently discarded by the hand-rolled YAML parser (section != "hard_gates" guard). Fixed: parser now loads the 6 forbidden phrases into `RuleSet.forbidden_language`; `RuleEngine._check_forbidden_language()` raises `ValueError` if any generated claim contains a forbidden phrase. 7 tests added in `test_forbidden_language.py`.
- Fixed fragile `_unknown_claims` filter in `service.py`: replaced `"UNKNOWN" in claim.claim_code` substring scan with `claim.severity == SeverityBand.UNKNOWN` (the correct and complete signal).
- Added `intent_code_enum` to `db/types.py` — closes the gap for future ORM models against `core.intents` or `reports.report_runs`. Added explanatory comment for `area_type_enum` (the one known exception, pending coordinated migration).
- Added AGENTS.md non-negotiable: no agent name, model name, or AI attribution in any file or commit message.
- Removed `Author: Claude (ralplan)` tag from `plans/2026-06-03-repo-audit-and-forward-options.md`.
- Rewrote all session commit messages to remove `Co-Authored-By:` trailers (17 local commits; no remote push affected).
- Added 3 structural invariant checks to `scripts/validate_workspace.ps1` (runs as part of `verify.ps1`):
  1. Exactly 1 `DeclarativeBase` subclass in `backend/app/` (prevents ORM base fragmentation)
  2. Zero `.query(` calls in `backend/app/` (prevents SQLAlchemy 1.x API regression)
  3. No `noreply@anthropic` in tracked `.py` or `.sql` files (prevents agent attribution leakage)
- Verified: 201 tests pass (non-DB); 84 source files mypy-clean; ruff clean; structural invariants pass.

## 2026-06-03 (pre-Codex structural hardening — ralplan A-minus + deep re-audit)

**Initial hardening (commit group 99cde91–3d5a9fd):**
- Committed all 49 uncommitted files in 9 logical groups (CI scripts, Lane A provenance, Lane B area models, Lane C evidence/claim models, Lane D report persistence, ADRs, agent docs, state/plans, archive cleanup).
- Created `backend/app/db/base.py` with single `AppBase(DeclarativeBase)` + MetaData naming_convention for Alembic readiness.
- Created `backend/app/db/types.py` with canonical `authority_level_enum`, `confidence_band_enum`, `job_status_enum` (one definition each, `create_type=False`).
- Updated all 4 ORM model modules (source_registry, area_geometry, evidence_ledger, reports) to inherit from `AppBase`; removed duplicate enum declarations; backward-compat aliases preserved.
- Fixed 3 legacy `.query()` sites in `source_registry/provenance_repo.py` → SQLAlchemy 2.x `select()` style.
- Added `IntentCode(StrEnum)` to `domain/enums.py` with 9 values matching `core.intent_code` SQL enum exactly.
- Constrained `ReportRunContract.intent_code` to `IntentCode`; updated API and service signatures.
- Fixed `SqlAlchemyReportRunRepository._contract_to_model()` which was silently dropping `intent_id` (setting it NULL); added `_resolve_intent_id()` that looks up `core.intents` by `intent_code`.
- Added DB assertion to `test_report_repository.py` verifying `intent_id` is NOT NULL after round-trip.

**Deep re-audit (commits 4f4c0ca, 714a07b):**
- Discovered that the global `mypy` used by `verify.ps1` catches errors that `python -m mypy` misses. Fixed 6 pre-existing type errors in report test files (string literals passed where `IntentCode` is required).
- Audited the Codex task spec (`plans/2026-06-03-codex-deferred-tasks.md`) against the actual migration SQL and found 3 blocking schema errors:
  - `claims.claims`: spec listed `is_negative`/`is_unknown`/`needs_review` (not in DB); omitted `rule_execution_run_id` and `intent_id` (are in DB).
  - `claims.claim_evidence`: spec had `evidence_order int` (not in DB); actual column is `support_role text`.
  - `claims.verification_tasks`: spec showed 3-column stub; actual table has 12 columns.
- Added `severity_band_enum` to `backend/app/db/types.py` (pre-completes the structural prerequisite for C-001 ORM models; all 4 canonical DB ENUMs are now in `db/types.py`).
- Corrected C-002 design: the `evidence_ids` non-empty invariant blocks naive not-evaluated claims; updated spec to use sentinel source failure evidence approach (creates SOURCE_FAILURE evidence records for each missing domain, then the rule engine emits UNKNOWN claims from them — preserves evidence-before-claim invariant).
- Corrected D-001 design: removed `build_engine()`-per-request anti-pattern (destroys connection pooling); delegated to existing `get_session()` singleton from `engine.py`. Added `main.py` to required change list.
- Made C-002 severity choice definitive: not-evaluated claims use `SeverityBand.UNKNOWN` (consistent with all other "source not available" claims; ensures they appear in `ReportRunContract.unknowns`).
- Verified: 235 tests pass; `ruff check` clean; global `mypy` clean (83 source files including tests).

## 2026-06-04 (Lane C DB-backed claim persistence)

- Completed Lane C TC-150 by adding `SqlAlchemyClaimRepository` for `claims.claims`, DB-backed claim/evidence links in `claims.claim_evidence`, and verification-task persistence in `claims.verification_tasks`.
- Preserved rule metadata and evidence ordering in `claims.claims.metadata` until a coordinated schema migration promotes those fields.
- Added DB-gated tests for durable claim round-trip, evidence-link rows, verification-task rows, unknown/source-failure claim persistence, duplicate claim rejection, and rollback behavior.
- Added `docs/adr/lane-c-rules.md` to document deterministic rules, claim persistence, evidence links, rule version metadata, verification tasks, hard gates before scoring, and deferred suitability scoring.
- Verified Lane C targeted checks: 130 tests pass with `RUN_DB_SMOKE=1`; targeted ruff and mypy pass; cross-lane import scan returns 0 matches.
- Verified `$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1`: 235 tests; lint clean; mypy clean (81 source files); DB smoke passes.
- Re-audit note: Level 6 remains partial until missing rule categories are implemented or explicitly labeled as not evaluated.

## 2026-06-04 (Lane C evidence geometry/spatial precision + automation guardrails)

- Removed the remaining live automatic-execution reference from `CLAUDE.md`; active automation sweeps now return 0 matches, the Claude/Codex automatic config paths are absent, and `local_artifacts/psql.cmd` remains present.
- Updated `AGENTS.md` and repo-local Claude debug/validation skills so Windows verification points to PowerShell wrappers instead of `.sh` commands.
- Completed Lane C TC-140 by adding optional GeoJSON/SRID/spatial precision fields to `EvidenceContract`, mapping geometry to `evidence.observations.geometry`, and preserving spatial precision in evidence metadata.
- Added `docs/adr/lane-c-evidence.md` to document evidence persistence, immutability, supersession/amendment, audit events, geometry mapping, and source-failure treatment.
- Verified Lane C targeted checks: 126 tests pass with `RUN_DB_SMOKE=1`; targeted ruff and mypy pass; cross-lane import scan returns 0 matches.
- Verified `$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1`: 231 tests; lint clean; mypy clean (80 source files); DB smoke passes.
- Re-audit note: Level 5 now passes for the fixture-backed DB evidence-ledger path; next dependency is Level 6 durable claim/claim-evidence persistence.

## 2026-06-04 (Lane C DB-backed evidence repository and audit log)

- Completed Lane C TC-130 by adding `SqlAlchemyEvidenceRepository` for `evidence.observations` and `SqlAlchemyEvidenceAuditLog` for evidence events in `audit.events`.
- Preserved contract-only evidence fields in observation metadata: `source_id`, `evidence_code`, `observed_at`, and `superseded_by`.
- Added DB-gated tests for source observation, source failure, spatial intersection, derived metric, document extract, human verification, invalid payload rejection, supersession, retrieval by area/source/type, rollback behavior, and durable audit events.
- Verified Lane C targeted checks: 122 tests pass with `RUN_DB_SMOKE=1`; targeted ruff and mypy pass; cross-lane import scan returns 0 matches.
- Verified `$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1`: 227 tests collected; lint clean; mypy clean (80 source files); DB smoke passes.
- Re-audit note: Level 5 remains partial until `EvidenceContract` exposes geometry/SRID/spatial-precision fields and maps them into `evidence.observations.geometry`.

## 2026-06-04 (Lane B supported domain area-type mapping)

- Completed Lane B TB-090 by preserving exact domain area type in `core.areas.metadata.domain_area_type`.
- Mapped `multi_polygon` to DB bucket `polygon` and `buffer` to DB bucket `generated_candidate`, while keeping reads fail-closed if metadata conflicts with stored DB area type.
- Added DB-gated tests for all six Level 4 domain area types and conflicting metadata rejection.
- Verified Lane B targeted checks: 46 tests pass with `RUN_DB_SMOKE=1`; `ruff check app/area_geometry app/domain/area_contracts.py tests/area_geometry` passes; `mypy app/area_geometry app/domain/area_contracts.py tests/area_geometry` passes.
- Verified `$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1`: 216 tests collected; lint clean; mypy clean (78 source files); DB smoke passes.
- Re-audit note: Level 4 now passes for the current fixture-backed DB repository path; next dependency is Lane C durable evidence-ledger/audit persistence.

## 2026-06-04 (Lane B DB-backed area versioning)

- Completed Lane B TB-080 for the current repository path by adding `AreaVersionContract`, `AreaVersionModel`, `SqlAlchemyAreaRepository.replace_geometry`, and `SqlAlchemyAreaRepository.list_versions`.
- Added DB-gated tests for immutable prior-geometry storage in `core.area_versions`, version number sequencing, missing-area no-op behavior, invalid replacement rejection, and rollback behavior.
- Verified Lane B targeted checks: 41 tests pass with `RUN_DB_SMOKE=1`; `ruff check app/area_geometry app/domain/area_contracts.py tests/area_geometry` passes; `mypy app/area_geometry app/domain/area_contracts.py tests/area_geometry` passes.
- Verified `$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1`: 211 tests collected; lint clean; mypy clean (78 source files); DB smoke passes.
- Re-audit note: superseded by TB-090, which resolves the `multi_polygon`/`buffer` domain-to-DB area-type alignment for the current repository path.

## 2026-06-04 (Lane B DB-backed spatial relation helper)

- Completed Lane B TB-070 by adding `AreaSpatialRelationContract` and `SqlAlchemyAreaRepository.get_spatial_relation`.
- Added DB-gated tests for contained, disjoint, missing-area, wrong-SRID, empty-geometry, and unsupported-geometry-type comparison behavior.
- Verified Lane B targeted checks: 35 tests pass with `RUN_DB_SMOKE=1`; `ruff check app/area_geometry app/domain/area_contracts.py tests/area_geometry` passes; `mypy app/area_geometry app/domain/area_contracts.py tests/area_geometry` passes.
- Verified `$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1`: 205 tests collected; lint clean; mypy clean (78 source files); DB smoke passes.

## 2026-06-04 (Lane B DB-backed area metrics)

- Completed Lane B TB-060 by adding `AreaMetricsContract` and `SqlAlchemyAreaRepository.get_metrics`.
- Added DB-gated tests for PostGIS-derived geodesic area, centroid, bbox, SRID, and measurement caveats for Polygon and MultiPolygon fixtures.
- Verified Lane B targeted checks: 27 tests pass with `RUN_DB_SMOKE=1`; `ruff check app/area_geometry app/domain/area_contracts.py tests/area_geometry` passes; `mypy app/area_geometry app/domain/area_contracts.py tests/area_geometry` passes.
- Verified `$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1`: 197 tests collected; lint clean; mypy clean (78 source files); DB smoke passes.

## 2026-06-04 (Lane B DB-backed area repository)

- Completed Lane B TB-050 by adding `AreaModel` for `core.areas` and `SqlAlchemyAreaRepository` for PostGIS-backed area persistence.
- Added DB-gated tests for Polygon and MultiPolygon round-trips, service integration, existence/list behavior, SRID 4326 persistence, source/confidence/validated field round-trips, and fail-closed domain/DB area-type mismatches.
- Verified Lane B targeted checks: 22 tests pass with `RUN_DB_SMOKE=1`; `ruff check app/area_geometry tests/area_geometry` passes; `mypy app/area_geometry tests/area_geometry` passes.
- Verified `$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1`: 192 tests collected; lint clean; mypy clean (78 source files); DB smoke passes.

## 2026-06-04 (source governance and DB verification hardening)

- Hardened `SourceService.source_production_use_allowed` so production evidence requires reviewed license, commercial, redistribution, cache, export, raw-data, and AI-use rights.
- Added regression tests for blocked/unknown source usage-right dimensions and updated report/provenance fixtures to model fully reviewed sources.
- Strengthened `db_smoke_check.py` from schema/source-count checks to schema, table, column, enum, foreign-key, source seed, and intent seed assertions.
- Added a PostGIS-backed GitHub Actions `db-verify` job and Python 3.12 selection/version checks for verification scripts.
- Corrected Windows DB-smoke command snippets and demoted Lane D state wording to a partial report-run harness rather than full Level 7 PASS.
- Verified `$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1`: Python 3.12.10 selected; 186 tests pass; ruff clean; mypy clean; migrations/seeds and stronger DB smoke pass.

## 2026-06-04 (Session 2 D-001 DB-backed API workflow)

- Completed Lane D D-001 from clean root `main` without touching Session 1's Lane A or Lane B worktrees.
- Added explicit DB API mode through `create_app(use_db_services=True)`, preserving default in-memory API services for fast fixture tests.
- Wired request-scoped SQLAlchemy-backed source, area, evidence, claim, and report services in `backend/app/api/dependencies.py`; successful DB requests commit and failed requests roll back.
- Added DB-backed API integration coverage for `POST /areas`, `POST /report-runs`, `GET /report-runs/{id}`, persisted `reports.report_runs` row, non-null seeded `intent_id`, unsupported-category UNKNOWN claims, and report artifact path.
- Hardened Lane D's internal unsupported-category sentinel lookup to use a stable source UUID instead of scanning all source rows. This avoids coupling report generation to Lane A source-row URL normalization while keeping the change inside Lane D-owned report code.
- Verified targeted Lane D/API checks with DB smoke enabled before full workspace verification.

## 2026-06-04 (Session 2 D-002 report artifact regression)

- Created `plans/2026-06-04-l7-closeout-l8-entry.md` to sequence Level 7 closeout and Level 8 entry without prematurely editing shared schemas or Lane A/B/C implementation files.
- Added `backend/tests/reports/test_report_regression.py`, a normalized fixture report regression that asserts stable generated report semantics while ignoring dynamic UUID, timestamp, and path fields.
- Kept Session 2 work away from Session 1's active Lane B coordinate-validation branch and away from Lane A/C implementation surfaces.
- Set the next Session 2 task to a schema-contract alignment note before any `schemas/*.json` changes or Level 8 connector implementation.

## 2026-06-04 (Session 2 D-003 schema-contract alignment)

- Audited active shared schemas against current source, evidence, claim, and report domain contracts without editing schema files.
- Recorded schema gaps and future lane owners in `plans/2026-06-04-l7-closeout-l8-entry.md`.
- Identified that `schemas/evidence_schema.json` still reflects older geometry/timestamp fields, `schemas/claim_schema.json` requires fields not in the current claim contract and omits ruleset metadata, and no active report-run schema exists yet.
- Preserved shared-schema ownership boundaries: Lane A for source schema, Lane C for evidence/claim schemas, Lane D for report schema proposal, and coordinator review for cross-lane composition.
- Set the next task to Level 8 ownership and fixture-only connector acceptance planning before connector runtime code.

## 2026-06-04 (Session 2 CON-019 connector source-failure IDs)

- Adopted Lane C TC-180 source-failure ID preservation from the connector side by passing deterministic source-failure `EvidenceContract.evidence_id` values into the public `create_source_failure(...)` method.
- Adjusted connector source-failure idempotency to check existing stored source-failure fingerprints before deterministic-ID duplicate fallback, preserving stored authority for repeated fixture runs.
- Updated connector/API fake evidence ports and DB-backed public wiring assertions so supplied source-failure IDs are preserved in tests.
- Added `docs/adr/lane-d-0008-connector-source-failure-ids.md`.
- Merged root `main` at `ca10f85` into the Session 2 integration branch, preserving Lane A TA-070 source schema-contract records and resolving only append-style shared state conflicts.
- Verification passed after reconciliation: focused connector adoption tests, DB-backed public wiring source-failure ID test, targeted/broader connector/API ruff and mypy, connector/API tests, full DB-enabled PowerShell verification with 335 backend tests, lint clean, mypy clean over 119 source files, migrations/seeds apply, and DB smoke passes.
- Preserved boundaries: no Lane C implementation/schema edits, no database migration, no live I/O, no queue API mutation, no claims/reports shortcut, and no durable `ingest_run_id` evidence-row linkage.

## 2026-06-04 (Session 2 CON-020 connector fixture quality)

- Extended `evaluate_flood_fixture_quality(...)` with fixture-local identity and timing checks.
- Added blocking quality issues for duplicate evidence IDs within one fixture connector run.
- Added blocking quality issues for evidence `observed_at` timestamps before retrieval start or after retrieval finish.
- Added focused fixture-quality tests for the new issue categories.
- Preserved boundaries: no Lane A/B/C implementation changes, no shared schema edits, no API mutation route, no persistence change, no live I/O, no claims/reports shortcut, and no durable `ingest_run_id` evidence-row linkage.

## 2026-06-03 (Windows PowerShell verification wrapper)

- Added PowerShell-native wrappers for verification, workspace validation, DB migration application, and bootstrap so Windows users can avoid launching Git Bash.
- Updated README, AGENTS, testing docs, prompt template, and current state blocks to point Windows usage at `.\scripts\verify.ps1`.
- Verified `.\scripts\verify.ps1` with `RUN_DB_SMOKE=1`: 179 tests pass; ruff clean; mypy clean (76 source files); DB smoke passes through the local `psql` shim.

## 2026-06-03 (Lane D persisted report runs)

- Completed Lane D TD-040 by adding the `reports.report_runs` ORM model, the SQLAlchemy report-run repository, a machine-readable artifact round-trip, and a DB-backed persistence test.
- `verify.sh` now passes with DB smoke enabled: 173 tests pass; ruff clean; mypy clean (72 source files).
- Updated Lane D plan/state/validation docs and recorded the persistence decision in `docs/adr/lane-d-0001-report-persistence.md`.

## 2026-06-03 (scaffold validation alignment)

- Added `.gitignore` entry for the nested `001-audit/` audit worktree so root status no longer presents it as a candidate repo artifact.
- Added minimal scaffold tests for Lane B area contract defaults, Lane D report contract defaults, and API health scaffold.
- Corrected Lane B and Lane D state evidence so documented lane-specific verification commands now match runnable tests.
- `verify.sh` passes via Git Bash: 22 tests pass; ruff clean; mypy clean (44 source files); DB smoke skipped.
- Anchored local `main` to `origin/main` and created local baseline commit `ffb73e1` (`Establish governed scaffold baseline`); no push performed.
- Completed Lane A TA-010 by archiving backward-compat shims from `backend/app/repositories/` and `backend/app/services/` into `archive/2026-06-03_source-registry-lane-migration/backend/app/`.
- `verify.sh` passes after TA-010: 22 tests pass; ruff clean; mypy clean (40 active source files); DB smoke skipped.
- Completed Lane A TA-020 by adding `SourceModel` for `source.sources` plus model contract tests. `verify.sh` passes: 26 tests pass; ruff clean; mypy clean (42 source files); DB smoke skipped.
- Completed Lane A TA-030 by adding `SqlAlchemySourceRepository` plus non-DB repository tests. `verify.sh` passes: 30 tests pass; ruff clean; mypy clean (43 source files); DB smoke skipped.
- Completed Lane A TA-040 by adding registry-backed source seed loading, a seed runner, seed tests, and metadata persistence mapping. Lane A tests pass: 23 tests; seed dry-run validates 8 `Must` rows.
- Completed Lane B TB-010 through TB-040 for the in-memory fixture slice: AreaService, InMemoryAreaRepository, GeoJSON/SRID validator, geometry fixtures, and service/validator tests. Lane B tests pass: 16 tests.
- `verify.sh` passes via Git Bash after TA-040 and Lane B fixture slice: 49 tests pass; ruff clean; mypy clean (48 source files); DB smoke skipped.
- Completed Lane C TC-010 for the in-memory evidence slice: EvidenceService, InMemoryEvidenceRepository, source/area protocol validation, source-failure evidence, typed human notes, area/source/type retrieval, and duplicate evidence protection. Lane C tests pass: 16 tests.
- `verify.sh` passes via Git Bash after TC-010: 59 tests pass; ruff clean; mypy clean (51 source files); DB smoke skipped.
- Completed Lane A TA-050 by adding the source provenance/license ADR, strengthening the canonical data-source license review template, wiring explicit governance fields through the source register/schema/seed path, and adding fail-closed SourceService production-use checks. Lane A tests pass: 28 tests.
- `verify.sh` passes via Git Bash after TA-050: 64 collected tests; ruff clean; mypy clean (51 source files); DB smoke skipped.
- Completed Lane C TC-020 for the in-memory evidence slice: `superseded_by`, repository supersession marking, and service safeguards for same-area replacement, new evidence IDs, already-superseded originals, pre-superseded new records, and source-failure replacement. Lane C tests pass: 23 tests.
- `verify.sh` passes via Git Bash after TC-020: 71 collected tests; ruff clean; mypy clean (51 source files); DB smoke skipped.
- Completed Lane C TC-030 for the in-memory claim-service slice: `ClaimRepository`, `InMemoryClaimRepository`, and `ClaimService` with stored evidence-link validation, same-area enforcement, unknown claim generation from source-failure evidence, user-safe-language enforcement, and verification-task enforcement. Lane C tests pass: 35 tests.
- `verify.sh` passes via Git Bash after TC-030: 83 tests pass; ruff clean; mypy clean (54 source files); DB smoke skipped.
- Completed Lane C TC-040 for the first deterministic rule-engine slice: rule metadata on claims, constrained current-ruleset loading, deterministic flood hard-gate claims, source-failure unknown claims, low-risk no-claim output, empty input, multi-area grouping, simultaneous positive/failure output, input-order determinism, invalid severity rejection, and superseded-evidence exclusion. Lane C tests pass: 45 tests.
- `verify.sh` passes via Git Bash after TC-040: 93 tests pass; ruff clean; mypy clean (56 source files); DB smoke skipped.
- Completed Lane C TC-050 for the in-memory evidence payload-validation slice: type-specific `observed_value` validation for source observations, spatial intersections, derived metrics, document extracts, source failures, and human-note guardrails. Spatial validation accepts `flood_zone_code` results and bounds `intersection_ratio` to `0..1`. Lane C tests pass: 59 tests.
- `verify.sh` passes via Git Bash after TC-050: 107 tests pass; ruff clean; mypy clean (59 source files); DB smoke skipped.
- Completed Lane C TC-060 for the in-memory evidence audit-event slice: optional `EvidenceAuditLog` injection, `EvidenceAuditEvent`, `InMemoryEvidenceAuditLog`, and create/source-failure/human-note/supersede event tests. Lane C tests pass: 63 tests.
- `verify.sh` passes via Git Bash after TC-060: 111 tests pass; ruff clean; mypy clean (60 source files); DB smoke skipped.
- Completed Lane C TC-070 for the in-memory flood contradiction/stale rule slice: deterministic needs-review claims for conflicting active evidence and positive-plus-source-failure evidence, explicit `source_stale` fixture handling, superseded-evidence exclusion, and deterministic review-output ordering. Lane C tests pass: 69 tests.
- `verify.sh` passes via Git Bash after TC-070: 117 tests pass; ruff clean; mypy clean (60 source files); DB smoke skipped.
- Completed Lane D TD-020 for the in-memory API scaffold: per-app in-memory service wiring, source/area/evidence/report-run routers, router registration, and API tests for happy paths and representative 422 cases. Lane D tests pass: 7 tests.
- `verify.sh` passes via Git Bash after TD-020: 122 tests pass; ruff clean; mypy clean (65 source files); DB smoke skipped.
- Completed Lane D TD-030 for the in-memory report-run service: ReportRunService validates registered areas, gathers area evidence, runs the deterministic rule engine, stores evidence-linked claims through ClaimService, and returns report evidence, claims, unknowns, red flags, caveats, verification tasks, source manifest, and artifact metadata. Lane D tests pass: 11 tests.
- `verify.sh` passes via explicit Git Bash after TD-030: 126 tests pass; ruff clean; mypy clean (67 source files); DB smoke skipped. Docker Desktop Linux engine remains unavailable for DB smoke.
- Completed Lane C TC-080 for the access hard-gate fixture slice: deterministic `ACCESS_001`, access source-unavailable unknown, access needs-review, stale access review, safe legal-access language, and access adjacency payload validation. Lane C tests pass: 76 tests.
- `verify.sh` passes via explicit Git Bash after TC-080: 131 tests pass; ruff clean; mypy clean (67 source files); DB smoke skipped. Docker Desktop Linux engine remains unavailable for DB smoke.
- Completed Lane C TC-090 for the wetlands hard-gate fixture slice: deterministic `WETLAND_001`, wetland source-unavailable unknown, wetland needs-review, stale wetland review, screening-only/no-delineation language, and wetland fixture payload validation. Lane C tests pass: 83 tests.
- `verify.sh` passes via explicit Git Bash after TC-090: 138 tests pass; ruff clean; mypy clean (67 source files); DB smoke skipped. Docker Desktop Linux engine remains unavailable for DB smoke.
- Completed Lane C TC-100 for the slope/buildability hard-gate fixture slice: deterministic `SLOPE_001`, slope source-unavailable unknown, slope needs-review, stale slope review, screening-only/no-final-buildability language, and slope derived-metric payload validation. Lane C tests pass: 90 tests.
- `verify.sh` passes via explicit Git Bash after TC-100: 145 tests pass; ruff clean; mypy clean (67 source files); DB smoke skipped. Docker Desktop Linux engine remains unavailable for DB smoke.
- Completed Lane C TC-110 for the zoning/use hard-gate fixture slice: deterministic `ZONING_001`, zoning source-unavailable unknown, zoning needs-review for incomplete/mixed evidence, stale zoning review, screening-only/no-final-legal-use language, and zoning source-observation payload validation. Lane C tests pass: 100 tests.
- `verify.sh` passes via explicit Git Bash after TC-110: 157 tests pass; ruff clean; mypy clean (67 source files); DB smoke skipped. Docker Desktop Linux engine remains unavailable for DB smoke.
- Completed Lane C TC-120 for the water-context hard-gate fixture slice: deterministic `WATER_001`, water source-unavailable unknown, water needs-review for incomplete/mixed evidence including internally contradictory fixture records, stale water review, screening-only/no-water-rights/no-well-viability language, and water source-observation payload validation. Lane C tests pass: 111 tests.
- `verify.sh` passes via explicit Git Bash after TC-120: 168 tests pass; ruff clean; mypy clean (67 source files); DB smoke skipped. Docker Desktop Linux engine remains unavailable for DB smoke.
- Completed Lane D TD-050 for the in-memory protocol adapter wiring: added `SourceServiceProtocolAdapter` and `AreaServiceProtocolAdapter`, wired them into `EvidenceService` construction in the report pipeline, and added adapter-focused delegation/guardrail tests. Lane D tests pass: 15 tests.
- `verify.sh` passes via explicit Git Bash after TD-050: 172 tests pass; ruff clean; mypy clean (69 source files); DB smoke skipped. Docker Desktop Linux engine remains unavailable for DB smoke.

## 2026-06-03 (repo bootstrap + local index)

- Ran `npx codesight --index`; local index written to `.codesight/`.
- Created `plans/2026-06-03-repo-bootstrap.md` for local-only GitHub bootstrap work.
- Aligned README and `manifest.json` with target repo `benjmcd/land-dd`.
- Corrected `tasks/task_queue.yaml` against canonical state: T010 blocked on Docker, T020 done, lane plans listed for implementation routing.
- Initialized local Git on `main` and set `origin` to `https://github.com/benjmcd/land-dd.git`; no commit or push performed.
- `verify.sh` passes via Git Bash: 19 tests pass; ruff clean; mypy clean (40 source files); DB smoke skipped.
- Added `.codesight/` to `.gitignore` and `MANIFEST.md` generated-artifact policy.
- Added `PROMPT_FOR_ISOLATED_LANE_AGENT.md` for parallel lane agents, with local-only, no-shared-checkout, lane-ownership, and stop-condition rules.
- Strengthened isolated-lane prompt with no-baseline-commit isolation guidance, Windows/Git Bash command notes, test-first work protocol, tech-debt controls, shared-log conflict handling, and stricter definition of done.

## 2026-06-03 (session 3 — lane scaffold)

- Installed `psycopg[binary]`, `pytest-cov`, `types-PyYAML` (from pyproject.toml dev deps).
- Fixed `engine.py` to use deferred/lazy initialization (prevents module-import DB connection).
- Split `backend/app/domain/contracts.py` into per-lane contract files:
  - `source_contracts.py` (Lane A), `area_contracts.py` (Lane B),
    `evidence_contracts.py` (Lane C), `claim_contracts.py` (Lane C), `report_contracts.py` (Lane D)
- Added `protocols.py` (shared: SourceExistsProtocol, AreaExistsProtocol).
- Extended `enums.py`: added EvidenceType, AreaType, JobStatus.
- Migrated source_repo + source_service into `backend/app/source_registry/`.
  Old `repositories/` and `services/` are now backward-compat shims (Lane A archives to `archive/` once no imports remain).
- Split `test_domain_contracts.py` and `test_source_service.py` into per-lane test directories.
- Created lane module directories: source_registry/, area_geometry/, evidence_ledger/, claims_engine/, reports/.
- Created lane test directories: tests/source_registry/, tests/area_geometry/, tests/evidence_ledger/, tests/claims_engine/, tests/reports/.
- Created per-lane operating contracts: lanes/lane-{a,b,c,d}/AGENTS.md + CLAUDE.md.
- Created per-lane plans: plans/lane-{a,b,c,d}-2026-06-03-*.md.
- Created per-lane state files: state/lane-{a,b,c,d}-state.md.
- Created LANE_OWNERSHIP.md (canonical isolation map).
- Created db/migrations/MIGRATION_REGISTRY.md.
- Updated MANIFEST.md, state/PROJECT_STATE.md (MILESTONE_MAP status block added).
- verify.sh: 19 tests pass; lint clean; mypy clean (40 source files).

## 2026-06-03 (session 2)

- Fixed 3 baseline lint errors (`config.py` E501, `contracts.py` UP017/UP037).
- Installed mypy in Python 3.11 environment; `verify.sh` typecheck step now executes.
- T010 (DB smoke) blocked: Docker Desktop not running. Recorded blocker in VALIDATION_LOG.
- T020 completed: added source registry repository/service layer.
  - `backend/app/repositories/source_repo.py`: `SourceRepository` Protocol + `InMemorySourceRepository`.
  - `backend/app/services/source_service.py`: `SourceService` with dedup enforcement.
  - `backend/tests/test_source_service.py`: 8 fixture-backed tests, all passing.
- `verify.sh` passes: 14 tests, lint clean, mypy clean.

## 2026-06-03 (initial)

- Created dual-agent workspace structure for Codex and Claude Code.
- Added thin `AGENTS.md`, `CLAUDE.md` importer, `MANIFEST.md`, plans, skills, subagents, CI, and validation scripts.
- Preserved comprehensive planning pack under `docs/planning_pack/` as reference, not startup context.
