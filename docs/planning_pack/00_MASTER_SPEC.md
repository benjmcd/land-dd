# 00 Master Spec: Intent-Aware Area Due-Diligence Compiler

Generated: 2026-05-28

## 1. Project definition

Build a system that analyzes a place for a stated intent and produces an evidence-backed decision file.

### 1.1 One-sentence product

An **intent-aware due-diligence compiler** that takes a parcel, polygon, locality, or generated candidate region and returns source-linked evidence, interpreted claims, red flags, unknowns, confidence levels, and next verification steps.

### 1.2 Primary v1 market

The recommended MVP is a **United States rural land / homestead / small-investor diligence dossier** for a limited geography, ideally 3-5 counties in one state.

### 1.3 Long-term market

The long-term product can support rural land purchase, homestead feasibility, small development, farmland evaluation, conservation acquisition, energy/infrastructure siting, mineral/resource screening, regional investment research, and global environmental/physical screening.

### 1.4 Core constraint

The system must distinguish physical/geospatial facts, legal/regulatory facts, market facts, interpretations, unknowns, and professional verification tasks. It must not collapse them into one unqualified score.

## 2. Scope boundary

### 2.1 In scope for MVP

| Area | In scope |
|---|---|
| Geography | 3-5 counties in one selected U.S. state |
| Input | Parcel ID, address, coordinates, drawn polygon, uploaded parcel list |
| Intent | Rural land purchase / homestead feasibility |
| Data | public baseline layers, selected commercial parcel source, local zoning/assessor/recorder where feasible |
| Output | web/Markdown dossier, red flags, evidence ledger, maps, unknowns, verification checklist |
| Automation | source ingestion, spatial overlays, feature extraction, rules, report draft |
| Human role | QA review for high-risk claims and uncertain sources |

### 2.2 Out of scope for MVP

| Area | Out of scope |
|---|---|
| Legal advice | The system can flag issues; it cannot determine legal rights conclusively |
| Title/survey | It cannot replace title search, title insurance, or licensed survey |
| Wetland delineation | NWI and remote data are screening inputs, not field determinations |
| Appraisal/AVM | Do not position as mortgage-collateral valuation |
| Insurance underwriting | Do not decide insurability |
| Global legal diligence | Future tier, not v1 |
| Demographic area ranking | Avoid fair-housing/steering risk |

## 3. Product object model

### Area

An area is the subject of analysis: parcel, multi-parcel assemblage, user-drawn polygon, address-derived area, administrative locality, watershed, corridor, or generated search candidate. Minimum attributes: stable ID, type, geometry, centroid, bounding box, CRS/SRID, geometry source, geometry confidence, and version history.

### Intent

An intent describes why the area is being evaluated. Initial intents are `rural_land_purchase` and `homestead_feasibility`. Future intents include farmland, development, solar, data center, conservation, mineral/resource screen, and speculative hold.

### Evidence

Evidence is a source-linked observation: parcel intersects flood polygon, parcel has 18% mean slope, county zoning text contains a minimum lot area, NWI maps a wetland feature, no public road adjacency was detected, or a source was unavailable.

### Claim

A claim is an interpreted assertion derived from evidence: mapped flood constraint present, legal access cannot be verified, residential use appears possibly compatible but county confirmation is required.

### Report

A report is a reproducible run: fixed input geometry, source versions, ruleset version, model/prompt versions, timestamp, output sections, source appendix, unknowns, and verification tasks.

## 4. Architectural principles

1. Build source registry, area/geometry model, evidence schema, Postgres storage, ingestion adapters, feature extraction, claims/rules, report runs, report templates, API, UI, and batch screening in that order.
2. Use Postgres/PostGIS as the system of record for sources, areas, evidence, claims, rules, reports, jobs, audit, and most vector-derived metrics.
3. Use object storage for raw rasters, raw source archives, original PDFs, generated reports, tile packages, large GeoParquet/COG/STAC assets.
4. Avoid false precision: every score must include evidence count, source freshness, authority level, missing-source count, contradictions, and confidence band.
5. Treat failed source lookups as first-class evidence.
6. Do not hide contradictions behind a final score.

## 5. Product outputs

### Dossier sections

1. Executive summary
2. Area identity
3. Data confidence summary
4. Deal-killer gates
5. Buildability
6. Access
7. Flood/wetlands
8. Soil/septic proxy
9. Water context
10. Zoning/use
11. Environmental/compliance hazards
12. Resource/mineral/public-land context
13. Market context
14. Unknowns
15. Verification tasks
16. Source appendix
17. Machine-readable JSON output

### Severity bands

| Severity | Meaning |
|---|---|
| Critical | plausible deal killer; do not proceed without verification |
| High | material risk; must verify before offer/closing |
| Medium | relevant risk; affects price/terms/inspection |
| Low | informational |
| Unknown | data unavailable or inconclusive |

### Suitability bands

- Strong candidate
- Potential candidate
- High-risk candidate
- Insufficient information
- Not compatible with stated intent based on available evidence

## 6. Top-level requirements

Detailed requirements live in `registers/requirements_traceability.csv`.

Core requirements:
- Store every source and evidence item with provenance.
- Reproduce every report from stored versions.
- Support PostGIS geometry operations.
- Separate source observations from interpreted claims.
- Support explicit unknowns and failed-source records.
- Support jurisdiction adapters.
- Support hard gates before scoring.
- Support human QA on high-severity outputs.
- Enforce data-license entitlements.
- Avoid protected-class and valuation-risk features in MVP.

## 7. Key assumptions

1. Initial geography is U.S.-only.
2. MVP can be limited to 3-5 counties in one state.
3. Commercial parcel data is likely required for serious usability.
4. Public national datasets are adequate for physical/environmental screening, not legal-grade diligence.
5. Zoning and local land-use interpretation are the hardest MVP workflow.
6. Human QA remains necessary until source coverage and rule behavior are validated.
7. Postgres/PostGIS can handle MVP and early pro scale if raster-heavy data is stored externally.
8. Global expansion is feasible only as tiered screening first, not parcel/legal diligence everywhere.

## 8. Primary blockers

1. Parcel/ownership licensing.
2. County-level zoning fragmentation.
3. Legal access/easement verification.
4. Water rights and well viability.
5. Mineral rights severance and stale mineral datasets.
6. Wetlands/flood data being screening inputs, not field/legal determinations.
7. Fair housing and valuation compliance if residential recommendation or valuation features expand.
8. Unit economics if reports are underpriced relative to data and QA cost.
9. Overbuilding global scope before validating U.S. MVP demand.

## 9. Acceptance criteria for v1 product readiness

The MVP is ready for private beta only when:
- 100 test parcels can be processed with source/run lineage.
- At least 20 manually reviewed reports establish baseline quality.
- Each report explicitly lists unknowns and source failures.
- High-severity claims include evidence links and verification tasks.
- Re-running a report with the same source versions produces materially identical output.
- The system can explain why a parcel failed a hard gate.
- No report uses demographic/protected-class filters.
- Data licenses permit intended customer display/export.
- Human reviewer can override or annotate claims.
- Cost per report is measured, not guessed.
