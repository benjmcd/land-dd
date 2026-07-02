# Geology Fixture Ingestion

## Goal
Add an owner-independent, fixture-only end-to-end proof for the `geology`
extended domain on the existing Buncombe golden AOI. The slice should prove that
local NC Geological Survey 1985 geologic map-unit context fixture evidence can
flow through evidence storage, advisory claim generation, source-failure
handling, and Section 14 dossier rendering for map-units-present,
no-map-units, and source-failure paths.

## Non-goals
- No live NC Geological Survey or ArcGIS network calls.
- No landslide, sinkhole, radon, subsidence, geotechnical, engineering,
  geologic-hazard, mineral-resource, buildability, title, appraisal, lending,
  insurance, investment, safety, or legal conclusion.
- No source approval, source-rights decision, vendor authority, DS-017 change,
  or Bologna source/corpus/report authority.
- No database schema, API contract, auth/security, UI, or report-semantics
  change.
- No qualification `PASS`, owner-decision unfreeze, hosted authority, Level 10
  claim, or `P0` unblock.

## Current state
PR #171 landed the USGS water monitoring fixture-ingestion proof and left
geology as the next owner-independent extended-domain lane. DS-015 is
source-reviewed with restrictions for NC Geological Survey 1985 map-unit
context. The source review and registry both limit DS-015 to historical,
generalized map-unit context and forbid treating it as parcel-scale geology or
as hazard, buildability, mineral-resource, valuation, lending, insurance, or
investment evidence.

Relevant existing surfaces:
- `backend/app/connectors/nc_geologic_map.py` emits
  `NC_GEOLOGIC_MAP_UNIT_CONTEXT` source observations with
  `geologic_hazard_determined=false`, `buildability_determined=false`, map-unit
  metadata, and DS-015 caveats. It emits `NC_GEOLOGIC_MAP_SOURCE_FAILURE` source
  failures on request/service/truncation/malformed response errors.
- `backend/app/claims_engine/rule_engine.py` maps non-failure geology evidence
  with `geologic_hazard_determined=false` to the existing
  `GEOLOGY_NOT_EVALUATED` advisory claim. The source-failure path does not
  create a no-hazard or no-issue claim.
- `backend/app/reports/dossier.py` renders Section 14 geologic map-unit context
  and renders source failure as NCGS geologic map data unavailable.
- `docs/source-reviews/ds-015.md` and `registers/data_source_registry.csv`
  preserve the DS-015 authority boundary.
