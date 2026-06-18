# Workflow Load Proof

## Goal
Make the local release-candidate load-test scenarios exercise a real area-to-report
admission workflow instead of accepting validation-shaped POST probes. This advances
`L10-PERF-006` repo-local proof while preserving that hosted production load capacity
and SLOs remain unproven.

## Non-goals
- No hosted load test, production SLO, or capacity benchmark claim.
- No new dependency or external load-testing tool.
- No CI live HTTP gate by default.
- No committed measured result artifacts.
- No database schema, source connector, or hosted deployment change.
- No selected-county DS-017, vendor/license, IdP, billing, or alert-routing decision.

## Current state
- This is a Level 9/10 follow-on pass selected from
  `state/LEVEL_9_10_GATE_MATRIX.md`, not a standalone performance claim.
- `config/performance_baseline.yaml` defines sequential and concurrent local scenarios
  with `/health`, `/version`, `/metrics`, `POST /areas`, and `POST /report-runs`.
- Before this pass, `scripts/load_test_runner.py` could write `load_test_result_v1` JSON
  evidence, but its POST payloads did not prove a successful report-admission workflow.
- Before this pass, `docs/runbooks/load_testing.md` said 4xx POST responses were expected
  and not counted as errors, which was too weak for the stated MVP workload proof.
- `scripts/run_load_test.ps1 -ValidateOnly`, `scripts/performance_baseline_check.py`, and
  release-readiness checks validate artifacts without sending HTTP requests or creating
  measured result artifacts.
- `tasks/task_queue.yaml`, `plans/README.md`, and the top of `state/PROJECT_STATE.md`
  were rerouted from the completed queue-backpressure plan to this active pass.

## Proposed design
Keep the same endpoint mix and request counts, but make the runner stateful where the
workflow requires state:

1. `POST /areas` sends the API's valid area-create shape.
2. Each successful area response is parsed for `area_id`.
3. `POST /report-runs` uses that `area_id` and `rural_land_purchase`.
4. POST requests fail when expected success statuses are not returned; 4xx responses are
   no longer considered acceptable for the workflow workload.
5. JSON results continue to use `load_test_result_v1` top-level fields, with richer
   request records for expected status and failure reasons.

Alternatives rejected:
- Merely documenting that current 4xx responses are weak proof: accurate but does not
  move the proof surface.
- Adding hosted or external-load-tooling fields: premature until hosted platform
  authority exists.
- Moving directly to selected-county packaged cases in the load test: higher setup/auth
  surface and less focused on the current `L10-PERF-006` load-test contract.

## Bottom-up sequence
1. Add/adjust load-runner tests to require valid `/areas` and `/report-runs` workflow
   behavior, expected statuses, and failure on unexpected 4xx.
2. Update `scripts/load_test_runner.py` with a typed request result and stateful workflow
   request generation for sequential and concurrent scenarios.
3. Update the performance baseline config, checker, and runbooks to pin successful POST
   semantics while preserving validate-only boundaries.
4. Reroute state/task files from completed `R-006` to a new active `R-007` workflow load
   proof task.
5. Run focused tests and validators, then the canonical verification gate.

## Files likely to change
| File | Expected change |
|---|---|
| `scripts/load_test_runner.py` | Use valid workflow payloads, parse `area_id`, and fail unexpected POST statuses. |
| `config/performance_baseline.yaml` | Record expected statuses for each request mix entry. |
| `scripts/performance_baseline_check.py` | Validate expected-status contract and runbook wording. |
| `backend/tests/test_load_test_artifacts.py` | Cover successful workflow request chaining and 4xx failure semantics. |
| `docs/runbooks/load_testing.md` | Document successful workflow load semantics and retained local-only limits. |
| `docs/runbooks/performance.md` | Align release-candidate load proof language. |
| `plans/README.md` | Route to this active plan. |
| `tasks/task_queue.yaml` | Mark `R-006` done and add active `R-007`. |
| `state/PROJECT_STATE.md` | Record the new active checkpoint and R-006 completion boundary. |
| `state/LEVEL_9_10_GATE_MATRIX.md` | Name this as the next unblocked pass while keeping hosted proof partial. |
| `state/WORKLOG.md` | Record the slice. |
| `state/VALIDATION_LOG.md` | Record verification results. |

## Tests / verification
```powershell
cd backend; python -m pytest -q .\tests\test_load_test_artifacts.py .\tests\test_performance_artifacts.py
python .\scripts\performance_baseline_check.py
.\scripts\run_load_test.ps1 -ValidateOnly
python .\scripts\release_readiness_check.py
python .\scripts\readiness_matrix_check.py
git diff --check
git diff --name-only --diff-filter=D
.\scripts\verify.ps1
```

If a local server is already available or can be started safely, also run:

```powershell
.\scripts\run_load_test.ps1 -BaseUrl http://127.0.0.1:<port>
```

Live load-test result JSON remains local artifact evidence and must not be committed.

## Risks and blockers
- A real live load test still only proves local single-node behavior.
- `POST /report-runs` admission does not prove full selected-county packaged corpus
  ingestion; `/operator-cases/{case_id}/report` remains that stronger proof path.
- Hosted latency, dashboard, alerting, billing, DS-017, and IdP/RBAC remain blocked by
  external decisions.

## Decision log
- 2026-06-18: Chose workflow-valid local load-test semantics after the matrix showed
  hosted deployment/DS-017/IdP work remained blocked and the current load runner could
  pass while POST workload requests returned 4xx validation responses.

## Progress log
- 2026-06-18: Plan opened from clean `origin/main` after PR #69 merged and routing still
  pointed at the completed queue-backpressure plan.
- 2026-06-18: Rerouted active plan/task state to `R-007`, updated the load runner to
  create valid areas and queue reports from returned `area_id` values, pinned expected
  success statuses in the performance baseline contract, and updated runbooks/tests so
  POST 4xx validation responses fail the workload proof.
- 2026-06-18: Focused tests, performance baseline checker, validate-only load wrapper,
  focused ruff/mypy, release-readiness, readiness-matrix, and a temporary local live load
  run passed. The live run proved sequential `20/20` and concurrent `40/40` workflow
  requests with `POST /areas` returning `201` and `POST /report-runs` returning `202`.
- 2026-06-18: `git diff --check`, no-deletions check, attribution scan, and default
  `.\scripts\verify.ps1` passed. DB smoke was skipped by default.
- 2026-06-18: Marked `R-007` done and routed the active plan to
  `plans/2026-06-18-county-rc-proof.md` for the next selected-county release-candidate
  proof refresh.
