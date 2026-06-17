# Connector Runbook

## Overview

Connectors are the ingestion boundary between external data sources and the evidence ledger.
Each connector fetches or loads source data for a specific domain (e.g. flood), wraps the
result in a `SourceRetrievalRunContract` with full provenance, and emits a list of
`EvidenceContract` inputs that the ingestion adapter persists to the ledger.

Architecture position:

```
External source / fixture file
        |
    [Connector]
        |  SourceRetrievalRunContract + EvidenceContract[]
        v
[Evidence Ledger]  <-- system of record
        |
[Claims Engine]
        |
[Report]
```

The current implementation includes fixture connectors and bounded public live connectors
for DS-001 USGS The National Map, DS-002 FEMA NFHL, DS-003 USDA SSURGO, and DS-004
National Wetlands Inventory.
`StaticFloodFixtureConnector` reads a local JSON fixture file that was prepared offline.
The live connectors require bounded EPSG:4326 areas, preserve source caveats, and return
the same retrieval/evidence contract shape as fixture connectors.
DS-004 also has raw NWI response fixtures under `tests/fixtures/connectors/` for
representative success parsing and empty-response source-failure behavior. Those fixtures
are deterministic test corpus inputs, not source authority and not proof that no
wetland/deepwater mapping intersects a real area.

---

## Fixture Corpora

There are separate fixture corpora for API smoke tests, selected-county operator utility,
and private-MVP regression. Confusing them leads to overclaiming county coverage.

| Corpus | Location | Reachable via | Connector types | County-specific |
|---|---|---|---|---|
| Generic embedded | `backend/app/connectors/fixtures/*.json` (8 files) | HTTP `POST /connector-runs` via `connector_fixture_resource()` in `backend/app/connectors/fixture_resources.py` | 3 only: `fixture_access_static`, `fixture_flood_static`, `fixture_zoning_static` (see `_SUPPORTED_FIXTURE_CONNECTOR_NAMES` in `backend/app/api/connectors.py`) | No |
| Selected-county operator package | `backend/app/operator_cases/*` | HTTP `GET /operator-cases`, HTTP `POST /operator-cases/{case_id}/report`, and the `/ui/` selected-county launcher | All 8 where present per case: flood, access, zoning, parcels, soils, terrain, wetlands, buildability | Yes (NC Buncombe / Chatham / Brunswick) |
| County golden regression | `tests/fixtures/connectors/*.json` and `tests/fixtures/golden_aois/*.geojson` | Filesystem only: `scripts/generate_dossier.py` and private-MVP tests | All 8 where present per case: flood, access, zoning, parcels, soils, terrain, wetlands, buildability | Yes (NC Buncombe / Chatham / Brunswick) |

Coverage boundary: `POST /connector-runs` still exposes only the generic embedded
package, and `POST /report-runs` does not auto-ingest connector fixtures unless
`ENABLE_LIVE_CONNECTORS=true` (gated in `backend/app/api/reports.py`; default `false`).
The selected-county HTTP path is the dedicated fixture-only utility route:
`POST /operator-cases/{case_id}/report` loads the packaged selected-county case,
ingests its local connector fixtures, approves eligible connector-QA handoffs, creates
an approved report, and returns links to the existing report UI, dossier download, and
JSON artifact routes.

Consequence: a pure-curl operator on a default fixture-mode server can now produce one
of the nine packaged selected-county private-MVP dossiers through `/operator-cases`.
This remains fixture-only utility coverage; it does not imply live county coverage,
DS-017 vendor readiness, legal zoning conclusions, surveyed boundaries, or final
buildability/wetland/access determinations.

---

## Connector Interface

Every connector must:

1. Accept a source identifier (fixture path for static connectors, URI/credentials for live).
2. Return a `FloodFixtureConnectorResult` (or its domain equivalent) containing:
   - `retrieval_run: SourceRetrievalRunContract` — provenance record for this fetch.
   - `evidence_inputs: tuple[EvidenceContract, ...]` — one or more evidence items.
3. Set `retrieval_run.connector_name` to the connector's `connector_name` constant
   (`fixture_flood_static` for the static flood connector).
4. Emit at least one evidence item. An empty evidence list is a contract violation.
5. Use `SourceRetrievalStatus.SUCCEEDED` only when spatial evidence is present and
   `is_source_failure` is `False` on every emitted item.
6. Use `SourceRetrievalStatus.FAILED` or `BLOCKED` only when every emitted item is a
   source-failure evidence record (`is_source_failure=True`,
   `evidence_type=EvidenceType.SOURCE_FAILURE`).

Fixture connectors must additionally use the `fixture://` scheme for `log_uri` and set
`metrics["fixture_only"] = True`.

Live USGS TNM EPQS connector runs must additionally:

1. Use DS-001 (`USGS The National Map`) only after the source license guard passes.
2. Query only the official EPQS JSON endpoint:
   `https://epqs.nationalmap.gov/v1/json`.
3. Require an EPSG:4326 bounding box no larger than 0.25 degrees in either dimension.
4. Sample at most 9 points; the current connector-layer slice samples center plus corners
   by default.
