# Observability Readiness UI G8

## Goal

Add the narrow `G8` local observability readiness surface after the merged `G6c`
performance guardrails UI. The pass should expose existing repo-owned runtime metrics,
queue health, recovery preview, connector observability, source-failure evidence, alert
rule, deployment-smoke, and hosted-blocker authority through a read-only local operator
view and validate-only checker.

## Non-goals

- No hosted dashboard provisioning, alert routing, pager/on-call setup, hosted log
  retention, log shipping, SIEM integration, hosted deployment, public endpoint opening,
  secret writing, live connector execution, runtime source-readiness mutation, DS-017
  approval, source/vendor expansion, Bologna pilot, generic AOI proof, hosted
  identity/RBAC, hosted SLO/capacity proof, or Level 10 completion claim.
- No public JSON API contract change beyond the server-rendered local UI route.
- No DB schema change, source registry mutation, connector runtime behavior change,
  report semantics change, or production dependency addition.

## Current state

- `G6c` performance guardrails UI is merged on live `origin/main` at
  `3ea51589fd2a69e52b474c8a38baf8047a5d7744`.
- The dirty root checkout remains preserved candidate evidence only; this work is in
  clean worktree `worktrees/obs-ready` on branch `codex/obs-ready`.
- `state/reconciliation-dispositions.md` retains `backend/app/observability_readiness.py`,
  `backend/tests/api/test_ui_observability_readiness.py`,
  `backend/tests/test_observability_readiness_artifacts.py`,
  `config/observability_readiness.yaml`, `scripts/observability_readiness_check.py`,
  and the Windows/POSIX wrappers as an isolated `G8` local-only observability slice.
- Existing live-main observability authority is spread across `backend/app/core/metrics.py`,
  `backend/app/api/metrics.py`, `backend/app/connectors/observability.py`,
  `config/ops_alert_rules.yaml`, `config/hosted_deployment.yaml`,
  `config/data_retention.yaml`, `config/release_readiness.yaml`,
  `docs/runbooks/alerting.md`, `scripts/run_deployment_smoke.ps1`,
  `scripts/run_deployment_smoke.sh`, and focused tests.
