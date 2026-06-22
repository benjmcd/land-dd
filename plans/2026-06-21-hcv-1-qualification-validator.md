# HCV-1 Qualification Validator Hardening

## Goal
Harden `scripts/validate_qualification.py` and the qualification result schema against the live PR #126/#127 review findings, with selftest mutations proving each still-valid defect fails closed. The framework must remain honestly `P0 = BLOCKED`; no gate or criterion becomes `PASS`.

## Non-goals
- No Bologna or authority scaffolding.
- No DB schema, public API, report semantics, UI, connector, or product-lane changes.
- No owner-decision unfreezing, source approval, candidate selection, or qualification promotion.
- No file deletion.

## Current state
- Live authority is `origin/main@816a4dd39d174d0b3689837a489879031e49113d`
  after reconciling the PR #142 HCV handoff with the later PR #143 and PR #145
  merges.
- Baseline `py -3.12 scripts\validate_qualification.py --root .` passes structurally and reports blocked readiness warnings.
- The active plan must keep citing `state/LEVEL_9_10_GATE_MATRIX.md` and explicit Level 9/10 context so the readiness-matrix checker does not treat HCV routing as detached from the release gate map.
- PR #126 review threads are still open and map to current missing checks:
  expired PASS gates, status gate/result `gate_id` binding, result identity binding, criterion evidence resolution, frozen domain modality/channel coverage, conditional rights enforcement, unresolved frozen domain profiles, source profile coverage, and PASS reviewer metadata.
- PR #127 review threads are still open for P0 blocked-record validation with `result_path` and RAW_EXPORT requiring both `raw_data` and `export` rights.

## Proposed design
Use validator-level fail-closed checks instead of changing qualification data:
- Add deterministic expiry validation with injectable `now` passed through in-process tests.
- Bind each result file to the status record's expected gate and current status identity.
- Compare result scope/version fields against status candidate fields when candidate identity is populated, and always compare selected product/deployment profiles to the active status.
- Resolve top-level and per-criterion evidence references for PASS rows to repo-local files.
- Require frozen domain profiles to have no unresolved required contract fields and to exactly match target geographies, intents, input modalities, and output channels.
- Require approved source profiles to cover target geographies/domains and require explicit enforcement proof when enabled operations rely on `CONDITIONAL` rights.
- Require RAW_EXPORT to satisfy both `raw_data` and `export` rights.
- Validate P0 `blocked_record` whenever P0 is `BLOCKED`, including when a result file is present.
- Tighten `qualification_result.schema.json` so PASS requires non-empty reviewer metadata and at least one independent reviewer.

## Bottom-up sequence
1. Add selftest mutations that currently fail to fail closed for the HCV-1 defects.
2. Run the selftest and confirm the new cases fail for the expected reasons.
3. Implement the smallest validator/schema changes to make the tests pass.
4. Re-run selftest and the baseline validator/status checks.
5. Update state, worklog, validation log, and task routing for HCV-1 only.
6. Run full `.\scripts\verify.ps1`, then push a PR if clean.

## Files likely to change
| File | Expected change |
|---|---|
| `scripts/validate_qualification.py` | Add fail-closed result, profile, rights, evidence, expiry, and blocker validation. |
| `scripts/selftest_qualification_validator.py` | Add HCV-1 regression mutations. |
| `schemas/qualification/qualification_result.schema.json` | Require PASS reviewer metadata and independent reproduction signal. |
| `plans/README.md` | Add HCV-1 plan routing. |
| `tasks/task_queue.yaml` | Mark HCV-1 active/done without touching Bologna scaffolding. |
| `state/PROJECT_STATE.md` | Record active HCV-1 authority and no-PASS boundary. |
| `state/WORKLOG.md` | Append HCV-1 execution notes. |
| `state/VALIDATION_LOG.md` | Append focused/full validation results. |

## Tests / verification
- `py -3.12 scripts\selftest_qualification_validator.py`
- `py -3.12 scripts\validate_qualification.py --root .`
- `py -3.12 scripts\qualification_status_check.py --root .`
- `py -3.12 scripts\qualification_change_impact_check.py --root .`
- `py -3.12 scripts\readiness_matrix_check.py`
- Focused pytest for qualification artifacts if affected.
- `git diff --check`
- `.\scripts\verify.ps1`

## Risks and blockers
- The validator should become stricter without changing committed qualification status. If a stricter rule causes live blocked state to fail structurally, stop and distinguish a real data inconsistency from an over-broad validator.
- Reviewer-thread resolution requires GitHub thread IDs and should happen only after the fix is merged or clearly proven stale.

## Decision log
- 2026-06-21: HCV-1 chosen first because it hardens the control plane that gates later qualification claims; Bologna remains externally blocked and out of scope.

## Progress log
- 2026-06-21: Created clean worktree `worktrees/hcv1`, then rebased it to
  `origin/main@816a4dd` after PR #145 merged; reconciled PR #126/#127 review
  threads and baseline validator state.
- 2026-06-21: Added HCV-1 selftest mutations, hardened the validator/schema, updated routing/state, and ran focused checks plus full `.\scripts\verify.ps1` successfully. DB smoke was skipped by default because `RUN_DB_SMOKE` was not set.
