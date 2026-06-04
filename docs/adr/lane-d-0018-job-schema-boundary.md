# ADR Lane D 0018: Job Schema Boundary

## Status
Accepted

## Context

`schemas/job_schema.json` exists as a shared planning-pack-era schema, and `jobs.job_queue` exists in the database spine. Connector review queue work now uses `jobs.job_queue` for review orchestration through `ConnectorReviewQueueItem`, while source retrieval runs remain connector attempt provenance authority through Lane A source provenance contracts.

The current repo has no `JobContract` domain model and no schema parity test for `schemas/job_schema.json`. Treating the existing schema as a live connector-run contract would blur two separate concepts:

- source retrieval runs: connector lifecycle/provenance authority;
- jobs: async/review orchestration state.

## Decision

Do not promote `schemas/job_schema.json` to a live connector-run or API contract until a future planned schema/test slice defines the exact authority it mirrors.

Future job-schema work must choose one authority before implementation:

- `jobs.job_queue` row shape for durable orchestration state; or
- `ConnectorReviewQueueItem` for connector review queue API/read-model state; or
- a new `JobContract` domain model, if broader async workflow needs a stable public contract.

Connector retrieval lifecycle must not be represented by job schema. Retrieval status, timing, row/error/warning counts, log URI, dataset version, metrics, and connector attempt identity remain source retrieval-run fields.

## Required Future Scope

Before editing `schemas/job_schema.json`, add a planned schema/test slice that:

- identifies the canonical source of truth;
- keeps `JobStatus` enum parity with `backend/app/domain/enums.py`;
- decides whether worker fields (`not_before`, `locked_by`, `locked_at`, `started_at`, `finished_at`) are in schema scope;
- decides whether payload references such as `ingest_run_id` are required for `connector_review_status` jobs;
- preserves `source.ingest_runs` as connector provenance authority.

## Consequences

- Review-action route implementation can continue to use existing queue repositories without claiming job schema parity.
- OpenAPI route work should not expose or regenerate job schema claims until the chosen job contract exists.
- Source retrieval-run schema and job schema stay separate; neither replaces the other.
