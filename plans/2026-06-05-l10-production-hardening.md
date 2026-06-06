# Level 10 Production Hardening

## Goal

Advance the MVP workflow toward production operation by removing hardcoded reviewer
credentials, adding a backend container target, emitting structured runtime logs, and
persisting async report job state in Postgres when DB-backed API services are enabled.
Add a fail-closed API-key gate that can protect runtime API/UI/docs surfaces when
production mode requires it. Add a default-off runtime rate limiter for single-node
API exposure. Add structured runtime metrics for API operation visibility.
Verify the backend image builds and the Compose runtime serves basic operational
endpoints. Align connector preflight license/source-use checks with the source registry's
fail-closed production-use rule before any live connector is attempted. Gate report
consumption of connector-produced evidence on explicit connector review approval.

## Non-goals

- No live connector integration outside the bounded DS-001 USGS TNM EPQS connector plus
  controlled operator/API, durable scheduling, and request-time orchestration slices; the
  bounded DS-002 FEMA NFHL slice; the bounded DS-003 USDA SSURGO connector plus
  operator/API, durable scheduling, and request-time slices; and the bounded DS-004
  National Wetlands Inventory operator/API, durable scheduling, and request-time
  orchestration slice.
- No live source/API calls outside bounded DS-001 USGS TNM EPQS, DS-002 FEMA
  NFHL, DS-003 Soil Data Access/SSURGO, and DS-004 NWI validate-only smoke
  checks.
- No paid vendor APIs or credentials.
- No billing, report credits, hosted billing reconciliation, hosted/cloud deployment,
  hosted deployment attestation, registry image push/signing, published registry-image
  attestation, full user auth/RBAC/OAuth/OIDC/user accounts, or automatic key
  rotation/external secret-manager integration for the local-only product.
- No new legal conclusions, suitability assertions, or source interpretation beyond
  fail-closed eligibility gating for reviewed connector evidence.
- No user accounts, RBAC, OAuth/OIDC, session auth, automatic key rotation, external
  secret-manager integration, hosted log-retention/SIEM integration, or user-bound auth
  audit semantics.
- No distributed or multi-process rate-limit backend.
- No automatic migration runner inside the backend container.
- No DB schema migration unless the existing `jobs.job_queue` table is insufficient.

## Current state

- `state/PROJECT_STATE.md` records Level 10 as partially passing and names further
  production hardening as the next lowest-dependency task.
- The local-only scope has been clarified: billing, hosted deployment, hosted
  attestations, registry push/signing, automatic key rotation/external secret managers,
  and full user auth/RBAC/OIDC/user accounts are deferred out of scope unless a future
  plan explicitly changes the product target.
- Connector review action routes currently accept local service-account reviewer auth.
- The interrupted Claude session started US-015 through US-018 and partially applied
  US-015 in `backend/app/core/config.py`, `backend/app/api/dependencies.py`,
  `backend/app/api/connectors.py`, and `backend/app/main.py`.
- The existing DB migration defines `jobs.job_queue` with job status, payload,
  idempotency key, attempts, timing fields, and error fields.
- `backend/tests/api/test_report_runs_db.py` now passes in DB mode after the
  background task was moved to a fresh SQLAlchemy session.
- Runtime API-key auth is now configurable through `REQUIRE_API_KEY`, `API_KEYS`, and
  `API_KEY_SPECS`.
  It is off by default for local development, protects API/UI/docs/OpenAPI when enabled,
  leaves `/health` and `/version` public, and fails closed if enabled without keys.
- Runtime rate limiting is now configurable through `ENABLE_RATE_LIMIT`,
  `RATE_LIMIT_REQUESTS`, and `RATE_LIMIT_WINDOW_SECONDS`. It is off by default,
  protects API/UI/docs when enabled, leaves `/health` and `/version` public, and
  uses hashed API-key identity when a key is present or client host otherwise.
- Runtime metrics are now configurable through `ENABLE_METRICS`. Metrics are on by
  default, exposed at `/metrics`, aggregate by route template to avoid UUID/path
  cardinality, and are protected by API-key/rate-limit middleware when those gates
  are enabled.
- Compose now allows the host Postgres port to be changed through `DB_PORT`, while
  preserving the internal backend-to-db URL.
- Connector source-use preflight now fails closed unless the source registry record has
  approved review status and explicit allowed production-use rights for license,
  commercial use, redistribution, cache, export, raw data, and AI use.
- DS-002 FEMA NFHL is the first reviewed live-source candidate. A bounded connector now
  queries the public effective-data FEMA NFHL ArcGIS REST service layer 28 only, requires
  a small EPSG:4326 bounding box, emits source-failure evidence for no-data/error/limit
  cases, and reuses the existing retrieval provenance plus evidence-ingestion adapters.
- DS-001 USGS The National Map is now reviewed for MVP physical-screening/base-layer
  source-rights use with restrictions. A bounded connector-layer USGS TNM EPQS
  slice now samples the official EPQS JSON service at the bbox center and corners,
  emits one low-confidence terrain-relief derived metric for screening, emits
  source-failure evidence for no-data/error/malformed cases, and reuses existing
  connector provenance/evidence adapters. DS-001 remains a screening-only source and
  does not add DEM-download, survey-grade elevation, engineering, site-plan, legal,
  buildability, lending, appraisal, or investment conclusions.
- A controlled reviewer-authenticated DS-001 API/operator route now invokes the bounded
  USGS TNM EPQS connector at `POST /connector-runs/usgs-tnm/query-bbox`, records
  retrieval provenance, persists terrain-relief derived metric or source-failure evidence,
  enqueues connector review status, and refreshes OpenAPI parity. It does not create
  scheduler jobs, request-time shortcuts, reports, claims, DEM downloads, survey-grade
  elevation, engineering, legal, buildability, lending, appraisal, or investment
  conclusions.
- Explicit background DS-001 connector scheduling is now available through the same
  durable `live_connector_run` queue and bounded worker helper as DS-002, DS-003, and
  DS-004. `POST /connector-runs/usgs-tnm/schedule-bbox` enqueues bounded DS-001 work
  without calling EPQS or creating reports; `run_next_live_connector_job` leases the job,
  dispatches by `source_registry_id`, runs the existing DS-001 orchestration path, and
  records the connector review item for later approval.
- Request-time DS-001 orchestration now runs first in the same `/intake` and
  `/report-runs` flow when `ENABLE_LIVE_CONNECTORS=true`. After DS-001 approval,
  operators continue with `/report-runs` for the same `area_id`; the API then advances
  through the existing DS-002, DS-004, and DS-003 gates before creating a report job.
  Approved DS-001 evidence may appear as buildability-domain terrain screening evidence,
  but DS-001 still has no DEM downloads, survey-grade elevation, engineering, legal,
  buildability, lending, appraisal, investment conclusion, or DS-001-specific claim.
- DS-003 USDA Web Soil Survey/SSURGO is now reviewed for MVP soil/septic/ag screening
  source-rights use with restrictions. This makes the source rights-ready in the
  source-readiness audit.
- A bounded DS-003 USDA SSURGO connector-layer slice now uses the official Soil
  Data Access `post.rest` query service with `JSON+COLUMNNAME` output and the
  documented `SDA_Get_Mukey_from_intersection_with_WktWgs84` function to query a
  small EPSG:4326 bbox. It emits ledger-safe soil/septic/ag screening
  spatial-intersection evidence for intersecting mapunit/component rows and
  source-failure evidence for no-data/error/malformed cases.
- A controlled reviewer-authenticated DS-003 API/operator route now invokes the bounded
  SSURGO connector at `POST /connector-runs/ssurgo/query-bbox`, records retrieval
  provenance, persists soil/septic/ag screening spatial or source-failure evidence,
  enqueues connector review status, and refreshes OpenAPI parity. It does not add WSS
  interpretation/rating execution, pAOI state, or final septic, soil-suitability,
  engineering, permitting, legal, buildability, lending, appraisal, or investment
  conclusions.
- Explicit background DS-003 connector scheduling is now available through the same
  durable `live_connector_run` queue and bounded worker helper as DS-002 and DS-004.
  `POST /connector-runs/ssurgo/schedule-bbox` enqueues bounded DS-003 work without
  calling SSURGO or creating reports; `run_next_live_connector_job` leases the job,
  dispatches by `source_registry_id`, runs the existing DS-003 orchestration path, and
  records the connector review item for later approval. DS-003 still has no pAOI state,
  WSS interpretations/ratings, or final septic/soil-suitability/buildability
  conclusions.
- DS-004 National Wetlands Inventory is now reviewed for MVP wetland/deepwater
  screening source-rights use with restrictions. This makes the source rights-ready in
  the source-readiness audit.
- A bounded DS-004 National Wetlands Inventory connector now queries the official
  USFWS-linked Wetlands ArcGIS REST layer 0 with EPSG:4326 bbox and feature limits,
  emits wetland/deepwater screening evidence for usable features, emits source-failure
  evidence for no-data/error/malformed/transfer-limit cases, and reuses the existing
  retrieval provenance plus evidence-ingestion adapters.
- A controlled reviewer-authenticated DS-004 API/operator route now invokes the bounded
  NWI connector at `POST /connector-runs/nwi/query-bbox`, records retrieval provenance,
  persists spatial or source-failure evidence, enqueues connector review status, and
  refreshes OpenAPI parity. Approved DS-004 connector evidence can feed the existing
  generic connector report-resume path after `approve_for_connector_qa`; this is covered
  by an API regression.
- Explicit background DS-004 connector scheduling is now available through the same
  durable `live_connector_run` queue and bounded worker helper as DS-002.
  `POST /connector-runs/nwi/schedule-bbox` enqueues bounded DS-004 work without
  calling NWI or creating reports; `run_next_live_connector_job` leases the job,
  dispatches by `source_registry_id`, runs the existing DS-004 orchestration path, and
  records the connector review item for later approval. DS-004 still has no
  source-specific autonomous scheduling policy.
- File-backed DS-004 raw NWI response fixtures now cover one representative
  wetland/deepwater FeatureCollection success response and one empty FeatureCollection
  source-failure response. These fixtures validate connector parsing and failure
  semantics without making live NWI calls.
- API route validation/error paths now use the non-deprecated FastAPI/Starlette 422
  status constant name, preserving status code 422 while keeping the full verification
  gate free of the prior deprecation warning summary.
- A reviewer-authenticated live connector sequence scheduler is now available at
  `POST /connector-runs/live-sequence/schedule-bbox`. It enqueues the current reviewed
  DS-001, DS-002, DS-004, then DS-003 durable job sequence for a registered area without
  fetching live sources, persisting evidence, approving review, or creating reports.
- A reviewer-authenticated read-only live connector job status route is now available at
  `GET /connector-runs/live-jobs/{job_id}`. It returns the durable queued/running/
  succeeded/failed job record without leasing work, retrying jobs, fetching live sources,
  creating reports, or mutating queue state.
- A reviewer-authenticated failed report job retry route is now available at
  `POST /report-runs/{report_run_id}/retry`. It preserves the failed job, creates a new
  queued report job from the failed job's stored area and intent, and stores retry lineage
  as `retry_of_report_run_id`.
- A local backup/restore proof is now available through
  `scripts/run_backup_restore_check.ps1` and `scripts/run_backup_restore_check.sh`. The
  check dumps the configured source DB, restores into a dedicated
  `land_diligence_restore_check*` database, runs `scripts/db_smoke_check.py` against the
  restored database, and drops the restore DB by default.
- A controlled reviewer-authenticated DS-002 API route now invokes the bounded FEMA NFHL
  connector, records retrieval provenance, persists evidence or source-failure evidence,
  and enqueues the existing connector review status without creating claims or reports.
- Reviewer-authenticated connector review actions now provide a real manual closeout path:
  approve for connector QA, request fixture/source fix, requeue after fix, and cancel
  mutate only review queue state and record reviewer decisions in the queue payload.
