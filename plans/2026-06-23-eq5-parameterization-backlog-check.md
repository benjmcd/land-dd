# EQ-5 Parameterization Backlog Check

## Goal

Make EQ-5 executable by adding one validate-only checker that reconciles the
qualification parameterization backlog with the owner-decision packet, owner-decision
ledger, Bologna owner-answer intake, qualification status, qualification targets,
selected DS-002 source profile, task routing, and verification wiring.

## Non-goals

- Do not approve, infer, or record any new owner authority.
- Do not select a Bologna AOI, approve Bologna sources, create a recorded corpus, seed a
  database, run a DB-backed Bologna report, or alter report/API/UI behavior.
- Do not change qualification targets from globally `DRAFT`.
- Do not move `P0` from `BLOCKED` or any non-P0 qualification from `NOT_RUN`.
- Do not add production dependencies or alter DB schema/auth/security boundaries.

## Current state

- `BOL-POST-ODP4-AUTH` is done: the ODP-BOL-001 through ODP-BOL-004 response-gate
  scaffold exists, but every substantive Bologna step remains blocked by missing cited
  owner authority.
- `state/owner-decision-packet.md` is a decision-request-only artifact. It lists the
  owner decisions and consequences, but it is not an authority ledger.
- `state/owner-decisions.md` contains only QFREEZE-1, which freezes the explicitly
  listed scope/version/source and W target values while excluding P0 PASS, domain
  profiles, rubrics, broader source approval, Bologna, hosted, and runtime/report work.
- `config/bologna_owner_answer_intake.yaml` has no current owner answers and disables
  all downstream updates.
- `state/QUALIFICATION_PARAMETERIZATION_BACKLOG.md` records the blocked-state boundary,
  but it needs an executable consistency check so drift is caught by verify/CI.
- `state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 authority context for
  release-governance routing; this EQ-5 plan only maintains blocked qualification
  parameterization state and does not change Level 9/10 readiness claims.

## Proposed design

Add `scripts/qualification_parameterization_backlog_check.py` as an empirical
qualification control-plane checker. It should fail closed when:

- required control files are missing or not parseable;
- owner answers, downstream unlocks, or Bologna response statuses appear before the
  planned authority chain is updated;
- selected sources differ from DS-002 only;
- frozen criterion bindings differ from W-003 and W-011 only;
- `P0` is not `BLOCKED`, non-P0 statuses are not `NOT_RUN`, or candidate identity is
  populated;
- `EQ-5` task routing no longer matches the blocked-state proof;
- verify/CI wiring stops running the checker.

This approach is narrower than adding another Bologna gate because the ODP-BOL gate
sequence is already complete. It is also safer than starting DB-backed report work,
because the prerequisite owner authority is absent.

## Bottom-up sequence

1. Add the checker and wrappers.
2. Wire the checker into `verify.ps1`, `verify.sh`, and the qualification CI job.
3. Add focused tests for the checker pass path and an injected owner-answer failure.
4. Update the backlog with an explicit owner-decision blocker table.
5. Update task routing, manifest, plan index, project state, worklog, and validation log.
6. Run narrow checks and then the canonical Windows verify gate.

## Files likely to change

| File | Expected change |
|---|---|
| `scripts/qualification_parameterization_backlog_check.py` | New validate-only EQ-5 checker. |
| `scripts/run_qualification_parameterization_backlog_check.*` | New direct wrappers. |
| `scripts/verify.ps1`, `scripts/verify.sh` | Run the checker in the qualification section. |
| `.github/workflows/ci.yml` | Run the checker in `qualification-selftest`. |
| `backend/tests/test_qualification_parameterization_backlog_artifacts.py` | Cover pass and fail-closed owner-answer mutation. |
| `state/QUALIFICATION_PARAMETERIZATION_BACKLOG.md` | Add checker reference and owner-decision blocker table. |
| `tasks/task_queue.yaml` | Mark EQ-5 done as blocked-state consistency proof only. |
| `MANIFEST.md`, `plans/README.md`, `state/*` | Record routing and validation evidence. |

## Tests / verification

- `py -3.12 scripts\qualification_parameterization_backlog_check.py --root .`
- `py -3.12 -m pytest -q backend\tests\test_qualification_parameterization_backlog_artifacts.py`
- `py -3.12 scripts\validate_qualification.py --root . --layout repo`
- `py -3.12 scripts\bologna_owner_answer_intake_check.py`
- `.\scripts\verify.ps1`

## Risks and blockers

- External owner authority remains the blocker for any Bologna implementation. This
  checker must not be read as authority.
- If real owner authority arrives, this checker should fail until a planned update
  changes the expected boundary and cites the new evidence.
- The root checkout has stale dirty work; all implementation must stay in the clean
  repo-local worktree for `codex/eq5-audit`.

## Decision log

- 2026-06-23: Chose EQ-5 consistency checking over another Bologna gate because
  BOL-POST-ODP4-AUTH already records that gate scaffolding is complete and further
  Bologna work is external-authority dependent.
- 2026-06-23: Mark EQ-5 complete only as a blocked-state control-plane proof. No
  qualification blocker, Bologna step, source approval, hosted step, or P0 gate is
  resolved.

## Progress log

- 2026-06-23: Reconciled live `origin/main`, worktree placement, stale inbox, active
  routing files, and baseline qualification checks before editing.
- 2026-06-23: Added the checker, wrappers, verification wiring, focused tests, backlog
  table, and task routing updates.
