# Lane C Schema Contracts

## Status

Accepted on 2026-06-04.

## Context

The active shared schema files `schemas/evidence_schema.json` and `schemas/claim_schema.json` had drifted from the current Lane C Pydantic domain contracts. The D-003 schema-contract alignment note in `plans/2026-06-04-l7-closeout-l8-entry.md` assigned evidence and claim schema follow-up to Lane C after cross-lane review, while reserving source, job, and report schema decisions for their owning lanes or coordinator review.

## Decision

The canonical root evidence and claim JSON schemas represent the serialized `EvidenceContract` and `ClaimContract` field sets. They do not represent database rows, stale planning-pack snapshots, future report/export envelopes, or type-specific `observed_value` payload schemas.

Lane C keeps schema parity tests for these files in `backend/tests/evidence_ledger/test_evidence_schema_contract.py` and `backend/tests/claims_engine/test_claim_schema_contract.py`. Those tests assert field-set parity, enum parity, stale-field exclusion, and serialized Pydantic output parity without adding a JSON Schema runtime dependency.

## Consequences

- Report and connector work can reference the root evidence and claim schemas as current Lane C contract truth.
- `docs/planning_pack/schemas/*.json` remains a docs-packaging surface and may be stale until a separate packaging pass reconciles it.
- Source, job, report-run, and connector-envelope schemas remain outside this ADR.
- Type-specific `observed_value` schemas remain deferred until a dedicated payload-schema pass decides whether to encode those constraints in JSON Schema or leave them enforced by Lane C runtime validators.
