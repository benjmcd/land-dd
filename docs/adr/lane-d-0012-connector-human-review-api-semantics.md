# ADR: Connector Human Review API Semantics

Status: accepted

Date: 2026-06-04

## Context

CON-021 defined future connector human-review action vocabulary, but did not accept API route shape, reviewer identity, auth expectations, request/response contracts, idempotency, or transition preconditions. Without those decisions, adding mutation routes would risk mixing review workflow, connector provenance, queue orchestration, evidence persistence, and report semantics.

Existing API surface is read-only for connector review status and queue state:

- `GET /connector-runs/{ingest_run_id}/review-status`;
- `GET /connector-runs/{ingest_run_id}/review-queue`.

Existing repository transitions are available for queue orchestration, but not every CON-021 action maps cleanly to current persistence fields. Acknowledgement and reviewer ownership need explicit future persistence semantics before implementation.

## Decision

Accept route semantics for a future narrow connector human-review action API, but do not implement it in this slice.

Future route:

- `POST /connector-runs/{ingest_run_id}/review-actions`

Future request fields:

- `action`: one of `acknowledge`, `approve_for_connector_qa`, `request_fixture_fix`, `requeue_after_fix`, `cancel_review`;
- `reviewer_id`: non-empty reviewer/operator identity;
- `reason`: required for `request_fixture_fix`, `requeue_after_fix`, and `cancel_review`; optional for `acknowledge` and `approve_for_connector_qa`;
- `idempotency_key`: optional client-supplied key for repeated equivalent reviewer actions;
- `expected_status`: optional fail-closed guard against stale UI/API clients.

Future response fields:

- `ingest_run_id`;
- `job_id`;
- `action`;
- `status`;
- `reviewer_id`;
- `reason`;
- `idempotency_key`;
- `created_at`;
- `queue_item`.

Auth and reviewer expectations:

- The route must require an authenticated operator/reviewer boundary before implementation.
- The accepted reviewer identity must be non-empty and must match the authenticated principal or a documented service-account delegation rule.
- Anonymous, inferred, or empty reviewer IDs are rejected.

Transition expectations:

- The route mutates only `connector_review_status` queue rows.
- Missing queue rows return 404.
- Non-connector-review job types fail closed.
- Invalid transitions fail closed with 409.
- `source.ingest_runs` remains connector provenance/lifecycle authority and is not mutated.
- `jobs.job_queue` remains review orchestration state.
- Evidence, claims, reports, source schemas, job schemas, connector runtime, live I/O, and migrations remain out of scope.

Implementation preconditions:

- `acknowledge` cannot be implemented until reviewer ownership storage is accepted.
- `approve_for_connector_qa` cannot bypass existing queue transition semantics; implementation must either use an accepted queue transition path or add a planned repository method first.
- `request_fixture_fix`, `requeue_after_fix`, and `cancel_review` must require non-empty reasons.
- `requeue_after_fix` must reuse retry/requeue semantics and fail closed when attempts are exhausted.
- Durable idempotency and reviewer action history cannot be claimed until action logging, reviewer ownership storage, or an equivalent persistence decision is accepted.

## Consequences

- Future API mutation work has accepted route/reviewer/auth semantics.
- Implementation remains blocked until auth/reviewer identity enforcement and any needed reviewer-ownership persistence or repository transitions are explicitly planned.
- ADR Lane D 0014 records the current implementation blocker: this repo has no authenticated reviewer/operator principal dependency, so a review-action mutation route must not be implemented by trusting caller-supplied identity alone.
- Retry/cancel API surfacing remains separate from this route decision unless implemented through the accepted action route in a future planned slice.
- This slice changes no API behavior, OpenAPI, connector runtime, queue code, schemas, migrations, evidence, claims, reports, live I/O, hook config, or POSIX scripts.
