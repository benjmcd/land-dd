# Open Questions

These questions gate live-source, user-facing, or impact-heavy implementation.

## Critical

1. Which U.S. state and 3-5 counties are the MVP geography?
2. Should `api/openapi_stub.yaml` remain manually curated, or should generated
   FastAPI OpenAPI become the API authority?
3. What is the report review lifecycle before beta delivery: draft, needs
   review, approved, rejected, superseded, or another state model?
4. What workspace/user identity mechanism should scope API queries?

## Decided

1. First federal source candidate: FEMA NFHL (`DS-002`) is the reviewed source
   for the federal-first flood path. Live connector code remains gated by
   fixture-backed success/failure tests, source-failure behavior, and API/report
   caveat surfacing.

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
