# EQ-3 Honest Blocked Qualification Status

## Goal
Make the empirical-qualification control plane report the current repo truth: P0 is blocked by unresolved parameterization, not passed, failed, or merely unrun. The validator must accept that P0 blocked state only when the status cites concrete blocker references, and it must not require a fabricated qualification result artifact for a gate that has not been run.

## Non-goals
- Do not pass P0 or any higher qualification.
- Do not fabricate candidate commits, artifact digests, criterion results, or evidence paths.
- Do not approve new owner decisions, Bologna AOI/source rights, DS-017, hosted operations, or production deployment targets.
- Do not add live connectors, DB seeds, API/report semantic changes, or UI surfaces.

## Current state
- `state/EMPIRICAL_QUALIFICATION_STATUS.yaml` has `highest_valid_classification: L9-R` and `qualifications.p0.status: NOT_RUN`.
- The status schema permits `BLOCKED` with `result_path: null`, but the validator currently requires a `result_path` for `PASS`, `FAIL`, or `BLOCKED`.
- `state/QUALIFICATION_PARAMETERIZATION_BACKLOG.md` and `docs/qualification/PROJECT_PARAMETERIZATION_BLOCKERS.md` are the canonical blocker records for unresolved P0 parameterization.
- `state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 readiness authority context; EQ-3 reports into that control plane and must not claim Level 10 readiness.
- `config/qualification/domain_profiles/` contains eight DRAFT domain stubs even though EQ-3 should retain only one active template until domain profiles are actually frozen.
- `config/qualification/source_profiles/example_source.yaml` is a placeholder. DS-002 FEMA NFHL already has a source review and registry mapping, so it is the right source for the one real approved source-quality profile.

## Proposed design
Treat P0 `BLOCKED` as a first-class status distinct from a completed qualification result. The P0 gate may omit `result_path` only when it has a non-empty `blocked_reason` and concrete `blocker_references` that resolve inside the repo. `PASS` and `FAIL` still require a result artifact.

Collapse active domain profiles to a single `domain_profile.template.yaml` and archive the eight cloned DRAFT stubs. The validator should fail P0 `PASS` if required domain profiles are missing, but should emit blocked-readiness warnings rather than errors while P0 is not passing.

Replace the placeholder source profile with one approved DS-002 FEMA NFHL source-quality profile. The profile will map its rights fields to `backend/app/source_registry/usage_rights.py::PRODUCTION_USAGE_FIELDS`, including raw-data handling, so source-quality governance does not drift from production usage checks.

Rejected alternative: create a synthetic P0 result record with `BLOCKED`. That would satisfy the old validator shape, but it would require candidate commit and artifact digest values for a result that was not actually produced.

## Bottom-up sequence
1. Add tests that assert P0 is `BLOCKED` with blocker references, the active domain profile set is one template, and the active source profile set is one DS-002 profile mapped to `PRODUCTION_USAGE_FIELDS`.
2. Extend schemas for blocked-status metadata and source profile production-usage mapping.
3. Update status/config profiles and archive superseded stubs without deletion.
4. Update the validator so P0 blocked status with references validates without a result artifact, and missing exact domain/source coverage is blocking only for P0 `PASS`.
5. Extend validator selftests to prove missing blocked references fail closed.
6. Run focused tests, qualification validator/selftest, and full local verification.

## Files likely to change
| File | Expected change |
|---|---|
| `state/EMPIRICAL_QUALIFICATION_STATUS.yaml` | Set P0 to `BLOCKED` with reason and blocker references. |
| `schemas/qualification/empirical_qualification_status.schema.json` | Permit blocked metadata on P0. |
| `schemas/qualification/source_quality_profile.schema.json` | Require/validate production usage mapping and raw-data rights. |
| `config/qualification/domain_profiles/domain_profile.template.yaml` | Add single active domain template. |
| `config/qualification/source_profiles/source_quality_profile.ds-002.yaml` | Add one approved DS-002 profile. |
| `archive/2026-06-21_eq3-domain-stubs/` | Preserve retired domain DRAFT stubs. |
| `archive/2026-06-21_eq3-source-stub/` | Preserve retired example source stub. |
| `scripts/validate_qualification.py` | Add honest blocked-status and pre-P0 template semantics. |
| `scripts/selftest_qualification_validator.py` | Add fail-closed mutation for blocked status without blocker evidence. |
| `backend/tests/test_qualification_spine.py` | Tighten P0 expectations from `NOT_RUN`/`BLOCKED` to `BLOCKED`. |
| `backend/tests/test_qualification_honest_blocked_status.py` | Add EQ-3 focused tests. |
| `state/PROJECT_STATE.md`, `state/WORKLOG.md`, `state/VALIDATION_LOG.md`, `tasks/task_queue.yaml` | Route and record EQ-3 only after validation. |

## Tests / verification
- `py -3.12 -m pytest backend/tests/test_qualification_honest_blocked_status.py backend/tests/test_qualification_spine.py -q`
- `py -3.12 scripts/validate_qualification.py --root . --layout repo`
- `py -3.12 scripts/selftest_qualification_validator.py`
- `.\scripts\verify.ps1`
- `git diff --check`
- `git status --short`

## Risks and blockers
- If the validator accepts `BLOCKED` too loosely, a team could mask incomplete qualification as valid governance. The blocker references and fail-closed selftest mitigate that.
- If active domain stubs remain, they can imply frozen domain readiness. Archiving preserves evidence without keeping them active.
- DS-002 source-quality approval must not be mistaken for enabling all production sources or passing P0. The target registry remains DRAFT and P0 remains blocked.

## Decision log
- 2026-06-21: Use explicit blocked-status metadata instead of a synthetic result artifact, because no completed P0 run exists.
- 2026-06-21: Keep exact domain/source coverage mandatory for P0 `PASS`; allow template-only active config only while P0 is non-passing.

## Progress log
- 2026-06-21: Created from live `origin/main` in `worktrees/eq-3` after EQ-2 merge proof.
- 2026-06-21: Added red EQ-3 tests, then implemented P0 `BLOCKED` metadata, domain/source profile consolidation, validator blocked-status semantics, and fail-closed selftest coverage.
- 2026-06-21: Focused EQ-3/spine tests, direct validator, and validator selftest passed.
- 2026-06-21: Fixed stale EQ-2 routing assertions and active-plan Level 9/10 citation; final `.\scripts\verify.ps1` passed.
- 2026-06-21: Tightened validator scope so only P0 may use the no-result blocked path; direct qualification checks and final `.\scripts\verify.ps1` still passed.