- Connector-produced evidence now carries optional `source_ingest_run_id` lineage. Report
  generation includes connector-lineage evidence only when the matching connector review
  queue item is `SUCCEEDED` with latest `review_decision.action` equal to
  `approve_for_connector_qa`; otherwise it is excluded from report claims and manifests.
- Request-time DS-002 orchestration is now available for `/intake` and `/report-runs`
  when `ENABLE_LIVE_CONNECTORS=true`. Those entry points run bounded DS-002, persist
  provenance/evidence/review queue state, and return `pending_connector_review` instead
  of scheduling report generation until the connector review item is approved.
- Request-time DS-004 orchestration now follows DS-001 and DS-002 in the same `/intake`
  and `/report-runs` flow when `ENABLE_LIVE_CONNECTORS=true`. After DS-002 approval,
  operators continue with `/report-runs` for the same `area_id`; the API runs bounded
  DS-004, returns `pending_connector_review` until DS-004 approval, and creates the report
  only after both reviewed connector runs are approved.
- Request-time DS-003 orchestration now follows DS-001, DS-002, and DS-004 in the same
  `/intake` and `/report-runs` flow when `ENABLE_LIVE_CONNECTORS=true`. After DS-004 approval,
  operators continue with `/report-runs` for the same `area_id`; the API runs bounded
  DS-003, returns `pending_connector_review` until DS-003 approval, and creates the report
  only after DS-001, DS-002, DS-004, and DS-003 are approved. Approved DS-003 evidence may produce
  only an UNKNOWN, review-required SSURGO screening claim; it does not determine septic
  approval, perc results, soil suitability, engineering feasibility, permitting,
  buildability, lending, appraisal, or investment suitability.
- An explicit post-approval report resume endpoint is now available at
  `POST /connector-runs/{ingest_run_id}/report-runs`. It derives `area_id` from the
  approved connector review queue item, requires reviewer auth plus
  `approve_for_connector_qa`, schedules the existing async report job, and does not
  re-fetch DS-002.
- Connector review queue payloads now keep durable reviewer action history. Approve/fix
  decisions still update `review_decision` for report gating, while closeout, requeue, and
  cancel actions append authenticated reviewer metadata to `review_action_history`.
- Explicit background DS-002 connector scheduling is now available through durable
  `live_connector_run` jobs. `POST /connector-runs/fema-nfhl/schedule-bbox` enqueues
  bounded DS-002 work without calling FEMA or creating reports; `run_next_live_connector_job`
  leases one job, runs the existing orchestration path, and records the connector review
  item for later approval.
- A bounded live connector worker command is now available at
  `scripts/live_connector_worker.py`. It opens fresh DB-backed services per job, calls
  `run_next_live_connector_job(...)`, commits succeeded or failed job state, emits text or
  JSON summaries, and exits after one job by default. It does not autostart a daemon,
  create reports, schedule jobs, or bypass connector review.
- The worker command now supports explicit polling mode, and Compose exposes it through
  an opt-in `workers` profile as `live-connector-worker`. The profile is omitted from
  default `docker compose up`, uses `restart: unless-stopped`, and still only processes
  existing `live_connector_run` jobs through the review-gated helper.

## Proposed design

- Keep reviewer auth local and explicit: parse `REVIEWER_ACCOUNTS` from settings
  into service-account tokens and inject the auth dependency through `ApiServices`.
- Add a Dockerfile that installs the backend package and runs Uvicorn against
  `app.main:app`; extend compose with a backend service depending on healthy PostGIS.
- Add stdlib JSON logging with a compact formatter and app startup wiring. Log async
  report job state transitions from the report route boundary.
- Add a `SqlAlchemyAsyncReportJobStore` backed by `jobs.job_queue`. Store report
  job metadata in JSON payload and use the existing `job_status` enum values.
- Keep Level 10 release readiness scoped to local PC production-grade: source rights,
  evidence/claim/report correctness, local reproducibility, local packaging, local
  backup/restore, local smoke tests, local security checks, and operator workflow
  quality are required; hosted/cloud, billing, registry publication, full user-account
  auth, and external secret-manager automation are optional future scope only.
- In DB mode, schedule background report creation through a fresh session factory
  instead of reusing request-scoped services.
- Add a small FastAPI middleware for shared API-key enforcement before rate limiting.
  Keep it dependency-free, default-off, constant-time for key comparison, and explicit
  about public liveness/version endpoints.
- Add an in-process fixed-window rate limiter before app routing. Keep it dependency-free
  and default-off, with explicit headers and a documented single-node limitation.
- Add a dependency-free structured metrics collector for request counts, status counts,
  and duration aggregates. Expose it as JSON for operators without changing report or
  evidence semantics.
- Verify `docker compose build backend`, bring up `db` and `backend`, and smoke
  `/health`, `/version`, and `/metrics` through the published backend port.
- Reuse the source registry production-use helper for connector preflight so connector
  runs cannot proceed on unknown, unreviewed, pending, blocked, or incompatible source
  rights.
- Add a read-only source-readiness audit command so operators can see which registry
  fields block live connector candidates before attempting integration.
- Add a bounded DS-002 FEMA NFHL connector that stays in the connector layer, uses no
  claims/report/API shortcuts, and emits evidence contracts plus retrieval provenance
  contracts compatible with the existing connector adapters.
- Add a controlled DS-002 FEMA NFHL API/operator invocation path that requires reviewer
  auth, registered DS-002 source authority, and a registered area, then routes the run
  through the existing provenance, evidence-ingestion, and review queue adapters.
- Add durable evidence lineage to connector-produced evidence and a report-layer approval
  gate that consumes the connector review queue as the current approval authority.
- Add default-off request-time DS-002 orchestration to `/intake` and `/report-runs` that
  pauses report generation at the same connector review gate rather than bypassing it.
- Add an explicit durable live-connector scheduler path for DS-002 that queues work in
  `jobs.job_queue` and provides a bounded supervisor-callable worker command plus opt-in
  Compose worker profile without bypassing connector review.
- Add a bounded connector-layer DS-004 National Wetlands Inventory connector that stays
  before API/worker/report orchestration, preserves NWI caveats, and converts empty,
  errored, malformed, or transfer-limited live responses into source-failure evidence.
- Add a controlled DS-004 National Wetlands Inventory API/operator invocation path that
  requires reviewer auth, registered DS-004 source authority, and a registered area, then
  routes the run through the existing provenance, evidence-ingestion, review queue, and
  approved connector report-resume gates.
- Generalize the durable live connector scheduler and worker helper so DS-004 can use
  the existing `jobs.job_queue` path without adding a migration, fetching at schedule
  time, creating report jobs, or bypassing connector review.
- Add a read-only operator status route for durable live connector jobs so scheduled
  work can be inspected through the API without direct DB access or worker logs.
- Extend default-off request-time live connector orchestration from DS-002 to DS-004 in a
  fixed order, preserving one review gate per connector and report creation only after all
  request-time connector-lineage evidence is approved.
- Extend default-off request-time live connector orchestration from DS-004 to DS-003 in
  the same fixed-order/review-gated sequence, and add cautious UNKNOWN report language for
  approved SSURGO screening evidence without adding septic, soil-suitability, or
  buildability conclusions.
- Add a bounded connector-layer DS-001 USGS TNM EPQS terrain-relief screening connector
  that stays before API/worker/report orchestration, samples only a small EPSG:4326 bbox
  center/corners set, preserves USGS caveats, and converts empty, errored, malformed, or
  no-elevation live responses into source-failure evidence.
- Add a controlled DS-001 USGS TNM EPQS API/operator invocation path that requires
  reviewer auth, registered DS-001 source authority, and a registered area, then routes
  the run through the existing provenance, evidence-ingestion, and review queue adapters
  without adding scheduling, request-time orchestration, claims, or reports.
- Extend the durable live connector scheduler and worker helper to DS-001 without adding a
  migration, fetching at schedule time, creating report jobs, or bypassing connector
  review.
- Extend default-off request-time live connector orchestration to run bounded DS-001 first
  for `/intake` and `/report-runs`, reusing existing review gating so approved DS-001
  evidence can enter reports without creating a DS-001 claim or terrain/buildability
  conclusion.
- Add a file-backed DS-004 NWI raw response corpus for representative success and empty
  source-failure behavior, and keep the shared worker CLI help synchronized with the
  supported DS-001/DS-002/DS-003/DS-004 job set.
- Replace deprecated API 422 status constant usages with the current constant name without
  changing response status codes, payloads, validation semantics, or routing.
- Add a reviewer-authenticated batch scheduler for the current reviewed live connector
  sequence so operators can enqueue DS-001, DS-002, DS-004, and DS-003 durable jobs with
  one call while preserving one worker execution and review gate per source.

## Bottom-up sequence

1. Finish US-015 settings-backed reviewer auth and parser coverage.
2. Add US-016 backend Dockerfile and compose service without new dependencies.
3. Add US-017 JSON logging module, app startup wiring, and narrow formatter tests.
4. Add US-018 SQLAlchemy job store plus DB-mode background task wiring.
5. Add US-019 production API-key middleware, parser coverage, and container/env wiring.
6. Add US-020 default-off runtime rate limiting, parser coverage, and container/env wiring.
7. Add US-021 structured runtime metrics, `/metrics` route, OpenAPI parity, and env wiring.
8. Add US-022 container build/runtime smoke with configurable host DB port.
9. Add US-023 fail-closed connector source-use preflight aligned to source registry
   production-use checks.
10. Add US-024 source-readiness audit reporting for connector candidate selection.
11. Add US-025 bounded DS-002 FEMA NFHL live connector.
12. Add US-026 controlled DS-002 FEMA NFHL API/operator invocation.
13. Add US-027 connector review closeout actions for live and fixture connector runs.
14. Add US-028 approved connector evidence report gating with evidence lineage.
15. Add US-029 request-time DS-002 orchestration for intake/report-run flows.
16. Add US-030 explicit durable DS-002 live connector scheduling.
17. Add US-031 bounded supervised DS-002 live connector worker command.
18. Add US-032 opt-in supervised polling/profile packaging for the DS-002 worker.
19. Add US-033 DS-001 USGS The National Map source-rights review and readiness update.
20. Add US-034 DS-003 USDA Web Soil Survey/SSURGO source-rights review and readiness update.
21. Add US-035 DS-004 National Wetlands Inventory source-rights review and readiness update.
22. Add US-036 bounded connector-layer DS-004 National Wetlands Inventory connector.
23. Add US-037 controlled DS-004 National Wetlands Inventory API/operator invocation.
24. Add US-038 explicit durable DS-004 live connector scheduling and worker dispatch.
25. Add US-039 read-only live connector job status API.
26. Add US-040 explicit durable DS-003 live connector scheduling and worker dispatch.
27. Add US-041 request-time DS-004 orchestration after DS-002 approval.
28. Add US-042 request-time DS-003 orchestration after DS-004 approval with cautious
    UNKNOWN SSURGO screening claim/report language.
29. Add US-043 bounded connector-layer DS-001 USGS TNM EPQS terrain-relief screening.
30. Add US-044 controlled DS-001 USGS TNM EPQS API/operator invocation.
31. Add US-045 explicit durable DS-001 live connector scheduling and worker dispatch.
32. Add US-046 request-time DS-001 orchestration and approved-evidence report inclusion
    before the existing DS-002, DS-004, and DS-003 gates.
33. Add US-047 DS-004 file-backed raw NWI response fixture corpus plus worker CLI
    supported-source help coverage.
34. Add US-048 API 422 status constant deprecation cleanup.
35. Add US-049 reviewer-authenticated live connector sequence scheduler.
36. Add US-050 reviewer-authenticated failed report job retry with retry lineage.
37. Add US-051 backup/restore proof scripts and runbook.
38. Add US-052 reviewer-authenticated operator queue-health surface.
39. Add US-053 DB-backed deployment smoke automation.
40. Add US-054 incident response and rollback proof.
41. Add US-055 repo-local alert rules for high-severity failures and stale source
    metadata.
