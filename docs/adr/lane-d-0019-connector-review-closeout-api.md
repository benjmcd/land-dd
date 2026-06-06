# ADR Lane D 0019: Connector Review Closeout API

## Status
Accepted

## Context

Connector review queue repositories already supported worker lease, mark-succeeded,
mark-failed, requeue, and cancel transitions. The API exposed read-only review status and
queue state, plus a narrow review-action subset, but `request_fixture_fix` did not actually
mutate the queue item and `approve_for_connector_qa` remained blocked because no accepted
queue transition existed.

DS-002 FEMA NFHL live connector runs now create review queue items. Before report
integration can rely on review state, reviewers need a controlled closeout path that does
not mutate source retrieval provenance, evidence observations, claims, reports, schemas,
connector runtime behavior, or live source data.

## Decision

Add explicit connector review closeout transitions to the connector review queue
repository:

- `approve_for_connector_qa(job_id, reviewer_id, reason=None)`;
- `request_fixture_fix(job_id, reviewer_id, reason)`.

Both transitions are valid only for open review items with status `needs_review`,
`queued`, or `running`. Final or failed rows fail closed. The transitions record the
reviewer id, finish time, and latest reviewer decision in the queue-item payload.
`request_fixture_fix` also stores the reason in `last_error`.

Expose route-specific API actions:

- `POST /connector-runs/{ingest_run_id}/review-actions/approve_for_connector_qa`;
- `POST /connector-runs/{ingest_run_id}/review-actions/request_fixture_fix`;
- `POST /connector-runs/{ingest_run_id}/review-actions/requeue_after_fix`;
- `POST /connector-runs/{ingest_run_id}/review-actions/cancel_review`.

All routes require the accepted reviewer principal dependency. `request_fixture_fix`,
`requeue_after_fix`, and `cancel_review` require non-empty reasons. Responses include the
updated queue item so clients can verify the transition that actually occurred.

## Consequences

- Connector review closeout is now an explicit queue-orchestration workflow, not a
  passive acknowledgement.
- The latest reviewer decision is visible on the queue item, but this is not a durable
  action-history ledger.
- Report integration may now gate on approved connector review queue state in a later
  slice.
- Source retrieval runs remain connector provenance authority.
- Evidence observations, claims, reports, source records, connector runtime behavior,
  schemas, migrations, and live source data remain unchanged by closeout actions.

## Links

- `docs/adr/lane-d-0011-connector-human-review-actions.md`
- `docs/adr/lane-d-0012-connector-human-review-api-semantics.md`
- `docs/adr/lane-d-0016-connector-review-action-route-subset.md`
- `backend/app/api/connectors.py`
- `backend/app/connectors/review_queue.py`
