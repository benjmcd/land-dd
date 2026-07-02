# Water Fixture Ingestion

## Goal
Add an owner-independent, fixture-only end-to-end proof for the `water` extended
domain on the existing Buncombe golden AOI. The slice should prove that local USGS
Water Data API monitoring-context fixture evidence can flow through evidence
storage, claim generation, unknown/review handling, and Section 9 dossier rendering
for monitoring-stations-found, no-monitoring-stations, source-failure,
conflicting-evidence, and stale-evidence paths.

## Non-goals
- No live USGS network calls.
- No DS-013 well-log access, DS-014 water-rights authority, source approval,
  source-rights decision, vendor authority, or DS-017 change.
- No database schema, API contract, auth/security, UI, or report-semantics change.
- No qualification `PASS`, owner-decision unfreeze, hosted authority, Level 10
  claim, or Bologna implementation authority.
- No assertion that USGS monitoring-station context proves water rights, well
  viability, potable water, supply adequacy, lawful hauling, legal water access,
  title, buildability, appraisal value, lending suitability, insurance suitability,
  or investment quality.

## Current state
PR #170 landed the environmental hazard fixture-ingestion proof and left water and
geology as later extended-domain lanes. DS-005 is source-reviewed with restrictions
for USGS water-monitoring context, while DS-013 well logs and DS-014 water rights
remain blocked or pending.

Relevant existing surfaces:
- `backend/app/connectors/usgs_water_monitoring.py` emits `WATER_MONITORING_SCREEN`
  source observations with `plausible_water_context`,
  `no_plausible_water_context`, `monitoring_station_count`, and
  `water_context_status`, and emits `WATER_SOURCE_UNAVAILABLE` source failures.
- `backend/app/claims_engine/rule_engine.py` maps no-context evidence to
  `WATER_001`, source failures to `WATER_SOURCE_UNAVAILABLE_UNKNOWN`,
  conflicting/incomplete evidence to `WATER_EVIDENCE_NEEDS_REVIEW`, and stale
  evidence to `WATER_STALE_EVIDENCE_NEEDS_REVIEW`.
- `backend/app/reports/dossier.py` renders Section 9 water-monitoring results and
  explicitly keeps water-rights status as not determined.
- Existing connector, API, rule-engine, and report tests prove synthetic/live-shape
  behavior, but no `StaticWaterFixtureConnector` currently exercises fixture
  ingestion to evidence to claim to dossier on a real AOI.