42. Add US-056 CI supply-chain dependency vulnerability scanning and update hygiene.
43. Add US-057 repo-local cost monitoring catalog and guardrail proof.
44. Add US-058 backend production dependency lock, SBOM, and provenance proof.
45. Add US-059 backend container image/base-image vulnerability scan proof.
46. Add US-060 digest-pinned backend Docker base-image proof.
47. Add US-061 GitHub dependency lock/SBOM artifact attestation proof.
48. Add US-062 report cost metrics zero-dollar attribution proof.
49. Add US-063 repo-local release readiness catalog and validate-only proof.
50. Add US-064 repo-local access-control posture catalog and validate-only proof.
51. Add US-065 scoped reviewer service-account authorization for protected operator routes.
52. Add US-066 local release package builder, manifest, and validate-only proof.
53. Add US-067 registry image publication readiness catalog and validate-only proof.
54. Add US-068 hosted deployment readiness catalog and validate-only proof.
55. Add US-069 raw-or-sha256 API/reviewer secret specs.
56. Add US-070 configured static API-key lifecycle specs.
57. Add US-071 structured API-key auth audit logging.
58. Add US-072 DB-backed API-key auth audit events.
59. Add US-073 load test baseline: `scripts/run_load_test.ps1/.sh`, `docs/runbooks/load_testing.md`, `backend/tests/test_load_test_artifacts.py`, `config/release_readiness.yaml` load_test entry. Covers L10-PERF-006.
60. Add US-074 security static analysis CI gate: `scripts/run_security_scan.ps1/.sh`, `docs/runbooks/security_scan.md`, bandit CI job, `backend/tests/test_security_scan_artifacts.py`. Covers L10-SEC-005.
61. Add US-075 data retention policy catalog: `config/data_retention.yaml`, `docs/runbooks/data_retention.md`, proof scripts, artifact tests. Covers L10-SEC-007.
62. Add US-076 jurisdiction and rulepack readiness checklists: `docs/checklists/jurisdiction_readiness.md`, `docs/checklists/rulepack_readiness.md`, `backend/tests/test_readiness_checklists.py`. Covers L10-DATA-005/006.
63. Add US-077 DB connection pool explicit configuration: `DB_POOL_SIZE/MAX_OVERFLOW/TIMEOUT/RECYCLE` in config.py + conditional pool kwargs in engine.py + `backend/tests/test_db_pool_config.py`. Covers L10-PERF-009.
64. Add US-078 performance and scalability runbook: `docs/runbooks/performance.md` (cache, batch, spatial indexes, backpressure, perf regression). Covers L10-PERF-002/005/008/010.
65. Add US-079 report lineage endpoint: `GET /report-runs/{id}/lineage` in `backend/app/api/reports.py` + `backend/tests/api/test_report_lineage.py`. Covers L10-DATA-007.
66. Add US-080 candidate comparison endpoint: `GET /report-runs/compare` + `backend/tests/api/test_report_comparison.py`. Covers L10-PROD-006.
67. Add US-081 report rerun diff endpoint: `GET /report-runs/{id}/diff?base_id=`. Covers L10-PROD-004.
68. Run targeted tests, lint, type checks, and the Windows verification gate.
69. Update project state, worklog, validation log, and this plan.

## Files likely to change

| File | Expected change |
|---|---|
| `backend/app/core/config.py` | API/reviewer secret parsing, `API_KEY_SPECS`, `REVIEWER_ACCOUNTS`, `REVIEWER_ACCOUNT_SCOPES`, and logging-related settings |
| `backend/app/api/api_key_auth.py` | Default-off API-key middleware and structured auth audit logs/events |
| `backend/app/api/auth_audit.py` | API-key auth audit event model plus in-memory and SQLAlchemy `audit.events` sinks |
| `backend/app/api/secret_specs.py` | Shared raw-or-sha256 secret spec validation and matching |
| `backend/app/api/reviewer_auth.py` | Scoped local reviewer service-account auth |
| `backend/app/api/rate_limit.py` | Default-off fixed-window rate-limit middleware |
| `backend/app/core/metrics.py` | Structured runtime metrics collector and middleware |
| `backend/app/api/metrics.py` | JSON runtime metrics endpoint |
| `backend/app/api/dependencies.py` | Inject reviewer auth and DB-backed async job store |
| `backend/app/api/connectors.py` | Use services-backed scoped reviewer auth |
| `backend/app/api/live_connector_jobs.py` | Worker helper for queued live connector jobs |
| `backend/app/api/live_connectors.py` | Shared live connector API and request-time orchestration |
| `backend/app/api/areas.py` | API validation status constant cleanup |
| `backend/app/api/intake.py` | API validation status constant cleanup |
| `docs/adr/live-sequence.md` | ADR for the reviewed live connector sequence scheduler |
| `docs/runbooks/mvp_operator.md` | Operator-facing live connector sequence scheduling workflow |
| `backend/app/api/reports.py` | Log job transitions, use fresh DB services in background, and expose failed-job retry |
| `backend/app/main.py` | Store settings and configure logging |
| `backend/app/reports/job_store.py` | Add SQLAlchemy-backed job store and retry lineage |
| `backend/app/core/logging.py` | Structured JSON logging |
| `backend/app/source_registry/usage_rights.py` | Shared source production-use decision |
| `backend/app/connectors/license_guard.py` | Fail-closed connector source-use preflight |
| `scripts/source_readiness.py` | Read-only connector source-readiness report |
| `scripts/run_backup_restore_check.ps1` | Windows backup/restore proof against a dedicated restore DB |
| `scripts/run_backup_restore_check.sh` | POSIX backup/restore proof against a dedicated restore DB |
| `docs/runbooks/backup_restore.md` | Backup/restore proof runbook and safety boundaries |
| `backend/app/api/operations.py` | Reviewer-authenticated and scoped operator health API |
| `backend/app/domain/job_health.py` | Shared queue-health DTO |
| `backend/tests/api/test_operations.py` | Operator queue-health API tests |
| `scripts/run_deployment_smoke.ps1` | Windows Compose deployment smoke |
| `scripts/run_deployment_smoke.sh` | POSIX Compose deployment smoke |
| `backend/tests/api/test_app_runtime_mode.py` | Runtime service-mode configuration tests |
| `backend/tests/test_deployment_smoke_scripts.py` | Deployment smoke artifact coverage |
| `docs/runbooks/incident_response.md` | Incident severity, ownership, escalation, rollback, and recovery runbook |
| `scripts/run_incident_rollback_check.ps1` | Windows incident/rollback runbook proof |
| `scripts/run_incident_rollback_check.sh` | POSIX incident/rollback runbook proof |
| `backend/tests/test_incident_rollback_artifacts.py` | Incident/rollback artifact coverage |
| `config/ops_alert_rules.yaml` | Repo-local alert rule catalog for Level 10 ops signals |
| `docs/runbooks/alerting.md` | Alert rule source, validation, and escalation runbook |
| `scripts/run_alert_rules_check.ps1` | Windows validate-only alert rule proof |
| `scripts/run_alert_rules_check.sh` | POSIX validate-only alert rule proof |
| `backend/tests/test_alerting_artifacts.py` | Alerting artifact coverage |
| `.github/workflows/ci.yml` | CI supply-chain dependency vulnerability scan |
| `.github/dependabot.yml` | Dependency update hygiene for GitHub Actions and backend Python dependencies |
| `docs/runbooks/supply_chain.md` | Supply-chain scan operator workflow and limits |
| `scripts/run_supply_chain_check.ps1` | Windows validate-only supply-chain configuration proof |
| `scripts/run_supply_chain_check.sh` | POSIX validate-only supply-chain configuration proof |
| `backend/tests/test_supply_chain_artifacts.py` | Supply-chain artifact coverage |
| `backend/requirements-prod.lock` | Hashed backend production dependency lock for CPython 3.12 manylinux runtime |
| `docs/sbom/backend-prod-sbom.json` | Repo-local CycloneDX SBOM derived from the production dependency lock |
| `docs/runbooks/dependency_provenance.md` | Dependency provenance workflow and limits |
| `scripts/run_provenance_check.ps1` | Windows validate-only dependency provenance proof |
| `scripts/run_provenance_check.sh` | POSIX validate-only dependency provenance proof |
| `backend/tests/test_provenance_artifacts.py` | Dependency lock/SBOM/provenance artifact coverage |
| `.github/workflows/ci.yml` | Dependency artifact and SBOM attestation job |
| `docs/runbooks/container_image_scan.md` | Docker Scout backend image scan workflow and limits |
| `scripts/run_container_scan_check.ps1` | Windows validate-only container image scan proof |
| `scripts/run_container_scan_check.sh` | POSIX validate-only container image scan proof |
| `backend/tests/test_container_scan_artifacts.py` | Container image scan artifact coverage |
| `backend/Dockerfile` | Digest-pinned backend runtime base image |
| `config/ops_cost_monitoring.yaml` | Cost category and guardrail catalog |
| `docs/runbooks/cost_monitoring.md` | Cost monitoring workflow and limits |
| `scripts/run_cost_monitoring_check.ps1` | Windows validate-only cost monitoring proof |
| `scripts/run_cost_monitoring_check.sh` | POSIX validate-only cost monitoring proof |
| `backend/tests/test_cost_monitoring_artifacts.py` | Cost monitoring artifact coverage |
| `config/release_readiness.yaml` | Repo-local release readiness gate catalog |
| `docs/runbooks/release_readiness.md` | Release readiness workflow and release blockers |
| `scripts/run_release_readiness_check.ps1` | Windows validate-only release readiness proof |
| `scripts/run_release_readiness_check.sh` | POSIX validate-only release readiness proof |
| `backend/tests/test_release_readiness_artifacts.py` | Release readiness artifact coverage |
| `config/release_package.yaml` | Local release package boundary catalog |
| `docs/runbooks/release_package.md` | Release package workflow and publishing limits |
| `scripts/build_release_package.ps1` | Windows local release package builder |
| `scripts/build_release_package.sh` | POSIX local release package builder |
| `scripts/run_release_package_check.ps1` | Windows validate-only release package proof |
| `scripts/run_release_package_check.sh` | POSIX validate-only release package proof |
| `backend/tests/test_release_package_artifacts.py` | Release package artifact coverage |
| `config/image_publication.yaml` | Registry image publication boundary catalog |
| `docs/runbooks/image_publication.md` | Image publication workflow and blocked remote-publish limits |
| `scripts/run_image_publication_check.ps1` | Windows validate-only image publication proof |
| `scripts/run_image_publication_check.sh` | POSIX validate-only image publication proof |
| `backend/tests/test_image_publication_artifacts.py` | Image publication artifact coverage |
| `config/hosted_deployment.yaml` | Hosted deployment runtime input/evidence boundary catalog |
| `docs/runbooks/hosted_deployment.md` | Hosted deployment workflow and blocked infrastructure limits |
| `scripts/run_hosted_deployment_check.ps1` | Windows validate-only hosted deployment proof |
| `scripts/run_hosted_deployment_check.sh` | POSIX validate-only hosted deployment proof |
| `backend/tests/test_hosted_deployment_artifacts.py` | Hosted deployment artifact coverage |
| `config/access_control.yaml` | Repo-local access-control posture catalog |
| `docs/runbooks/access_control.md` | Access-control workflow and auth/RBAC blockers |
| `scripts/run_access_control_check.ps1` | Windows validate-only access-control proof |
| `scripts/run_access_control_check.sh` | POSIX validate-only access-control proof |
| `backend/tests/test_access_control_artifacts.py` | Access-control artifact coverage |
| `backend/tests/api/test_api_key_auth.py` | API-key raw/hash auth parser, middleware, runtime log, and durable audit-event coverage |
| `backend/tests/api/test_reviewer_auth.py` | Reviewer auth and scope parser coverage |
| `backend/tests/api/test_async_report_runs.py` | Report retry scope coverage |
| `schemas/report_run_schema.json` | Required report cost metric fields |
| `backend/app/reports/report_repo.py` | Persisted report cost metric fallback/defaults |
| `docs/adr/lane-d-0010-report-manifest-metadata.md` | Report metadata schema follow-up note |
| `registers/data_source_registry.csv` | Source readiness status for reviewed live-source candidates |
| `docs/source-reviews/ds-001.md` | DS-001 USGS The National Map source-rights review |
| `docs/source-reviews/ds-003.md` | DS-003 USDA Web Soil Survey/SSURGO source-rights review |
| `docs/source-reviews/ds-004.md` | DS-004 National Wetlands Inventory source-rights review |
| `docs/planning_pack/registers/data_source_registry.csv` | Intentionally scoped planning-pack mirror of reviewed source identity/caveats |
| `scripts/live_connector_worker.py` | Bounded DB-backed DS-002 live connector worker command |
| `backend/app/connectors/fema_nfhl.py` | Bounded DS-002 FEMA NFHL live connector |
| `backend/app/connectors/usgs_tnm.py` | Bounded connector-layer DS-001 USGS TNM EPQS terrain screening connector |
| `backend/app/connectors/nwi.py` | Bounded connector-layer DS-004 NWI wetland/deepwater connector |
| `backend/app/connectors/live_jobs.py` | Durable live connector job queue records |
| `backend/app/connectors/result.py` | Structural result protocol shared by fixture and live connectors |
| `backend/app/connectors/review_queue.py` | Manual connector review closeout transitions |
| `backend/app/domain/evidence_contracts.py` | Optional connector run lineage on evidence |
| `backend/app/evidence_ledger/evidence_repo.py` | Persist connector run lineage in evidence metadata |
| `backend/app/reports/service.py` | Exclude unapproved connector-lineage evidence from reports and emit report cost metrics |
| `schemas/evidence_schema.json` | Evidence schema parity for connector run lineage |
| `backend/tests/**` | Parser, logging, job-store, API DB tests |
| `backend/tests/api/test_fema_nfhl_connector_api.py` | Controlled DS-002 API, approval-to-report, DB, and DS-001-through-DS-003 live request-time regressions |
| `backend/tests/connectors/test_nwi_connector.py` | Bounded DS-004 connector success, failure, idempotency, and adapter behavior |
| `backend/tests/connectors/test_usgs_tnm_connector.py` | Bounded DS-001 connector success, failure, idempotency, and adapter behavior |
| `backend/tests/api/test_usgs_tnm_connector_api.py` | Controlled DS-001 API invocation, durable scheduling, and review queue behavior |
| `backend/tests/api/test_nwi_connector_api.py` | Controlled DS-004 API invocation and approved report-resume behavior |
| `tests/fixtures/connectors/nwi_success.geojson` | File-backed raw DS-004 NWI success response fixture |
| `tests/fixtures/connectors/nwi_empty.geojson` | File-backed raw DS-004 NWI empty-response source-failure fixture |
| `backend/tests/api/test_api_key_auth.py` | API-key parser and middleware behavior |
| `backend/tests/api/test_rate_limit.py` | Rate-limit parser and middleware behavior |
| `backend/tests/api/test_metrics.py` | Metrics route, aggregation, auth, and rate-limit behavior |
| `backend/tests/api/test_live_connector_worker.py` | Worker command session/commit/exit behavior |
| `backend/Dockerfile` | Backend container image |
| `.dockerignore` | Keep agent state, caches, archives, and local artifacts out of Docker context |
| `docker-compose.yml` | Backend service and opt-in live connector worker profile |
| `.env.example` | Reviewer/logging/backend runtime settings |
| `state/**` | Progress and validation records |

