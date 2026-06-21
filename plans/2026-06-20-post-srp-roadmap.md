# Post-SRP Roadmap

## Goal
Close the merged `SRP-001` runtime-provenance regression lane and record the current
next-step decision from live repo evidence: candidate-work reconciliation has no
remaining unblocked implementation slice that should be copied forward; external
authority remains required before DS-017, hosted production, or Bologna work can
advance.

## Non-goals
- Do not add source, report, connector, API, UI, DB schema, or runtime behavior.
- Do not implement the deferred `project_readiness.py` or `release_readiness.py`
  parser candidates without a new control-plane consolidation need.
- Do not approve DS-017, select a vendor, provision hosted services, select a Bologna
  AOI, approve Bologna sources, capture fixtures, implement rulepacks, or claim Level
  10 authority.

## Current state
Live `origin/main` is `12de4f5bcf044f813f68e04d71c1617dab5c4eb9`, which includes PR
#114 (`RSR-001`) and its prerequisite PR #113 (`SRP-001`). `SRP-001` reworked the
retained dirty-root runtime-provenance candidate as a current-main test-only
regression; `RSR-001` records the post-SRP residual routing closeout.

`state/residual-reconciliation.md` now has two remaining `STILL_DIVERGENT` paths:

- `backend/app/project_readiness.py`
- `backend/app/release_readiness.py`

Both are read-only orientation/control-plane parser candidates. Current live authority
for release readiness remains `config/release_readiness.yaml` plus
`scripts/release_readiness_check.py`; current live authority for Level 9/10 routing
remains `state/LEVEL_9_10_GATE_MATRIX.md` and `state/PRODUCTION_AUTHORITY_PACKET.md`.
The Level 9/10 authority context remains unchanged: repo-local selected-county proof
is not hosted production proof.

Must-source readiness remains `sources=8 ready=7 blocked=1`, with `DS-017` as the only
blocked Must source. `BSA-001` remains blocked on explicit product/AOI/source-review
authority.

## Proposed design
Treat this as a routing and evidence closeout rather than an implementation lane. The
remaining parser candidates should stay deferred until a future slice proves that a
control-plane consolidation surface is needed and can be validated without replacing
the existing executable validators as authority.

This avoids manufacturing implementation work from candidate residue while keeping the
long-term compiler path honest:

1. external source/hosted/Bologna authority can unlock the relevant blocked lanes;
2. absent that authority, only future repo-local work with direct evidence value should
   be selected;
3. candidate files remain evidence, not live truth.

## Bottom-up sequence
1. Update `tasks/task_queue.yaml` to point at this routing plan.
2. Update `plans/README.md`, `state/PROJECT_STATE.md`, and
   `state/residual-reconciliation.md` with the post-SRP state.
3. Record validation in `state/WORKLOG.md` and `state/VALIDATION_LOG.md`.
4. Run routing/readiness validators, no-deletion checks, workspace validation, and the
   canonical Windows verify gate.

## Files likely to change

| File | Expected change |
|---|---|
| `plans/2026-06-20-post-srp-roadmap.md` | New routing closeout plan |
| `plans/README.md` | Current routing plan update |
| `tasks/task_queue.yaml` | Add `RSR-001` and route active plan |
| `state/PROJECT_STATE.md` | Record post-SRP checkpoint |
| `state/residual-reconciliation.md` | Refresh live SHA and remaining residual status |
| `state/WORKLOG.md` | Record work |
| `state/VALIDATION_LOG.md` | Record validation |

## Tests / verification
```powershell
py -3.12 .\scripts\source_readiness.py --priority Must --json
py -3.12 .\scripts\release_readiness_check.py
py -3.12 .\scripts\production_authority_intake_check.py
py -3.12 .\scripts\readiness_matrix_check.py
git diff --check
git diff --name-only --diff-filter=D
.\scripts\validate_workspace.ps1
.\scripts\verify.ps1
```

## Risks and blockers
- This does not unblock the long-term objective by itself; it prevents stale routing
  from implying that completed work is still active.
- The remaining compiler milestones require either external authority
  (DS-017/hosted/Bologna) or a future explicitly selected repo-local slice.

## Decision log
- 2026-06-20: Do not implement `project_readiness.py` or `release_readiness.py` from
  the dirty-root candidate stack. Existing validators remain authority, and no current
  blocker requires parser consolidation.
- 2026-06-20: Keep `BSA-001`, DS-017, hosted platform, identity/RBAC, hosted
  observability, billing, image publication, and Level 10 authority blocked.

## Progress log
- 2026-06-20: Created `worktrees/post-srp` on `codex/post-srp` from live `origin/main`
  at `b144544`.
- 2026-06-20: Updated plan routing, task queue, project state, and residual
  reconciliation to close `SRP-001` and keep remaining parser candidates deferred.
- 2026-06-20: Merged through PR #114 at
  `12de4f5bcf044f813f68e04d71c1617dab5c4eb9`.