- `state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 authority context; this
  plan does not change its blocked or partial statuses.

## Proposed design
Mirror the landed minerals, broadband, and environmental hazard slices with a
USGS-water-specific static fixture connector. The connector reads local JSON only,
validates `connector_name`, `domain`, non-empty evidence, retrieval status, and
evidence-type consistency, then feeds into
`build_fixture_workflow_with_public_services` through a new
`evaluate_water_fixture_quality` wrapper.

Fixture retrieval `row_count` must equal the count of non-failure evidence records,
not the raw station count. Station count belongs in `metrics.station_count` and
`observed_value.monitoring_station_count`.

Water follows environmental hazards because it has sharper legal, well-yield,
potable-water, and water-rights overclaim boundaries. This pass stays within DS-005
monitoring-context evidence and keeps DS-013/DS-014 blocked.

## Bottom-up sequence
1. Add `backend/app/connectors/water_fixture.py` with `StaticWaterFixtureConnector`
   and result dataclass.
2. Add `evaluate_water_fixture_quality` in fixture quality checks with
   source-observation, non-spatial expectations.
3. Export the connector and quality evaluator from `backend/app/connectors/__init__.py`.
4. Add five local connector fixtures:
   `nc_buncombe_bun_water_stations_found.json`,
   `nc_buncombe_bun_water_no_stations.json`,
   `nc_buncombe_bun_water_unavailable.json`,
   `nc_buncombe_bun_water_conflicting.json`, and
   `nc_buncombe_bun_water_stale.json`.
5. Add connector fail-closed tests for local path, connector/domain, success, and
   source-failure requirements.
6. Add private-MVP end-to-end tests for stations-found, no-stations,
   source-failure, conflicting-evidence, and stale-evidence paths, including
   evidence-to-claim linkage, Section 9 rendering, and forbidden-overclaim checks.
7. Update project/task/readiness routing so `ENV-FIXTURE` is completed and
   `WATER-FIXTURE` is active.
8. Run focused checks, authority guardrails, then the full Windows verifier.
9. Update state, worklog, and validation log with exact commands and residual risk.

## Files likely to change
| File | Expected change |
|---|---|
| `backend/app/connectors/water_fixture.py` | New static local JSON fixture connector. |
| `backend/app/connectors/fixture_quality.py` | Add water quality profile wrapper. |
| `backend/app/connectors/__init__.py` | Export water fixture connector and evaluator. |
| `backend/tests/connectors/test_water_fixture_connector.py` | New connector fail-closed tests. |
| `backend/tests/private_mvp/test_extended_domain_water.py` | New end-to-end water fixture tests. |
| `tests/fixtures/connectors/nc_buncombe_bun_water_*.json` | New water monitoring-context fixtures. |
| `plans/README.md` | Route to this active plan. |
| `scripts/qualification_parameterization_backlog_check.py` | Guard the new active routing. |
| `backend/tests/test_qualification_parameterization_backlog_artifacts.py` | Mirror backlog checker expectations. |
| `backend/tests/test_readiness_core_artifacts.py` | Mirror readiness model expectations. |
| `state/PROJECT_STATE.md` | Record active water lane and completed env-hazard lane. |
| `state/WORKLOG.md` | Record implementation and validation notes. |
| `state/VALIDATION_LOG.md` | Record exact commands, results, and residual risk. |
| `tasks/task_queue.yaml` | Mark env-hazard done and water active. |

## Tests / verification
Expected focused commands:

```powershell
$env:PYTHONPATH='backend'; py -3.12 -m pytest backend\tests\connectors\test_water_fixture_connector.py backend\tests\private_mvp\test_extended_domain_water.py -q
$env:PYTHONPATH='backend'; py -3.12 -m pytest backend\tests\connectors\test_water_fixture_connector.py backend\tests\private_mvp\test_extended_domain_env_hazard.py backend\tests\private_mvp\test_extended_domain_water.py backend\tests\test_readiness_core_artifacts.py backend\tests\test_qualification_parameterization_backlog_artifacts.py -q
py -3.12 -m ruff check backend\app\connectors\water_fixture.py backend\app\connectors\fixture_quality.py backend\app\connectors\__init__.py backend\tests\connectors\test_water_fixture_connector.py backend\tests\private_mvp\test_extended_domain_water.py backend\tests\test_readiness_core_artifacts.py backend\tests\test_qualification_parameterization_backlog_artifacts.py scripts\qualification_parameterization_backlog_check.py
$env:PYTHONPATH='backend'; $env:MYPYPATH='backend'; py -3.12 -m mypy backend\app\connectors\water_fixture.py backend\app\connectors\fixture_quality.py backend\tests\connectors\test_water_fixture_connector.py backend\tests\private_mvp\test_extended_domain_water.py
py -3.12 scripts\source_readiness.py
py -3.12 scripts\qualification_parameterization_backlog_check.py --root .
py -3.12 scripts\readiness_matrix_check.py
py -3.12 scripts\qualification_status_check.py --root .
.\scripts\verify.ps1
```

Pass/fail requirements:
- The fixture connector refuses remote paths, empty evidence, connector/domain
  mismatch, successful source-failure-only fixtures, and failed/blocked fixtures
  that lack source-failure evidence.
- The stations-found fixture produces `WATER_MONITORING_SCREEN` with
  `plausible_water_context=true`, station-count evidence, Section 9 station-count
  language, no `WATER_001`, and DS-005 monitoring-context caveats.
- The no-stations fixture produces `WATER_001` with ingested evidence linkage and
  a caveat that absence of monitoring stations is not a water-availability, well,
  potable-water, water-rights, or buildability conclusion.
- The unavailable fixture produces `WATER_SOURCE_UNAVAILABLE_UNKNOWN`, suppresses
  `WATER_001`, and renders source-failure language rather than a no-water conclusion.
- The conflicting fixture produces `WATER_EVIDENCE_NEEDS_REVIEW`, suppresses
  `WATER_001`, and requires human review.
- The stale fixture produces `WATER_STALE_EVIDENCE_NEEDS_REVIEW` and requires
  refresh before relying on water-context screening.
- No forbidden water-rights, potable-water, well-yield, supply-adequacy, legal
  access, title, buildability, value, insurance, lending, investment, or safety
  conclusion appears.
- Qualification status remains `P0 = BLOCKED`; no hosted, DS-017, Bologna,
  source-authority, source-rights, water-rights, well-log, or Level 10 status changes.

## Risks and blockers
- USGS monitoring stations are weak context signals, not evidence of parcel-level
  water rights, well viability, potable water, supply adequacy, lawful hauling, or
  legal water access.
- DS-013 well logs and DS-014 water rights remain blocked or pending; this pass must
  not imply their authority through DS-005 fixtures.
- Source-failure evidence must remain first-class; a failed USGS fixture must not
  become a no-water or no-issue conclusion.
- Routing changes are control-plane facts and must stay synchronized across
  `tasks/task_queue.yaml`, `plans/README.md`, readiness tests, and backlog checks.

## Decision log
- 2026-07-02: Selected water after environmental hazards because DS-005 already has
  live connector/rule/dossier semantics, and the next owner-independent proof should
  close the most legally sensitive remaining extended-domain fixture gap while
  preserving DS-013/DS-014 blockers.

## Progress log
- 2026-07-02: Created the plan after PR #170 merged environmental hazard fixture
  ingestion.
- 2026-07-02: Implemented the static water fixture connector, five Buncombe water
  fixtures, connector fail-closed tests, private-MVP end-to-end tests, and routing
  updates. Focused tests, ruff, mypy, source readiness, backlog/readiness/status
  checks, `git diff --check`, and full `.\scripts\verify.ps1` passed.
