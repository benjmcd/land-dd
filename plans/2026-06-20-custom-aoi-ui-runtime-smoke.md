# Custom AOI UI Runtime Smoke

## Goal

Prove the custom GeoJSON AOI UI path through the same runtime smoke surface used for
selected-county operator cases: submit a fixture polygon through `/ui/intake`, wait for
the generated report, approve it through the existing reviewer UI path when needed,
verify approved delivery links, verify evidence lineage, and include that proof in the
DB-backed deployment smoke scripts.

## Non-goals

- No new source, connector, county, jurisdiction, rulepack, DS-017, Bologna, hosted
  deployment, hosted identity/RBAC, hosted object-store, alerting, SLO, capacity, or
  production-traffic authority.
- No report semantics, schema, auth policy, public API, or database migration change.
- No ranking, recommendation, suitability score, legal conclusion, or source-entitlement
  claim.

## Current state

- `G8` observability readiness UI merged through PR #100; live `origin/main` is
  `2522b734578ad498910f10598aa5404fb6601129`.
- `/ui/` already exposes "Custom GeoJSON Intake" and posts `area_geojson` plus `intent`
  to `/ui/intake`.
- API and route tests cover custom intake validation, CSRF, and report-run creation.
- `scripts/run_deployment_smoke.ps1` and `.sh` already create a custom AOI through the
  JSON API, but `scripts/ui_runtime_smoke.py` only creates selected-county UI reports.
- Custom intake schedules async report work and redirects to a report status page; the
  resulting report still needs the normal reviewer approval step before dossier,
  artifact, and lineage delivery can be inspected.
- `state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 authority for this slice:
  this work can strengthen repo-local Level 9 workflow evidence, but it does not change
  blocked or partial Level 10 hosted/source/identity gates.

## Proposed design

Add an explicit `--custom-aoi-fixture` option to `scripts/ui_runtime_smoke.py`. The
option reads a repo fixture, submits it through `/ui/intake`, waits for either approved
delivery or a pending approval page, approves pending reports using the existing reviewer
session or fallback reviewer fields, then verifies delivery links, artifact persistence
when requested, and lineage.

Rejected alternatives:

- Treat API-level `/areas` plus `/report-runs` deployment smoke as enough: that misses
  the custom AOI UI form, redirect, CSRF, approval, and lineage path.
- Auto-approve reports in production code for smoke convenience: approval is a real
  review boundary and must remain explicit.
- Reuse selected-county compare checks for custom AOI now: compare is already proven on
  same-area selected-county reports, and custom AOI compare should stay out of scope
  unless a later slice needs it.

## Bottom-up sequence

1. Add failing smoke-script tests for custom AOI fixture submission, async report-page
   waiting, reviewer-session approval, artifact persistence, and lineage labels.
2. Extend `scripts/ui_runtime_smoke.py` with custom AOI posting, bounded report wait,
   pending-approval detection, reviewer approval, artifact persistence, and lineage.
3. Compose the custom AOI UI proof into the PowerShell and POSIX deployment smoke
   wrappers with a 90-second report wait.
4. Update routing/state files to move past stale G8 and record the custom AOI proof
   boundary.
5. Run focused tests, lint/type checks, validators, workspace checks, and full
   verification before publication.

## Files likely to change

| File | Expected change |
|---|---|
| `backend/tests/test_ui_runtime_smoke_script.py` | Custom AOI smoke, wait, approval, artifact, and lineage tests. |
| `scripts/ui_runtime_smoke.py` | Add custom AOI fixture option and approval-aware report verification. |
| `scripts/run_deployment_smoke.ps1` | Include custom AOI UI runtime smoke in DB-backed smoke. |
| `scripts/run_deployment_smoke.sh` | Include custom AOI UI runtime smoke in DB-backed smoke. |
| `plans/README.md` | Route active plan to this slice. |
| `tasks/task_queue.yaml` | Mark G8 done and add active G9a. |
| `state/PROJECT_STATE.md` | Current checkpoint and boundaries. |
| `state/WORKLOG.md` | Work summary. |
| `state/VALIDATION_LOG.md` | Commands, results, and residual risk. |
| `state/LEVEL_9_10_GATE_MATRIX.md` | Refresh custom AOI runtime-smoke evidence wording. |

## Tests / verification

```powershell
py -3.12 -m pytest backend\tests\test_ui_runtime_smoke_script.py -q
cd backend
ruff check ..\scripts\ui_runtime_smoke.py tests\test_ui_runtime_smoke_script.py
cd ..
py -3.12 -m mypy scripts\ui_runtime_smoke.py
py -3.12 .\scripts\private_mvp_readiness_check.py
py -3.12 .\scripts\release_readiness_check.py
py -3.12 .\scripts\readiness_matrix_check.py
git diff --check
git diff --name-only --diff-filter=D
.\scripts\validate_workspace.ps1
.\scripts\verify.ps1
```

## Risks and blockers

- Custom intake is async and report delivery is gated by review; the smoke must wait and
  approve through the existing reviewer path rather than expecting immediate delivery.
- This proves repo-local UI workflow coverage only. Hosted deployment, hosted identity,
  hosted object storage, production traffic, DS-017, and new geography/source authority
  remain blocked or future work.
- The deployment smoke remains opt-in Docker runtime proof and must not be invoked from a
  GET-only UI helper or validate-only checker.

## Decision log

- 2026-06-20: Selected custom AOI UI runtime smoke as the next unblocked slice after G8
  because it advances generic supported-AOI workflow proof below the blocked hosted,
  DS-017, source-entitlement, and new-jurisdiction authority gates.

## Progress log

- 2026-06-20: Reconciled live `origin/main` at
  `2522b734578ad498910f10598aa5404fb6601129`, created clean worktree
  `worktrees/aoi-smoke` on `codex/aoi-smoke`, confirmed no branch/worktree/open-PR
  collision, and opened this plan.
- 2026-06-20: Added red tests for missing custom AOI smoke support, async report waiting,
  and pending-review approval; implemented `--custom-aoi-fixture`,
  approval-aware report verification, custom lineage labels, and deployment-smoke
  wrapper composition. Focused tests passed (`19 passed`), focused ruff and mypy passed,
  private-MVP/release-readiness/readiness-matrix validators passed, readiness-matrix
  wrapper and artifact tests passed, diff/no-deletion/workspace checks passed, and final
  `.\scripts\verify.ps1` passed with backend tests, ruff, and mypy over `341` source
  files. DB smoke was skipped by default.
