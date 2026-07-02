# Environmental Hazard Fixture Ingestion

## Goal
Add an owner-independent, fixture-only end-to-end proof for the `env_hazard`
extended domain on the existing Buncombe golden AOI. The slice should prove that
local EPA ECHO fixture evidence can flow through evidence storage, claim
generation, unknown handling, and Section 11 dossier rendering for both
regulated-facility proximity and source-failure paths.

## Non-goals
- No live EPA ECHO network calls.
- No new source approval, source-rights decision, vendor authority, or DS-017 change.
- No database schema, API contract, auth/security, UI, or report-semantics change.
- No qualification `PASS`, owner-decision unfreeze, hosted authority, Level 10
  claim, or Bologna implementation authority.
- No assertion that a nearby regulated facility proves contamination, exposure,
  remediation status, environmental liability, safety, value, insurability, lending
  suitability, or investment quality.

## Current state
PR #169 landed the broadband fixture-ingestion proof and left water,
environmental hazards, and geology as later extended-domain lanes. EPA ECHO is
already source-reviewed with restrictions as DS-006, and the live connector emits
`ENV_HAZ_FACILITY_SCREEN` source observations and `ENV_HAZ_SOURCE_UNAVAILABLE`
source failures.

Relevant existing surfaces:
- `backend/app/connectors/epa_echo.py` emits EPA ECHO source observations with
  `has_env_hazard_proximity`, `no_env_hazard_proximity`,
  `regulated_facility_count`, and controlled source-failure payloads.
- `backend/app/claims_engine/rule_engine.py` maps proximity evidence to `ENV_001`
  and source failures to `ENV_SOURCE_UNAVAILABLE_UNKNOWN`.
- `config/ruleset_homestead_mvp.yaml` contains `ENV_G001` and requires EPA/state
  agency/Phase I ESA follow-up.
- `backend/app/reports/dossier.py` renders Section 11 environmental hazard
  facility counts, source failures, caveats, and required verification.
- Existing report and rule-engine tests prove synthetic evidence behavior, but no
  `StaticEnvHazardFixtureConnector` currently exercises fixture ingestion to
  evidence to claim to dossier on a real AOI.
