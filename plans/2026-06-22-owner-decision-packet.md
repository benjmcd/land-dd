# Owner Decision Packet

## Goal
Create a repo-owned packet that turns the remaining owner-driven qualification and
Bologna choices into explicit questions, expected consequences, downstream gates, and
reversal costs. This is the next pursuit after QFREEZE-1 because QFREEZE-1 landed the
first narrow freeze, while the remaining blockers are now decision-ordering and
authority problems rather than code implementation problems.

## Non-goals
- Do not freeze any additional target, domain profile, criterion contract, judgment
  rubric, source profile, Bologna source, AOI, or report-use boundary.
- Do not change qualification status: P0 remains `BLOCKED`, and non-P0 statuses remain
  `NOT_RUN`.
- Do not create fixtures, source registry rows, DB seeds, connectors, report artifacts,
  runtime/API/UI proof, DS-017 approval, hosted authority, or Level 10 claims.
- Do not treat this packet as owner authority. It is a decision-request and consequence
  map only.

## Current state
- Live `origin/main` is `cc77b83b5b2bc17b5dc49a2539cb126fbde1bb10`, which includes
  PR #151 and the QFREEZE-1 owner-authorized scope/source/Windows freeze.
- `state/owner-decisions.md` records the only branch-local owner authority currently
  available: DS-002 selection, scope/version fields, and W-003/W-011 target binding
  freeze.
- `state/QUALIFICATION_PARAMETERIZATION_BACKLOG.md` still records P0 as `BLOCKED`,
  49 active draft/unresolved target bindings, 60 active draft contracts, 16 active
  draft judgment rubrics, 8 draft domain profiles, and one approved selected source
  profile (`DS-002` only).
- `state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 authority context; this
  packet does not change its hosted, production, source, qualification, or release
  blocker statuses.
- `state/PROJECT_STATE.md` and `tasks/task_queue.yaml` still route QFREEZE-1 as active,
  so this pass must close QFREEZE-1 routing and make the decision packet the active
  repo-local pursuit.

## Proposed design
Add `state/owner-decision-packet.md` as the canonical decision-request packet. Keep it
separate from `state/owner-decisions.md` because the latter is an authority ledger and
must not record inferred or recommended decisions.

The packet uses a repeated row shape:
- decision ID and owner question;
- current repo-confirmed state;
- recommended default;
- allowed owner outcomes;
- consequences and downstream gates;
- required evidence;
- reversal cost and over/under-freeze risk.

Talmudic coherence check:
- Position A, freeze broad values now: fastest path to green-looking routing, but
  incoherent because many values would be agent-inferred and post-result mutable.
- Position B, keep only the backlog: accurate but underspecified because it does not
  explain the owner consequences of each choice.
- Position C, add a non-authorizing decision packet and route to it: preserves evidence
  boundaries while giving the owner an actionable decision tree. Choose C.

## Bottom-up sequence
1. Add tests that require the decision packet, non-authorizing language, and active
   routing to `OWNER-DEC-1`.
2. Add the packet and route QFREEZE-1 to done.
3. Update project state, plan index, backlog references, worklog, validation log, and
   manifest routing.
4. Run focused tests and validators.
5. Run full verification before handoff.

## Files likely to change
| File | Expected change |
|---|---|
| `state/owner-decision-packet.md` | New decision-request and consequence packet. |
| `state/QUALIFICATION_PARAMETERIZATION_BACKLOG.md` | Reference the packet as the owner-facing decision map. |
| `tasks/task_queue.yaml` | Mark QFREEZE-1 done and make OWNER-DEC-1 active. |
| `state/PROJECT_STATE.md` | Route the current checkpoint to OWNER-DEC-1 after PR #151. |
| `plans/README.md` | Record QFREEZE-1 as latest completed and this plan as current. |
| `MANIFEST.md` | Route empirical-qualification decisions to the packet. |
| `backend/tests/test_qualification_parameterization_backlog_artifacts.py` | Packet/routing assertions. |
| `backend/tests/test_readiness_core_artifacts.py` | Current readiness routing assertions. |
| `state/WORKLOG.md` | Execution notes. |
| `state/VALIDATION_LOG.md` | Validation evidence. |

## Tests / verification
- `py -3.12 -m pytest -q tests\test_qualification_parameterization_backlog_artifacts.py tests\test_readiness_core_artifacts.py` from `backend\`.
- `py -3.12 scripts\qualification_status_check.py --root .`
- `py -3.12 scripts\validate_qualification.py --root . --now 2026-06-22T12:00:00Z`
- `py -3.12 scripts\readiness_matrix_check.py`
- Focused `ruff`/`mypy` on touched tests.
- `git diff --check`
- `git diff --name-only --diff-filter=D`
- `.\scripts\verify.ps1`

## Risks and blockers
- The packet is only useful if it stays non-authorizing; confusing it with
  `state/owner-decisions.md` would fabricate authority.
- Overly broad decisions could force requalification or invalidate a future sealed run.
- Under-specified decisions keep P0, Bologna, and Level 10 paths blocked, which is
  correct if evidence is absent.

## Decision log
- 2026-06-22: Use a non-authorizing owner-decision packet as the next repo-local pursuit
  after QFREEZE-1; do not freeze any additional values in this pass.

## Progress log
- 2026-06-22: Created `worktrees/owner-packet` from live
  `origin/main@cc77b83`, read startup/routing/qualification artifacts, confirmed
  baseline status remains `BLOCKED=1 NOT_RUN=20`, and drafted this executable plan.
