# Spatial Runtime Plan Proof

## Goal
Add an opt-in DB-enabled runtime review harness for the selected-county private-MVP
spatial query-plan contract. The harness should run read-only `EXPLAIN ANALYZE` checks
against a caller-provided local or release-candidate database and fail closed when the
expected target GIST index is not visible in the plan evidence.

## Non-goals
- No hosted deployment, hosted SLO, or Level 10 completion claim.
- No default DB connection in release-readiness or static verification.
- No fixture seeding, generated runtime state, or source-data loading in any validate-only
  action.
- No DB schema change, migration rewrite, or public API change.

## Current state
- `state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 authority for this
  follow-on pass and keeps `L10-PERF-003` at `PARTIAL`.
- `config/spatial_query_plan.yaml` declares the static spatial workload/index contract.
- `scripts/spatial_query_plan_check.py` validates the static contract, DDL indexes, wrapper
  wiring, and runbook wording without opening a DB connection.
- `docs/runbooks/performance.md` documents manual runtime `EXPLAIN ANALYZE` review, but
  operators do not yet have a repo-local script that runs the configured statements in a
  read-only transaction and records structured plan evidence.
- Existing DB smoke and selected-county DB tests can prepare local PostGIS state, but this
  slice must not add a seeding path to the spatial validate action.

## Proposed design
Add a separate runtime checker and wrappers, leaving the static checker as the default
release-readiness proof. The runtime checker will:

- require `DATABASE_URL_SYNC` or an explicit `--db-url`;
- require a caller-supplied `--area-id` or `SPATIAL_QUERY_PLAN_AREA_ID`;
- validate the static contract before connecting;
- start a read-only transaction, set a local statement timeout, verify the area exists,
  run each configured statement as `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)`, and roll
  back;
- require the target table's configured GIST index in the JSON plan evidence;
- optionally write a JSON result only when `--output-json` is provided.

Rejected alternatives:
- Seeding representative rows inside the runtime checker would create write behavior in a
  proof tool and could be mistaken for production data loading.
- Composing runtime `EXPLAIN` into release readiness would make CI depend on a populated
  representative database the repo does not yet control.
- Forcing planner settings such as disabling sequential scan would overstate the evidence.

## Bottom-up sequence
1. Mark the completed SQL-contract guard task done and route the active coordinator lane
   to this runtime proof plan.
2. Add runtime-check metadata to `config/spatial_query_plan.yaml` and static validation
   for the metadata/wrappers.
3. Add `scripts/spatial_query_plan_runtime_check.py` plus Windows/POSIX wrappers.
4. Add artifact tests for read-only/default-off behavior, SQL conversion, plan parsing,
   and fail-closed missing-index handling.
5. Update performance/release guidance and state logs without promoting `L10-PERF-003`
   beyond `PARTIAL` unless actual representative runtime evidence exists.
6. Run focused checks, optional DB smoke/runtime evidence if a suitable DB is available,
   and full `.\scripts\verify.ps1`.

## Files likely to change
| File | Expected change |
|---|---|
| `config/spatial_query_plan.yaml` | Add opt-in runtime review metadata |
| `scripts/spatial_query_plan_check.py` | Validate runtime metadata/wrapper wiring statically |
| `scripts/spatial_query_plan_runtime_check.py` | New read-only DB runtime plan checker |
| `scripts/run_spatial_query_plan_runtime_check.ps1` | Windows wrapper |
| `scripts/run_spatial_query_plan_runtime_check.sh` | POSIX wrapper |
| `backend/tests/test_spatial_query_plan_artifacts.py` | Static metadata and wrapper coverage |
| `backend/tests/test_spatial_query_plan_runtime_artifacts.py` | Runtime checker unit/artifact tests |
| `docs/runbooks/performance.md` | Runtime review workflow and boundary |
| `docs/runbooks/release_readiness.md` | Clarify runtime checker remains manual/opt-in |
| `plans/README.md` | Active-plan routing |
| `tasks/task_queue.yaml` | Active task routing |
| `state/PROJECT_STATE.md` | Current checkpoint |
| `state/WORKLOG.md` | Progress record |
| `state/VALIDATION_LOG.md` | Validation evidence |

## Tests / verification
```powershell
python .\scripts\spatial_query_plan_check.py
.\scripts\run_spatial_query_plan_check.ps1
Push-Location .\backend
python -m pytest -q .\tests\test_spatial_query_plan_artifacts.py .\tests\test_spatial_query_plan_runtime_artifacts.py .\tests\test_performance_artifacts.py .\tests\test_release_readiness_artifacts.py .\tests\test_readiness_matrix_artifacts.py
python -m ruff check .\tests\test_spatial_query_plan_artifacts.py .\tests\test_spatial_query_plan_runtime_artifacts.py .\tests\test_performance_artifacts.py .\tests\test_release_readiness_artifacts.py .\tests\test_readiness_matrix_artifacts.py ..\scripts\spatial_query_plan_check.py ..\scripts\spatial_query_plan_runtime_check.py ..\scripts\release_readiness_check.py ..\scripts\readiness_matrix_check.py
python -m mypy .\tests\test_spatial_query_plan_artifacts.py .\tests\test_spatial_query_plan_runtime_artifacts.py .\tests\test_performance_artifacts.py .\tests\test_release_readiness_artifacts.py .\tests\test_readiness_matrix_artifacts.py ..\scripts\spatial_query_plan_check.py ..\scripts\spatial_query_plan_runtime_check.py ..\scripts\release_readiness_check.py ..\scripts\readiness_matrix_check.py
Pop-Location
python .\scripts\release_readiness_check.py
python .\scripts\readiness_matrix_check.py
git diff --check
git diff --name-only --diff-filter=D
```

Optional DB proof, only after a representative local/candidate database has been
prepared:

```powershell
python .\scripts\spatial_query_plan_runtime_check.py --area-id <area_id> --output-json .\local_artifacts\spatial-query-plan\<run-id>.json
```

Full handoff gate:

```powershell
.\scripts\verify.ps1
```

## Risks and blockers
- A runtime checker cannot itself prove representative workload quality; the operator must
  prepare a candidate DB with meaningful rows before using it as promotion evidence.
- Small or empty local tables may produce sequential scans. That should fail the runtime
  checker rather than be treated as evidence.
- `L10-PERF-003` should remain `PARTIAL` unless plan evidence comes from a representative
  candidate DB and the matrix is updated with that provenance.

## Decision log
- 2026-06-18: Chose an opt-in read-only runtime checker rather than a seeding helper or
  release-readiness DB gate because current default validation must remain artifact-free
  and not depend on shared runtime state.

## Progress log
- 2026-06-18: Re-anchored `main` and `origin/main`, read the active state/matrix, and
  selected `L10-PERF-003` runtime plan evidence as the next unblocked pass.
- 2026-06-18: Added the opt-in runtime checker, wrappers, static metadata validation,
  and focused artifact tests; static release-readiness remains DB-free by default.
- 2026-06-18: Applied migrations/seeds to an isolated PostGIS database on port `55450`,
  prepared a local synthetic spatial workload, and ran the runtime checker with explicit
  `--area-id`/`--output-json`. The local evidence observed `parcels_geom_gix`,
  `reference_features_geom_gix`, and `observations_geom_gix`; `L10-PERF-003` remains
  `PARTIAL` until equivalent proof exists for a representative selected-county or
  release-candidate workload.
- 2026-06-18: Passed the broad focused validator/test/lint/typecheck gate, default full
  verification, and DB-enabled full verification on a separate clean isolated PostGIS DB
  at port `55451`.
