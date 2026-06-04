# ADR 0001: Postgres/PostGIS as system of record

## Status
Accepted

## Context
The product requires durable source registry, evidence, claims, geometry, report runs, audit, and reproducibility. The user specifically prioritized Postgres for maximum non-fragility, flexibility, and utility.

## Decision
Use PostgreSQL + PostGIS as the v1 system of record. Use object storage only for large immutable assets and store references/checksums in Postgres.

## Consequences
- Domain logic should target Postgres-backed contracts rather than vendor schemas.
- Heavy raster/imagery processing may later require specialized stores, but not as the primary transactional source.
- Schema migrations must preserve report reproducibility.
