# Raw-Data Inventory UI

## Goal
Add a local operator UI route that shows the current runtime inventory for sources,
areas, evidence, claims, report-run contracts, report jobs, connector review items, and
live connector jobs. The route is read-only and makes empty runtime state visible.

## Non-goals
- Do not seed fixtures, create reports, run connectors, approve review items, or mutate
  runtime state from `GET /ui/raw-data`.
- Do not add source-readiness, source-provenance, evidence-provenance, selected-county
  report-path, release-readiness, guardrail, or observability UI surfaces.
- Do not change DB schema, public JSON API contracts, report semantics, source-rights
  policy, auth/security boundaries, hosted deployment, identity/RBAC, or DS-017 status.

## Current state
- `G1a` account-free local auth posture has merged, but live routing files still point
  at it as active.
- `state/reconciliation-dispositions.md` ranks `G1b` next: reconstruct the raw-data
  inventory route from live `origin/main`, use focused raw-data tests, and keep GET
  behavior read-only with no hidden seeding.
- `state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 authority; this route is a
  local visibility slice and not a Level 10 hosted/source/identity completion claim.
- Live `backend/app/api/ui.py` has a server-rendered home and report-run list but no
  `/ui/raw-data` route or runtime inventory summary.
- Runtime services expose source, area, report-job, connector-review, and
  live-connector reads. Evidence and claim repositories have list-all behavior, but
  `EvidenceService` does not currently expose it and `ApiServices` does not currently
  expose `ClaimService`. Report-run contracts can be read by ID, but there is no public
  recent-list method on `ReportRunService`.

## Proposed design
Expose the existing evidence/claim/report read APIs needed by raw inventory:
`EvidenceService.list_all`, the already-constructed `ClaimService` through
`ApiServices`, and a narrow `list_recent_report_runs` method on the report
service/repositories. Build `/ui/raw-data` from those read APIs plus existing
job/review/live stores, with a home status summary that fails closed per category if a
collector raises.

Rejected alternatives:
- Copying dirty-root `backend/app/api/ui.py` would bring later readiness/provenance
  surfaces into `G1b`.
- Counting report contracts only through recent report jobs would miss direct report
  creation paths and blur report-job state with report-contract state.
- Adding hidden selected-county seeding would violate the reconciliation stop condition
  for raw inventory.

## Bottom-up sequence
1. Add focused raw-data inventory tests, including an intentional red run for the
   missing route and read-only GET behavior.
2. Expose claim/report read APIs needed by the UI.
3. Implement small raw inventory collectors, tables, route, and home summary link.
4. Update routing/state logs to mark `G1a` complete and `G1b` active/completed in this
   branch.
5. Run focused tests, validators, diff/no-delete checks, workspace validation, and full
   verification.

## Files likely to change
| File | Expected change |
|---|---|
| `backend/app/api/dependencies.py` | Expose `claim_service` in `ApiServices`. |
| `backend/app/evidence_ledger/service.py` | Add read-only all-evidence listing. |
| `backend/app/reports/report_repo.py` | Add read-only recent report-run listing. |
| `backend/app/reports/service.py` | Delegate recent report-run listing. |
| `backend/app/api/ui.py` | Add `/ui/raw-data` route, collectors, tables, and home link/summary. |
| `backend/tests/api/test_ui_raw_data_inventory.py` | Focused route/home/read-only regressions. |
| `plans/README.md` | Route active plan to `G1b`. |
| `tasks/task_queue.yaml` | Mark `G1a` done and `G1b` active. |
| `state/PROJECT_STATE.md` | Record current checkpoint. |
| `state/WORKLOG.md` | Record progress and validation. |
| `state/VALIDATION_LOG.md` | Record commands, results, and residual risk. |

## Tests / verification
```powershell
cd backend
py -3.12 -m pytest -q .\tests\api\test_ui_raw_data_inventory.py
ruff check .\app\api\dependencies.py .\app\reports\report_repo.py .\app\reports\service.py .\app\api\ui.py .\tests\api\test_ui_raw_data_inventory.py
py -3.12 -m mypy .\app\api\dependencies.py .\app\reports\report_repo.py .\app\reports\service.py .\app\api\ui.py .\tests\api\test_ui_raw_data_inventory.py
cd ..
py -3.12 .\scripts\release_readiness_check.py
py -3.12 .\scripts\readiness_matrix_check.py
git diff --check
git diff --name-only --diff-filter=D
.\scripts\validate_workspace.ps1
.\scripts\verify.ps1
```

## Risks and blockers
- The UI route must stay read-only even when empty; empty runtime state is a valid
  display state, not a reason to seed fixtures.
- Report-run listing touches both in-memory and DB-backed repositories; keep the method
  read-only and order-bounded.
- The route must not describe raw inventory as source-readiness proof, hosted proof, or
  legal/compliance diligence completion.

## Decision log
- 2026-06-20: Selected `G1b` after live reconciliation confirmed `G1a` merged and the
  disposition matrix ranked raw-data inventory next.
- 2026-06-20: Chose small read APIs for claim/report inventories over deriving them
  from report jobs because report jobs are not the canonical report/claim stores.

## Progress log
- 2026-06-20: Opened from clean `worktrees/raw-inv` on live `origin/main` at
  `6d8b9d66019453e99628e21d595a7a97b149d41c`; no active inbox collision found.
- 2026-06-20: Intentional red focused pytest failed for missing `/ui/raw-data`, missing
  home link/summary, and absent evidence list-all service read. Added the narrow read
  APIs, route, home summary, and focused tests; focused raw-data tests, ruff, and mypy
  now pass.
- 2026-06-20: Full verify initially failed only because the generated OpenAPI stubs did
  not yet include `/ui/raw-data`. Regenerated stubs with `scripts/export_openapi_stub.py`;
  OpenAPI parity tests, workspace validation, diff/no-deletion checks, and final
  `.\scripts\verify.ps1` passed.
