# ADR Lane D 0009: Report run schema contract

## Status
Accepted

## Context

Level 7 requires a report JSON schema, but before this ADR the report artifact surface was governed by `ReportRunContract`, `SqlAlchemyReportRunRepository`, and the normalized report regression test only. D-003 deferred the schema edit until source/evidence/claim schema scope was settled by the owning lanes.

Lane A, Lane C, and the planning-pack schema-copy follow-up now align the canonical source, evidence, and claim schemas to their serialized domain contracts. This gives Lane D enough lower-layer contract authority to propose the report-run schema without redefining nested evidence or claim structures.

## Decision

Add `schemas/report_run_schema.json` as the serialized `ReportRunContract` schema. The schema tracks `ReportRunContract.model_fields`, constrains `intent_code` and `status` to current enum values, and references the lane-owned evidence and claim schema IDs for nested `evidence`, `claims`, `unknowns`, and `red_flags` arrays.

`source_manifest` and `artifact_metadata` remain open objects. Their current contents are report-runtime manifests and artifact metadata, not stable cross-lane contracts. Tightening those maps requires a separate report manifest/schema decision after connector provenance, cost metrics, and report artifact metadata semantics stabilize.

The report-run schema does not model DB-only columns, connector queue records, source dataset/version/retrieval-run contracts, OpenAPI output envelopes, PDF output, or UI-specific report views.

## Consequences

- Report-run schema drift is test-enforced against `ReportRunContract`.
- Nested evidence and claim shapes remain owned by Lane C schemas rather than duplicated in Lane D.
- Report-run schema can support the Level 7 artifact requirement without blocking on future source provenance-family schemas.
- Source manifest and artifact metadata remain flexible until a narrower manifest contract is justified.
- OpenAPI refresh remains a separate future Lane D pass.

## Links

- `MILESTONE_MAP.md` Level 7
- `plans/2026-06-04-l7-closeout-l8-entry.md`
- `backend/app/domain/report_contracts.py`
- `schemas/report_run_schema.json`
- `schemas/evidence_schema.json`
- `schemas/claim_schema.json`
