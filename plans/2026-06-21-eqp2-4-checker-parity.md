# EQP2-4 Checker Advertisement Parity

## Goal
Make the empirical-qualification crosswalk executable at the checker boundary: every mapped readiness/authority checker must emit its mapped criterion IDs in a machine-readable form, the status checker must consume those checker-advertised IDs, and qualification validation must fail closed when checker advertisements drift from the crosswalk.

## Non-goals
- Do not change checker pass/fail behavior or gate semantics.
- Do not move any qualification, overlay, conditional overlay, or criterion to `PASS`.
- Do not unfreeze owner decisions, target bindings, source profiles, candidate identity, domain profiles, rubrics, source rights, AOI scope, or target status.
- Do not add DB schema, public API, auth, UI, report, connector, fixture, source-registry, hosted, Bologna runtime, or source-rights changes.
- Do not replace the crosswalk as canonical mapping authority.

## Current state
- `EQP2-1` derives committed status from the crosswalk and real checker exits, but failed checker paths are mapped back to status through crosswalk entries inside `qualification_status_check.py`.
- `EQP2-2` makes change-impact advisory and executable from matrix-owned globs plus crosswalk surface context.
- `EQP2-3` adds blocked repo-local P0 auto-evidence for `P0-004`, `P0-005`, `P0-021`, and `P0-023`.
- `config/qualification/readiness_crosswalk.yaml` currently maps 27 surfaces to checker paths and criterion IDs. The mapped checker scripts do not yet expose those IDs themselves.
- `state/EMPIRICAL_QUALIFICATION_STATUS.yaml` remains honest: P0 is `BLOCKED`, non-P0 qualification surfaces are `NOT_RUN`, `result_path` stays null, targets are `DRAFT`, and candidate fields remain null.
- `state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 authority context. EQP2-4 only changes how existing checks report into qualification; it does not reinterpret Level 9/10 readiness or create hosted/runtime authority.

## Proposed design
Add a shared `scripts/qualification_checker_advertisement.py` helper that emits `qualification_checker_advertisement_v1` JSON for a checker path from the canonical crosswalk. Add a tiny pre-main hook to each checker referenced by `checker_paths` so `python <checker> --qualification-criteria-json` exits before normal validation and prints the advertisement.

Extend `scripts/validate_qualification.py` to invoke every mapped checker with the advertisement flag and compare its JSON against the crosswalk. Extend `scripts/qualification_status_check.py` so failed checker results block status through the advertised criterion IDs carried on `CheckerResult`, not by directly re-reading crosswalk entries for the failed path.

Rejected alternatives:
- Duplicate criterion ID constants in every checker: this would create a second mapping authority and make the checkers fight the crosswalk.
- Keep status derivation crosswalk-only: this would leave EQP2-4's checker-boundary drift unproven.
- Change checker normal output to always include criteria: that risks breaking existing callers and is unnecessary for validation.

## Bottom-up sequence
1. Add failing tests for checker advertisement, validator parity rejection, and status-check fail-closed behavior when advertisements are missing.
2. Add the shared advertisement helper.
3. Add the `--qualification-criteria-json` pre-main hook to every crosswalk-mapped checker.
4. Extend qualification validation and status derivation to consume checker advertisements.
5. Update selftest/routing/state docs.
6. Run focused checks, full verify, PR/CI, post-merge proof, and worktree cleanup.

## Files likely to change
| File | Expected change |
|---|---|
| `scripts/qualification_checker_advertisement.py` | New shared advertisement helper and CLI. |
| `scripts/*_check.py`, `scripts/source_readiness.py` | Add additive `--qualification-criteria-json` hook to crosswalk-mapped checkers. |
| `scripts/validate_qualification.py` | Validate crosswalk-to-checker advertisement parity. |
| `scripts/qualification_status_check.py` | Attach and consume checker-advertised criterion IDs. |
| `scripts/selftest_qualification_validator.py` | Add fail-closed checker-advertisement drift case. |
| `backend/tests/test_qualification_checker_advertisement.py`, `backend/tests/test_qualification_status_check.py`, `backend/tests/test_qualification_spine.py` | Focused coverage. |
| `MANIFEST.md`, `plans/README.md`, `state/PROJECT_STATE.md`, `state/WORKLOG.md`, `state/VALIDATION_LOG.md`, `tasks/task_queue.yaml` | Routing/state updates. |

## Tests / verification
- Red first: `$env:PYTHONPATH='backend'; py -3.12 -m pytest backend\tests\test_qualification_checker_advertisement.py backend\tests\test_qualification_status_check.py backend\tests\test_qualification_spine.py -q`
- Focused green: same pytest command after implementation.
- Direct validator: `py -3.12 scripts\validate_qualification.py --root . --layout repo`.
- Direct status check: `py -3.12 scripts\qualification_status_check.py --root .`.
- Selftest: `py -3.12 scripts\selftest_qualification_validator.py`.
- Full gate: `.\scripts\verify.ps1`.

## Risks and blockers
- Invoking each checker for advertisement must not run normal checker side effects or require runtime inputs.
- The helper must preserve the crosswalk as canonical mapping authority without hiding a missing checker hook.
- PowerShell and POSIX verification must continue to use the same checker behavior as before.

## Decision log
- 2026-06-21: Checker advertisements will be opt-in via `--qualification-criteria-json` to avoid changing existing checker output or exit semantics.

## Progress log
- 2026-06-21: Created `worktrees/eqp2-4` from live `origin/main@2ba6f1b` on branch `eqp2/4-checker-parity`.
- 2026-06-21: Added RED tests for checker advertisement output, validator advertisement-drift rejection, status fail-closed behavior for missing advertisements, and qualification spine ownership of the new helper.
- 2026-06-21: Added shared advertisement helper, opt-in checker hooks for all 29 crosswalk-mapped checker paths, validator parity checking, status derivation through checker-advertised criterion IDs, and selftest coverage for checker-advertisement drift.
- 2026-06-21: Focused tests, direct qualification validator/status/selftest checks, and full `.\scripts\verify.ps1` passed; DB smoke skipped because `RUN_DB_SMOKE` was not set.
