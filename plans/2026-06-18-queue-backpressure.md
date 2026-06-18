# Queue Backpressure Runtime Guard

## Goal
Add a default-off, repo-local runtime admission guard for report and live-connector
queues so high queue depth or stale workers can fail closed before more work is
accepted. This advances the Level 9/10 gate matrix row `L10-PERF-008` without claiming
hosted production readiness.

## Non-goals
- No hosted deployment, alert manager, dashboard, billing, or SLO claim.
- No database schema changes or queue table migrations.
- No source connector execution, vendor calls, fixture seeding, or generated runtime
  artifacts in validate-only paths.
- No per-connector distributed rate limiter; the slice is queue admission control only.
- No override workflow for operators under backpressure.

## Current state
- `state/LEVEL_9_10_GATE_MATRIX.md` marks `L10-PERF-008` as `PARTIAL`: current proof
  is fail-closed source failures and runbook guidance, while explicit runtime
  backpressure behavior is missing.
- `backend/app/domain/job_health.py` already exposes `JobQueueHealth` for report and
  live connector queues, including queued/running/failed counts, oldest queued age,
  and stale-running count.
- `backend/app/api/operations.py` and UI operations routes expose queue health and
  recovery preview read-only.
- `backend/app/api/reports.py` creates report jobs after auth, area, idempotency, and
  optional connector-review checks; queue health is not consulted before admission.
- `backend/app/api/connectors.py` schedules live connector jobs after reviewer auth and
  bounded bbox validation; queue health is not consulted before admission.
- `docs/runbooks/performance.md` documents rate limiting, source-failure evidence, DB
  pool settings, and audit-sink fail-closed behavior, but not queue-depth admission
  control.

## Proposed design
Introduce a small pure decision layer in `backend/app/operations/backpressure.py` that
evaluates `JobQueueHealth` against settings-backed thresholds. Wire it into report
creation/retry and reviewed live-connector scheduling before any new queue record is
created.

Use HTTP 503 for queue backpressure because the service is temporarily unable to accept
more work while preserving idempotent replay behavior for existing jobs. Return a
structured detail payload with queue type, reason code, observed value, and threshold so
operators can correlate the response with `/operations/queue-health`.

Settings remain disabled by default:
- `ENABLE_QUEUE_BACKPRESSURE=false`
- `MAX_REPORT_QUEUE_DEPTH`
- `MAX_LIVE_CONNECTOR_QUEUE_DEPTH`
- `MAX_QUEUE_OLDEST_QUEUED_SECONDS`
- `MAX_QUEUE_STALE_RUNNING`

The guard should be DB/in-memory compatible because it only consumes the existing store
`health()` protocol.

Alternatives rejected:
- Static-only batch/concurrency contract: useful but it would not add the explicit runtime
  behavior called out by `L10-PERF-008`.
- Hosted smoke prep: still blocked by external platform authority and would not prevent
  load/outage admission locally.
- Per-connector rate limiter: larger surface and separate from queue admission.

## Bottom-up sequence
1. Add tests for the pure backpressure decision helper.
2. Add the helper and settings validation.
3. Wire report job creation/retry and live connector scheduling through the helper.
4. Add API tests proving enabled backpressure fails closed without creating jobs and
   disabled backpressure preserves current behavior.
5. Update runbooks, matrix, task queue, project state, worklog, and validation log.

## Files likely to change
| File | Expected change |
|---|---|
| `backend/app/operations/backpressure.py` | New pure admission-decision helper. |
| `backend/app/core/config.py` | Add queue-backpressure settings and validation. |
| `backend/app/api/reports.py` | Guard new report queue admission and retry. |
| `backend/app/api/intake.py` | Guard intake-created report queue admission. |
| `backend/app/api/connectors.py` | Guard live connector schedule routes. |
| `backend/app/api/ui.py` | Guard UI report retry admission. |
| `backend/app/api/ui_review.py` | Guard UI connector-review report resume admission. |
| `backend/app/api/live_connectors.py`, `backend/app/api/areas.py`, `backend/app/api/dependencies.py` | Replace invalid 422 status references exposed by affected API validation. |
| `backend/tests/api/test_backpressure.py` | New focused API/helper tests. |
| `docs/runbooks/performance.md` | Document queue-backpressure behavior and limits. |
| `docs/runbooks/incident_response.md` | Add operator response for queue backpressure. |
| `state/LEVEL_9_10_GATE_MATRIX.md` | Update `L10-PERF-008` evidence while keeping hosted proof partial. |
| `plans/README.md` | Point active plan to this file. |
| `tasks/task_queue.yaml` | Add active queue-backpressure task. |
| `state/PROJECT_STATE.md` | Record current authority and boundaries. |
| `state/WORKLOG.md` | Summarize implemented slice. |
| `state/VALIDATION_LOG.md` | Record verification commands and results. |

## Tests / verification
```powershell
cd backend; python -m pytest -q .\tests\api\test_backpressure.py
cd backend; python -m pytest -q .\tests\api\test_backpressure.py .\tests\api\test_async_report_runs.py .\tests\api\test_fema_nfhl_connector_api.py .\tests\api\test_operations.py
cd backend; python -m ruff check .\tests\api\test_backpressure.py .\app\operations\backpressure.py .\app\core\config.py .\app\api\reports.py .\app\api\connectors.py .\app\api\intake.py .\app\api\ui.py .\app\api\ui_review.py .\app\api\live_connectors.py .\app\api\dependencies.py .\app\api\areas.py
cd backend; python -m mypy .\tests\api\test_backpressure.py .\app\operations\backpressure.py .\app\core\config.py .\app\api\reports.py .\app\api\connectors.py .\app\api\intake.py .\app\api\ui.py .\app\api\ui_review.py .\app\api\live_connectors.py .\app\api\dependencies.py .\app\api\areas.py
python .\scripts\readiness_matrix_check.py
git diff --check
git diff --name-only --diff-filter=D
.\scripts\verify.ps1
```

## Risks and blockers
- Hosted dashboard, alert routing, and production workload proof remain blocked by hosted
  platform decisions, so `L10-PERF-008` must remain `PARTIAL`.
- Aggressive thresholds can block recovery retries; keep defaults disabled and document
  operator tuning.
- Existing queue health is aggregate, not per-tenant or per-source. Fine-grained
  per-workspace admission requires future RBAC/entitlement authority.

## Decision log
- 2026-06-18: Chose runtime queue admission over static batch controls because the gate
  explicitly lacks runtime backpressure behavior and current queue health makes a
  schema-free, testable guard possible.

## Progress log
- 2026-06-18: Plan opened from live `origin/main` after spatial runtime proof merged.
- 2026-06-18: Added default-off queue-backpressure helper/settings, guarded report,
  intake, UI retry, connector-review resume, and live connector scheduling paths, and
  fixed invalid 422 status constants that blocked connector error-path validation.
- 2026-06-18: Resolved review findings by switching queue-depth checks to projected
  admission depth, replaying idempotent report requests before returning backpressure,
  and adding focused helper tests for oldest queued age and stale-running decisions.
