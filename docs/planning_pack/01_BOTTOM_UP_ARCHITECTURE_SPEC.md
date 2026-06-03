# 01 Bottom-Up Architecture Spec

Generated: 2026-05-28

## 1. Architectural thesis

The product should be built as a **geospatial evidence and claims system** with a map/report interface, not as a map product with AI bolted on.

Bottom-up order:

```text
Source registry
  -> raw source archive
  -> normalized Postgres/PostGIS tables
  -> derived features
  -> evidence ledger
  -> claim/rule execution
  -> report run
  -> API
  -> UI
```

## 2. Canonical layers

### 2.1 Source connector layer

Responsibilities:
- fetch or ingest data
- normalize source metadata
- preserve raw files
- calculate checksums
- create ingest run records
- record license/entitlement constraints
- fail loudly when a source cannot be reached

Non-responsibilities:
- no final business conclusions
- no opaque transformations without metadata
- no silent source fallback

### 2.2 Raw archive layer

Storage:
- object storage or filesystem-backed bucket
- immutable source snapshots
- raw PDFs, shapefiles, GeoPackages, CSVs, XML, JSON, COGs, GeoParquet, imagery references
- checksums and manifests in Postgres

Rule:
- never overwrite raw source files
- new source version = new object key + new dataset version row

### 2.3 Normalized geospatial warehouse

Primary store:
- Postgres/PostGIS

Responsibilities:
- normalized vector features
- authoritative area table
- source lineage columns
- spatial indexes
- derived feature views
- jurisdiction adapter tables
- audit and run tables

### 2.4 Derived feature store

Stored in Postgres unless too large.

Examples:
- parcel area
- slope statistics
- flood intersection area
- wetland intersection area
- distance to road
- nearest regulated facility
- zoning district extracted
- soil limitation summaries
- source freshness scores

### 2.5 Evidence ledger

Stores observations, not conclusions. Examples:
- `FLOOD_INTERSECTION_OBSERVED`
- `NWI_WETLAND_INTERSECTION_OBSERVED`
- `ROAD_ADJACENCY_NOT_FOUND`
- `ZONING_TEXT_EXTRACTED`
- `SOURCE_UNAVAILABLE`

### 2.6 Claims/rules engine

Transforms evidence into claims. Rules must be versioned, testable, and linked to an intent and, when needed, to a jurisdiction adapter.

### 2.7 Report compiler

Responsibilities:
- assemble a reproducible report
- include evidence references
- generate map snapshots
- list unknowns
- list failed source checks
- list verification tasks
- provide JSON and human-readable outputs

### 2.8 API/UI layer

UI should not duplicate logic. It should read report run status, area records, evidence records, claim records, map assets, and verification tasks.

## 3. Postgres-first storage pattern

### 3.1 What Postgres owns

Postgres owns durable truth for:
- users/workspaces
- areas/geometries
- source registry
- dataset versions
- licensing flags
- ingest runs
- normalized vector facts
- derived metrics
- evidence
- claims
- ruleset versions
- report runs
- jobs
- audit logs
- entitlements

### 3.2 What Postgres should not own directly

Avoid storing these as large BYTEA blobs:
- large rasters
- high-resolution imagery
- source archives
- bulky generated PDFs
- vector tile packages
- massive GeoParquet outputs

Store them in object storage and reference them from Postgres.

### 3.3 Recommended extensions

- `postgis`
- `pgcrypto`
- `citext`
- `pg_trgm`
- `btree_gist`
- `pgvector` optional after text/evidence retrieval requirements are proven
- `postgis_raster` only if needed; prefer COG/object storage for large rasters

## 4. Service boundaries

### Minimal v1 modules

| Module | Role |
|---|---|
| `source-registry` | CRUD source/dataset metadata and license flags |
| `ingestion-worker` | Pull and normalize datasets |
| `geometry-service` | Validate/simplify/project geometries |
| `feature-extractor` | Spatial overlays, buffers, distance, raster stats |
| `evidence-service` | Store and query evidence |
| `rules-service` | Execute gates/scoring/claims |
| `report-service` | Compile dossiers |
| `api-gateway` | User/workspace/API access |
| `review-console` | Human QA and override workflow |

These can begin as modules in one deployable. Extract services only when independent scaling, security boundaries, or team ownership justify the complexity.

## 5. Queue and workload model

### Fast path

For UI:
- fetch area record
- fetch cached derived metrics
- fetch report status
- serve vector tiles or precomputed map assets

### Slow path

For report generation:
- source checks
- spatial overlay
- raster statistics
- document retrieval
- LLM extraction
- rule execution
- report rendering
- human QA

Use a durable job queue with idempotent workers. A Postgres-backed queue is acceptable for MVP.

## 6. Scalability/throughput constraints

| Bottleneck | Mitigation |
|---|---|
| raster processing | precompute, tile, COG range access, async jobs |
| polygon overlay at scale | GiST indexes, tiling, prepared geometries, partitioning |
| county source variability | adapter framework and per-source QA |
| document parsing | caching, chunking, citations, human review |
| LLM costs | deterministic rules first, AI only for extraction/summarization |
| map tile cost | PMTiles/vector tile caching |
| report rendering | queue, reuse map assets |
| commercial data quotas | entitlement layer and query budgets |

## 7. Flexibility requirements

The architecture must support:
- adding a new state without schema rewrite
- adding a new country as an adapter
- replacing a parcel vendor
- changing a ruleset while preserving historical report runs
- running public-data-only reports when commercial data is unavailable
- flagging missing data instead of fabricating conclusions
- adding human verification evidence
- exporting machine-readable JSON for downstream workflows

## 8. Implementation constraints

1. Every table that stores source-derived data must include source or lineage references.
2. Every report must reference source versions.
3. Every claim must cite evidence IDs.
4. No inference can be stored without method/version metadata.
5. Failed source lookups must be first-class evidence.
6. Hard gates execute before weighted scores.
7. The UI must not recompute authoritative conclusions client-side.
8. Data-license entitlements must be enforced before display/export.
9. User-generated annotations must be separated from source-derived evidence.
10. PII/ownership data must have access controls and audit.

## 9. Open architectural questions

| Question | Why it matters | Recommended decision point |
|---|---|---|
| Which state/county first? | determines local adapters and source costs | before writing ingestion code |
| Which parcel vendor? | affects schema, license, and unit economics | before private beta |
| Use Postgres queue or external queue? | MVP simplicity vs throughput | start Postgres queue, revisit at batch scale |
| Use pgvector? | document retrieval convenience vs complexity | optional after evidence schema is stable |
| Use COG/GeoParquet internally? | interoperability vs operational overhead | use for heavy exchange/archive, not core truth |
| Human review required for all reports? | quality vs margin | all beta reports, later risk-based sampling |