5. Emit one `DERIVED_METRIC` terrain-relief screening observation for usable samples.
6. Emit source-failure evidence, not negative evidence, for request, malformed, or no-data
   responses.
7. Preserve DS-001 screening, citation, metadata, non-survey, and non-engineering caveats
   on every emitted evidence item.
8. Set `EvidenceContract.source_ingest_run_id` on every emitted evidence item to the
   connector result's `retrieval_run.ingest_run_id`.

Live FEMA NFHL connector runs must additionally:

1. Use DS-002 (`FEMA NFHL`) only after the source license guard passes.
2. Query only the effective NFHL ArcGIS REST service:
   `https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer`.
3. Query only layer `28` (`Flood Hazard Zones`) for this slice.
4. Require an EPSG:4326 bounding box no larger than 1 degree in either dimension.
5. Request at most 1000 features.
6. Emit source-failure evidence, not negative evidence, for empty, errored, malformed,
   or transfer-limited responses.
7. Preserve DS-002 screening, citation, and FEMA non-endorsement caveats on every emitted
   evidence item.
8. Set `EvidenceContract.source_ingest_run_id` on every emitted evidence item to the
   connector result's `retrieval_run.ingest_run_id`.

---

## Run Lifecycle

A complete connector ingest run proceeds through these steps:

```
1. Source license check        check_connector_source_license(source)
        |
2. Connector load              connector.load_fixture(fixture_path)
        |                        -> SourceRetrievalRunContract + EvidenceContract[]
        v
3. Retrieval provenance        retrieval_provenance_adapter.record(connector_result)
        |                        -> recorded or skipped (idempotent on ingest_run_id)
        v
4. Evidence ingestion          evidence_ingestion_adapter.ingest(connector_result)
        |                        -> created_evidence + skipped_evidence (idempotent on evidence_id)
        v
5. Review packet               build_connector_run_review_packet(workflow_result)
        |                        -> ConnectorRunReviewPacket with signals and tasks
        v
6. Review handoff              build_connector_review_handoff(packet)
        |                        -> ConnectorReviewHandoff with disposition and queue routing
        v
7. Review queue enqueue        queue_repo.enqueue_review_status(review_status)
                                 -> ConnectorReviewQueueItem (idempotent on ingest_run_id)
```

Steps 2-4 are orchestrated by `FixtureConnectorIngestWorkflow.ingest_fixture()`.
Steps 5-7 are assembled by callers after the workflow completes. The controlled
USGS TNM EPQS, FEMA NFHL, SSURGO, and NWI API routes perform the same steps for live runs
without using the fixture workflow wrapper.

The DS-001 USGS TNM EPQS connector currently has a controlled immediate operator route,
an explicit durable live-job scheduler/worker path, and a default-off request-time
`/intake` plus `/report-runs` gate when live connectors are enabled. Its derived metric is
a sparse point-sample screening proxy and does not determine surveyed elevation,
engineering feasibility, site-plan approval, buildability, lending, appraisal, or
investment suitability.

---

## Controlled USGS TNM EPQS API Invocation

`POST /connector-runs/usgs-tnm/query-bbox` is the current operator-facing invocation path
for the bounded DS-001 live connector.

Request requirements:

1. Reviewer service-account headers are required (`X-Reviewer-Id` and
   `X-Reviewer-Token`).
2. DS-001 must be present in the source registry and pass connector source-use preflight.
3. `area_id` must reference an already registered area.
4. `bbox` must be EPSG:4326 and no larger than 0.25 degrees in either dimension.
5. `max_sample_points` must be between 1 and 9; the current implementation samples from
   the fixed center-plus-corners set.

Route behavior:

1. Builds and runs `UsgsTnmElevationConnector` for DS-001 only.
2. Records retrieval provenance through `ConnectorRetrievalProvenanceAdapter`.
3. Persists one terrain-relief derived metric or source-failure evidence through
   `ConnectorEvidenceIngestionAdapter`.
4. Builds a connector review packet/status and enqueues the run into the existing review
   queue.
5. Returns `202 Accepted` with retrieval status, evidence counts, queue status, queue
   name, source registry id, and request URL.

The immediate route does not create claims, reports, scheduler jobs, request-time
connector runs, DEM downloads, surveyed elevation records, legal conclusions,
buildability conclusions, lending conclusions, appraisal conclusions, or investment
conclusions. Empty/no-data, service errors, and malformed payloads remain source-failure
evidence requiring review; they are not interpreted as "no terrain issue found."

---

## Controlled FEMA NFHL API Invocation

`POST /connector-runs/fema-nfhl/query-bbox` is the current operator-facing invocation
path for the bounded DS-002 live connector.

Request requirements:

1. Reviewer service-account headers are required (`X-Reviewer-Id` and
   `X-Reviewer-Token`).
2. DS-002 must be present in the source registry and pass connector source-use preflight.
3. `area_id` must reference an already registered area.
4. `bbox` must be EPSG:4326 and no larger than 1 degree in either dimension.
5. `max_features` must be between 1 and 1000.

