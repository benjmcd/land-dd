# Access Control Runbook

## Purpose

Use `config/access_control.yaml` as the repo-local Level 10 access-control posture
catalog. It records the current API-key middleware, private-beta operator UI
API-key cookie bridge, UI reviewer-session bridge, local scoped reviewer
service-account boundary, reviewer-authenticated and scoped operator routes, intentionally public
health/version routes, and production auth blockers.

This runbook does not add user accounts, OAuth/OIDC, full user RBAC, automatic key
rotation, external secrets management, or hosted identity-provider integration.
It also treats `secret_management_contract` in `config/access_control.yaml` as a
validate-only secret handoff catalog, not a hosted secret manager integration.
It treats `identity_rbac_contract` in `config/access_control.yaml` as a
validate-only identity/RBAC design handoff, not production identity or RBAC.

## Current Controls

| Control | Status | Evidence |
|---|---|---|
| API-key middleware | Implemented, default off | `ApiKeyAuthMiddleware` protects non-public paths when `REQUIRE_API_KEY=true`, uses `X-API-Key`, supports raw or `sha256:<64-hex>` configured secrets for local/dev/development/test, requires hashed `API_KEY_SPECS` outside those app environments, fails closed when required but unconfigured, and leaves `/health` and `/version` public |
| API-key static lifecycle | Implemented configured rotation substrate | `API_KEY_SPECS` accepts comma-separated `id|status|secret` entries, where `status` is `active` or `retired`; active specs authenticate, retired specs do not, malformed, duplicate-id, or duplicate-secret specs fail closed, and non-local `APP_ENV` values require `sha256:<64-hex>` secrets |
| API-key audit logging | Implemented structured runtime logs plus DB events | Protected-path API-key decisions and `/ui/auth` login attempts emit `event_type=api_key_auth`, outcome, status code, method, path, auth source, and configured `api_key_id` for accepted `API_KEY_SPECS` keys without logging the provided key, configured secret, or query string. When API-key auth and DB services are both enabled, decisions are also written to `audit.events` |
| UI API-key cookie bridge | Implemented private-beta browser bridge | When `REQUIRE_API_KEY=true`, `/ui/auth` is public and accepts the same configured API keys as `X-API-Key`. Successful form login sets a signed expiring HttpOnly SameSite cookie scoped to `/ui` without storing the submitted API key and may redirect back to a safe `/ui/*` return path; only `/ui/*` routes accept that cookie as an alternative to the header. Cookie-authenticated UI mutation forms require a signed CSRF token derived from the HttpOnly UI cookie, and logout uses a CSRF-protected POST. The token is signed with `UI_AUTH_COOKIE_SECRET`; non-local API-key-locked app environments fail fast when that setting is blank, while local/dev/development/test environments may use a per-process generated fallback. Non-local `APP_ENV` values set the cookie `Secure` flag automatically. JSON/API routes such as `/areas` still require `X-API-Key` |
| Reviewer service account | Implemented local scoped substrate | `LocalServiceAccountReviewerAuth` requires `X-Reviewer-Id` plus `X-Reviewer-Token`, supports raw local or `sha256:<64-hex>` configured tokens, requires explicit `REVIEWER_ACCOUNT_SCOPES`, rejects the fixture account and raw token specs outside local/dev/development/test `APP_ENV` values, and fails closed when unconfigured |
| UI reviewer session bridge | Implemented private-beta browser bridge | `/ui/auth/reviewer` and first submitted UI action credentials can set a signed expiring HttpOnly SameSite reviewer cookie scoped to `/ui`. The cookie stores reviewer id, scopes, expiry, and a non-secret HMAC binding to the configured reviewer token spec; raw reviewer tokens are not stored, reviewer-token rotation invalidates existing reviewer sessions, per-action scopes are still enforced, and JSON/API routes still require `X-Reviewer-Id` plus `X-Reviewer-Token` headers |
| Operator routes | Reviewer-authenticated and scoped | Connector invocation/scheduling requires `connector:run`, connector review decisions require `connector:review`, queue/live-job health reads require `operations:read`, report retry requires `report:retry`, and manual approved-connector report creation requires `report:run` |
| Public health routes | Intentionally public | `/health` and `/version` remain unauthenticated for local and deployment smoke checks |

## Secret Management Contract

The repo-local `secret_management_contract` is the secret management handoff contract.
It records required secret references and handoff expectations for operators. It is a
validate-only secret handoff: it does
not create hosted infrastructure, write or rotate secret values, read secret
payloads from a hosted provider, or provision a hosted secret manager.

The required runtime references are `API_KEY_SPECS, REVIEWER_ACCOUNTS, REVIEWER_ACCOUNT_SCOPES`,
`UI_AUTH_COOKIE_SECRET, REPORT_IDENTITY_TOKEN_SECRET, and DATABASE_URL`. Non-local
`APP_ENV` values require hashed API/reviewer secrets through `API_KEY_SPECS` and
`REVIEWER_ACCOUNTS`; raw fixture or plaintext secret specs remain local-only.
`UI_AUTH_COOKIE_SECRET` is required when `REQUIRE_API_KEY=true` outside
local/dev/development/test app environments. `REPORT_IDENTITY_TOKEN_SECRET` is
required only when `REPORT_AUTH_MODE=signed_token`.