## Tests / verification

```powershell
cd backend; py -3.12 -m pytest -q tests/api/test_connector_review_actions.py tests/api/test_reviewer_auth.py
cd backend; py -3.12 -m pytest -q tests/api/test_api_key_auth.py tests/api/test_api_scaffold.py tests/api/test_reviewer_auth.py tests/api/test_connector_review_actions.py
cd backend; py -3.12 -m pytest -q tests/api/test_rate_limit.py tests/api/test_api_key_auth.py tests/api/test_api_scaffold.py
cd backend; py -3.12 -m pytest -q tests/api/test_metrics.py tests/api/test_rate_limit.py tests/api/test_api_key_auth.py tests/api/test_api_scaffold.py
cd backend; py -3.12 -m pytest -q tests/connectors/test_license_guard.py tests/connectors/test_static_file_connector.py tests/source_registry/test_source_service.py
cd backend; py -3.12 -m pytest -q tests/source_registry/test_source_readiness.py tests/source_registry/test_source_seeds.py tests/source_registry/test_source_service.py
cd backend; py -3.12 -m pytest -q tests/connectors/test_fema_nfhl_connector.py
cd backend; py -3.12 -m pytest -q tests/connectors/test_usgs_tnm_connector.py
cd backend; py -3.12 -m pytest -q tests/api/test_usgs_tnm_connector_api.py tests/connectors/test_usgs_tnm_connector.py
cd backend; py -3.12 -m pytest -q tests/api/test_usgs_tnm_connector_api.py tests/api/test_live_connector_worker.py
cd backend; py -3.12 -m pytest -q tests/connectors/test_nwi_connector.py
cd backend; py -3.12 -m pytest -q tests/api/test_nwi_connector_api.py tests/connectors/test_nwi_connector.py
cd backend; py -3.12 -m pytest -q tests/test_planning_pack_schema_copies.py tests/api/test_fema_nfhl_connector_api.py tests/api/test_nwi_connector_api.py
cd backend; py -3.12 -m pytest -q tests/api/test_nwi_connector_api.py tests/api/test_fema_nfhl_connector_api.py tests/api/test_live_connector_worker.py
cd backend; py -3.12 -m pytest -q tests/api/test_fema_nfhl_connector_api.py tests/connectors/test_fema_nfhl_connector.py
cd backend; py -3.12 -m pytest -q tests/api/test_connector_review_actions.py tests/connectors/test_review_queue.py
cd backend; py -3.12 -m pytest -q tests/evidence_ledger/test_evidence_schema_contract.py tests/evidence_ledger/test_sqlalchemy_evidence_repo.py tests/connectors/test_fema_nfhl_connector.py tests/reports/test_report_service.py
cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/api/test_fema_nfhl_connector_api.py::test_db_fema_nfhl_approval_feeds_report_api
cd backend; py -3.12 -m pytest -q tests/connectors tests/source_registry
cd backend; py -3.12 -m pytest -q tests/api tests/connectors tests/source_registry
py -3.12 .\scripts\source_readiness.py --priority Must
py -3.12 .\scripts\source_readiness.py --priority Must --json
cd backend; py -3.12 -m pytest -q tests/api tests/test_planning_pack_schema_copies.py
cd backend; py -3.12 -m pytest -q tests/api/test_live_connector_worker.py tests/api/test_fema_nfhl_connector_api.py
cd backend; py -3.12 -m pytest -q tests/reports/test_job_store.py
cd backend; py -3.12 -m pytest -q tests/api/test_async_report_runs.py tests/api/test_report_runs_db.py
cd backend; ruff check app/core app/api app/reports tests/api tests/reports
cd backend; ruff check app/connectors/nwi.py app/connectors/__init__.py tests/connectors/test_nwi_connector.py
cd backend; ruff check app/api tests/api/test_nwi_connector_api.py tests/api/test_fema_nfhl_connector_api.py tests/test_planning_pack_schema_copies.py
cd backend; ruff check app/connectors/live_jobs.py app/api/live_connector_jobs.py app/api/connectors.py app/connectors/__init__.py tests/api/test_nwi_connector_api.py tests/api/test_fema_nfhl_connector_api.py tests/api/test_live_connector_worker.py ../scripts/live_connector_worker.py
cd backend; py -3.12 -m mypy app/core app/api app/reports tests/api tests/reports
cd backend; mypy app/connectors/nwi.py app/connectors/__init__.py tests/connectors/test_nwi_connector.py
cd backend; mypy app/api tests/api/test_nwi_connector_api.py tests/api/test_fema_nfhl_connector_api.py tests/test_planning_pack_schema_copies.py
cd backend; mypy app/connectors/live_jobs.py app/api/live_connector_jobs.py app/api/connectors.py app/connectors/__init__.py tests/api/test_nwi_connector_api.py tests/api/test_fema_nfhl_connector_api.py tests/api/test_live_connector_worker.py ../scripts/live_connector_worker.py
mypy app tests
docker compose config
docker compose build backend
$env:DB_PORT='55432'; docker compose up -d db backend
Invoke-RestMethod -Uri http://127.0.0.1:8000/health
Invoke-RestMethod -Uri http://127.0.0.1:8000/version
Invoke-RestMethod -Uri http://127.0.0.1:8000/metrics
docker compose logs backend --tail 80
docker compose down
.\scripts\verify.ps1
```

Optional DB verification:

```powershell
$env:RUN_DB_SMOKE='1'; cd backend; py -3.12 -m pytest -q tests/api/test_report_runs_db.py
```

## Risks and blockers

- DB-mode async report generation must not reuse a request-scoped SQLAlchemy session.
- `jobs.job_queue` is shared with connector review status; report jobs must use a
  distinct `job_type` and idempotency prefix.
- Docker build verification may be skipped if Docker is unavailable.
- `REVIEWER_ACCOUNTS` must fail closed for blank or malformed entries.
- `REQUIRE_API_KEY=true` without any configured active `API_KEYS` or `API_KEY_SPECS`
  must fail closed on protected endpoints while keeping health/version probes available.
- API-key auth is a production gate, not a complete identity system; rate limiting,
  automatic key rotation, audit events, and per-operator authorization remain separate
  future work.
- The current rate limiter is in-process only. It protects a single running process but
  does not coordinate across multiple workers, hosts, or restarts.
- Runtime metrics are in-memory only and reset on process restart. They are operational
  telemetry, not evidence, claims, or report-run reproducibility data.
- Connector source-use preflight is now stricter than older fixture-era language. A source
  with `unknown`, `unreviewed`, `pending`, `blocked`, or incompatible production-use rights
  is not connector-ready.
- Container runtime smoke covers build, service startup, health, version, and metrics.
  DB-backed API behavior remains covered by `RUN_DB_SMOKE=1` verification; no automatic
  container migration runner has been added.
- The DS-002 FEMA NFHL connector is bounded and contract-compatible, now has a controlled
  reviewer-authenticated API/operator invocation path, and connector review queue items
  can be approved, rejected for fix, requeued, or cancelled by authenticated reviewers.
  Approved connector-run evidence can now reach reports through an explicit lineage and
  review gate. That approval-to-report path is now covered in both in-memory and
  DB-backed API service configurations. `/intake` and `/report-runs` can now run DS-002
  at request time when live connectors are enabled, but they pause report generation
  until the connector review item is approved. Operators can now resume report generation
  with `POST /connector-runs/{ingest_run_id}/report-runs` after approval, without
  re-running the live connector. Reviewer closeout/requeue/cancel actions now append
  durable queue-payload history. DS-002 work can now also be scheduled as durable
  `live_connector_run` jobs and processed by an explicit worker helper or bounded
  supervisor-callable worker command. This slice still does not add an autonomous
  always-on daemon or separate audit-event auth ledger.
- Validate-only live FEMA NFHL smoke checks in this environment returned FEMA transfer-limit
  responses even for small bboxes. The connector converted those into non-retryable
  source-failure evidence as designed; deterministic tests cover the successful feature
  response path without depending on live service availability.
- DS-004 is wired to a reviewer-authenticated operator API route, approved generic
  report-resume path, explicit durable scheduler/worker-dispatch path, and default-off
  request-time `/intake` plus `/report-runs` orchestration. It still has no
  source-specific autonomous scheduling policy. Empty NWI responses are represented as
  source-failure evidence, not as proof that no wetlands/deepwater mapping intersects.
- The live connector job status API is read-only. It does not add retry, requeue, cancel,
  queue mutation, queue dashboard, long-running worker supervision, or report scheduling.
