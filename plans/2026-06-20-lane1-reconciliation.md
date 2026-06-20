# Lane 1 Repository-State Reconciliation

## Goal

Establish a durable, reviewable reconciliation lane for the current split between live
`origin/main` and recoverable local candidate work. The outcome is not to land the
whole dirty workspace. The outcome is to classify, preserve, decompose, and selectively
land only coherent slices that still match current architecture and validation
requirements.

## Non-goals

- Do not treat local `R-023` through `R-056` state prose as merged product truth.
- Do not land the dirty root workspace as one broad change.
- Do not discard, reset, delete, or overwrite local candidate files.
- Do not claim hosted deployment, DS-017 approval, full identity/RBAC, hosted alerting,
  production observability, source entitlement, or Level 10 completion.
- Do not broaden product scope, geography scope, report semantics, database schema,
  auth/security boundaries, or source-rights policy during reconciliation.
- Do not publish coordination-only files such as `state/agent-inbox/*`.

## Current state

Live authority was refreshed before this plan was opened.

```text
origin/main: c3364ea01605cef09e03da6da8551fa4d1a155e8
local main: c3364ea01605cef09e03da6da8551fa4d1a155e8
dirty root branch: codex/r026-raw-readiness-ui at c3364ea01605cef09e03da6da8551fa4d1a155e8
clean reconciliation worktree: worktrees/l1-recon on codex/l1-recon
origin/main vs dirty-root HEAD: 0 ahead / 0 behind
open GitHub PRs: none
tracked modified files in dirty root: 53
untracked files in dirty root: 75
tracked deleted files in dirty root: 0
```

Live `origin/main` records `R-022` error-state/no-leak hardening as the latest completed
lane and does not select a next implementation lane. The dirty root contains a large
uncommitted candidate stack that advances local state/task/plan claims through later
`R-0xx` readiness and UI slices. Those claims are recoverable candidate evidence, not
merged repo truth.

The Level 9/10 gate matrix remains the release-readiness authority surface during this
reconciliation. `state/LEVEL_9_10_GATE_MATRIX.md` is not superseded by local candidate
readiness pages, and any retained slice that affects release, hosted, source, identity,
observability, artifact, or production claims must update that matrix only after the
executable behavior and validation evidence land.

Initial file-level classification is recorded in `state/reconciliation-inventory.md`.
Provisional dependency grouping is recorded in `state/reconciliation-slices.md`.
The first candidate content review is recorded in `state/r023-review.md`.
Initial retain/rework/defer/archive/discard decisions are recorded in
`state/reconciliation-dispositions.md`.

Observed candidate buckets:

| Bucket | Examples | Initial state |
|---|---|---|
| Local production/readiness UI surfaces | `backend/app/*_readiness.py`, `backend/app/*_guardrails.py`, UI tests | `LOCAL_UNCOMMITTED` |
| Runtime/browser smoke and local deployment proof | `scripts/ui_runtime_smoke.py`, `scripts/ui_browser_smoke.mjs`, deployment smoke wrappers | `LOCAL_UNCOMMITTED` |
| Release/package/observability validators | package manifest, observability, local deployment checkers | `LOCAL_UNCOMMITTED` |
| State/task/plan prose | `state/PROJECT_STATE.md`, `tasks/task_queue.yaml`, `plans/2026-06-19-*.md` | `LOCAL_UNCOMMITTED` |
| Coordination-only inbox material | `state/agent-inbox/*` | `COORDINATION_ONLY` |
| Ignored local artifacts/caches | `.codesight/`, `.mypy_cache/`, `.pytest_cache/`, `.ruff_cache/`, `local_artifacts/` | ignored/runtime |

## Proposed design

Use a selective landing lane with live `origin/main` as the authority surface and the
dirty root as preserved candidate evidence. All retained work should be reintroduced
from clean worktrees under `worktrees/<short-name>`, not edited directly in the dirty
root.

Talmudic debate:

| Position | Argument | Resolution |
|---|---|---|
| Land the whole dirty stack | It is recoverable and may already be validated locally. | Rejected because it mixes many lanes, includes coordination state, and lets local prose outrun live proof. |
| Discard the stack and start after `R-022` | Live main is clean and authoritative. | Rejected because the candidate work is material and recoverable; discarding it loses evidence. |
| Selectively classify and land slices | Preserves recoverable work while forcing each slice through current-main proof. | Accepted because it respects live authority, minimizes blast radius, and keeps completion semantics honest. |

The first implementation unit is documentation/control-plane only: this plan plus state
routing. Later units must be split by independently testable capability. Current
review ranks the early retained slices as:

1. package manifest validator, release-package manifest verification, and CI gate;
2. source-readiness extraction;
3. local account-free/auth posture;
4. raw-data inventory route;
5. selected-county source-provenance catalog;
6. DB-backed local UI smoke and deployment-smoke guard;
7. read-only readiness/guardrail surfaces in small batches;
8. selected-county provenance, report inventory, and evidence/claim surfaces;
9. observability readiness after local deployment/release boundaries are clear.

That ordering is provisional. Each candidate slice must be re-audited against current
`origin/main`, current tests, and current boundaries before implementation.

## Bottom-up sequence

1. Preserve the dirty root as candidate evidence. Do not reset, clean, rebase, or
   destructively partition it.
