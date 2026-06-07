# Source Readiness Closure Plan

## Purpose

Close the remaining Must-priority source-readiness gaps without overclaiming production readiness. This plan starts from the current audited state: DS-001, DS-002, DS-003, DS-004, and DS-010 are ready; DS-011, DS-017, and DS-023 remain blocked or pending.

## Current facts

- DS-010 County GIS parcels is approved-with-restrictions for Chatham County only. The connector queries PIN, ACRES, and ZONING; owner, value, and sale-history fields remain excluded.
- DS-011 County assessor is NOT_EVALUATED. No county endpoint, access terms, schema, or privacy field policy has been selected.
- DS-023 Local zoning ordinance PDFs is fixture-backed only. No live county document connector, parsing policy, amendment-tracking policy, or redistribution review exists.
- DS-017 Commercial parcel data is blocked by vendor/license selection and is not required for the private MVP unless product scope changes.
- DB-enabled verification for the latest Lane 5 closeout is locally blocked by missing PostgreSQL client/runtime prerequisites.

## Immediate pass

1. Provision DB verification prerequisites.
   - Provide `psql`.
   - Start a Postgres/PostGIS database reachable by `DATABASE_URL_SYNC` or `postgresql://land:land@localhost:5432/land_diligence`.
   - Rerun `$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1`.
   - Record pass/fail evidence in `state/VALIDATION_LOG.md`.

2. Select official candidate sources for DS-011 and DS-023.
   - DS-011: choose the target county assessor/tax endpoints for the private MVP counties.
   - DS-023: Chatham County is the first live-candidate county; see `docs/source-reviews/ds-023-chatham-live-scope.md`.
   - Use official county or municipal sources first. Do not promote registry readiness from third-party mirrors.

3. Review rights and constraints before implementation.
   - Confirm cache, display, export, AI extraction, attribution, and raw-data restrictions per source.
   - For DS-011, decide the field policy for owner name, owner address, situs address, assessed value, sale history, and tax year.
   - For DS-023, decide the policy for PDF caching, extracted text retention, report excerpts, amendment dates, and citation text.

## Mid-term pass

1. Update source reviews.
   - Revise `docs/source-reviews/ds-011.md` and `docs/source-reviews/ds-023.md` with official URLs, terms evidence, field policy, and production decision.
   - Keep status pending if any blocking term, field, connector, or parsing question remains unresolved.

2. Update registry and seeds only if the review supports it.
   - Edit `registers/data_source_registry.csv`.
   - Edit `db/seeds/002_seed_source_registry.sql`.
   - Update `backend/tests/source_registry/test_source_readiness.py` and seed/readiness assertions to match the truthful count.

3. Implement connectors only after source authority is clear.
   - DS-011 connector: bounded county-specific endpoint or adapter, restricted field query, attribution/caveat mapping, failure evidence.
   - DS-023 connector: bounded live document retrieval or reviewed fixture/live hybrid, citation extraction, amendment-date handling, no unsupported legal interpretation.

4. Verify.
   - Run source-readiness JSON output.
   - Run targeted connector/source-registry/report tests.
   - Run `.\scripts\verify.ps1`.
   - Run DB-enabled verifier if prerequisites are available.

## Long-term path

1. Private MVP evidence integrity.
   - Maintain ready/blocker counts as auditable state, not aspirational state.
   - Keep restricted fields suppressed at connector/query boundaries.
   - Preserve source caveats in evidence, claims, reports, and exports.

2. Production hardening.
   - Re-run DB-backed smoke in an environment with PostgreSQL/PostGIS.
   - Close hosted-production readiness gates separately from private MVP proof.
   - Validate deployment, image publication, access-control, alerting, cost, release packaging, and backup/restore artifacts without seeding artifacts during validate-only actions.

3. Source expansion.
   - Promote additional counties only after county-specific source review and connector proof.
   - Revisit DS-017 only after a vendor, license, cost model, and product need are selected.

## Non-goals

- Do not expose owner/value/sale-history data without a reviewed field policy.
- Do not mark DS-011 or DS-023 production-ready from fixture evidence alone.
- Do not implement a live zoning or assessor connector before official source URLs and rights constraints are recorded.
- Do not claim hosted-production or DB-backed readiness from default local verification.

## Acceptance criteria

- DB-enabled verification is either passed and logged or remains explicitly blocked with prerequisite evidence.
- DS-011 and DS-023 reviews identify official source URLs, terms evidence, restrictions, field policy, and next review decision.
- Registry, seed, and test readiness counts match the source reviews exactly.
- All changed files pass `git diff --check`.
- Default verifier passes; DB verifier passes only when runtime prerequisites are present.
