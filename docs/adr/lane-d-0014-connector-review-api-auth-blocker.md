# ADR Lane D 0014: Connector Review Action API Auth Blocker

## Status
Accepted

## Context

ADR Lane D 0011 defines future connector human-review actions. ADR Lane D 0012 accepts the future `POST /connector-runs/{ingest_run_id}/review-actions` route shape, reviewer identity expectations, and fail-closed transition behavior.

The current FastAPI app has no authenticated reviewer/operator principal dependency. Existing connector API routes are read-only, and existing queue mutation methods are repository-level only. Implementing a review-action mutation route now would either accept anonymous mutations or treat a caller-supplied header/body field as authentication. Both would contradict ADR Lane D 0012.

## Decision

Do not implement the connector human-review action API until an authenticated reviewer/operator boundary exists.

Current accepted blocker:

- `acknowledge` remains blocked because reviewer ownership storage is not accepted.
- `approve_for_connector_qa` remains blocked because no accepted queue transition maps it to current persistence.
- `request_fixture_fix`, `requeue_after_fix`, and `cancel_review` have repository-level mutation substrate, but API surfacing remains blocked until reviewer authentication and identity matching are implemented.
- Header-only identity such as `X-Reviewer-Id` is not sufficient by itself unless a future ADR defines it as a documented local service-account delegation rule with explicit non-production limits.
- The API route must reject anonymous, empty, inferred, or mismatched reviewer identities before mutating `jobs.job_queue`.

The next implementation-enabling slice should add a narrow reviewer principal dependency and tests, or document a service-account delegation rule, before any review-action route is added.

## Consequences

- The repo avoids shipping a mutation endpoint that overclaims auth or reviewer provenance.
- Existing read-only connector review APIs and repository-level queue transitions remain valid.
- Retry/cancel API surfacing remains future work until the reviewer/operator boundary is accepted and test-covered.
- No API route, OpenAPI change, queue code, schema, migration, connector runtime behavior, live I/O, hook config, POSIX script, evidence behavior, claim behavior, or report behavior changes in this blocker decision.

## Links

- `docs/adr/lane-d-0011-connector-human-review-actions.md`
- `docs/adr/lane-d-0012-connector-human-review-api-semantics.md`
- `backend/app/api/connectors.py`
- `backend/app/connectors/review_queue.py`
