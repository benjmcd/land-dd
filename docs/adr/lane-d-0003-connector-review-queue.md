# ADR: Connector Review Queue Persistence

Status: accepted

Date: 2026-06-04

## Context

CON-013 added an in-memory API status surface for connector review handoffs and fixture quality profiles. The next Level 8 workflow step needs durable human-review queue persistence, but connector lifecycle authority must remain with `source.ingest_runs`.

The existing database spine already includes `jobs.job_queue` with `job_type`, `status`, `priority`, `payload`, `idempotency_key`, attempts, and timing fields. `LANE_OWNERSHIP.md` and `lane-d-0002-connector-entry-ownership.md` reserve this table for async orchestration and explicitly reject using jobs as source provenance.

## Decision

Use `jobs.job_queue` for durable connector review-status work items without a schema migration.

Connector review queue items:

- use `job_type = "connector_review_status"`;
- use idempotency key `connector_review_status:<ingest_run_id>`;
- store `source.ingest_runs.ingest_run_id` in the JSON payload;
- set `status = "needs_review"` and high priority for human-review-required statuses;
- set `status = "queued"` and normal priority for non-blocking connector QA statuses;
- preserve `source.ingest_runs` as connector attempt provenance and lifecycle authority.

The connector integration zone owns the adapter that projects connector review status into queue items. Lane D may expose API surfaces that consume connector-owned status records. Future worker execution, retry policy, queue dashboards, and DB-backed API retrieval are separate planned slices.

## Consequences

- Durable human-review queue persistence can be tested against the existing DB spine.
- No schema migration is needed for the current connector review-status queue item.
- The queue payload is an orchestration envelope, not evidence, claim, report output, or source provenance.
- Future changes to queue status semantics, worker leases, or payload schema should update this ADR or add a follow-up ADR before implementation.
