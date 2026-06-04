# Project State

## MILESTONE_MAP status block

```text
Current milestone: Level 5 - Evidence Ledger
Milestone status: PASS
Last verified: 2026-06-04
Verification command(s):
- cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/evidence_ledger
- cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/evidence_ledger tests/claims_engine
- cd backend; ruff check app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
- cd backend; mypy app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
- cd backend; rg -n "from app\.source_registry|from app\.area_geometry|import app\.source_registry|import app\.area_geometry" app/evidence_ledger app/claims_engine
- cd backend; py -3.12 -m pytest --collect-only -q
- $env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
Verification result:
- 235 tests pass; lint clean; mypy clean (81 source files)
- Local Postgres/PostGIS starts from repo instructions, migrations apply cleanly, seeds apply deterministically, and DB smoke validates required schemas, tables, columns, enums, foreign keys, and seeds
- Source versioning, retrieval lifecycle, caveats, freshness, authority, and license/review/usage-right metadata are implemented and surfaced downstream
- Lane B area/geometry slice now includes a SQLAlchemy/PostGIS `core.areas` repository that round-trips Polygon/MultiPolygon GeoJSON as SRID 4326 MultiPolygon geometry, supports all six Level 4 domain area types with explicit metadata-preserved domain type mapping, preserves source/confidence/validated fields, reads PostGIS-derived area/centroid/bbox metrics, queries fixture spatial relations through PostGIS, and stores immutable prior-geometry rows in `core.area_versions` on geometry replacement
- Lane C evidence/claim/rule-engine slices pass targeted runtime, type, lint, and import-isolation checks; the evidence ledger now has a SQLAlchemy/Postgres repository for `evidence.observations`, durable evidence audit events in `audit.events`, first-class optional evidence geometry mapped to `evidence.observations.geometry`, and spatial precision preserved in evidence metadata
- Lane D report runs now persist through `reports.report_runs` and a machine-readable JSON artifact under `OBJECT_STORE_ROOT`
Failed or blocked gates:
- No Level 5 blockers remain in the fixture-backed DB repository path verified on 2026-06-04.
- L5-001 through L5-010: PASS for the DB-backed evidence repository/service scope (source observations, source failures, spatial intersections, derived metrics, document extracts, human verification notes, geometry/SRID/spatial precision, invalid payload rejection, supersession, deterministic retrieval, rollback behavior, durable audit events, and the evidence-ledger persistence ADR are tested or documented)
- L6-001/L6-004/L6-006/L6-007: PARTIAL/PASS with durable claim persistence for current scope (stored claims require evidence links, `claims.claim_evidence` links are DB-backed, unknown claims require source-failure evidence, severity/confidence stay separate, and verification tasks persist to `claims.verification_tasks`)
- L6-002/L6-003/L6-010: PARTIAL/PASS for flood, access, zoning, water, wetlands, and slope hard-gate rules (ruleset ID/version load, deterministic claim IDs, and rule logic lives in `rule_engine.py`, not an LLM/UI prompt)
- L6-005/L6-008/L6-009: PARTIAL/PASS for current flood/access/zoning/water/wetlands/slope rule scope (rule-generated claims propagate caveats and cover positive, negative/no-claim, unknown/source-failure, explicit stale fixture signal, contradiction/needs-review where implemented, incomplete evidence where implemented, superseded evidence, empty input, multi-area, input-order determinism, and invalid-rule-config cases)
Completion evidence:
- state/VALIDATION_LOG.md
- backend/tests/source_registry/ (41 tests)
- backend/tests/area_geometry/ (46 tests)
- backend/app/domain/area_contracts.py (`AreaContract`, `AreaMetricsContract`, `AreaSpatialRelationContract`, `AreaVersionContract`)
- backend/app/area_geometry/models.py (`AreaModel`, `AreaVersionModel`)
- backend/app/area_geometry/area_repo.py (`SqlAlchemyAreaRepository`)
- backend/tests/evidence_ledger/ and backend/tests/claims_engine/ (130 tests)
- backend/app/domain/evidence_contracts.py (`EvidenceContract` with optional GeoJSON/SRID/spatial precision fields)
- backend/app/evidence_ledger/evidence_repo.py (`SqlAlchemyEvidenceRepository`)
- backend/app/evidence_ledger/audit_log.py (`SqlAlchemyEvidenceAuditLog`)
- docs/adr/lane-c-evidence.md
- backend/app/claims_engine/claim_repo.py (`SqlAlchemyClaimRepository`)
- docs/adr/lane-c-rules.md
- backend/app/reports/service.py
- backend/app/reports/models.py
- backend/app/reports/report_repo.py
- backend/app/reports/adapters.py
- docs/adr/lane-d-0001-report-persistence.md
- backend/tests/reports/test_report_repository.py (1 test)
- backend/tests/reports/test_adapters.py (4 tests)
- backend/tests/reports/ and backend/tests/api/ (16 tests)
- db/seeds/source_registry_seeds.py
- scripts/seed_sources.py
- docs/adr/lane-a-0001-provenance-model.md
- templates/data_source_license_review.md
- registers/data_source_registry.csv
- schemas/source_schema.json
- tests/fixtures/geometries/
Next lowest-dependency task:
- Lane C/Lane D coordination: close the remaining Level 6 rule-category gap by implementing or explicitly marking not-evaluated categories for soil/septic, environmental hazards, market context, and resource context before claiming a complete rules/report workflow
Do not work on yet:
- Live connectors
- UI or LLM summaries
- Production ops/security/observability
- New jurisdictions or intents until durable Level 6 claim persistence and Level 7 report/API workflow gates pass
```


