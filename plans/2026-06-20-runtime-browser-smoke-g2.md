# Runtime Browser Smoke G2

## Goal
Rebuild the local runtime and browser smoke gates around the accepted G1 UI surface:
account-free default local operation plus the read-only raw-data inventory. The smoke
checks should prove default local browser behavior without expecting `/ui/auth*` routes
to be mounted, while preserving protected/credentialed auth checks as opt-in paths.

## Non-goals
- Do not add readiness, selected-geography, provenance, guardrail, deployment,
  production-authority, observability, dossier-readiness, or release-readiness UI pages.
- Do not seed fixture/runtime data from GET smoke routes.
- Do not run live connectors, approve DS-017, expand county/source coverage, or change
  source-rights decisions.
- Do not change DB schema, public JSON API contracts, report semantics, auth/security
  boundaries, hosted deployment, identity/RBAC, or Level 10 gate status.
- Do not change the `state/LEVEL_9_10_GATE_MATRIX.md` Level 9/10 authority boundary;
  this slice only strengthens local smoke proof for already-admitted surfaces.
- Do not make browser smoke part of default `verify.ps1`; keep it an explicit operator
  gate.

## Current state
- Live `origin/main` at slice start is
  `cc272d0de492c424ff1b3ad715f25b25587c9e53`, after PR #92 merged the `G3b`
  selected-county source-provenance catalog.
- `state/reconciliation-dispositions.md` ranks `G2` next: rebuild runtime/browser smoke
  around the accepted G1 UI only, then add DB-backed/local deployment smoke if still
  required.
- `backend/tests/api/test_ui_api_key_auth.py` proves default local no-auth mode does
  not mount `/ui/auth*`; protected local mode still exposes `/ui/auth`.
- `scripts/ui_runtime_smoke.py` and `scripts/ui_browser_smoke.mjs` still include
  default `/ui/auth` and `/ui/auth/reviewer` route checks, which conflicts with the
  accepted account-free default-local UI posture.
- `scripts/run_deployment_smoke.*` currently proves health/version/metrics, operations,
  area creation, and report completion against Compose/Postgres, but does not run the
  accepted local UI smoke path against that DB-backed runtime.

## Proposed design
Adjust default smoke route sets to make `/ui/raw-data` a first-class default local UI
check and make `/ui/auth*` default-disabled checks explicit. Keep API-key and reviewer
session checks opt-in, so protected mode remains testable without making default local
smoke expect login pages.

Add deployment-smoke composition that runs `scripts/ui_runtime_smoke.py` against the
same Compose backend with `--operator-case-id BUN-slope`, `--compare-same-area`, and
`--expect-artifact-persistence postgres+object_store`. This proves the accepted local
operator UI path on DB-backed services without adding new UI pages or hosted claims.

Rejected alternatives:
- Copying the dirty-root smoke diff would pull in later readiness/provenance/guardrail
  pages that have not been reconstructed from live main.
- Leaving `/ui/auth*` as default smoke requirements would contradict the merged local
  no-auth route posture.
- Running browser smoke from default verification would make a local visual/browser gate
  implicit rather than operator-explicit.

## Bottom-up sequence
1. Add focused tests that fail on stale default `/ui/auth*` smoke expectations and
   missing `/ui/raw-data` smoke coverage.
2. Update `ui_runtime_smoke.py` and `ui_browser_smoke.mjs` route definitions.
3. Update deployment-smoke wrappers to run the runtime UI smoke against DB-backed
   Compose/Postgres and preserve local `APP_ENV`.
4. Update runbook/routing/state files for the G2 checkpoint and G3b merge closeout.
5. Run focused tests, syntax checks, smoke validators, workspace validation, and full
   verification. Run deployment smoke if Docker/runtime cost is acceptable in the
   current environment; otherwise record the specific blocker.