Route behavior:

1. Builds and runs `FemaNfhlConnector` for DS-002 only.
2. Records retrieval provenance through `ConnectorRetrievalProvenanceAdapter`.
3. Persists spatial evidence or source-failure evidence through
   `ConnectorEvidenceIngestionAdapter`.
4. Builds a connector review packet/status and enqueues the run into the existing review
   queue.
5. Returns `202 Accepted` with retrieval status, evidence counts, queue status, queue
   name, source registry id, and request URL.

The route does not create claims, reports, legal conclusions, scheduler jobs, or `/intake`
shortcuts. Empty FEMA responses, service errors, malformed payloads, and transfer-limit
responses remain source-failure evidence requiring review; they are not interpreted as
"no flood issue found."

Connector-produced evidence is report-eligible only after review approval. Report
generation includes evidence with `source_ingest_run_id` only when the connector review
queue has a matching item whose status is `SUCCEEDED` and whose latest
`review_decision.action` is `approve_for_connector_qa`. Unapproved connector-lineage
evidence remains in the ledger but is excluded from report evidence, claims, caveats, and
source manifests.

Manual operator sequence:

1. Register or select an area.
2. Invoke `POST /connector-runs/fema-nfhl/query-bbox` for DS-002.
3. Approve the queued connector run with
   `POST /connector-runs/{ingest_run_id}/review-actions/approve_for_connector_qa`.
4. Create a report from the approved connector run with
   `POST /connector-runs/{ingest_run_id}/report-runs`, passing only the desired
   `intent_code`. The route derives the `area_id` from the connector review queue item,
   requires the latest review decision to be `approve_for_connector_qa`, and does not
   re-run the live FEMA request.
5. Fetch the report with `GET /report-runs/{report_run_id}` and verify the report evidence
   contains the connector `source_ingest_run_id`.

This sequence is operator-driven and is covered by API regressions for both in-memory and
DB-backed service wiring.

When `ENABLE_LIVE_CONNECTORS=true`, `/intake` and `/report-runs` perform request-time
DS-001, DS-002, DS-004, then DS-003 orchestration before report generation:

1. The entry point derives bounded USGS TNM EPQS, FEMA NFHL, and NWI bounding boxes from
   the submitted or stored area; DS-003 derives the bounded SSURGO WKT query area from
   the same area.
2. DS-001 runs first through the same provenance, evidence-ingestion, and review-queue
   adapters as the manual route. If DS-001 is not approved, the API returns
   `status="pending_connector_review"` plus the DS-001 `ingest_run_id`, and does not
   create a report job.
3. After DS-001 approval, call `POST /report-runs` with the same `area_id`. DS-002 then
   runs through the same adapters. If DS-002 is not approved, the API returns
   `status="pending_connector_review"` plus the DS-002 `ingest_run_id`, and still does
   not create a report job.
4. After DS-002 approval, call `POST /report-runs` with the same `area_id`. DS-004 then
   runs through the same adapters. If DS-004 is not approved, the API returns
   `status="pending_connector_review"` plus the DS-004 `ingest_run_id`, and still does
   not create a report job.
5. After DS-004 approval, call `POST /report-runs` with the same `area_id` again. DS-003
   then runs through the same adapters. If DS-003 is not approved, the API returns
   `status="pending_connector_review"` plus the DS-003 `ingest_run_id`, and still does
   not create a report job.
6. After DS-003 approval, call `POST /report-runs` with the same `area_id` again. The API
   creates the normal report job, and report generation may consume only connector-lineage
   evidence approved with `approve_for_connector_qa`.
7. Approved DS-001 evidence may appear as buildability-domain terrain screening evidence,
   but it does not create a DS-001 claim or any buildability, legal, lending, appraisal,
   or investment conclusion.
8. Approved DS-003 evidence may produce only an UNKNOWN, review-required SSURGO screening
   claim. It does not determine septic approval, perc results, soil suitability,
   engineering feasibility, permitting, legal access, buildability, lending, appraisal, or
   investment suitability.

For `/intake`, keep the returned `area_id` from the first pending response and continue
with `/report-runs`; calling `/intake` again creates a new area and starts a new request
sequence.

The connector-run resume route remains available for explicit manual report creation from
one approved connector run. Use the repeated `/report-runs` flow above when the intent is
to complete the full request-time DS-001, DS-002, DS-004, plus DS-003 sequence.

This is request-time orchestration, not an autonomous background live connector daemon.

Background DS-001, DS-002, DS-003, and DS-004 connector scheduling is available as an
explicit queue/worker path:

Use `POST /connector-runs/live-sequence/schedule-bbox` when the operator wants to enqueue
the current reviewed live-source sequence for one registered area in one call. The route
requires reviewer auth plus `X-Workspace-Id`/`X-User-Id`, validates that the registered
`area_id` belongs to that workspace, validates one bounded EPSG:4326 bbox, and enqueues
four separate `live_connector_run` jobs in this order: DS-001, DS-002, DS-004, then
DS-003. The response includes
`policy_id="reviewed_live_sequence_ds001_ds002_ds004_ds003_v1"` and the ordered live job
records. Sequence scheduling is idempotent through workspace-scoped per-source job keys
used by the individual routes.

