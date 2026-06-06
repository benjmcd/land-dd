# Access Control Runbook

## Purpose

Use `config/access_control.yaml` as the repo-local Level 10 access-control posture
catalog. It records the current API-key middleware, local scoped reviewer
service-account boundary, reviewer-authenticated and scoped operator routes,
intentionally public health/version routes, and local-only auth non-goals.

Full user auth/RBAC, OAuth/OIDC, user-account persistence, automatic key rotation,
external secret manager integration, and hosted identity-provider integration are
out of scope for local-only production-grade. No full user auth/RBAC is planned unless
the local-only scope changes.

## Current Controls

| Control | Status | Evidence |
|---|---|---|
| API-key middleware | Implemented, default off | `ApiKeyAuthMiddleware` protects non-public paths when `REQUIRE_API_KEY=true`, uses `X-API-Key`, supports raw or `sha256:<64-hex>` configured secrets, fails closed when required but unconfigured, and leaves `/health` and `/version` public |
| API-key static lifecycle | Implemented configured rotation substrate | `API_KEY_SPECS` accepts comma-separated `id|status|secret` entries, where `status` is `active` or `retired`; active specs authenticate, retired specs do not, and malformed, duplicate-id, or duplicate-secret specs fail closed |
| API-key audit logging | Implemented structured runtime logs plus DB events | Protected-path API-key decisions emit `event_type=api_key_auth`, outcome, status code, method, path, auth source, and configured `api_key_id` for accepted `API_KEY_SPECS` keys without logging the provided key, configured secret, or query string. When API-key auth and DB services are both enabled, decisions are also written to `audit.events` |
| Reviewer service account | Implemented local scoped substrate | `LocalServiceAccountReviewerAuth` requires `X-Reviewer-Id` plus `X-Reviewer-Token`, supports raw or `sha256:<64-hex>` configured tokens, requires explicit `REVIEWER_ACCOUNT_SCOPES`, and fails closed when unconfigured |
| Operator routes | Reviewer-authenticated and scoped | Connector invocation/scheduling requires `connector:run`, connector review decisions require `connector:review`, queue/live-job health reads require `operations:read`, report retry requires `report:retry`, and manual approved-connector report creation requires `report:run` |
| Public health routes | Intentionally public | `/health` and `/version` remain unauthenticated for local and deployment smoke checks |

## Validate Access Control

Run from the repository root:

```powershell
.\scripts\run_access_control_check.ps1
```

The check is validate-only. It verifies that:

- the access-control catalog names current controls and local-only non-goals;
- referenced authority files exist;
- API-key middleware still uses `X-API-Key`, keeps only `/health` and `/version`
  public, supports raw and `sha256:<64-hex>` configured secrets, and fails closed with
  401/403/503 behavior;
- `API_KEY_SPECS` supports configured active/retired key lifecycle specs, authenticates
  only active specs, and fails closed for malformed lifecycle entries;
- API-key auth emits structured runtime audit logs and, in DB-service mode, durable
  `audit.events` rows for accepted, missing, invalid, and unconfigured decisions
  without logging or persisting secret material;
- reviewer auth still requires `X-Reviewer-Id` and `X-Reviewer-Token`, uses
  constant-time token comparison through raw or `sha256:<64-hex>` configured tokens, and
  fails closed with 401/403/503 behavior;
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
4. Override the fixture `REVIEWER_ACCOUNTS` and `REVIEWER_ACCOUNT_SCOPES` values before
   any shared or production-like reviewer/operator workflow. Every account must have
   explicit scopes. Prefer `id:sha256:<64-hex>` reviewer token specs outside local fixture
   mode.
5. Treat a failed access-control proof as a release blocker until the current controls,
   tests, catalog, and runbook are reconciled.
6. Do not plan or claim full user auth/RBAC, OAuth/OIDC, user accounts, automatic key
   rotation, external secret manager integration, hosted identity, or hosted retention
   for the local-only product. Treat those as optional future-hosting work only after an
   explicit scope change.

## Known Limits

- No full user auth/RBAC is planned for local-only operation.
- No OAuth/OIDC integration or hosted identity provider is planned for local-only
  operation.
- No user-account persistence is planned for local-only operation.
- API keys are static environment values; raw and `sha256:<64-hex>` configured secrets
  are supported.
- A configured static key lifecycle exists through `API_KEY_SPECS`, but no automatic
  key-rotation scheduler, external secret manager integration, revocation propagation,
  or hosted key-management workflow is planned for local-only operation.
- API-key auth writes runtime logs, and DB-service mode writes `audit.events`, but there is
  no hosted log-retention/export/SIEM integration, no user-account binding, and no
  durable per-key usage audit ledger for legacy `API_KEYS` entries without configured IDs.
- Reviewer service-account auth is a local scoped substrate, not a full production
  identity system.
- Route-level reviewer scopes exist, but full user-account role policy and hosted
  identity-provider authorization are not modeled.
