# Security Guardrails UI G6a

## Goal

Add the narrow `G6a` local security/access-control guardrail surface as the first
post-G5 guardrail slice. The pass should expose existing repo-owned access-control and
security posture evidence through a read-only local operator view without changing
auth semantics or claiming hosted identity/RBAC.

## Non-goals

- No OAuth/OIDC, user accounts, org/user RBAC, tenant provisioning, entitlement model,
  secret-manager integration, automatic key rotation, hosted identity provider, hosted
  log retention, or SIEM integration.
- No public JSON API contract change, DB schema change, source registry change,
  connector execution, fixture seeding, report creation, claim/rule behavior change, or
  report-semantics change.
- No DS-017 approval, source/vendor expansion, generic AOI proof, Bologna pilot,
  hosted deployment, hosted source authority, hosted observability, or Level 10
  completion claim.

## Current state

- PR #96 merged the G5 source-provenance UI on `origin/main` at
  `e27dc88e470d8fa861af8194bf330d98e9f164c1`.
- `state/reconciliation-dispositions.md` retains `backend/app/security_guardrails.py`
  and `backend/tests/api/test_ui_security_guardrails.py` as an isolated `G6` slice, while
  keeping production-authority and product-correctness aggregation deferred.
- `config/access_control.yaml`, `scripts/access_control_check.py`, and
  `docs/runbooks/access_control.md` are the current repo-local authority surfaces for
  local API-key/reviewer posture and hosted identity/RBAC blockers.
- `state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 authority. This plan may
  make partial security posture easier to inspect, but it must not promote hosted
  identity, tenant safety, DS-017 entitlement, or production security gates.

## Proposed design

Reconstruct the retained security guardrail work from live `origin/main`, not by copying
the dirty-root aggregate UI stack. Start with route/helper tests that prove the page is
read-only, fails closed on drift, links from the accepted local operator home, and keeps
hosted identity/RBAC blockers explicit. Then implement the smallest parser/view over
existing access-control artifacts.

Rejected alternatives:

- Land all G6 guardrails in one PR: operations, performance, and security have different
  authority surfaces and validation risks.
- Reintroduce production-authority UI now: external platform, identity, alerting, and
  source/vendor authorities remain blocked.
- Mutate `config/access_control.yaml` to make the page easier to render: the UI should
  follow existing authority, not reshape it prematurely.

## Bottom-up sequence

1. Add failing focused tests for the security guardrails helper and GET-only UI route.
2. Implement the read-only helper over existing access-control/security artifacts.
3. Add the local route and navigation without changing default auth mounting behavior.
4. Regenerate OpenAPI stubs if the route set changes.
5. Run access-control, release-readiness, readiness-matrix, workspace, and full verify
   gates before updating state to completed.

## Files likely to change

| File | Expected change |
|---|---|
| `backend/tests/api/test_ui_security_guardrails.py` | New focused parser, fail-closed, route, and navigation tests. |
| `backend/app/security_guardrails.py` | Read-only parser/model over existing security/access-control artifacts. |
| `backend/app/api/ui.py` | Add GET-only local security guardrails route and nav link. |
| `api/openapi_stub.yaml` | Regenerated FastAPI contract stub if a route is added. |
| `docs/planning_pack/api/openapi_stub.yaml` | Regenerated planning-pack mirror if a route is added. |
| `MANIFEST.md` | Route to the new source-of-truth file only after implementation exists. |
| `plans/README.md` | Active-plan pointer. |
| `tasks/task_queue.yaml` | Active-plan routing and validation commands. |
| `state/PROJECT_STATE.md` | Current checkpoint and boundaries. |
| `state/WORKLOG.md` | Work summary. |
| `state/VALIDATION_LOG.md` | Commands, results, residual risk. |

## Tests / verification

```powershell
cd backend
py -3.12 -m pytest -q .\tests\api\test_ui_security_guardrails.py .\tests\test_access_control_artifacts.py
ruff check .\app\security_guardrails.py .\app\api\ui.py .\tests\api\test_ui_security_guardrails.py ..\scripts\access_control_check.py
py -3.12 -m mypy .\app\security_guardrails.py .\app\api\ui.py .\tests\api\test_ui_security_guardrails.py ..\scripts\access_control_check.py
cd ..
py -3.12 .\scripts\access_control_check.py
py -3.12 .\scripts\release_readiness_check.py
py -3.12 .\scripts\readiness_matrix_check.py
git diff --check
git diff --name-only --diff-filter=D
.\scripts\validate_workspace.ps1
.\scripts\verify.ps1
```

If the route set changes:

```powershell
py -3.12 .\scripts\export_openapi_stub.py
cd backend
py -3.12 -m pytest -q .\tests\api\test_openapi_contract.py::test_openapi_stub_path_methods_match_runtime_schema .\tests\test_planning_pack_schema_copies.py::test_planning_pack_openapi_stub_matches_generated_fastapi_contract
```

## Risks and blockers

- A local security page can easily overclaim if it reads like hosted identity/RBAC proof.
  The route copy and tests must keep local service-account/API-key proof separate from
  external IdP, tenant, entitlement, hosted logging, and rotation blockers.
- G6a must not relax default local no-auth behavior or protected-route mounting rules
  established by G1a/G2.
- DS-017 remains blocked until a product/source entitlement decision changes the
  registry and readiness evidence.

## Decision log

- 2026-06-20: Selected G6a as the next post-G5 slice because PR #96 is merged, the
  remaining reconciliation sequence calls for local guardrail/auth-hardening surfaces
  before G8 observability, and security/access-control is the highest-leverage guardrail
  boundary before hosted identity/RBAC work.

## Progress log

- 2026-06-20: Corrected post-G5 routing from the merged G5 source-provenance UI to this
  G6a plan after confirming live `origin/main` at
  `e27dc88e470d8fa861af8194bf330d98e9f164c1`.
- 2026-06-20: Added failing focused tests for the missing `app.security_guardrails`
  helper and `/ui/security-guardrails` route, then implemented the read-only parser,
  page, navigation, OpenAPI refresh, and manifest/state routing. Focused G6a tests
  passed (`7 passed`), focused security/access-control tests passed (`20 passed`),
  OpenAPI parity passed (`2 passed`), focused ruff/mypy passed, access-control,
  release-readiness, readiness-matrix, Must-source readiness, diff/no-deletion,
  workspace validation, and full `.\scripts\verify.ps1` passed. DB smoke was skipped
  by default.