The sequence scheduler does not call live sources, persist evidence, create claims,
approve connector review items, or create report jobs. It is an operator convenience for
queue creation only; the worker, connector review, and report approval gates remain the
execution authorities.

1. Call the relevant reviewer-authenticated and workspace-authenticated route with a
   registered workspace-owned `area_id` and a bounded EPSG:4326 bbox:
   `POST /connector-runs/usgs-tnm/schedule-bbox` for DS-001,
   `POST /connector-runs/fema-nfhl/schedule-bbox` for DS-002,
   `POST /connector-runs/ssurgo/schedule-bbox` for DS-003, or
   `POST /connector-runs/nwi/schedule-bbox` for DS-004. DS-001 accepts optional
   `max_sample_points`; DS-002 and DS-004 accept optional `max_features`; DS-003 accepts
   optional `max_rows`.
2. The API validates the area workspace and connector-specific bounds, then enqueues a
   durable `live_connector_run` job in `jobs.job_queue` with workspace/requester
   metadata. Scheduling does not call the live source, persist evidence, create claims,
   or create report jobs.
3. Run the bounded worker command:
   `py -3.12 .\scripts\live_connector_worker.py --max-jobs 1 --json`.
   The command opens fresh DB-backed services, calls `run_next_live_connector_job(...)`,
   leases one queued live connector job by default, dispatches by `source_registry_id`,
   runs the same bounded connector orchestration, persists provenance/evidence, and
   enqueues the normal connector review item.
4. The live connector job is marked `SUCCEEDED` with `connector_ingest_run_id`,
   `connector_review_status`, and `request_url`, or `FAILED` with `last_error`.
5. Report creation remains gated on reviewer approval of the resulting connector review
   item; operators still use `POST /connector-runs/{ingest_run_id}/report-runs` after
   approval.

The worker exits `0` when no queued job exists or all processed jobs succeed. It exits
`1` when a processed job fails after the failure state is committed. One-shot mode remains
the default for operator calls.

For supervised polling, pass `--poll-seconds <seconds>`. `--idle-polls 0` means keep
polling until the process is stopped by the supervisor; a positive value exits after that
many consecutive idle polls. The Compose file includes an opt-in worker profile:

```powershell
docker compose --profile workers up -d live-connector-worker
docker compose --profile workers logs -f live-connector-worker
```

The profile is not part of default `docker compose up`. It uses
`LIVE_CONNECTOR_WORKER_ID`, `LIVE_CONNECTOR_WORKER_MAX_JOBS`,
`LIVE_CONNECTOR_WORKER_POLL_SECONDS`, and `LIVE_CONNECTOR_WORKER_IDLE_POLLS` from the
environment or `.env`.

Even in supervised mode, report creation remains separate and review-gated. The worker
does not approve connector review items, create report jobs, or bypass
`POST /connector-runs/{ingest_run_id}/report-runs`.

---

## Failure Taxonomy

### LicenseBlockedError (`ConnectorLicenseBlockedError`)

Raised by `check_connector_source_license()` before any ingestion attempt when the source
is not approved for production use. This includes unapproved review status, unknown or
blocked license status, and unknown or blocked commercial/cache/export/raw-data/AI-use
rights. No retrieval run is recorded and no evidence is written.

### ConnectorLoadError (`FixtureConnectorError`)

Raised by `StaticFloodFixtureConnector.load_fixture()` when:
- The fixture path uses a remote scheme (`://` in path).
- The fixture file does not exist on disk.
- The JSON payload fails Pydantic validation for `SourceRetrievalRunContract` or
  `EvidenceContract`.
- `retrieval_run.connector_name` does not match `connector_name`.
- Evidence list is empty.
- A succeeded run contains no spatial evidence.
- A failed/blocked run contains no source-failure evidence.

### Live FEMA NFHL request failure

`FemaNfhlConnector` converts live request errors, FEMA service errors, malformed responses,
empty feature responses, and FEMA transfer-limit responses into
`EvidenceType.SOURCE_FAILURE` evidence. These are not treated as "no flood issue found."
The source-failure payload includes the failure reason, error message, and retryability.
Service URL, layer ID, and query bounding box are preserved in retrieval-run metrics.

### EvidenceIngestionError (`ConnectorEvidenceIngestionError`)

Raised by `ConnectorEvidenceIngestionAdapter` during evidence routing when:
- An evidence item has `evidence_type=SOURCE_FAILURE` but `is_source_failure=False`.
- A source-failure item is missing a caveat.

### SourceFailureEvidence

Not an exception. When a connector explicitly reports that a source could not be reached or
was blocked, it emits one or more `EvidenceContract` items with `is_source_failure=True` and
`evidence_type=EvidenceType.SOURCE_FAILURE`. These are persisted as first-class evidence in
the ledger. They propagate to downstream claims and reports as documented gaps, not as silent
missing data. Source-failure evidence triggers the `SOURCE_FAILURE_EVIDENCE_PRESENT` review
signal and requires human review.

