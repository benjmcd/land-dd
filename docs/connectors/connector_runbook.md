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

The current implementation is fixture-only. `StaticFloodFixtureConnector` reads a local JSON
fixture file that was prepared offline. Live connectors that call external APIs or vendor
services will follow the same contract once the fixture layer is stable.

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

Steps 2–4 are orchestrated by `FixtureConnectorIngestWorkflow.ingest_fixture()`.
Steps 5–7 are assembled by callers after the workflow completes.

---

## Failure Taxonomy

### LicenseBlockedError (`ConnectorLicenseBlockedError`)

Raised by `check_connector_source_license()` before any ingestion attempt when the source
`license_status` is `incompatible` or `unknown_blocking`. No retrieval run is recorded and
no evidence is written.

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

Blocking statuses (raise `ConnectorLicenseBlockedError`):
- `incompatible` — source license is incompatible with the project's use terms.
- `unknown_blocking` — license is unknown and has been explicitly flagged as blocking.

Pass-through statuses (no exception):
- `allowed`
- `allowed_with_attribution`
- `review_required`
- `unknown`
- `unreviewed`

When `ConnectorLicenseBlockedError` is raised, the connector run must be aborted. No
retrieval run is recorded, no evidence is written, and no review queue item is created.
Record the blocked attempt in operational logs with the `source_id` and `license_status`.

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
| Mark succeeded | `mark_succeeded(job_id)` | RUNNING | Closes job as SUCCEEDED |
| Mark failed | `mark_failed(job_id, error=...)` | RUNNING | Closes job as FAILED |
| Requeue after fix | `requeue_failed(job_id, reason=..., not_before=...)` | FAILED (with retries remaining) | Returns to QUEUED |
| Cancel | `cancel(job_id, reason=...)` | Any except SUCCEEDED, CANCELLED | Closes as CANCELLED |

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