2. Record the state envelope and active reconciliation plan from a clean worktree.
3. Build a file-level classification table for every tracked and untracked candidate
   file: `MERGED_LIVE`, `LOCAL_UNCOMMITTED`, `COORDINATION_ONLY`, `GENERATED_IGNORED`,
   `STALE_OR_SUPERSEDED`, or `UNKNOWN`.
4. Group product-relevant candidate files into coherent slices with dependencies and
   minimum proof commands.
5. Record retain/rework/defer/archive/discard decisions for every candidate file.
6. For the first retained slice, create or reuse a fresh short worktree under
   `worktrees/`, reapply only that slice, and run focused tests before any broad verify.
7. Repeat for each slice only after the previous slice is reviewable and state prose
   matches executable behavior.
8. Stop after each slice, re-fetch `origin/main`, re-check PR/worktree/branch state,
   and re-rank the lane portfolio.

## Files likely to change

| File | Expected change |
|---|---|
| `plans/2026-06-20-lane1-reconciliation.md` | New executable reconciliation plan and state envelope. |
| `plans/README.md` | Route the active plan to reconciliation while keeping `R-022` as latest completed live lane. |
| `tasks/task_queue.yaml` | Add `REC-001` as the active reconciliation task. |
| `state/reconciliation-inventory.md` | Record initial file-level candidate classification. |
| `state/reconciliation-slices.md` | Record provisional candidate grouping and first content-review target. |
| `state/r023-review.md` | Record R-023 content-review findings and reconstruction constraints. |
| `state/reconciliation-dispositions.md` | Record initial disposition decisions and focused PR sequence. |
| `state/PROJECT_STATE.md` | Record the reconciliation checkpoint and preserve live/candidate authority split. |
| `state/WORKLOG.md` | Record the lane-start audit and worktree creation. |
| `state/VALIDATION_LOG.md` | Record read-only reconciliation checks and residual validation risk. |

Future product slices may touch backend, scripts, config, docs, tests, or CI, but only
after their file groups are classified and their plan/proof is narrowed.

## Tests / verification

Planning/control-plane slice:

```powershell
git status --short --branch
git diff --check
git diff --name-only --diff-filter=D
.\scripts\validate_workspace.ps1
```

Candidate classification slice:

```powershell
git -C ..\.. diff --name-status origin/main --
git -C ..\.. ls-files --others --exclude-standard
git -C ..\.. diff --stat origin/main --
```

Product landing slices must choose focused tests by touched surface. Full verification
for any material product slice remains:

```powershell
.\scripts\verify.ps1
```

DB-enabled proof is separate and must not be implied when `RUN_DB_SMOKE=1` is not set.

## Risks and blockers

- The dirty root may include coherent product work, stale work, generated artifacts,
  and coordination-only messages in the same diff.
- Local state prose may claim validations that need to be rerun after selective
  reapplication.
- Untracked files have no commit history; they must be treated as candidate content
  until individually reviewed.
- Large UI/readiness changes may need decomposition before any PR can be reviewed
  safely.
- Browser proof should use both headless and headed Chrome when a retained UI slice
  actually changes browser behavior.
- External-authority blockers remain unchanged: DS-017, hosted deployment, identity,
  billing, hosted alerting, registry/image publication, secret management, and hosted
  production proof.

## Decision log

- 2026-06-20: Refreshed `origin/main` and confirmed live `main`, local `main`, and the
  dirty root branch all point at `c3364ea01605cef09e03da6da8551fa4d1a155e8`.
- 2026-06-20: Selected Lane 1 because recoverable material local divergence exists and
  no open remote PR supersedes it.
- 2026-06-20: Created clean worktree `worktrees/l1-recon` on `codex/l1-recon` from
  `origin/main` to avoid editing the dirty root candidate stack.
- 2026-06-20: Chose `REC-001` instead of `R-023` because `R-023` and later ids already
  appear in local candidate state and should not be promoted by naming.
- 2026-06-20: Added `state/reconciliation-dispositions.md` because Lane 1 requires
  retain/rework/defer/archive/discard decisions for every candidate file before product
  landing work can safely start.

## Progress log

- 2026-06-20: Opened reconciliation plan and routed active control-plane state to
  Lane 1. No product code, schema, source registry, API, report semantics, or auth
  behavior changed in this step.
- 2026-06-20: Added `state/reconciliation-inventory.md` with initial file-level
  classification. Next step is content/dependency review and coherent slice grouping,
  not product implementation yet.
- 2026-06-20: Added `state/reconciliation-slices.md`. `R-023 Local-only raw-data UI
  posture` is the first content-review target because it is the lowest-dependency
  dirty-root product candidate, but no product implementation has been selected yet.
- 2026-06-20: Reviewed R-023 candidate surface and recorded `state/r023-review.md`.
  Conclusion: reconstruct minimal R-023 from live `origin/main`; do not copy dirty-root
  `ui.py` or smoke scripts wholesale because they already contain later lane work.
- 2026-06-20: Added `state/reconciliation-dispositions.md` after independent read-only
  reviews of UI/auth/browser, source/report/provenance, and packaging/CI/readiness
  surfaces. The matrix records initial decisions for every candidate path and ranks the
  next focused PR sequence without changing product behavior.