Secret handoff evidence must identify external secret manager reference names,
the per-environment secret owner, a rotation runbook or ticket, and
post-rotation access-control proof. The hosted secret manager remains blocked until
that authority exists. The catalog ensures no plaintext secret values are committed,
no committed secret values are accepted as proof, no secret writes, and no hosted secret
manager provisioning.
There is no hosted secret manager provisioning.

## Identity/RBAC Contract

The repo-local `identity_rbac_contract` is the identity and RBAC design handoff
contract. It records the claims, roles, route scopes, audit requirements, and
migration expectations that future identity work must preserve before production
RBAC can be claimed. It is a validate-only identity/RBAC design handoff with
no IdP provisioning, no user DB tables, no OAuth/OIDC implementation, and no
production RBAC claim.

The required identity claims are subject, email, display_name, workspace_id, user_id,
and groups_or_roles. In operator terms, `groups_or_roles` means groups/roles supplied
by the future identity provider.
Canonical claim list: subject, email, display_name, workspace_id, user_id, and groups_or_roles.
Required role mappings are platform_admin, workspace_admin, reviewer, operator, and read_only.
Route-scope mappings include connector:run, connector:review, operations:read, report:retry, report:run, and report:approve.

Identity audit evidence must support user-bound audit events and include the IdP subject, workspace/user id, session/token id, route-scope decision, and decision outcome.
The current API-key and reviewer service-account controls remain static
private-MVP substrates until the OAuth/OIDC identity provider, full user auth/RBAC,
user-account persistence, and full user role policy blockers are resolved.
The hosted identity provider remains blocked.

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
  public, supports raw and `sha256:<64-hex>` configured secrets in local fixture
  environments, requires hashed `API_KEY_SPECS` for non-local API-key-locked
  environments, and fails closed with 401/403/503 behavior;
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
  constant-time token comparison through raw local or `sha256:<64-hex>` configured
  tokens, rejects fixture reviewer defaults and raw token specs in non-local
  environments, and fails closed with 401/403/503 behavior;
- UI reviewer sessions do not expose submitted reviewer tokens, are invalidated by
  token rotation or scope removal, remain scoped to `/ui`, and do not authenticate
  JSON/API reviewer-protected routes;
- reviewer accounts require explicit route scopes through `REVIEWER_ACCOUNT_SCOPES`;
- `identity_rbac_contract` records the validate-only identity/RBAC design handoff,
  required identity claims, required role mappings, route-scope mappings, user-bound
  audit requirements, migration expectations, blocked identity/RBAC statuses, and
  explicit limits against IdP provisioning, user DB tables, OAuth/OIDC implementation,
  or a production RBAC claim;
- operator route modules depend on `ReviewerPrincipal` and enforce the route's scope;
- current tests cover API-key and reviewer-auth failure paths;
- CI includes the `access-control` validate-only job.

## Operator Workflow

1. For local fixture mode, leave `REQUIRE_API_KEY=false` unless testing production
   request gating.
2. For deployment smoke or any shared environment, set `REQUIRE_API_KEY=true` and provide
   `API_KEY_SPECS` through the environment, never through committed files. Non-local
   `APP_ENV` values reject `API_KEYS` and raw `API_KEY_SPECS` secrets.
3. For planned static key rotation, use `API_KEY_SPECS` instead of bare `API_KEYS`:
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
   any shared or production-like reviewer/operator workflow. Non-local `APP_ENV` values
   reject the fixture reviewer defaults and raw reviewer token specs; every account must
   use `id:sha256:<64-hex>` and have explicit scopes.
6. Browser operators can use `/ui/auth/reviewer` to start a reviewer session once,
   or submit reviewer credentials on a UI action to set the same session. API clients
   must still use `X-Reviewer-Id` and `X-Reviewer-Token`.
7. Treat a failed access-control proof as a release blocker until the current controls,
   tests, catalog, and runbook are reconciled.
8. Treat the repo-local identity/RBAC contract as a design handoff only. Do not
   claim full user auth/RBAC until user accounts, identity-provider integration,
   full role policy, automatic key rotation, hosted retention, and audit semantics are designed,
   implemented, and verified.

## Known Limits

- No full user auth/RBAC exists yet.
- No OAuth/OIDC integration or hosted identity provider exists.
- No user-account persistence exists.
- No IdP provisioning, no user DB tables, no OAuth/OIDC implementation, and no production RBAC claim exists through `identity_rbac_contract`.
- No hosted secret manager integration exists.
- API keys are static environment values; raw configured secrets are local-only, and
  non-local API-key-locked environments require `API_KEY_SPECS` with `sha256:<64-hex>`
  secrets.
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
- Reviewer service-account auth is a scoped static-token substrate, not a full production
  identity system; raw reviewer tokens and fixture reviewer defaults are local-only.
- Route-level reviewer scopes exist, but full user-account role policy and hosted
  identity-provider authorization are not modeled.
