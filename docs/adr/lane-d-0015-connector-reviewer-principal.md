# ADR Lane D 0015: Connector Reviewer Principal Boundary

## Status
Accepted

## Context

CON-024 records that connector review mutation API implementation is blocked until an authenticated reviewer/operator boundary exists. Existing connector review APIs are read-only, and repository-level queue mutation methods already exist for some future actions. A full product auth system is outside the current Level 8 fixture workflow, but future review-action routes still need a concrete fail-closed principal boundary before route implementation.

## Decision

Add a narrow, local service-account reviewer principal dependency under Lane D API code.

The dependency:

- accepts `X-Reviewer-Id` and `X-Reviewer-Token`;
- requires a configured allow-list of reviewer service-account IDs and tokens supplied by the caller constructing the dependency;
- strips surrounding whitespace from accepted values;
- rejects missing or blank credentials with 401;
- rejects unknown reviewer IDs or wrong tokens with 403;
- fails closed with 503 when no service-account allow-list is configured;
- returns a `ReviewerPrincipal` with `auth_scheme = "local_service_account"` after token validation.

This is a local fixture/developer substrate only. It does not register a route, mutate queue rows, add production auth, add settings/secrets, change OpenAPI, or claim durable reviewer action history. Any future review-action request that still carries a `reviewer_id` field must compare that request value to the authenticated `ReviewerPrincipal.reviewer_id`.

## Consequences

- Future connector review mutation routes have a tested principal dependency to use before mutating `jobs.job_queue`.
- Header-only reviewer identity remains rejected; the accepted local rule requires a configured token for the reviewer service account.
- Production auth, reviewer ownership persistence, reviewer action history, and mutation routes remain separate planned slices.
- No connector runtime behavior, queue mutation route, report behavior, evidence behavior, claim behavior, schema, migration, live I/O, hook config, or POSIX script changes in this slice.

## Links

- `docs/adr/lane-d-0014-connector-review-api-auth-blocker.md`
- `docs/adr/lane-d-0012-connector-human-review-api-semantics.md`
- `backend/app/api/reviewer_auth.py`
- `backend/tests/api/test_reviewer_auth.py`
