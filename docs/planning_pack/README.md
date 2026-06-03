# Land/Area Due-Diligence Planning Pack

Generated: 2026-05-28

## Purpose

This pack specifies a bottom-up, Postgres-first plan for a land/locality intelligence system that can eventually support worldwide screening, while limiting the first product to a United States MVP.

The intended product is not a generic GIS viewer. It is an **intent-aware due-diligence compiler** that turns an area, parcel, polygon, or search constraint into source-linked evidence, interpreted claims, red flags, unknowns, and verification tasks.

## Primary architectural stance

1. **Bottom-up first.** Start with source metadata, storage, evidence, claims, and reproducible report runs. Do not start with the UI.
2. **Postgres/PostGIS as the system of record.** Use Postgres for sources, areas, evidence, claims, jobs, rules, audit, reports, and most vector-derived facts. Use object storage for raw heavy rasters/documents and store references/manifests in Postgres.
3. **Claim-first, not layer-first.** Map layers are evidence. The product value is defensible claim resolution.
4. **US/state MVP, global-ready core.** The core model must avoid hard-coding U.S. assumptions, but v1 should not pretend to provide global legal-grade diligence.
5. **Confidence separate from suitability.** Attractive land can still be low-confidence if title, access, water, zoning, or source freshness are unresolved.

## Files in this pack

| File | Use |
|---|---|
| `00_MASTER_SPEC.md` | Integrated project specification and scope boundary |
| `01_BOTTOM_UP_ARCHITECTURE_SPEC.md` | System architecture, service boundaries, Postgres-first implementation path |
| `02_POSTGRES_POSTGIS_STORAGE_SPEC.sql` | Executable-draft schema for a Postgres/PostGIS storage spine |
| `03_DATA_SOURCE_AND_INGESTION_SPEC.md` | Source classes, data-feed strategy, licensing, QA, blockers |
| `04_EVIDENCE_CLAIMS_RULES_SCORING_SPEC.md` | Evidence/claim model, red flags, rules, confidence, scoring |
| `05_MVP_US_RURAL_LAND_DOSSIER_SPEC.md` | Recommended first product and acceptance criteria |
| `06_GLOBAL_EXPANSION_STRATEGY.md` | Worldwide tiers and jurisdiction-adapter model |
| `07_FINANCIAL_CONSTRAINTS_AND_UNIT_ECONOMICS.md` | Cost centers, pricing implications, financial blockers |
| `08_SECURITY_LEGAL_COMPLIANCE_GOVERNANCE.md` | Fair housing, valuation, data rights, privacy, disclaimers |
| `09_QA_TESTING_OBSERVABILITY_SPEC.md` | Tests, quality gates, monitoring, reproducibility |
| `10_IMPLEMENTATION_ROADMAP_AND_BACKLOG.md` | Build phases and sequenced backlog |
| `11_API_AND_INTEGRATION_SPEC.md` | API boundaries and integration rules |
| `12_OPERATING_MODEL_AND_SOPS.md` | Human review, support, source maintenance, release operations |
| `13_ASSUMPTIONS_AMBIGUITIES_BLOCKERS.md` | Explicit open issues and decision gates |
| `14_ADR_LOG.md` | Architecture decision records |
| `15_GLOSSARY.md` | Shared vocabulary |
| `16_REFERENCE_SOURCES.md` | Seed reference sources and standards |
| `registers/*.csv` | Machine-usable source, risk, backlog, cost, and requirements tables |
| `planning_registers.xlsx` | Multi-sheet planning workbook |
| `schemas/*.json` | JSON schemas for source/evidence/claim/job objects |
| `config/ruleset_homestead_mvp.yaml` | MVP ruleset draft |
| `api/openapi_stub.yaml` | API contract draft |
| `templates/*.md` | Report, call script, and data-license review templates |
| `diagrams/*.mmd` | Mermaid diagrams |

## Recommended reading order

1. `00_MASTER_SPEC.md`
2. `13_ASSUMPTIONS_AMBIGUITIES_BLOCKERS.md`
3. `01_BOTTOM_UP_ARCHITECTURE_SPEC.md`
4. `02_POSTGRES_POSTGIS_STORAGE_SPEC.sql`
5. `03_DATA_SOURCE_AND_INGESTION_SPEC.md`
6. `04_EVIDENCE_CLAIMS_RULES_SCORING_SPEC.md`
7. `05_MVP_US_RURAL_LAND_DOSSIER_SPEC.md`
8. `10_IMPLEMENTATION_ROADMAP_AND_BACKLOG.md`

## Non-goals for v1

- No claim of legal, title, survey, engineering, wetland delineation, appraisal, insurance, lending, or investment advice.
- No worldwide legal-grade parcel diligence in v1.
- No automated valuation product for mortgage collateral use.
- No demographic steering, neighborhood desirability scoring, or protected-class proxy scoring.
- No single opaque universal land score.
