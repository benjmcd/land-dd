# Project State

## MILESTONE_MAP status block

```text
Current milestone: Level 7 - Reproducible Report Vertical Slice
Milestone status: PASS for fixture-backed report/API workflow
Last verified: 2026-06-04
Verification command(s):
- cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/evidence_ledger
- cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/evidence_ledger tests/claims_engine
- cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/claims_engine
- cd backend; py -3.12 -m pytest -q tests/reports tests/api
- cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/api tests/reports
- cd backend; py -3.12 -m pytest -q tests/reports/test_report_regression.py
- cd backend; ruff check app/api app/main.py app/reports tests/api tests/reports
- cd backend; mypy app/reports app/api tests/reports tests/api
- cd backend; ruff check app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
- cd backend; ruff check app/claims_engine tests/claims_engine
- cd backend; mypy app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
- cd backend; mypy app/claims_engine tests/claims_engine
- cd backend; py -3.12 -m pytest -q tests/connectors/test_fixture_quality.py
- cd backend; ruff check app/connectors/fixture_quality.py tests/connectors/test_fixture_quality.py
- cd backend; mypy app/connectors/fixture_quality.py tests/connectors/test_fixture_quality.py
- cd backend; py -3.12 -m pytest -q tests/connectors/test_review_status.py tests/api/test_connector_review_status.py
- cd backend; py -3.12 -m pytest -q tests/connectors/test_review_queue.py
- cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/connectors/test_review_queue.py
- cd backend; py -3.12 -m pytest -q tests/api/test_connector_review_status.py tests/api/test_connector_review_queue_db.py
- cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/api/test_connector_review_queue_db.py
- cd backend; py -3.12 -m pytest -q tests/connectors
- cd backend; py -3.12 -m pytest -q tests/connectors tests/api -rA
- cd backend; ruff check app/connectors tests/connectors
- cd backend; ruff check app/connectors app/api app/main.py tests/connectors tests/api
- cd backend; mypy app/connectors tests/connectors
- cd backend; mypy app/connectors app/api app/main.py tests/connectors tests/api
- cd backend; rg -n "from app\.source_registry|from app\.area_geometry|import app\.source_registry|import app\.area_geometry" app/evidence_ledger app/claims_engine
- cd backend; py -3.12 -m pytest --collect-only -q
- python scripts/db_smoke_check.py
- cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/area_geometry
- cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/evidence_ledger tests/claims_engine
- cd backend; py -3.12 -m pytest -q tests/test_planning_pack_schema_copies.py
- cd backend; ruff check tests/test_planning_pack_schema_copies.py
- cd backend; mypy tests/test_planning_pack_schema_copies.py
- .\scripts\verify.ps1
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
- 362 tests pass in the DB-enabled Windows PowerShell verification path after TD-083 report validation metadata; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes.
- 363 tests pass in the DB-enabled Windows PowerShell verification path after CON-027 connector fixture retrieval metric quality; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes.
- 363 tests pass in the DB-enabled Windows PowerShell verification path after TD-084 job-schema boundary; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes.
- 364 tests pass in the DB-enabled Windows PowerShell verification path after CON-028 connector source-failure payload type quality; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes.
- 365 tests pass in the DB-enabled Windows PowerShell verification path after CON-029 connector source-failure reason consistency; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes.
- 365 tests pass in the DB-enabled Windows PowerShell verification path after CON-030 connector retrieval failure-reason metric quality; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes.
- 365 tests pass in the DB-enabled Windows PowerShell verification path after CON-031 connector succeeded-retrieval failure-metric quality; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes.
- 366 tests pass in the DB-enabled Windows PowerShell verification path after CON-032 connector fixture evidence domain quality; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes.
- 367 tests pass in the DB-enabled Windows PowerShell verification path after CON-033 connector fixture retrieval name quality; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes.
- 368 tests pass in the DB-enabled Windows PowerShell verification path after CON-034 connector fixture evidence source consistency; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes.
- 369 tests pass in the DB-enabled Windows PowerShell verification path after CON-035 connector fixture evidence area consistency; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes.
- 350 tests pass in the DB-enabled Windows PowerShell verification path after TA-080 source provenance-family schema parity; lint clean; mypy clean (121 source files); migrations/seeds apply; DB smoke passes.
- 343 tests pass in the DB-enabled Windows PowerShell verification path after TD-081 report manifest metadata schema tightening; lint clean; mypy clean (120 source files); migrations/seeds apply; DB smoke passes.
- 344 tests pass in the DB-enabled Windows PowerShell verification path after rebasing TD-090 planning-pack OpenAPI refresh onto TD-081 report manifest metadata schema tightening; lint clean; mypy clean (120 source files); migrations/seeds apply; DB smoke passes.
- 331 tests pass in the DB-enabled Windows PowerShell verification path after combined Lane C TC-180 plus CON-017/CON-018 integration rehearsal; lint clean; mypy clean (118 source files); migrations/seeds apply; DB smoke passes.
- 330 tests pass in the DB-enabled Windows PowerShell verification path after aligning the Lane A source schema with serialized `SourceContract`; lint clean; mypy clean (119 source files); migrations/seeds apply; DB smoke passes.
- 335 tests pass in the DB-enabled Windows PowerShell verification path after merging Lane A TA-070 and CON-019 connector source-failure ID adoption into the Session 2 integration branch; lint clean; mypy clean (119 source files); migrations/seeds apply; DB smoke passes.
- 337 tests pass in the DB-enabled Windows PowerShell verification path after CON-020 connector fixture identity/timing quality; lint clean; mypy clean (119 source files); migrations/seeds apply; DB smoke passes.
- 339 tests pass in the DB-enabled Windows PowerShell verification path after adding the Lane D report-run schema contract; lint clean; mypy clean (120 source files); migrations/seeds apply; DB smoke passes.
- 341 tests pass in the DB-enabled Windows PowerShell verification path after merging CON-020 connector fixture quality with Lane D TD-080 report-run schema; lint clean; mypy clean (120 source files); migrations/seeds apply; DB smoke passes.
- 342 tests pass in the DB-enabled Windows PowerShell verification path after TD-090 planning-pack OpenAPI refresh; lint clean; mypy clean (120 source files); migrations/seeds apply; DB smoke passes.
- Local Postgres/PostGIS migrations and seeds apply cleanly, and DB smoke validates required schemas, tables, columns, enums, foreign keys, and seeds
- Source versioning, retrieval lifecycle, caveats, freshness, authority, and license/review/usage-right metadata are implemented and surfaced downstream; canonical `schemas/source_schema.json` is aligned to serialized `SourceContract` with parity tests
- Lane B area/geometry slice now includes a SQLAlchemy/PostGIS `core.areas` repository that round-trips Polygon/MultiPolygon GeoJSON as SRID 4326 MultiPolygon geometry, supports all six Level 4 domain area types with explicit metadata-preserved domain type mapping, preserves source/confidence/validated fields, reads PostGIS-derived area/centroid/bbox metrics, queries fixture spatial relations through PostGIS, stores immutable prior-geometry rows in `core.area_versions` on geometry replacement, and rejects non-finite or out-of-range EPSG:4326 lon/lat positions
- Lane C evidence/claim/rule-engine/schema slices pass targeted runtime, type, lint, schema-contract, and import-isolation checks; the evidence ledger now has a SQLAlchemy/Postgres repository for `evidence.observations`, durable evidence audit events in `audit.events`, first-class optional evidence geometry mapped to `evidence.observations.geometry`, spatial precision preserved in evidence metadata, DB-backed claim/evidence/verification-task persistence, source-failure evidence ID preservation through the public Lane C service, evidence-backed not-evaluated UNKNOWN claims for unsupported soil/septic, environmental hazard, resource-context, and market-context categories, and canonical evidence/claim JSON schemas aligned to serialized domain contracts
- Lane D report runs now persist through `reports.report_runs` and a machine-readable JSON artifact under `OBJECT_STORE_ROOT`; report/API output now surfaces stored not-evaluated unsupported-category source failures as UNKNOWN claims
- Lane D API DB mode now wires SQLAlchemy-backed source, area, evidence, claim, and report repositories through request-scoped services; `POST /areas`, `POST /report-runs`, and `GET /report-runs/{id}` are covered by a DB-backed integration test
- Lane D report artifact semantics are now pinned by a normalized regression test that ignores dynamic UUID/timestamp/path fields while asserting source manifest, evidence, claims, unknowns, red flags, caveats, and artifact metadata
- Shared schema gaps for job schema remain recorded with future lane ownership in `plans/2026-06-04-l7-closeout-l8-entry.md`; Lane A source and source provenance-family schemas, Lane C evidence/claim root schemas, Lane D report-run schema plus stable generated report manifest metadata keys and report metadata extension boundaries, planning-pack evidence/claim schema copies, and planning-pack OpenAPI are now aligned to their serialized/generated contract authorities
- Level 8 connector gates L8-001 through L8-010 are mapped to lane owners, and the first fixture-only connector runtime contract slice is implemented as a static local flood fixture with no live network, explicit idempotency, blocked/source-failure behavior, and source retrieval provenance
- D-005 is complete: `LANE_OWNERSHIP.md` assigns a coordinator-owned connector integration zone, `docs/adr/lane-d-0002-connector-entry-ownership.md` is accepted, source retrieval runs are connector lifecycle/provenance authority, and jobs remain future async orchestration
- CON-001 is complete: `StaticFloodFixtureConnector` reads local flood fixture JSON, rejects URI-like paths, emits `SourceRetrievalRunContract` plus `EvidenceContract` inputs, covers success/failure source-failure fixtures, and stays before claims/reports
- CON-002 is complete: connector evidence-ingestion handoff is defined; the connector-zone adapter must use injected public Lane C EvidenceService methods, direct Lane C repository/private-helper access is rejected, and durable retrieval-run/evidence linkage gaps are recorded for future coordination
- CON-003 is complete: `ConnectorEvidenceIngestionAdapter` uses an injected public evidence-ingestion port, routes normal evidence to `create_observation`, routes source failures to `create_source_failure`, skips duplicate deterministic evidence IDs, fingerprints source failures for repeated fixture idempotency, and stays before claims/reports
- CON-004 is complete: `ConnectorRetrievalProvenanceAdapter` uses an injected source retrieval provenance port, preserves connector-supplied retrieval-run identity, skips duplicate `ingest_run_id` values, and records the Lane A concrete wiring gap without importing Lane A repositories/services
- CON-005 is complete: `FixtureConnectorIngestWorkflow` composes the fixture connector, retrieval provenance adapter, and evidence ingestion adapter so retrieval provenance is recorded before evidence ingestion, repeated fixture workflow runs are idempotent, and the workflow remains fixture-only/injected-port based before claims/reports
- CON-006 is complete: connector-owned public-service wiring now composes the fixture workflow with public Lane C `EvidenceService` methods while preserving the Lane A retrieval-run identity requirement behind an explicit provenance port; flood source-failure fixture payloads are aligned to Lane C validation
- CON-007 is complete: Lane A public provenance service now records supplied `SourceRetrievalRunContract` values while preserving `ingest_run_id`, and connector public wiring can use that service without Lane A repository imports
- CON-008 is complete: the fixture success workflow now runs against DB-backed public Lane A provenance and public Lane C evidence services, records the supplied retrieval-run identity, persists evidence through public evidence methods, and skips the existing retrieval/evidence records on a repeated run
- CON-009 is complete: the fixture source-failure workflow now runs against DB-backed public Lane A provenance and public Lane C evidence services, records the supplied blocked retrieval-run identity, persists source-failure evidence through public source-failure methods, and skips the existing retrieval/source-failure fingerprint on a repeated run
- CON-010 is complete: connector run/status review packets now summarize fixture workflow retrieval status, provenance action, evidence counts, source-failure counts, idempotent skips, review signals, and human-review tasks without API, claims, reports, schema edits, live I/O, or persistence changes
- CON-011 is complete: connector review handoffs now consume review packets and classify them into `needs_human_review`, `ready_for_connector_qa`, or `idempotent_noop` records without API, durable queue persistence, claims, reports, schema edits, live I/O, or Lane A/B/C/D implementation changes
- CON-012 is complete: connector fixture quality profiles now flag fixture-local provenance, dataset-version, row-count, spatial evidence, retrieval-status/evidence consistency, and source-failure payload/confidence gaps without API, durable queue persistence, claims, reports, schema edits, live I/O, or Lane A/B/C/D implementation changes
- CON-013 is complete: connector review status now composes handoff and fixture-quality data, and `GET /connector-runs/{ingest_run_id}/review-status` exposes stored in-memory status without durable queue persistence, connector status tables, claims, reports, schema edits, live I/O, or DB-backed connector status
- CON-014 is complete: connector review status can now be persisted as idempotent `connector_review_status` jobs in `jobs.job_queue` with payload references to `source.ingest_runs.ingest_run_id`, preserving source retrieval runs as connector provenance and lifecycle authority
- CON-015 is complete: `GET /connector-runs/{ingest_run_id}/review-queue` retrieves in-memory or DB-backed connector review queue items by `ingest_run_id` without job mutation, worker execution, schema edits, live I/O, claims, reports, or DB-backed evidence linkage
- CON-016 is complete: connector review queue repositories can lease eligible `connector_review_status` jobs, mark running jobs succeeded, and mark running jobs failed without adding a scheduler, API mutation route, retry/requeue policy, live I/O, claims, reports, schema edits, or provenance mutation
- TC-180 is complete for Lane C public service scope: `EvidenceService.create_source_failure(...)` preserves caller-supplied source-failure evidence IDs through in-memory and SQLAlchemy-backed evidence storage while still rejecting duplicate IDs without overwrite; CON-019 completes connector-zone adapter adoption in the Session 2 integration branch
- CON-017 is complete: `GET /connector-runs/{ingest_run_id}/review-queue` exposes queue attempts, lock/start/finish metadata, and last error for in-memory and DB-backed queue rows without adding API-side job mutation, worker execution, retry/requeue policy, live I/O, claims, reports, schema edits, or provenance mutation
- CON-018 is complete: connector review queue repositories can requeue failed `connector_review_status` jobs only when attempts remain and cancel nonfinal jobs with reasons, without adding API-side mutation, automatic retry policy, scheduler, live I/O, claims, reports, schema edits, or provenance mutation
- CON-019 is complete in the Session 2 integration branch: connector evidence ingestion now passes deterministic source-failure evidence IDs into Lane C's public `create_source_failure(...)` method and DB-backed public wiring proves the ID round-trips; no Lane C implementation/schema edits, live I/O, queue mutation/API route, claim/report shortcut, or durable `ingest_run_id` evidence-row linkage was added
- CON-020 is complete: connector fixture quality now flags duplicate evidence IDs and evidence observed outside the retrieval-run time window without adding API mutation routes, persistence, live I/O, shared schema edits, claims, reports, or durable `ingest_run_id` evidence-row linkage
- TD-081 is complete: stable generated report `source_manifest`, `source_details`, `artifact_metadata`, and `cost_metrics` schema keys are constrained with parity tests and ADR `docs/adr/lane-d-0010-report-manifest-metadata.md`, without adding runtime validation, API behavior changes, DB migrations, connector behavior, live I/O, hook config, or POSIX scripts
- TD-090 is complete: the planning-pack OpenAPI reference now matches the live FastAPI-generated OpenAPI contract and the planning-pack API spec separates implemented endpoints from future roadmap endpoints.
- CON-021 is complete as a planning-only human-review action semantics pass. Future connector review actions are named before any API mutation route, worker, scheduler, dashboard, connector runtime change, schema, or migration.
- CON-022 is complete as a planning-only human-review API semantics pass. Future route/reviewer/auth/idempotency semantics are accepted before API mutation implementation or OpenAPI change.
- TA-080 is complete: the separate source provenance-family schema now covers serialized source dataset, dataset-version, and retrieval-run contracts without changing runtime validation, migrations, connector behavior, queue semantics, live I/O, or durable evidence-row linkage.
- CON-023 is complete: connector-local fixture quality now fails closed when evidence provenance text, caveats, or non-failure source dates are missing, without changing APIs, schemas, queues, source/evidence/claim/report behavior, or live I/O.
- TD-082 is complete as a planning-only report metadata extension boundary. Future report metadata extension families and promotion rules are accepted without changing report runtime behavior, APIs, schemas, queues, migrations, or live I/O.
- CON-024 is complete as a connector review action API auth blocker decision. The future review-action mutation route remains blocked until an authenticated reviewer/operator principal dependency or accepted service-account delegation rule is added and tested.
- CON-025 is complete as a local service-account reviewer principal dependency for future connector review mutation routes, without registering a route or changing OpenAPI.
- CON-026 is complete as a connector review action route-subset decision for `request_fixture_fix`, `requeue_after_fix`, and `cancel_review`; route/OpenAPI implementation remains deferred to avoid Session 1's Lane C evidence-linkage/OpenAPI branch.
- TD-083 is complete as a report validation metadata implementation: `artifact_metadata.validation` records report contract/profile and ruleset identity, with schema/regression coverage, without claiming verification-command execution or changing routes, OpenAPI, DB schema, connector runtime, queue behavior, live I/O, hook config, POSIX scripts, or Lane A/B/C modules.
- CON-027 is complete: connector-local fixture quality now fails closed when succeeded retrievals have nonzero errors or missing/mismatched row counts, and when blocked/failed retrievals lack explicit zero row count or positive error count, without changing API/OpenAPI, DB schema, queue behavior, connector runtime, live I/O, hook config, POSIX scripts, durable evidence-row lineage, or lane-owned modules outside connector quality.
- TD-084 is complete as a job-schema boundary decision: `schemas/job_schema.json` remains unedited and is not promoted to a live connector-run/API contract until a future schema/test slice chooses `jobs.job_queue`, `ConnectorReviewQueueItem`, or a new `JobContract` as authority; source retrieval runs remain connector provenance authority.
- CON-028 is complete: connector-local fixture quality now fails closed when source-failure payload values have empty/non-string `failure_reason` or `error_message`, or non-boolean `retryable`, without changing API/OpenAPI, DB schema, queue behavior, connector runtime, live I/O, hook config, POSIX scripts, durable evidence-row lineage, or lane-owned modules outside connector quality.
- CON-029 is complete: connector-local fixture quality now fails closed when source-failure payload `failure_reason` disagrees with retrieval `metrics.failure_reason`, without changing API/OpenAPI, DB schema, queue behavior, connector runtime, live I/O, hook config, POSIX scripts, durable evidence-row lineage, or lane-owned modules outside connector quality.
- CON-030 is complete: connector-local fixture quality now fails closed when blocked/failed retrievals lack non-empty `metrics.failure_reason`, without changing API/OpenAPI, DB schema, queue behavior, connector runtime, live I/O, hook config, POSIX scripts, durable evidence-row lineage, or lane-owned modules outside connector quality.
- CON-031 is complete: connector-local fixture quality now fails closed when succeeded retrievals carry non-empty `metrics.failure_reason`, without changing API/OpenAPI, DB schema, queue behavior, connector runtime, live I/O, hook config, POSIX scripts, durable evidence-row lineage, or lane-owned modules outside connector quality.
- CON-032 is complete: connector-local fixture quality now fails closed when flood fixture evidence has a domain other than `flood`, without changing API/OpenAPI, DB schema, queue behavior, connector runtime, live I/O, hook config, POSIX scripts, durable evidence-row lineage, or lane-owned modules outside connector quality.
- CON-033 is complete: connector-local fixture quality now fails closed when flood fixture retrievals have a connector name other than `fixture_flood_static`, without changing API/OpenAPI, DB schema, queue behavior, connector runtime, live I/O, hook config, POSIX scripts, durable evidence-row lineage, or lane-owned modules outside connector quality.
- CON-034 is complete: connector-local fixture quality now fails closed when one flood fixture retrieval emits evidence with mixed `source_id` values, without changing API/OpenAPI, DB schema, queue behavior, connector runtime, live I/O, hook config, POSIX scripts, durable evidence-row lineage, or lane-owned modules outside connector quality.
- CON-035 is complete: connector-local fixture quality now fails closed when one flood fixture retrieval emits evidence with mixed `area_id` values, without changing API/OpenAPI, DB schema, queue behavior, connector runtime, live I/O, hook config, POSIX scripts, durable evidence-row lineage, or lane-owned modules outside connector quality.
Failed or blocked gates:
- No Level 5 blockers remain in the fixture-backed DB repository path verified on 2026-06-04.
- L5-001 through L5-010: PASS for the DB-backed evidence repository/service scope (source observations, source failures, spatial intersections, derived metrics, document extracts, human verification notes, geometry/SRID/spatial precision, invalid payload rejection, supersession, deterministic retrieval, rollback behavior, durable audit events, and the evidence-ledger persistence ADR are tested or documented)
- L6-001 through L6-010: PASS for Lane C claim/rule scope (claims require evidence links, unknowns require source-failure evidence, severity/confidence stay separate, verification tasks persist, rules are versioned/deterministic, caveats propagate, contradiction/stale/incomplete/source-failure/not-evaluated cases are tested, and rule logic lives in code/config rather than an LLM/UI prompt)
- L7-001 through L7-010: PASS for the fixture-backed report/API vertical slice (persisted report run, source/evidence/rule manifest data, API create/retrieve path, evidence-linked claims, unknown/source-failure surfacing, caveats/verification tasks, repeatable fixture behavior, API contract coverage, artifact metadata, and no live external APIs)
Completion evidence:
- state/VALIDATION_LOG.md
- backend/tests/source_registry/ (48 tests collected)
- backend/tests/area_geometry/ (49 tests)
- backend/app/domain/area_contracts.py (`AreaContract`, `AreaMetricsContract`, `AreaSpatialRelationContract`, `AreaVersionContract`)
- backend/app/area_geometry/models.py (`AreaModel`, `AreaVersionModel`)
- backend/app/area_geometry/area_repo.py (`SqlAlchemyAreaRepository`)
- backend/tests/evidence_ledger/ and backend/tests/claims_engine/ (153 tests)
- backend/app/domain/evidence_contracts.py (`EvidenceContract` with optional GeoJSON/SRID/spatial precision fields)
- backend/app/evidence_ledger/evidence_repo.py (`SqlAlchemyEvidenceRepository`)
- backend/app/evidence_ledger/audit_log.py (`SqlAlchemyEvidenceAuditLog`)
- docs/adr/lane-c-evidence.md
- backend/app/claims_engine/claim_repo.py (`SqlAlchemyClaimRepository`)
- backend/app/claims_engine/not_evaluated.py
- backend/tests/claims_engine/test_not_evaluated_claims.py
- backend/tests/evidence_ledger/test_evidence_schema_contract.py
- backend/tests/claims_engine/test_claim_schema_contract.py
- schemas/evidence_schema.json
- schemas/claim_schema.json
- docs/adr/lane-c-schemas.md
- docs/adr/lane-c-rules.md
- backend/app/reports/service.py
- backend/app/reports/models.py
- backend/app/reports/report_repo.py
- backend/app/reports/adapters.py
- docs/adr/lane-d-0001-report-persistence.md
- backend/tests/reports/test_report_repository.py (1 test)
- backend/tests/reports/test_adapters.py (4 tests)
- backend/tests/reports/ and backend/tests/api/ (20 tests)
- backend/tests/api/test_report_runs_db.py
- backend/tests/reports/test_report_regression.py
- schemas/report_run_schema.json
- backend/tests/reports/test_report_schema_contract.py
- docs/adr/lane-d-0010-report-manifest-metadata.md
- docs/adr/lane-d-0013-report-metadata-extension-boundary.md
- docs/adr/lane-d-0011-connector-human-review-actions.md
- docs/adr/lane-d-0014-connector-review-api-auth-blocker.md
- docs/adr/lane-d-0012-connector-human-review-api-semantics.md
- docs/adr/lane-d-0015-connector-reviewer-principal.md
- docs/adr/lane-d-0016-connector-review-action-route-subset.md
- docs/adr/lane-d-0017-report-validation-metadata.md
- docs/adr/lane-d-0018-job-schema-boundary.md
- backend/app/api/reviewer_auth.py
- backend/tests/api/test_reviewer_auth.py
- docs/planning_pack/api/openapi_stub.yaml
- backend/tests/test_planning_pack_schema_copies.py
- db/seeds/source_registry_seeds.py
- scripts/seed_sources.py
- docs/adr/lane-a-0001-provenance-model.md
- templates/data_source_license_review.md
- registers/data_source_registry.csv
- schemas/source_schema.json
- schemas/source_provenance_schema.json
- backend/tests/source_registry/test_source_schema_contract.py
- backend/tests/source_registry/test_source_provenance_schema_contract.py
- backend/tests/connectors/test_fixture_quality.py
- tests/fixtures/geometries/
Next lowest-dependency task:
- After Session 1's Lane C evidence-linkage/OpenAPI branch reaches a clean merge point, implement the accepted review-action mutation route subset with OpenAPI refresh, or choose a specific accepted report metadata extension implementation/broader fixture-quality slice if route work would conflict.
Do not work on yet:
- Live connectors
- UI or LLM summaries
- Production ops/security/observability
- New jurisdictions or intents until Level 8/Level 9 planning explicitly selects them
- Live connector behavior, credentials, browser/download steps, paid APIs, schema edits, and Lane A/B/C/D implementation changes for connector work unless explicitly coordinated with the owning lane
```


