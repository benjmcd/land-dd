# 10 Implementation Roadmap and Backlog

Generated: 2026-05-28

## 1. Build strategy

Build from the bottom up. The first milestone is not a polished UI; it is a working evidence pipeline and reproducible report run.

## 2. Phases

### Phase 0: manual validation

Goal: prove users value the dossier.

Deliverables:
- 20-30 manual parcel reports
- source checklist
- red flag taxonomy
- user interview notes
- preliminary price test
- source/time/cost log

Exit criteria:
- at least 5 paid or serious buyer/pro user commitments
- repeated source workflows identified
- top red flags validated
- target geography selected

### Phase 1: Postgres storage spine

Goal: durable source/area/evidence/report schema.

Deliverables:
- Postgres/PostGIS database
- schemas from `02_POSTGRES_POSTGIS_STORAGE_SPEC.sql`
- source registry seed
- area ingestion
- job queue
- audit events
- basic admin scripts

Exit criteria:
- can store area, source, dataset version, evidence, claim, report run
- source failure can be recorded
- report run has source manifest

### Phase 2: public data ingestion

Goal: load MVP public baseline sources.

Deliverables:
- parcel source for target counties
- FEMA flood overlay
- NWI wetlands
- USGS elevation/slope
- soils
- EPA ECHO
- road/access proxy
- zoning source/manual adapter

Exit criteria:
- 100 sample parcels enriched with basic features
- source version lineage complete
- data QA tests pass

### Phase 3: feature extraction and evidence

Goal: produce source-linked observations.

Deliverables:
- spatial overlay functions
- distance/buffer functions
- raster stats
- evidence records
- contradiction detection v0
- source failure recording

Exit criteria:
- each report-relevant feature has evidence rows
- failed data source produces visible unknown
- metrics reproducible by method version

### Phase 4: rules and claims

Goal: convert evidence into useful, safe claims.

Deliverables:
- hard-gate rules
- confidence bands
- red-flag taxonomy
- verification tasks
- homestead MVP ruleset
- safe-language lint

Exit criteria:
- golden parcels produce expected claims
- every claim links to evidence
- every high/critical claim has verification task

### Phase 5: report compiler

Goal: generate usable diligence dossier.

Deliverables:
- Markdown report
- JSON output
- map asset placeholders or generated maps
- source appendix
- reviewer notes workflow

Exit criteria:
- 20 automated+reviewed reports meet manual-quality threshold
- report can be re-run with same source versions
- cost metrics recorded

### Phase 6: private beta

Goal: charge for real reports.

Deliverables:
- private order flow
- reviewer console
- billing/manual invoicing if needed
- support workflow
- feedback capture

Exit criteria:
- positive gross margin after measured review cost
- users understand caveats
- issue rate manageable
- source coverage sufficient for target geography

### Phase 7: productization

Goal: self-serve or pro workflow.

Deliverables:
- UI
- map viewer
- report dashboard
- report purchase
- batch screening
- workspaces
- API

Exit criteria:
- 100+ paid reports or equivalent pro demand
- stable source refresh
- support and QA processes operational

## 3. Backlog structure

Use epics:
- E01 Source Registry
- E02 Postgres/PostGIS Core
- E03 Area/Geometry
- E04 Ingestion Adapters
- E05 Feature Extraction
- E06 Evidence Ledger
- E07 Rules/Claims
- E08 Report Compiler
- E09 Human Review
- E10 API
- E11 UI/Map
- E12 Billing/Entitlements
- E13 QA/Observability
- E14 Legal/Governance
- E15 Globalization/Jurisdiction Adapters

Detailed backlog is in `registers/backlog.csv` and `planning_registers.xlsx`.

## 4. Sequencing constraints

Do not build:
- scoring before evidence
- UI before report run model
- global adapters before U.S. MVP
- batch search before single-parcel evidence quality
- paid subscriptions before unit economics
- raw data exports before license review
- valuation features before legal review

## 5. Technical decision gates

| Gate | Decision |
|---|---|
| G1 | first state/counties selected |
| G2 | parcel data provider selected |
| G3 | source license review complete |
| G4 | Postgres schema accepted |
| G5 | evidence schema accepted |
| G6 | ruleset tested on golden parcels |
| G7 | human review process ready |
| G8 | unit economics measured |
| G9 | public beta launch approved |
