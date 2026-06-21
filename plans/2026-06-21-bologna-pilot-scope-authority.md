# Bologna Pilot Scope Authority

## Goal
Add a validate-only first-gate authority packet for the Bologna recorded-source pilot
so product, one-AOI, jurisdiction, rulepack/evidence-only, DS-017-treatment,
fixture-boundary, and runtime-boundary decisions are separated from later per-source
rights review.

## Non-goals
- Do not select a Bologna AOI, approve Italy/EU/local sources, change source rights,
  promote source registry rows, capture fixtures, run connectors, seed the database, or
  create report/runtime artifacts.
- Do not approve DS-017, provision hosted services, implement hosted identity/RBAC,
  publish images, add billing, or claim Level 10 authority.
- Do not generalize a multi-geography framework before a one-AOI pilot proves reusable
  contracts.

## Current state
Live `origin/main` is `d31bb8e5b2c9849e6989544f3bf43fff065e1fef`, which merged PR
#120 (`BOL-PRIORITY`). The root checkout remains preserved dirty candidate evidence, so
this slice is isolated in `worktrees/bol-auth`.

Current Bologna catalogs already cover candidate source inventory, source rights,
source-authority intake, and recorded-source corpus requirements. The missing first
gate is a narrow product/AOI/scope authority packet. Without that, `BSA-001` has to
carry both pilot-scope authority and per-source authority in one broad blocked bucket.
`state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 authority context for this
plan; this packet does not promote any Level 9/10 status.

## Proposed design
Add `config/bologna_pilot_scope_authority.yaml` plus runbook, checker, wrappers, and
focused tests. Compose the checker into Bologna preflight, production-authority intake,
and release readiness.

Rejected alternative: directly edit source-rights rows. That would require external
product/AOI/source-review authority that is not present.

Rejected alternative: leave the first gate in prose only. That would preserve ambiguity
around whether the pilot itself is approved before per-source rights review starts.

## Bottom-up sequence
1. Reconfirm live `origin/main`, current worktree placement, and current Bologna
   authority catalogs.
2. Add the validate-only pilot-scope authority catalog, runbook, checker, wrappers, and
   focused tests.
3. Wire the catalog into preflight, production-authority intake, release readiness, and
   routing/state artifacts.
4. Run focused Bologna and readiness validators, no-deletion checks, workspace
   validation, and full verification.
5. Publish and merge only if CI passes; after merge, revalidate detached live main and
   remove the worktree.

## Files likely to change

| File | Expected change |
|---|---|
| `config/bologna_pilot_scope_authority.yaml` | New validate-only first-gate authority packet |
| `docs/runbooks/bologna_pilot_scope_authority.md` | Operator runbook and evidence checklist |
| `scripts/bologna_pilot_scope_authority_check.py` | New fail-closed checker |
| `scripts/run_bologna_pilot_scope_authority_check.ps1` | Windows wrapper |
| `scripts/run_bologna_pilot_scope_authority_check.sh` | POSIX wrapper |
| `backend/tests/test_bologna_pilot_scope_authority_artifacts.py` | Focused artifact tests |
| `config/bologna_preflight.yaml` | Cite the new first-gate packet |
| `scripts/bologna_preflight_check.py` | Compose the new checker |
| `backend/tests/test_bologna_preflight_artifacts.py` | Prove preflight composition |
| `config/production_authority_intake.yaml` | Add Bologna pilot-scope stream |
| `scripts/production_authority_intake_check.py` | Validate the new stream |
| `docs/runbooks/production_authority_intake.md` | Add checklist section |
| `config/release_readiness.yaml` | Add release-readiness proof |
| `scripts/release_readiness_check.py` | Compose the new checker |
| `backend/tests/test_release_readiness_artifacts.py` | Prove release composition |
| `MANIFEST.md` | Route the new catalog |
| `plans/README.md` | Mark current plan |
| `state/PROJECT_STATE.md` | Record checkpoint and current routing |
| `tasks/task_queue.yaml` | Add `BPS-001` task |
| `state/WORKLOG.md` | Add worklog entry |
| `state/VALIDATION_LOG.md` | Record validation |

## Tests / verification
```powershell
py -3.12 .\scripts\bologna_pilot_scope_authority_check.py
py -3.12 .\scripts\bologna_preflight_check.py
py -3.12 .\scripts\production_authority_intake_check.py
py -3.12 .\scripts\release_readiness_check.py
py -3.12 .\scripts\source_readiness.py --priority Must --json
py -3.12 .\scripts\readiness_matrix_check.py
cd backend; py -3.12 -m pytest tests\test_bologna_pilot_scope_authority_artifacts.py tests\test_bologna_preflight_artifacts.py tests\test_production_authority_intake_artifacts.py tests\test_release_readiness_artifacts.py -q
git diff --check
git diff --name-only --diff-filter=D
.\scripts\validate_workspace.ps1
.\scripts\verify.ps1
```

Expected signal: all checks pass; no deleted files exist; DS-017 remains the only
blocked Must source; Bologna remains blocked for source approval, fixture capture,
runtime/report use, and multi-geography generalization.

## Risks and blockers
The main risk is treating the first-gate packet as product authority. The checker keeps
all approvals false, all downstream unlocks disabled, and all authority references
empty until external evidence exists.

## Decision log
- 2026-06-21: Selected a dedicated pilot-scope authority packet because it advances
  the prioritized Bologna path without crossing source-rights, fixture, runtime, or
  hosted authority boundaries.

## Progress log
- 2026-06-21: Created `worktrees/bol-auth` from live `origin/main` at
  `d31bb8e5b2c9849e6989544f3bf43fff065e1fef`.