- The NWI-reported acreage is feature area from the source response, not a clipped
  parcel-overlap measurement. Report/user-facing semantics must preserve that caveat
  wherever DS-004 evidence is shown.

## Decision log

- 2026-06-05: Use existing `jobs.job_queue` for report job state instead of adding a
  new migration because it already has the status, timing, payload, and error fields
  needed for Level 10 report job persistence.
- 2026-06-05: Keep file-drop/IPC OMC state out of this plan; it is unrelated to the
  active Level 10 production-hardening continuation.
- 2026-06-05: Use `EvidenceContract.source_ingest_run_id` plus connector review queue
  approval state as the current report eligibility gate for connector-produced evidence,
  without adding a DB migration.
- 2026-06-05: Store reviewer action history in existing connector review queue payloads
  rather than adding a migration; this preserves action sequence durability for queue
  rows while keeping full audit-event auth ledger work out of this slice.
- 2026-06-05: Use existing `jobs.job_queue` for explicit DS-002 live connector scheduling
  instead of adding a migration. The scheduler stores only bounded connector work and
  records the resulting connector review item; it does not create reports or bypass review.
- 2026-06-05: Add a bounded root `scripts/live_connector_worker.py` command instead of
  an autostart daemon. Supervisors can run the command explicitly; the command opens
  fresh DB-backed services per job and commits both succeeded and failed job state.
- 2026-06-05: Keep default worker invocation one-shot, but add explicit polling mode and
  an opt-in Compose `workers` profile for external supervision. The profile processes
  only existing `live_connector_run` jobs and remains outside default Compose startup.
- 2026-06-05: Add DS-004 NWI as a connector-layer-only slice before API/worker/report
  wiring. This gives a second public official live-source connector pattern without
  broadening review-gated downstream semantics.
- 2026-06-05: Promote DS-004 through the reviewer-authenticated operator API and existing
  approved connector report-resume gate before any scheduler/worker/request-time
  automation. This exposes the source to operators while preserving manual review as the
  downstream authority.
- 2026-06-05: Reuse the existing durable `live_connector_run` queue and bounded worker
  helper for DS-004 scheduling instead of adding a second worker queue or migration. The
  worker dispatches by explicit `source_registry_id` and still does not schedule reports
  or bypass connector review.
- 2026-06-05: Add read-only live connector job status through the existing connector API
  rather than a separate queue dashboard. Operators need status visibility, but queue
  mutation/retry policy remains outside this slice.
- 2026-06-05: Add file-backed raw NWI response fixtures before expanding DS-004
  automation. Stable success and empty-response payloads make connector parsing and
  source-failure behavior reproducible without live service availability.
- 2026-06-05: Treat full-gate deprecation warnings as production-hardening debt when the
  fix is a narrow semantic no-op. For 422 validation errors, use the current
  FastAPI/Starlette constant name while preserving the HTTP code and response behavior.
- 2026-06-05: Add the reviewed live connector sequence scheduler as an operator
  convenience, not as an autonomous daemon. It creates four existing durable job types in
  the same DS-001/DS-002/DS-004/DS-003 order as request-time orchestration and leaves
  worker execution, connector review approval, and report creation separate.

## Progress log

- 2026-06-05: Plan created from interrupted session export and current repo state.
- 2026-06-05: Completed settings-backed reviewer auth, backend Docker/Compose wiring,
  structured JSON logging, and Postgres-backed async report job persistence.
- 2026-06-05: Regenerated `docs/planning_pack/api/openapi_stub.yaml` from the live
  FastAPI contract after the full gate exposed OpenAPI parity drift.
- 2026-06-05: Full DB-enabled `.\scripts\verify.ps1` passed; 461 backend tests pass
  with `RUN_DB_SMOKE=1`; ruff and mypy are clean; DB migrations/seeds and smoke pass.
- 2026-06-05: Added default-off production API-key middleware with parser coverage,
  protected API/UI/docs/OpenAPI behavior, public health/version probes, `.env.example`
  settings, and Compose environment wiring.
- 2026-06-05: Full DB-enabled `.\scripts\verify.ps1` passed after API-key auth;
  472 tests are collected, ruff and canonical mypy are clean, migrations/seeds apply,
  and DB smoke passes.
- 2026-06-05: Added default-off fixed-window rate limiting with parser coverage,
  public health/version probes, per-API-key or per-client-host buckets, rate-limit
  headers, `.env.example` settings, and Compose environment wiring.
- 2026-06-05: Full DB-enabled `.\scripts\verify.ps1` passed after rate limiting;
  479 tests are collected, ruff and canonical mypy are clean over 145 source files,
  migrations/seeds apply, and DB smoke passes.
- 2026-06-05: Added structured runtime metrics with route-template aggregation,
  `/metrics` JSON endpoint, API-key/rate-limit composition tests, `ENABLE_METRICS`
  wiring, and planning-pack OpenAPI refresh.
- 2026-06-05: Full DB-enabled `.\scripts\verify.ps1` passed after structured metrics;
  484 tests are collected, ruff and canonical mypy are clean over 148 source files,
  migrations/seeds apply, and DB smoke passes.
- 2026-06-05: Backend image build and Compose runtime smoke passed. The stack served
  `/health`, `/version`, and `/metrics`; `DB_PORT` was added so local host port
  collisions can be avoided.
- 2026-06-05: Added shared source production-use rights helper and aligned connector
  source-use preflight to fail closed on unapproved or unknown source rights before any
  live connector can be attempted.
- 2026-06-05: Full DB-enabled `.\scripts\verify.ps1` passed after connector source-use
  preflight; 493 tests are collected, ruff and canonical mypy are clean over 149 source
  files, migrations/seeds apply, and DB smoke passes.
- 2026-06-05: Added read-only source-readiness audit reporting for all registry rows or
  priority-filtered candidates. Initial MVP `Must` sources reported ready=0 and blocked=8.
- 2026-06-05: Full DB-enabled `.\scripts\verify.ps1` passed after source-readiness
  audit reporting; 497 tests are collected, ruff and canonical mypy are clean over 150
  source files, migrations/seeds apply, and DB smoke passes.
- 2026-06-05: Reviewed FEMA NFHL source rights from official FEMA/NFHL/OpenFEMA sources,
  added `docs/source-reviews/ds-002.md`, updated DS-002 to
  `approved-with-restrictions`, and current MVP `Must` readiness is ready=1 blocked=7.
- 2026-06-05: Full DB-enabled `.\scripts\verify.ps1` passed after DS-002 review;
  499 tests are collected, ruff and canonical mypy are clean over 150 source files,
  migrations/seeds apply, and DB smoke passes.
- 2026-06-05: Re-audited the DS-002 seed path and fixed the static SQL seed to insert
  first-class `attribution_required` plus refresh first-class source usage-rights columns
  on conflict. Full DB-enabled `.\scripts\verify.ps1` passed again; 500 tests are
  collected, ruff and canonical mypy are clean over 150 source files, migrations/seeds
  apply, and DB smoke passes.
- 2026-06-05: Added US-025 bounded DS-002 FEMA NFHL live connector. It queries the
  official effective-data ArcGIS REST layer 28 with EPSG:4326 bbox and feature limits,
  emits spatial-intersection evidence on usable features, emits source-failure evidence
  for no-data/error/malformed/transfer-limit responses, preserves DS-002 caveats, and
  reuses the existing connector provenance/evidence adapters.
- 2026-06-05: Full DB-enabled `.\scripts\verify.ps1` passed after the bounded DS-002
  connector; 513 tests are collected, ruff and canonical mypy are clean over 153 source
  files, migrations/seeds apply, and DB smoke passes.
- 2026-06-05: Added US-026 controlled DS-002 FEMA NFHL API/operator invocation at
  `POST /connector-runs/fema-nfhl/query-bbox`. The route requires reviewer auth and a
  registered area, invokes DS-002 only, records retrieval provenance, persists
  ledger-safe spatial or source-failure evidence, enqueues connector review status, and
  does not create claims, reports, scheduler jobs, or `/intake` shortcuts.
- 2026-06-05: Full DB-enabled `.\scripts\verify.ps1` passed after controlled DS-002
  API invocation; 518 tests are collected, ruff and canonical mypy are clean over 154
  source files, migrations/seeds apply, and DB smoke passes.
- 2026-06-05: Added US-027 connector review closeout actions. Authenticated reviewers
  can approve connector runs for QA, request fixture/source fixes with reasons, requeue
  fixed failed items, or cancel nonfinal reviews. The transitions mutate only
  `jobs.job_queue` / connector review queue state and record latest reviewer decision
  details in the queue payload.
- 2026-06-05: Full DB-enabled `.\scripts\verify.ps1` passed after connector review
  closeout actions; 523 tests are collected, ruff and canonical mypy are clean over 154
  source files, migrations/seeds apply, and DB smoke passes.
- 2026-06-05: Added US-028 approved connector evidence report gating. DS-002 connector
  evidence and source-failure evidence now carry `source_ingest_run_id`, the SQLAlchemy
  evidence repository round-trips that lineage through metadata, and reports exclude
  connector-lineage evidence unless the matching review queue item is succeeded with an
  `approve_for_connector_qa` decision.
- 2026-06-05: Full DB-enabled `.\scripts\verify.ps1` passed after US-028; 525 tests
  are collected, ruff and canonical mypy are clean over 154 source files,
  migrations/seeds apply, and DB smoke passes.
- 2026-06-05: Added an API-level regression proving the manual DS-002 operator sequence
  can feed reports after approval: query bbox, approve for connector QA, create report,
  fetch report, and observe `FLOOD_001` plus connector evidence lineage.
- 2026-06-05: Full DB-enabled `.\scripts\verify.ps1` passed after the API-level
  operator regression; 526 tests are collected, ruff and canonical mypy remain clean
  over 154 source files, migrations/seeds apply, and DB smoke passes.
- 2026-06-05: Added a DB-backed DS-002 approval-to-report API regression proving the
  manual operator sequence across SQLAlchemy services: area registration, FEMA bbox
  query, connector review approval, report creation, report retrieval, queue state, and
  connector-lineage evidence persistence.
- 2026-06-05: Hardened SQLAlchemy source mapping for stale local source rows with
  placeholder homepage URLs and aligned FEMA NFHL success evidence `source_date` with
  the DB `date` column while preserving access timestamps via `observed_at` and
  retrieval metrics.
- 2026-06-05: Full DB-enabled `.\scripts\verify.ps1` passed after the DB-backed
  DS-002 approval-to-report regression; 528 tests are collected, ruff and canonical
  mypy remain clean over 154 source files, migrations/seeds apply, and DB smoke passes.
- 2026-06-05: Added US-029 request-time DS-002 orchestration for `/intake` and
  `/report-runs` behind `ENABLE_LIVE_CONNECTORS`. Those entry points now run bounded
  DS-002 and return `pending_connector_review` without creating report jobs until the
  connector review item is approved.
- 2026-06-05: DB-backed automatic orchestration regression proves no `report_run` job is
  inserted before DS-002 approval, and that a second `/report-runs` call after approval
  creates a report including `FLOOD_001` plus connector evidence lineage.
- 2026-06-05: Full DB-enabled `.\scripts\verify.ps1` passed after request-time DS-002
  orchestration; 532 tests are collected, ruff and canonical mypy are clean over 155
  source files, migrations/seeds apply, and DB smoke passes.
- 2026-06-05: Added explicit post-approval report resume at
  `POST /connector-runs/{ingest_run_id}/report-runs`. Connector review packets and queue
  payloads now carry the originating `area_id`; the resume endpoint requires reviewer
  auth and `approve_for_connector_qa`, derives the report area from queue state, and
  schedules the normal async report job without re-fetching DS-002.
- 2026-06-05: Full DB-enabled `.\scripts\verify.ps1` passed after connector report
  resume; 534 tests are collected, ruff and canonical mypy are clean over 155 source
  files, migrations/seeds apply, and DB smoke passes.
