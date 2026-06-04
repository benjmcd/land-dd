# ADR Lane D 0013: Report Metadata Extension Boundary

## Status
Accepted

## Context

ADR Lane D 0010 tightened the stable generated report metadata keys in `schemas/report_run_schema.json` while keeping nested metadata maps open for additive extension. Since then, Lane A source provenance-family schemas were aligned, connector review semantics were planned, and connector-local fixture quality coverage deepened.

The remaining report metadata gap is not a need for immediate schema or runtime mutation. It is a boundary question: which future metadata belongs in report artifacts, which metadata remains owned by connector/source/job systems, and which claims must not be made until lower-layer lineage exists.

## Decision

Future report metadata extensions must be additive, namespaced, and promoted to stable schema keys only after the producing lower layer is accepted and test-covered.

Accepted future extension families:

- `artifact_metadata.rendering`: future report rendering/export metadata such as format, renderer version, checksum, or derived artifact URIs.
- `artifact_metadata.validation`: future validation-run metadata such as verification command identity, fixture profile version, or contract version fingerprints.
- `artifact_metadata.workflow`: future operator workflow metadata such as report review status or job references, only after job schema/API workflow semantics are accepted.
- `source_manifest.provenance_summary`: future summarized source dataset/version/retrieval-run coverage, only as a summary of Lane A provenance records.
- `source_manifest.connector_summary`: future connector-run status summary, only after durable connector/evidence lineage is accepted.

Required constraints:

- Metadata extensions must not reinterpret evidence, claims, red flags, unknowns, caveats, or verification tasks.
- Metadata extensions must not assert evidence-row `ingest_run_id` lineage until that linkage exists in the evidence/storage contract.
- Metadata extensions must not assert legal access, buildability, title, water rights, wetland jurisdiction, surveyed boundaries, insurability, appraisal value, lending suitability, or investment advice.
- Metadata extensions must not introduce live connector behavior, API mutation routes, DB migrations, runtime JSON Schema validation, auth boundaries, or queue behavior by implication.
- New stable keys require a planned schema/test slice before becoming required in `schemas/report_run_schema.json`.

## Consequences

- Lane D can close the open "future report metadata extensions" planning gap without changing report runtime behavior.
- Future report metadata work can pick a specific extension family instead of adding ad hoc keys to open metadata maps.
- Job schema, API mutation workflow, rendering/export implementation, and durable `ingest_run_id` evidence-row linkage remain separate future work.

## Links

- `docs/adr/lane-d-0009-report-run-schema.md`
- `docs/adr/lane-d-0010-report-manifest-metadata.md`
- `schemas/report_run_schema.json`
- `plans/lane-d-2026-06-03-reports-api-infra.md`
- `plans/2026-06-04-l7-closeout-l8-entry.md`
