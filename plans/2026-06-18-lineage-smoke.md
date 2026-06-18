# Lineage Smoke

## Goal
Add selected-county release-candidate smoke proof that the approved operator-case report
lineage surface is reachable and evidence-linked after the existing UI runtime smoke
creates a packaged selected-county report.

## Non-goals
- No DS-017 vendor/license/cost decision.
- No hosted deployment, public endpoint, SLO, dashboard, pager, or alerting claim.
- No new geography, source, rulepack, connector, schema, or API contract.
- No full user identity, OAuth/OIDC, org RBAC, or production entitlement model.
- No committed generated report, lineage JSON, browser screenshot, or DB dump artifact.

## Current state
- `R-008` hardened selected-county release-candidate proof:
  - Chrome browser smoke now asserts the selected-county launcher/form contract on `/ui/`.
  - UI runtime smoke now uses reviewer-session CSRF correctly.
  - DB-gated operator-case proof now covers all nine packaged selected-county cases.
  - DB-backed runtime smoke proved `postgres+object_store` artifact persistence for
    the selected-county UI path on an isolated local PostGIS runtime.
- The current UI runtime smoke checks that the approved report page contains
  "View evidence lineage", but it does not follow the link or validate lineage payload
  contents.
- `state/LEVEL_9_10_GATE_MATRIX.md` keeps lineage as repo-local proof that should be
  included in Level 9/10 release-candidate smoke evidence.

## Proposed design
Extend the existing opt-in `scripts/ui_runtime_smoke.py` operator-case path rather than
adding a new smoke surface. After the report page passes, derive or parse the lineage
route for the final report, fetch it, and require evidence/claim/source lineage content
that already exists in the current UI/API contract.

The first pass should prefer UI lineage page proof. If the page is too presentation
oriented for stable assertions, use the linked API lineage JSON as the stable contract
and keep the UI assertion to "lineage link exists".

## Bottom-up sequence
1. Audit current lineage API/UI routes and tests for the stable contract.
2. Add a narrow failing unit test around `ui_runtime_smoke.py` lineage follow-through.
3. Implement lineage fetch/assertion in the existing operator-case smoke path.
4. Update the MVP operator runbook and private-MVP readiness guards if commands or
   guarantees change.
5. Run focused runtime-smoke tests, private-MVP readiness, release/readiness validators,
   browser/runtime live smoke, and `.\scripts\verify.ps1`.

## Files likely to change
| File | Expected change |
|---|---|
| `scripts/ui_runtime_smoke.py` | Follow the selected-county report lineage route after opt-in report creation. |
| `backend/tests/test_ui_runtime_smoke_script.py` | Unit coverage for lineage fetch success and fail-closed behavior. |
| `backend/tests/test_private_mvp_readiness.py` | Static guard only if runbook/catalog language changes. |
| `docs/runbooks/mvp_operator.md` | Clarify that runtime smoke proves lineage reachability/content. |
| `state/PROJECT_STATE.md` | Record active target and boundaries. |
| `state/WORKLOG.md` | Record completed slice. |
| `state/VALIDATION_LOG.md` | Record exact checks and results. |

## Tests / verification
```powershell
python .\scripts\private_mvp_readiness_check.py
cd backend; python -m pytest -q .\tests\test_ui_runtime_smoke_script.py .\tests\api\test_ui_routes.py .\tests\api\test_report_lineage.py
python .\scripts\release_readiness_check.py
python .\scripts\readiness_matrix_check.py
git diff --check
git diff --name-only --diff-filter=D
.\scripts\verify.ps1
```

Add live browser/runtime smoke only after starting a local candidate runtime; keep any
generated evidence under ignored `local_artifacts/`.

## Risks and blockers
- Lineage assertions must not become brittle presentation checks if a stable API contract
  already exists.
- DB-backed lineage proof should remain opt-in and isolated from default validate-only
  commands.
- Hosted lineage proof remains future work until hosted deployment and object storage
  authority exist.

## Progress log
- 2026-06-18: Plan opened after `R-008` selected-county release-candidate proof refresh
  completed. No implementation work has started under this plan yet.
