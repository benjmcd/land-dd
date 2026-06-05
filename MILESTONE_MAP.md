# Milestone Map

This file is the repo-local milestone authority. It resolves the historical
references in ADRs to `MILESTONE_MAP.md` and gives future implementation work a
single place to check what is complete, what is only fixture-ready, and what is
blocked by product/data/legal decisions.

## Status Legend

| Status | Meaning |
|---|---|
| Complete | Implemented and covered by the normal verification gate. |
| Fixture-ready | Works for the packaged/demo fixture slice, not live MVP production. |
| Contract-ready | The contract or schema exists, but runtime integration remains pending. |
| Blocked | Work should not proceed until a named authority gap is resolved. |
| Later | Intentionally out of the current MVP path. |

## Current Milestones

| Level | Milestone | Current status | Authority | Notes |
|---|---|---|---|---|
| 0 | Product and risk frame | Complete | `docs/PRODUCT_SPEC.md`, `docs/SECURITY.md`, `registers/risk_blocker_register.csv` | v1 scope and prohibited claims are documented. |
| 1 | Repo scaffold and verification gate | Complete | `README.md`, `docs/TESTING.md`, `scripts/verify.*` | Fast local gate is runnable. |
| 2 | Postgres/PostGIS system of record | Complete | `docs/POSTGRES_FIRST_STORAGE.md`, `docs/adr/0001-postgres-postgis-system-of-record.md`, `db/migrations/0001_initial_spine.sql` | DB smoke is CI-backed when local Docker/Postgres is unavailable. |
| 3 | Source registry and provenance model | Fixture-ready | `docs/adr/lane-a-0001-provenance-model.md`, `registers/data_source_registry.csv`, `templates/data_source_license_review.md` | Production source rights remain unresolved for most rows. |
| 4 | Area geometry contract and persistence | Complete | `backend/app/domain/area_contracts.py`, `backend/app/area_geometry/`, `tests/fixtures/geometries/` | Current slice is implemented; future area-type expansion may add adapters. |
| 5 | Evidence ledger persistence | Complete | `docs/adr/lane-c-evidence.md`, `schemas/evidence_schema.json` | Current evidence contract and persistence slice are implemented. |
| 6 | Rule and claim engine | Fixture-ready | `docs/adr/lane-c-rules.md`, `config/ruleset_homestead_mvp.yaml`, `schemas/claim_schema.json` | Rulepack is not a production jurisdictional rulepack. |
| 7 | Report run persistence | Fixture-ready | `docs/adr/lane-d-0001-report-persistence.md`, `backend/app/reports/` | Machine JSON exists; served dossier compilation is later. |
| 8 | Fixture connector runtime | Fixture-ready | `docs/adr/lane-d-0002-connector-entry-ownership.md`, `backend/app/connectors/` | Static access, flood, and zoning fixtures only. |
| 9 | Public API contract | Contract-ready | `api/openapi_stub.yaml`, `backend/app/api/` | Compact draft; needs workspace, async, and report-review semantics. |
| 10 | MVP geography and live-source path | Blocked | `docs/DATA_SOURCE_STRATEGY.md`, `registers/data_source_registry.csv`, `state/OPEN_QUESTIONS.md` | Needs selected geography and reviewed source rows. |
| 11 | User-facing dossier/dashboard | Later | `templates/report_template_rural_land_dossier.md` | Wait for API and source gates before productizing. |

## Next Milestone Gate

Before live-source or user-facing implementation, resolve Level 9 and Level 10:

1. Select the MVP state and target counties.
2. Record source license/review decisions for the first live data slice.
3. Promote the API contract beyond the compact draft for workspace scope,
   async/idempotent report generation, report review, and source-failure semantics.
4. Choose the first implementation slice from `docs/IMPLEMENTATION_READINESS.md`.

## Verification Caveat

Level 2 is complete against the current repository contract. Local DB smoke
requires Docker/Postgres on the machine; when those are unavailable, the DB
verification claim is CI-backed rather than locally reproduced.
