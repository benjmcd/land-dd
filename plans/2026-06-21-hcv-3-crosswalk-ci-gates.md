# HCV-3 Crosswalk CI Gate Completeness

## Goal
Map readiness/release CI and gate wrapper scripts into the empirical-qualification
readiness crosswalk, then make the validator fail closed when a future CI gate wrapper
is added without a crosswalk mapping. This closes HCV-3 without promoting any
qualification criterion to `PASS`.

## Non-goals
- Do not change qualification status derivation, P0 blocker logic, source rights,
  owner decisions, Bologna authority, DB schema, API, UI, report semantics, or runtime
  behavior.
- Do not run backup/restore proof locally unless explicitly needed; the wrapper is a
  release gate and may require DB/runtime setup.
- Do not treat shell or PowerShell wrappers as Python checker scripts that must emit
  qualification-advertisement JSON.

## Current state
- HCV-1 and HCV-2 are merged; post-merge proof after HCV-2 preserved
  `BLOCKED=1 NOT_RUN=20`.
- This plan intentionally preserves routing context for
  `state/LEVEL_9_10_GATE_MATRIX.md` so the readiness-matrix checker can continue
  carrying the Level 9/10 release-gate and maintainability/governance blockers while
  HCV-3 remains fix-only.
- `config/qualification/readiness_crosswalk.yaml` maps Python checker scripts through
  `checker_paths`, and `scripts/validate_qualification.py` validates those files and
  their advertised criterion IDs.
- CI invokes wrapper gates such as `./scripts/run_provenance_check.sh` and
  `./scripts/run_security_scan.sh`; `config/release_readiness.yaml` also names
  `scripts/run_backup_restore_check.ps1` as a release proof.
- `checker_paths` cannot safely absorb `.sh` or `.ps1` wrappers because validator
  advertisement runs `python <checker_path> --emit-qualification-criteria`.

## Proposed design
Add a separate `gate_paths` field for crosswalk entries. `checker_paths` remains
Python-advertisement-only; `gate_paths` records shell/PowerShell wrapper gates that
exercise the same empirical criteria. The validator will derive expected gate paths
from current CI workflow script references, excluding qualification-control-plane
self-check wrappers, plus repo-local wrapper proofs declared in
`config/release_readiness.yaml.required_checks[*].proof`. It will fail if any expected
gate path is not declared by a crosswalk entry.

Alternatives rejected:
- Adding wrappers to `checker_paths`: breaks the existing checker-advertisement
  contract.
- Hard-coding only the three HCV-3 paths: fixes the immediate finding but does not make
  future unmapped CI gates fail closed.
- Hard-coding only backup/restore as a release proof: misses the rest of the release
  readiness proof inventory and would let a release wrapper drift out of the crosswalk.
- Mapping every local wrapper script: broader than the review finding and would force
  non-CI/manual helper scripts into the empirical crosswalk.

## Bottom-up sequence
1. Add red tests showing CI/release gate paths must be mapped and that removing one
   gate path from the crosswalk fails validation.
2. Extend the schema and validator with `gate_paths` coverage while preserving Python
   checker advertisement behavior.
3. Map current CI wrapper gates and repo-local release proof wrappers to appropriate
   crosswalk entries and criterion IDs.
4. Run focused crosswalk tests, qualification validator selftest, structural
   validation/status checks, ruff/mypy, diff hygiene, and full `.\scripts\verify.ps1`.
5. Push one HCV-3 PR, require separate review, wait for green checks, merge, run
   detached post-merge proof, and remove the worktree.

## Files likely to change
| File | Expected change |
|---|---|
| `plans/2026-06-21-hcv-3-crosswalk-ci-gates.md` | Executable HCV-3 plan. |
| `schemas/qualification/readiness_crosswalk.schema.json` | Allow optional `gate_paths` on crosswalk entries. |
| `config/qualification/readiness_crosswalk.yaml` | Map CI/release wrapper gate paths, including provenance, security scan, backup/restore, and the release-readiness proof-wrapper inventory. |
| `scripts/validate_qualification.py` | Enforce derived CI/release gate path coverage. |
| `scripts/selftest_qualification_validator.py` | Add fail-closed selftest for unmapped gate path. |
| `backend/tests/test_qualification_readiness_crosswalk.py` | Add artifact tests for gate-path coverage and catalog IDs. |
| `plans/README.md` | Route current plan to HCV-3. |
| `tasks/task_queue.yaml` | Mark HCV-2 done and HCV-3 active. |
| `state/PROJECT_STATE.md` | Record HCV-3 as current lane and preserve boundaries. |
| `state/WORKLOG.md` | Append HCV-3 execution notes. |
| `state/VALIDATION_LOG.md` | Append focused/full validation results. |

## Tests / verification
- `py -3.12 -m pytest -q backend\tests\test_qualification_readiness_crosswalk.py`
- `py -3.12 scripts\selftest_qualification_validator.py`
- `py -3.12 scripts\validate_qualification.py --root . --now 2026-06-21T12:00:00Z`
- `py -3.12 scripts\qualification_status_check.py --root .`
- Focused `ruff`/`mypy` on touched scripts/tests.
- `git diff --check`
- `git diff --name-only --diff-filter=D`
- `.\scripts\verify.ps1`

## Risks and blockers
- Gate wrappers must not be treated as advertisement-capable Python checkers.
- The validator must not require qualification self-check wrappers to appear in the
  readiness crosswalk; those are the control plane itself, not readiness surfaces.
- Backup/restore remains a release proof, but this lane only maps/enforces the wrapper
  reference. It does not claim DB restore pass authority or run DB smoke unless the
  normal verification path requires it.
- Mapping a gate path to criteria is crosswalk evidence only; it does not satisfy or
  pass those criteria.

## Decision log
- 2026-06-21: Use a separate `gate_paths` field for shell/PowerShell wrappers so
  Python `checker_paths` remain tied to checker-advertisement validation.

## Progress log
- 2026-06-21: Created clean `worktrees/hcv3` branch
  `codex/hcv3-crosswalk-gates` from live `origin/main@ba75f47`; read startup routing,
  architecture, ADR 0004, HCV control-plane plan, current crosswalk/validator/tests,
  CI workflow, release-readiness gate catalog, and wrapper scripts. Baseline
  `backend\tests\test_qualification_readiness_crosswalk.py` passed before red tests
  were added.
- 2026-06-21: Added red tests for missing gate-path mapping and missing validator
  enforcement. The focused artifact test failed because the three HCV-3 paths were
  unmapped; after adding `gate_paths` to the schema/crosswalk and validator coverage,
  focused crosswalk tests and qualification selftest pass.
- 2026-06-21: Initial full `.\scripts\verify.ps1` failed only on stale routing tests
  that still expected HCV-2 active. Updated those assertions for HCV-3; focused
  routing tests and final full `.\scripts\verify.ps1` passed. DB smoke was skipped
  because `RUN_DB_SMOKE=1` was not set.
- 2026-06-21: Separate review found the first implementation derived CI wrappers plus
  backup/restore only, leaving `config/release_readiness.yaml.required_checks[*].proof`
  wrappers unenforced. Expanded derivation to all repo-local release proofs, mapped
  those gate paths in the crosswalk, added a release-proof selftest mutation, and
  reran focused validation and full `.\scripts\verify.ps1` with
  `BLOCKED=1 NOT_RUN=20` preserved.
- 2026-06-21: Live `origin/main` advanced to PR #149
  `e124db6ce002d472ad800dac6ac4af1633c746b4`; rebased HCV-3 cleanly and reran focused
  validation with `BLOCKED=1 NOT_RUN=20` preserved before the final full verify.
