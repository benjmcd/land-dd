# Route-Scope/RBAC Handoff Coverage

## Goal

Prove that the repo-local identity/RBAC handoff catalog names the protected route
surfaces future hosted identity must preserve, without implementing OAuth/OIDC, user
tables, full org/user RBAC, paid-data entitlements, or hosted identity-provider
authorization.

## Non-goals

- No OAuth/OIDC, hosted IdP, user table, org membership, or production RBAC
  implementation.
- No public API contract expansion unless current runtime behavior already exposes the
  surface.
- No DS-017 entitlement model or paid/vendor data access.
- No hosted deployment, secret-manager, billing, alerting, or production workload work.
- No weakening of existing API-key, reviewer-token, UI reviewer-session, UI identity
  session, CSRF, or workspace-scope checks.

## Current state

- `config/access_control.yaml` contains an `identity_rbac_contract` section with
  required claims, role mappings, route-scope mappings, audit requirements, migration
  expectations, and blocked statuses.
- `docs/runbooks/access_control.md` documents that the contract is validate-only and
  not a production RBAC claim.
- `scripts/access_control_check.py` validates current access-control artifacts, but the
  next pass should re-audit whether route-scope mappings are complete enough for future
  hosted identity handoff.
- `state/LEVEL_9_10_GATE_MATRIX.md` keeps `L10-SEC-001`, `L10-SEC-002`,
  `L10-SEC-003`, and `L10-SEC-006` partial until hosted identity, external
  secret-manager, and user-bound audit authority exist.
- This plan preserves the Level 9/10 authority context: repo-local controls can be
  proven here, while hosted identity/RBAC remains external authority.

## Proposed design

Use a validate-only handoff coverage pass:

1. Identify canonical protected API/UI route surfaces from current route modules and
   access-control tests.
2. Compare those surfaces to the `identity_rbac_contract.route_scope_mappings` catalog.
3. Add the smallest static validator/test hardening needed so missing route-scope
   mappings fail closed.
4. Preserve all existing local/private-MVP auth mechanisms and external blockers.

Rejected alternatives:

- Implementing hosted identity/RBAC would require external IdP/user/account authority.
- Inferring production RBAC from reviewer tokens would overclaim current local controls.
- Broad route refactors would increase risk without improving the handoff contract.

## Bottom-up sequence

1. Audit `config/access_control.yaml`, `scripts/access_control_check.py`, access-control
   runbook text, and current protected route tests.
2. Build the route-scope evidence map from current code/tests; keep it static and
   validate-only unless a runtime gap is proven.
3. Add focused artifact tests for fail-closed route-scope mapping coverage.
4. Run access-control, release-readiness, readiness-matrix, focused pytest, ruff, mypy,
   and full verification.
5. Update state logs without claiming hosted identity or production RBAC.

## Files likely to change

| File | Expected change |
|---|---|
| `config/access_control.yaml` | Add or clarify route-scope handoff mappings only if audit finds gaps. |
| `scripts/access_control_check.py` | Add static coverage checks for route-scope mappings if needed. |
| `docs/runbooks/access_control.md` | Clarify handoff limits and route-scope evidence only if needed. |
| `backend/tests/*` | Add focused artifact tests for any validator changes. |
| `state/PROJECT_STATE.md` | Record active route-scope/RBAC handoff scope and validation. |
| `state/WORKLOG.md` | Record completion summary. |
| `state/VALIDATION_LOG.md` | Record validators and residual risk. |
| `tasks/task_queue.yaml` | Mark task active/done as appropriate. |

## Tests / verification

```powershell
python .\scripts\access_control_check.py
.\scripts\run_access_control_check.ps1
python .\scripts\release_readiness_check.py
python .\scripts\readiness_matrix_check.py
cd backend; python -m pytest -q .\tests\test_access_control_artifacts.py .\tests\api\test_api_key_auth.py .\tests\api\test_reviewer_auth.py .\tests\api\test_report_auth.py .\tests\api\test_ui_routes.py .\tests\api\test_ui_review_routes.py
git diff --check
git diff --name-only --diff-filter=D
.\scripts\verify.ps1
```

Narrow checks may be refined after the route-scope audit identifies the actual affected
files.

## Risks and blockers

- Route-scope coverage can prove handoff completeness, but it cannot prove hosted
  identity-provider behavior.
- Mapping route scopes too broadly can hide privilege-boundary gaps; mapping too
  narrowly can create brittle false positives.
- Existing reviewer-token and signed UI identity-token bridges remain private-MVP
  controls, not production RBAC.

## Decision log

- 2026-06-18: Selected after `R-019` because checklist dry-run proof closes the
  expansion checklist executability gap, and the next repo-local candidate that best
  advances the overarching objective is authenticated operator/reviewer route-scope
  handoff coverage without starting hosted IdP/RBAC.

## Progress log

- 2026-06-18: Plan opened as the next active repo-local lane after R-019.
