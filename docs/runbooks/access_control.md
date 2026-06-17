# Access Control Runbook

## Purpose

Use `config/access_control.yaml` as the repo-local Level 10 access-control posture
catalog. It records the current API-key middleware, private-beta operator UI
API-key cookie bridge, UI reviewer-session bridge, local scoped reviewer
service-account boundary, reviewer-authenticated and scoped operator routes, intentionally public
health/version routes, and production auth blockers.

This runbook does not add user accounts, OAuth/OIDC, full user RBAC, automatic key
rotation, external secrets management, or hosted identity-provider integration.

## Current Controls

| Control | Status | Evidence |
|---|---|---|
| API-key middleware | Implemented, default off | `ApiKeyAuthMiddleware` protects non-public paths when `REQUIRE_API_KEY=true`, uses `X-API-Key`, supports raw or `sha256:<64-hex>` configured secrets, fails closed when required but unconfigured, and leaves `/health` and `/version` public |
| API-key static lifecycle | Implemented configured rotation substrate | `API_KEY_SPECS` accepts comma-separated `id|status|secret` entries, where `status` is `active` or `retired`; active specs authenticate, retired specs do not, and malformed, duplicate-id, or duplicate-secret specs fail closed |
| API-key audit logging | Implemented structured runtime logs plus DB events | Protected-path API-key decisions and `/ui/auth` login attempts emit `event_type=api_key_auth`, outcome, status code, method, path, auth source, and configured `api_key_id` for accepted `API_KEY_SPECS` keys without logging the provided key, configured secret, or query string. When API-key auth and DB services are both enabled, decisions are also written to `audit.events` |
| UI API-key cookie bridge | Implemented private-beta browser bridge | When `REQUIRE_API_KEY=true`, `/ui/auth` is public and accepts the same configured API keys as `X-API-Key`. Successful form login sets a signed expiring HttpOnly SameSite cookie scoped to `/ui` without storing the submitted API key and may redirect back to a safe `/ui/*` return path; only `/ui/*` routes accept that cookie as an alternative to the header. Cookie-authenticated UI mutation forms require a signed CSRF token derived from the HttpOnly UI cookie, and logout uses a CSRF-protected POST. The token is signed with `UI_AUTH_COOKIE_SECRET`; non-local API-key-locked app environments fail fast when that setting is blank, while local/dev/development/test environments may use a per-process generated fallback. Non-local `APP_ENV` values set the cookie `Secure` flag automatically. JSON/API routes such as `/areas` still require `X-API-Key` |
| Reviewer service account | Implemented local scoped substrate | `LocalServiceAccountReviewerAuth` requires `X-Reviewer-Id` plus `X-Reviewer-Token`, supports raw or `sha256:<64-hex>` configured tokens, requires explicit `REVIEWER_ACCOUNT_SCOPES`, and fails closed when unconfigured |
| UI reviewer session bridge | Implemented private-beta browser bridge | `/ui/auth/reviewer` and first submitted UI action credentials can set a signed expiring HttpOnly SameSite reviewer cookie scoped to `/ui`. The cookie stores reviewer id, scopes, expiry, and a non-secret HMAC binding to the configured reviewer token spec; raw reviewer tokens are not stored, reviewer-token rotation invalidates existing reviewer sessions, per-action scopes are still enforced, and JSON/API routes still require `X-Reviewer-Id` plus `X-Reviewer-Token` headers |
| Operator routes | Reviewer-authenticated and scoped | Connector invocation/scheduling requires `connector:run`, connector review decisions require `connector:review`, queue/live-job health reads require `operations:read`, report retry requires `report:retry`, and manual approved-connector report creation requires `report:run` |
| Public health routes | Intentionally public | `/health` and `/version` remain unauthenticated for local and deployment smoke checks |

## Validate Access Control

Run from the repository root:

```powershell
.\scripts\run_access_control_check.ps1
```

The check is validate-only and static: it verifies declared controls, source
phrases, and named tests without starting the API or seeding runtime data.
Run the pytest targets named below for behavioral proof. The check verifies that:

- the Windows and POSIX wrappers delegate to the shared
  `scripts/access_control_check.py` validator;
- the access-control catalog names current controls and production blockers;
- referenced authority files exist;
- API-key middleware still uses `X-API-Key`, keeps only `/health` and `/version`
  public, supports raw and `sha256:<64-hex>` configured secrets, and fails closed with
  401/403/503 behavior;
- `API_KEY_SPECS` supports configured active/retired key lifecycle specs, authenticates
  only active specs, and fails closed for malformed lifecycle entries;
- API-key auth emits structured runtime audit logs and, in DB-service mode, durable
  `audit.events` rows for accepted, missing, invalid, and unconfigured decisions,
  including `/ui/auth` login attempts, without logging or persisting secret material;