## Current objective

Build the foundation vertical slice for the land/locality due-diligence compiler:

```text
source registry -> area geometry -> evidence -> claim -> report run -> API response
```

## Active plan (overall)

`plans/2026-06-03-foundation-vertical-slice.md`

## 4-lane agent architecture (active)

This workspace uses 4 isolated agent lanes, each with dedicated scope, plans, and state files.
See `LANE_OWNERSHIP.md` for ownership boundaries.

| Lane | Scope | Active plan | State | Milestone gates |
|---|---|---|---|---|
| Lane A | Source Registry + DB Infrastructure | `plans/lane-a-2026-06-03-source-registry.md` | `state/lane-a-state.md` | L2-*, L3-* |
| Lane B | Area + Geometry Domain | `plans/lane-b-2026-06-03-area-geometry.md` | `state/lane-b-state.md` | L4-* |
| Lane C | Evidence Ledger + Claims Engine | `plans/lane-c-2026-06-03-evidence-claims.md` | `state/lane-c-state.md` | L5-*, L6-* |
| Lane D | Reports + API + Platform | `plans/lane-d-2026-06-03-reports-api-infra.md` | `state/lane-d-state.md` | L7-* |

**Each lane agent must read `LANE_OWNERSHIP.md` before any code change.**

## Key constraints

- Bottom-up implementation only.
- Postgres/PostGIS is system of record.
- Evidence-before-claim invariant is non-negotiable.
- No live data connectors before license/source registry/fixture tests.
- No UI or LLM work until the storage/evidence/claim/report spine works.
- Lane agents MUST NOT modify files owned by other lanes.

## Known blockers / undecided items

| Item | Status | Impact |
|---|---|---|
| MVP state/counties | Undecided | Do not hard-code jurisdiction-specific logic |
| Parcel vendor | Undecided | Use fixtures/public source registry only |
| Live connector credentials | Unavailable | No live API/vendor integrations |
| Docker availability | Available | DB smoke now passes locally |

## Last verified state

235 tests pass; lint clean; mypy clean (81 source files). DB smoke passes with schema/table/column/enum/FK/seed assertions.

## Local repo bootstrap state

- Local Git initialized on `main`.
- `origin` is configured as `https://github.com/benjmcd/land-dd.git`.
- Local baseline commit exists on `main`: `ffb73e1` (`Establish governed scaffold baseline`).
- No GitHub push has been performed; `origin/main` remains at `13b75a9`.
- Local Codesight index exists at `.codesight/`; regenerate after significant code changes.

