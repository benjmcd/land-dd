# Post-RC Authority Split

## Goal
Turn the completed selected-county release-candidate proof ladder into a concrete
next-lane decision package: identify which remaining Level 9/10 gaps are repo-local
implementation work, which require external authority, and which should stay blocked
until hosted platform, source, identity, billing, or alerting decisions exist.

## Non-goals
- No hosted infrastructure, DNS, TLS, registry publication, billing, or alert setup.
- No DS-017 vendor/license/cost decision.
- No OAuth/OIDC, full org RBAC, entitlement model, or production identity provider.
- No new county, source, connector, rulepack, schema, report semantics, or API contract.
- No committed generated report, DB dump, browser screenshot, or runtime evidence file.

## Current state
- `R-008` refreshed selected-county release-candidate proof for browser/runtime smoke,
  reviewer-session CSRF, all nine packaged DB operator cases, and DB artifact
  persistence.
- `R-009` made the selected-county UI runtime smoke follow the approved report lineage
  route and require source, evidence, and claim lineage content.
- The Level 9/10 matrix still keeps hosted deployment, DS-017, external secret manager,
  IdP/RBAC, billing, hosted alerting, and production workload proof outside current
  repo-local authority.
- The handoff artifact at `C:/Users/benny/Downloads/land_dd_handoff.md` is an
  exhaustive read-only audit prompt, not implementation authority by itself.

## Proposed design
Use a read-only authority split before starting another implementation slice. Update the
matrix and state only where current proof changed, then produce a ranked lane decision:
external-authority blockers, repo-local implementation candidates, and evidence-only
audit candidates. Do not promote hosted or source-readiness gates from local proof.

## Bottom-up sequence
1. Reconcile `state/LEVEL_9_10_GATE_MATRIX.md` after `R-008`/`R-009`.
2. Check release, hosted, access-control, source-readiness, and private-MVP validators.
3. Classify remaining gaps into external-authority, repo-local, and audit-only lanes.
4. Select the next implementation plan only if a repo-local lane is lower-risk than
   getting external decisions first.

## Files likely to change
| File | Expected change |
|---|---|
| `state/LEVEL_9_10_GATE_MATRIX.md` | Update changed lineage evidence and next-lane text. |
| `state/PROJECT_STATE.md` | Record the post-RC authority-split checkpoint. |
| `tasks/task_queue.yaml` | Route to the authority-split task. |
| `plans/README.md` | Point at this active plan. |
| `state/WORKLOG.md` | Record the selected next lane. |
| `state/VALIDATION_LOG.md` | Record validators used for the split. |

## Tests / verification
```powershell
python .\scripts\private_mvp_readiness_check.py
python .\scripts\source_readiness.py --priority Must --json
python .\scripts\release_readiness_check.py
python .\scripts\hosted_deployment_check.py
python .\scripts\access_control_check.py
python .\scripts\readiness_matrix_check.py
git diff --check
git diff --name-only --diff-filter=D
```

Run `.\scripts\verify.ps1` before handoff if any executable contract changes.

## Risks and blockers
- Treating local selected-county proof as hosted or multi-user production proof would
  overclaim.
- DS-017 remains blocked until vendor/license/cost and product field-policy authority is
  explicit.
- Hosted deployment, secret-manager, billing, alert-routing, and IdP decisions cannot be
  inferred from repo files.

## Decision log
- 2026-06-18: Selected authority split as the next active plan after `R-009` because the
  lowest-risk repo-local proof gaps were hardened and the remaining major Level 10
  blockers require external decisions before implementation.

## Progress log
- 2026-06-18: Plan opened after selected-county lineage smoke proof completed.
