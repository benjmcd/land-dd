# UI Report Identity Bridge

## Goal
Enable non-local browser creation of selected-county/operator-case UI reports by deriving a signed `/ui` identity session from the existing report identity token authority. The created selected-county report must persist `workspace_id` and `requested_by` from the verified report identity token.

## Non-goals
- Do not add user accounts, OAuth/OIDC, RBAC, or database-backed browser sessions.
- Do not store or render the raw `report_identity_token` after submission.
- Do not change selected-county fixture semantics beyond authenticated provenance.

## Current state
- `backend/app/api/report_auth.py` verifies signed report identity tokens but previously returned only workspace/user claims.
- `backend/app/api/dependencies.py` treats report identity tokens as the API authority for signed-token report auth.
- `backend/app/api/ui_shared.py` owns signed `/ui` reviewer cookies and CSRF helpers.
- `backend/app/api/ui.py` selected-county UI POST required reviewer auth, then failed closed outside local-like app envs because it only had seeded local workspace/user fallback.
- `backend/app/api/ui_auth.py` owns browser auth pages under `/ui/auth`.

## Proposed design
Talmudic debate:
- Position A: post the raw bearer-style report token through every selected-county form. This is simple but keeps a reusable authority secret in rendered browser markup.
- Position B: accept the raw token once, verify it with `REPORT_IDENTITY_TOKEN_SECRET`, then store only workspace/user/expiration in a signed, path-scoped HttpOnly UI cookie. This matches the existing reviewer-session bridge and avoids echoing bearer material.
- Consensus: implement Position B, while still allowing a one-shot `report_identity_token` field on selected-county forms. The UI identity cookie expiry and `max_age` must never outlive the verified report token `exp`.

## Bottom-up sequence
1. Add tests for report token expiration claims and non-local selected-county UI identity flows.
2. Extend `ReportIdentityClaims` with token expiration.
3. Add signed UI report identity cookie helpers in `ui_shared.py`.
4. Add `/ui/auth/identity` GET/POST/logout in `ui_auth.py`.
5. Wire selected-county forms and POST in `ui.py`.
6. Update access-control static proof, runbooks, state, and OpenAPI stubs.
7. Run focused tests and static validators.

## Files likely to change
| File | Expected change |
|---|---|
| `backend/app/api/report_auth.py` | Add expiration to verified claims |
| `backend/app/api/ui_shared.py` | Add signed UI identity session helpers and form fields |
| `backend/app/api/ui_auth.py` | Add identity session management routes |
| `backend/app/api/ui.py` | Use submitted/cookie UI identity for selected-county creation |
| `backend/tests/api/test_report_auth.py` | Cover expiration claim |
| `backend/tests/api/test_ui_routes.py` | Cover UI identity token/session/fail-closed flows |
| `scripts/access_control_check.py` | Pin helper/routes/tests |
| `docs/runbooks/access_control.md` | Document browser report identity bridge |
| `docs/runbooks/mvp_operator.md` | Update selected-county UI operator instructions |
| `api/openapi_stub.yaml` | Regenerated route contract |
| `docs/planning_pack/api/openapi_stub.yaml` | Regenerated route contract |
| `state/PROJECT_STATE.md` | Record current checkpoint |

## Tests / verification
- `cd backend; $env:PYTHONPATH='.'; python -m pytest -q ./tests/api/test_report_auth.py ./tests/api/test_ui_routes.py`
- `python ./scripts/access_control_check.py`
- `PYTHONPATH=./backend python ./scripts/export_openapi_stub.py`
- OpenAPI parity tests if stubs change.

## Risks and blockers
- Cookie signing must fail closed if signing material or report token secret is unavailable outside local-like environments.
- Raw report identity tokens must not be stored in cookies or rendered back in forms.
- Cookie expiry must be bounded by verified report token expiration.

## Decision log
- 2026-06-17: Use a signed derived UI identity cookie with workspace/user/exp, not raw token persistence.
- 2026-06-17: Treat API-key, reviewer, and report-identity UI session cookies as CSRF-bearing authority for UI mutation forms.

## Progress log
- 2026-06-17: Audit complete; canonical auth sources identified in `report_auth.py`, `dependencies.py`, `ui_shared.py`, `ui_auth.py`, and `ui.py`.
- 2026-06-17: Added failing report-auth/UI route tests for token expiration, submitted identity token, identity session cookie reuse, invalid identity, CSRF-protected identity login, and selected-county report CSRF with identity plus reviewer sessions.
- 2026-06-17: Extended the UI CSRF helper so reviewer and report-identity session cookies also require signed CSRF tokens for UI mutations, including deployments that do not require API-key UI auth.
- 2026-06-17: Implemented report token expiration claims, signed UI report identity session helpers, `/ui/auth/identity` routes, selected-county UI identity wiring, docs, state, and access-control static checks.
