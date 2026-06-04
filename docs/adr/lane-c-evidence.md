# Lane C ADR: Evidence Ledger Persistence

## Status

Accepted

## Context

Level 5 requires stored evidence to carry provenance, source failure state, area linkage, geometry where applicable, temporal/spatial precision, caveats, confidence, and amendment history. Claims and reports may interpret evidence, but no interpreted claim is valid without stored evidence.

The database already has `evidence.observations`, `evidence.observations.geometry`, and `audit.events`. Lane C needs a durable repository that preserves the current contract without broadening schema scope before the full vertical slice is proven.

## Decision

Use `evidence.observations` as the durable evidence ledger for the fixture-backed vertical slice.

- Evidence records are not silently overwritten. Corrections create a replacement evidence record and mark the prior record with `metadata.superseded_by`.
- Evidence create and supersede operations write durable audit events in `audit.events` with `target_table = 'evidence.observations'`.
- `source_id`, `evidence_code`, `observed_at`, and `superseded_by` remain in `evidence.observations.metadata` until a coordinated schema migration promotes them to columns.
- Evidence geometry is optional. When present, the contract requires GeoJSON geometry with SRID 4326, and the repository stores it in `evidence.observations.geometry`.
- Spatial precision is optional and stored as `metadata.spatial_precision_meters` until a later schema decision promotes it.
- Source failures are first-class evidence records. Missing source data must never be interpreted as "no issue found."
- Human verification notes remain typed evidence, separate from source-derived observations.

## Consequences

- Claims can require evidence IDs and reject superseded or missing evidence before report assembly.
- Evidence geometry can be queried by PostGIS without requiring every evidence type to carry geometry.
- Contract-only metadata must be validated on read; malformed durable metadata fails closed.
- A later schema migration may promote metadata fields, but must preserve reproducibility for existing report runs.

## Links

- `MILESTONE_MAP.md` Level 5
- `backend/app/domain/evidence_contracts.py`
- `backend/app/evidence_ledger/evidence_repo.py`
- `backend/app/evidence_ledger/audit_log.py`
- `backend/tests/evidence_ledger/test_sqlalchemy_evidence_repo.py`
