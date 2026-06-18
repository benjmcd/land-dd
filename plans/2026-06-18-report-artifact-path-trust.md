# Report Artifact Path Trust

## Goal
Ensure DB-backed report artifact delivery only reads persisted report JSON from the
configured object-store root. A stored report `machine_json_uri` or `output_uri` must
not cause the API to read arbitrary local files outside that root.

## Non-goals
- No schema changes.
- No object-storage provider integration.
- No change to the in-memory artifact fallback behavior.
- No report serialization contract changes.
- No new report review or auth model.

## Current state
- `SqlAlchemyReportRunRepository` writes artifacts to
  `OBJECT_STORE_ROOT / {report_run_id}.json` and stores that path in
  `reports.report_runs.output_uri`, `reports.report_runs.machine_json_uri`, and
  `artifact_metadata`.
- `GET /report-runs/{report_run_id}/artifact` in `backend/app/api/reports.py` reads
  `report.artifact_metadata["machine_json_uri"]` or `report.output_uri` directly with
  `Path(str(artifact_uri))`.
- Existing DB-gated tests prove the endpoint serves the persisted file, but they do not
  prove the path is under `OBJECT_STORE_ROOT` or that tampered DB paths fail closed.
- `OBJECT_STORE_ROOT` reaches DB services through `app.state.object_store_root` and
  `create_db_api_services(..., object_store_root=...)`.

## Proposed design
Add a small report-artifact path guard near report persistence/delivery:

- Canonical authority: configured `OBJECT_STORE_ROOT`.
- Accepted artifact path: resolved path must be inside the resolved object-store root.
- Expected persisted file name remains `{report_run_id}.json`.
- If a DB-backed report carries an out-of-root artifact URI, artifact delivery should
  fail closed instead of reading the file. The endpoint should not fall back to
  serializing the in-memory contract for a suspicious persisted path, because that would
  hide a corrupted/tampered persisted artifact pointer.
- Existing in-memory reports may still serialize from the contract when no persisted
  artifact URI is present.

Rejected alternatives:
- Trusting the DB path because report rows are app-owned is too weak for a production
  artifact boundary; DB contents and migrations are still attack/corruption surfaces.
- Replacing file paths with opaque object-store IDs is broader than needed for this
  slice.
- Reading then comparing artifact content is too late; path authorization must happen
  before filesystem access.

## Bottom-up sequence
1. Add a focused DB-gated regression that tampers an approved report row to point
   outside `OBJECT_STORE_ROOT` and proves `/report-runs/{id}/artifact` does not read it
   or silently fall back.
2. Add a small path-resolution helper for report artifacts that resolves root and
   candidate paths and checks `Path.is_relative_to`.
3. Use the helper in SQLAlchemy report artifact reads and API artifact delivery.
4. Preserve existing persisted-artifact success tests and in-memory artifact tests.
5. Run focused report-export tests, ruff/mypy on touched files, and the default verify
   gate; run DB smoke if the change touches DB-backed artifact behavior.

## Files likely to change
| File | Expected change |
|---|---|
| `backend/app/reports/report_repo.py` | Add or use object-store-root path guard for DB artifact reads |
| `backend/app/api/reports.py` | Use guarded artifact path before reading persisted artifact file |
| `backend/tests/api/test_report_export.py` | Add DB-gated out-of-root/tampered URI regression |
| `plans/README.md` | Route active plan to this slice |
| `tasks/task_queue.yaml` | Route active plan to this slice |
| `state/PROJECT_STATE.md` | Record current checkpoint/active plan if behavior lands |
| `state/WORKLOG.md` | Record implementation note |
| `state/VALIDATION_LOG.md` | Record validation evidence |

## Tests / verification
Focused:
```powershell
cd backend
$env:RUN_DB_SMOKE='1'; python -m pytest -q .\tests\api\test_report_export.py -k "artifact"
python -m pytest -q .\tests\api\test_report_export.py -k "artifact and not db"
python -m ruff check .\app\api\reports.py .\app\reports\report_repo.py .\tests\api\test_report_export.py
python -m mypy .\app\api\reports.py .\app\reports\report_repo.py .\tests\api\test_report_export.py
```

Handoff:
```powershell
.\scripts\verify.ps1
```

DB-backed handoff when Docker/Postgres is available:
```powershell
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

## Risks and blockers
- Existing tests sometimes inspect artifact paths from response bodies; keep the stored
  path stable for valid in-root artifacts.
- Do not make in-memory report artifact delivery depend on `OBJECT_STORE_ROOT`.
- If `OBJECT_STORE_ROOT` is relative, resolve it consistently against process cwd.
- Any suspicious persisted path must fail closed before file read; falling back to
  serialized contract would mask the issue.

## Decision log
- 2026-06-18: Choose artifact-path trust as the next slice because it is a concrete
  production security boundary with a narrow DB-backed test surface.
- 2026-06-18: Treat `OBJECT_STORE_ROOT` as the canonical artifact file boundary.

## Progress log
- 2026-06-18: Created plan after PR #60 merged and live `origin/main` reached
  `30914c8`.
- 2026-06-18: Implemented object-store-root path confinement in
  `SqlAlchemyReportRunRepository`, removed the artifact endpoint's second path
  dereference, and added DB-gated tamper coverage.
- 2026-06-18: Added a report API helper so path trust-boundary failures from DB-backed
  report reloads surface as `409` across report API reads.
- 2026-06-18: Added workspace-scoped repository/service report reads so authenticated
  wrong-workspace requests return `404` before artifact files are loaded.
- 2026-06-18: Added resolver-level coverage for out-of-root and wrong-filename
  artifact paths, plus DB-backed regressions for wrong-workspace concealment, wrong
  filenames, out-of-root paths, and artifact body identity mismatch.
- 2026-06-18: Focused artifact tests, report repository/export tests, ruff, mypy,
  default `.\scripts\verify.ps1`, and DB-enabled `.\scripts\verify.ps1` passed on
  isolated Postgres port `55449`.
