# Compare/Diff Workflow Smoke

## Goal

Include the existing report compare and same-area diff surfaces in release-candidate
workflow smoke so operators can verify multiple candidate reports and rerun differences
from the current API/UI paths without claiming arbitrary multi-geography utility,
hosted production readiness, or new report semantics.

## Non-goals

- No new compare algorithm, scoring model, ranking, recommendation, or suitability
  conclusion.
- No new geography, rulepack, source, DS-017 connector, or paid/vendor entitlement work.
- No hosted browser farm, hosted load/SLO proof, production dashboard, alert route, or
  image publication.
- No public API contract change unless current route behavior is repo-confirmed broken.
- No committed runtime artifacts; any smoke evidence stays under ignored
  `local_artifacts/`.

## Current state

- `state/POST_RC_AUTHORITY_SPLIT.md` lists compare/diff workflow smoke as a repo-local
  release-candidate candidate because the API and UI surfaces already exist.
- `state/LEVEL_9_10_GATE_MATRIX.md` preserves the Level 9/10 distinction between
  repo-local compare/diff proof and hosted production or arbitrary-geography readiness.
- `GET /report-runs/compare`, `GET /report-runs/{report_run_id}/diff`, and
  `/ui/compare` have unit/API/UI coverage.
- `docs/runbooks/mvp_operator.md` documents compare and same-area diff behavior for
  selected reports.
- `scripts/ui_runtime_smoke.py` currently checks that the report list exposes the
  compare form, but it does not yet drive an approved-report compare/diff flow.

## Proposed design

Start with an audit of the current compare/diff route contracts, tests, and runtime
smoke script. If the gap is confirmed, extend the narrowest existing smoke path to
create or reuse two release-candidate report runs, follow the compare UI/API surface,
and, when the reports share an area, verify the diff/change-review surface. Keep compare
output tied to report summaries and caveated change review; do not add recommendation
or ranking semantics.

Rejected alternatives:

- A new comparison engine is premature because the existing compare/diff surfaces
  already encode the current product contract.
- Hosted browser/load proof remains blocked until hosted platform and workload
  authority exists.
- Committing smoke artifacts would make machine-specific runtime evidence part of repo
  truth.

## Bottom-up sequence

1. Audit existing compare/diff API, UI, tests, and operator runbook authority.
2. Identify the smallest runtime smoke gap: compare reachability, same-area diff
   reachability, or API/UI semantic parity.
3. Add focused tests before or alongside any smoke-script behavior change.
4. Extend only the existing release-candidate smoke path if the current proof is
   insufficient.
5. Re-run private-MVP, release-readiness, readiness-matrix, and focused compare/UI
   checks.
6. Update state logs without promoting hosted production, arbitrary geography, or
   recommendation semantics.

## Files likely to change

| File | Expected change |
|---|---|
| `scripts/ui_runtime_smoke.py` | Add compare/diff follow-through only if audit confirms the runtime smoke gap. |
| `backend/tests/test_ui_runtime_smoke_script.py` | Cover any smoke-script compare/diff additions. |
| `docs/runbooks/mvp_operator.md` | Clarify operator compare smoke only if current prose is incomplete. |
| `state/PROJECT_STATE.md` | Record active compare/diff smoke scope and validation. |
| `state/WORKLOG.md` | Record completion summary. |
| `state/VALIDATION_LOG.md` | Record validators and smoke evidence. |
| `state/LEVEL_9_10_GATE_MATRIX.md` | Update next-pass routing without promoting hosted readiness. |
| `tasks/task_queue.yaml` | Mark task active/done as appropriate. |

## Tests / verification

```powershell
python .\scripts\private_mvp_readiness_check.py
python .\scripts\release_readiness_check.py
python .\scripts\readiness_matrix_check.py
cd backend; python -m pytest -q .\tests\api\test_report_comparison.py .\tests\api\test_ui_routes.py .\tests\test_ui_runtime_smoke_script.py
git diff --check
git diff --name-only --diff-filter=D
.\scripts\verify.ps1
```

Optional runtime proof, only after a local release-candidate runtime is prepared:

```powershell
python .\scripts\ui_runtime_smoke.py --base-url http://127.0.0.1:<port> --selected-county-case <case-id> --reviewer-id <id> --reviewer-token <token>
```

## Risks and blockers

- Compare can easily be mistaken for ranking or suitability. The smoke must verify
  report summaries and change review only, not recommendations.
- Diff is meaningful only for same-area report reruns. Different-area comparisons
  should keep their existing note instead of inventing false diff semantics.
- Hosted production, DS-017, full IdP/RBAC, secret-manager, billing, alerting, image
  publication, and hosted workload proof remain external-authority blockers.

## Decision log

- 2026-06-18: Selected after `R-016` because local performance rehearsal completed and
  `state/POST_RC_AUTHORITY_SPLIT.md` lists compare/diff workflow smoke as the next
  unblocked repo-local release-candidate candidate.

## Progress log

- 2026-06-18: Plan opened after the representative local performance rehearsal proved
  local load/spatial evidence and fixed the concurrent internal sentinel source race.
