# Spatial Query Plan Proof

## Goal
Turn the current manual spatial query-plan review into a repo-local, validate-only
proof surface for the selected-county private-MVP runtime. The slice should prove that
the canonical PostGIS DDL, documented workload contract, and release-readiness checks
agree on which spatial workloads depend on GIST indexes while preserving the Level 9/10
authority context from `state/LEVEL_9_10_GATE_MATRIX.md`.

## Non-goals
- No database schema change, migration rewrite, or new production dependency.
- No hosted performance, capacity, p99, autoscaling, or Level 10 completion claim.
- No default CI/live DB query-plan gate that depends on seeded runtime state.
- No source/vendor connector expansion and no change to report semantics.
- No committed measured runtime plan artifacts.

## Current state
- `state/LEVEL_9_10_GATE_MATRIX.md` marks `L10-PERF-003` as `PARTIAL` and asks for
  query-plan/performance proof for selected production workloads.
- `db/migrations/0001_initial_spine.sql` is the canonical DDL authority and already
  defines GIST indexes on `core.areas.geom`, `core.area_versions.geom`,
  `geo.parcels.geom`, `geo.reference_features.geom`, and
  `evidence.observations.geometry`.
- `backend/app/area_geometry/area_repo.py` uses PostGIS for area metrics and spatial
  relations, while connector bbox workflows persist spatial evidence through
  `evidence.observations.geometry`.
- `docs/runbooks/performance.md` documents spatial index coverage but still says query
  plan review is manual and has no automated plan-regression gate.
- `scripts/performance_baseline_check.py` provides the closest repo pattern: a compact
  YAML contract plus validate-only wrapper composition.

## Proposed design
Add a compact spatial query-plan contract and checker that prove static repo agreement:
the selected spatial workloads name their backing tables, geometry columns, predicates,
and expected GIST indexes; the checker confirms those indexes exist in the canonical
migration, wrappers delegate to the checker, and the performance runbook documents the
contract and its limits.

Rejected alternatives:
- Adding or changing indexes would be schema work without evidence that the current DDL
  is wrong.
- Making release readiness run `EXPLAIN ANALYZE` against a local DB would create
  environment-dependent proof and conflict with the validate-only/default-empty-runtime
  policy.
- Treating this as hosted performance proof would overclaim; DB-enabled plan evidence
  still belongs to a candidate runtime with representative data.

## Bottom-up sequence
1. Add `config/spatial_query_plan.yaml` describing selected spatial workloads, required
   indexes, and proof limits.
2. Add `scripts/spatial_query_plan_check.py` plus Windows/POSIX wrappers that validate
   the contract, canonical DDL, wrapper routing, and runbook wording without DB access
   by default.
3. Compose the new checker into release-readiness validation as a repo-local performance
   contract.
4. Update `docs/runbooks/performance.md` to replace the manual-only gap with the
   validate-only contract and explicit DB-enabled future proof boundary.
5. Add focused artifact tests for the contract/checker/runbook and update release
   readiness tests for composition.
6. Update matrix/state/task routing so future agents know `L10-PERF-003` remains
   `PARTIAL` until DB-enabled representative workload evidence exists.

## Files likely to change
| File | Expected change |
|---|---|
| `config/spatial_query_plan.yaml` | Static workload/index contract |
| `scripts/spatial_query_plan_check.py` | Validate-only contract guard |
| `scripts/run_spatial_query_plan_check.ps1` | Windows wrapper |
| `scripts/run_spatial_query_plan_check.sh` | POSIX wrapper |
| `docs/runbooks/performance.md` | Spatial plan proof workflow and limits |
| `scripts/release_readiness_check.py` | Compose the spatial checker |
| `backend/tests/test_spatial_query_plan_artifacts.py` | Focused contract/checker tests |
| `backend/tests/test_performance_artifacts.py` | Spatial runbook assertions if needed |
| `backend/tests/test_release_readiness_artifacts.py` | Release composition assertions |
| `plans/README.md` | Active-plan routing |
| `tasks/task_queue.yaml` | Active task routing |
| `state/PROJECT_STATE.md` | Current checkpoint |
| `state/LEVEL_9_10_GATE_MATRIX.md` | Updated next action and residual proof boundary |
| `state/WORKLOG.md` | Progress record |
| `state/VALIDATION_LOG.md` | Validation evidence |

## Tests / verification
```powershell
python .\scripts\spatial_query_plan_check.py
.\scripts\run_spatial_query_plan_check.ps1
python .\scripts\release_readiness_check.py
python .\scripts\readiness_matrix_check.py
Push-Location .\backend
python -m pytest -q .\tests\test_spatial_query_plan_artifacts.py .\tests\test_performance_artifacts.py .\tests\test_release_readiness_artifacts.py .\tests\test_readiness_matrix_artifacts.py
python -m ruff check .\tests\test_spatial_query_plan_artifacts.py .\tests\test_performance_artifacts.py .\tests\test_release_readiness_artifacts.py .\tests\test_readiness_matrix_artifacts.py ..\scripts\spatial_query_plan_check.py ..\scripts\release_readiness_check.py ..\scripts\readiness_matrix_check.py
python -m mypy .\tests\test_spatial_query_plan_artifacts.py .\tests\test_performance_artifacts.py .\tests\test_release_readiness_artifacts.py .\tests\test_readiness_matrix_artifacts.py ..\scripts\spatial_query_plan_check.py ..\scripts\release_readiness_check.py ..\scripts\readiness_matrix_check.py
Pop-Location
git diff --check
```

Full handoff gate:

```powershell
.\scripts\verify.ps1
```

## Risks and blockers
- Static DDL proof does not show observed query plans on a representative database.
  `L10-PERF-003` should remain `PARTIAL` until candidate-runtime plan evidence exists.
- Optional DB plan checks, if added later, must be read-only, fail closed on missing
  runtime/indexes, and must not seed or write artifacts.
- The workload list must stay intentionally scoped to selected-county private-MVP spatial
  paths, not a broad promise that every future spatial query is covered.

## Decision log
- 2026-06-18: Chose `L10-PERF-003` after the performance-baseline slice because it is
  unblocked, repo-local, Postgres/PostGIS-first, and directly closes the runbook's
  manual-only query-plan review gap without crossing hosted deployment or source/vendor
  blockers.

## Progress log
- 2026-06-18: Re-anchored on `origin/main` commit
  `3ac1b6451171cf070df85bfe08cfbcfbe6ebba3e`, created branch
  `codex/spatial-query-plan-proof`, audited canonical spatial DDL and existing
  performance/release validator patterns, and selected the static contract/checker
  approach.
- 2026-06-18: Added `spatial_query_plan_v1`, the validate-only checker and wrappers,
  release-readiness composition, corrected performance/release runbook language, and
  focused tests. Focused validators/tests/lint/type checks passed, and full
  `.\scripts\verify.ps1` passed with DB smoke skipped by default.