- 2026-06-05: Added durable connector reviewer action history in queue payloads.
  `approve_for_connector_qa` and `request_fixture_fix` update `review_decision` and append
  the same action to `review_action_history`; `requeue_after_fix` and `cancel_review`
  append authenticated reviewer id, reason, and timestamp without replacing the latest
  approval/fix decision.
- 2026-06-05: Full DB-enabled `.\scripts\verify.ps1` passed after reviewer action history;
  536 tests are collected, ruff and canonical mypy are clean over 155 source files,
  migrations/seeds apply, and DB smoke passes.
- 2026-06-05: Added US-030 explicit durable DS-002 live connector scheduling. Operators can
  enqueue bounded DS-002 work with `POST /connector-runs/fema-nfhl/schedule-bbox`; workers
  call `run_next_live_connector_job(...)` to lease one `live_connector_run`, execute the
  existing DS-002 orchestration, and record the connector review item without creating a
  report job.
- 2026-06-05: Planning-pack OpenAPI was regenerated after adding the schedule route.
- 2026-06-05: Full DB-enabled `.\scripts\verify.ps1` passed after explicit DS-002
  scheduling; 538 tests are collected, ruff and canonical mypy are clean over 157 source
  files, migrations/seeds apply, and DB smoke passes.
- 2026-06-05: Added US-031 bounded supervised DS-002 live connector worker command at
  `scripts/live_connector_worker.py`. The command processes queued `live_connector_run`
  jobs through fresh DB-backed services, defaults to one job, supports JSON summaries,
  commits succeeded and failed job state, exits nonzero for processed job failures, and
  does not create reports or bypass connector review.
- 2026-06-05: Full DB-enabled `.\scripts\verify.ps1` passed after the bounded worker
  command; 541 tests are collected, ruff and canonical mypy are clean over 158 source
  files, migrations/seeds apply, DB smoke passes, source readiness remains
  `sources=8 ready=1 blocked=7`, and no Docker services remain running.
- 2026-06-05: Added US-032 opt-in supervised polling/profile packaging for the DS-002
  worker. `scripts/live_connector_worker.py` now supports `--poll-seconds` plus
  `--idle-polls`; `backend/Dockerfile` copies the root worker script into the runtime
  image; `docker-compose.yml` exposes `live-connector-worker` under the `workers`
  profile with `restart: unless-stopped`; `.env.example` documents the worker controls.
- 2026-06-05: Full DB-enabled `.\scripts\verify.ps1` passed after the worker profile;
  543 tests are collected, ruff and canonical mypy are clean over 158 source files,
  migrations/seeds apply, DB smoke passes, source readiness remains
  `sources=8 ready=1 blocked=7`, default Compose config excludes the worker, profile
  Compose config includes it, backend image build passes, and containerized worker help
  passes.
- 2026-06-05: Added US-033 DS-001 USGS The National Map source-rights review. DS-001
  is now approved-with-restrictions for physical screening/base-layer use only; registry,
  planning-pack mirror, SQL seed, source-readiness tests, and source-seed tests now
  reflect DS-001 plus DS-002 as the two source-rights-ready `Must` sources.
- 2026-06-05: Focused DS-001 source-readiness validation passed: source readiness
  reports `sources=8 ready=2 blocked=6`, source-readiness/source-seed tests pass, and
  focused ruff/mypy are clean for the touched source-registry tests and scripts.
- 2026-06-05: Full DB-enabled `.\scripts\verify.ps1` passed after the DS-001 review;
  544 tests are collected, ruff and canonical mypy are clean over 158 source files,
  migrations/seeds apply, DB smoke passes, source-readiness JSON reports DS-001 and
  DS-002 ready with six `Must` sources still blocked, and no Docker services or worker-run
  containers remain running.
- 2026-06-05: Added US-034 DS-003 USDA Web Soil Survey/SSURGO source-rights review.
  DS-003 is now approved-with-restrictions for soil/septic/ag screening use only;
  registry, planning-pack mirror, SQL seed, source-readiness tests, and source-seed tests
  now reflect DS-001, DS-002, and DS-003 as source-rights-ready `Must` sources.
- 2026-06-05: Focused DS-003 source-readiness validation passed: source readiness
  reports `sources=8 ready=3 blocked=5`, source-readiness/source-seed tests pass, and
  focused ruff/mypy are clean for the touched source-registry tests and scripts.
- 2026-06-05: Full DB-enabled `.\scripts\verify.ps1` passed after the DS-003 review;
  545 tests are collected, ruff and canonical mypy are clean over 158 source files,
  migrations/seeds apply, DB smoke passes, source-readiness JSON reports DS-001,
  DS-002, and DS-003 ready with five `Must` sources still blocked, and no Docker services
  or worker-run containers remain running.
- 2026-06-05: Added US-035 DS-004 National Wetlands Inventory source-rights review.
  DS-004 is now approved-with-restrictions for wetland/deepwater screening use only;
  registry, planning-pack mirror, SQL seed, source-readiness tests, and source-seed tests
  now reflect DS-001, DS-002, DS-003, and DS-004 as source-rights-ready `Must` sources.
- 2026-06-05: Focused DS-004 source-readiness validation passed: source readiness
  reports `sources=8 ready=4 blocked=4`, source-readiness/source-seed tests pass, and
  focused ruff/mypy are clean for the touched source-registry tests and scripts.
- 2026-06-05: Full DB-enabled `.\scripts\verify.ps1` passed after the DS-004 review;
  546 tests are collected, ruff and canonical mypy are clean over 158 source files,
  migrations/seeds apply, DB smoke passes, source-readiness JSON reports DS-001,
  DS-002, DS-003, and DS-004 ready with four `Must` sources still blocked, and no Docker
  services or worker-run containers remain running.
- 2026-06-05: Added US-036 bounded connector-layer DS-004 National Wetlands Inventory
  connector. It queries the official USFWS-linked Wetlands ArcGIS REST layer 0 with a
  small EPSG:4326 bbox and feature limit, emits wetlands spatial-intersection evidence
  for usable features, emits source-failure evidence for no-data/error/malformed/transfer
  limit cases, keeps NWI caveats screening-only, and reuses existing connector provenance
  and evidence-ingestion adapters.
- 2026-06-05: Focused DS-004 connector validation passed: 13 connector tests pass, ruff
  is clean for `app/connectors/nwi.py`, connector exports, and the NWI tests, and mypy is
  clean for the same touched paths.
- 2026-06-05: Full DB-enabled `.\scripts\verify.ps1` passed after the bounded DS-004
  connector; 559 tests are collected, ruff and canonical mypy are clean over 160 source
  files, migrations/seeds apply, DB smoke passes, source-readiness JSON remains
  `sources=8 ready=4 blocked=4`, and no Docker services or worker-run containers remain
  running.
- 2026-06-05: Added US-037 controlled DS-004 National Wetlands Inventory API/operator
  invocation at `POST /connector-runs/nwi/query-bbox`. The route requires reviewer auth
  and a registered area, invokes DS-004 only, records retrieval provenance, persists
  ledger-safe wetlands spatial or source-failure evidence, enqueues connector review
  status, and does not add DS-004 scheduling, workers, request-time orchestration, or an
  autonomous daemon.
- 2026-06-05: Added an API regression proving approved DS-004 connector evidence can feed
  the existing connector report-resume path without re-fetching NWI and yields the
  existing screening-only `WETLAND_001` claim after `approve_for_connector_qa`.
- 2026-06-05: Full DB-enabled `.\scripts\verify.ps1` passed after the DS-004 API path;
  565 tests are collected, ruff and canonical mypy are clean over 161 source files,
  migrations/seeds apply, DB smoke passes, source-readiness JSON remains
  `sources=8 ready=4 blocked=4`, OpenAPI parity is refreshed, and no Docker services or
  worker-run containers remain running.
- 2026-06-05: Added US-038 explicit durable DS-004 live connector scheduling and worker
  dispatch. Operators can enqueue bounded DS-004 work with
  `POST /connector-runs/nwi/schedule-bbox`; the shared live connector worker leases the
  durable job, dispatches by `source_registry_id`, runs the existing DS-004 orchestration
  path, and records the connector review item without fetching at schedule time,
  creating reports, or bypassing review.
- 2026-06-05: Focused DS-004 scheduler validation passed: DS-004/NWI, DS-002/FEMA, worker
  command, and OpenAPI parity tests passed; focused ruff and mypy passed for the shared
  live job store, API dispatcher, connector routes, connector exports, and affected API
  tests.
- 2026-06-05: Full DB-enabled `.\scripts\verify.ps1` passed after the DS-004 durable
  scheduler slice; 567 tests are collected, ruff and canonical mypy are clean over 161
  source files, migrations/seeds apply, DB smoke passes, source-readiness JSON remains
  `sources=8 ready=4 blocked=4`, and no Docker services or worker-run containers remain
  running.
- 2026-06-05: Added US-039 read-only live connector job status at
  `GET /connector-runs/live-jobs/{job_id}`. The route requires reviewer auth, returns
  durable scheduled job state before and after worker execution, and does not mutate
  queue state, fetch live sources, or schedule reports.
- 2026-06-05: Focused job-status validation passed: DS-004/NWI, DS-002/FEMA, worker
  command, and OpenAPI parity tests passed; focused ruff and mypy passed for
  `backend/app/api/connectors.py` and `backend/tests/api/test_nwi_connector_api.py`.
- 2026-06-05: Full DB-enabled `.\scripts\verify.ps1` passed after the live connector
  job-status endpoint; 569 tests are collected, ruff and canonical mypy are clean over
  161 source files, migrations/seeds apply, DB smoke passes, source-readiness JSON
  remains `sources=8 ready=4 blocked=4`, and no Docker services or worker-run containers
  remain running.
- 2026-06-05: Added US-040 explicit durable DS-003 live connector scheduling and worker
  dispatch. Operators can enqueue bounded DS-003 work with
  `POST /connector-runs/ssurgo/schedule-bbox`; the shared live connector worker leases
  the durable job, dispatches by `source_registry_id`, runs the existing DS-003
  orchestration path with `max_rows`, and records the connector review item without
  fetching at schedule time, creating reports, or bypassing review.
- 2026-06-05: Full DB-enabled `.\scripts\verify.ps1` passed after the DS-003 durable
  scheduler slice; 595 tests are collected, ruff and canonical mypy are clean over 164
  source files, migrations/seeds apply, DB smoke passes, source-readiness JSON remains
  `sources=8 ready=4 blocked=4`, and no Docker services or worker-run containers remain
  running.
- 2026-06-05: Added US-041 request-time DS-004 orchestration after DS-002 approval.
  When `ENABLE_LIVE_CONNECTORS=true`, `/intake` and `/report-runs` now use the shared
  request-time live connector sequence: DS-002 runs first, DS-004 runs after DS-002 is
  approved, and report jobs are created only after both connector review items are
  approved. The connector-run resume endpoint remains the explicit manual one-connector
  report path.
- 2026-06-05: Full DB-enabled `.\scripts\verify.ps1` passed after US-041; 596 tests are
  collected, ruff and canonical mypy are clean over 164 source files, migrations/seeds
  apply, DB smoke passes, source-readiness JSON remains `sources=8 ready=4 blocked=4`,
  and no Docker services or worker-run containers remain running.
- 2026-06-05: Added US-042 request-time DS-003 orchestration after DS-004 approval.
  When `ENABLE_LIVE_CONNECTORS=true`, `/intake` and `/report-runs` now use the shared
  request-time live connector sequence: DS-002 first, DS-004 after DS-002 approval,
  DS-003 after DS-004 approval, and report jobs only after all three connector review
  items are approved. Approved DS-003 report integration emits an UNKNOWN
  `SOIL_NOT_EVALUATED` screening-review claim and does not assert septic approval, perc
  results, soil suitability, permitting, buildability, lending, appraisal, or investment
  conclusions.