---

## Data Quality Gates

`evaluate_flood_fixture_quality()` produces a `ConnectorFixtureQualityProfile` after the
connector loads but before the result is accepted into the review pipeline. A profile
`passed` when no blocking issue is present.

Issue codes and what they check:

| Code | What it checks |
|---|---|
| `retrieval_finished_before_started` | `finished_at` must not precede `started_at` |
| `retrieval_connector_name_mismatch` | `connector_name` must equal `fixture_flood_static` |
| `retrieval_dataset_version_missing` | `dataset_version_id` must be set |
| `fixture_log_uri_not_local` | `log_uri` must use `fixture://` scheme |
| `fixture_metric_missing` | `metrics["fixture_only"]` must be `True` |
| `succeeded_row_count_mismatch` | `row_count` must equal non-failure evidence count |
| `succeeded_error_count_nonzero` | `error_count` must be `0` on succeeded runs |
| `succeeded_has_failure_reason` | Succeeded run must not record a `failure_reason` metric |
| `succeeded_has_source_failure` | Succeeded run must not emit source-failure evidence |
| `blocked_or_failed_row_count_not_zero` | `row_count` must be `0` on failed/blocked runs |
| `blocked_or_failed_error_count_missing` | Failed/blocked run must record at least one error |
| `retrieval_failure_reason_missing` | Failed/blocked run must set `metrics["failure_reason"]` |
| `blocked_has_non_failure_evidence` | Failed/blocked run must not emit non-failure evidence |
| `evidence_area_id_mismatch` | All evidence in one run must share the same `area_id` |
| `evidence_source_id_mismatch` | All evidence in one run must share the same `source_id` |
| `evidence_domain_mismatch` | Evidence `domain` must be `flood` |
| `evidence_dataset_version_mismatch` | Evidence `dataset_version_id` must match retrieval run |
| `evidence_method_code_mismatch` | Method code must start with `fixture_flood_` |
| `duplicate_evidence_id` | Evidence IDs must be unique within one run |
| `evidence_observed_before_retrieval` | `observed_at` must not precede `retrieval_run.started_at` |
| `evidence_observed_after_retrieval_finished` | `observed_at` must not follow `retrieval_run.finished_at` |
| `evidence_provenance_text_missing` | `evidence_code`, `observation`, `method_code`, `method_version` must be non-empty |
| `evidence_caveat_missing` | Every evidence item must include a `caveat` |
| `source_observation_source_date_missing` | Non-failure evidence must include `source_date` |
| `source_failure_payload_incomplete` | Source-failure `observed_value` must contain `failure_reason`, `error_message`, `retryable` |
| `source_failure_payload_invalid` | Payload values must be typed and non-empty (`retryable` must be `bool`) |
| `source_failure_type_mismatch` | `is_source_failure` flag must match `evidence_type == SOURCE_FAILURE` |
| `source_failure_reason_mismatch` | `observed_value["failure_reason"]` must match `metrics["failure_reason"]` |
| `source_failure_confidence_not_unknown` | Source-failure evidence must use `ConfidenceBand.UNKNOWN` |
| `spatial_evidence_geometry_missing` | Spatial (non-failure) evidence must include `geometry_geojson` and `spatial_precision_meters` |
| `source_failure_geometry_present` | Source-failure evidence must not include geometry fields |

---

## Idempotency

The connector system is idempotent at three levels:

1. **Retrieval run**: `ConnectorRetrievalProvenanceAdapter.record_retrieval_run()` checks
   `retrieval_run_exists(ingest_run_id)` before writing. A duplicate `ingest_run_id` is
   skipped; `skipped_run` is populated and `recorded_run` is `None`.

2. **Evidence**: `ConnectorEvidenceIngestionAdapter.ingest_evidence()` calls
   `evidence_exists(evidence_id)` before each write. Existing evidence IDs are placed in
   `skipped_evidence`. Source-failure items are additionally fingerprinted by
   `(area_id, source_id, method_code, evidence_code, domain, observation, caveat,
   observed_value)` to catch semantic duplicates even when `evidence_id` differs.

3. **Review queue**: `enqueue_review_status()` (both in-memory and SQLAlchemy
   implementations) checks for an existing row keyed on
   `connector_review_status:{ingest_run_id}` before inserting. A second enqueue for the
   same `ingest_run_id` returns the existing item unchanged.

When a run is fully idempotent (retrieval skipped, no evidence created, some evidence
skipped), the review handoff disposition is `IDEMPOTENT_NOOP` and it routes to the
`connector-idempotency-log` queue rather than the human review queue.

---

## Rate Limit and Retry Policy

`ConnectorPolicy` holds the operational limits for a connector run.

| Field | Type | Default | Meaning |
|---|---|---|---|
| `rate_limit_per_minute` | `int` | `0` | Maximum calls per minute; `0` = unlimited |
| `timeout_seconds` | `float` | `30.0` | Maximum seconds per request; `0` = no limit |
| `max_retries` | `int` | `3` | Maximum retry attempts after failure |
| `retry_backoff_seconds` | `float` | `1.0` | Seconds to wait between retries |

