# County RC Proof

## Goal
Refresh selected-county private-MVP release-candidate proof across the existing
Buncombe, Chatham, and Brunswick packaged operator cases, with emphasis on isolated
DB-backed persistence and UI/browser smoke evidence. This advances the Level 9/10
product-correctness and release-candidate evidence path without claiming hosted
production readiness.

## Non-goals
- No DS-017 vendor/license/cost decision.
- No hosted deployment, public HTTPS endpoint, TLS, billing, dashboard, pager, or SLO
  claim.
- No new county, state, source, jurisdiction, or rulepack.
- No live-source expansion beyond already approved connector surfaces.
- No full user identity, OAuth/OIDC, org RBAC, or production entitlement model.
- No committed generated report, browser screenshot, load-test, or DB dump artifact.

## Current state
- This is a Level 9/10 follow-on pass selected from
  `state/LEVEL_9_10_GATE_MATRIX.md`, not a hosted production claim.
- Must source readiness remains `sources=8 ready=7 blocked=1`; DS-017 remains blocked.
- Private-MVP readiness, release-readiness, hosted-deployment, access-control, and
  readiness-matrix validators pass as repo-local/validate-only proof.
- Existing selected-county proof surfaces include `config/private_mvp_beta_readiness.yaml`,
  `scripts/run_private_mvp_readiness_check.ps1`, `scripts/run_mvp_regression.ps1`,
  `scripts/run_ui_browser_smoke.ps1`, `scripts/ui_runtime_smoke.py`,
  `backend/tests/api/test_operator_cases_api.py`,
  `backend/tests/api/test_operator_cases_db.py`, and
  `backend/tests/test_ui_browser_smoke_scripts.py`.
- `R-007` strengthened local load proof by making `POST /areas` and `POST /report-runs`
  use valid workflow traffic, but it does not prove packaged selected-county corpus
  delivery, DB persistence, or browser operator usability.

## Proposed design
Start with an audit of the existing release-candidate proof ladder, then close the
narrowest gap that prevents an operator from reproducing selected-county proof without
overclaiming hosted production. Prefer extending an existing script/test/checker over
adding another proof surface.

Candidate first slice:
1. Re-run private-MVP readiness and source-readiness validators from current `main`.
2. Identify the exact selected-county DB-backed and UI/browser proof commands that are
   already executable.
3. If a command exists but is under-documented or not statically pinned, harden the
   runbook/checker/test to make it discoverable.
4. If a proof is missing, add the smallest fixture-backed test or wrapper that exercises
   an existing operator-case path.

Alternatives rejected:
- DS-017 work: blocked by product/vendor/license/cost authority.
- Hosted smoke execution: blocked by hosted platform and secret authority.
- Broad UI redesign: premature; the question is proof coverage, not presentation.

## Bottom-up sequence
1. Audit `config/private_mvp_beta_readiness.yaml`, MVP runbooks, operator-case API/DB
   tests, and UI/browser smoke scripts for the exact proof ladder.
2. Choose one missing or weak proof link.
3. Add or update tests/checkers/runbooks before changing any runtime behavior.
4. Run the narrowest focused tests plus private-MVP/release/readiness validators.
5. Run `.\scripts\verify.ps1` before handoff.

## Files likely to change
| File | Expected change |
|---|---|
| `config/private_mvp_beta_readiness.yaml` | Only if proof catalog wording or commands need tightening. |
| `scripts/private_mvp_readiness_check.py` | Only if catalog validation misses a real proof gap. |
| `scripts/ui_runtime_smoke.py` | Possible selected-county UI launcher proof hardening. |
| `scripts/ui_browser_smoke.mjs` | Possible browser-route coverage hardening, not broad UI testing. |
| `backend/tests/api/test_operator_cases_db.py` | Possible DB-backed selected-county proof expansion. |
| `backend/tests/test_private_mvp_readiness.py` | Static guard coverage for proof catalog/runbook wording. |
| `docs/runbooks/mvp_operator.md` | Clarify exact release-candidate proof ladder if needed. |
| `state/PROJECT_STATE.md` | Record current active proof target and boundaries. |
| `state/WORKLOG.md` | Record the completed slice. |
| `state/VALIDATION_LOG.md` | Record exact validation commands and outcomes. |

## Tests / verification
```powershell
python .\scripts\source_readiness.py --priority Must --json
python .\scripts\private_mvp_readiness_check.py
.\scripts\run_private_mvp_readiness_check.ps1
cd backend; python -m pytest -q .\tests\test_private_mvp_readiness.py .\tests\api\test_operator_cases_api.py
python .\scripts\release_readiness_check.py
python .\scripts\readiness_matrix_check.py
git diff --check
git diff --name-only --diff-filter=D
.\scripts\verify.ps1
```

Add DB-enabled or browser smoke commands only after confirming local prerequisites and
isolating generated evidence under ignored `local_artifacts`.

## Risks and blockers
- DS-017 remains the Must-source blocker for full source readiness.
- Browser smoke depends on local Chrome availability and should remain explicit, not a
  default verification gate.
- DB-enabled proof depends on local Postgres/PostGIS availability and should stay
  isolated from default validate-only commands unless deliberately enabled.
- Hosted deployment, hosted identity, billing, and alert routing remain external
  authority blockers.

## Decision log
- 2026-06-18: Selected this as the next active pass after `R-007` because read-only
  audits identified selected-county release-candidate proof refresh as the best
  remaining unblocked movement toward the overarching objective.

## Progress log
- 2026-06-18: Plan opened after workflow-valid local load proof completed; no
  implementation work has started under this plan yet.