## Current objective

Build the foundation vertical slice for the land/locality due-diligence compiler:

```text
source registry -> area geometry -> evidence -> claim -> report run -> API response
```

## Active plan (overall)

`plans/2026-06-03-foundation-vertical-slice.md`

## 4-lane agent architecture (active)

This workspace uses 4 isolated agent lanes, each with dedicated scope, plans, and state files.
See `LANE_OWNERSHIP.md` for ownership boundaries.

| Lane | Scope | Active plan | State | Milestone gates |
|---|---|---|---|---|
| Lane A | Source Registry + DB Infrastructure | `plans/lane-a-2026-06-03-source-registry.md` | `state/lane-a-state.md` | L2-*, L3-* |
| Lane B | Area + Geometry Domain | `plans/lane-b-2026-06-03-area-geometry.md` | `state/lane-b-state.md` | L4-* |
| Lane C | Evidence Ledger + Claims Engine | `plans/lane-c-2026-06-03-evidence-claims.md` | `state/lane-c-state.md` | L5-*, L6-* |
| Lane D | Reports + API + Platform | `plans/lane-d-2026-06-03-reports-api-infra.md` | `state/lane-d-state.md` | L7-* |

**Each lane agent must read `LANE_OWNERSHIP.md` before any code change.**

## Key constraints

