# ADR: Connector Queue Worker Lease Semantics

Status: accepted

Date: 2026-06-04

## Context

CON-014 added durable connector review queue persistence in `jobs.job_queue`, and CON-015 added read-only queue retrieval by connector retrieval run. Queue mutation now needs explicit semantics before any worker-facing code changes can safely mark queue items as in progress or complete.

The queue remains orchestration state. `source.ingest_runs` remains connector attempt provenance and lifecycle authority.

## Decision

Add repository-level worker lease and finish semantics for connector review queue items only.

Worker semantics:

- lease only `job_type = "connector_review_status"` rows;
- lease only rows with `status = "needs_review"` or `status = "queued"`;
- respect `not_before` and `attempts < max_attempts`;
- order leases by priority, then creation time;
- transition leased rows to `status = "running"`, increment `attempts`, and set lock/start metadata;
- complete only running connector review queue rows;
- mark successful review completion with `status = "succeeded"` and `finished_at`;
- mark failed review completion with `status = "failed"`, `finished_at`, and `last_error`;
- reject empty worker IDs and empty failure errors.

This slice does not add a long-running worker process, scheduler, background loop, API mutation route, retry policy, queue dashboard, live connector execution, evidence persistence, claims, reports, schema migration, or source provenance mutation.

## Consequences

- Connector review queue items can now be safely leased and finished by future explicit worker or review workflow code.
- The lease path is deterministic and DB-backed without changing the existing schema.
- API consumers still have read-only queue retrieval only.
- Future retry, timeout, requeue, cancellation, dashboard, and worker execution surfaces remain separate planned slices.
