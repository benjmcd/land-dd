# Deployment Readiness UI G3

## Goal

Add a read-only `/ui/deployment-readiness` operator view over the existing
release-package, image-publication, and hosted-deployment catalogs. The page should
make local package/image/hosted deployment blockers visible without building,
publishing, pushing, signing, deploying, writing secrets, opening public endpoints,
approving DS-017, or claiming Level 10 production authority.

## Non-goals

- No package build, generated package artifact, registry push, image signing,
  attestation publication, hosted deployment, hosted infrastructure mutation, secret
  write, public endpoint creation, hosted billing, hosted alerting, or DS-017 approval.
- No source/vendor expansion, selected-geography coverage page, expansion page,
  production-authority page, broad readiness overview, source-provenance page, guardrail
  page, or observability page.
- No schema, DB migration, connector runtime, report semantics, public JSON API
  behavior, OAuth/OIDC, user accounts, or full identity/RBAC change.

## Current state

- `state/reconciliation-dispositions.md` retains `backend/app/deployment_readiness.py`
  and `backend/tests/api/test_ui_deployment_readiness.py` as a focused G3/G7 slice.
- `config/release_package.yaml`, `config/image_publication.yaml`, and
  `config/hosted_deployment.yaml` are the canonical deployment-path catalogs.
- Existing validators prove those catalogs are validate-only and keep registry,
  hosted, attestation, secret, and endpoint blockers explicit.
- `state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 authority; this plan cites it
  and does not promote any hosted or production gate.
- G2 runtime/browser smoke has just landed around accepted G1 UI routes. This slice
  should not broaden default smoke beyond the already accepted route set.

## Proposed design

Add a packaged helper in `backend/app/deployment_readiness.py` that reads the three
deployment-path catalogs, validates request-critical invariants, and returns typed
readiness data to the UI. Render one GET-only `/ui/deployment-readiness` route from the
existing UI router and link it from the currently live operator pages: home and raw-data.

Rejected alternatives:

- Import CLI validators inside a web request: those scripts are command-oriented and
  subprocess-aware; a small packaged helper gives the UI a safer request-time contract.
- Render unchecked YAML: that would expose drift as apparent truth instead of failing
  closed.
- Copy the broader dirty-root route set: current live authority only supports home and
  raw-data navigation for this slice; readiness overview, coverage, expansion,
  release-readiness UI, production authority, and smoke expansion stay deferred.

## Bottom-up sequence

1. Add failing parser and route tests for the deployment-readiness helper and UI route.
2. Implement the read-only helper over existing catalog files.
3. Add `/ui/deployment-readiness` and live-page navigation only where current routes
   already exist.
4. Regenerate OpenAPI stubs for the new FastAPI UI route.
5. Update routing/state/worklog/validation records after verification.

## Files likely to change

| File | Expected change |
|---|---|
| `backend/tests/api/test_ui_deployment_readiness.py` | Parser, fail-closed, route, and navigation tests. |
| `backend/app/deployment_readiness.py` | Read-only parser/model for package/image/hosted deployment catalogs. |
| `backend/app/api/ui.py` | Add GET-only deployment-readiness route and current-page nav links. |
| `api/openapi_stub.yaml` | Regenerated FastAPI contract stub. |
| `docs/planning_pack/api/openapi_stub.yaml` | Regenerated planning-pack mirror. |
| `plans/README.md` | Active-plan pointer. |
| `tasks/task_queue.yaml` | Active-plan routing. |
| `state/PROJECT_STATE.md` | Current checkpoint and boundaries. |
| `state/WORKLOG.md` | Work summary. |
| `state/VALIDATION_LOG.md` | Commands, results, residual risk. |

## Tests / verification

```powershell
cd backend
py -3.12 -m pytest -q .\tests\api\test_ui_deployment_readiness.py
py -3.12 -m ruff check .\app\deployment_readiness.py .\app\api\ui.py .\tests\api\test_ui_deployment_readiness.py
py -3.12 -m mypy .\app\deployment_readiness.py .\app\api\ui.py .\tests\api\test_ui_deployment_readiness.py
cd ..
py -3.12 .\scripts\export_openapi_stub.py
cd backend
py -3.12 -m pytest -q .\tests\api\test_openapi_contract.py::test_openapi_stub_path_methods_match_runtime_schema .\tests\test_planning_pack_schema_copies.py::test_planning_pack_openapi_stub_matches_generated_fastapi_contract
cd ..
py -3.12 .\scripts\release_package_check.py
py -3.12 .\scripts\image_publication_check.py
py -3.12 .\scripts\hosted_deployment_check.py
py -3.12 .\scripts\release_readiness_check.py
py -3.12 .\scripts\readiness_matrix_check.py
git diff --check
git diff --name-only --diff-filter=D
.\scripts\validate_workspace.ps1
.\scripts\verify.ps1
```

## Risks and blockers

- The page can overclaim if it presents blockers as readiness. Tests and copy must keep
  hosted, registry, attestation, secrets, DS-017, and identity/RBAC blockers explicit.
- The parser overlaps existing CLI validators. It should pin request-critical UI
  invariants only, while the full validators remain the deeper release authority.
- Adding a FastAPI UI route requires OpenAPI stub regeneration even though this does not
  change the JSON API behavior.

## Decision log

- 2026-06-20: Selected the narrow deployment-readiness page as the next G3 retained
  slice after G2 merge because package, image, and hosted catalog authority already
  exists and can be exposed without starting blocked production work.

## Progress log

- 2026-06-20: Live main, worktrees, PRs, inboxes, reconciliation dispositions, catalog
  validators, UI route patterns, and dirty-root candidate evidence audited. The candidate
  plan was narrowed to avoid non-live readiness/coverage/expansion/release pages and
  default smoke expansion.
- 2026-06-20: Implemented `app.deployment_readiness`, `/ui/deployment-readiness`,
  current-page navigation, OpenAPI refresh, and docs/state routing. Focused
  deployment-readiness tests passed (`9 passed`), OpenAPI parity passed (`2 passed`),
  focused ruff/mypy passed, release-package/image-publication/hosted-deployment,
  release-readiness/readiness-matrix/private-MVP/access-control validators passed,
  diff/no-deletion/workspace checks passed, and full `.\scripts\verify.ps1` passed with
  backend tests, ruff, and mypy over `330` source files. DB smoke was skipped by default.
