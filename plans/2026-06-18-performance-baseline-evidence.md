# Performance Baseline Evidence

## Goal
Make release-candidate performance regression evidence observable and repeatable for the
selected-county private-MVP runtime by giving the existing load-test runner a
machine-readable baseline contract and optional JSON result output.

## Non-goals
- No hosted load test, production SLO, capacity claim, autoscaling work, or external
  load-testing service integration.
- No new API behavior, database schema, connector behavior, source coverage, or report
  semantics.
- No CI live-load gate that starts a server or fails builds on environment-dependent
  latency.
- No claim that Level 10 performance is complete; hosted workload proof remains future
  deployment work.

## Current state
- `state/LEVEL_9_10_GATE_MATRIX.md` marks `L10-PERF-010` as `VALIDATE_ONLY` and calls
  for measured baseline artifacts for release candidates.
- `scripts/load_test_runner.py` already runs sequential and concurrent local scenarios
  and prints latency/error summaries to stdout.
- `scripts/run_load_test.ps1` and `scripts/run_load_test.sh` validate that load-test
  artifacts exist, then run live scenarios by default.
- `docs/runbooks/load_testing.md` documents sequential and concurrent scenarios,
  thresholds, and limitations, but it treats output as console evidence.
- `docs/runbooks/performance.md` says release readiness validates artifacts while live
  load scenarios remain local/manual.
- `scripts/release_readiness_check.py` only requires the runner/wrappers/runbooks to
  exist and does not validate a baseline evidence schema.

## Proposed design
Add a small repo-local performance baseline contract that records the expected scenario
shape, thresholds, and required result fields. Extend the load-test runner to optionally
write JSON results for sequential and concurrent scenarios, then make validate-only
checks prove that the baseline contract, runner, wrappers, and runbooks agree.

Rejected alternatives:
- Running live load tests in CI would make release readiness depend on hosted/runtime
  availability and noisy shared-runner timing.
- Committing measured local results would make the repo carry stale machine-specific
  evidence.
- Adding a new load-test framework would introduce a dependency before the current
  standard-library runner is exhausted.

## Bottom-up sequence
1. Add a compact `config/performance_baseline.yaml` contract for current local scenarios.
2. Add `scripts/performance_baseline_check.py` plus Windows/POSIX wrappers to validate
   the contract, runner support, wrapper routing, and runbook wording without live HTTP.
3. Extend `scripts/load_test_runner.py` with optional JSON result output while preserving
   existing stdout behavior and exit codes.
4. Extend `run_load_test` wrappers to accept an optional output path for live runs and
   include the baseline contract in validate-only artifact checks.
5. Add focused artifact/unit tests for the baseline contract and JSON result shape.
6. Update runbooks/state so future agents know this is release-candidate evidence, not
   hosted production proof.

## Files likely to change
| File | Expected change |
|---|---|
| `config/performance_baseline.yaml` | Scenario thresholds and JSON evidence schema |
| `scripts/load_test_runner.py` | Optional JSON result output |
| `scripts/run_load_test.ps1` | Optional result output parameter and baseline artifact check |
| `scripts/run_load_test.sh` | Optional result output argument and baseline artifact check |
| `scripts/performance_baseline_check.py` | Validate-only contract guard |
| `scripts/run_performance_baseline_check.ps1` | Windows wrapper |
| `scripts/run_performance_baseline_check.sh` | POSIX wrapper |
| `docs/runbooks/load_testing.md` | Document JSON evidence output and limitations |
| `docs/runbooks/performance.md` | Route release-candidate baseline evidence |
| `scripts/release_readiness_check.py` | Include the baseline contract/checker in release readiness |
| `backend/tests/test_load_test_artifacts.py` | Focused artifact and runner JSON tests |
| `backend/tests/test_performance_artifacts.py` | Baseline checker/runbook tests |
| `plans/README.md` | Active-plan routing |
| `tasks/task_queue.yaml` | Active task and validation routing |
| `state/PROJECT_STATE.md` | Current checkpoint |
| `state/WORKLOG.md` | Progress record |
| `state/VALIDATION_LOG.md` | Validation evidence |

## Tests / verification
```powershell
python .\scripts\performance_baseline_check.py
.\scripts\run_performance_baseline_check.ps1
.\scripts\run_load_test.ps1 -ValidateOnly
Push-Location .\backend
python -m pytest -q .\tests\test_load_test_artifacts.py .\tests\test_performance_artifacts.py .\tests\test_release_readiness_artifacts.py .\tests\test_readiness_matrix_artifacts.py
python -m ruff check .\tests\test_load_test_artifacts.py .\tests\test_performance_artifacts.py .\tests\test_release_readiness_artifacts.py .\tests\test_readiness_matrix_artifacts.py ..\scripts\load_test_runner.py ..\scripts\performance_baseline_check.py ..\scripts\release_readiness_check.py ..\scripts\readiness_matrix_check.py
python -m mypy .\tests\test_load_test_artifacts.py .\tests\test_performance_artifacts.py .\tests\test_release_readiness_artifacts.py .\tests\test_readiness_matrix_artifacts.py ..\scripts\load_test_runner.py ..\scripts\performance_baseline_check.py ..\scripts\release_readiness_check.py ..\scripts\readiness_matrix_check.py
Pop-Location
python .\scripts\release_readiness_check.py
python .\scripts\readiness_matrix_check.py
git diff --check
```

Full handoff gate:

```powershell
.\scripts\verify.ps1
```

## Risks and blockers
- Latency measurements are environment-dependent; do not make CI assert live latency
  until a controlled runtime target exists.
- JSON result output must not seed repo artifacts by default; operators choose the output
  path during a release-candidate run.
- Existing POST payloads may return 4xx in local modes; the current runner treats 4xx as
  non-error, and this slice should preserve that contract.
- Hosted workload proof, DB/object-store tuning, and formal p99/SLO targets remain
  blocked by production deployment decisions.

## Decision log
- 2026-06-18: Chose `L10-PERF-010` because it is an unblocked repo-local slice from the
  Level 9/10 matrix and improves release-candidate evidence without crossing hosted
  production blockers.

## Progress log
- 2026-06-18: Created the active plan after auditing the existing load-test runner,
  wrappers, release-readiness validator, and performance/load-testing runbooks.
- 2026-06-18: Added the performance baseline contract/checker, optional
  `load_test_result_v1` JSON output for live load-test runs, result-directory wrapper
  support, runbook documentation, release-readiness composition, and focused tests.
- 2026-06-18: Focused validation passed: baseline checker and wrapper, load-test
  validate-only wrapper, `40` artifact tests, ruff, mypy, release-readiness validator,
  readiness-matrix validator, and whitespace check.
- 2026-06-18: Full `.\scripts\verify.ps1` passed; DB smoke was skipped by default.
