# ADR: Connector Queue Retry And Cancel Semantics

Status: accepted

Date: 2026-06-04

## Context

CON-016 added repository-level lease and finish semantics for connector review queue items. CON-017 exposed queue worker state through the existing read-only queue API. The next queue-orchestration boundary is retry/requeue and cancellation behavior.

The queue remains orchestration state. `source.ingest_runs` remains connector attempt provenance and lifecycle authority.

## Decision

Add repository-level retry/requeue and cancel semantics for connector review queue items only.

Retry/requeue semantics:

- requeue only `job_type = "connector_review_status"` rows;
- requeue only rows with `status = "failed"`;
- require `attempts < max_attempts`;
- transition the row to `status = "queued"`;
- preserve attempt count;
- clear lock and finish metadata;
- set `not_before` to the supplied schedule time or current time;
- record a non-empty requeue reason in `last_error`.

Cancel semantics:

- cancel only `job_type = "connector_review_status"` rows;
- reject already `succeeded` or already `cancelled` rows;
- transition cancellable rows to `status = "cancelled"`;
- record `finished_at` and a non-empty cancellation reason in `last_error`.

This slice does not add API-side mutation, automatic retry policy, timeout handling, a scheduler, background loop, queue dashboard, live connector execution, evidence persistence, claims, reports, schema migration, or source provenance mutation.

## Consequences

- Future explicit worker or review workflow code has a deterministic repository surface for retry and cancellation.
- Default connector review queue items remain single-attempt because CON-014 inserts them with `max_attempts = 1`; requeue is fail-closed unless a future planned queue producer or operator explicitly allows additional attempts.
- Retry scheduling can use existing `jobs.job_queue.not_before` without a schema change.
- API mutation routes, dashboards, timeout handling, and automatic retry policy remain separate planned slices.
