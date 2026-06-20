# Supported AOI UI Runtime Proof

## Goal

Prove the newly landed supported-AOI `area_id` route through the browser/operator
workflow: an operator can submit an existing stored AOI from the UI, create the same
reviewed selected-county fixture-backed report, and validate the resulting approved
report page, artifact, and lineage through runtime smoke.

## Non-goals

- No new sources, source approvals, counties, jurisdictions, rulepacks, or source
  registry rows.
- No DS-017 vendor decision, owner/value/title field exposure, paid source integration,
  or entitlement claim.
- No hosted deployment, hosted identity/RBAC, hosted observability, hosted object-store,
  production traffic proof, or Level 10 completion claim.
- No arbitrary in-county coverage. The UI path must preserve the recorded fixture-profile
  match and fail-closed behavior implemented by `/operator-cases/supported-aoi/report`.
- No change to generic `POST /report-runs`; it remains evidence-consumer-only by
  default.

## Current state

- PR #104 added `/operator-cases/supported-aoi/report` and service/API/DB proof for
  existing `area_id` inputs.
- `state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 authority. This slice only
  refreshes Level 9 private-MVP UI/runtime proof and does not promote hosted Level 10
  gates.
- The operator UI has a packaged selected-county launcher and custom AOI intake, but no
  no-JavaScript form that calls the supported-AOI area-ID route.
- Runtime smoke can post packaged operator cases and custom AOIs, but cannot exercise
  the supported-AOI area-ID UI workflow.
- Source readiness still has one Must blocker, DS-017. Hosted validators are repo-local
  proof only, not external runtime authority.

## Decision

Implement the narrow UI/runtime proof rather than DS-017, hosted, or Bologna work.
The supported-AOI UI path is the next unblocked step because it strengthens the generic
AOI workflow just landed, while DS-017 and hosted authority require external evidence
and Bologna is premature before the supported AOI operator path is complete.

## Bottom-up sequence

1. Add failing UI route tests for posting an existing `area_id` to a supported-AOI UI
   route with reviewer and workspace identity handling.
2. Add failing runtime-smoke tests for a `--supported-aoi-area-id` form post and report
   page/artifact/lineage verification.
3. Implement the UI form/handler by reusing the existing supported-AOI API response
   helper and the same reviewer/identity controls as packaged selected-county reports.
4. Extend runtime smoke narrowly for the supported-AOI UI route.
5. Update runbook/state/task routing after behavior exists.
6. Run focused tests, readiness checks, and `.\scripts\verify.ps1`.

## Validation

```powershell
py -3.12 -m pytest backend\tests\api\test_ui_routes.py backend\tests\test_ui_runtime_smoke_script.py -q
py -3.12 .\scripts\private_mvp_readiness_check.py
py -3.12 .\scripts\release_readiness_check.py
py -3.12 .\scripts\readiness_matrix_check.py
git diff --check
git diff --name-only --diff-filter=D
.\scripts\validate_workspace.ps1
.\scripts\verify.ps1
```

## Risks

- A UI area-ID launcher can be mistaken for arbitrary live coverage. Copy and runbook
  text must keep the fixture-profile boundary explicit.
- Smoke support can overclaim DB persistence if it only checks in-memory local runtime.
  Keep artifact persistence expectations explicit and rely on DB gates separately.
- The supported-AOI route must keep using existing stored AOIs, not packaged `case_id`
  fallbacks.

## Progress log

- 2026-06-20: Implemented the supported-AOI UI/runtime slice in clean worktree
  `worktrees/next-route`: `/ui/` now exposes a no-JavaScript existing-area form, the
  new `/ui/operator-cases/supported-aoi/report` handler reuses reviewer and workspace
  identity gates before calling the existing supported-AOI API helper, and
  `scripts/ui_runtime_smoke.py` now supports `--supported-aoi-area-id` with report page
  and lineage checks.
- 2026-06-20: Validated with focused UI/runtime-smoke tests, focused OpenAPI contract
  tests after regenerating stubs, a DB-gated supported-AOI UI persistence test against
  isolated PostGIS on port `55471`, private-MVP/release-readiness/readiness-matrix
  checks, diff/no-deletion audit, default `.\scripts\verify.ps1`, and DB-enabled
  `.\scripts\verify.ps1` against the same isolated PostGIS runtime.
