# EQP2-2 Executable Change Impact

## Goal
Make qualification change-impact invalidation executable and advisory: a changed path set maps to implicated `change_classes`, review groups, invalidated criterion IDs, and crosswalk surface criterion IDs without changing any gate status or producing any PASS result.

## Non-goals
- Do not move any qualification, overlay, conditional overlay, or criterion to `PASS`.
- Do not unfreeze owner decisions, target bindings, source profiles, candidate identity, domain profiles, rubrics, or target status.
- Do not change DB schema, public APIs, auth, report semantics, runtime product modules, or UI files.
- Do not make change impact a hard gate. Affected criteria should print/report while the command exits zero unless its inputs are internally inconsistent.
- Do not implement EQP2-3 evidence collection or EQP2-4 checker criterion-advertisement parity in this lane.

## Current state
- `config/qualification/change_impact_matrix.yaml` lists review groups and `invalidate_by_default` criterion IDs for each change class, but it has no executable path matching metadata.
- `config/qualification/readiness_crosswalk.yaml` maps active config/checker surfaces to criterion IDs and evidence roles.
- `scripts/qualification_status_check.py` already provides a small qualification script pattern: YAML loading, repo-relative path safety, pure derivation functions, CLI output, and wrappers.
- `scripts/selftest_qualification_validator.py` already copies repo fixtures, runs the structural validator, and now runs the status checker for fail-closed drift.
- `verify.ps1`, `verify.sh`, and `.github/workflows/ci.yml` run selftest, validator, and status derivation. EQP2-2 needs the same local and CI visibility.
- Post-merge baseline from `origin/main@a291d0d` passed `.\scripts\verify.ps1` in detached proof before this lane started.
- `state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 authority matrix for release/readiness routing; this lane only reports qualification invalidation impact and does not change Level 9/10 gate status.

## Proposed design
Extend the change-impact matrix with `path_globs` under each change class. This keeps path classification in the canonical matrix rather than hardcoding policy in Python.

The new `scripts/qualification_change_impact_check.py` will:
- load the change-impact matrix and readiness crosswalk;
- take changed paths from `--changed-path` values, `--changed-paths-file`, or default `git diff --name-only origin/main...HEAD`;
- normalize every path to repo-relative POSIX form and reject absolute/escaping paths;
- match each path against matrix `path_globs`;
- also match exact crosswalk `config_paths`/`checker_paths` to surface IDs and criterion IDs;
- report impacted change classes, review groups, matrix invalidation criterion IDs, crosswalk surface criterion IDs, and unmatched paths;
- exit zero when impacts are found or no impacts are found; exit nonzero only for internal inconsistency, such as matrix invalidation IDs not in the catalog, path-glob-free non-doc classes, unknown crosswalk criterion IDs, or unsafe changed paths.

Rejected alternatives:
- Hardcoded Python path heuristics: easier initially, but it would duplicate qualification policy outside the matrix and drift from the config.
- Treat every unmapped file as every change class: maximally conservative, but too noisy for advisory use and not backed by declared matrix semantics.
- Use only the readiness crosswalk: it can surface criterion IDs for readiness/config/checker files, but it cannot classify changes such as DB migrations, docs-only edits, UI workflow, AI/provider, or financial-model changes.

## Bottom-up sequence
1. Add failing tests for path-glob matrix shape and script behavior.
2. Extend `change_impact_matrix.schema.json` and `change_impact_matrix.yaml` with path glob metadata.
3. Implement `scripts/qualification_change_impact_check.py` with pure mapping functions and advisory CLI.
4. Add Windows/POSIX wrappers and wire the check into `verify.ps1`, `verify.sh`, and the `qualification-selftest` CI job.
5. Extend selftest with a known mapped-path case.
6. Update spine/routing/state docs and run focused checks, full verify, review, PR, and post-merge proof.

## Files likely to change
| File | Expected change |
|---|---|
| `plans/2026-06-21-eqp2-2-change-impact.md` | Lane plan and progress log. |
| `config/qualification/change_impact_matrix.yaml` | Add executable `path_globs` to change classes. |
| `schemas/qualification/change_impact_matrix.schema.json` | Allow and validate `path_globs`. |
| `scripts/qualification_change_impact_check.py` | New advisory diff-to-impact checker. |
| `scripts/qualification_change_impact_check.ps1` | Windows wrapper. |
| `scripts/run_qualification_change_impact_check.sh` | POSIX/CI wrapper. |
| `scripts/selftest_qualification_validator.py` | Add known mapped-path selftest. |
| `scripts/verify.ps1` | Add informational qualification change-impact step. |
| `scripts/verify.sh` | Add informational qualification change-impact step. |
| `.github/workflows/ci.yml` | Add change-impact step to qualification-selftest job. |
| `backend/tests/test_qualification_change_impact_check.py` | New focused tests. |
| `backend/tests/test_qualification_readiness_crosswalk.py` | Assert path globs are present and catalog-valid. |
| `backend/tests/test_qualification_spine.py` | Register artifacts and verify/CI wiring. |
| `MANIFEST.md`, `plans/README.md`, `state/PROJECT_STATE.md`, `state/WORKLOG.md`, `state/VALIDATION_LOG.md`, `tasks/task_queue.yaml` | State/routing updates after implementation. |

## Tests / verification
- Red first: `py -3.12 -m pytest backend/tests/test_qualification_change_impact_check.py backend/tests/test_qualification_readiness_crosswalk.py backend/tests/test_qualification_spine.py -q`
- Focused green: same pytest command after implementation.
- Direct checker: `py -3.12 scripts/qualification_change_impact_check.py --root . --changed-path config/release_readiness.yaml --changed-path scripts/source_readiness.py`
- Selftest: `py -3.12 scripts/selftest_qualification_validator.py`
- Validator: `py -3.12 scripts/validate_qualification.py --root . --layout repo`
- Status check: `py -3.12 scripts/qualification_status_check.py --root .`
- Lint/type narrow surface: `ruff check scripts/qualification_change_impact_check.py backend/tests/test_qualification_change_impact_check.py backend/tests/test_qualification_readiness_crosswalk.py backend/tests/test_qualification_spine.py`; targeted mypy if the environment supports it.
- Full gate before PR: `.\scripts\verify.ps1`.
- CI before merge: GitHub `verify`, `db-verify`, and `qualification-selftest` green.
- Post-merge proof: detached `origin/main` `.\scripts\verify.ps1`.

## Risks and blockers
- Path-glob mapping is policy. Overbroad globs make the advisory report noisy; underbroad globs miss impact. Keep globs conservative, and surface unmatched paths explicitly.
- `git diff origin/main...HEAD` may be empty in CI after merge or in unchanged worktrees; empty input must be valid and advisory, not a failure.
- Some changed paths may map through both matrix globs and crosswalk exact paths. The report should merge rather than double-count criterion IDs.
- This lane does not validate whether impacted criteria are satisfied. It only identifies what needs review or invalidation.

## Decision log
- 2026-06-21: Use matrix-owned `path_globs` plus crosswalk exact-path enrichment. This keeps executable classification in the canonical change-impact source and avoids Python-only policy drift.

## Progress log
- 2026-06-21: Lane worktree `worktrees/eqp2-2` created from `origin/main@a291d0d` after EQP2-1 merge and detached proof passed.
- 2026-06-21: Added red tests for the new checker, matrix path-glob metadata, and verify/CI wiring.
- 2026-06-21: Implemented matrix-owned path globs, advisory change-impact checker, wrappers, selftest case, verify/CI wiring, and routing/state updates.
- 2026-06-21: Focused tests, direct checker, qualification selftest, structural validator, status check, ruff, and mypy passed before full verify.
- 2026-06-21: Full `.\scripts\verify.ps1` passed after routing assertion and PowerShell wrapper fixes.
- 2026-06-21: Tightened matrix globs so qualification control-plane configs, schemas, scripts, wrappers, and qualification tests map to `DOMAIN_REFERENCE_OR_RUBRIC`; full verify passed again with default diff reporting those impacts.
- 2026-06-21: Addressed review feedback by mapping current `connectors`, `claims_engine`, `area_geometry`, and `evidence_ledger` package/test paths, proving `scripts/verify.sh`/`.ps1` impact mapping, and setting `fetch-depth: 0` for CI jobs that run the checker; full verify passed again.
