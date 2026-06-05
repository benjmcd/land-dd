# Lane Ownership

This file is the repo-local ownership authority for cross-cutting work. It
reconciles the ownership references in ADRs and prevents future implementation
passes from silently expanding across lane boundaries.

## Operating Rule

Use the narrowest lane that owns the invariant being changed. If a change needs
to modify another lane's implementation files, stop and record the cross-lane
reason before editing.

## Lane Map

| Lane | Owns | Primary paths | Must coordinate before changing |
|---|---|---|---|
| Lane A: Source and storage | Source registry, dataset versions, retrieval runs, license/usage metadata, migrations | `backend/app/source_registry/`, `db/migrations/`, `db/seeds/`, `registers/data_source_registry.csv`, `schemas/source*.json`, `templates/data_source_license_review.md` | Evidence payload semantics, report/API output, connector evidence mapping |
| Lane B: Area and geometry | Area contracts, geometry validation, geometry fixtures, PostGIS area persistence | `backend/app/area_geometry/`, `backend/tests/area_geometry/`, `tests/fixtures/geometries/` | Source registry changes, evidence storage, report output |
| Lane C: Evidence and claims | Evidence contracts, payload validation, evidence persistence, claim rules, rule-backed verification tasks | `backend/app/evidence_ledger/`, `backend/app/claims_engine/`, `schemas/evidence_schema.json`, `schemas/claim_schema.json`, `config/ruleset_homestead_mvp.yaml` | Source license/provenance fields, area geometry persistence, report/API envelope |
| Lane D: Reports and API | Public API routes, report runs, report artifacts, report/API surfacing | `backend/app/api/`, `backend/app/reports/`, `api/openapi_stub.yaml`, `templates/report_template_rural_land_dossier.md` | Source ingestion semantics, evidence/claim contracts, schema migrations |

## Connector Integration Zone

`backend/app/connectors/`, `backend/tests/connectors/`, and
`tests/fixtures/connectors/` are coordinator-owned integration zones. A connector
pass may edit these paths only when its scope names the connector and fixture
family it owns.

Connector work may read public APIs from Lane A, Lane B, Lane C, and Lane D. It
must not modify lane-owned implementation files unless the pass explicitly
records why the connector cannot be completed without that cross-lane change.

## Connector Lifecycle Authority

Source retrieval runs are the provenance authority for connector attempts.
`jobs.job_queue` may schedule or retry work, but it must not replace source
retrieval provenance.

## Migration Ownership

Lane A stewards `db/migrations/MIGRATION_REGISTRY.md`. Any migration pass must
claim a migration number before adding a migration file.

## Human Coordination Required

Human or coordinator review is required before:

- enabling a live connector;
- changing license, entitlement, export, cache, or AI-use behavior;
- introducing public user/workspace access control;
- changing report approval or beta-delivery semantics;
- broadening the MVP geography beyond the selected state/counties.
