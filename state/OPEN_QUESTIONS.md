# Open Questions

These questions gate live-source, user-facing, or impact-heavy implementation.

## Critical

*(No open critical questions — all critical questions have been decided.)*

## Decided

1. MVP geography: **North Carolina — Buncombe County, Chatham County, Brunswick County** are
   accepted as the Private MVP Utility Proof geography (decided 2026-06-06). These counties
   cover mountain/slope (Buncombe), rural/piedmont/zoning-edge (Chatham), and coastal/wetland
   (Brunswick) representative stress cases. Fixture-backed connectors (flood, access, zoning)
   are used for private MVP; DS-010/DS-011 data is NOT_EVALUATED and recorded explicitly as
   unknown; DS-017 is deferred and not a private-MVP blocker.
2. First federal source candidate: FEMA NFHL (`DS-002`) is the reviewed source
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
6. Report authorization contract: report routes require trusted
   `X-Workspace-Id` and `X-User-Id` headers. Report creation/job submission bind
   workspace/requester to those headers; report/job reads, review actions,
   workspace filters, job execution, and dossier delivery fail closed across
   workspace boundaries.
7. Report operator worker: `scripts/run_report_worker.py` can execute a bounded
   number of queued report jobs through the authenticated public API.
8. Beta report identity boundary: report routes can run with
   `REPORT_AUTH_MODE=signed_token`, where a signed bearer token supplies
   workspace/user authority and mismatched identity headers fail closed.
9. Area/evidence workspace boundary: area creation/listing and evidence reads
   require request identity. Areas are bound to authenticated workspace/user
   claims, evidence reads are filtered through area ownership, and report
   creation/job submission rejects area IDs outside the authenticated workspace
   at both the API route and report-service boundary.
10. Fixture connector workspace boundary: connector fixture runs and connector
    review queue routes require request identity. Fixture evidence area IDs are
    preflighted against the authenticated workspace before durable writes;
    queue rows are workspace-scoped; review actions require `reviewer_id` to
    match the authenticated user.

## High

1. Which golden parcels should represent flood, wetlands, access, zoning,
   slope/buildability, and source-failure regressions?
2. Beyond the approved Markdown endpoint, does beta need PDF, web page,
   dashboard, or operator UI dossier surfaces?
3. Which source/license fields are required in API responses versus internal
   metadata?
4. What cost metrics need to be measured during the first real source pass?
5. Should a public beta use an external IdP/session issuer, or is the signed
   report identity token boundary sufficient behind a trusted product gateway?
6. What source-authority and tenancy contract should source-management routes
   and future live connector ingestion use once packaged deterministic fixtures
   are no longer the only connector path?
7. Do any pre-existing or direct-service null-owned area rows need a one-time
   ownership backfill before beta data is preserved behind authenticated APIs?

## Medium

1. Should source-specific observed-value payloads become JSON Schemas or remain
   runtime-validator-only for now?
2. Is bounded operator/API report-job execution sufficient for beta, or should a
   scheduler/daemon be introduced for automatic processing?
3. Which UI/dashboard scope is worth doing before live county data exists?
