# Validation Log

## 2026-06-05 Session Continuation Audit

- `git fetch origin`: completed. Local `main` HEAD `53efb49` matches
  `origin/main`.
- `gh pr list --state all --limit 30`: confirmed PRs #12, #13, #14, #15, and
  #16 are merged, and superseded PR #10 is closed.
- `gh run list --branch main --limit 8`: latest `main` run for commit
  `53efb49` passed.
- `git check-ignore -v .omc .omx`: confirmed both local orchestration folders
  are ignored by repo `.gitignore`.
- `python .\scripts\render_project_status.py`: passed and printed all state
  documents after the baseline sync.
- `python .\scripts\check_csv_files.py`: passed across all five register CSV
  files.
- `.\scripts\validate_workspace.ps1`: passed with JSON, CSV, and structural
  invariant checks.
- `.\scripts\verify.ps1`: passed on Python 3.12.10; DB smoke remains locally
  skipped unless `RUN_DB_SMOKE=1` is set after Postgres is available.

## 2026-06-05 DS-002 Source Governance Pass

- `registers/license-reviews/ds-002-fema-nfhl.md`: added a source-governance
  review for FEMA NFHL with federal-work, attribution, caveat, and connector
  gate notes.
- `registers/data_source_registry.csv`: DS-002 changed from unknown/pending to
  approved/reviewed with usage fields populated.
- `db/seeds/002_seed_source_registry.sql`: DS-002 source seed aligned with the
  reviewed registry status so DB bootstrap does not reintroduce unknown values.
- `python .\scripts\check_csv_files.py`: passed across all five register CSV
  files.
- `python .\scripts\check_source_registry.py`: passed across 26 source rows and
  verifies approved registry rows against the SQL source seed.
- `python -m pytest backend\tests\source_registry\test_source_seeds.py -q`:
  passed.
- `.\scripts\validate_workspace.ps1`: passed with JSON, CSV, source registry,
  and structural invariant checks.
- `.\scripts\verify.ps1`: passed on Python 3.12.10; DB smoke remains locally
  skipped unless `RUN_DB_SMOKE=1` is set after Postgres is available.

## 2026-06-05 API Authority Pass

- `scripts/export_openapi.py`: added runtime OpenAPI export to
  `local_artifacts/openapi.generated.json`.
- `backend/tests/api/test_openapi_contract.py`: added path/method parity check
  between FastAPI runtime OpenAPI and `api/openapi_stub.yaml`.
- `api/openapi_stub.yaml`: documented as a curated companion, not the runtime
  authority.
- `python -m pytest backend\tests\api\test_openapi_contract.py -q`: passed.
- `python scripts\export_openapi.py`: passed and wrote the ignored local export.
- `.\scripts\validate_workspace.ps1`: passed with JSON, CSV, source registry,
  and structural invariant checks.
- `.\scripts\verify.ps1`: passed on Python 3.12.10; DB smoke remains locally
  skipped unless `RUN_DB_SMOKE=1` is set after Postgres is available.

## 2026-06-05 Report Review Lifecycle Pass

- `ReportRunContract`: added review status, reviewer, reviewed timestamp, and
  review action audit history.
- `ReportRunService`: added approve, reject, and supersede transitions. New
  report runs default to `needs_review`; rejection and supersession require a
  reason; invalid transitions fail closed.
- `POST /report-runs/{report_run_id}/approve`, `/reject`, and `/supersede`:
  added public API review actions and documented them in the curated OpenAPI
  companion.
- `db/migrations/0002_d_report_review_lifecycle.sql`: added persisted review
  status/action columns and a status check constraint.
- `python -m pytest backend\tests\reports\test_report_service.py
  backend\tests\reports\test_report_repository.py
  backend\tests\api\test_api_scaffold.py
  backend\tests\api\test_openapi_contract.py -q`: passed with one DB smoke
  skip.
- `python -m ruff check` on affected backend and test files: passed.
- `python scripts\export_openapi.py`: passed and wrote the ignored local export.
- `python scripts\render_project_status.py`: passed and printed updated state
  documents.
- `.\scripts\validate_workspace.ps1`: passed with JSON, CSV, source registry,
  and structural invariant checks.
- `.\scripts\verify.ps1`: passed on Python 3.12.10; DB smoke remains locally
  skipped unless `RUN_DB_SMOKE=1` is set after Postgres is available.

## 2026-06-05 Report Request Contract Pass

- `ReportRunContract`: added optional `workspace_id`, `requested_by`, and
  `idempotency_key` request metadata.
- `ReportRunService`: synchronous report creation now reuses an existing report
  for the same workspace-scoped idempotency key; `requested_by` requires an
  explicit workspace.