All fields must be non-negative. `ConnectorPolicy.__post_init__` raises `ValueError`
otherwise.

`DEFAULT_FIXTURE_POLICY` is the policy for all fixture connectors:

```python
DEFAULT_FIXTURE_POLICY = ConnectorPolicy(
    rate_limit_per_minute=0,   # unlimited — local file read
    timeout_seconds=5.0,       # short timeout for local I/O
    max_retries=0,             # no retries — fixture file is static
    retry_backoff_seconds=0.0,
)
```

Live connectors use the default `ConnectorPolicy()` values or define a source-specific
policy instance.

---

## License Enforcement

`check_connector_source_license(source: SourceContract)` must be called before any connector
run begins.

Connector source use is fail-closed. A source passes only when:

- `review_status` is `approved` or `approved-with-restrictions`;
- `license_status`, `commercial_use_status`, `redistribution_status`, `cache_allowed`,
  `export_allowed`, `raw_data_allowed`, and `ai_use_allowed` are explicit allowed values:
  `yes`, `allowed`, `approved`, `approved-with-restrictions`, or `restricted`.

Unknown, unreviewed, pending, blocked, incompatible, or absent production-use rights raise
`ConnectorLicenseBlockedError`. The error includes `source_id`, `license_status`, and the
blocked source fields.

When `ConnectorLicenseBlockedError` is raised, the connector run must be aborted. No
retrieval run is recorded, no evidence is written, and no review queue item is created.
Record the blocked attempt in operational logs with the `source_id`, `license_status`, and
blocked fields.

Use the source-readiness audit before selecting a live connector candidate:

```powershell
py -3.12 .\scripts\source_readiness.py
py -3.12 .\scripts\source_readiness.py --priority Must
py -3.12 .\scripts\source_readiness.py --priority Must --json
```

The command is read-only. It reports connector-ready counts and the exact registry fields
that block each source. Add `--require-ready` only in a gate that should fail when no source
in the selected scope is connector-ready.

---

## Observability

`ConnectorRunObservabilityLog` collects `ConnectorObservabilityEvent` objects in process
during a connector run. Events are held in memory for the duration of the run and are
consumed by the calling orchestrator.

Event types:

| Event type | When to emit |
|---|---|
| `run_started` | Connector run begins (before license check; emitted even for blocked runs) |
| `run_succeeded` | Workflow completes without exception |
| `run_failed` | Workflow raises an exception |
| `rate_limited` | Run is paused by rate limit enforcement |
| `retry_attempt` | A retry is being attempted after a transient failure |
| `evidence_stored` | A non-failure evidence item is persisted |
| `source_failure_stored` | A source-failure evidence item is persisted |

Each event carries `event_type`, `connector_name`, `ingest_run_id`, `message`, and
`timestamp`. Use `log.events_of_type(ConnectorEventType.run_failed)` to filter by type.

The current implementation is in-process only. Structured log forwarding to a persistent
store is a future integration point.

---

## Human Review Workflow

After `FixtureConnectorIngestWorkflow.ingest_fixture()` completes:

1. **Build review packet**: `build_connector_run_review_packet(workflow_result)` aggregates
   counts, signals, and human review tasks from the workflow result.

2. **Build review handoff**: `build_connector_review_handoff(packet)` computes the
   disposition and routes to the appropriate queue:
   - `NEEDS_HUMAN_REVIEW` → `connector-human-review` queue (priority HIGH)
   - `READY_FOR_CONNECTOR_QA` → `connector-quality-review` queue (priority NORMAL)
   - `IDEMPOTENT_NOOP` → `connector-idempotency-log` queue (priority NORMAL)

3. **Build review status**: `build_connector_run_review_status(handoff, quality_profile)`
   combines the handoff with the quality profile. `review_required` is `True` when
   disposition is `NEEDS_HUMAN_REVIEW` or the quality profile has blocking issues.

4. **Enqueue**: `queue_repo.enqueue_review_status(review_status)` creates a
   `ConnectorReviewQueueItem` in `jobs.job_queue` (SQLAlchemy implementation) or the
   in-memory store. Status is `NEEDS_REVIEW` when `review_required` is True, else `QUEUED`.

Signals that force `review_required = True`:
- `retrieval_not_succeeded` — retrieval status is not `SUCCEEDED`
- `retrieval_errors_present` — `error_count > 0`
- `retrieval_warnings_present` — `warning_count > 0`
- `source_failure_evidence_present` — one or more source-failure evidence items created or skipped
- `no_evidence_persisted` — no evidence was created or skipped

Review queue actions available to human reviewers:

