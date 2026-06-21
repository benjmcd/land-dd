# EQ-4 Readiness Crosswalk

## Goal
Subordinate the existing readiness, authority, and release-governance gates to the empirical-qualification control plane by mapping each active gate surface to canonical qualification criterion IDs. The result should reduce governance ambiguity without changing any existing checker behavior.

## Non-goals
- Do not change readiness, authority, source, release, UI, API, DB, or report behavior.
- Do not retire or archive any existing readiness/authority checker.
- Do not claim any qualification `PASS`, Level 10 readiness, Bologna approval, source approval, or owner-decision resolution.
- Do not add runtime dependencies or product behavior.

## Current state
- ADR 0004 says existing readiness YAML/checkers, authority packets, release-readiness checks, and `state/LEVEL_9_10_GATE_MATRIX.md` report into empirical qualification rather than competing with it.
- This plan preserves the Level 9/10 authority context by treating `state/LEVEL_9_10_GATE_MATRIX.md` as a reporting surface, not an empirical qualification pass source.
- `config/qualification/change_impact_matrix.yaml` exists, but its `invalidate_by_default` values are still prose/gate labels rather than validated criterion IDs.
- There is no `docs/qualification/readiness-crosswalk.md` or machine-readable crosswalk that proves every active readiness/authority surface has a catalog home or a recorded orphan/gap status.
- `scripts/validate_qualification.py` validates the change-impact matrix schema but does not validate invalidation IDs or any readiness crosswalk.

## Proposed design
Add a machine-readable `config/qualification/readiness_crosswalk.yaml` plus schema and a concise `docs/qualification/readiness-crosswalk.md`. The crosswalk will list the self-derived inventory policy, each mapped surface, config/checker paths, criterion IDs, evidence role, and notes. The validator will load the crosswalk, validate its schema, ensure criterion IDs exist in `criterion_catalog.yaml`, and ensure the declared inventory covers the self-derived readiness/authority config and checker paths.

Normalize `config/qualification/change_impact_matrix.yaml` so `invalidate_by_default` contains exact criterion IDs, then validate those IDs against the catalog. The matrix remains a conservative invalidation map, not a claim that those criteria pass.

Rejected alternative: annotate every existing checker/config file in-place. That would touch many ownership surfaces for metadata-only gain. A central crosswalk with self-derived inventory tests gives the governance link without behavior churn.

## Bottom-up sequence
1. Add failing tests for crosswalk presence, inventory coverage, criterion-ID validity, and change-impact criterion-ID validity.
2. Add `readiness_crosswalk.yaml`, its schema, and the Markdown crosswalk.
3. Convert change-impact invalidation targets to criterion IDs.
4. Extend the qualification validator and selftest to validate crosswalk and change-impact IDs.
5. Update routing/state logs.
6. Run focused tests, validator/selftest, readiness matrix, and full `.\scripts\verify.ps1`.

## Files likely to change
| File | Expected change |
|---|---|
| `config/qualification/readiness_crosswalk.yaml` | New machine-readable mapping from readiness/authority surfaces to criterion IDs. |
| `schemas/qualification/readiness_crosswalk.schema.json` | New schema for the crosswalk. |
| `docs/qualification/readiness-crosswalk.md` | Human-readable crosswalk, gaps, and orphan summary. |
| `config/qualification/change_impact_matrix.yaml` | Replace prose invalidation targets with criterion IDs. |
| `scripts/validate_qualification.py` | Validate crosswalk and change-impact criterion IDs. |
| `scripts/selftest_qualification_validator.py` | Add fail-closed mutation for invalid crosswalk/change-impact IDs. |
| `backend/tests/test_qualification_readiness_crosswalk.py` | New focused tests for EQ-4. |
| `backend/tests/test_qualification_spine.py` | Include new crosswalk artifacts in repo-owned spine checks. |
| `state/PROJECT_STATE.md`, `state/WORKLOG.md`, `state/VALIDATION_LOG.md`, `tasks/task_queue.yaml`, `plans/README.md`, `MANIFEST.md` | Route and record EQ-4. |

## Tests / verification
- `py -3.12 -m pytest backend/tests/test_qualification_readiness_crosswalk.py backend/tests/test_qualification_spine.py -q`
- `py -3.12 scripts/validate_qualification.py --root . --layout repo`
- `py -3.12 scripts/selftest_qualification_validator.py`
- `py -3.12 scripts/readiness_matrix_check.py`
- `.\scripts\verify.ps1`
- `git diff --check`
- `git diff --name-only --diff-filter=D`

## Risks and blockers
- A crosswalk can become another stale authority if it is not checked against live inventory. The test and validator must derive expected paths from globs rather than only trusting hand-maintained rows.
- Mapping a checker to a criterion ID does not satisfy that criterion. The crosswalk must state evidence-role and blocked gaps, not pass status.
- Change-impact criterion IDs must be conservative and exact enough to be enforceable without listing the entire catalog for every class.

## Decision log
- 2026-06-21: Use a central checked crosswalk instead of editing every readiness/authority checker for metadata-only annotations.

## Progress log
- 2026-06-21: Started from live `origin/main` at `961bffd513df6b8fc66b177e605094c7205e1dee` in `worktrees/eq-4`.
- 2026-06-21: Added focused red tests for missing crosswalk artifacts and prose-based change-impact invalidations.
- 2026-06-21: Added the checked readiness crosswalk, schema, human doc, catalog-ID change-impact matrix, validator enforcement, and selftest mutations without changing readiness checker behavior.
- 2026-06-21: Tightened validator/test coverage so required readiness/authority glob families cannot be silently removed from crosswalk inventory.