- `POST /report-runs/jobs` and `GET /report-runs/jobs/{job_id}`: added queued
  report job contract. Queued jobs require idempotency keys and start in
  `queued` status; no worker execution is claimed.
- `db/migrations/0003_d_report_request_scope.sql`: added report-run
  idempotency storage with a workspace-scoped unique index.
- DB-backed report and report-job writes validate workspace/user references
  before flush so invalid scope metadata fails closed.
- `python -m pytest backend\tests\reports\test_report_service.py
  backend\tests\reports\test_report_repository.py
  backend\tests\api\test_api_scaffold.py
  backend\tests\api\test_openapi_contract.py -q`: passed with one DB smoke
  skip.
- `python -m ruff check` on affected backend and test files: passed.
- `python scripts\export_openapi.py`: passed and wrote the ignored local export.
- `.\scripts\verify.ps1`: passed on Python 3.12.10; DB smoke remains locally
  skipped unless `RUN_DB_SMOKE=1` is set after Postgres is available.

## 2026-06-05 Report Job Worker Pass

- `ReportRunJobContract`: added attempts, max attempts, lock owner, lock time,
  and execution timestamps for worker lifecycle visibility.
- `ReportRunJobRepository`: added lease, succeed, fail, and requeue operations
  for in-memory and Postgres-backed report jobs.
- `SqlAlchemyReportRunJobRepository.enqueue`: defaults `not_before` with
  Postgres `now()` when no explicit delay is requested, so newly queued DB jobs
  are immediately eligible for worker leasing under CI DB smoke timing.
- `ReportRunService.execute_next_report_run_job`: leases one queued report job,
  runs the existing report creation path, and records the produced
  `report_run_id`; execution failures mark the job failed with `last_error`.
- `POST /report-runs/jobs/execute-next` and
  `POST /report-runs/jobs/{job_id}/requeue`: added explicit worker/operator
  endpoints. No autonomous scheduler/daemon is claimed.
- `python -m pytest backend\tests\reports\test_report_service.py
  backend\tests\reports\test_report_repository.py
  backend\tests\api\test_api_scaffold.py
  backend\tests\api\test_openapi_contract.py -q`: passed with one DB smoke
  skip.
- `python -m ruff check` on affected backend and test files: passed.
- `python scripts\export_openapi.py`: passed and wrote the ignored local export.
- `python scripts\render_project_status.py`: passed and printed updated state
  documents.
- `.\scripts\validate_workspace.ps1`: passed with JSON, CSV, source registry,
  and structural invariant checks.
- `.\scripts\verify.ps1`: passed on Python 3.12.10; DB smoke remains locally
  skipped unless `RUN_DB_SMOKE=1` is set after Postgres is available.

## 2026-06-05 Approved Dossier Delivery Gate Pass

- `ReportRunService.render_approved_dossier`: serves the rural-land Markdown
  dossier only when the report review status is `approved`; reports still in
  review, rejected reports, and superseded reports fail closed for served
  dossier delivery.
- `GET /report-runs/{report_run_id}/dossier`: added a Markdown delivery
  endpoint for approved report runs and documented it in the curated OpenAPI
  companion.
- `backend/app/reports/dossier.py`: compiles the report contract into the
  rural-land dossier sections, preserving source appendix, red flags, unknowns,
  verification tasks, caveats, and required screening/legal-access caution
  language.
- `backend/tests/api/test_report_runs_db.py`: DB smoke now checks that the
  dossier endpoint blocks unapproved persisted reports and serves approved
  persisted reports. This remains CI-backed locally unless Postgres is
  available.
- `python -m pytest backend\tests\reports\test_report_service.py
  backend\tests\api\test_api_scaffold.py backend\tests\api\test_openapi_contract.py
  backend\tests\api\test_report_runs_db.py -q`: passed with one DB smoke skip.
- `python -m ruff check` on affected backend and test files: passed.
- `python scripts\export_openapi.py`: passed and wrote the ignored local export.
- `python scripts\render_project_status.py`: passed and printed updated state
  documents.
- `.\scripts\verify.ps1`: passed on Python 3.12.10; DB smoke remains locally
  skipped unless `RUN_DB_SMOKE=1` is set after Postgres is available.

## 2026-06-05 Report API Authorization Pass

- `get_request_auth_context`: added trusted `X-Workspace-Id` and `X-User-Id`
  request identity parsing for report API routes; missing headers fail with
  `401`, and malformed UUID headers fail with `422`.
- Report create and report-job submit routes now bind `workspace_id` and
  `requested_by` to the authenticated request headers; body mismatches fail
  closed with `403`.
- Report list, report read, review actions, job access, job requeue, workspace
  job execution, and dossier delivery now enforce the authenticated workspace
  boundary. Cross-workspace reads return not found rather than exposing report
  or job existence.