- 2026-06-05: Full DB-enabled `.\scripts\verify.ps1` passed after US-042; 597 tests are
  collected, ruff and canonical mypy are clean over 164 source files, migrations/seeds
  apply, DB smoke passes, source-readiness JSON remains `sources=8 ready=4 blocked=4`,
  and no Docker services or worker-run containers remain running.
- 2026-06-05: Added US-043 bounded connector-layer DS-001 USGS TNM EPQS
  terrain-relief screening. It samples the official EPQS JSON service at the bbox
  center and corners, emits one low-confidence `DERIVED_METRIC` screening value, emits
  source-failure evidence for no-data/error/malformed cases, preserves USGS caveats,
  and reuses existing retrieval provenance plus evidence-ingestion adapters without
  adding API/operator, scheduler, request-time, report, or buildability conclusions.
- 2026-06-05: Full DB-enabled `.\scripts\verify.ps1` passed after US-043; 608 tests are
  collected, ruff and canonical mypy are clean over 166 source files, migrations/seeds
  apply, DB smoke passes, source-readiness JSON remains `sources=8 ready=4 blocked=4`,
  and no Docker services or worker-run containers remain running.
- 2026-06-05: Added US-044 controlled DS-001 USGS TNM EPQS API/operator invocation at
  `POST /connector-runs/usgs-tnm/query-bbox`. The route requires reviewer auth and a
  registered area, invokes DS-001 only, records retrieval provenance, persists
  terrain-relief derived metric or source-failure evidence, enqueues connector review
  status, refreshes OpenAPI parity, and does not create scheduler jobs, request-time
  runs, reports, or buildability conclusions.
- 2026-06-05: Full DB-enabled `.\scripts\verify.ps1` passed after US-044; 614 tests are
  collected, ruff and canonical mypy are clean over 167 source files, migrations/seeds
  apply, DB smoke passes, source-readiness JSON remains `sources=8 ready=4 blocked=4`,
  and no Docker services or worker-run containers remain running.
- 2026-06-05: Added US-045 explicit durable DS-001 live connector scheduling and worker
  dispatch. Operators can enqueue bounded DS-001 work with
  `POST /connector-runs/usgs-tnm/schedule-bbox`; the shared live connector worker leases
  the durable job, dispatches by `source_registry_id`, runs the existing DS-001
  orchestration path with `max_sample_points`, and records the connector review item
  without fetching at schedule time, creating reports, or bypassing review.
- 2026-06-05: Full DB-enabled `.\scripts\verify.ps1` passed after US-045; 616 tests are
  collected, ruff and canonical mypy are clean over 167 source files, migrations/seeds
  apply, DB smoke passes, source-readiness JSON remains `sources=8 ready=4 blocked=4`,
  and no Docker services or worker-run containers remain running.
- 2026-06-05: Added US-046 request-time DS-001 orchestration. When
  `ENABLE_LIVE_CONNECTORS=true`, `/intake` and `/report-runs` now run the shared
  request-time live connector sequence as DS-001 first, then DS-002 after DS-001
  approval, DS-004 after DS-002 approval, and DS-003 after DS-004 approval. Reports are
  created only after all four connector review items are approved. Approved DS-001
  evidence may enter reports as buildability-domain terrain screening evidence, but it
  does not create a DS-001 claim or terrain/buildability conclusion.
- 2026-06-05: Focused US-046 validation passed:
  `RUN_DB_SMOKE=1 py -3.12 -m pytest -q tests\api\test_usgs_tnm_connector_api.py
  tests\api\test_fema_nfhl_connector_api.py tests\api\test_nwi_connector_api.py
  tests\api\test_ssurgo_connector_api.py tests\api\test_live_connector_worker.py` passed
  with 45 tests; ruff passed; mypy passed for `app\api\live_connectors.py` and
  `tests\api\test_fema_nfhl_connector_api.py`.
- 2026-06-05: Full DB-enabled `.\scripts\verify.ps1` passed after US-046; 616 tests are
  collected, ruff and canonical mypy are clean over 167 source files, migrations/seeds
  apply, DB smoke passes, source-readiness JSON remains `sources=8 ready=4 blocked=4`,
  `git diff --check` exits 0 with only CRLF warnings on generated/state files, and no
  Docker services or worker-run containers remain running.
- 2026-06-05: Added US-047 DS-004 file-backed raw NWI response fixtures for
  representative success and empty-response source-failure behavior. Added worker CLI
  help coverage proving DS-001, DS-002, DS-003, and DS-004 are named as supported queued
  source jobs.
- 2026-06-05: Focused US-047 tests passed: 21 NWI connector and live-worker tests; ruff
  passed for the touched NWI/worker test paths plus `scripts/live_connector_worker.py`;
  mypy passed for the touched NWI/worker test paths.
- 2026-06-05: Broader DS-004 API/connector/worker regression and full DB-enabled
  `.\scripts\verify.ps1` passed after US-047; 619 tests are collected, canonical mypy
  remains clean over 167 source files, source readiness remains
  `sources=8 ready=4 blocked=4`, `git diff --check` reports only CRLF warnings on
  generated/state files, and no Docker services or worker-run containers remain running.
- 2026-06-05: Added US-048 API 422 status constant deprecation cleanup across the API
  route modules. Warning-producing API tests passed with `-W error::DeprecationWarning`;
  focused ruff/mypy passed; full DB-enabled `.\scripts\verify.ps1` passed without the
  prior 422 deprecation warning summary. Test collection remains 619 tests, source
  readiness remains `sources=8 ready=4 blocked=4`, `git diff --check` reports only CRLF
  warnings on generated/state files, and no Docker services or worker-run containers
  remain running.
- 2026-06-05: Added US-049 reviewer-authenticated live connector sequence scheduling at
  `POST /connector-runs/live-sequence/schedule-bbox`, with ADR
  `docs/adr/live-sequence.md`. The route enqueues ordered DS-001, DS-002, DS-004, and
  DS-003 jobs, returns the sequence policy id plus ordered job records, and stays
  side-effect-free for live fetches, evidence, review approval, and reports. The
  endpoint uses a source-neutral bbox request schema rather than reusing a FEMA-specific
  public model.
- 2026-06-05: Updated `docs/runbooks/mvp_operator.md` so the operator-facing workflow no
  longer describes the current Level 10 app as fixture-only or completely
  unauthenticated. It now points operators to the reviewed live-sequence scheduler and
  preserves screening-only/review-gated limitations.
- 2026-06-05: Regenerated `docs/planning_pack/api/openapi_stub.yaml` from
  `create_app().openapi()` after US-049 and after the neutral sequence bbox schema
  cleanup. Focused sequence scheduler tests, OpenAPI parity, broader connector
  API/worker regressions, focused ruff/mypy, and full
  DB-enabled `.\scripts\verify.ps1` passed; 622 tests are collected, source readiness
  remains `sources=8 ready=4 blocked=4`, `git diff --check` reports only CRLF warnings
  on generated/state files, and no Docker services or worker-run containers remain
  running.
- 2026-06-05: Added US-050 reviewer-authenticated failed report job retry at
  `POST /report-runs/{report_run_id}/retry`. The route requires reviewer service-account
  headers, accepts only failed report jobs, preserves the failed job, creates a new queued
  report job from the failed job's stored area and intent, and records
  `retry_of_report_run_id` lineage in in-memory and DB-backed job stores.
- 2026-06-05: Full DB-enabled `.\scripts\verify.ps1` passed after US-050; 627 tests are
  collected, source readiness remains `sources=8 ready=4 blocked=4`, `git diff --check`
  reports only CRLF warnings on generated/state files, and no Docker services or
  worker-run containers remain running.
- 2026-06-05: Added US-051 backup/restore proof scripts and runbook. The Windows script
  validated a dump/restore cycle from the configured source DB into
  `land_diligence_restore_check`, ran `scripts/db_smoke_check.py` against the restored
  database, reported `backup/restore check: ok`, and dropped the restore DB. The scripts
  fail closed unless the restore DB name starts with `land_diligence_restore_check`.
- 2026-06-05: Full DB-enabled `.\scripts\verify.ps1` passed after US-051; 627 tests are
  collected, source readiness remains `sources=8 ready=4 blocked=4`, `git diff --check`
  reports only CRLF warnings on generated/state files, no Docker services or worker-run
  containers remain running, and a Docker psql query confirmed the restore-check database
  is absent after cleanup.
- 2026-06-05: Added US-052 reviewer-authenticated operator queue health at
  `GET /operations/queue-health`. The route aggregates in-memory and DB-backed
  `report_run` and `live_connector_run` status counts plus oldest queued age without
  leasing jobs, retrying jobs, fetching live sources, persisting evidence, or creating
  reports. Focused tests, ruff, and mypy passed for the touched API/store files.
- 2026-06-05: Added US-053 DB-backed deployment smoke automation. `USE_DB_SERVICES`
  now lets the deployed `app.main:app` use Postgres-backed services, Compose opts into
  that mode with `COMPOSE_USE_DB_SERVICES=true`, and deployment smoke scripts exercise
  health, version, metrics, queue health, and an area-to-report HTTP workflow against an
  isolated Compose project. The Windows smoke initially exposed missing DB readiness and
  repeated-migration idempotence issues; `scripts/run_deployment_smoke.ps1` now waits for
  `pg_isready`, and `db/migrations/0001_initial_spine.sql` now guards
  `rule_execution_report_fk`. Final deployment smoke, focused tests, ruff, mypy, and full
  DB-enabled `.\scripts\verify.ps1` passed.
- 2026-06-05: Added US-054 incident response and rollback proof. The runbook names
  severity levels, incident owner roles, escalation criteria, deployment rollback,
  database rollback/mitigation, connector outage handling, queue/report failure handling,
  recovery criteria, and closure records. The validate-only check verifies required
  artifacts and runbook sections, runs `docker compose config --quiet` when Docker is
  available, and checks source-readiness JSON shape. Focused tests, the Windows
  incident/rollback proof, ruff, mypy, and full DB-enabled `.\scripts\verify.ps1`
  passed; 638 tests are collected and source readiness remains `sources=8 ready=4
  blocked=4`.
- 2026-06-05: Added US-055 repo-local alert rules for high-severity failures and stale
  source metadata. `config/ops_alert_rules.yaml` maps SEV0 safety-contract failure, SEV1
  health/deployment/DB/restore failures, SEV2 metrics/queue/live-connector failures,
  source-readiness ready-count drops, and stale source-registry `Last Checked At`
  metadata to owners, escalation, runbooks, and validation proofs.
  `scripts/run_alert_rules_check.ps1` validates the rule catalog, referenced proof
  artifacts, source-readiness JSON shape, Must-source freshness metadata, and Compose
  config when Docker is available. Focused tests, the Windows alert-rules proof, ruff,
  mypy, PowerShell parser validation, and full DB-enabled `.\scripts\verify.ps1` passed;
  642 tests are collected and source readiness remains `sources=8 ready=4 blocked=4`.
- 2026-06-05: Added US-056 CI supply-chain dependency vulnerability scanning and update
  hygiene. `.github/workflows/ci.yml` now has a `supply-chain` job that installs the
  backend dependency environment and runs `pip-audit --local`; `.github/dependabot.yml`
  requests weekly updates for GitHub Actions and backend Python dependency metadata.
  `scripts/run_supply_chain_check.ps1` validates the CI job, Dependabot scope, and
  runbook limits. Focused tests, the Windows supply-chain proof, ruff, mypy, PowerShell
  parser validation, and full DB-enabled `.\scripts\verify.ps1` passed; 645 tests are
  collected and source readiness remains `sources=8 ready=4 blocked=4`.
