# ADR: Connector Human Review Action Semantics

Status: accepted

Date: 2026-06-04

## Context

Connector review packets, handoffs, status records, and durable queue rows now exist for fixture connector review. CON-016 through CON-018 added repository-level lease, finish, retry/requeue, and cancel semantics. CON-017 and CON-015 expose read-only queue/status API views.

The next human-review step needs action semantics before any API mutation route, worker, dashboard, or operator workflow can be added. Without an explicit action boundary, future code could confuse review decisions with connector provenance, claim generation, evidence persistence, or automatic retry policy.

## Decision

Define future connector human-review actions as explicit operations over `connector_review_status` queue rows only:

- `acknowledge`: record reviewer ownership or attention without changing source retrieval provenance, evidence, claims, or report output.
- `approve_for_connector_qa`: mark a review item ready for connector QA when fixture quality and handoff signals are acceptable.
- `request_fixture_fix`: fail the review item with a reason when fixture data, fixture metadata, or source-failure payload quality needs correction.
- `requeue_after_fix`: requeue a failed review item only through existing retry/requeue semantics and only when attempts remain.
- `cancel_review`: cancel a nonfinal review item with a reason when review is superseded or no longer needed.

These action names are planning authority only. They do not add API routes, repository methods, workers, schedulers, dashboards, migrations, source provenance mutation, evidence persistence, claims, reports, live connector execution, or automatic retry policy.

Any future API mutation route must be a separate planned slice and must:

- use explicit route semantics and request/response contracts;
- require a non-empty reviewer identity where ownership is recorded;
- require non-empty reasons for failure, requeue, or cancellation;
- preserve `source.ingest_runs` as connector provenance/lifecycle authority;
- preserve `jobs.job_queue` as review orchestration state;
- fail closed for missing queue rows, non-connector-review job types, invalid transitions, and exhausted retry attempts;
- remain idempotent for repeated equivalent reviewer actions where possible;
- avoid mutating evidence, claims, reports, schemas, or connector runtime behavior.

ADR Lane D 0012 accepts the route, reviewer identity, auth, idempotency, and transition semantics for a future narrow action API. It does not implement that API.

## Consequences

- Future review workflow/API work can target known action semantics instead of inventing behavior inside route handlers.
- Existing repository-level queue transitions remain the only accepted mutation substrate until an API mutation slice is explicitly planned.
- Human review remains orchestration over connector review status, not legal approval, source truth, claim interpretation, or report approval.
- Retry/cancel API surfacing remains a separate implementation slice after ADR Lane D 0012 route/reviewer/auth semantics.
- Route/reviewer/auth semantics are accepted by ADR Lane D 0012; implementation remains a separate planned slice.
