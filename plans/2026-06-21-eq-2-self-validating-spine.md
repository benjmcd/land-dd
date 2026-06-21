# EQ-2 Self-Validating Qualification Spine

## Goal
Land the empirical-qualification framework as a repo-shaped, self-validating control-plane spine with local and CI validation gates. The imported artifacts must validate structurally, preserve an honest blocked/not-qualified posture, and fail closed when the validator selftest mutates status, targets, or catalog evidence.

## Non-goals
- Do not claim qualification PASS.
- Do not freeze owner decisions, targets, judgment rubrics, domain profiles, or source profiles.
- Do not approve Bologna product/AOI/source-rights decisions or capture Bologna fixtures.
- Do not change runtime report semantics, public APIs, database schema, or production dependencies.
- Do not retire existing readiness/authority checkers; crosswalk consolidation is a later lane.

## Current State
- `origin/main` is at `2e5cc0dafe3bc6cbdb25aed165410216badbdc3f`, with EQ-1 and EQ-BOL merged.
- The dirty root checkout remains a preservation lane and is not implementation authority.
- `state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 gate-matrix authority; this
  lane adds qualification structural validation without changing any Level 9/10 gate
  status or claiming hosted/production authority.
- The read-only framework package at `C:\Users\benny\Downloads\land-dd_empirical_qualification` passes:
  - `python ...\scripts\selftest_qualification_validator.py`
  - `python ...\scripts\validate_qualification.py --root ...\land-dd_empirical_qualification`
- The package validator does not support a catalog-only default. In repo layout it requires framework docs, targets, status, rubrics, change-impact files, schemas, and domain/source profile directories before it can validate catalog/framework parity and run adversarial selftests.
- `backend[dev]` currently includes PyYAML typing support but not `jsonschema`.

## Proposed Design
Import the framework into the package's recommended repo layout instead of weakening the validator or adding a narrower validation mode.

Rejected alternatives:
- **Copy only the four EQ-2 YAML/schema files:** fails the package selftest and would leave the CI gate unable to validate the exact imported control plane.
- **Add a catalog-only validator mode:** reduces immediate blast radius, but it bypasses the package's strongest fail-closed checks and creates a second validation semantics before the first repo import is proven.
- **Run CI against the package in Downloads:** not portable and violates repo-owned reproducibility.

The spine will therefore include DRAFT target/rubric/profile inputs and status evidence needed for structural validation. These artifacts are validation authority only: they keep target status `DRAFT`, preserve no PASS claims, and retain the blocked-readiness warnings as expected output.

## Bottom-Up Sequence
1. Add tests that assert expected files, dev dependency, CI/verify wiring, validator selftest success, and framework/catalog parity.
2. Copy the package into canonical repo layout:
   - `docs/qualification/`
   - `config/qualification/`
   - `schemas/qualification/`
   - `state/EMPIRICAL_QUALIFICATION_STATUS.yaml`
   - `scripts/validate_qualification.*`
   - `scripts/selftest_qualification_validator.*`
3. Add repo-native shell wrappers and wire verify scripts.
4. Add `jsonschema` to backend dev dependencies.
5. Add `qualification-selftest` CI job.
6. Update manifest, task queue, project state, worklog, and validation log.
7. Run focused tests, validator scripts, and full verify.

## Files Likely To Change
| File | Expected change |
|---|---|
| `docs/qualification/*` | Imported framework and supporting package docs |
| `config/qualification/*` | Imported vocabulary, catalog, profiles, targets, rubrics, change matrix, domain/source profiles |
| `schemas/qualification/*` | Imported JSON schemas |
| `state/EMPIRICAL_QUALIFICATION_STATUS.yaml` | Imported honest non-PASS status surface |
| `scripts/validate_qualification.*` | Imported validator entrypoints |
| `scripts/selftest_qualification_validator.*` | Imported selftest entrypoints |
| `scripts/run_qualification_validate.sh` | CI wrapper |
| `scripts/run_qualification_selftest.sh` | CI wrapper |
| `scripts/verify.ps1` / `scripts/verify.sh` | Qualification validation step |
| `.github/workflows/ci.yml` | `qualification-selftest` job |
| `backend/pyproject.toml` | `jsonschema` dev dependency |
| `backend/tests/test_qualification_spine.py` | Repo-owned regression coverage |
| `MANIFEST.md`, `tasks/task_queue.yaml`, `state/*` | Routing and closeout state |

## Tests / Verification
- `python -m pytest backend/tests/test_qualification_spine.py -q`
- `python scripts/selftest_qualification_validator.py`
- `python scripts/validate_qualification.py --root . --layout repo`
- `.\scripts\verify.ps1`
- After merge, detached post-merge `.\scripts\verify.ps1`.

## Risks And Blockers
- The imported catalog is large, so line-level review must focus on path placement, schema validation, and digest/parity checks rather than manual catalog inspection.
- If `jsonschema` is absent from the local interpreter, validation must fail closed until backend dev dependencies are installed.
- A structurally valid qualification framework is not a product qualification. State and final handoff must keep `P0` blocked/not passed.
- CI will become stricter; failures should be treated as integration issues in this branch, not suppressed.

## Decision Log
- 2026-06-21: Chose full repo-shaped structural import because the package validator and selftest require targets, status, rubrics, change matrix, and profile directories; weakening the validator would undercut the lane's purpose.

## Progress Log
- 2026-06-21: Created `worktrees/eq-2` from live `origin/main` at `2e5cc0dafe3bc6cbdb25aed165410216badbdc3f`.
- 2026-06-21: Verified the read-only package selftest and bundle validation pass before importing.
- 2026-06-21: Added a failing `backend/tests/test_qualification_spine.py` before import; it failed because repo-owned qualification artifacts and wiring were absent.
- 2026-06-21: Imported the framework into repo layout, added wrappers, wired `jsonschema`, CI, and verify gates, then brought the focused qualification spine test green.
- 2026-06-21: Verified Python validator/selftest entrypoints and PowerShell wrappers; local `.sh` execution is blocked by the machine's broken WSL bash shim, but the wrappers are retained for Linux CI.
- 2026-06-21: Full `.\scripts\verify.ps1` initially exposed stale routing assertions and a missing Level 9/10 matrix citation in the active plan; updated those surfaces and focused routing tests passed.
- 2026-06-21: Final `.\scripts\verify.ps1` passed after fixing ruff line-length issues in the new qualification test.