- `state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 authority for this slice.
  This plan may make local observability posture easier to inspect, but it must not
  promote hosted dashboarding, alert delivery, pager/on-call, hosted log retention,
  production traffic observability, or Level 10 production operations gates.

## Proposed design

Add a machine-readable `config/observability_readiness.yaml` catalog and
`scripts/observability_readiness_check.py` validator. Then add
`backend/app/observability_readiness.py` to parse that catalog and verify referenced
repo-relative artifacts before rendering `/ui/observability-readiness`.

Rejected alternatives:

- Fold this into operations or performance guardrails: those slices are already merged
  and have different blocker semantics.
- Execute deployment smoke from the UI helper: deployment smoke is live runtime proof,
  while the UI route must remain GET-only and repo-file-read-only.
- Treat alert-rule presence as hosted observability: current alert rules are repo-local
  validation authority only; hosted delivery and log retention remain blockers.

## Bottom-up sequence

1. Add failing focused artifact and UI tests for the observability catalog, checker,
   parser, fail-closed behavior, route, and navigation links.
2. Implement the observability catalog, checker, and wrappers.
3. Implement the read-only helper over the catalog and existing artifacts.
4. Add `/ui/observability-readiness` and navigation without changing metrics,
   operations, connector, or report runtime behavior.
5. Compose the validate-only observability checker into release-readiness artifacts.
6. Regenerate OpenAPI stubs because the route set changes.
7. Run focused observability/release checks, OpenAPI parity, validators, workspace, and
   full verification before updating state to completed.

## Files likely to change

| File | Expected change |
|---|---|
| `backend/tests/test_observability_readiness_artifacts.py` | New catalog/checker/wrapper/release-readiness tests. |
| `backend/tests/api/test_ui_observability_readiness.py` | New parser, fail-closed, route, and navigation tests. |
| `config/observability_readiness.yaml` | New local-only observability readiness catalog. |
| `scripts/observability_readiness_check.py` | New validate-only checker over current observability authority. |
| `scripts/run_observability_readiness_check.ps1` | Windows wrapper for the checker. |
| `scripts/run_observability_readiness_check.sh` | POSIX wrapper for the checker. |
| `backend/app/observability_readiness.py` | Read-only parser/model over the observability catalog. |
| `backend/app/api/ui.py` | Add GET-only local observability readiness route and nav link. |
| `config/release_readiness.yaml` | Add validate-only observability readiness check. |
| `scripts/release_readiness_check.py` | Compose the new checker into release-readiness validation. |
| `api/openapi_stub.yaml` | Regenerated FastAPI contract stub for the new UI route. |
| `docs/planning_pack/api/openapi_stub.yaml` | Regenerated planning-pack mirror. |
| `MANIFEST.md` | Route to the new observability readiness source-of-truth files. |
| `plans/README.md` | Active-plan pointer. |
| `tasks/task_queue.yaml` | Active-plan routing and validation commands. |
| `state/PROJECT_STATE.md` | Current checkpoint and boundaries. |
| `state/WORKLOG.md` | Work summary. |
| `state/VALIDATION_LOG.md` | Commands, results, and residual risk. |

## Tests / verification

```powershell
cd backend
py -3.12 -m pytest -q .\tests\test_observability_readiness_artifacts.py .\tests\api\test_ui_observability_readiness.py
py -3.12 -m pytest -q .\tests\test_observability_readiness_artifacts.py .\tests\api\test_ui_observability_readiness.py .\tests\api\test_metrics.py .\tests\api\test_operations.py .\tests\connectors\test_connector_observability.py .\tests\test_alerting_artifacts.py .\tests\test_deployment_smoke_scripts.py .\tests\test_release_readiness_artifacts.py
ruff check .\app\observability_readiness.py .\app\api\ui.py .\tests\api\test_ui_observability_readiness.py .\tests\test_observability_readiness_artifacts.py ..\scripts\observability_readiness_check.py ..\scripts\release_readiness_check.py
py -3.12 -m mypy .\app\observability_readiness.py .\app\api\ui.py .\tests\api\test_ui_observability_readiness.py .\tests\test_observability_readiness_artifacts.py ..\scripts\observability_readiness_check.py ..\scripts\release_readiness_check.py
cd ..
py -3.12 .\scripts\observability_readiness_check.py
.\scripts\run_observability_readiness_check.ps1
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

- A local observability view can overclaim if it reads like hosted dashboards, alert
  routing, pager/on-call, or hosted log retention. Catalog limits, route copy, and tests
  must keep those blockers explicit.
- Deployment smoke is useful runtime proof but is not safe to invoke from a GET-only UI
  helper.
- Existing `/metrics`, `/operations/*`, and connector observability runtime behavior
  must remain unchanged.

## Decision log

- 2026-06-20: Selected `G8` local observability readiness because `G6a/G6b/G6c` are
  merged, `state/reconciliation-dispositions.md` retains the observability catalog,
  checker, helper, and tests as an isolated slice, and live main already has local
  metrics, queue/recovery, connector event, alert-rule, and deployment-smoke authority.

## Progress log

- 2026-06-20: Reconciled live `origin/main`, created clean worktree
  `worktrees/obs-ready` on `codex/obs-ready`, audited current observability authority,
  and opened this plan before behavior edits.
- 2026-06-20: Added red artifact/UI tests, then implemented
  `config/observability_readiness.yaml`, the validate-only checker and wrappers,
  `backend/app/observability_readiness.py`, `/ui/observability-readiness`, navigation,
  release-readiness composition, and OpenAPI stub regeneration.
- 2026-06-20: Focused observability tests passed (`14 passed`) after review hardening
  added schema-ref drift coverage, adjacent
  metrics/operations/connector/alerting/deployment-smoke/release-readiness tests passed,
  focused ruff and mypy passed, observability-readiness/release-readiness/readiness
  matrix validators passed, and OpenAPI parity passed (`3 passed`). Diff/no-deletion
  checks passed with only existing OpenAPI line-ending normalization warnings, workspace
  validation passed, and final `.\scripts\verify.ps1` passed with backend tests, ruff,
  and mypy over `341` source files. DB smoke was skipped by default.