- Bottom-up implementation only.
- Postgres/PostGIS is system of record.
- Evidence-before-claim invariant is non-negotiable.
- No live data connectors before license/source registry/fixture tests.
- No UI or LLM work until the storage/evidence/claim/report spine works.
- Lane agents MUST NOT modify files owned by other lanes.

## Known blockers / undecided items

| Item | Status | Impact |
|---|---|---|
| MVP state/counties | Undecided | Do not hard-code jurisdiction-specific logic |
| Parcel vendor | Undecided | Use fixtures/public source registry only |
| Live connector credentials | Unavailable | No live API/vendor integrations |
| Docker availability | Available | DB smoke now passes locally |
| Connector integration zone | Canonical in `LANE_OWNERSHIP.md` | CON-001 through CON-020 complete; next Level 8 connector pass needs selection |

## Last verified state

369 tests pass in the DB-enabled Windows PowerShell verification path after CON-035 connector fixture evidence area consistency; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes. C-002, D-000, D-001, D-002, D-003, D-004, D-005, CON-001, CON-002, CON-003, CON-004, CON-005, CON-006, CON-007, CON-008, CON-009, CON-010, CON-011, CON-012, CON-013, CON-014, CON-015, CON-016, CON-017, CON-018, CON-019, CON-020, CON-021, CON-022, CON-023, CON-024, CON-025, CON-026, CON-027, CON-028, CON-029, CON-030, CON-031, CON-032, CON-033, CON-034, CON-035, Lane A TA-070, Lane A TA-080, Lane C TC-170, Lane C TC-180, Lane C planning-pack schema-copy alignment, Lane D TD-080, Lane D TD-081, Lane D TD-082, Lane D TD-083, Lane D TD-084, Lane D TD-090, and Lane B TB-100 are complete in this worktree. The next Level 8 pass should implement the accepted review-action mutation route subset with OpenAPI refresh after Session 1's Lane C evidence-linkage/OpenAPI branch reaches a clean merge point, or choose broader fixture-quality/report metadata work if route work would conflict.

## Local repo bootstrap state

- Local Git initialized on `main`.
- `origin` is configured as `https://github.com/benjmcd/land-dd.git`.
- Local baseline commit exists on `main`: `ffb73e1` (`Establish governed scaffold baseline`).
- No GitHub push has been performed; `origin/main` remains at `13b75a9`.
- Local Codesight index exists at `.codesight/`; regenerate after significant code changes.
