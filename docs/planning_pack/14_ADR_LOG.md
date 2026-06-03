# 14 Architecture Decision Records

Generated: 2026-05-28

## ADR-001: Use Postgres/PostGIS as system of record

Status: proposed/accepted for planning

Decision:
Use Postgres/PostGIS as the durable system of record for source registry, areas, vector facts, evidence, claims, rules, reports, jobs, audit, and entitlements.

Rationale:
- flexibility
- geospatial support
- transactional consistency
- mature indexing
- broad operational knowledge
- avoids early polyglot fragility
- supports modular monolith architecture

Consequences:
- heavy rasters/raw files should live in object storage
- careful indexing/partitioning needed for scale
- do not force every data type into Postgres if object references are safer

## ADR-002: Claim-first model

Status: proposed/accepted for planning

Decision:
Model evidence and claims separately.

Rationale:
Map layers do not answer user questions. Claims must cite evidence, source versions, and caveats.

Consequences:
- more schema complexity
- better auditability
- safer output language
- stronger trust moat

## ADR-003: U.S. rural land MVP

Status: proposed

Decision:
First product should be a rural land/homestead diligence dossier in 3-5 U.S. counties.

Rationale:
Broad global version is too complex; rural land has clear pain and tractable first-pass data.

Consequences:
- not worldwide in v1
- requires local source adapters
- proof-of-value before scale

## ADR-004: Modular monolith first

Status: proposed

Decision:
Start as a modular monolith with clear modules and async workers.

Rationale:
Distributed microservices would create premature fragility.

Consequences:
- module boundaries must be enforced in code
- extraction possible later
- one database simplifies transactions/audit

## ADR-005: Suitability and confidence separated

Status: proposed/accepted for planning

Decision:
Never publish suitability without confidence.

Rationale:
A parcel can look attractive but have stale/missing/conflicting data.

Consequences:
- reporting is more nuanced
- protects against false precision
- may frustrate users who want one number

## ADR-006: Human review in beta

Status: proposed

Decision:
All beta reports require human review.

Rationale:
Source quality and rules are not yet proven; legal/product risk high.

Consequences:
- lower throughput
- higher cost
- better feedback loop
