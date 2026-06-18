# Spatial Query SQL Contract Guard

## Goal
Harden the static spatial query-plan proof so every configured review statement names
columns and aliases that exist in the canonical PostGIS schema. The immediate defect is
`area_observation_intersections` selecting `o.observation_id` even though
`evidence.observations` uses `evidence_id`.

## Non-goals
- No DB schema change or migration rewrite.
- No live DB `EXPLAIN ANALYZE` execution in the default checker.
- No hosted performance, production SLO, or Level 10 completion claim.
- No runtime seed data or generated query-plan artifacts.

## Current state
- `state/LEVEL_9_10_GATE_MATRIX.md` keeps `L10-PERF-003` at `PARTIAL` and remains the
  Level 9/10 authority for why this static guard does not promote the performance gate.
- `config/spatial_query_plan.yaml` defines three manual/read-only review statements.
- `db/migrations/0001_initial_spine.sql` is the canonical DDL authority.
- Canonical primary keys are `geo.parcels.parcel_id`, `geo.reference_features.feature_id`,
  and `evidence.observations.evidence_id`.
- The checker currently validates indexes, wrappers, and runbook wording, but only checks
  that each statement contains `EXPLAIN`; it does not verify selected columns or table
  aliases.
- The static checker still passes even when the observations statement names the
  non-existent `observation_id` column.

## Proposed design
Correct the bad statement and make the checker fail closed on statement drift by adding
a small expected-statement contract keyed by review ID. The checker should normalize SQL
text and require each statement to include the expected table aliases, selected primary
key, `ST_Intersects` join, `core.areas` join, and `a.area_id = :area_id` filter. This
keeps validation repo-file-only while making the static proof stronger.

Rejected alternatives:
- Running live DB plans by default would cross the validate-only boundary and still would
  not be representative without candidate data.
- Parsing full SQL would add avoidable dependency/complexity; exact token checks are
  enough for the current fixed review statements.

## Bottom-up sequence
1. Correct `area_observation_intersections` to select `o.evidence_id`.
2. Add expected statement token validation in `scripts/spatial_query_plan_check.py`.
3. Add focused artifact tests proving primary-key tokens are pinned and `observation_id`
   is absent/rejected.
4. Update active routing/state logs after validation.

## Files likely to change
| File | Expected change |
|---|---|
| `config/spatial_query_plan.yaml` | Correct observation statement primary key |
| `scripts/spatial_query_plan_check.py` | Statement token validation |
| `backend/tests/test_spatial_query_plan_artifacts.py` | Regression coverage for statement identifiers |
| `plans/README.md` | Active-plan routing |
| `tasks/task_queue.yaml` | Active task routing |
| `state/PROJECT_STATE.md` | Current checkpoint |
| `state/WORKLOG.md` | Progress record |
| `state/VALIDATION_LOG.md` | Validation evidence |

## Tests / verification
```powershell
python .\scripts\spatial_query_plan_check.py
.\scripts\run_spatial_query_plan_check.ps1
python .\scripts\release_readiness_check.py
.\scripts\run_release_readiness_check.ps1
python .\scripts\readiness_matrix_check.py
.\scripts\run_readiness_matrix_check.ps1
Push-Location .\backend
python -m pytest -q .\tests\test_spatial_query_plan_artifacts.py .\tests\test_performance_artifacts.py .\tests\test_release_readiness_artifacts.py .\tests\test_readiness_matrix_artifacts.py
python -m ruff check .\tests\test_spatial_query_plan_artifacts.py .\tests\test_performance_artifacts.py .\tests\test_release_readiness_artifacts.py .\tests\test_readiness_matrix_artifacts.py ..\scripts\spatial_query_plan_check.py ..\scripts\release_readiness_check.py ..\scripts\readiness_matrix_check.py
python -m mypy .\tests\test_spatial_query_plan_artifacts.py .\tests\test_performance_artifacts.py .\tests\test_release_readiness_artifacts.py .\tests\test_readiness_matrix_artifacts.py ..\scripts\spatial_query_plan_check.py ..\scripts\release_readiness_check.py ..\scripts\readiness_matrix_check.py
Pop-Location
git diff --check
git diff --name-only --diff-filter=D
```

Full handoff gate:

```powershell
.\scripts\verify.ps1
```

## Risks and blockers
- Static token validation is not a substitute for live `EXPLAIN ANALYZE`; it only prevents
  contract statements from drifting away from canonical schema identifiers.
- Keep this slice narrow. Representative DB query-plan evidence remains a separate
  runtime/candidate-data pass.

## Decision log
- 2026-06-18: Chose a focused SQL-contract guard before runtime DB evidence because the
  existing static contract contained a non-existent column and therefore could mislead
  later runtime reviewers.

## Progress log
- 2026-06-18: Audited `db/migrations/0001_initial_spine.sql` and confirmed
  `evidence.observations.evidence_id` is canonical.
- 2026-06-18: Corrected the observations query-plan statement, added DDL-derived static
  statement validation, and passed the spatial checker, Windows wrapper, focused
  spatial tests, release-readiness/readiness-matrix validators, 35 focused artifact
  tests, focused ruff/mypy, and default full verification.
