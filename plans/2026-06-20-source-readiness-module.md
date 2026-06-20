# Source Readiness Module Extraction

## Goal
Make `backend/app/source_registry/readiness.py` the packaged authority for source-readiness record construction while preserving the existing `scripts/source_readiness.py` CLI behavior and JSON contract.

## Non-goals
- Do not change source-readiness counts, source-rights policy, connector readiness semantics, DS-017 blocker status, or review freshness thresholds.
- Do not add UI routes, public API changes, DB schema changes, live connector execution, generated artifacts, or hosted/source authority claims.
- Do not promote any broader dirty-root readiness/UI candidate work.

## Current state
- Live `origin/main` already contains the package-manifest CI gate merge commit.
- `state/reconciliation-dispositions.md` ranks `G3a` after `G7a`: extract source-readiness logic into a packaged module and keep CLI/tests focused on source-rights/freshness fail-closed behavior.
- `scripts/source_readiness.py` currently owns both CLI handling and business logic.
- `backend/tests/source_registry/test_source_readiness.py` loads `scripts/source_readiness.py` directly, so tests cannot prove packaged-module authority.
- `backend/app/source_registry/readiness.py` does not exist in live main.
- `state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 authority map; this slice preserves the existing source-readiness blocker boundary and does not claim new Level 10 hosted/source authority.

## Proposed design
Move the dataclasses and readiness construction helpers into `backend/app/source_registry/readiness.py`; keep `scripts/source_readiness.py` as the command-line wrapper that loads registry rows and serializes the module output.

Rejected alternatives:
- Keep script-only logic: this preserves the current coupling and fails the retained G3a disposition.
- Copy logic into the package while leaving script logic duplicated: this creates drift between CLI proof and importable backend behavior.
- Broaden into source-readiness UI or source policy changes: those are separate G3/G5 slices and would mix authority boundaries.

## Bottom-up sequence
1. Add a focused failing test proving source-readiness records are built from the packaged module.
2. Add `backend/app/source_registry/readiness.py` with the extracted record and freshness logic.
3. Refactor `scripts/source_readiness.py` to delegate to the packaged module and keep the CLI output stable.
4. Update state files to mark `G7a` as merged and route the active slice to `G3a`.
5. Run focused tests, validators, lint/type checks, workspace validation, and full verification.

## Files likely to change
| File | Expected change |
|---|---|
| `backend/app/source_registry/readiness.py` | New packaged source-readiness authority |
| `scripts/source_readiness.py` | CLI wrapper delegates to packaged module |
| `backend/tests/source_registry/test_source_readiness.py` | Import packaged module directly and keep CLI JSON coverage |
| `plans/README.md` | Active plan routes to this slice |
| `tasks/task_queue.yaml` | Mark `G7a` done and add/activate `G3a` |
| `state/PROJECT_STATE.md` | Current checkpoint routes to G3a |
| `state/WORKLOG.md` | Record audit/edit/validation progress |
| `state/VALIDATION_LOG.md` | Record validation evidence |

## Tests / verification
- Red: `cd backend; py -3.12 -m pytest -q .\tests\source_registry\test_source_readiness.py`
- Green focused: `cd backend; py -3.12 -m pytest -q .\tests\source_registry\test_source_readiness.py`
- CLI JSON: `py -3.12 .\scripts\source_readiness.py --priority Must --as-of 2026-06-18 --json`
- CLI readiness gate: `py -3.12 .\scripts\source_readiness.py --priority Must --as-of 2026-06-18 --require-ready`
- Release readiness: `py -3.12 .\scripts\release_readiness_check.py`
- Readiness matrix: `py -3.12 .\scripts\readiness_matrix_check.py`
- Focused lint/type: `cd backend; py -3.12 -m ruff check .\app\source_registry\readiness.py ..\scripts\source_readiness.py .\tests\source_registry\test_source_readiness.py`
- Focused type check: `cd backend; py -3.12 -m mypy .\app\source_registry\readiness.py ..\scripts\source_readiness.py .\tests\source_registry\test_source_readiness.py`
- Diff integrity: `git diff --check`; `git diff --name-only --diff-filter=D`
- Workspace gate: `.\scripts\validate_workspace.ps1`
- Final gate: `.\scripts\verify.ps1`

## Risks and blockers
- The main risk is silent drift between the CLI JSON contract and packaged module behavior. The test suite must cover both direct module calls and CLI JSON output.
- State files currently lag the merged package-manifest PR. This slice should repair routing prose without claiming new product capability.
- DS-017 remains blocked by vendor/license/cost authority; this extraction must not make it ready.

## Decision log
- 2026-06-20: Chose module extraction plus CLI delegation because it creates one importable backend source of truth and preserves the existing validate-only CLI surface.

## Progress log
- 2026-06-20: Plan opened from clean `worktrees/src-ready` on live `origin/main`; audit found script-only readiness logic and stale active-plan routing after G7a merge.
- 2026-06-20: Intentional red focused pytest failed only because `app.source_registry.readiness` was missing.
- 2026-06-20: Added packaged readiness module, delegated the CLI wrapper to it, and updated tests so direct record-building coverage imports the packaged module.
- 2026-06-20: Focused source-readiness tests, Must-source CLI JSON, `--require-ready`, focused ruff, and focused mypy passed; Must readiness remained `sources=8 ready=7 blocked=1`.
- 2026-06-20: `release_readiness_check.py` passed; `readiness_matrix_check.py` initially failed because the plan omitted the Level 9/10 matrix citation, so the plan authority context was corrected.
- 2026-06-20: First full `verify.ps1` failed because the source-readiness wrapper no longer exposed `STALE_AFTER_DAYS` for an alerting artifact test; the wrapper now explicitly re-exports the package constant.
- 2026-06-20: Focused compatibility tests, focused ruff/mypy, diff integrity, no-deletion audit, workspace validation, final `verify.ps1`, final Must source-readiness, release-readiness, and readiness-matrix checks passed. DB smoke was skipped by default.
