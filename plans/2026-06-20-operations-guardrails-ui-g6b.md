# Operations Guardrails UI G6b

## Goal

Add the narrow `G6b` local operations guardrails surface after the merged `G6a`
security/access-control guardrails UI. The pass should expose existing repo-owned
operations evidence through a read-only local operator view without executing
operational scripts, mutating queues, or claiming hosted production operations.

## Non-goals

- No hosted alert routing, pager/on-call system, dashboard provisioning, cloud billing
  integration, hosted backup policy, hosted scheduler, or production on-call claim.
- No queue mutation, recovery execution, report retry, live connector execution, purge
  execution, backup/restore execution, alert dispatch, Docker invocation, or runtime
  source-readiness validation from the UI helper.
- No public JSON API contract change beyond the server-rendered local UI route, DB schema
  change, source registry mutation, DS-017 approval, source/vendor expansion, Bologna
  pilot, generic AOI proof, hosted source authority, hosted identity/RBAC, hosted
  observability, or Level 10 completion claim.

## Current state

- `G6a` security/access-control guardrails is merged on live `origin/main` at
  `98d7211f705a91fe3e0963b294aeb5813916bff5`.
- Live state still names the pre-merge `G6a` plan as active, so this pass must correct
  routing after implementation and verification.
- `state/reconciliation-dispositions.md` retains `backend/app/operations_guardrails.py`
  and `backend/tests/api/test_ui_operations_guardrails.py` as an isolated `G6` slice.
- Current operations authority is spread across repo-owned artifacts:
  `config/ops_alert_rules.yaml`, `docs/runbooks/alerting.md`,
  `docs/runbooks/incident_response.md`, `docs/runbooks/backup_restore.md`,
  `config/data_retention.yaml`, `docs/runbooks/data_retention.md`,
  `config/ops_cost_monitoring.yaml`, `docs/runbooks/cost_monitoring.md`,
  `backend/app/api/operations.py`, `backend/app/api/ui_operations.py`,
  `backend/app/operations/recovery_preview.py`, and their validate-only check scripts.
- `state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 authority for this slice.
  This plan may make local operations posture easier to inspect, but it must not promote
  hosted alerting, pager/on-call, hosted scheduler, hosted billing, hosted backup policy,
  hosted observability, DS-017 entitlement, or Level 10 production operations gates.

## Proposed design

Build a small `backend/app/operations_guardrails.py` helper that parses the existing
operations catalogs and verifies referenced repo-relative artifacts before rendering.
The helper will fail closed on schema drift, missing required alert signals, missing
retention/cost categories, missing runbooks, missing validation scripts, or any catalog
change that turns blocked hosted operations into an implied pass.

Rejected alternatives:

- Bundle operations, performance, and observability guardrails: they have separate
  authority surfaces and different blocker semantics.
- Reuse operational validators directly inside the UI helper: several validators can run
  subprocesses or Docker checks, which is too broad for a GET-only local view.
- Add production-authority aggregation now: hosted platform, alerting, scheduler,
  billing, identity, and source-entitlement authority remain external blockers.

## Bottom-up sequence

1. Add failing focused tests for the operations guardrails parser, fail-closed behavior,
   GET-only route, and navigation links.
2. Implement the read-only helper over existing operations artifacts.
3. Add `/ui/operations-guardrails` and navigation without changing the existing protected
   `/ui/operations` workflow.
4. Regenerate OpenAPI stubs because the route set changes.
5. Run focused operations/guardrail checks, OpenAPI parity, validators, workspace, and
   full verification before updating state to completed.

## Files likely to change

| File | Expected change |
|---|---|
| `backend/tests/api/test_ui_operations_guardrails.py` | New parser, fail-closed, route, and navigation tests. |
| `backend/app/operations_guardrails.py` | Read-only parser/model over operations catalogs, runbooks, and validation scripts. |
| `backend/app/api/ui.py` | Add GET-only local operations guardrails route and nav link. |
| `api/openapi_stub.yaml` | Regenerated FastAPI contract stub for the new UI route. |
| `docs/planning_pack/api/openapi_stub.yaml` | Regenerated planning-pack mirror. |
| `MANIFEST.md` | Route to the new operations guardrails source-of-truth file after implementation exists. |
| `plans/README.md` | Active-plan pointer. |
| `tasks/task_queue.yaml` | Active-plan routing and validation commands. |
| `state/PROJECT_STATE.md` | Current checkpoint and boundaries. |
| `state/WORKLOG.md` | Work summary. |
| `state/VALIDATION_LOG.md` | Commands, results, and residual risk. |

## Tests / verification

```powershell
cd backend
py -3.12 -m pytest -q .\tests\api\test_ui_operations_guardrails.py
py -3.12 -m pytest -q .\tests\api\test_ui_operations_guardrails.py .\tests\test_alerting_artifacts.py .\tests\test_incident_rollback_artifacts.py .\tests\test_data_retention_artifacts.py .\tests\test_cost_monitoring_artifacts.py .\tests\api\test_operations.py .\tests\api\test_ui_operations_routes.py
ruff check .\app\operations_guardrails.py .\app\api\ui.py .\tests\api\test_ui_operations_guardrails.py
py -3.12 -m mypy .\app\operations_guardrails.py .\app\api\ui.py .\tests\api\test_ui_operations_guardrails.py
cd ..
py -3.12 .\scripts\alert_rules_check.py
py -3.12 .\scripts\incident_rollback_check.py
py -3.12 .\scripts\data_retention_check.py
py -3.12 .\scripts\cost_monitoring_check.py
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

- A local operations view can overclaim if it reads like hosted alerting, scheduler,
  pager, billing, or backup authority. Route copy and tests must keep those blockers
  explicit.
- Operations validators intentionally do more than parse files; the UI helper must not
  import or execute them.
- Existing protected `/ui/operations` and `/operations/*` routes must retain reviewer
  scope behavior. This pass adds only a read-only guardrails overview page.

## Decision log

- 2026-06-20: Selected `G6b` operations guardrails as the next post-G6a slice because
  `state/reconciliation-dispositions.md` retains it as an isolated G6 surface, live
  operations catalogs already exist, and G8 observability remains explicitly later until
  local deployment/release boundaries and hosted-observability blockers are settled.

## Progress log

- 2026-06-20: Reconciled live `origin/main`, created clean worktree
  `worktrees/ops-guard` on `codex/ops-guard`, and opened this plan before behavior
  edits.
- 2026-06-20: Added failing focused tests for the missing `app.operations_guardrails`
  helper and `/ui/operations-guardrails` route, then implemented the read-only parser,
  page, navigation, OpenAPI refresh, and manifest/state routing. Focused G6b tests
  passed (`8 passed`), broader operations guardrail/artifact/API tests passed
  (`75 passed`), OpenAPI parity passed (`2 passed`), focused ruff/mypy passed, and
  alert-rules, incident/rollback, data-retention, cost-monitoring, release-readiness,
  and readiness-matrix validators passed.
- 2026-06-20: Fixed limited pre-existing YAML scalar syntax drift in `tasks/task_queue.yaml`
  after adding G6b routing exposed it during a parse check. Full verification first failed
  because this active plan did not cite `state/LEVEL_9_10_GATE_MATRIX.md`; added the
  required Level 9/10 authority citation, reran readiness-matrix checks successfully, and
  final `.\scripts\verify.ps1` passed. DB smoke was skipped by default.