- `/ui/auth` serves a public HTML form without exposing configured secrets, sets
  a signed expiring path-scoped HttpOnly SameSite cookie only after the same
  API-key verifier accepts the submitted key, requires `UI_AUTH_COOKIE_SECRET`
  for non-local API-key-locked app environments, uses a per-process fallback only
  for local/dev/development/test app environments, sets `Secure` automatically for non-local
  app environments, requires signed CSRF tokens for cookie-authenticated UI mutation
  forms, keeps logout on a CSRF-protected POST, does not store the submitted API key
  in the cookie, and `/areas` rejects cookie-only API access;
- reviewer auth still requires `X-Reviewer-Id` and `X-Reviewer-Token`, uses
  constant-time token comparison through raw or `sha256:<64-hex>` configured tokens, and
  fails closed with 401/403/503 behavior;
- UI reviewer sessions do not expose submitted reviewer tokens, are invalidated by
  token rotation or scope removal, remain scoped to `/ui`, and do not authenticate
  JSON/API reviewer-protected routes;
- reviewer accounts require explicit route scopes through `REVIEWER_ACCOUNT_SCOPES`;
- operator route modules depend on `ReviewerPrincipal` and enforce the route's scope;
- current tests cover API-key and reviewer-auth failure paths;
- CI includes the `access-control` validate-only job.

## Operator Workflow

1. For local fixture mode, leave `REQUIRE_API_KEY=false` unless testing production
   request gating.
2. For deployment smoke or any shared environment, set `REQUIRE_API_KEY=true` and provide
   `API_KEYS` through the environment, never through committed files. Prefer
   `sha256:<64-hex>` entries for shared or production-like environments.
3. For planned static key rotation, prefer `API_KEY_SPECS` over bare `API_KEYS`:
   add the new key as `new-id|active|sha256:<64-hex>`, deploy, move callers to the
   new key, then mark the old entry `old-id|retired|sha256:<64-hex>` or remove it.
   Retired entries are kept only as explicit fail-closed configuration evidence; they
   do not authenticate.
4. For private-beta browser access with `REQUIRE_API_KEY=true`, operators can visit
    `/ui/auth`, submit the configured API key, and receive a session cookie scoped to
   `/ui`. The cookie contains a signed expiring token carrying the key digest and
   expiry, not the submitted API key. Set `UI_AUTH_COOKIE_SECRET` to a high-entropy
   value in shared environments so cookies remain valid across restarts and replicas.
   When `REQUIRE_API_KEY=true` outside local/dev/development/test `APP_ENV` values,
   startup fails closed if this setting is blank; only local/dev/development/test app
   environments use a per-process local signing secret at startup.
   Non-local `APP_ENV` values set `Secure` automatically; use `UI_AUTH_COOKIE_SECURE`
   to force that flag in any environment. Cookie-authenticated UI mutation forms carry
   a signed CSRF token derived from the HttpOnly UI cookie; refresh the page before
   retrying a stale form. Sign-out is a CSRF-protected POST from `/ui/auth/logout`.
   The cookie is not accepted by JSON/API routes; scripts and API clients must still
   send `X-API-Key`.
5. Override the fixture `REVIEWER_ACCOUNTS` and `REVIEWER_ACCOUNT_SCOPES` values before
   any shared or production-like reviewer/operator workflow. Every account must have
   explicit scopes. Prefer `id:sha256:<64-hex>` reviewer token specs outside local fixture
   mode.
6. Browser operators can use `/ui/auth/reviewer` to start a reviewer session once,
   or submit reviewer credentials on a UI action to set the same session. API clients
   must still use `X-Reviewer-Id` and `X-Reviewer-Token`.
7. Treat a failed access-control proof as a release blocker until the current controls,
   tests, catalog, and runbook are reconciled.
8. Do not claim full user auth/RBAC until user accounts, identity-provider integration,
   full role policy, automatic key rotation, hosted retention, and audit semantics are designed,
   implemented, and verified.

## Known Limits

- No full user auth/RBAC exists yet.
- No OAuth/OIDC integration or hosted identity provider exists.
- No user-account persistence exists.
- No hosted secret manager integration exists.
- API keys are static environment values; raw and `sha256:<64-hex>` configured secrets
  are supported.
- The `/ui/auth` cookie bridge is a private-beta browser convenience, not full user
  auth/RBAC. It stores a signed expiring token in an HttpOnly cookie scoped to `/ui`,
  not the submitted API key. It uses separate UI-cookie signing material instead of
  API-key specs/hashes, but does not add users, roles, OAuth/OIDC, account
  persistence, or user-bound audit semantics.
- A configured static key lifecycle exists through `API_KEY_SPECS`, but no automatic
  key-rotation scheduler, external secret manager integration, revocation propagation,
  or hosted key-management workflow exists yet.
- API-key auth writes runtime logs, and DB-service mode writes `audit.events`, but there is
  no hosted log-retention/export/SIEM integration, no user-account binding, and no
  durable per-key usage audit ledger for legacy `API_KEYS` entries without configured IDs.
- Reviewer service-account auth is a local scoped substrate, not a full production
  identity system.
- Route-level reviewer scopes exist, but full user-account role policy and hosted
  identity-provider authorization are not modeled.
