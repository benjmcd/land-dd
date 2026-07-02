# Post-ODP1 Packet Authority Routing

## Goal
Move current routing off the completed ODP-BOL-001 owner-answer packet after PR #161
merged, and make the live next step explicit: real cited owner authority for
`ODP-BOL-001` product/AOI/scope before any Bologna source, corpus, fixture, DB, or
report work proceeds.

## Non-goals
- Do not record an owner answer or pilot-scope authority record.
- Do not select a Bologna AOI, approve sources, change source rights, create a
  recorded corpus, capture fixtures, seed the DB, prove a report, or change API/UI/
  report semantics.
- Do not add another Bologna scaffold or qualification PASS.

## Current state
- Live `origin/main` is `6d493ee27a1b9112da1f22bcdf086ae4c95eedc7`, the PR #161
  merge commit for `BOL-ODP1-PACKET`.
- `state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 authority context for this
  follow-on; this routing sync does not change any gate status.
- `state/PROJECT_STATE.md`, `tasks/task_queue.yaml`, and `plans/README.md` still
  describe the ODP1 packet lane as current branch work from pre-merge base
  `b5ed59e7143773f306ab216865df0133ca7b0451`.
- `config/bologna_owner_answer_intake.yaml` still has `current_owner_answers: []`.
- `config/bologna_pilot_scope_authority.yaml` still has
  `current_authority_records: []`.
- The local inbox contains older owner authority for QFREEZE-1/DS-002 only; it does
  not provide ODP-BOL-001 product/AOI/scope authority.

## Proposed design
Add a routing-only completed task, `BOL-POST-ODP1-PACKET`, and update state surfaces
to say the ODP1 packet is merged and complete. Keep `active_plan` on this routing sync
and keep the task queue with no active implementation tasks, because the next
substantive Bologna step is external-owner-authority dependent.

Alternative A, starting ODP-BOL-002 source-rights work, is rejected because
`ODP-BOL-001` remains missing. Alternative B, recording authority from the existing
QFREEZE owner directive, is rejected because that directive did not authorize Bologna
product/AOI/scope decisions. Alternative C, adding another Bologna response scaffold,
is rejected because the useful repo-local scaffold is already complete.

## Bottom-up sequence
1. Update routing/state tests to expect the post-ODP1 packet routing plan and task.
2. Update `state/PROJECT_STATE.md`, `tasks/task_queue.yaml`, and `plans/README.md`.
3. Run focused routing/backlog checks, qualification status/validation, change-impact,
   diff hygiene, and full verification.

## Files likely to change
| File | Expected change |
|---|---|
| `plans/2026-06-23-post-odp1-packet-routing.md` | New routing-only plan. |
| `plans/README.md` | Mark ODP1 packet complete and route to the post-packet authority boundary. |
| `state/PROJECT_STATE.md` | Update live main SHA/current checkpoint and keep owner authority blocked. |
| `tasks/task_queue.yaml` | Add completed `BOL-POST-ODP1-PACKET` routing task and update active plan. |
| `backend/tests/test_readiness_core_artifacts.py` | Update active-plan/completed-task assertions. |
| `backend/tests/test_qualification_parameterization_backlog_artifacts.py` | Update task-routing assertions. |
| `scripts/qualification_parameterization_backlog_check.py` | Require the post-packet routing task if needed. |
| `state/WORKLOG.md` | Record execution. |
| `state/VALIDATION_LOG.md` | Record validation. |

## Tests / verification
```powershell
py -3.12 scripts\qualification_parameterization_backlog_check.py --root .
py -3.12 scripts\readiness_matrix_check.py
$python = py -3.12 -c "import sys; print(sys.executable)"
& $python scripts\qualification_status_check.py --root . --python-command $python
py -3.12 scripts\validate_qualification.py --root . --layout repo
$env:PYTHONPATH='backend'; py -3.12 -m pytest -q backend\tests\test_readiness_core_artifacts.py backend\tests\test_qualification_parameterization_backlog_artifacts.py backend\tests\test_bologna_odp1_owner_answer_packet_artifacts.py
py -3.12 scripts\qualification_change_impact_check.py --root . --changed-path <changed path> [...]
git diff --check
git diff --name-only --diff-filter=D
.\scripts\verify.ps1
```

## Risks and blockers
- This is routing cleanup only; it cannot unblock Bologna without an owner response.
- Leaving a completed packet as the active branch would invite stale-state mistakes.
- The next substantive implementation remains blocked until `ODP-BOL-001` authority is
  cited and recorded in a later slice.

## Decision log
- 2026-06-23: Chose a routing-only sync because PR #161 merged successfully and live
  state should now stop describing the packet as in-flight branch work.

## Progress log
- 2026-06-23: Baseline backlog, readiness matrix, and focused routing tests passed
  before edits.
- 2026-06-23: Updated project state, plan index, task routing, readiness-core tests,
  and backlog routing tests for the post-PR #161 authority boundary.
- 2026-06-23: Focused backlog, readiness matrix, and routing tests passed after
  correcting the EQ-5 exact-fragment line wrap and adding the Level 9/10 matrix cite.