## Files likely to change
| File | Expected change |
|---|---|
| `scripts/ui_runtime_smoke.py` | Default raw-data and disabled-auth route checks; opt-in protected auth checks. |
| `backend/tests/test_ui_runtime_smoke_script.py` | Focused runtime smoke contract and failure tests. |
| `scripts/ui_browser_smoke.mjs` | Default raw-data and disabled-auth browser checks; opt-in protected auth checks. |
| `backend/tests/test_ui_browser_smoke_scripts.py` | Static browser smoke contract tests. |
| `scripts/run_deployment_smoke.ps1` | Run DB-backed UI runtime smoke after backend is healthy. |
| `scripts/run_deployment_smoke.sh` | POSIX mirror of DB-backed UI runtime smoke. |
| `backend/tests/test_deployment_smoke_scripts.py` | Static deployment smoke wrapper expectations. |
| `backend/app/api/ui.py` | Mobile containment fix for `/ui/raw-data` dense tables found by live browser smoke. |
| `backend/tests/api/test_ui_raw_data_inventory.py` | Focused raw-data responsive contract assertion. |
| `docs/runbooks/mvp_operator.md` | Document default-local smoke and protected auth option. |
| `plans/README.md` | Route active plan to G2. |
| `tasks/task_queue.yaml` | Mark G3b done and add/activate G2. |
| `state/PROJECT_STATE.md` | Record G2 checkpoint. |
| `state/WORKLOG.md` | Record implementation summary. |
| `state/VALIDATION_LOG.md` | Record verification evidence. |

## Tests / verification
```powershell
cd backend; py -3.12 -m pytest -q .\tests\api\test_ui_raw_data_inventory.py .\tests\test_ui_runtime_smoke_script.py .\tests\test_ui_browser_smoke_scripts.py .\tests\test_deployment_smoke_scripts.py
node --check .\scripts\ui_browser_smoke.mjs
py -3.12 .\scripts\ui_runtime_smoke.py --help
py -3.12 .\scripts\release_readiness_check.py
py -3.12 .\scripts\readiness_matrix_check.py
cd backend; ruff check .\app\api\ui.py .\tests\api\test_ui_raw_data_inventory.py .\tests\test_ui_runtime_smoke_script.py .\tests\test_ui_browser_smoke_scripts.py .\tests\test_deployment_smoke_scripts.py ..\scripts\ui_runtime_smoke.py
cd backend; py -3.12 -m mypy .\app\api\ui.py .\tests\api\test_ui_raw_data_inventory.py .\tests\test_ui_runtime_smoke_script.py .\tests\test_ui_browser_smoke_scripts.py .\tests\test_deployment_smoke_scripts.py ..\scripts\ui_runtime_smoke.py
.\scripts\run_deployment_smoke.ps1
.\scripts\run_ui_browser_smoke.ps1 -BaseUrl http://127.0.0.1:18081 -Mode both
git diff --check
git diff --name-only --diff-filter=D
.\scripts\validate_workspace.ps1
.\scripts\verify.ps1
```

## Risks and blockers
- Browser smoke needs a local Chrome executable and a running backend; keep it explicit
  and configurable rather than a default verify gate.
- Deployment smoke needs Docker/Compose and may be expensive locally. If not run, the
  wrapper composition must still be covered by static tests and CI/manual execution can
  provide runtime proof later.
- Default-disabled auth checks must not weaken protected-mode auth compatibility; they
  only describe default `REQUIRE_API_KEY=false` local behavior.

## Decision log
- 2026-06-20: Chose G2 because live reconciliation ranks it after G3b, and live smoke
  scripts still expect default `/ui/auth*` routes even though G1a made default local UI
  account-free.

## Progress log
- 2026-06-20: Opened from clean `worktrees/g2-smoke` on live `origin/main` at
  `cc272d0de492c424ff1b3ad715f25b25587c9e53`; no active inbox collision found.
- 2026-06-20: Added intentional red focused tests for stale default auth smoke
  assumptions, missing `/ui/raw-data` smoke coverage, and missing DB-backed UI runtime
  composition in deployment smoke wrappers; the red run failed as expected.
- 2026-06-20: Updated runtime/browser smoke scripts and deployment wrappers, then
  passed the focused smoke-script test suite, browser script syntax check, and runtime
  smoke help check before broader routing/state validation.
- 2026-06-20: Real deployment smoke found missing direct reviewer credentials and
  second-post CSRF handling in the DB-backed operator compare path; fixed the runtime
  smoke to fall back to direct reviewer form credentials when default auth routes are
  intentionally disabled and to use CSRF after the app issues a reviewer cookie.
- 2026-06-20: Real headed/headless browser smoke found `/ui/raw-data` mobile page-level
  overflow; fixed the raw-data table wrapper so the dense table scrolls inside its
  container instead of widening the page.
- 2026-06-20: Final focused tests, deployment smoke, headed/headless browser smoke,
  release/readiness validators, diff/no-deletion checks, workspace validation, and full
  `.\scripts\verify.ps1` passed.