- `state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 authority context; this
  plan does not change its blocked or partial statuses.

## Proposed design
Mirror the landed minerals and broadband slices with an EPA ECHO-specific static
fixture connector. The connector reads local JSON only, validates
`connector_name`, `domain`, non-empty evidence, retrieval status, and evidence-type
consistency, then feeds into `build_fixture_workflow_with_public_services` through
a new `evaluate_env_hazard_fixture_quality` wrapper.

Environmental hazards follow broadband before water because they use the same
source-observation/source-failure shape and existing Section 11 rendering, while
water has sharper rights, well-yield, and potable-water overclaim boundaries.

## Bottom-up sequence
1. Add `backend/app/connectors/env_hazard_fixture.py` with
   `StaticEnvHazardFixtureConnector` and result dataclass.
2. Add `evaluate_env_hazard_fixture_quality` in fixture quality checks with
   source-observation, non-spatial expectations.
3. Export the connector and quality evaluator from `backend/app/connectors/__init__.py`.
4. Add two local connector fixtures:
   `nc_buncombe_bun_env_hazard_facilities.json` and
   `nc_buncombe_bun_env_hazard_unavailable.json`.
5. Add connector fail-closed tests for local path, connector/domain, success, and
   source-failure requirements.
6. Add private-MVP end-to-end tests for proximity and source-failure paths,
   including evidence-to-claim linkage, Section 11 rendering, and forbidden
   overclaim checks.
7. Update project/task/readiness routing so `BROADBAND-FIXTURE` is completed and
   `ENV-FIXTURE` is active.
8. Run focused checks, authority guardrails, then the full Windows verifier.
9. Update state, worklog, and validation log with exact commands and residual risk.

## Files likely to change
| File | Expected change |
|---|---|
| `backend/app/connectors/env_hazard_fixture.py` | New static local JSON fixture connector. |
| `backend/app/connectors/fixture_quality.py` | Add env-hazard quality profile wrapper. |
| `backend/app/connectors/__init__.py` | Export env-hazard fixture connector and evaluator. |
| `backend/tests/connectors/test_env_hazard_fixture_connector.py` | New connector fail-closed tests. |
| `backend/tests/private_mvp/test_extended_domain_env_hazard.py` | New end-to-end env-hazard fixture tests. |
| `tests/fixtures/connectors/nc_buncombe_bun_env_hazard_facilities.json` | New regulated-facility fixture. |
| `tests/fixtures/connectors/nc_buncombe_bun_env_hazard_unavailable.json` | New source-failure fixture. |
| `plans/README.md` | Route to this active plan. |
| `scripts/qualification_parameterization_backlog_check.py` | Guard the new active routing. |
| `backend/tests/test_qualification_parameterization_backlog_artifacts.py` | Mirror backlog checker expectations. |
| `backend/tests/test_readiness_core_artifacts.py` | Mirror readiness model expectations. |
| `state/PROJECT_STATE.md` | Record active env-hazard lane and completed broadband lane. |
| `state/WORKLOG.md` | Record implementation and validation notes. |
| `state/VALIDATION_LOG.md` | Record exact commands, results, and residual risk. |
| `tasks/task_queue.yaml` | Mark broadband done and env-hazard active. |

## Tests / verification
Expected focused commands:

```powershell
$env:PYTHONPATH='backend'; py -3.12 -m pytest backend\tests\connectors\test_env_hazard_fixture_connector.py backend\tests\private_mvp\test_extended_domain_env_hazard.py -q
$env:PYTHONPATH='backend'; py -3.12 -m pytest backend\tests\connectors\test_env_hazard_fixture_connector.py backend\tests\private_mvp\test_extended_domain_broadband.py backend\tests\private_mvp\test_extended_domain_env_hazard.py backend\tests\test_readiness_core_artifacts.py backend\tests\test_qualification_parameterization_backlog_artifacts.py -q
py -3.12 -m ruff check backend\app\connectors\env_hazard_fixture.py backend\app\connectors\fixture_quality.py backend\app\connectors\__init__.py backend\tests\connectors\test_env_hazard_fixture_connector.py backend\tests\private_mvp\test_extended_domain_env_hazard.py backend\tests\test_readiness_core_artifacts.py backend\tests\test_qualification_parameterization_backlog_artifacts.py scripts\qualification_parameterization_backlog_check.py
$env:PYTHONPATH='backend'; $env:MYPYPATH='backend'; py -3.12 -m mypy backend\app\connectors\env_hazard_fixture.py backend\app\connectors\fixture_quality.py backend\tests\connectors\test_env_hazard_fixture_connector.py backend\tests\private_mvp\test_extended_domain_env_hazard.py
py -3.12 scripts\qualification_parameterization_backlog_check.py --root .
py -3.12 scripts\readiness_matrix_check.py
py -3.12 scripts\qualification_status_check.py --root .
.\scripts\verify.ps1
```

Pass/fail requirements:
- The fixture connector refuses remote paths, empty evidence, connector/domain
  mismatch, successful source-failure-only fixtures, and failed/blocked fixtures
  that lack source-failure evidence.
- The regulated-facility fixture produces `ENV_001` with evidence linkage and
  Section 11 facility-count language.
- The unavailable fixture produces `ENV_SOURCE_UNAVAILABLE_UNKNOWN`, suppresses
  `ENV_001`, and renders source-failure language rather than silent pass/not
  evaluated language.
- No forbidden contamination, safety, liability, value, insurance, lending,
  investment, access, title, buildability, or water-rights conclusion appears.
- Qualification status remains `P0 = BLOCKED`; no hosted, DS-017, Bologna,
  source-authority, or Level 10 status changes.

## Risks and blockers
- EPA ECHO is a facility/compliance screening source, not a contamination or
  environmental-liability determination. Acceptance must assert caveats and avoid
  legal/safety conclusions.
- Source-failure evidence must remain first-class; a failed EPA ECHO fixture must
  not become a no-hazard or not-evaluated pass.
- Routing changes are control-plane facts and must stay synchronized across
  `tasks/task_queue.yaml`, `plans/README.md`, readiness tests, and backlog checks.

## Decision log
- 2026-07-02: Selected environmental hazards after broadband because it is the
  next highest-value owner-independent extended-domain proof with a narrow
  source-observation/source-failure shape and existing Section 11 rendering.

## Progress log
- 2026-07-02: Created the plan after PR #169 merged broadband fixture ingestion.
- 2026-07-02: Added static env-hazard fixture connector, EPA ECHO success and
  source-failure fixtures, focused connector tests, private-MVP Section 11 end-to-end
  tests, and active routing updates. Focused pytest, ruff, mypy, backlog, readiness,
  and qualification-status checks passed after restoring explicit plan lineage and the
  Level 9/10 authority citation.
- 2026-07-02: Full `.\scripts\verify.ps1` passed; DB smoke was skipped by default.
