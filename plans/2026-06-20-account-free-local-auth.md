# Account-Free Local Auth Posture

## Goal
Make the default local browser runtime account-free at the route and OpenAPI level: in local/dev/development/test app environments with `REQUIRE_API_KEY=false`, `/ui/auth*` login/session routes are not mounted or advertised. Explicit protected local mode and non-local/private-beta auth behavior stay available.

## Non-goals
- Do not delete or archive auth modules.
- Do not weaken JSON/API `X-API-Key`, reviewer scope enforcement, CSRF checks, report identity tokens, or non-local fail-closed behavior.
- Do not add OAuth/OIDC, user accounts, full RBAC, hosted identity, hosted deployment, secret-manager integration, or DS-017 work.
- Do not change DB schema, source, connector, evidence, claim, report, or release-package behavior.

## Current state
- Live `origin/main` at `7204d9fbba182eb21fb32176449be3d0d174de71` includes the merged G3a source-readiness module extraction.
- `state/reconciliation-dispositions.md` ranks `G1a` after G7a/G3a: reconstruct local account-free/auth posture from live main, starting with auth/reviewer UI tests, access-control catalog/checker/docs, and explicit `APP_ENV` versus `REQUIRE_API_KEY` protected-mode behavior.
- `backend/app/main.py` currently mounts `ui_auth_router` unconditionally.
- Existing tests prove protected UI API-key cookie behavior and reviewer/report identity sessions, but do not prove default local `/ui/auth*` route/OpenAPI omission.
- `state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 authority; this slice must not promote hosted identity/RBAC or hosted production gates.

## Proposed design
Mount `ui_auth_router` only when `REQUIRE_API_KEY=true` or the app environment is not local/dev/development/test. This keeps default local browser operation account-free while preserving explicit protected local mode and non-local/private-beta compatibility.

Rejected alternatives:
- Disable auth handlers inside `ui_auth.py`: this still advertises login/session paths and keeps the local OpenAPI surface misleading.
- Remove auth files: this breaks protected/non-local behavior and violates the no-delete rule.
- Carry the broad dirty-root UI stack: that mixes G1a with raw-data, smoke, deployment, and later readiness surfaces.

## Bottom-up sequence
1. Add failing tests for default local `/ui/auth*` route and OpenAPI omission while proving protected local mode still exposes `/ui/auth`.
2. Add the conditional router mount in `backend/app/main.py`.
3. Update access-control docs/checker/catalog and state routing for G1a.
4. Run focused auth/access-control tests, validators, diff checks, workspace validation, and full verification.

## Files likely to change
| File | Expected change |
|---|---|
| `backend/app/main.py` | Conditionally include `ui_auth_router`. |
| `backend/app/api/ui_shared.py` | Hide links to auth/session setup routes when they are not mounted. |
| `backend/app/api/ui_operations.py` | Hide hard-coded reviewer-session management links when auth routes are not mounted. |
| `backend/tests/api/test_ui_api_key_auth.py` | Add default-local route/OpenAPI omission tests. |
| `scripts/access_control_check.py` | Validate conditional mount and documentation/test coverage. |
| `config/access_control.yaml` | Record default local account-free route posture. |
| `docs/runbooks/access_control.md` | Document default local omission and protected/non-local preservation. |
| `docs/runbooks/mvp_operator.md` | Document local operator auth route posture. |
| `.env.example` | Add short local no-auth route note. |
| `DESIGN.md` | Update compatibility constraint. |
| `plans/README.md` | Route active plan. |
| `tasks/task_queue.yaml` | Mark G3a done and G1a active. |
| `state/PROJECT_STATE.md` | Record checkpoint. |
| `state/WORKLOG.md` | Record progress and validation. |
| `state/VALIDATION_LOG.md` | Record commands and residual risk. |

## Tests / verification
- Red: `cd backend; py -3.12 -m pytest -q .\tests\api\test_ui_api_key_auth.py::test_local_no_auth_ui_auth_routes_are_not_mounted`
- Focused: `cd backend; py -3.12 -m pytest -q .\tests\api\test_ui_api_key_auth.py .\tests\test_access_control_artifacts.py`
- Lint/type: `cd backend; ruff check .\app\main.py .\tests\api\test_ui_api_key_auth.py .\tests\test_access_control_artifacts.py ..\scripts\access_control_check.py`
- Type: `cd backend; py -3.12 -m mypy .\app\main.py .\tests\api\test_ui_api_key_auth.py .\tests\test_access_control_artifacts.py ..\scripts\access_control_check.py`
- Validators: `py -3.12 .\scripts\access_control_check.py`; `py -3.12 .\scripts\release_readiness_check.py`; `py -3.12 .\scripts\readiness_matrix_check.py`
- Integrity: `git diff --check`; `git diff --name-only --diff-filter=D`; `.\scripts\validate_workspace.ps1`; `.\scripts\verify.ps1`

## Risks and blockers
- The local omission must not be described as hosted auth readiness or full RBAC.
- Existing auth tests that assume `REQUIRE_API_KEY=false` can use reviewer/report identity UI sessions may need to switch to explicit protected or non-local mode only if they are truly testing browser auth.
- Default OpenAPI stubs are regenerated when tracked stubs mirror default `create_app()` output for `/ui/auth*`; do not hand-edit generated mirrors.

## Decision log
- 2026-06-20: Selected conditional router mounting as the narrow G1a core because it directly proves account-free default local browser posture while preserving protected local and non-local auth code.

## Progress log
- 2026-06-20: Plan opened from clean `worktrees/auth-posture` on live `origin/main`; audit found unconditional `ui_auth_router` mounting and no default-local `/ui/auth*` OpenAPI omission test.
- 2026-06-20: Intentional red focused pytest proved default local `/ui/auth` still returned 200; added conditional router mount and docs/catalog/checker coverage; focused UI auth/access-control tests, OpenAPI parity tests, and access-control checker passed.
- 2026-06-20: Full verify exposed UI route tests still relying on `/ui/auth/reviewer` in default local no-auth mode; route tests now create signed reviewer-session cookies directly, and default local pages no longer link to unmounted `/ui/auth*` setup routes. Final full `.\scripts\verify.ps1` passed; DB smoke skipped by default.
