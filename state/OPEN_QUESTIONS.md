# Open Questions

These questions gate live-source, user-facing, or impact-heavy implementation.

## Critical

1. Which U.S. state and 3-5 counties are the MVP geography?
2. What workspace/user identity mechanism should scope API queries?
3. What are the idempotency and async job semantics for report creation?

## Decided

1. First federal source candidate: FEMA NFHL (`DS-002`) is the reviewed source
   for the federal-first flood path. Live connector code remains gated by
   fixture-backed success/failure tests, source-failure behavior, and API/report
   caveat surfacing.
2. API authority mode: generated FastAPI OpenAPI is the runtime authority.
   `api/openapi_stub.yaml` remains a curated companion and is path/method
   drift-checked against the runtime schema.
3. Report review lifecycle: new report runs default to `needs_review`; reviewers
   can approve or reject them; approved reports can later be superseded. Review
   actions record reviewer identity, reason, transition, and timestamp.

## High

1. Which golden parcels should represent flood, wetlands, access, zoning,
   slope/buildability, and source-failure regressions?
2. What is the minimum served dossier surface: machine JSON, Markdown, PDF, web
   page, or a combination?
3. Which source/license fields are required in API responses versus internal
   metadata?
4. What cost metrics need to be measured during the first real source pass?

## Medium

1. Should source-specific observed-value payloads become JSON Schemas or remain
   runtime-validator-only for now?
2. When should async jobs move from report planning into report runtime?
3. Which UI/dashboard scope is worth doing before live county data exists?