| Action | Method | Applicable statuses | Effect |
|---|---|---|---|
| Approve for connector QA | `approve_for_connector_qa(job_id, reviewer_id=..., reason=...)` | NEEDS_REVIEW, QUEUED, RUNNING | Closes job as SUCCEEDED and records the reviewer decision in the queue payload |
| Request fixture/source fix | `request_fixture_fix(job_id, reviewer_id=..., reason=...)` | NEEDS_REVIEW, QUEUED, RUNNING | Closes job as FAILED, records the reviewer decision in the queue payload, and stores the reason in `last_error` |
| Mark succeeded | `mark_succeeded(job_id)` | RUNNING | Closes job as SUCCEEDED |
| Mark failed | `mark_failed(job_id, error=...)` | RUNNING | Closes job as FAILED |
| Requeue after fix | `requeue_failed(job_id, reviewer_id=..., reason=..., not_before=...)` | FAILED (with retries remaining) | Returns to QUEUED and appends the reviewer action to the queue payload |
| Cancel | `cancel(job_id, reviewer_id=..., reason=...)` | Any except SUCCEEDED, CANCELLED | Closes as CANCELLED and appends the reviewer action to the queue payload |

API actions:

| Route | Reason required | Effect |
|---|---|---|
| `POST /connector-runs/{ingest_run_id}/review-actions/approve_for_connector_qa` | No | Calls `approve_for_connector_qa` and returns the updated queue item |
| `POST /connector-runs/{ingest_run_id}/review-actions/request_fixture_fix` | Yes | Calls `request_fixture_fix` and returns the updated queue item |
| `POST /connector-runs/{ingest_run_id}/review-actions/requeue_after_fix` | Yes | Calls `requeue_failed` and returns the updated queue item |
| `POST /connector-runs/{ingest_run_id}/review-actions/cancel_review` | Yes | Calls `cancel` and returns the updated queue item |

These actions mutate only connector review queue state. They do not mutate source
retrieval provenance, evidence observations, claims, report runs, schemas, connector
runtime behavior, or live source data. Downstream report generation reads the queue state
as an approval gate for connector-lineage evidence, so `approve_for_connector_qa` affects
future report eligibility without rewriting already persisted evidence.

Reviewer action metadata is stored in the queue item payload. `review_decision` records the
latest approve/fix decision used by report gating. `review_action_history` is an append-only
payload array for reviewer closeout, requeue, and cancel actions; API routes pass the
authenticated reviewer id into each history entry. This is durable queue metadata, not a
separate audit-event authorization ledger.

---

---

## Live Smoke

`scripts/run_live_smoke.ps1` (Windows) and `scripts/run_live_smoke.sh` (Linux/macOS) are
env-gated wrappers that drive the four existing `query-bbox` routes once each against a
small Buncombe County NC bounding box (`-82.60,35.55 to -82.55,35.60`). They add no new
connector logic; every live call goes through the already-existing API routes.

### Prerequisites

- Python 3.12+ available as `py -3.12` (Windows) or `python3.12` / `python3` (Linux/macOS).
- `uvicorn` installed in the Python environment (`pip install uvicorn` or project venv).
- Port 8103 free on localhost.
- Network access to the four public federal endpoints:
  - DS-001: `https://epqs.nationalmap.gov/v1/json`
  - DS-002: `https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28/query`
  - DS-003: `https://SDMDataAccess.sc.egov.usda.gov/Tabular/SDMTabularService/post.rest`
  - DS-004: `https://www.fws.gov/wetlands/arcgis/rest/services/Wetlands_Raster/MapServer/0/query`

No credentials beyond the default local reviewer account (`fixture-reviewer` /
`fixture-token-123`) are required. The routes do not require `ENABLE_LIVE_CONNECTORS`;
the wrapper sets it anyway for completeness with `POST /intake` paths.

### Exact commands

**Validate-only (no live calls — safe in CI):**

```powershell
# Prints "SKIP: live connector smoke" and exits 0.
.\scripts\run_live_smoke.ps1
```

```bash
./scripts/run_live_smoke.sh
```

**Full live execution (one bounded bbox, public federal APIs):**

```powershell
$env:RUN_LIVE_CONNECTOR_TESTS = '1'
.\scripts\run_live_smoke.ps1
```

```bash
RUN_LIVE_CONNECTOR_TESTS=1 ./scripts/run_live_smoke.sh
```

Optional overrides: `SMOKE_API_PORT` (default 8103), `SMOKE_OUTPUT_DIR`
(default `local_artifacts`).

### What the script does

1. Starts the API in-process on port 8103 with in-memory storage and
   `ENABLE_LIVE_CONNECTORS=true`.
2. Waits for the `/health` endpoint to respond.
3. Registers DS-001, DS-002, DS-003, and DS-004 sources from the CSV registry via
   `POST /sources` with the local reviewer service-account headers. The reviewer account
   must hold `source:manage`; the default local `fixture-reviewer` account includes it.
4. Registers a Buncombe NC polygon area via `POST /areas`.
5. Calls each of the four `query-bbox` routes in order (DS-001, DS-002, DS-004, DS-003)
   with reviewer auth headers.
6. Writes a timestamped JSON transcript to `local_artifacts/live_smoke_<timestamp>.json`.
7. Stops the API.

The `local_artifacts/` directory is gitignored; transcripts are never committed.

