# EQ-R Residual Reconciliation Closeout

## Goal
Close `EQ-R` by making the residual reconciliation state honest against current live
main and by proving the remaining deferred dirty-root candidates are explicitly
listed as blocked work, not silently treated as no residual divergence.

## Non-goals
- Do not copy dirty-root files forward or create a product/runtime/UI slice.
- Do not extract a defer branch in this pass.
- Do not change Bologna authority, source rights, source readiness, qualification
  status, report semantics, API behavior, database schema, or hosted authority.
- Do not promote any deferred residual work to `PASS` or live product authority.

## Current state
- Live main for this branch is `74af6f5a26594e80efed0fb4cfa9015e7e9e135d`.
- `state/residual-reconciliation.md` already lists 17 `DEFER_STILL_BLOCKED`
  paths, but its authority SHA is stale and the queued `EQ-R` task still frames
  the old falsehood as unresolved.
- `tasks/task_queue.yaml`, `plans/README.md`, and `state/PROJECT_STATE.md` still
  route through the completed EQ-5 plan.
- `scripts/qualification_parameterization_backlog_check.py` currently pins
  `tasks/task_queue.yaml.active_plan` to EQ-5, which would make later completed
  routing fail despite the EQ-5 boundary remaining intact.
- `state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 authority context for
  active follow-on plans; this closeout does not change any gate status.

## Proposed design
Treat the minimum honest correction as the coherent path: refresh the residual
authority, add an explicit EQ-R closeout statement, route `EQ-R` to done, and
adjust the EQ-5 checker so it validates the EQ-5 task/spec and blocked authority
boundary without freezing the repository's active plan forever.

Alternative A, extracting a defer branch, preserves bytes but adds branch
management without unlocking any product work. Alternative B, copying deferred
files into main, violates the current authority boundary. Alternative C, leaving
the stale routing alone, preserves a known false planning state. The selected path
is narrower and keeps every blocked product decision blocked.

## Bottom-up sequence
1. Add focused artifact coverage for residual closeout and active-plan decoupling.
2. Update the EQ-5 checker to keep EQ-5 proof stable while allowing a later
   active plan.
3. Update residual reconciliation, routing, project state, plan index, worklog,
   and validation log.
4. Run focused checks, change-impact, diff hygiene, and full verification before
   publication.

## Files likely to change
| File | Expected change |
|---|---|
| `plans/2026-06-23-eqr-residual-closeout.md` | Active plan for this slice. |
| `state/residual-reconciliation.md` | Refresh authority and add EQ-R closeout wording. |
| `tasks/task_queue.yaml` | Route active plan to EQ-R and mark `EQ-R` done. |
| `plans/README.md` | Mark EQ-5 complete and route current plan to EQ-R. |
| `state/PROJECT_STATE.md` | Record current checkpoint and boundaries. |
| `state/WORKLOG.md` | Add concise EQ-R execution entry. |
| `state/VALIDATION_LOG.md` | Record commands and residual risk. |
| `scripts/qualification_parameterization_backlog_check.py` | Stop pinning active plan to completed EQ-5. |
| `backend/tests/test_qualification_parameterization_backlog_artifacts.py` | Update routing assertions and checker input copy list. |
| `backend/tests/test_readiness_core_artifacts.py` | Update current active-plan and completed-task assertions. |
| `backend/tests/test_residual_reconciliation_artifacts.py` | Add direct residual closeout artifact coverage. |

## Tests / verification
```powershell
py -3.12 scripts\qualification_parameterization_backlog_check.py --root .
$env:PYTHONPATH='backend'; py -3.12 -m pytest -q backend\tests\test_residual_reconciliation_artifacts.py backend\tests\test_readiness_core_artifacts.py backend\tests\test_qualification_parameterization_backlog_artifacts.py
py -3.12 scripts\readiness_matrix_check.py
$python = py -3.12 -c "import sys; print(sys.executable)"
& $python scripts\qualification_status_check.py --root . --python-command $python
py -3.12 scripts\qualification_change_impact_check.py --root . --changed-path <changed path> [...]
git diff --check
git diff --name-only --diff-filter=D
.\scripts\verify.ps1
```

## Risks and blockers
- The residual inventory remains a historical dirty-root comparison. The closeout
  must not be read as live product authority.
- The 17 deferred paths still decay as old candidate work; future use requires a
  fresh branch/worktree and new tests against current main.
- Bologna still needs cited owner authority before product/AOI, source-rights,
  corpus, or DB-backed report work can proceed.

## Decision log
- 2026-06-23: Chose explicit deferred-work closeout over defer-branch extraction
  because no deferred file is currently unblocked by owner/source/AOI authority.

## Progress log
- 2026-06-23: Baseline EQ-5 checker, readiness matrix, and focused readiness/
  backlog tests passed before edits.
- 2026-06-23: Added focused residual closeout tests, updated EQ-5 checker active-plan
  handling, refreshed residual/project/task/plan routing, and recorded validation.
- 2026-06-23: Focused tests, EQ-5 checker, readiness matrix, qualification status,
  structural qualification validation, change-impact, ruff, diff hygiene, no-deletion
  check, and full `.\scripts\verify.ps1` passed.
