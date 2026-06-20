# Performance Guardrails UI G6c

## Goal

Add the narrow `G6c` local performance guardrails surface after the merged `G6b`
operations guardrails UI. The pass should expose existing repo-owned performance
baseline, spatial query-plan, and queue-backpressure authority through a read-only
local operator view without sending load-test traffic, opening DB connections, writing
performance artifacts, or claiming hosted performance/SLO readiness.

## Non-goals

- No live load-test execution, runtime `EXPLAIN`, DB connection, queue mutation,
  generated performance artifact, Docker invocation, hosted dashboard, alert routing,
  production capacity claim, SLO claim, DS-017 approval, source/vendor expansion,
  Bologna pilot, generic AOI proof, hosted identity/RBAC, hosted observability, or
  Level 10 completion claim.
- No public JSON API contract change beyond the server-rendered local UI route.
- No DB schema change, source registry mutation, connector runtime change, report
  semantics change, or production dependency addition.

## Current state

- `G6b` operations guardrails UI is merged on live `origin/main` at
  `51f347d9940016ef428ea3837cbc4888f6ac81c1`.
- The dirty root checkout remains preserved candidate evidence only; this work is in
  clean worktree `worktrees/perf-guard` on branch `codex/perf-guard`.
- `state/reconciliation-dispositions.md` retains `backend/app/performance_guardrails.py`
  and `backend/tests/api/test_ui_performance_guardrails.py` as an isolated `G6` slice.
- Current performance authority is spread across repo-owned artifacts:
  `config/performance_baseline.yaml`, `config/spatial_query_plan.yaml`,
  `docs/runbooks/performance.md`, `docs/runbooks/load_testing.md`,
  `scripts/load_test_runner.py`, `scripts/performance_baseline_check.py`,
  `scripts/spatial_query_plan_check.py`, `scripts/spatial_query_plan_runtime_check.py`,
  `backend/app/operations/backpressure.py`, and `backend/app/core/config.py`.
- `state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 authority for this slice.
  This plan may make local performance posture easier to inspect, but it must not
  promote hosted workload proof, hosted alerting/observability, production SLOs,
  DS-017 entitlement, or Level 10 production gates.

## Proposed design

Build a small `backend/app/performance_guardrails.py` helper that parses existing
performance catalogs and verifies referenced repo-relative artifacts before rendering.
The helper will fail closed on schema drift, missing required scenarios/indexes/query
reviews/backpressure settings, missing runbooks/scripts, or any catalog change that
turns local-only performance evidence into an implied hosted/Level 10 pass.

Rejected alternatives:

- Run existing performance validators inside the UI helper: validators are command
  gates, while the UI route must stay GET-only and file-read-only.
- Combine performance and observability readiness: G8 observability has different
  blockers and should follow after local deployment/release boundaries.
- Render measured load results: committed measured results are explicitly false, and
  local artifacts are operator-generated evidence outside default validation.

## Bottom-up sequence

1. Add failing focused tests for the performance guardrails parser, fail-closed
   behavior, GET-only route, and navigation links.
2. Implement the read-only helper over existing performance/spatial/backpressure
   artifacts.
3. Add `/ui/performance-guardrails` and navigation without changing protected
   operations or performance runtime behavior.
4. Regenerate OpenAPI stubs because the route set changes.
5. Run focused performance/guardrail checks, OpenAPI parity, validators, workspace,
   and full verification before updating state to completed.

## Files likely to change

| File | Expected change |
|---|---|
| `backend/tests/api/test_ui_performance_guardrails.py` | New parser, fail-closed, route, and navigation tests. |
| `backend/app/performance_guardrails.py` | Read-only parser/model over performance catalogs, runbooks, and validation scripts. |
| `backend/app/api/ui.py` | Add GET-only local performance guardrails route and nav link. |
| `api/openapi_stub.yaml` | Regenerated FastAPI contract stub for the new UI route. |
| `docs/planning_pack/api/openapi_stub.yaml` | Regenerated planning-pack mirror. |
| `MANIFEST.md` | Route to the new performance guardrails source-of-truth file after implementation exists. |
| `plans/README.md` | Active-plan pointer. |
| `tasks/task_queue.yaml` | Active-plan routing and validation commands. |
| `state/PROJECT_STATE.md` | Current checkpoint and boundaries. |
| `state/WORKLOG.md` | Work summary. |
| `state/VALIDATION_LOG.md` | Commands, results, and residual risk. |

## Tests / verification

```powershell
cd backend
py -3.12 -m pytest -q .\tests\api\test_ui_performance_guardrails.py
py -3.12 -m pytest -q .\tests\api\test_ui_performance_guardrails.py .\tests\test_performance_artifacts.py .\tests\test_load_test_artifacts.py .\tests\test_spatial_query_plan_artifacts.py .\tests\test_spatial_query_plan_runtime_artifacts.py .\tests\api\test_backpressure.py
ruff check .\app\performance_guardrails.py .\app\api\ui.py .\tests\api\test_ui_performance_guardrails.py
py -3.12 -m mypy .\app\performance_guardrails.py .\app\api\ui.py .\tests\api\test_ui_performance_guardrails.py
cd ..
py -3.12 .\scripts\performance_baseline_check.py
py -3.12 .\scripts\spatial_query_plan_check.py
.\scripts\run_load_test.ps1 -ValidateOnly
py -3.12 .\scripts\release_readiness_check.py
py -3.12 .\scripts\readiness_matrix_check.py
git diff --check
git diff --name-only --diff-filter=D
.\scripts\validate_workspace.ps1
.\scripts\verify.ps1
```

If the route set changes:

```powershell
py -3.12 .\scripts\export_openapi_stub.py
cd backend
py -3.12 -m pytest -q .\tests\api\test_openapi_contract.py::test_openapi_stub_path_methods_match_runtime_schema .\tests\test_planning_pack_schema_copies.py::test_planning_pack_openapi_stub_matches_generated_fastapi_contract
```

## Risks and blockers

- A local performance view can overclaim if it reads like hosted workload proof,
  production capacity proof, or an SLO commitment. Route copy and tests must keep those
  blockers explicit.
- Spatial runtime review is opt-in DB-backed `EXPLAIN`; the UI helper must not import or
  execute it.
- Load-test wrappers can send HTTP traffic unless `-ValidateOnly` is used; this route
  must never invoke them.

## Decision log

- 2026-06-20: Selected `G6c` performance guardrails as the next post-G6b slice because
  `state/reconciliation-dispositions.md` retains it as an isolated G6 surface, live
  performance/spatial/backpressure contracts already exist, and G8 observability remains
  later until local deployment/release boundaries and hosted-observability blockers are
  settled.

## Progress log

- 2026-06-20: Reconciled live `origin/main`, created clean worktree
  `worktrees/perf-guard` on `codex/perf-guard`, and opened this plan before behavior
  edits.
- 2026-06-20: Added focused tests for the missing `app.performance_guardrails` helper
  and `/ui/performance-guardrails` route. The initial focused run failed with
  `ModuleNotFoundError`, then passed after implementation (`8 passed`). Broader
  performance/spatial/load-test/backpressure tests passed (`63 passed`), OpenAPI parity
  passed (`2 passed`), focused ruff/mypy passed, performance-baseline, spatial
  query-plan, release-readiness, readiness-matrix validators passed, the load-test
  wrapper passed in `-ValidateOnly` mode, and `tasks/task_queue.yaml` parsed with `G6c`
  active.
- 2026-06-20: Final `.\scripts\verify.ps1` passed after workspace validation, backend
  tests, ruff, and mypy over `338` source files. DB smoke was skipped by default.
