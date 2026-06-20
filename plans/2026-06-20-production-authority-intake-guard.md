# Production Authority Intake Guard

## Goal
Add a validate-only production-authority intake guard that cross-checks the currently
blocked external authority streams before any hosted, DS-017, image-publication,
identity/RBAC, observability, billing, or Bologna recorded-source decision can be
treated as actionable.

## Non-goals
- Do not approve DS-017, select a vendor, or change source readiness.
- Do not select a hosted platform, provision infrastructure, publish images, write
  secrets, create billing integration, or create hosted observability.
- Do not select a Bologna AOI, approve Bologna sources, capture fixtures, run
  connectors, implement a Bologna rulepack, or generalize a multi-geography framework.
- Do not change API, UI, DB schema, report semantics, CI hosted jobs, or Level 10
  authority status.

## Current state
Live `origin/main` contains PR #109 (`BSR-001`), PR #110 post-BSR routing, and PR #111
(`BSG-001`). `BSA-001` remains blocked on explicit product/AOI/source-review authority.
Existing catalogs already record DS-017 source entitlement, hosted deployment,
access-control, image-publication, cost, hosted observability, and Bologna source
authority blockers, but no single production-wide intake guard ties those blockers to
`state/PRODUCTION_AUTHORITY_PACKET.md` and `state/LEVEL_9_10_GATE_MATRIX.md`. The
Level 9/10 authority context remains that repo-local proof is not hosted production
authority.

## Proposed design
Create `config/production_authority_intake.yaml` as the cross-catalog source of truth
for missing external authority streams. A dedicated Python checker validates that every
stream remains blocked, uncited, and disallowed for decision updates, and that each
stream's required evidence matches the lower-level authority catalog it references.

Compose the checker into release readiness because release readiness already aggregates
lower-level production blockers. Keeping the guard standalone would make it easier for
future production handoffs to miss one of the blocked authority classes.

## Bottom-up sequence
1. Add the intake catalog, checker, wrappers, and runbook.
2. Add focused artifact tests and negative drift tests.
3. Compose the checker into release readiness.
4. Update manifest, task routing, production authority packet, project state, and logs.
5. Run focused validators, focused tests, style/type checks, no-deletion checks,
   workspace validation, and the canonical Windows verify gate.

## Files likely to change

| File | Expected change |
|---|---|
| `config/production_authority_intake.yaml` | New validate-only authority-stream catalog |
| `scripts/production_authority_intake_check.py` | New cross-catalog checker |
| `scripts/run_production_authority_intake_check.ps1` | Windows wrapper |
| `scripts/run_production_authority_intake_check.sh` | POSIX wrapper |
| `docs/runbooks/production_authority_intake.md` | Operator runbook and boundary |
| `backend/tests/test_production_authority_intake_artifacts.py` | Focused artifact and drift tests |
| `config/release_readiness.yaml` | Add required check |
| `scripts/release_readiness_check.py` | Compose checker |
| `backend/tests/test_release_readiness_artifacts.py` | Expect composed checker |
| `docs/runbooks/release_readiness.md` | Document aggregate proof |
| `MANIFEST.md` | Route the new authority artifact |
| `state/PRODUCTION_AUTHORITY_PACKET.md` | Name the machine-readable intake guard |
| `tasks/task_queue.yaml` | Add `PAI-001` |
| `state/PROJECT_STATE.md` | Record current checkpoint and next route |
| `state/WORKLOG.md` | Record completed work |
| `state/VALIDATION_LOG.md` | Record commands and results |
| `plans/README.md` | Update plan routing summary |

## Tests / verification
```powershell
py -3.12 .\scripts\production_authority_intake_check.py
.\scripts\run_production_authority_intake_check.ps1
py -3.12 .\scripts\release_readiness_check.py
py -3.12 -m pytest backend\tests\test_production_authority_intake_artifacts.py backend\tests\test_release_readiness_artifacts.py -q
cd backend; ruff check ..\scripts\production_authority_intake_check.py ..\scripts\release_readiness_check.py .\tests\test_production_authority_intake_artifacts.py .\tests\test_release_readiness_artifacts.py
cd backend; py -3.12 -m mypy ..\scripts\production_authority_intake_check.py ..\scripts\release_readiness_check.py .\tests\test_production_authority_intake_artifacts.py .\tests\test_release_readiness_artifacts.py
py -3.12 .\scripts\source_readiness.py --priority Must --json
py -3.12 .\scripts\readiness_matrix_check.py
git diff --check
git diff --name-only --diff-filter=D
.\scripts\validate_workspace.ps1
.\scripts\verify.ps1
```

Expected signals: production-authority intake passes, release readiness passes with the
new composed checker, Must-source readiness remains `sources=8 ready=7 blocked=1` with
`DS-017` blocked, and no tracked deletion appears.

## Risks and blockers
- External authority remains absent; this guard cannot unlock DS-017, hosted production,
  identity/RBAC, observability, image publication, billing, or Bologna.
- The guard must stay validate-only. Any future non-empty `authority_references` or
  `decision_updates_allowed: true` needs source-specific checker changes and cited
  external evidence.
- DB smoke may remain skipped locally unless `RUN_DB_SMOKE=1` is explicitly set.

## Decision log
- 2026-06-20: Compose production authority intake into release readiness rather than
  keeping it standalone, because release readiness is the existing aggregate production
  boundary.
- 2026-06-20: Keep `BSA-001` blocked. A production-wide intake guard is not source/AOI
  authority and cannot justify Bologna fixture or runtime work.

## Progress log
- 2026-06-20: Created clean worktree `worktrees/auth-intake` on `codex/auth-intake`
  from live `origin/main` at `53aaa96`.
- 2026-06-20: Added the validate-only intake catalog, checker, wrappers, runbook,
  focused tests, and release-readiness composition.
- 2026-06-20: Focused tests, focused ruff/mypy, lower-level authority validators,
  readiness matrix, workspace validation, and default `.\scripts\verify.ps1` passed.
  DB smoke was skipped by default.
