# Selected-County Runtime Provenance Regression

## Goal
Close the retained residual test-hardening candidate for selected-county runtime
provenance by adding a current-main regression that proves selected-county fixture
reports hydrate source provenance review bundles, preserve case-specific connector
scope, and remain idempotent under repeated report creation.

## Non-goals
- Do not change source, report, connector, API, UI, DB schema, or runtime behavior.
- Do not promote dirty-root code wholesale or revive stale DS-010/DS-011/DS-023 helper
  assumptions from the old candidate test.
- Do not approve DS-017, hosted deployment, Bologna, source expansion, or Level 10
  authority.
- Do not claim live county assessor, owner/value/title, legal zoning, or parcel-title
  authority.

## Current state
`state/residual-reconciliation.md` retains
`backend/tests/api/test_operator_cases_runtime_provenance.py` as one of the only
remaining `STILL_DIVERGENT` candidate paths. The dirty-root test is stale: it expects
per-source helper internals like `_SOURCE_SPECS`, while live `origin/main` now records
selected-county runtime provenance under the selected-county fixture package source
and keeps unsupported screening categories as a separate source with no retrieval
runs.

Focused baseline tests from `backend` pass for operator cases, source-provenance UI,
and private-MVP readiness. `scripts/source_readiness.py --priority Must --json` still
reports `sources=8 ready=7 blocked=1` with `DS-017` blocked. The Level 9/10 authority
context in `state/LEVEL_9_10_GATE_MATRIX.md` remains unchanged: repo-local selected
county proof is not hosted production proof.

## Proposed design
Add a fresh test file under `backend/tests/api/` that targets live contracts:

- selected-county fixture package source appears in report source manifests;
- fixture review bundles have one source, one dataset, one dataset version, and exactly
  the current case's connector retrieval runs;
- repeated report creation does not duplicate fixture retrieval runs;
- different selected-county cases keep different connector scopes;
- the unsupported screening source has no fixture retrieval runs.

This is an intentionally narrow regression over existing in-memory services. DB-backed
operator-case persistence remains covered by `test_operator_cases_db.py`; a separate
DB runtime-provenance idempotency slice can be planned only if current DB coverage is
proven insufficient.

## Bottom-up sequence
1. Re-ground live `origin/main`, root dirtiness, and worktree placement.
2. Audit the dirty-root candidate test against live selected-county/source-provenance
   contracts.
3. Add the current-main regression.
4. Update residual reconciliation/routing/state as a test-hardening completion.
5. Run focused tests, focused style/type checks, source-readiness/release/readiness
   validators, no-deletion checks, workspace validation, and the canonical Windows
   verify gate.

## Files likely to change

| File | Expected change |
|---|---|
| `backend/tests/api/test_operator_cases_runtime_provenance.py` | New current-main regression test |
| `plans/2026-06-20-selected-county-runtime-provenance-regression.md` | This plan |
| `plans/README.md` | Route latest completed/current plan |
| `tasks/task_queue.yaml` | Add `SRP-001` |
| `state/residual-reconciliation.md` | Mark the residual candidate as reworked |
| `state/PROJECT_STATE.md` | Record the checkpoint and preserved blockers |
| `state/WORKLOG.md` | Record work performed |
| `state/VALIDATION_LOG.md` | Record commands/results |

## Tests / verification
```powershell
cd backend
py -3.12 -m pytest tests\api\test_operator_cases_runtime_provenance.py -q
py -3.12 -m pytest tests\api\test_operator_cases_runtime_provenance.py tests\api\test_operator_cases_api.py tests\api\test_ui_source_provenance.py tests\test_private_mvp_readiness.py -q
ruff check .\tests\api\test_operator_cases_runtime_provenance.py
py -3.12 -m mypy .\tests\api\test_operator_cases_runtime_provenance.py
cd ..
py -3.12 .\scripts\source_readiness.py --priority Must --json
py -3.12 .\scripts\release_readiness_check.py
py -3.12 .\scripts\readiness_matrix_check.py
git diff --check
git diff --name-only --diff-filter=D
.\scripts\validate_workspace.ps1
.\scripts\verify.ps1
```

## Risks and blockers
- This proves in-memory selected-county runtime provenance only. DB smoke may remain
  skipped locally unless `RUN_DB_SMOKE=1` is set, though CI `db-verify` should cover
  the full DB-enabled suite after publication.
- The test intentionally avoids stale per-DS source assumptions; source-readiness and
  private-MVP readiness catalogs remain the authority for DS-010/DS-011/DS-023
  expectations.

## Decision log
- 2026-06-20: Rework the dirty-root candidate test instead of copying it because live
  selected-county provenance no longer exposes the old `_SOURCE_SPECS` internals.
- 2026-06-20: Keep the slice test-only because live behavior already hydrates the
  selected-county fixture package review bundle and remains idempotent in memory.

## Progress log
- 2026-06-20: Created `worktrees/runtime-prov` on `codex/runtime-prov` from live
  `origin/main` at `b62bc48`.
- 2026-06-20: Added the focused runtime-provenance regression and confirmed the new
  test passes locally.
- 2026-06-20: Focused regression suite, ruff, mypy, source/readiness validators,
  workspace validation, and default `.\scripts\verify.ps1` passed. DB smoke was
  skipped by default.
