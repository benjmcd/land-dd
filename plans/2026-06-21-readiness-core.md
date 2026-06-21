# Readiness Control-Plane Core

## Goal
Rework the two remaining dirty-root `STILL_DIVERGENT` parser concepts into current-main
read-only readiness models for project routing and release readiness.

## Non-goals
- Do not copy the dirty-root modules wholesale.
- Do not add UI/API routes, schemas, database changes, connectors, fixtures, report
  behavior, source-readiness changes, or release-readiness semantic changes.
- Do not approve DS-017, hosted authority, identity/RBAC, Bologna source/AOI authority,
  fixture capture, runtime use, report use, or Level 10 status.

## Current state
Live `origin/main` is `7f4fa03677eee523d1bf65d94b74b720fb706893`, which merged PR
#118 (`AUTH-HANDOFF`). The root checkout remains the dirty preserved
`codex/r026-raw-readiness-ui` lane, so this work is isolated in
`worktrees/readiness-core`.

`state/residual-reconciliation.md` still lists two paths as `STILL_DIVERGENT`:
`backend/app/project_readiness.py` and `backend/app/release_readiness.py`. The dirty
candidate `project_readiness.py` expects older state-field names, and the dirty
candidate `release_readiness.py` lags the current release catalog. Both need current-main
rework, not wholesale promotion.

`state/LEVEL_9_10_GATE_MATRIX.md` and `config/release_readiness.yaml` remain the
authority surfaces. This slice is parser/consolidation work only.

## Proposed design
Add read-only app-layer readiness models:

- `backend/app/project_readiness.py` parses the current checkpoint, Level 9/10 gate
  matrix, task queue, and latest validation log into typed dataclasses.
- `backend/app/release_readiness.py` parses `config/release_readiness.yaml` into typed
  dataclasses, checks referenced proof/authority paths, rejects duplicate ids, and keeps
  release blockers blocked.
- Focused tests prove the models load current-main artifacts and fail closed on malformed
  control-plane input.
- Residual reconciliation is updated to mark both dirty-root candidates as reworked in
  this slice.

Rejected alternative: copy the dirty-root files. They encode stale assumptions and would
weaken the current authority surfaces.

## Bottom-up sequence
1. Reconfirm live `origin/main`, worktree placement, residual classification, and
   baseline readiness validators.
2. Add read-only parser modules and focused tests against current-main artifacts.
3. Update manifest, residual reconciliation, active routing, worklog, and validation log.
4. Run focused tests/validators, no-deletion checks, workspace validation, and full
   verification.
5. Publish and merge only if CI passes; after merge, revalidate detached live main and
   remove the worktree.

## Files likely to change

| File | Expected change |
|---|---|
| `backend/app/project_readiness.py` | New current-main read-only project readiness model |
| `backend/app/release_readiness.py` | New current-main read-only release readiness model |
| `backend/tests/test_readiness_core_artifacts.py` | Focused parser/model tests |
| `MANIFEST.md` | Route the new read-only models |
| `state/residual-reconciliation.md` | Mark residual parser candidates reworked |
| `plans/2026-06-21-readiness-core.md` | New execution plan |
| `plans/README.md` | Route current plan |
| `state/PROJECT_STATE.md` | Record current checkpoint and boundaries |
| `tasks/task_queue.yaml` | Add `READINESS-CORE` |
| `state/WORKLOG.md` | Add worklog entry |
| `state/VALIDATION_LOG.md` | Record validation |

## Tests / verification
```powershell
py -3.12 .\scripts\release_readiness_check.py
py -3.12 .\scripts\readiness_matrix_check.py
py -3.12 .\scripts\production_authority_intake_check.py
py -3.12 .\scripts\source_readiness.py --priority Must --json
cd backend; py -3.12 -m pytest tests\test_readiness_core_artifacts.py tests\test_release_readiness_artifacts.py tests\test_production_authority_intake_artifacts.py -q
git diff --check
git diff --name-only --diff-filter=D
.\scripts\validate_workspace.ps1
.\scripts\verify.ps1
```

Expected signal: all checks pass, no deleted files are present, and Must-source readiness
remains `sources=8 ready=7 blocked=1` with `DS-017` still blocked.

## Risks and blockers
The main risk is treating read-only parsed summaries as new authority. The parsers are
views over existing files only; the underlying state, gate matrix, release catalog, and
validators remain authoritative. External authority blockers are unchanged.

## Decision log
- 2026-06-21: Selected current-main rework of the remaining two `STILL_DIVERGENT`
  parser candidates because it advances the reconciliation part of the long-term goal
  without crossing hosted/source/Bologna authority boundaries.

## Progress log
- 2026-06-21: Created `worktrees/readiness-core` from live `origin/main` at
  `7f4fa03677eee523d1bf65d94b74b720fb706893`.
- 2026-06-21: Baseline readiness, authority, and release validators passed before edits.
- 2026-06-21: Added current-main read-only `project_readiness` and
  `release_readiness` app models with focused fail-closed tests.
- 2026-06-21: Updated manifest, residual reconciliation, routing, worklog, and
  validation log to classify the two remaining parser candidates as reworked.
- 2026-06-21: Focused validators, no-deletion checks, workspace validation, and full
  `.\scripts\verify.ps1` passed.