### What success looks like

Each leg returns `HTTP 202 Accepted` with `retrieval_status` of `SUCCEEDED` or `FAILED`.
A `FAILED` retrieval status is a first-class source-failure outcome, not a script error —
it means the public endpoint was reachable but returned no usable data (common for
wetland-free or out-of-service-area bboxes). The leg is counted as `PASS` as long as
the API route returns a 2xx status with the standard response shape.

Example successful leg output:

```
DS-002 FEMA NFHL: POST /connector-runs/fema-nfhl/query-bbox ... PASS (HTTP 202)
  retrieval=SUCCEEDED ev_created=3 sf_count=0
```

Example source-failure (first-class outcome, still a leg PASS):

```
DS-001 USGS TNM: POST /connector-runs/usgs-tnm/query-bbox ... PASS (HTTP 202)
  retrieval=FAILED ev_created=0 sf_count=1
```

A leg is `FAIL` only when the API returns a non-2xx status (e.g., 409 if a source is not
registered, 422 for a bad bbox, or 5xx for an internal error).

### What failure looks like

Non-2xx HTTP responses are recorded per leg. The transcript JSON includes
`response_summary.error_detail` for each failed leg. Common causes:

- `409 source registry id DS-00X is not registered` — source seed was not applied; check
  that `registers/data_source_registry.csv` contains the expected row and that the
  `/sources` seed step completed successfully.
- `401` or `403` during source seed - reviewer credentials were missing, invalid, or did
  not include `source:manage`; check `REVIEWER_ACCOUNTS` and
  `REVIEWER_ACCOUNT_SCOPES`.
- `422 area not found` — area registration failed; check API startup logs.
- `503 connector reviewer auth is not configured` — `REVIEWER_ACCOUNTS` env var is not
  set or is empty; the default value applies automatically when no `.env` overrides it.
- Network timeout or connection error — the public federal endpoint was unreachable;
  recorded as source-failure evidence in the transcript, not a script failure.

### Source-rights restrictions

All four sources carry approved-with-restrictions status. Screening language applies:

- **DS-001 USGS TNM** — Public domain, non-survey, non-engineering. Results are
  point-sample terrain-relief screening only; not surveyed elevation, not engineering
  feasibility, not buildability, lending, appraisal, or investment advice.
- **DS-002 FEMA NFHL** — Effective FEMA flood-hazard-zone screening only; not a final
  legal, insurance, lending, buildability, title, water-rights, wetland, or survey
  determination. Cite FEMA and state non-endorsement.
- **DS-003 USDA SSURGO** — Soil screening only; not perc results, not septic approval,
  not engineering feasibility. Results require review and produce an UNKNOWN confidence
  claim pending human QA.
- **DS-004 NWI (FWS)** — Wetland screening only; not a jurisdictional wetland delineation
  and not a final regulatory or legal determination.

No report produced from these connectors may assert final legal access, buildability,
title status, water rights, wetland jurisdiction, surveyed boundaries, insurability,
appraisal value, lending suitability, or investment advice.

---

## Troubleshooting

**Missing fixture file**

`FixtureConnectorError: connector fixture does not exist: <path>`

Check that the fixture path is correct and the file is accessible from the working directory.
Fixture paths must not use remote schemes (`://`).

**License-blocked source**

`ConnectorLicenseBlockedError: connector run blocked: source <id> has license_status='incompatible'`

Update the source record's `license_status` in the source registry, or obtain an approved
license before running the connector. Do not change the status without an ADR or explicit
approval.

**Fixture quality failures**

The quality profile is logged in the review packet under `quality.issues`. Each issue
includes a `code` (see the Data Quality Gates table above), a human-readable `message`, and
`blocking: true`. Correct the fixture JSON to satisfy each blocking issue code and re-run
ingestion. Common issues:

- `retrieval_dataset_version_missing`: add a `dataset_version_id` UUID to `retrieval_run`.
- `succeeded_row_count_mismatch`: ensure `row_count` equals the number of non-failure
  evidence items.
- `source_failure_payload_incomplete`: ensure source-failure `observed_value` includes
  `failure_reason` (str), `error_message` (str), and `retryable` (bool).
- `spatial_evidence_geometry_missing`: add `geometry_geojson` and
  `spatial_precision_meters` to spatial evidence items.
- `source_failure_geometry_present`: remove geometry fields from source-failure items.

**Empty evidence set after ingestion**

`evidence_created_count = 0` and `evidence_skipped_count = 0` triggers the
`no_evidence_persisted` signal and forces human review. Verify the fixture file contains
well-formed evidence items and that `ingest_run_id` is fresh (not a duplicate of a prior run).

**Duplicate ingest_run_id skip**

If `retrieval_skipped = True` and `evidence_skipped_count > 0` with no new evidence
created, the run was detected as a duplicate. This is expected idempotent behaviour. The
review queue item will have disposition `IDEMPOTENT_NOOP`. To force a fresh ingest, use a
new `ingest_run_id` UUID in the fixture's `retrieval_run` block.
