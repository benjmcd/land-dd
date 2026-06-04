# ADR Lane D 0016: Connector Review Action Route Subset

## Status
Accepted

## Context

CON-021 defined connector review action vocabulary. CON-022 accepted the future `POST /connector-runs/{ingest_run_id}/review-actions` route shape. CON-025 added a tested local service-account reviewer principal dependency.

The remaining implementation risk is scope. Current queue repositories already support a few transitions, but not all planned actions. Adding a route for unsupported actions would either invent workflow semantics in the API layer or overclaim reviewer ownership/action-history persistence.

Session 1 is also working Lane C evidence-linkage and OpenAPI/schema parity in an isolated branch, so this pass avoids route registration and OpenAPI regeneration.

## Decision

The next connector review mutation route implementation, if pursued, must be limited to the actions that current repository authority supports:

- `request_fixture_fix`: map to `ConnectorReviewQueueRepository.mark_failed(...)`; only valid for a running `connector_review_status` queue item; requires a non-empty reason.
- `requeue_after_fix`: map to `ConnectorReviewQueueRepository.requeue_failed(...)`; only valid for a failed item with attempts remaining; requires a non-empty reason.
- `cancel_review`: map to `ConnectorReviewQueueRepository.cancel(...)`; valid only for nonfinal cancellable items; requires a non-empty reason.

The route must:

- require `LocalServiceAccountReviewerAuth` or an equivalent accepted reviewer principal dependency;
- compare any request `reviewer_id` to `ReviewerPrincipal.reviewer_id` and reject mismatches;
- fetch the queue item by `ingest_run_id` before transition and return 404 when absent;
- fail closed with 409 for invalid transitions, exhausted retry attempts, final jobs, and unsupported actions;
- return the current queue item shape after mutation;
- preserve `source.ingest_runs` as connector provenance/lifecycle authority;
- mutate only `jobs.job_queue` / connector review queue state;
- not mutate evidence, claims, reports, source records, connector runtime behavior, schemas, migrations, or live I/O.

Unsupported actions remain out of scope:

- `acknowledge` remains blocked until reviewer ownership storage is accepted.
- `approve_for_connector_qa` remains blocked until an accepted queue transition or repository method exists.
- Durable idempotency and reviewer action history remain blocked until action logging, reviewer ownership storage, or equivalent persistence is accepted.

## Consequences

- Future route work can implement a bounded mutation subset without revisiting action semantics.
- OpenAPI regeneration and route tests are deferred to the implementation slice, reducing conflict with Session 1's Lane C evidence-linkage/OpenAPI branch.
- The accepted route subset still does not create production auth, dashboard workflow, reviewer ownership persistence, action-history persistence, automatic retry policy, worker execution, or live connector behavior.

## Links

- `docs/adr/lane-d-0011-connector-human-review-actions.md`
- `docs/adr/lane-d-0012-connector-human-review-api-semantics.md`
- `docs/adr/lane-d-0015-connector-reviewer-principal.md`
- `backend/app/api/connectors.py`
- `backend/app/connectors/review_queue.py`
