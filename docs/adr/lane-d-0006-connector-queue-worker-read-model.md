# ADR: Connector Queue Worker Read Model

Status: accepted

Date: 2026-06-04

## Context

CON-016 added repository-level lease and finish semantics for connector review queue items. Operators and future review workflow code need to inspect queue worker state through the existing queue retrieval API without introducing API-side job mutation.

The queue remains orchestration state. `source.ingest_runs` remains connector attempt provenance and lifecycle authority.

## Decision

Extend the existing read-only connector review queue item response with worker-state fields already present in `jobs.job_queue` and `ConnectorReviewQueueItem`:

- `attempts`;
- `max_attempts`;
- `locked_by`;
- `locked_at`;
- `started_at`;
- `finished_at`;
- `last_error`.

The `GET /connector-runs/{ingest_run_id}/review-queue` endpoint remains read-only. It may surface queued, running, succeeded, or failed queue state, but it must not lease, complete, fail, retry, requeue, cancel, execute, or create jobs.

## Consequences

- Consumers can inspect connector review queue worker state after CON-016.
- No new queue mutation route or scheduler is introduced.
- Retry/requeue/cancel policy, worker execution, dashboards, and human-review workflow actions remain separate planned slices.
