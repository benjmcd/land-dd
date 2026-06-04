# Postgres/PostGIS Storage Policy

## Decision

PostgreSQL + PostGIS is the system of record for v1. It stores structured entities, provenance, evidence, claims, report runs, audit, jobs, source registry, entitlements, and vector-derived metrics.

## What belongs in Postgres

- source registry and license metadata
- areas and geometries
- normalized evidence
- claims and claim/evidence links
- report runs and report sections
- ruleset/version references
- audit log and human review notes
- job queue and job state for early implementation
- vector features and summary metrics

## What does not belong directly in Postgres

- large rasters
- satellite/source imagery
- source PDFs/archives
- generated PDF reports
- large tile bundles
- vendor data dumps when license prohibits storage

Store those in object storage or local artifact storage with immutable URI, checksum, size, source, and retrieval metadata in Postgres.

## Schema principles

- Prefer explicit tables for domain invariants and JSONB for source-specific detail.
- Use PostGIS `geometry` columns for canonical geometry.
- Enforce SRID and geometry validity.
- Use join tables for claim-evidence relationships.
- Preserve historical report reproducibility; do not mutate past report semantics silently.
- Add migrations in small reversible slices.

## Initial schema areas

The initial migration in `db/migrations/0001_initial_spine.sql` should establish:

- extensions
- enums/domains
- sources
- intents
- areas
- evidence
- claims
- report runs
- jobs
- audit/review tables

## Future migration policy

Before changing schema:

1. write/update a plan;
2. update an ADR if architecture-level;
3. add contract tests;
4. create migration;
5. run DB smoke test;
6. update seed data or fixtures;
7. update docs/state.
