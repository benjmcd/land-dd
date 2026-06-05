# Open Questions

These questions gate live-source, user-facing, or impact-heavy implementation.

## Critical

1. Which U.S. state and 3-5 counties are the MVP geography?
2. How should workspace/user identity be authenticated and enforced beyond the
   current explicit API fields?

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
4. Report request contract: synchronous report creation accepts optional
   workspace, requester, and idempotency metadata. Queued report jobs require an
   idempotency key, are workspace-scoped, and can be explicitly leased/executed
   into persisted report runs.
5. Dossier delivery gate: approved report runs can be served as Markdown rural
   land dossiers. Reports still in review, rejected reports, and superseded
   reports are not served as deliverable dossiers.

## High

1. Which golden parcels should represent flood, wetlands, access, zoning,
   slope/buildability, and source-failure regressions?
2. Beyond the approved Markdown endpoint, does beta need PDF, web page,
   dashboard, or operator UI dossier surfaces?
3. Which source/license fields are required in API responses versus internal
   metadata?
4. What cost metrics need to be measured during the first real source pass?

## Medium

1. Should source-specific observed-value payloads become JSON Schemas or remain
   runtime-validator-only for now?
2. Should report job execution run only through explicit operator/API calls, or
   should a scheduler/daemon be introduced for automatic processing?
3. Which UI/dashboard scope is worth doing before live county data exists?