- `state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 authority context;
  this plan does not change its blocked or partial statuses.

## Proposed design
Mirror the landed minerals, broadband, env-hazard, and water slices with a
DS-015-specific static fixture connector. The connector reads local JSON only,
validates `connector_name`, `domain`, non-empty evidence, retrieval status, and
evidence-type consistency, then feeds into
`build_fixture_workflow_with_public_services` through a new
`evaluate_geology_fixture_quality` wrapper.

Fixture retrieval `row_count` must equal the count of non-failure evidence
records, not the raw geologic unit count. Unit count belongs in
`metrics.geologic_unit_count` and `observed_value.geologic_unit_count`.

## Consensus decision
Three options were considered:

1. Live DS-015 connector execution. Rejected because this pass is
   owner-independent fixture ingestion and must not create live-network or
   source-authority side effects.
2. A report-only geology display update. Rejected because the report and rule
   surfaces already exist; the missing proof is the local fixture ingestion path
   through evidence, claim, and dossier.
3. A static geology fixture connector. Selected because it reuses the landed
   extended-domain pattern, exercises the existing DS-015 semantics, and keeps
   the source-rights and overclaim boundaries intact.

## Bottom-up sequence
1. Add `backend/app/connectors/geology_fixture.py` with
   `StaticGeologyFixtureConnector` and result dataclass.
2. Add `evaluate_geology_fixture_quality` in fixture quality checks with a
   source-observation, non-spatial geology profile.
3. Export the connector and quality evaluator from
   `backend/app/connectors/__init__.py`.
4. Add three local connector fixtures:
   `nc_buncombe_bun_geology_units.json`,
   `nc_buncombe_bun_geology_no_units.json`, and
   `nc_buncombe_bun_geology_unavailable.json`.
5. Add connector fail-closed tests for local path, connector/domain, success,
   and source-failure requirements.
6. Add private-MVP end-to-end tests for map-units-present, no-map-units, and
   source-failure paths, including evidence-to-claim linkage, Section 14
   rendering, and forbidden-overclaim checks.
7. Update project/task/readiness routing so `WATER-FIXTURE` is completed and
   `GEOLOGY-FIXTURE` is active.
8. Run focused checks, authority guardrails, then the full Windows verifier.
9. Update state, worklog, and validation log with exact commands and residual
   risk.

## Files likely to change
| File | Expected change |
|---|---|
| `backend/app/connectors/geology_fixture.py` | New static local JSON fixture connector. |
| `backend/app/connectors/fixture_quality.py` | Add geology quality profile wrapper. |
| `backend/app/connectors/__init__.py` | Export geology fixture connector and evaluator. |
| `backend/tests/connectors/test_geology_fixture_connector.py` | New connector fail-closed tests. |
| `backend/tests/private_mvp/test_extended_domain_geology.py` | New end-to-end geology fixture tests. |
| `tests/fixtures/connectors/nc_buncombe_bun_geology_*.json` | New NCGS geologic map context fixtures. |
| `plans/README.md` | Route to this active plan. |
| `scripts/qualification_parameterization_backlog_check.py` | Guard the new active routing. |
| `backend/tests/test_qualification_parameterization_backlog_artifacts.py` | Mirror backlog checker expectations. |
| `backend/tests/test_readiness_core_artifacts.py` | Mirror readiness model expectations. |
| `state/PROJECT_STATE.md` | Record active geology lane and completed water lane. |
| `state/WORKLOG.md` | Record implementation and validation notes. |
| `state/VALIDATION_LOG.md` | Record exact commands, results, and residual risk. |
| `tasks/task_queue.yaml` | Mark water done and geology active. |

## Tests / verification
Expected focused commands:

```powershell
$env:PYTHONPATH='backend'; py -3.12 -m pytest backend\tests\connectors\test_geology_fixture_connector.py backend\tests\private_mvp\test_extended_domain_geology.py -q
$env:PYTHONPATH='backend'; py -3.12 -m pytest backend\tests\connectors\test_geology_fixture_connector.py backend\tests\private_mvp\test_extended_domain_water.py backend\tests\private_mvp\test_extended_domain_geology.py backend\tests\test_readiness_core_artifacts.py backend\tests\test_qualification_parameterization_backlog_artifacts.py -q
py -3.12 -m ruff check backend\app\connectors\geology_fixture.py backend\app\connectors\fixture_quality.py backend\app\connectors\__init__.py backend\tests\connectors\test_geology_fixture_connector.py backend\tests\private_mvp\test_extended_domain_geology.py backend\tests\test_readiness_core_artifacts.py backend\tests\test_qualification_parameterization_backlog_artifacts.py scripts\qualification_parameterization_backlog_check.py
$env:PYTHONPATH='backend'; $env:MYPYPATH='backend'; py -3.12 -m mypy backend\app\connectors\geology_fixture.py backend\app\connectors\fixture_quality.py backend\tests\connectors\test_geology_fixture_connector.py backend\tests\private_mvp\test_extended_domain_geology.py
py -3.12 scripts\source_readiness.py
py -3.12 scripts\qualification_parameterization_backlog_check.py --root .
py -3.12 scripts\readiness_matrix_check.py
py -3.12 scripts\qualification_status_check.py --root .
git diff --check
.\scripts\verify.ps1
```

Pass/fail requirements:
- The fixture connector refuses remote paths, empty evidence, connector/domain
  mismatch, successful source-failure-only fixtures, and failed/blocked fixtures
  that lack source-failure evidence.
- The map-units fixture produces `NC_GEOLOGIC_MAP_UNIT_CONTEXT` with map-unit
  metadata, `geologic_hazard_determined=false`, `buildability_determined=false`,
  Section 14 unit/formation/type/belt language, and a
  `GEOLOGY_NOT_EVALUATED` advisory claim linked to the ingested evidence.
- The no-map-units fixture records `NC_GEOLOGIC_MAP_UNIT_CONTEXT` with
  `no_geologic_map_context=true` and still makes clear that hazards and
  buildability are not determined.
- The source-failure fixture records `NC_GEOLOGIC_MAP_SOURCE_FAILURE`, renders
  Section 14 source-failure language, and does not become a no-hazard,
  no-constraint, no-issue, or buildable conclusion.
- No forbidden hazard, geotechnical, buildability, resource-value, title, legal,
  appraisal, insurance, lending, investment, or safety conclusion appears.
- Qualification status remains `P0 = BLOCKED`; no hosted, DS-017, Bologna,
  source-authority, source-rights, geologic-hazard, buildability, or Level 10
  status changes.

## Risks and blockers
- DS-015 is historical statewide map-unit context, not parcel-scale geology.
- Absence of a returned map unit is not evidence that no geologic constraint,
  hazard, or site condition exists.
- Source-failure evidence must remain first-class; a failed NCGS fixture must not
  become a no-hazard or no-issue conclusion.
- Routing changes are control-plane facts and must stay synchronized across
  `tasks/task_queue.yaml`, `plans/README.md`, readiness tests, and backlog checks.

## Decision log
- 2026-07-02: Selected geology after water because DS-015 already has live
  connector/rule/dossier semantics, and the next owner-independent proof should
  close the remaining extended-domain fixture gap while preserving DS-015 hazard,
  buildability, source-authority, DS-017, Bologna, hosted, Level 10, and
  qualification blockers.
