# ADR: Connector Queue Retrieval Semantics

Status: accepted

Date: 2026-06-04

## Context

CON-014 added durable connector review queue persistence in `jobs.job_queue`. The next API step is retrieving those queued review items by connector retrieval run without introducing worker execution semantics.

The queue is orchestration state. It must not replace `source.ingest_runs` as connector provenance or lifecycle authority.

## Decision

Expose read-only connector review queue retrieval by `ingest_run_id`.

Retrieval semantics:

- read the existing `connector_review_status:<ingest_run_id>` queue item;
- return 404 when no queue item exists;
- do not create, mutate, lock, retry, cancel, or complete jobs;
- do not derive evidence, claims, reports, or source provenance from queue state;
- keep worker execution, leasing, retry policy, dashboards, and status mutation as future planned work.

## Consequences

- API consumers can inspect durable connector review queue state after CON-014.
- The read path is safe to expose before worker behavior because it is side-effect-free.
- Future worker or dashboard slices must update queue execution semantics before mutating `jobs.job_queue`.