- Report review actions require `reviewer_id` to match `X-User-Id`.
- Report job leasing now accepts a workspace filter so the API worker endpoint
  only leases jobs in the authenticated workspace.
- `db/seeds/003_seed_demo_identity.sql` seeds deterministic local demo
  workspace/user IDs used by `scripts/demo_mvp.py` for Postgres-backed demos.
- `python -m pytest backend\tests\reports\test_report_service.py
  backend\tests\api\test_api_scaffold.py
  backend\tests\api\test_ingest_report_integration.py
  backend\tests\api\test_report_runs_db.py
  backend\tests\api\test_openapi_contract.py -q`: passed with one DB smoke
  skip.
- `python scripts\export_openapi.py`: passed and wrote the ignored local export.
- `python scripts\render_project_status.py`: passed and printed updated state
  documents.
- `.\scripts\verify.ps1`: passed on Python 3.12.10; DB smoke remains locally
  skipped unless `RUN_DB_SMOKE=1` is set after Postgres is available.

## 2026-06-05 Report Safe-Language Gate Pass

- `RuleEngine.forbidden_language`: exposes the active ruleset's
  forbidden-language list as a read-only policy input for report delivery.
- `assert_safe_report_text`: added a report-owned safe-language guard that
  fails closed when generated report text contains active ruleset forbidden
  phrases.
- `ReportRunService.render_approved_dossier`: now checks the exact Markdown
  dossier text against the active ruleset before serving an approved report.
- `python -m pytest backend\tests\reports\test_safe_language.py
  backend\tests\reports\test_report_service.py
  backend\tests\api\test_api_scaffold.py
  backend\tests\api\test_openapi_contract.py -q`: passed.
- `python -m ruff check` on affected report/ruleset files and tests: passed.
- `python scripts\render_project_status.py`: passed and printed updated state
  documents.
- `.\scripts\verify.ps1`: passed on Python 3.12.10; DB smoke remains locally
  skipped unless `RUN_DB_SMOKE=1` is set after Postgres is available.

## 2026-06-05 Baseline

- `git fetch origin`: completed.
- `git rebase origin/main`: current branch was already up to date.
- `git status --short --branch`: clean on `main...origin/main` before readiness
  edits.
- `.\scripts\verify.ps1`: passed on Python 3.12.10.
- In-memory API demo: passed through health, fixture source/area seed, flood,
  zoning, access connector runs, report creation, connector review approval, and
  report listing.
- GitHub Actions `main` run `27004780227` for commit `0745917`: passed for
  both `verify` and `db-verify`.

## Local Caveat

Local Docker is not installed on this machine, so local DB smoke is not
available here. DB verification is currently CI-backed unless Docker/Postgres is
installed locally.

## 2026-06-05 Readiness Artifact Pass

- `python .\scripts\render_project_status.py`: passed and printed all three
  state documents.
- `python .\scripts\check_csv_files.py`: passed across all five register CSV
  files.
- `.\scripts\validate_workspace.ps1`: passed with `MILESTONE_MAP.md`,
  `LANE_OWNERSHIP.md`, `docs/IMPLEMENTATION_READINESS.md`, and `state/*.md`
  included in required workspace files, plus JSON and CSV checks.
- `.\scripts\verify.ps1`: passed after readiness artifact updates.
- POSIX wrapper note: `bash` and `sh` are not available in this Windows shell,
  so `scripts/validate_workspace.sh` was reviewed and validate-gated by file
  presence but not executed locally.

## 2026-06-05 Verifier Fix Pass

- Read-only verifier requested three fixes: normalize the Level 2 milestone
  status to the defined legend, add `registers/data_source_registry.csv` to
  Lane A ownership, and explicitly require `scripts/check_csv_files.py` in the
  workspace gate.
- All requested fixes were applied. Verifier re-check approved the corrected
  state and found no remaining required fixes.

## 2026-06-04 Sync and Registry Gap Pass

- `git fetch origin`: completed. Local `main` HEAD `937b033` matches `origin/main`.
- `git status --short`: clean on `main`.
- `.\scripts\verify.ps1`: passed — all tests green, lint clean, typecheck clean.
- `python scripts/check_csv_files.py`: passed across all five register CSV files.
- Gap addressed: `registers/data_source_registry.csv` lacked a row for the
  fixture source UUID (`55555555-5555-4555-8555-555555555555`). Added
  DS-FIXTURE-001 row with approved internal fixture status.
- `state/PROJECT_STATE.md` baseline updated to current HEAD `937b033` and What
  Works section updated to reflect connector review actions, report list endpoint,
  and fixture registry entry.
