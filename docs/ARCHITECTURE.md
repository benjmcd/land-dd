# Architecture

## System purpose

Land Diligence is an evidence-first backend for area due diligence. It accepts an `Area` and `Intent`, gathers or receives source observations, stores evidence, derives cautious claims, and produces reproducible report runs.

It is not a GIS viewer, legal-title system, appraisal engine, insurance engine, lending system, or global land registry. Those may be adjacent integrations later.

## Core architectural stance

```text
source registry
  -> source connector / manual observation
  -> raw source reference
  -> normalized evidence
  -> claim/rule engine
  -> report run
  -> API / later UI
```

The architecture is claim-first rather than layer-first. Map layers are evidence inputs. They are not product conclusions.

## Components

| Component | Path | Responsibility | Must not do |
|---|---|---|---|
| API | `backend/app/api/` | Thin request/response layer | Own business rules or persistence semantics |
| Domain | `backend/app/domain/` | Contracts, enums, invariants | Call live vendors directly |
| Persistence | `backend/app/db/`, `db/migrations/` | Postgres/PostGIS storage | Hide source failures |
| Source registry | `db/seeds/`, `schemas/source_schema.json` | Dataset/license/provenance metadata | Treat unknown license as allowed |
| Evidence ledger | DB tables + contracts | Store observations and failures | Generate claims without traceability |
| Rule/claim engine | future `backend/app/rules/` | Convert evidence into cautious claims | Make legal/appraisal/final truth assertions |
| Report runs | DB + future compiler | Reproducible dossier runs | Be non-reproducible or source-version opaque |
| Connectors | future `backend/app/connectors/` | Fixture-first data acquisition | Use live APIs without approval/license review |

## Key domain objects

```text
Source       dataset, authority, license, cache/export/AI-use flags, refresh cadence
Area         parcel/polygon/locality/corridor/candidate-region geometry and metadata
Evidence     source-linked observation, failure, extraction, calculation, or human verification
Claim        cautious assertion derived from evidence IDs
Rule         deterministic mapping from evidence conditions to claims/red flags
ReportRun    reproducible run over area + intent + source/model/rules versions
ReviewNote   human verification, caveat, override, or professional-review marker
```

## Architectural invariants

- Postgres/PostGIS is the system of record for structured facts, evidence, claims, reports, jobs, audit, entitlements, and vector-derived metrics.
- Object storage is for large immutable artifacts: rasters, PDFs, source archives, report PDFs, tile bundles. Store references and checksums in Postgres.
- Every derived claim must trace to evidence IDs.
- Every evidence item must trace to a source or explicit manual/human verification record.
- Failed data lookups are evidence with `source_unavailable`/`unknown`, not absence of risk.
- No single universal score. Hard gates first, then intent-specific suitability bands, separately from confidence.
- Every report run must store source versions, ruleset version, code/model version if applicable, timestamp, and assumptions.

## Data flow

1. User or batch process defines an `Area` and `Intent`.
2. The system validates geometry and stores the area.
3. Source adapters or fixtures produce raw observations and source references.
4. Feature extraction creates evidence records.
5. Rules evaluate evidence into claims, red flags, unknowns, and verification tasks.
6. Report run stores claims, evidence references, ruleset version, and output artifacts.
7. API exposes report status and evidence-linked summaries.

## Scalability pattern

Use two paths:

| Path | Purpose | Pattern |
|---|---|---|
| Interactive/API | Fast lookups and report status | cached summaries, indexed PostGIS queries |
| Analytical/report | Heavy overlays, raster stats, document extraction | queued jobs, precomputed features, resumable tasks |

Do not make the UI or synchronous API wait on arbitrary raster/document work.

## Extension points

| Add | Modify |
|---|---|
| New source | source registry, license review, connector fixture, connector tests |
| New evidence type | DB enum/table contract, Pydantic contract, tests, docs |
| New claim/rule | ruleset YAML, claim contract tests, report template |
| New intent | intent seed, ruleset, score weights, report section template |
| New geography | jurisdiction adapter, source registry entries, fixtures, caveats |

## Known tradeoffs

- Postgres-first favors operational clarity and flexible querying over specialized lakehouse performance in v1.
- Fixture-first connectors delay live-data polish but reduce licensing and reproducibility risk.
- Cautious claim language may feel less decisive, but it is necessary to avoid false precision and liability.
- Global-ready abstractions are required, but v1 must remain U.S. rural land scoped.
