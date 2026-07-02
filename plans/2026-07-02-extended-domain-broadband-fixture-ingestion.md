# Extended-Domain Broadband Fixture Ingestion

## Goal
Add an owner-independent, fixture-only end-to-end proof for the `broadband` extended
domain on the existing Buncombe golden AOI. The slice should prove that local fixture
ingestion can carry FCC Broadband Data Collection evidence through evidence storage,
claim generation, unknown handling, and dossier rendering for both no-provider and
source-failure paths.

## Non-goals
- No live FCC network calls.
- No new source approval, vendor authority, source-rights decision, or DS-017 change.
- No database schema, API contract, auth/security, report semantics, or UI changes.
- No qualification `PASS`, owner-decision unfreeze, hosted authority, Level 10 claim,
  or Bologna implementation authority.
- No assertion that FCC provider-reported coverage proves service availability or that
  a parcel is suitable for remote work.

## Current state
`plans/2026-06-29-extended-domain-minerals-fixture-ingestion.md` and PR #168 proved
the minerals pattern with a static fixture connector, domain quality evaluator, two
fixtures, and private-MVP tests. The same gap remains for `broadband`: the live
connector, API tests, rule-engine logic, and synthetic dossier coverage exist, but no
`StaticBroadbandFixtureConnector` currently exercises the fixture-ingestion to
evidence to claim to dossier path on a real AOI.

Relevant existing surfaces:
- `backend/app/connectors/fcc_broadband.py` emits `FCC_BROADBAND_AVAILABILITY_SCREEN`
  and `BROADBAND_SOURCE_UNAVAILABLE` evidence.
- `backend/app/claims_engine/rule_engine.py` maps `has_any_broadband == false` to
  `BROADBAND_NO_ACCESS_001` and source failures to `BROADBAND_SOURCE_UNAVAILABLE`.
- `config/ruleset_homestead_mvp.yaml` contains `BROADBAND_G001` and `BROADBAND_G002`
  with verification tasks that preserve provider-verification caveats.
- `backend/tests/reports/test_dossier_enrichment.py` already proves synthetic Section
  12 rendering, but not fixture-ingestion linkage.
- `state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 authority context; this
  plan does not change its blocked or partial statuses.

## Proposed design
Mirror the landed minerals slice, but adapt it to broadband's source-observation
shape. Add a static fixture connector that reads local JSON only, validates
`connector_name`, `domain`, retrieval status, and evidence type consistency, then feed
it through `build_fixture_workflow_with_public_services`.

Broadband is intentionally selected before water, environmental hazards, or geology
because it is the narrowest follow-up to minerals: it has one positive/no-provider
source-observation path, one source-failure path, existing hard-gate rules, and direct
Section 12 dossier coverage. Water/environmental/geology remain valuable next lanes,
but they carry more domain-specific interpretation and should follow after this
pattern is re-proven.

## Bottom-up sequence
1. Add `backend/app/connectors/broadband_fixture.py` with
   `StaticBroadbandFixtureConnector` and result dataclass.
2. Add `evaluate_broadband_fixture_quality` in fixture quality checks with
   source-observation, non-spatial expectations.
3. Export the connector and quality evaluator from `backend/app/connectors/__init__.py`.
4. Add two local connector fixtures:
   `nc_buncombe_bun_broadband_no_access.json` and
   `nc_buncombe_bun_broadband_unavailable.json`.
5. Add private-MVP end-to-end tests for no-provider advisory and source-failure unknown
   paths, including evidence-to-claim linkage, Section 12 rendering, and forbidden
   overclaim checks.
6. Run focused checks, then the repo verification gate if the focused checks are clean.
7. Update state, worklog, and validation log with exact commands and residual risk.

## Files likely to change
| File | Expected change |
|---|---|
| `backend/app/connectors/broadband_fixture.py` | New static local JSON fixture connector. |
| `backend/app/connectors/fixture_quality.py` | Add broadband quality profile wrapper. |
| `backend/app/connectors/__init__.py` | Export broadband fixture connector and quality evaluator. |
| `backend/tests/private_mvp/test_extended_domain_broadband.py` | New end-to-end broadband fixture tests. |
| `tests/fixtures/connectors/nc_buncombe_bun_broadband_no_access.json` | New no-provider fixture. |
| `tests/fixtures/connectors/nc_buncombe_bun_broadband_unavailable.json` | New source-failure fixture. |
| `state/PROJECT_STATE.md` | Record completion/progress after validation. |
| `state/WORKLOG.md` | Record implementation and verification notes. |
| `state/VALIDATION_LOG.md` | Record exact commands, results, and residual risk. |

## Tests / verification
Expected focused commands:

```powershell
$env:PYTHONPATH='backend'; py -3.12 -m pytest backend\tests\private_mvp\test_extended_domain_broadband.py -q
py -3.12 -m ruff check backend\app\connectors\broadband_fixture.py backend\app\connectors\fixture_quality.py backend\app\connectors\__init__.py backend\tests\private_mvp\test_extended_domain_broadband.py
$env:MYPYPATH='backend'; py -3.12 -m mypy backend\app\connectors\broadband_fixture.py backend\app\connectors\fixture_quality.py backend\tests\private_mvp\test_extended_domain_broadband.py
py -3.12 scripts\qualification_parameterization_backlog_check.py --root .
py -3.12 scripts\readiness_matrix_check.py
py -3.12 scripts\qualification_status_check.py --root .
.\scripts\verify.ps1
```

Pass/fail requirements:
- The fixture connector refuses remote paths, empty evidence, connector/domain
  mismatch, successful source-failure-only fixtures, and failed/blocked fixtures that
  lack source-failure evidence.
- The no-provider fixture produces `BROADBAND_NO_ACCESS_001` with evidence linkage and
  Section 12 no-provider language.
- The unavailable fixture produces `BROADBAND_SOURCE_UNAVAILABLE`, suppresses the
  no-provider claim, and renders source-failure language instead of silent pass/not
  evaluated language.
- No forbidden legal, investment, access, water-rights, value, safety, or guaranteed
  service-availability language appears in the generated dossier.
- Qualification status remains `P0 = BLOCKED`; no hosted, DS-017, Bologna, source
  authority, or Level 10 status changes.

## Risks and blockers
- FCC BDC data is provider-reported and may overstate availability, so acceptance
  criteria must verify caveats and must not require or imply service guarantee.
- Source-failure evidence must remain first-class; a failed FCC fixture must not be
  converted into a no-provider conclusion.
- The active plan and task routing are control-plane facts. They must be kept in sync
  with `tasks/task_queue.yaml`, `plans/README.md`, and readiness/backlog tests.

## Decision log
- 2026-07-02: Selected broadband as the next extended-domain fixture-ingestion lane
  after PR #168 because it is the smallest owner-independent continuation of the
  minerals pattern and does not require external source authority.

## Progress log
- 2026-07-02: Created the active executable plan after reconciling live
  `origin/main@35077d25e79fb105ada87fc86a1ead6623eb5e66` with completed ODGAV
  PR #167 and minerals PR #168.
- 2026-07-02: Added `StaticBroadbandFixtureConnector`,
  `evaluate_broadband_fixture_quality`, two Buncombe broadband fixtures, connector
  fail-closed unit tests, and private-MVP no-provider/source-failure end-to-end tests.
  Focused tests, ruff, mypy, backlog/readiness/qualification checks, and full
  `.\scripts\verify.ps1` passed; DB smoke remained skipped by default.
