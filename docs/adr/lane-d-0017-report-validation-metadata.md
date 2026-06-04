# ADR Lane D 0017: Report Validation Metadata

## Status
Accepted

## Context

ADR Lane D 0013 accepted `artifact_metadata.validation` as a future additive report metadata family. Session 1's Lane C evidence-linkage branch is not merged, so connector review action route and OpenAPI work would overlap the parked evidence/OpenAPI branch. A narrow Lane D report metadata slice can advance without touching connector runtime, API routes, OpenAPI, migrations, or Lane A/B/C implementation files.

## Decision

Generated report runs now include optional `artifact_metadata.validation` with deterministic contract and ruleset identity:

- `contract_name`: `ReportRunContract`
- `contract_version`: `report_run_contract_v1`
- `validation_profile`: `fixture_report_contract_v1`
- `ruleset_id`
- `ruleset_version`

`schemas/report_run_schema.json` constrains that optional object while keeping it additive and open for future fields. The key is emitted by `ReportRunService` and covered by report service/schema/regression tests.

This metadata records the report contract/profile and ruleset identity used to construct the fixture-backed report. It does not claim that a verification command was run or passed.

## Constraints

- No runtime JSON Schema validation is introduced.
- No API route, OpenAPI, auth, queue, connector, migration, live I/O, or evidence/claim/report semantic change is introduced.
- The metadata must not reinterpret evidence, claims, red flags, unknowns, caveats, or verification tasks.
- Evidence-row `ingest_run_id` lineage remains Lane C/connector follow-up until that branch lands and is adopted.

## Consequences

- The first accepted report metadata extension family is implemented as a stable optional report-artifact key.
- Later validation metadata may add command fingerprints, fixture profile versions, or artifact checksums only after the producing layer and tests exist.
- Connector review action routes remain deferred until Session 1's Lane C evidence-linkage/OpenAPI branch is merged or otherwise cleared.