- 2026-06-05: Added US-057 repo-local cost monitoring catalog and guardrail proof.
  `config/ops_cost_monitoring.yaml` covers compute, storage, LLM-if-used, maps,
  geocoding, and data vendors; the Windows check validates report `cost_metrics`
  schema, planning cost inputs, and that DS-017 remains blocked without vendor
  cost/license review. `config/ops_alert_rules.yaml` now includes a SEV2
  `cost_monitoring_check_failed` rule. Focused tests, the Windows cost-monitoring proof,
  ruff, mypy, PowerShell parser validation, and full DB-enabled `.\scripts\verify.ps1`
  passed; 650 tests are collected, canonical mypy is clean over 176 source files, and
  source readiness remains `sources=8 ready=4 blocked=4`.
- 2026-06-05: Added US-058 backend production dependency provenance proof.
  `backend/requirements-prod.lock` pins the backend runtime dependency closure for
  CPython 3.12 manylinux binary wheels with SHA-256 hashes, and
  `docs/sbom/backend-prod-sbom.json` mirrors that component set as a repo-local
  CycloneDX SBOM. `scripts/run_provenance_check.ps1` validates the lock, SBOM, CI
  wiring, and a hash-checked pip dry run. Focused tests, the Windows provenance proof,
  the updated supply-chain proof, ruff, mypy, PowerShell parser validation, and full
  DB-enabled `.\scripts\verify.ps1` passed; 653 tests are collected, canonical mypy is
  clean over 177 source files, and source readiness remains `sources=8 ready=4 blocked=4`.
- 2026-06-05: Added US-059 backend container image/base-image vulnerability scan proof.
  `.github/workflows/ci.yml` now includes `container-image-scan`, which builds
  `backend/Dockerfile` and scans `local://land-diligence-backend:${{ github.sha }}` with
  `docker/scout-action@v1` for critical/high CVEs using `exit-code: true`.
  `scripts/run_container_scan_check.ps1` validates the CI job, Dockerfile base image,
  `.dockerignore` context boundaries, and runbook limits. Focused tests, the Windows
  container scan proof, updated supply-chain proof, ruff, mypy, PowerShell parser
  validation, and full DB-enabled `.\scripts\verify.ps1` passed; 657 tests are collected,
  canonical mypy is clean over 178 source files, and source readiness remains
  `sources=8 ready=4 blocked=4`.
- 2026-06-05: Added US-060 digest-pinned backend Docker base-image proof.
  `backend/Dockerfile` now pins `python:3.12-slim` to OCI index digest
  `sha256:090ba77e2958f6af52a5341f788b50b032dd4ca28377d2893dcf1ecbdfdfe203`, verified
  from live `docker buildx imagetools inspect python:3.12-slim` output before editing.
  `scripts/run_container_scan_check.ps1` and the container scan artifact tests now fail
  closed unless that pinned base image is present, and the runbook records the digest
  refresh boundary. Focused tests, the Windows container scan proof, ruff, mypy, an
  actual `docker build -f backend/Dockerfile -t land-diligence-backend:pinned-check .`,
  and full DB-enabled `.\scripts\verify.ps1` passed; canonical mypy remains clean over
  178 source files.
- 2026-06-05: Added US-061 GitHub dependency lock/SBOM artifact attestation proof.
  `.github/workflows/ci.yml` now has a `dependency-attestations` job with `contents:
  read`, `id-token: write`, `attestations: write`, and `artifact-metadata: write`.
  The job validates dependency provenance first, then uses `actions/attest@v4` to create
  a provenance attestation for `backend/requirements-prod.lock` and
  `docs/sbom/backend-prod-sbom.json`, plus an SBOM attestation binding
  `docs/sbom/backend-prod-sbom.json` to the production lock subject. Focused tests, the
  Windows provenance and supply-chain proofs, ruff, mypy, PowerShell parser validation,
  and full DB-enabled `.\scripts\verify.ps1` passed; canonical mypy remains clean over
  178 source files.
- 2026-06-05: Added US-062 report cost metrics zero-dollar attribution proof.
  Generated report `artifact_metadata.cost_metrics` now requires and emits non-negative
  USD-cent and reviewer-minute fields for estimated total, compute, storage, LLM, map
  tiles, geocoding, paid data, and human review. Current local-only paths set those
  fields to `0`; paid paths remain disabled or blocked until approved metering exists.
  The report repository fills missing attribution defaults when persisting older/custom
  report metadata while preserving extension fields. Focused cost-monitoring proof,
  report schema/service/repository/regression/API tests, ruff, mypy, PowerShell parser
  validation, and full DB-enabled `.\scripts\verify.ps1` passed; 659 tests are
  collected, canonical mypy remains clean over 178 source files, source readiness remains
  `sources=8 ready=4 blocked=4`, `git diff --check` reports only CRLF warnings on
  generated/state files, and no Docker services or worker-run containers remain running.
- 2026-06-05: Added US-063 repo-local release readiness catalog and validate-only proof.
  `config/release_readiness.yaml` gathers the current verification, DB, deployment
  smoke, dependency provenance, supply-chain, container scan, backup/restore, incident,
  alerting, cost, and source-readiness proof surfaces into one release gate catalog.
  `scripts/run_release_readiness_check.ps1` and `.sh` validate the catalog, required CI
  jobs, current Must-source readiness counts, and explicit release blockers without
  creating a package, pushing an image, or claiming hosted deployment. Focused release
  readiness proof, artifact tests, ruff, mypy, and PowerShell parser validation passed.
- 2026-06-05: Added US-064 repo-local access-control posture catalog and validate-only
  proof. `config/access_control.yaml` records current API-key middleware, local
  reviewer service-account auth, reviewer-authenticated operator routes, intentionally
  public health/version routes, and explicit production auth/RBAC blockers.
  `scripts/run_access_control_check.ps1` and `.sh` validate the catalog, auth authority
  files, failure-mode test coverage, protected-route reviewer dependencies, the
  `access-control` CI job, and runbook limits without claiming full user identity,
  OAuth/OIDC, key rotation, or role-scoped authorization. Focused access-control and
  release-readiness proofs, artifact/auth tests, ruff, mypy, PowerShell parser
  validation, and full DB-enabled `.\scripts\verify.ps1` passed; 668 tests are
  collected, canonical mypy is clean over 180 source files, source readiness remains
  `sources=8 ready=4 blocked=4`, `git diff --check` reports only CRLF warnings on
  generated/state files, and no Docker services or worker-run containers remain running.
- 2026-06-05: Added US-065 scoped reviewer service-account authorization for protected
  operator routes. Reviewer principals now carry explicit `REVIEWER_ACCOUNT_SCOPES`;
  custom reviewer accounts fail closed without scopes; connector invocation/scheduling
  requires `connector:run`, connector review decisions require `connector:review`,
  queue/live-job health reads require `operations:read`, report retry requires
  `report:retry`, and manual approved-connector report creation requires `report:run`.
  The access-control catalog and proof now validate this scoped local substrate. US-083
  later reclassified full user auth/RBAC, OAuth/OIDC, user accounts, key rotation, and
  hosted identity-provider authorization as out-of-scope for local-only operation.
- 2026-06-05: Added US-066 local release package builder, manifest, and validate-only
  proof. `config/release_package.yaml` defines the package boundary,
  `scripts/build_release_package.ps1` and `.sh` create a local ZIP plus JSON manifest under
  `local_artifacts/releases`, and `scripts/run_release_package_check.ps1` and `.sh`
  validate package includes/excludes, builder no-delete/no-overwrite behavior, and
  runbook limits. A clean package build produced
  `local_artifacts/releases/land-diligence-us066-20260606T013648Z.zip` with a sibling
  manifest; the package excludes `.git`, `local_artifacts`, and secret-like `.env`
  files while keeping `.env.example`.
- 2026-06-05: Added US-067 registry image publication readiness catalog and
  validate-only proof. `config/image_publication.yaml` records the backend image source,
  required release/deployment/scan gates, required post-publish evidence, and explicit
  registry/deployment/attestation blockers. `scripts/run_image_publication_check.ps1`
  and `.sh` validate the boundary and ensure validate-only CI/scripts do not push,
  registry-login, or sign images. `docs/runbooks/image_publication.md` records the
  operator workflow and limits. The proof is wired into release readiness and CI as a
  read-only `image-publication` job; it does not push a registry image, create a hosted
  deployment, sign an image SBOM, or publish registry-image attestations.
- 2026-06-05: Added US-068 hosted deployment readiness catalog and validate-only proof.
  `config/hosted_deployment.yaml` recorded pre-deploy gates, runtime inputs, hosted
  runtime evidence, and hosted platform/DNS/TLS/secrets/database/billing/alerting
  blockers at the time. US-083 later reclassified hosted deployment as an optional
  future-hosting checklist, removed it from the local-only release CI path, and kept the
  proof validate-only.
- 2026-06-05: Added US-069 raw-or-sha256 configured secret specs for API-key and local
  reviewer service-account auth. `backend/app/api/secret_specs.py` normalizes raw or
  `sha256:<64-hex>` secret specs and compares provided secrets through constant-time
  raw or SHA-256 digest matching. `backend/app/api/api_key_auth.py` now accepts hashed
  `API_KEYS`; `backend/app/api/reviewer_auth.py` now accepts hashed reviewer tokens from
  `REVIEWER_ACCOUNTS`; `backend/app/core/config.py` validates malformed hash specs
  fail closed. Access-control docs, catalog, proofs, and tests now cover hashed
  configured secrets. This reduces production secret exposure in environment config, but
  does not add key rotation, user accounts, OAuth/OIDC, hosted identity, or full RBAC.
- 2026-06-05: Added US-070 configured static API-key lifecycle specs.
  `API_KEY_SPECS` accepts comma-separated `id|status|secret` entries where status is
  `active` or `retired`, secrets may be raw or `sha256:<64-hex>`, active specs
  authenticate, retired specs do not, and malformed or duplicate lifecycle entries fail
  closed. Access-control docs, catalog, proofs, `.env.example`, Compose, and hosted
  deployment readiness now treat this as the implemented static rotation substrate while
  keeping automatic rotation, external secret-manager integration, per-key usage audit,
  user accounts, OAuth/OIDC, hosted identity, and full RBAC out of scope.
- 2026-06-05: Added US-071 structured API-key auth audit logging. Protected-path
  API-key decisions now emit structured runtime log events with
  `event_type=api_key_auth`, outcome, status code, method, path, auth source, and the
  configured `api_key_id` for accepted `API_KEY_SPECS` credentials. The log path does
  not include provided keys, configured secrets, or query strings. Access-control docs,
  catalog, proofs, and tests now cover the audit fields. This provides runtime
  observability for configured key usage; before US-072 it was not a durable database
  audit ledger, hosted log-retention system, automatic rotation, user accounts,
  OAuth/OIDC, hosted identity, or full RBAC.
- 2026-06-05: Added US-072 DB-backed API-key auth audit events. `auth_audit.py` now
  defines API-key auth audit events plus in-memory and SQLAlchemy sinks; the SQLAlchemy
  sink writes protected-path API-key decisions to existing `audit.events` when DB
  services and API-key auth are enabled. `ApiKeyAuthMiddleware` records accepted,
  missing, invalid, and unconfigured decisions through the structured runtime log and
  optional audit sink, fails closed with 503 if configured audit persistence fails, and
  still excludes provided keys, configured secrets, and query strings from log/event
  payloads. Access-control catalog, runbook, proof scripts, operator runbook, and tests
  now validate the DB-backed event path. Focused auth/access-control tests, the
  access-control proof, ruff, and mypy passed. Remaining blockers: hosted log retention
  or SIEM export, user-account binding, automatic key rotation/secret-manager workflow,
  OAuth/OIDC, hosted identity, and full RBAC.
- 2026-06-06: Added US-083 local-only scope correction. Release readiness now treats
  billing/hosted billing, hosted deployment and hosted attestation, published
  registry-image attestation and registry push/signing, automatic key rotation/external
  secret-manager integration, hosted log retention/alerting, and full user
  auth/RBAC/OIDC/user accounts as `out_of_scope_local_only` rather than remaining Level
  10 blockers. The local-only release path keeps source readiness as the active blocker
  and removes remote-only image-publication/hosted-deployment CI jobs from required
  release readiness.
