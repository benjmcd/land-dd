# HCV-4 Status And Config Consistency

## Goal
Close HCV-4 by aligning qualification status derivation with the validator's full P0
parameterization blocker set, reconciling the DS-002 source-quality profile rights
vocabulary with production source-registry usage fields, and correcting current routing
after HCV-3 merged. The lane must keep `P0 = BLOCKED`, all non-P0 statuses `NOT_RUN`,
and every owner/source/AOI/Bologna/hosted decision frozen or blocked exactly as before.

## Non-goals
- Do not promote any qualification gate to `PASS` or create a result artifact.
- Do not freeze owner decisions, source bindings, domain profiles, criterion contracts,
  judgment rubrics, Bologna authority, DS-017 authority, hosted authority, DB schema,
  public API, UI behavior, or report semantics.
- Do not add Bologna/source-authority scaffolding or new source approvals.
- Do not touch product API/UI files owned by the parallel product lane.

## Current state
- HCV-1, HCV-2, and HCV-3 are merged. HCV-3 merged through PR #148 at
  `d9e16db199dee185bc05602112df010d40b4c711` after separate review, green GitHub
  checks, and detached post-merge `.\scripts\verify.ps1`.
- `scripts/qualification_status_check.py` currently blocks P0 only when
  `qualification_targets.status != FROZEN` or candidate identity fields are missing.
  `scripts/validate_qualification.py` reports a broader non-passing blocker set:
  template-only domain profiles, empty source bindings, unresolved scope/version fields,
  unresolved `ruleset_versions`, draft targets, draft criterion contracts, and draft
  judgment rubrics.
- `config/qualification/source_profiles/source_quality_profile.ds-002.yaml` maps profile
  rights to production `SourceContract` usage fields, but its values use `CONDITIONAL`
  while `backend/app/source_registry/usage_rights.py` accepts lower-case production
  statuses such as `restricted` and `approved-with-restrictions`.
- Current routing still names the HCV-3 plan/task as active because HCV-4 begins after
  the HCV-3 merge. `REC-001` and `BPS-001` are already `done`, not active; HCV-4 should
  guard against completed historical tasks being treated as active.
- The active HCV plan must keep citing `state/LEVEL_9_10_GATE_MATRIX.md` and preserve
  Level 9/10 blockers so the readiness-matrix checker remains authoritative.

## Proposed design
Extend `qualification_status_check.py` with a P0 parameterization blocker derivation that
matches the validator's blocker categories, using repo-local targets, status, catalog,
rubrics, domain profiles, and source profiles. Keep the status checker fail-closed and
status-only: it should still derive only `BLOCKED` or `NOT_RUN`, not produce pass results
or mutate artifacts.

Update the source-quality profile schema and validator rights interpretation so approved
source profiles may use production usage statuses. Treat `restricted` and
`approved-with-restrictions` as condition-bearing rights that require
`rights_conditions` and `conditions_enforced_by`, preserving the existing
`CONDITIONAL` behavior for historical fixtures/tests. Change DS-002 to the production
statuses already recorded in `registers/data_source_registry.csv`.

Route the repo from HCV-3 to HCV-4 with focused tests asserting HCV-3 is done, HCV-4 is
active, and no completed historical routing task (`REC-001`, `BPS-001`) is active.

Alternatives rejected:
- Calling the full validator from the status checker: heavier and harder to isolate from
  status derivation; the status checker only needs the P0 blocker categories.
- Dropping conditional-right enforcement for production statuses: would hide the source
  rights caveats that made DS-002 approved-with-restrictions.
- Rewriting historical HCV/Bologna plans: unnecessary; only current routing and live
  status surfaces need correction.

## Bottom-up sequence
1. Add red tests/selftest mutations for P0 remaining blocked when target/candidate
   identity is resolved but non-target parameterization blockers remain.
2. Add red tests for DS-002 production usage status vocabulary and no `CONDITIONAL`
   profile rights.
3. Add routing tests for HCV-3 done, HCV-4 active, and no stale active REC-001/BPS-001.
4. Implement status-checker blocker derivation, production-vocabulary schema/validator
   support, DS-002 profile updates, and routing/state updates.
5. Run focused qualification/status/source/routing tests, direct validators, ruff/mypy,
   diff hygiene/no-deletion checks, full `.\scripts\verify.ps1`, separate review, GitHub
   checks, merge, detached post-merge proof, and worktree removal.

## Files likely to change
| File | Expected change |
|---|---|
| `plans/2026-06-22-hcv-4-status-config-consistency.md` | Executable HCV-4 plan. |
| `scripts/qualification_status_check.py` | Derive P0 blockers from the full parameterization set. |
| `scripts/validate_qualification.py` | Interpret production source-rights statuses consistently. |
| `scripts/selftest_qualification_validator.py` | Add fail-closed HCV-4 status-derivation mutation. |
| `schemas/qualification/source_quality_profile.schema.json` | Allow production usage statuses for approved source profiles. |
| `config/qualification/source_profiles/source_quality_profile.ds-002.yaml` | Replace `CONDITIONAL` rights with production usage statuses. |
| `backend/tests/test_qualification_status_check.py` | Focused P0 blocker parity regression. |
| `backend/tests/test_qualification_honest_blocked_status.py` | DS-002 production vocabulary assertions. |
| `backend/tests/test_qualification_parameterization_backlog_artifacts.py` | Active routing assertions for HCV-4. |
| `backend/tests/test_readiness_core_artifacts.py` | Project-readiness active-plan/task assertions. |
| `plans/README.md` | Route latest/current HCV plans. |
| `tasks/task_queue.yaml` | Mark HCV-3 done and HCV-4 active. |
| `state/PROJECT_STATE.md` | Record HCV-4 as current lane and preserve blockers. |
| `state/WORKLOG.md` | Append HCV-4 execution notes. |
| `state/VALIDATION_LOG.md` | Append HCV-4 validation evidence. |

## Tests / verification
- `py -3.12 -m pytest -q tests\test_qualification_status_check.py tests\test_qualification_honest_blocked_status.py tests\test_qualification_parameterization_backlog_artifacts.py tests\test_readiness_core_artifacts.py` from `backend\`.
- `py -3.12 scripts\qualification_status_check.py --root .`
- `py -3.12 scripts\validate_qualification.py --root . --now 2026-06-21T12:00:00Z`
- `py -3.12 scripts\selftest_qualification_validator.py`
- `py -3.12 scripts\readiness_matrix_check.py`
- Focused `ruff`/`mypy` on touched scripts/tests.
- `git diff --check`
- `git diff --name-only --diff-filter=D`
- `.\scripts\verify.ps1`

## Risks and blockers
- Status derivation must not become a second independent qualification validator. It only
  derives whether P0 remains blocked from the validator's current parameterization blocker
  families plus checker results.
- Production source-rights statuses must preserve restricted/condition-bearing semantics;
  changing DS-002 to lower-case production vocabulary must not imply unrestricted use.
- Routing updates must not erase historical completed tasks or reorder the owner-authorized
  cascade that comes after HCV.

## Decision log
- 2026-06-22: Keep HCV-4 fix-only: align status/config/routing without unfreezing
  targets, source bindings, domain profiles, criterion contracts, rubrics, or P0.

## Progress log
- 2026-06-22: Created clean `worktrees/hcv4` branch `codex/hcv4-status-config` from
  live `origin/main@d9e16db`; read startup routing, HCV plan, current status checker,
  validator, DS-002 profile, production usage-rights helper, focused tests, and routing
  surfaces. Baseline focused tests, status check, structural qualification validation,
  and qualification selftest passed before edits.
