# Validation Log

Record commands, results, and residual risk.

## 2026-06-04 Connector CON-033 fixture retrieval name quality

**Commands run:**

```powershell
cd backend
python -m pytest -q tests/connectors/test_fixture_quality.py
ruff check app/connectors/fixture_quality.py tests/connectors/test_fixture_quality.py
mypy app/connectors/fixture_quality.py tests/connectors/test_fixture_quality.py
cd ..
git diff --check
.\scripts\verify.ps1
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend
python -m pytest --collect-only
```

**Results:**

- Focused fixture-quality tests: 15 passed.
- Focused connector ruff: clean.
- Focused connector mypy: clean over 2 source files.
- Whitespace check: clean.
- Default Windows PowerShell verification passed with 367 backend tests collected, lint clean, mypy clean over 123 source files, and DB smoke skipped by default.
- DB-enabled Windows PowerShell verification passed with 367 backend tests collected/passing, lint clean, mypy clean over 123 source files, migrations/seeds applied, and DB smoke passed.
- Backend collection: 367 tests collected.

**Residual risk:**

- CON-033 is connector-local fixture quality only. It does not add API routes, OpenAPI changes, DB schema changes, queue behavior, connector runtime behavior, live I/O, hook config, POSIX scripts, durable evidence-row `ingest_run_id` linkage, or Lane A/B/C/D module changes outside connector quality. Connector review route/OpenAPI implementation remains deferred while Session 1's Lane C evidence-linkage/OpenAPI branch is parked.

## 2026-06-04 Connector CON-032 fixture evidence domain quality

**Commands run:**

```powershell
cd backend
python -m pytest -q tests/connectors/test_fixture_quality.py
ruff check app/connectors/fixture_quality.py tests/connectors/test_fixture_quality.py
mypy app/connectors/fixture_quality.py tests/connectors/test_fixture_quality.py
cd ..
git diff --check
.\scripts\verify.ps1
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend
python -m pytest --collect-only
```

**Results:**

- Focused fixture-quality tests: 14 passed.
- Focused connector ruff: clean.
- Focused connector mypy: clean over 2 source files.
- Whitespace check: clean.
- Default Windows PowerShell verification passed with 366 backend tests collected, lint clean, mypy clean over 123 source files, and DB smoke skipped by default.
- DB-enabled Windows PowerShell verification passed with 366 backend tests collected/passing, lint clean, mypy clean over 123 source files, migrations/seeds applied, and DB smoke passed.
- Backend collection: 366 tests collected.

**Residual risk:**

- CON-032 is connector-local fixture quality only. It does not add API routes, OpenAPI changes, DB schema changes, queue behavior, connector runtime behavior, live I/O, hook config, POSIX scripts, durable evidence-row `ingest_run_id` linkage, or Lane A/B/C/D module changes outside connector quality. Connector review route/OpenAPI implementation remains deferred while Session 1's Lane C evidence-linkage/OpenAPI branch is parked.

## 2026-06-04 Connector CON-031 succeeded-retrieval failure-metric quality

**Commands run:**

```powershell
cd backend
python -m pytest -q tests/connectors/test_fixture_quality.py
ruff check app/connectors/fixture_quality.py tests/connectors/test_fixture_quality.py
mypy app/connectors/fixture_quality.py tests/connectors/test_fixture_quality.py
cd ..
git diff --check
.\scripts\verify.ps1
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend
python -m pytest --collect-only
```

**Results:**

- Focused fixture-quality tests: 13 passed.
- Focused connector ruff: clean.
- Focused connector mypy: clean over 2 source files.
- Whitespace check: clean.
- Default Windows PowerShell verification passed with 365 backend tests collected, lint clean, mypy clean over 123 source files, and DB smoke skipped by default.
- DB-enabled Windows PowerShell verification passed with 365 backend tests collected/passing, lint clean, mypy clean over 123 source files, migrations/seeds applied, and DB smoke passed.

**Residual risk:**

- CON-031 is connector-local fixture quality only. It does not add API routes, OpenAPI changes, DB schema changes, queue behavior, connector runtime behavior, live I/O, hook config, POSIX scripts, durable evidence-row `ingest_run_id` linkage, or Lane A/B/C/D module changes outside connector quality. Connector review route/OpenAPI implementation remains deferred while Session 1's Lane C evidence-linkage/OpenAPI branch is parked.

## 2026-06-04 Connector CON-030 retrieval failure-reason metric quality

**Commands run:**

```powershell
cd backend
py -3.12 -m pytest -q tests/connectors/test_fixture_quality.py
ruff check app/connectors/fixture_quality.py tests/connectors/test_fixture_quality.py
mypy app/connectors/fixture_quality.py tests/connectors/test_fixture_quality.py
cd ..
git diff --check
.\scripts\verify.ps1
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend
py -3.12 -m pytest --collect-only
```

**Results:**

- Focused fixture-quality tests: 13 passed.
- Focused connector ruff: clean.
- Focused connector mypy: clean over 2 source files.
- Whitespace check: clean.
- Default Windows PowerShell verification passed with 365 backend tests collected, lint clean, mypy clean over 123 source files, and DB smoke skipped by default.
- DB-enabled Windows PowerShell verification passed with 365 backend tests collected/passing, lint clean, mypy clean over 123 source files, migrations/seeds applied, and DB smoke passed.

**Residual risk:**

- CON-030 is connector-local fixture quality only. It does not add API routes, OpenAPI changes, DB schema changes, queue behavior, connector runtime behavior, live I/O, hook config, POSIX scripts, durable evidence-row `ingest_run_id` linkage, or Lane A/B/C/D module changes outside connector quality. Connector review route/OpenAPI implementation remains deferred while Session 1's Lane C evidence-linkage/OpenAPI branch is parked.

## 2026-06-04 Connector CON-029 source-failure reason consistency

**Commands run:**

```powershell
cd backend
py -3.12 -m pytest -q tests/connectors/test_fixture_quality.py
ruff check app/connectors/fixture_quality.py tests/connectors/test_fixture_quality.py
mypy app/connectors/fixture_quality.py tests/connectors/test_fixture_quality.py
cd ..
git diff --check
.\scripts\verify.ps1
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend
py -3.12 -m pytest --collect-only
```

**Results:**

- Focused fixture-quality tests: 13 passed.
- Focused connector ruff: clean.
- Focused connector mypy: clean over 2 source files.
- Whitespace check: clean.
- Default Windows PowerShell verification passed with 365 backend tests collected, lint clean, mypy clean over 123 source files, and DB smoke skipped by default.
- DB-enabled Windows PowerShell verification passed with 365 backend tests collected/passing, lint clean, mypy clean over 123 source files, migrations/seeds applied, and DB smoke passed.

**Residual risk:**

- CON-029 is connector-local fixture quality only. It does not add API routes, OpenAPI changes, DB schema changes, queue behavior, connector runtime behavior, live I/O, hook config, POSIX scripts, durable evidence-row `ingest_run_id` linkage, or Lane A/B/C/D module changes outside connector quality. Connector review route/OpenAPI implementation remains deferred while Session 1's Lane C evidence-linkage/OpenAPI branch is parked.

## 2026-06-04 Connector CON-028 source-failure payload type quality

**Commands run:**

```powershell
cd backend
py -3.12 -m pytest -q tests/connectors/test_fixture_quality.py
ruff check app/connectors/fixture_quality.py tests/connectors/test_fixture_quality.py
mypy app/connectors/fixture_quality.py tests/connectors/test_fixture_quality.py
cd ..
git diff --check
.\scripts\verify.ps1
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend
py -3.12 -m pytest --collect-only
```

**Results:**

- Focused fixture-quality tests: 12 passed.
- Focused connector ruff: clean.
- Focused connector mypy: clean over 2 source files.
- Whitespace check: clean.
- Default Windows PowerShell verification passed with 364 backend tests collected, lint clean, mypy clean over 123 source files, and DB smoke skipped by default.
- DB-enabled Windows PowerShell verification passed with 364 backend tests collected/passing, lint clean, mypy clean over 123 source files, migrations/seeds applied, and DB smoke passed.

**Residual risk:**

- CON-028 is connector-local fixture quality only. It does not add API routes, OpenAPI changes, DB schema changes, queue behavior, connector runtime behavior, live I/O, hook config, POSIX scripts, durable evidence-row `ingest_run_id` linkage, or Lane A/B/C/D module changes outside connector quality. Connector review route/OpenAPI implementation remains deferred while Session 1's Lane C evidence-linkage/OpenAPI branch is parked.

## 2026-06-04 Lane D TD-084 job schema boundary

**Commands run:**

```powershell
git diff --check
.\scripts\verify.ps1
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

**Results:**

- Whitespace check: clean.
- Default Windows PowerShell verification passed with 363 backend tests collected, lint clean, mypy clean over 123 source files, and DB smoke skipped by default.
- DB-enabled Windows PowerShell verification passed with 363 backend tests collected/passing, lint clean, mypy clean over 123 source files, migrations/seeds applied, and DB smoke passed.

**Residual risk:**

- TD-084 is a boundary decision only. It does not edit `schemas/job_schema.json`, add schema parity tests, add API routes, change OpenAPI, change queue code, add migrations, change connector runtime behavior, use live I/O, alter hook config, invoke POSIX scripts, add durable evidence-row `ingest_run_id` linkage, or change Lane A/B/C modules. Future job schema work still must choose `jobs.job_queue`, `ConnectorReviewQueueItem`, or a new `JobContract` as authority before schema/runtime changes.

## 2026-06-04 Connector CON-027 fixture retrieval metric quality

**Commands run:**

```powershell
cd backend
py -3.12 -m pytest -q tests/connectors/test_fixture_quality.py
ruff check app/connectors/fixture_quality.py tests/connectors/test_fixture_quality.py
mypy app/connectors/fixture_quality.py tests/connectors/test_fixture_quality.py
cd ..
git diff --check
.\scripts\verify.ps1
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend
py -3.12 -m pytest --collect-only
```

**Results:**

- Focused fixture-quality tests: 11 passed.
- Focused connector ruff: clean.
- Focused connector mypy: clean over 2 source files.
- Whitespace check: clean.
- Default Windows PowerShell verification passed with 363 backend tests collected, lint clean, mypy clean over 123 source files, and DB smoke skipped by default.
- DB-enabled Windows PowerShell verification passed with 363 backend tests collected/passing, lint clean, mypy clean over 123 source files, migrations/seeds applied, and DB smoke passed.

**Residual risk:**

- CON-027 is connector-local fixture quality only. It does not add API routes, OpenAPI changes, DB schema changes, queue behavior, connector runtime behavior, live I/O, hook config, POSIX scripts, durable evidence-row `ingest_run_id` linkage, or Lane A/B/C/D module changes outside connector quality. Connector review route/OpenAPI implementation remains deferred while Session 1's Lane C evidence-linkage/OpenAPI branch is parked.

## 2026-06-04 Lane D TD-083 report validation metadata

**Commands run:**

```powershell
cd backend
py -3.12 -m pytest -q tests/reports/test_report_schema_contract.py tests/reports/test_report_service.py tests/reports/test_report_regression.py
ruff check app/reports tests/reports/test_report_schema_contract.py tests/reports/test_report_service.py tests/reports/test_report_regression.py
mypy app/reports tests/reports/test_report_schema_contract.py tests/reports/test_report_service.py tests/reports/test_report_regression.py
cd ..
git diff --check
.\scripts\verify.ps1
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend
py -3.12 -m pytest --collect-only
```

**Results:**

- Focused report metadata tests: 11 passed.
- Focused report ruff: clean.
- Focused report mypy: clean over 8 source files.
- Whitespace check: clean.
- Default Windows PowerShell verification passed with 362 backend tests collected, lint clean, mypy clean over 123 source files, and DB smoke skipped by default.
- DB-enabled Windows PowerShell verification passed with 362 backend tests collected/passing, lint clean, mypy clean over 123 source files, migrations/seeds applied, and DB smoke passed.

**Residual risk:**

- TD-083 records report contract/profile and ruleset identity only. It does not claim that a verification command was run or passed inside report artifacts. It does not add API routes, OpenAPI changes, DB schema changes, runtime JSON Schema validation, queue behavior, connector runtime behavior, live I/O, hook config, POSIX scripts, durable evidence-row `ingest_run_id` linkage, or Lane A/B/C implementation changes. Connector review route/OpenAPI implementation remains deferred while Session 1's Lane C evidence-linkage/OpenAPI branch is parked.

## 2026-06-04 Connector CON-026 review action route subset

**Commands run:**

```powershell
.\scripts\verify.ps1
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
git diff --check
```

**Results:**

- Whitespace check: clean.
- Default Windows PowerShell verification passed with 362 backend tests collected/passing, lint clean, mypy clean over 123 source files, and DB smoke skipped by default.
- DB-enabled Windows PowerShell verification passed with 362 backend tests collected/passing, lint clean, mypy clean over 123 source files, migrations/seeds applied, and DB smoke passed.

**Residual risk:**

- CON-026 is a route-subset decision only. It does not register API routes, change OpenAPI, mutate queue rows, add repository methods, add production auth, persist reviewer ownership, persist reviewer action history, change connector runtime behavior, change evidence/claim/report behavior, add schemas, add migrations, use live I/O, alter hook config, or invoke POSIX scripts. Route implementation and OpenAPI refresh remain a future coordinated pass after Session 1's Lane C evidence-linkage/OpenAPI branch reaches a clean merge point.

## 2026-06-04 Connector CON-025 reviewer principal boundary

**Commands run:**

```powershell
cd backend
py -3.12 -m pytest -q tests/api/test_reviewer_auth.py
ruff check app/api/reviewer_auth.py tests/api/test_reviewer_auth.py
mypy app/api/reviewer_auth.py tests/api/test_reviewer_auth.py
py -3.12 -m pytest --collect-only -q
cd ..
git diff --check
.\scripts\verify.ps1
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

**Results:**

- Focused reviewer auth tests: 11 passed.
- Focused ruff: clean.
- Focused mypy: clean over 2 source files.
- Backend collection: 362 tests.
- Whitespace check: clean.
- Default Windows PowerShell verification passed with 362 backend tests collected/passing, lint clean, mypy clean over 123 source files, and DB smoke skipped by default.
- DB-enabled Windows PowerShell verification passed with 362 backend tests collected/passing, lint clean, mypy clean over 123 source files, migrations/seeds applied, and DB smoke passed.

**Residual risk:**

- CON-025 adds a tested local service-account reviewer principal dependency only. It does not register API routes, change OpenAPI, mutate queue rows, add settings/secrets, add production auth, persist reviewer ownership, persist reviewer action history, change connector runtime behavior, change evidence/claim/report behavior, add schemas, add migrations, use live I/O, alter hook config, or invoke POSIX scripts. Future mutation-route work must still compare request reviewer identity to the authenticated principal and avoid claiming durable action history until storage is accepted.

## 2026-06-04 Connector CON-024 review action API auth blocker

**Commands run:**

```powershell
git diff --check
.\scripts\verify.ps1
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

**Results:**

- Whitespace check: clean.
- Default Windows PowerShell verification passed with 351 backend tests collected/passing, lint clean, mypy clean over 121 source files, and DB smoke skipped by default.
- DB-enabled Windows PowerShell verification passed with 351 backend tests collected/passing, lint clean, mypy clean over 121 source files, migrations/seeds applied, and DB smoke passed.

**Residual risk:**

- CON-024 is an implementation-blocker decision only. It does not add API routes, OpenAPI changes, queue code, repository methods, schemas, migrations, connector runtime behavior, live I/O, hook config, POSIX scripts, evidence behavior, claim behavior, or report behavior. Connector review mutation routes remain blocked until an authenticated reviewer/operator principal dependency or accepted service-account delegation rule is added and tested.

## 2026-06-04 Lane D TD-082 report metadata extension boundary

**Commands run:**

```powershell
.\scripts\verify.ps1
```

**Results:**

- Pass. Full Windows PowerShell verification passed with 351 backend tests collected/passing, lint clean, mypy clean over 121 source files, migrations/seeds applied, and DB smoke passed.

**Residual risk:**

- TD-082 is planning-only. It does not add report runtime behavior, API behavior, OpenAPI changes, schema changes, migrations, queue behavior, live I/O, hook config, POSIX scripts, or durable `ingest_run_id` evidence-row linkage. Job schema, API mutation/workflow implementation, rendering/export implementation, and durable evidence-row retrieval lineage remain separate future work.

## 2026-06-04 Connector CON-023 fixture evidence provenance quality

**Commands run:**

```powershell
cd backend
py -3.12 -m pytest -q tests/connectors/test_fixture_quality.py
ruff check app/connectors/fixture_quality.py tests/connectors/test_fixture_quality.py
mypy app/connectors/fixture_quality.py tests/connectors/test_fixture_quality.py
cd ..
.\scripts\verify.ps1
```

**Results:**

- Focused fixture-quality tests: 10 passed.
- Focused ruff: clean.
- Focused mypy: clean over 2 source files.
- Full Windows PowerShell verification passed with 351 backend tests collected/passing, lint clean, mypy clean over 121 source files, migrations/seeds applied, and DB smoke passed.

**Residual risk:**

- CON-023 is connector-local fixture-quality validation only. It does not add API mutation, auth/reviewer enforcement, durable queue behavior, repository methods, source/evidence/claim/report behavior, schema changes, migrations, live I/O, future report metadata extensions, or durable `ingest_run_id` evidence-row linkage.

## 2026-06-04 TA-080 plus CON-022 merge reconciliation

**Commands run:**

```powershell
.\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
```

**Results:**

- Pass. Full Windows PowerShell verification passed with backend tests, lint, mypy, migrations/seeds, and DB smoke.
- Test collection confirmed 350 backend tests.
- Mypy checked 121 source files with no issues.

**Residual risk:**

- Merge reconciliation preserved TA-080 and CON-022 records only. Human-review action API implementation, auth/reviewer enforcement, retry/cancel mutation surfacing, job schema, future report metadata extensions, live connectors, and durable `ingest_run_id` evidence-row linkage remain separate future work.

## 2026-06-04 Connector CON-022 human-review API semantics

**Commands run:**

```powershell
.\scripts\verify.ps1
cd backend; python -m pytest --collect-only
```

**Results:**

- Pass. Full Windows PowerShell verification passed with backend tests, lint, mypy, migrations/seeds, and DB smoke.
- Test collection confirmed 344 backend tests.
- Mypy checked 120 source files with no issues.

**Residual risk:**

- CON-022 is planning-only. Human-review action API implementation, auth/reviewer enforcement, reviewer-ownership persistence, new queue transition substrate, retry/cancel mutation surfacing, workers, dashboards, source provenance-family schemas, job schema, future report metadata extensions, live connectors, and durable `ingest_run_id` evidence-row linkage remain separate future work.

## 2026-06-04 Lane A TA-080 source provenance-family schema parity

**Commands run:**

```powershell
cd backend
py -3.12 -m pytest -q tests/source_registry/test_source_provenance_schema_contract.py
ruff check tests/source_registry/test_source_provenance_schema_contract.py
mypy tests/source_registry/test_source_provenance_schema_contract.py
py -3.12 -m pytest --collect-only -q
cd ..
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

**Results:**

- Source provenance-family schema parity tests: 6 passed.
- Focused ruff: clean.
- Focused mypy: clean over 1 source file.
- Backend collection includes 350 tests.
- Full DB-enabled PowerShell verification: ok; 350 backend tests pass, lint clean, mypy clean over 121 source files, migrations/seeds apply, and DB smoke passes.

**Residual risk:**

- TA-080 is schema-contract parity only. It does not add runtime JSON Schema validation, DB migrations, connector behavior, queue semantics, live I/O, future report metadata extensions, human-review API routes, or durable `ingest_run_id` evidence-row linkage.

## 2026-06-04 Connector CON-021 human-review action semantics

**Commands run:**

```powershell
.\scripts\verify.ps1
```

**Results:**

- Full DB-enabled PowerShell verification: ok; 344 backend tests pass; lint clean; mypy clean over 120 source files; migrations/seeds apply; DB smoke passes.
- Backend collection includes 344 tests.

**Residual risk:**

- CON-021 is planning-only. Human-review action API routes, reviewer identity/auth handling, retry/cancel mutation surfacing, workers, dashboards, source provenance-family schemas, job schema, future report metadata extensions, live connectors, and durable `ingest_run_id` evidence-row linkage remain separate future work.

## 2026-06-04 Combined TD-081 plus TD-090 verification

**Commands run:**

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/test_planning_pack_schema_copies.py
ruff check tests/test_planning_pack_schema_copies.py
mypy tests/test_planning_pack_schema_copies.py
py -3.12 -m pytest --collect-only
Set-Location ..
```

**Results:**

- Planning-pack schema/OpenAPI parity tests: 2 passed.
- Focused planning-pack ruff: clean.
- Focused planning-pack mypy: clean over 1 source file.
- Backend collection includes 344 tests after rebasing TD-090 onto TD-081.
- Full DB-enabled PowerShell verification: ok; 344 backend tests pass; lint clean; mypy clean over 120 source files; migrations/seeds apply; DB smoke passes.

**Residual risk:**

- TD-081 and TD-090 together resolve stable generated report manifest metadata keys and planning-pack OpenAPI for the current local FastAPI app. Source provenance-family schemas, job schema, future report metadata extensions, live connectors, API mutation routes, generated clients, and durable `ingest_run_id` evidence-row linkage remain separate future work.

## 2026-06-04 Lane D TD-090 planning-pack OpenAPI refresh

**Commands run:**

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/test_planning_pack_schema_copies.py
ruff check tests/test_planning_pack_schema_copies.py
mypy tests/test_planning_pack_schema_copies.py
py -3.12 -m pytest --collect-only
Set-Location ..
```

**Results:**

- Planning-pack schema/OpenAPI parity tests: 2 passed.
- Focused planning-pack ruff: clean.
- Focused planning-pack mypy: clean over 1 source file.
- Backend collection includes 342 tests.
- Full DB-enabled PowerShell verification: ok; 342 backend tests pass; lint clean; mypy clean over 120 source files; migrations/seeds apply; DB smoke passes.

**Residual risk:**

- TD-090 resolves the planning-pack OpenAPI reference for the current local FastAPI app only. It does not add API behavior, API mutation routes, generated clients, live connectors, schemas, migrations, source provenance-family schemas, job schema changes, new report metadata extensions, or durable `ingest_run_id` evidence-row linkage.

## 2026-06-04 Lane D TD-081 report manifest metadata schema

**Commands run:**

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/reports/test_report_schema_contract.py tests/reports/test_report_contracts.py
ruff check tests/reports/test_report_schema_contract.py
mypy tests/reports/test_report_schema_contract.py
py -3.12 -m pytest -q tests/reports tests/api
ruff check app/reports app/api app/main.py tests/reports tests/api
mypy app/reports app/api app/main.py tests/reports tests/api
Set-Location ..
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
Set-Location backend
py -3.12 -m pytest --collect-only -q
```

**Results:**

- Focused report schema/default contract tests: 7 passed.
- Focused report schema ruff: clean.
- Focused report schema mypy: clean over 1 source file.
- Broader report/API tests: 31 passed, 4 skipped.
- Broader report/API ruff: clean.
- Broader report/API mypy: clean over 27 source/test files.
- Full DB-enabled PowerShell verification: ok; 343 backend tests pass; lint clean; mypy clean over 120 source files; migrations/seeds apply; DB smoke passes.
- Backend collection includes 343 tests, including 6 report schema-contract tests.

**Residual risk:**

- TD-081 tightens stable generated report `source_manifest`, `source_details`, `artifact_metadata`, and `cost_metrics` keys only. It does not add runtime JSON Schema validation, API behavior changes, DB migrations, connector behavior, source provenance-family schemas, job schema, live connectors, or durable `ingest_run_id` evidence-row linkage. Planning-pack OpenAPI is resolved separately by TD-090.
- Nested report metadata maps still allow extension fields by design; future extension keys need their own decision before being treated as stable.

## 2026-06-04 Combined CON-020 plus TD-080 root verification

**Commands run:**

```powershell
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
Set-Location backend
py -3.12 -m pytest --collect-only -q
```

**Results:**

- Full DB-enabled PowerShell verification: ok; 341 backend tests pass; lint clean; mypy clean over 120 source files; migrations/seeds apply; DB smoke passes.
- Backend collection includes 341 tests.

**Residual risk:**

- CON-020 remains fixture-local connector quality coverage only.
- TD-080 resolves `schemas/report_run_schema.json` for serialized `ReportRunContract` only. TD-081 later tightens stable generated report manifest metadata keys, and TD-090 later resolves planning-pack OpenAPI. Source provenance-family schemas, job schema, live connectors, and durable `ingest_run_id` evidence-row linkage remain separate future work.

## 2026-06-04 CON-020 connector fixture identity and timing quality

**Commands run:**

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/connectors/test_fixture_quality.py
ruff check app/connectors/fixture_quality.py tests/connectors/test_fixture_quality.py
mypy app/connectors/fixture_quality.py tests/connectors/test_fixture_quality.py
py -3.12 -m pytest -q tests/connectors -rA
ruff check app/connectors tests/connectors
mypy app/connectors tests/connectors
Set-Location ..
```

**Results:**

- Focused fixture-quality tests: 9 passed.
- Targeted ruff: clean.
- Targeted mypy: clean over 2 source/test files.
- Broader connector tests with DB smoke skipped by default: 51 passed, 5 skipped.
- Connector ruff: clean.
- Connector mypy: clean over 21 source/test files.
- Full DB-enabled PowerShell verification: ok; 337 backend tests pass; lint clean; mypy clean over 119 source files; migrations/seeds apply; DB smoke passes.
- Backend collection includes 337 tests.

**Residual risk:**

- CON-020 is fixture-local quality coverage only. Durable `ingest_run_id` evidence-row linkage, source provenance-family schemas, report-run schema, API mutation routes, and live connector behavior remain separate planned work.

## 2026-06-04 Lane D TD-080 report-run schema contract

**Commands run:**

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/reports/test_report_schema_contract.py tests/reports/test_report_contracts.py
py -3.12 -m pytest --collect-only -q tests/reports tests/api
ruff check tests/reports/test_report_schema_contract.py
mypy tests/reports/test_report_schema_contract.py
Set-Location ..
git diff --check
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
Set-Location backend
py -3.12 -m pytest --collect-only -q
```

**Results:**

- Focused report schema/default contract tests: 5 passed.
- Lane D report/API collection: 33 tests.
- Focused report schema ruff: clean.
- Focused report schema mypy: clean over 1 source file.
- Whitespace check: clean.
- Full DB-enabled PowerShell verification: ok; 339 backend tests pass; lint clean; mypy clean over 120 source files; migrations/seeds apply; DB smoke passes.
- Backend collection includes 339 tests, including 4 report schema-contract tests.

**Residual risk:**

- TD-080 resolves `schemas/report_run_schema.json` for serialized `ReportRunContract` only. TD-081 later tightens stable generated report manifest metadata keys, and planning-pack OpenAPI is resolved by TD-090. Source provenance-family schemas, job schema, live connectors, and durable `ingest_run_id` evidence-row linkage remain separate future work.

## 2026-06-04 CON-019 connector source-failure evidence ID adoption

**Commands run:**

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/connectors/test_evidence_ingestion_adapter.py tests/connectors/test_fixture_workflow.py tests/connectors/test_public_wiring.py
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/connectors/test_public_wiring.py::test_db_backed_public_lane_service_fixture_source_failure_is_idempotent
ruff check app/connectors/evidence_ingestion.py tests/connectors/test_evidence_ingestion_adapter.py tests/connectors/test_fixture_workflow.py tests/connectors/test_public_wiring.py tests/connectors/test_review_packet.py tests/connectors/test_review_handoff.py tests/connectors/test_review_queue.py tests/connectors/test_review_status.py tests/api/test_connector_review_status.py tests/api/test_connector_review_queue_db.py
mypy app/connectors/evidence_ingestion.py tests/connectors/test_evidence_ingestion_adapter.py tests/connectors/test_fixture_workflow.py tests/connectors/test_public_wiring.py tests/connectors/test_review_packet.py tests/connectors/test_review_handoff.py tests/connectors/test_review_queue.py tests/connectors/test_review_status.py tests/api/test_connector_review_status.py tests/api/test_connector_review_queue_db.py
py -3.12 -m pytest -q tests/connectors tests/api -rA
ruff check app/connectors app/api app/main.py tests/connectors tests/api
mypy app/connectors app/api app/main.py tests/connectors tests/api
Set-Location ..
$rootArtifacts = (Resolve-Path ..\..\local_artifacts).Path
$env:PATH = "$rootArtifacts;$env:PATH"; $env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
Set-Location backend
py -3.12 -m pytest --collect-only -q
```

**Results:**

- Focused connector adoption tests with DB smoke skipped by default: 15 passed, 2 skipped.
- DB-backed public wiring source-failure ID test: 1 passed.
- Targeted ruff: clean.
- Targeted mypy: clean over 10 source/test files.
- Broader connector/API tests with DB smoke skipped by default: 64 passed, 8 skipped.
- Broader connector/API ruff: clean.
- Broader connector/API mypy: clean over 36 source/test files.
- Full DB-enabled PowerShell verification after merging root `ca10f85`: ok; 335 backend tests pass; lint clean; mypy clean over 119 source files; migrations/seeds apply; DB smoke passes.
- Backend collection includes 335 tests.

**Residual risk:**

- CON-019 preserves deterministic source-failure evidence IDs through connector ingestion/public Lane C service wiring only. Durable `ingest_run_id` evidence-row linkage remains a future coordinated Lane C/schema pass.

## 2026-06-04 Lane A TA-070 source schema-contract parity

**Commands run:**

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/source_registry/test_source_schema_contract.py
py -3.12 -m pytest --collect-only -q tests/source_registry
py -3.12 -m pytest -q tests/source_registry
ruff check app/source_registry app/domain/source_contracts.py tests/source_registry
mypy app/source_registry app/domain/source_contracts.py tests/source_registry
Set-Location ..
git diff --check
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
Set-Location backend
py -3.12 -m pytest --collect-only -q
```

**Results:**

- Source schema-contract parity tests: 4 passed.
- Lane A source-registry collection: 48 tests; default local run has 47 passed and 1 DB-gated skip.
- Lane A source-registry ruff: clean.
- Lane A source-registry mypy: clean over 16 source/test files.
- Whitespace check: clean.
- Full DB-enabled PowerShell verification: ok; 330 backend tests pass; lint clean; mypy clean over 119 source files; migrations/seeds apply; DB smoke passes.
- Backend collection includes 330 tests, including 4 source schema-contract tests.

**Residual risk:**

- TA-070 resolves `schemas/source_schema.json` for serialized `SourceContract` only. `SourceDatasetContract`, `SourceDatasetVersionContract`, `SourceRetrievalRunContract`, and job schema remain separate future work; report-run schema is resolved by TD-080 and planning-pack OpenAPI is resolved by TD-090. Connector adapter adoption of deterministic source-failure evidence IDs is completed by CON-019 in the Session 2 integration branch.

## 2026-06-04 Combined TC-180 plus CON-017/CON-018 integration rehearsal

**Commands run:**

```powershell
git merge --no-ff codex/con-017-queue-read-model
Set-Location backend
py -3.12 -m pytest -q tests/connectors/test_review_queue.py tests/api/test_connector_review_status.py tests/api/test_connector_review_queue_db.py tests/evidence_ledger/test_evidence_service.py
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/connectors/test_review_queue.py tests/api/test_connector_review_queue_db.py tests/evidence_ledger/test_sqlalchemy_evidence_repo.py::test_sqlalchemy_evidence_service_persists_source_failure_and_human_note
ruff check app/connectors app/api app/evidence_ledger/service.py tests/connectors tests/api tests/evidence_ledger/test_evidence_service.py tests/evidence_ledger/test_sqlalchemy_evidence_repo.py
mypy app/connectors app/api app/evidence_ledger/service.py tests/connectors tests/api tests/evidence_ledger/test_evidence_service.py tests/evidence_ledger/test_sqlalchemy_evidence_repo.py
py -3.12 -m pytest --collect-only -q
Set-Location ..
$rootArtifacts = (Resolve-Path ..\..\local_artifacts).Path
$env:PATH = "$rootArtifacts;$env:PATH"; $env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

**Results:**

- Focused combined connector/API/Lane C evidence-service tests with DB smoke skipped by default: 32 passed, 5 skipped.
- DB-enabled focused combined queue/API/evidence persistence tests: 12 passed.
- Combined connector/API/Lane C ruff: clean.
- Combined connector/API/Lane C mypy: clean over 38 source/test files.
- Backend collection: 331 tests.
- Full DB-enabled PowerShell verification: ok after prepending the root `local_artifacts` Windows wrapper directory for isolated-worktree `psql` lookup; 331 backend tests pass; lint clean; mypy clean over 118 source files; migrations/seeds apply; DB smoke passes.

**Residual risk:**

- This is an isolated integration rehearsal branch only. Root `main` remains separately controlled; landing still needs a clean root fast-forward/merge checkpoint that preserves Session 1 TC-180 and Session 2 CON-017/CON-018 records.

## 2026-06-04 Lane C TC-180 source-failure evidence ID preservation

**Commands run:**

```powershell
git rebase main
Set-Location backend
py -3.12 -m pytest -q tests/evidence_ledger/test_evidence_service.py
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/evidence_ledger/test_sqlalchemy_evidence_repo.py::test_sqlalchemy_evidence_service_persists_source_failure_and_human_note
ruff check app/evidence_ledger/service.py tests/evidence_ledger/test_evidence_service.py tests/evidence_ledger/test_sqlalchemy_evidence_repo.py
mypy app/evidence_ledger/service.py tests/evidence_ledger/test_evidence_service.py tests/evidence_ledger/test_sqlalchemy_evidence_repo.py
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/evidence_ledger tests/claims_engine
ruff check app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
mypy app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
rg -n "from app\.source_registry|from app\.area_geometry|import app\.source_registry|import app\.area_geometry" app/evidence_ledger app/claims_engine
git diff --check
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
Set-Location backend
py -3.12 -m pytest --collect-only -q
```

**Results:**

- Focused evidence-service tests: 19 passed.
- DB-gated source-failure persistence assertion: 1 passed.
- Targeted ruff: clean.
- Targeted mypy: clean over 3 source/test files.
- Lane C evidence/claims tests with DB smoke enabled: 153 passed.
- Lane C ruff: clean.
- Lane C mypy: clean over 29 source files.
- Cross-lane import-isolation scan: 0 matches.
- Whitespace check: clean.
- Full DB-enabled PowerShell verification: ok; 326 backend tests pass; lint clean; mypy clean over 118 source files; migrations/seeds apply; DB smoke passes.
- Backend collection includes 326 tests, including 19 evidence-service tests.

**Residual risk:**

- TC-180 closes the Lane C public service side of source-failure evidence ID preservation only. CON-019 later completes connector-owned adapter adoption in the Session 2 integration branch.

## 2026-06-04 CON-018 connector queue retry and cancel semantics

**Commands run:**

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/connectors/test_review_queue.py
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/connectors/test_review_queue.py
ruff check app/connectors/review_queue.py tests/connectors/test_review_queue.py app/connectors/__init__.py
mypy app/connectors/review_queue.py tests/connectors/test_review_queue.py app/connectors/__init__.py
py -3.12 -m pytest -q tests/connectors tests/api -rA
ruff check app/connectors app/api app/main.py tests/connectors tests/api
mypy app/connectors app/api app/main.py tests/connectors tests/api
py -3.12 -m pytest --collect-only -q
Set-Location ..
$rootArtifacts = (Resolve-Path ..\..\local_artifacts).Path
$env:PATH = "$rootArtifacts;$env:PATH"; $env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

**Results:**

- Focused queue tests with DB smoke skipped by default: 6 passed, 3 skipped.
- DB-enabled queue tests: 9 passed.
- Focused queue ruff: clean.
- Focused queue mypy: clean over 3 source/test files.
- Connector/API tests with DB smoke skipped by default: 64 passed, 8 skipped.
- Connector/API ruff: clean.
- Connector/API mypy: clean over 36 source files.
- Backend collection: 329 tests.
- Full DB-enabled PowerShell verification: ok after prepending the root `local_artifacts` Windows wrapper directory for isolated-worktree `psql` lookup; 329 backend tests pass; lint clean; mypy clean over 118 source files; migrations/seeds apply; DB smoke passes.

**Residual risk:**

- CON-018 is repository-level retry/requeue/cancel semantics only. It does not add API-side mutation, automatic retry policy, timeout handling, scheduler, background loop, queue dashboard, live connector execution, evidence persistence, claims, reports, schema/migration changes, durable `ingest_run_id` evidence-row linkage, exact source-failure evidence ID preservation, or broader fixture-category coverage.
- Default connector review queue items still use `max_attempts = 1`; retry remains fail-closed unless a future planned producer/operator explicitly permits additional attempts.

## 2026-06-04 CON-017 connector queue worker read model

**Commands run:**

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/api/test_connector_review_status.py tests/api/test_connector_review_queue_db.py
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/api/test_connector_review_queue_db.py
ruff check app/api/connectors.py tests/api/test_connector_review_status.py tests/api/test_connector_review_queue_db.py
mypy app/api/connectors.py tests/api/test_connector_review_status.py tests/api/test_connector_review_queue_db.py
py -3.12 -m pytest -q tests/connectors tests/api -rA
ruff check app/connectors app/api app/main.py tests/connectors tests/api
mypy app/connectors app/api app/main.py tests/connectors tests/api
py -3.12 -m pytest --collect-only -q
Set-Location ..
$rootArtifacts = (Resolve-Path ..\..\local_artifacts).Path
$env:PATH = "$rootArtifacts;$env:PATH"; $env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

**Results:**

- Focused queue API tests with DB smoke skipped by default: 7 passed, 2 skipped.
- DB-enabled queue API tests: 2 passed.
- Focused queue API ruff: clean.
- Focused queue API mypy: clean over 3 source/test files.
- Connector/API tests with DB smoke skipped by default: 62 passed, 7 skipped.
- Connector/API ruff: clean.
- Connector/API mypy: clean over 36 source files.
- Backend collection: 326 tests.
- Full DB-enabled PowerShell verification: ok after prepending the root `local_artifacts` Windows wrapper directory for isolated-worktree `psql` lookup; 326 backend tests pass; lint clean; mypy clean over 118 source files; migrations/seeds apply; DB smoke passes.

**Residual risk:**

- CON-017 is read-only worker-state API surfacing only. It does not add API-side job mutation, worker execution, scheduler, background loop, retry/requeue/cancel policy, queue dashboard, live connector execution, evidence persistence, claims, reports, schema/migration changes, durable `ingest_run_id` evidence-row linkage, exact source-failure evidence ID preservation, or broader fixture-category coverage.
- The first isolated-worktree full verification attempt failed at DB migration because `psql` was not on that worktree PATH. No code/test failure was observed; rerun passed using the existing root `local_artifacts/psql.cmd` wrapper on PATH.

## 2026-06-04 CON-016 connector queue worker lease semantics

**Commands run:**

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/connectors/test_review_queue.py
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/connectors/test_review_queue.py
ruff check app/connectors/review_queue.py tests/connectors/test_review_queue.py app/connectors/__init__.py
mypy app/connectors/review_queue.py tests/connectors/test_review_queue.py app/connectors/__init__.py
py -3.12 -m pytest -q tests/connectors
ruff check app/connectors tests/connectors
mypy app/connectors tests/connectors
py -3.12 -m pytest -q tests/connectors tests/api -rA
ruff check app/connectors app/api app/main.py tests/connectors tests/api
mypy app/connectors app/api app/main.py tests/connectors tests/api
Set-Location ..
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
Set-Location backend
py -3.12 -m pytest --collect-only -q
Set-Location ..
git diff --check
```

**Results:**

- Focused queue tests with DB smoke skipped by default: 4 passed, 2 skipped.
- DB-enabled queue tests: 6 passed.
- Focused queue ruff: clean.
- Focused queue mypy: clean over 3 source/test files.
- Connector tests with DB smoke skipped by default: 47 passed, 4 skipped.
- Connector ruff: clean.
- Connector mypy: clean over 21 source files.
- Connector/API tests with DB smoke skipped by default: 61 passed, 6 skipped.
- Connector/API ruff: clean.
- Connector/API mypy: clean over 36 source/test files.
- Full DB-enabled PowerShell verification: ok; 324 backend tests pass; lint clean; mypy clean over 118 source files; migrations/seeds apply; DB smoke passes.
- Backend collection: 324 tests.
- Whitespace check: clean.

**Residual risk:**

- CON-016 is repository-level queue lease and finish semantics only. It does not add a long-running worker process, scheduler, background loop, API mutation route, retry/requeue policy, queue dashboard, live connector execution, evidence persistence, claims, reports, schema/migration changes, durable `ingest_run_id` evidence-row linkage, exact source-failure evidence ID preservation, or broader fixture-category coverage.

## 2026-06-04 CON-015 connector review queue API retrieval

**Commands run:**

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/api/test_connector_review_status.py tests/api/test_connector_review_queue_db.py
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/api/test_connector_review_queue_db.py
ruff check app/api/connectors.py app/api/dependencies.py tests/api/test_connector_review_status.py tests/api/test_connector_review_queue_db.py
mypy app/api/connectors.py app/api/dependencies.py tests/api/test_connector_review_status.py tests/api/test_connector_review_queue_db.py
py -3.12 -m pytest -q tests/connectors tests/api -rA
ruff check app/connectors app/api app/main.py tests/connectors tests/api
mypy app/connectors app/api app/main.py tests/connectors tests/api
```

**Results:**

- Focused queue-retrieval API tests with DB smoke skipped by default: 6 passed, 1 skipped.
- DB-enabled queue-retrieval API test: 1 passed.
- Focused queue-retrieval ruff: clean.
- Focused queue-retrieval mypy: clean over 4 source/test files.
- Connector/API tests with DB smoke skipped by default: 59 passed, 5 skipped.
- Connector/API ruff: clean.
- Connector/API mypy: clean over 36 source/test files.
- Full DB-enabled PowerShell verification: ok; 321 backend tests pass; lint clean; mypy clean over 118 source files; migrations/seeds apply; DB smoke passes.

**Residual risk:**

- CON-015 is read-only queue API retrieval only. It does not add worker execution, job mutation, leasing, retries, queue dashboards, live I/O, schema/migration changes, claims, reports, durable `ingest_run_id` evidence-row linkage, exact source-failure evidence ID preservation, or broader fixture-category coverage.

## 2026-06-04 CON-014 durable connector review queue

**Commands run:**

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/connectors/test_review_queue.py
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/connectors/test_review_queue.py
ruff check app/connectors/review_queue.py tests/connectors/test_review_queue.py app/connectors/__init__.py
mypy app/connectors/review_queue.py tests/connectors/test_review_queue.py app/connectors/__init__.py
```

**Results:**

- Focused queue tests with DB smoke skipped by default: 2 passed, 1 skipped.
- DB-enabled queue tests: 3 passed.
- Focused queue ruff: clean.
- Focused queue mypy: clean over 3 source/test files.
- Connector tests with DB smoke skipped by default: 45 passed, 3 skipped.
- Connector ruff: clean.
- Connector mypy: clean over 21 source/test files.
- Full DB-enabled PowerShell verification: ok; 318 backend tests pass; lint clean; mypy clean over 117 source files; migrations/seeds apply; DB smoke passes.

**Residual risk:**

- CON-014 is durable queue persistence only. It does not add worker execution, queue dashboards, API DB retrieval from the queue, live I/O, schema/migration changes, claims, reports, durable `ingest_run_id` evidence-row linkage, exact source-failure evidence ID preservation, or broader fixture-category coverage.

## 2026-06-04 CON-013 connector review status API surface

**Commands run:**

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/connectors/test_review_status.py tests/api/test_connector_review_status.py
ruff check app/connectors/review_status.py app/api/connectors.py app/api/dependencies.py app/main.py tests/connectors/test_review_status.py tests/api/test_connector_review_status.py
mypy app/connectors/review_status.py app/api/connectors.py app/api/dependencies.py app/main.py tests/connectors/test_review_status.py tests/api/test_connector_review_status.py
py -3.12 -m pytest -q tests/connectors tests/api -rA
ruff check app/connectors app/api app/main.py tests/connectors tests/api
mypy app/connectors app/api app/main.py tests/connectors tests/api
Set-Location ..
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

**Results:**

- Focused review-status/API tests: 8 passed.
- Connector/API tests with DB smoke skipped by default: 55 passed, 3 skipped.
- Connector/API ruff: clean.
- Connector/API mypy: clean over 33 source/test files.
- Full DB-enabled PowerShell verification: ok; 315 backend tests pass; lint clean; mypy clean over 115 source files; migrations/seeds apply; DB smoke passes.

**Residual risk:**

- CON-013 is an in-memory API status surface only. It does not add durable queue persistence, a connector status table, schema/migration changes, live I/O, claims, reports, durable `ingest_run_id` evidence-row linkage, exact source-failure evidence ID preservation, or broader fixture-category coverage.

## 2026-06-04 CON-012 connector fixture quality profile

**Commands run:**

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/connectors/test_fixture_quality.py
ruff check app/connectors tests/connectors/test_fixture_quality.py
mypy app/connectors tests/connectors/test_fixture_quality.py
py -3.12 -m pytest -q tests/connectors
ruff check app/connectors tests/connectors
mypy app/connectors tests/connectors
Set-Location ..
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

**Results:**

- Focused fixture-quality tests: 7 passed.
- Full connector tests: 39 passed, 2 skipped by DB-smoke gating.
- Connector ruff: clean.
- Connector mypy: clean over 17 source/test files.
- Full DB-enabled PowerShell verification: ok; 307 backend tests pass; lint clean; mypy clean over 111 source files; migrations/seeds apply; DB smoke passes.

**Residual risk:**

- CON-012 is a connector-owned fixture-quality evaluator only. It does not add API routing, durable queue persistence, claims, reports, schema edits, live I/O, durable `ingest_run_id` evidence-row linkage, exact source-failure evidence ID preservation, or broader fixture-category coverage.

## 2026-06-04 CON-011 connector review handoff consumer

**Commands run:**

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/connectors/test_review_handoff.py tests/connectors/test_review_packet.py
ruff check app/connectors tests/connectors/test_review_handoff.py tests/connectors/test_review_packet.py
mypy app/connectors tests/connectors/test_review_handoff.py tests/connectors/test_review_packet.py
py -3.12 -m pytest -q tests/connectors
ruff check app/connectors tests/connectors
mypy app/connectors tests/connectors
Set-Location ..
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

**Results:**

- Focused review-handoff/review-packet tests: 8 passed.
- Full connector tests: 32 passed, 2 skipped by DB-smoke gating.
- Connector ruff: clean.
- Connector mypy: clean over 15 source/test files.
- Full DB-enabled PowerShell verification: ok; 300 backend tests pass; lint clean; mypy clean over 109 source files; migrations/seeds apply; DB smoke passes.

**Residual risk:**

- CON-011 is a connector-owned review-packet consumer only. It does not add API routing, durable queue persistence, claims, reports, schema edits, live I/O, durable `ingest_run_id` evidence-row linkage, or exact source-failure evidence ID preservation.

## 2026-06-04 CON-010 connector run/status review packet

**Commands run:**

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/connectors/test_review_packet.py tests/connectors/test_fixture_workflow.py
ruff check app/connectors tests/connectors/test_review_packet.py
mypy app/connectors tests/connectors/test_review_packet.py
py -3.12 -m pytest -q tests/connectors
ruff check app/connectors tests/connectors
mypy app/connectors tests/connectors
Set-Location ..
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

**Results:**

- Focused review-packet/fixture-workflow tests: 8 passed.
- Full connector tests: 28 passed, 2 skipped by DB-smoke gating.
- Connector ruff: clean.
- Connector mypy: clean over 13 source/test files.
- Full DB-enabled PowerShell verification: ok; 296 backend tests pass; lint clean; mypy clean over 107 source files; migrations/seeds apply; DB smoke passes.

**Residual risk:**

- CON-010 is a connector-owned run/status and human-review handoff projection only. It does not add API routing, persistence, claims, reports, schema edits, live I/O, durable `ingest_run_id` evidence-row linkage, or exact source-failure evidence ID preservation.

## 2026-06-04 Session 1 planning-pack schema-copy reconciliation

**Commands run:**

```powershell
git rebase main
rg -n "(<{7}|={7}|>{7})" ./state/PROJECT_STATE.md ./state/VALIDATION_LOG.md ./state/WORKLOG.md
py -3.12 -m pytest -q backend/tests/test_planning_pack_schema_copies.py
ruff check backend/tests/test_planning_pack_schema_copies.py
mypy backend/tests/test_planning_pack_schema_copies.py
Set-Location backend
py -3.12 -m pytest --collect-only -q
Set-Location ..
git diff --no-index --quiet ./schemas/evidence_schema.json ./docs/planning_pack/schemas/evidence_schema.json
git diff --no-index --quiet ./schemas/claim_schema.json ./docs/planning_pack/schemas/claim_schema.json
git diff --check
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

**Results:**

- Preserved CON-009 state/task records from root `main` at `56d53c8`.
- `docs/planning_pack/schemas/evidence_schema.json` and `docs/planning_pack/schemas/claim_schema.json` parse-match their canonical root schema files in the isolated branch.
- Added a planning-pack schema-copy parity test for the evidence and claim schema copies.
- Focused planning-pack schema-copy parity test: 1 passed.
- Targeted ruff: clean.
- Targeted mypy: clean over 1 test file.
- Backend collection includes the planning-pack schema-copy parity test.
- Exact schema-copy equality checks: clean.
- Whitespace check: clean.
- Full DB-enabled PowerShell verification: ok; 292 backend tests pass; lint clean; mypy clean over 105 source files; migrations/seeds apply; DB smoke passes.

**Residual risk:**

- This pass only reconciles planning-pack evidence/claim schema copies. Planning-pack OpenAPI, source/job schemas, report schema proposals, connector envelopes, durable `ingest_run_id` evidence-row linkage, exact source-failure evidence ID preservation, and connector run/status review workflow planning remain separate owner-specific follow-ups.

## 2026-06-04 CON-009 DB-backed source-failure fixture workflow smoke

**Commands run:**

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/connectors/test_public_wiring.py
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/connectors/test_public_wiring.py
ruff check tests/connectors/test_public_wiring.py
mypy tests/connectors/test_public_wiring.py
Set-Location ..
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
git diff --check
```

**Results:**

- Connector public-wiring tests without DB smoke: 5 passed, 2 skipped.
- Connector public-wiring tests with DB smoke: 7 passed.
- Targeted ruff: clean.
- Targeted mypy: clean over 1 test file.
- Full DB-enabled PowerShell verification: ok; 291 collected backend tests; lint clean; mypy clean over 104 source files; migrations/seeds apply; DB smoke passes.
- Whitespace check: clean.

**Residual risk:**

- CON-009 proves the fixture source-failure workflow through DB-backed public Lane A and Lane C services only. It does not solve exact source-failure evidence ID preservation or durable `ingest_run_id` linkage on `evidence.observations`; both remain future scoped work.

## 2026-06-04 CON-008 DB-backed fixture workflow smoke

**Commands run:**

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/connectors/test_public_wiring.py
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/connectors/test_public_wiring.py
ruff check tests/connectors/test_public_wiring.py
mypy tests/connectors/test_public_wiring.py
Set-Location ..
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
git diff --check
```

**Results:**

- Connector public-wiring tests without DB smoke: 5 passed, 1 skipped.
- Connector public-wiring tests with DB smoke: 6 passed.
- Targeted ruff: clean.
- Targeted mypy: clean over 1 test file.
- Full DB-enabled PowerShell verification: ok; 290 collected backend tests; lint clean; mypy clean over 104 source files; migrations/seeds apply; DB smoke passes.
- Whitespace check: clean.

**Residual risk:**

- CON-008 proves the fixture success workflow through DB-backed public Lane A and Lane C services only. It does not prove source-failure DB workflow behavior and does not solve durable `ingest_run_id` linkage on `evidence.observations`; both remain future scoped work.

## 2026-06-04 CON-007 Lane A public provenance identity-preservation follow-up

**Commands run:**

```powershell
Set-Location backend
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/source_registry/test_source_provenance.py tests/connectors
ruff check app/source_registry/provenance_service.py app/connectors tests/source_registry/test_source_provenance.py tests/connectors
mypy app/source_registry/provenance_service.py app/connectors tests/source_registry/test_source_provenance.py tests/connectors
py -3.12 -m pytest --collect-only -q
Set-Location ..
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
git diff --check
```

**Results:**

- Targeted DB-enabled source-provenance/connector tests: 29 passed.
- Targeted ruff: clean.
- Targeted mypy: clean over 13 source/test files.
- Full DB-enabled PowerShell verification: ok; 289 collected backend tests; lint clean; mypy clean over 104 source files; migrations/seeds apply; DB smoke passes.
- Whitespace check: clean.

**Residual risk:**

- Public Lane A and Lane C service wiring now exists. The next connector proof should run the full fixture workflow against DB-backed public services together before making broader production ingestion claims.

## 2026-06-04 CON-006 concrete public-service workflow wiring handoff

**Commands run:**

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/connectors
ruff check app/connectors tests/connectors
mypy app/connectors tests/connectors
py -3.12 -m pytest --collect-only -q
Set-Location ..
.\scripts\verify.ps1
git diff --check
```

**Results:**

- Connector tests: 23 passed.
- Connector ruff: clean.
- Connector mypy: clean over 11 connector source/test files.
- Full PowerShell verification: ok; 286 collected backend tests; lint clean; mypy clean over 104 source files; DB smoke skipped by default.
- Whitespace check: clean.

**Residual risk:**

- DB smoke was not rerun for CON-006 because this slice does not touch DB wiring or schema.
- Lane C public evidence-service wiring is implemented, but durable DB-backed connector workflow ingestion is not claimed. The next required follow-up is a Lane A-compatible public provenance method/adapter that preserves supplied `SourceRetrievalRunContract.ingest_run_id`, followed by DB-smoke verification.

## 2026-06-04 CON-005 fixture connector ingest workflow composition

**Commands run:**

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/connectors
ruff check app/connectors tests/connectors
mypy app/connectors tests/connectors
py -3.12 -m pytest --collect-only -q
Set-Location ..
.\scripts\verify.ps1
git diff --check
```

**Results:**

- Connector tests: 19 passed.
- Connector ruff: clean.
- Connector mypy: clean over 9 connector source/test files.
- Full PowerShell verification: ok; 282 collected backend tests; lint clean; mypy clean over 102 source files; DB smoke skipped by default.
- Whitespace check: clean.

**Residual risk:**

- DB smoke was not rerun for CON-005 because this slice does not touch DB wiring or schema.
- CON-005 composes injected ports only. Concrete DB-backed workflow wiring still needs a public Lane A-compatible provenance port that preserves supplied `SourceRetrievalRunContract.ingest_run_id`, plus public Lane C evidence-ingestion service wiring.

## 2026-06-04 CON-004 connector retrieval-run provenance adapter

**Commands run:**

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/connectors
ruff check app/connectors tests/connectors
mypy app/connectors tests/connectors
py -3.12 -m pytest --collect-only -q
Set-Location ..
.\scripts\verify.ps1
git diff --check
```

**Results:**

- Connector tests: 15 passed.
- Connector ruff: clean.
- Connector mypy: clean over 7 connector source/test files.
- Full PowerShell verification: ok; 278 collected backend tests; lint clean; mypy clean over 100 source files; DB smoke skipped by default.
- Whitespace check: clean.

**Residual risk:**

- DB smoke was not rerun for CON-004 because this slice does not touch DB wiring or schema.
- Concrete production wiring needs a Lane A public method or Lane A-owned adapter that preserves supplied `SourceRetrievalRunContract.ingest_run_id`.

## 2026-06-04 CON-003 connector evidence-ingestion adapter

**Commands run:**

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/connectors
ruff check app/connectors tests/connectors
mypy app/connectors tests/connectors
py -3.12 -m pytest --collect-only -q
Set-Location ..
.\scripts\verify.ps1
git diff --check
```

**Results:**

- Connector tests: 11 passed.
- Connector ruff: clean.
- Connector mypy: clean over 5 connector source/test files.
- Full PowerShell verification: ok; 274 collected backend tests; lint clean; mypy clean over 98 source files; DB smoke skipped by default.
- Whitespace check: clean.

**Residual risk:**

- DB smoke was not rerun for CON-003 because this slice does not touch DB wiring or schema.
- `SourceRetrievalRunContract` persistence remains a connector/Lane A provenance handoff gap for CON-004.

## 2026-06-04 Session 1 Lane C TC-170 schema-contract alignment

**Commands run:**

```powershell
git worktree add -b lane-c/session1-schema-contracts ./worktrees/session1-lane-c-schema main
Set-Location backend
py -3.12 -m pytest -q tests/evidence_ledger/test_evidence_schema_contract.py tests/claims_engine/test_claim_schema_contract.py
ruff check tests/evidence_ledger/test_evidence_schema_contract.py tests/claims_engine/test_claim_schema_contract.py
mypy tests/evidence_ledger/test_evidence_schema_contract.py tests/claims_engine/test_claim_schema_contract.py
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/evidence_ledger tests/claims_engine
ruff check app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
mypy app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
rg -n "from app\.source_registry|from app\.area_geometry|import app\.source_registry|import app\.area_geometry" app/evidence_ledger app/claims_engine
py -3.12 -m pytest --collect-only -q tests/evidence_ledger tests/claims_engine
py -3.12 -m pytest --collect-only -q
Set-Location ..
$rootArtifacts = Resolve-Path ../../local_artifacts
$env:PATH = "$rootArtifacts;$env:PATH"
$env:RUN_DB_SMOKE='1'
.\scripts\verify.ps1
git stash push -u -m "session1-lane-c-schema-contracts"
git merge main --ff-only
git stash pop
rg -n "(<{7}|={7}|>{7})" ./state/PROJECT_STATE.md ./state/VALIDATION_LOG.md ./state/WORKLOG.md
git diff --check
$env:RUN_DB_SMOKE='1'
.\scripts\verify.ps1
git stash push -u -m "session1-lane-c-schema-contracts-after-d005"
git merge main --ff-only
git stash pop "stash@{0}"
rg -n "(<{7}|={7}|>{7})" ./state/PROJECT_STATE.md ./state/VALIDATION_LOG.md ./state/WORKLOG.md
git diff --check
$env:RUN_DB_SMOKE='1'
.\scripts\verify.ps1
git rebase main
rg -n "(<{7}|={7}|>{7})" ./state/PROJECT_STATE.md ./state/VALIDATION_LOG.md ./state/WORKLOG.md
git diff --check
$env:RUN_DB_SMOKE='1'
.\scripts\verify.ps1
```

**Results:**

- Work ran in isolated worktree `worktrees/session1-lane-c-schema` on branch `lane-c/session1-schema-contracts`.
- The branch was rebased onto root `main` at `a43b3e3` (`Define CON-002 evidence ingestion handoff`) before final verification so D-004, D-005, CON-001, CON-002, connector ownership, task, and state updates were preserved.
- `schemas/evidence_schema.json` now mirrors serialized `EvidenceContract` fields and enum values; stale DB/doc fields `retrieved_at`, `geometry_wkt`, `metadata`, and `authority_level` are removed.
- `schemas/claim_schema.json` now mirrors serialized `ClaimContract` fields and enum values; stale fields `intent`, `contradiction_group_ids`, and `metadata` are removed.
- `docs/adr/lane-c-schemas.md` records the shared-schema decision for root evidence/claim schemas.
- Added Lane C schema-contract parity tests without a new JSON-schema validation dependency.
- Focused schema-contract tests pass: 8 tests.
- Lane C evidence/claims tests pass with DB smoke enabled: 151 tests.
- Lane C targeted ruff passes.
- Lane C targeted mypy passes: no issues in 29 source/test files.
- Lane C import-isolation scan returns no matches.
- Full backend collection after rebasing onto CON-001 reports 268 tests.
- Full PowerShell verification passes with DB smoke enabled: 268 backend tests; lint clean; mypy clean (96 source files); migrations/seeds apply; DB smoke passes.

**Residual risk:**

- This aligns the canonical root schemas only. `docs/planning_pack/schemas/*.json` remains a stale documentation-packaging surface and should be handled in a separate docs/packaging pass.
- TC-170 does not edit connector ownership files or connector runtime code. CON-003 remains responsible for evidence-ingestion adapter implementation.

## 2026-06-04 Session 2 CON-001 fixture flood connector

**Commands run:**

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/connectors
ruff check app/connectors tests/connectors
mypy app/connectors tests/connectors
py -3.12 -m pytest --collect-only -q
Set-Location ..
.\scripts\verify.ps1
git diff --check
```

**Results:**

- Connector targeted tests pass: 5 tests.
- Connector ruff and mypy checks pass.
- `StaticFloodFixtureConnector` reads local fixture JSON and rejects URI-like paths.
- Success fixture returns source retrieval provenance plus flood spatial-intersection evidence input.
- Failure fixture returns blocked retrieval provenance plus SOURCE_FAILURE evidence input.
- Connector module does not import claim/report modules or live-IO libraries.
- Full PowerShell verification passes: 260 collected backend tests, lint clean, mypy clean (94 source files), and DB smoke skipped by default.
- `git diff --check` reports no whitespace errors.

**Residual risk:**

- CON-001 does not persist connector outputs. CON-002 defines the evidence-ingestion handoff without connector code modifying Lane C implementation.
- Live connector behavior remains blocked by license, fixture, failure, rate-limit, and caveat gates.

## 2026-06-04 Session 2 CON-002 evidence-ingestion handoff

**Commands run:**

```powershell
.\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only -q
git diff --check
```

**Results:**

- Defined the connector evidence-ingestion boundary in `plans/connector-2026-06-04-fixture-flood.md`.
- Decided that connector-zone ingestion adapters must use injected public Lane C EvidenceService methods rather than Lane C repositories or private service helpers.
- Normal connector evidence routes to `create_observation`.
- Source-failure templates route to `create_source_failure`, with returned evidence treated as persistence authority.
- Recorded durable retrieval-run/evidence linkage and exact source-failure field preservation as future Lane C/schema coordination gaps.
- No Lane C implementation, shared schema, migration, live connector, credential, browser/download, claim, report, or API files changed.
- Full PowerShell verification passes: 260 collected backend tests, lint clean, mypy clean (94 source files), and DB smoke skipped by default.
- `git diff --check` reports no whitespace errors.

**Residual risk:**

- CON-003 must implement the adapter and prove idempotency using public evidence service methods.
- Durable `ingest_run_id` linkage remains unimplemented until a coordinated contract/schema pass.

## 2026-06-04 Session 2 D-005 connector ownership decision packet

**Commands run:**

```powershell
.\scripts\verify.ps1
git diff --check
```

**Results:**

- Prepared and accepted the connector ownership/run-lifecycle ADR without changing runtime code.
- Added a coordinator-owned connector integration zone to `LANE_OWNERSHIP.md` for future `backend/app/connectors/`, `backend/tests/connectors/`, and `tests/fixtures/connectors/`.
- Selected source retrieval runs as connector lifecycle/provenance authority, with jobs reserved for future async orchestration.
- Assigned the first fixture-only flood connector implementation pass to the connector integration zone.
- No connector runtime code, shared schemas, migrations, automatic-execution config, POSIX script command path, or Lane A/B/C implementation files were changed.
- Full PowerShell verification passes: 255 backend tests, lint clean, mypy clean (91 source files), and DB smoke skipped by default.
- `git diff --check` reports no whitespace errors.

**Residual risk:**

- Runtime connector work must stay in the connector integration zone and remain fixture-only until live connector gates are explicitly satisfied.
- Lane A/B/C/D implementation changes remain blocked unless coordinated with the owning lane.

## 2026-06-04 Session 2 D-004 Level 8 ownership and fixture acceptance

**Commands run:**

```powershell
.\scripts\verify.ps1
git diff --check
```

**Results:**

- Mapped Level 8 connector gates L8-001 through L8-010 to primary and supporting lane owners in `plans/2026-06-04-l7-closeout-l8-entry.md`.
- Defined the first connector acceptance path as a static local flood fixture with no live network use, no runtime connector code in this slice, and explicit report/API downstream verification expectations.
- Recorded stop conditions for unassigned connector module ownership, unresolved source licensing, invalid Lane C evidence payload shape, unspecified idempotency, live-network requirements, and premature schema edits.
- No connector runtime code, shared schemas, migrations, or Lane A/B/C implementation files were edited.
- Full PowerShell verification passes: 255 backend tests, lint clean, mypy clean (91 source files), and DB smoke skipped by default.
- `git diff --check` reports no whitespace errors.

**Residual risk:**

- D-005 must resolve future `backend/app/connectors/` ownership and connector run lifecycle authority before Level 8 runtime implementation starts.
- The first fixture connector behavior remains a plan/acceptance contract only; it is not implemented in D-004.

## 2026-06-04 Session 1 Lane B TB-100 coordinate validation hardening

**Commands run:**

```powershell
git worktree add -b lane-b/session1-geometry-hardening ./worktrees/session1-lane-b main
Set-Location backend
py -3.12 -m pytest -q tests/area_geometry/test_area_service.py
ruff check app/area_geometry/geometry_validator.py tests/area_geometry/test_area_service.py
mypy app/area_geometry/geometry_validator.py tests/area_geometry/test_area_service.py
$env:RUN_DB_SMOKE='1'
py -3.12 -m pytest -q tests/area_geometry
ruff check app/area_geometry app/domain/area_contracts.py tests/area_geometry
mypy app/area_geometry app/domain/area_contracts.py tests/area_geometry
Set-Location ..
$rootArtifacts = Resolve-Path ../../local_artifacts
$env:PATH = "$rootArtifacts;$env:PATH"
$env:RUN_DB_SMOKE='1'
.\scripts\verify.ps1
git merge main --no-edit
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/area_geometry tests/reports tests/api
ruff check app/area_geometry app/domain/area_contracts.py tests/area_geometry app/reports app/api app/db tests/reports tests/api
mypy app/area_geometry app/domain/area_contracts.py tests/area_geometry app/reports app/api app/db tests/reports tests/api
py -3.12 -m pytest --collect-only -q
$rootArtifacts = Resolve-Path ../../local_artifacts
$env:PATH = "$rootArtifacts;$env:PATH"
$env:RUN_DB_SMOKE='1'
.\scripts\verify.ps1
git merge main --no-edit
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/area_geometry tests/reports tests/api
ruff check app/area_geometry app/domain/area_contracts.py tests/area_geometry app/reports app/api app/db tests/reports tests/api
mypy app/area_geometry app/domain/area_contracts.py tests/area_geometry app/reports app/api app/db tests/reports tests/api
py -3.12 -m pytest --collect-only -q
$rootArtifacts = Resolve-Path ../../local_artifacts
$env:PATH = "$rootArtifacts;$env:PATH"
$env:RUN_DB_SMOKE='1'
.\scripts\verify.ps1
git merge main --no-edit
py -3.12 -m pytest --collect-only -q
$rootArtifacts = Resolve-Path ../../local_artifacts
$env:PATH = "$rootArtifacts;$env:PATH"
$env:RUN_DB_SMOKE='1'
.\scripts\verify.ps1
Set-Location ..\..
git merge --squash lane-b/session1-geometry-hardening
Set-Location backend
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/area_geometry
ruff check app/area_geometry app/domain/area_contracts.py tests/area_geometry
mypy app/area_geometry app/domain/area_contracts.py tests/area_geometry
py -3.12 -m pytest --collect-only -q
Set-Location ..
$rootArtifacts = Resolve-Path ./local_artifacts
$env:PATH = "$rootArtifacts;$env:PATH"
$env:RUN_DB_SMOKE='1'
.\scripts\verify.ps1
```

**Results:**

- Work ran in isolated worktree `worktrees/session1-lane-b` on branch `lane-b/session1-geometry-hardening`; root checkout Lane D files were not edited.
- `validate_geojson` now rejects non-finite longitude/latitude values and out-of-range EPSG:4326 longitude/latitude positions.
- Focused service/validator tests pass: 18 tests.
- Lane B area-geometry tests pass with DB smoke enabled: 49 tests.
- Lane B ruff and mypy pass.
- Pre-D-003 full PowerShell verification after merging D-002 passes with DB smoke enabled: 255 backend tests; lint clean; mypy clean (91 source files); migrations/seeds apply; DB smoke passes.
- Root `main` D-003 was merged into the Lane B worktree; conflicts were limited to shared state files and resolved by preserving both D-003 and TB-100 entries.
- Post-D-003 collection reports 255 tests.
- Post-D-003 full PowerShell verification passes with DB smoke enabled: 255 backend tests; lint clean; mypy clean (91 source files); migrations/seeds apply; DB smoke passes.
- Lane B TB-100 was squash-merged from `lane-b/session1-geometry-hardening` onto root `main` after confirming the root diff only contained Lane B validator/test/fixture changes plus shared state records.
- Root `main` targeted Lane B tests pass with DB smoke enabled: 49 tests.
- Root `main` targeted Lane B ruff and mypy pass.
- Root `main` collection reports 255 tests.
- Root `main` full PowerShell verification passes with DB smoke enabled: 255 backend tests; lint clean; mypy clean (91 source files); migrations/seeds apply; DB smoke passes.
- No `.claude/settings.json`, `.codex/hooks.json`, hook-driven execution, `.sh` scripts, or replacement of `local_artifacts/psql.cmd` were introduced.

**Residual risk:**

- This is coordinate-sanity hardening only; it does not assert survey accuracy, legal boundary correctness, or suitability.
- Level 8 connector implementation remains blocked until D-004 maps connector gates to lane owners and fixture-only acceptance criteria.

## 2026-06-04 Session 2 D-003 schema-contract alignment

**Commands run:**

```powershell
.\scripts\verify.ps1
git diff --check
```

**Results:**

- Audited active shared source/evidence/claim/job schemas against current domain contracts and report/API artifacts.
- Recorded schema gaps and future lane ownership in `plans/2026-06-04-l7-closeout-l8-entry.md`.
- No shared `schemas/*.json` files, domain contracts, migrations, or Lane A/B/C implementation files were edited.
- Full PowerShell verification passes.
- `git diff --check` reports no whitespace errors.

**Residual risk:**

- Actual shared-schema edits remain pending and require owner-specific follow-up.
- Level 8 connector implementation remains blocked until D-004 maps connector gates to lane owners and fixture-only acceptance criteria.

## 2026-06-04 Session 2 D-002 report artifact regression

**Commands run:**

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/reports/test_report_regression.py
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/reports tests/api
ruff check app/reports app/api tests/reports tests/api
mypy app/reports app/api tests/reports tests/api
Set-Location ..
.\scripts\verify.ps1
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
Set-Location backend
py -3.12 -m pytest --collect-only -q
Set-Location ..
git diff --check
```

**Results:**

- Added a normalized report regression that pins the stable semantic shape of a generated fixture report artifact.
- Regression covers report status, intent, source manifest, evidence, claims, unknowns, red flags, caveats, and artifact metadata.
- Dynamic UUIDs, timestamps, and path-like fields are intentionally not expected-output fields.
- Lane D report/API tests pass with DB smoke enabled: 20 tests.
- Targeted Lane D/API ruff passes.
- Targeted Lane D/API mypy passes.
- Full PowerShell verification passes without DB smoke: lint clean, mypy clean (91 source files), DB smoke skipped.
- Full PowerShell verification passes with DB smoke enabled: 252 backend tests, lint clean, mypy clean (91 source files), migrations/seeds apply, and DB smoke passes.
- Full backend collection confirms 252 tests.

**Residual risk:**

- Shared schema-contract alignment remains D-003 and must happen before editing `schemas/*.json`.
- Level 8 connector implementation remains blocked on lane ownership and fixture-only connector acceptance criteria.

## 2026-06-04 Session 2 D-001 DB-backed API workflow

**Commands run:**

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/api tests/reports
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/api tests/reports
ruff check app/api app/main.py app/reports tests/api tests/reports
mypy app/api app/main.py app/reports tests/api/test_report_runs_db.py
Set-Location ..
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
git diff --check
```

**Results:**

- Default API scaffold tests remain in-memory and pass; the DB-backed API test is skipped unless `RUN_DB_SMOKE=1`.
- Lane D report/API tests pass with DB smoke enabled: 19 tests.
- DB-backed API mode creates areas and report runs through SQLAlchemy-backed services, retrieves the persisted report artifact, and stores a non-null `intent_id` in `reports.report_runs`.
- Unsupported-category source failures still surface as UNKNOWN claims in DB-backed API report output.
- Targeted Lane D/API ruff passes.
- Targeted Lane D/API mypy passes.
- Full PowerShell verification with DB smoke enabled passes: 251 backend tests, lint clean, mypy clean (90 source files), migrations/seeds apply, and DB smoke passes.
- `git diff --check` reports no whitespace errors.

**Residual risk:**

- Shared report/schema JSON alignment remains a coordinated follow-up before editing `schemas/*.json`.
- Live connectors, UI workflow, auth/security, and production observability remain out of scope until Level 8+ planning.

## 2026-06-04 Session 2 D-000 report surfacing

**Commands run:**

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/reports/test_report_service.py tests/api/test_api_scaffold.py
ruff check app/reports/service.py tests/reports/test_report_service.py tests/api/test_api_scaffold.py
mypy app/reports/service.py tests/reports/test_report_service.py tests/api/test_api_scaffold.py
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/reports tests/api
ruff check app/reports app/api app/db tests/reports tests/api
mypy app/reports app/api app/db tests/reports tests/api
Set-Location ..
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
Set-Location backend
py -3.12 -m pytest --collect-only -q
Set-Location ..
git diff --check
```

**Results:**

- `ReportRunService` now creates stored unsupported-category SOURCE_FAILURE evidence for missing not-evaluated domains before rule evaluation.
- Report/API output includes all four unsupported categories in `unknowns`: soil/septic, environmental hazards, resource context, and market context.
- Repeat report runs reuse the existing unsupported-category source failures and sentinel source instead of duplicating them.
- The DB-backed report repository round-trip now verifies the persisted report artifact includes the not-evaluated unknowns and sentinel source manifest entry.
- Targeted report/API tests pass: 11 tests.
- Lane D report/API tests pass with DB smoke enabled: 18 tests.
- Targeted Lane D ruff passes.
- Targeted Lane D mypy passes: no issues in 25 source/test files.
- Full PowerShell verification passes with DB smoke enabled: 250 backend tests, lint clean, mypy clean (89 source files), migrations/seeds apply, and DB smoke passes.
- Full backend collection confirms 250 tests.
- `git diff --check` reports no whitespace errors.

**Residual risk:**

- Level 7 remains partial until D-001 wires the API workflow to DB-backed repositories and proves `POST /report-runs` can create/retrieve a DB-backed report run end to end.
- Default API dependencies still use in-memory repositories outside the DB-gated repository tests.

## 2026-06-04 Session 2 C-002 merge and root verification

**Commands run:**

```powershell
git merge --no-ff codex/session1-lane-c -m "Merge Lane C C-002 handoff"
py -3.12 -m pytest -q tests/claims_engine/test_not_evaluated_claims.py tests/claims_engine/test_rule_engine.py tests/claims_engine/test_forbidden_language.py tests/reports tests/api
ruff check app/claims_engine tests/claims_engine app/api app/reports app/db tests/api tests/reports
mypy app/claims_engine tests/claims_engine app/api app/reports app/db tests/api tests/reports
py -3.12 -m pytest --collect-only -q
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

**Results:**

- C-002 is merged onto root `main`.
- Merge conflicts occurred only in `state/VALIDATION_LOG.md` and `state/WORKLOG.md`; both were resolved by preserving Session 1's C-002 evidence and Session 2's handoff-risk note.
- Targeted C-002/report/API tests pass.
- Targeted ruff passes.
- Targeted mypy passes: no issues in 38 source/test files.
- Full collection reports 250 tests.
- Full PowerShell verification passes with DB smoke enabled: 250 backend tests, lint clean, mypy clean (89 source files), migrations/seeds apply, and DB smoke passes.

**Residual risk:**

- D-000 report surfacing is now unblocked and should be implemented before D-001 DB-backed API workflow wiring.

## 2026-06-04 Session 1 C-002 not-evaluated rule categories

**Commands run:**

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/claims_engine/test_not_evaluated_claims.py tests/claims_engine/test_rule_engine.py tests/claims_engine/test_forbidden_language.py
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/claims_engine
py -3.12 -m pytest -q tests/reports tests/api
ruff check app/claims_engine tests/claims_engine
mypy app/claims_engine tests/claims_engine
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q
py -3.12 -m pytest --collect-only -q
Set-Location ..
python scripts/db_smoke_check.py
.\scripts\verify.ps1
```

**Results:**

- Added `backend/app/claims_engine/not_evaluated.py` with unsupported-domain constants and a source-failure evidence helper.
- Added four explicit unsupported-domain hard gates to `config/ruleset_homestead_mvp.yaml`.
- `RuleEngine.evaluate()` emits deterministic `SeverityBand.UNKNOWN` claims for soil/septic, environmental hazard, resource context, and market context when provided corresponding source-failure evidence.
- Not-evaluated claims cite source-failure evidence IDs and preserve ruleset metadata, confidence/severity separation, caveats, and verification tasks.
- Non-failure unsupported-domain records do not produce claims.
- Market-context not-evaluated claim language avoids unsafe market/steering terms.
- Lane C evidence/claims collection reports 143 tests before Session 2's later API additions.
- Full backend collection reports 248 tests before Session 2's later API additions.
- Lane C claims tests pass with DB smoke enabled.
- Report/API tests pass.
- Full DB-gated backend pytest passes.
- Targeted Lane C ruff and mypy pass.
- Direct DB smoke check passes against the currently running local Postgres/PostGIS database.
- Default Windows verification passes: workspace validation, structural invariants, backend tests, lint, and mypy; DB smoke skipped by default.

**Residual risk:**

- Report-run auto-creation/registration of unsupported-domain source-failure evidence is not implemented in Session 1 because `backend/app/reports/service.py` is Lane D-owned. D-000 should use the Lane C helper before rule evaluation so report runs include these unknowns.
- Default `.\scripts\verify.ps1` still skips DB smoke unless `RUN_DB_SMOKE=1`; DB runtime health was separately verified through DB-gated pytest and direct `scripts/db_smoke_check.py`.

## 2026-06-04 Session 2 C-002 handoff risk check

**Commands run:**

```powershell
git status --short --branch
git -C ./worktrees/session1-lane-c status --short --branch
Get-Content -Path 'C:\Users\benny\.codex\sessions\2026\06\03\rollout-2026-06-03T06-53-13-019e8dc2-681d-7480-aa9f-d8aeac662772.jsonl' -Tail 180
git show codex/session1-lane-c:config/ruleset_homestead_mvp.yaml | Select-String -Pattern 'SOIL_NOT_EVALUATED|ENV_HAZ_NOT_EVALUATED|RESOURCE_NOT_EVALUATED|MARKET_OUT_OF_SCOPE|severity_on_fail' -Context 0,2
git show codex/session1-lane-c:backend/tests/claims_engine/test_not_evaluated_claims.py | Select-String -Pattern 'severity_on_fail|SeverityBand.INFORMATIONAL|SeverityBand.UNKNOWN' -Context 1,1
rg -n '<{7}|>{7}|={7}' ./worktrees/session1-lane-c/state/PROJECT_STATE.md ./worktrees/session1-lane-c/state/VALIDATION_LOG.md ./worktrees/session1-lane-c/state/WORKLOG.md ./worktrees/session1-lane-c/tasks/task_queue.yaml ./worktrees/session1-lane-c/plans/2026-06-03-codex-deferred-tasks.md
git merge-tree main codex/session1-lane-c
.\scripts\verify.ps1
```

**Results:**

- Root `main` was clean and did not yet contain C-002 at the time of the check.
- Session 1's C-002 worktree was detached during rebase and still had conflict markers in `state/VALIDATION_LOG.md`.
- The draft C-002 branch emitted not-evaluated claims as `SeverityBand.UNKNOWN`, but its four unsupported-category ruleset entries still declared `severity_on_fail: informational`, and the C-002 unit test asserted `SeverityBand.INFORMATIONAL` for that metadata.
- Session 2 sent Session 1 a coordination note to correct the C-002 handoff before landing.
- Non-mutating `git merge-tree main codex/session1-lane-c` reported conflicts only in `state/PROJECT_STATE.md`, `state/VALIDATION_LOG.md`, and `state/WORKLOG.md`; no report/API code conflicts were identified.
- Default PowerShell verification passed after this state update: workspace validation, 244 backend tests, lint, and mypy clean; DB smoke skipped by default.

**Residual risk:**

- D-000 should remain blocked until C-002 is canonical on root `main` with both UNKNOWN claim behavior and `severity_on_fail: unknown` ruleset metadata for the four unsupported categories.
- D-001 remains blocked until D-000 completes.

## 2026-06-04 Session 2 API unknown surfacing regression

**Commands run:**

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/api/test_api_scaffold.py tests/api/test_db_session.py
ruff check app/api app/reports app/db tests/api tests/reports
mypy app/api app/reports app/db tests/api tests/reports
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/reports tests/api
py -3.12 -m pytest --collect-only -q
Set-Location ..
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

**Results:**

- API report-run regression passes: source-failure evidence generated by existing rules appears in the response `unknowns` list.
- Focused API checks pass: 8 tests.
- Lane D report/API checks pass: 18 tests with DB smoke enabled.
- Targeted Lane D ruff passes.
- Targeted Lane D mypy passes: no issues in 25 source/test files.
- Full collection reports 244 tests.
- Full PowerShell verification passes with DB smoke enabled: 244 tests; lint clean; mypy clean (87 source files); migrations/seeds apply; DB smoke passes.

**Residual risk:**

- D-000 remains blocked on C-002 for unsupported categories specifically; this test proves the existing API/report path preserves UNKNOWN claims once generated.
- Full D-001 DB-backed API wiring remains blocked until C-002 and D-000 complete.

## 2026-06-04 Session 2 Lane D boundary split and DB session pre-work

**Commands run:**

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/api/test_db_session.py
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/reports tests/api
ruff check app/api app/reports app/db tests/api tests/reports
mypy app/api app/reports app/db tests/api tests/reports
py -3.12 -m pytest --collect-only -q
Set-Location ..
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

**Results:**

- `backend/app/db/session.py` exists and `get_db_session()` delegates to `get_session()` from `app.db.engine`.
- `backend/tests/api/test_db_session.py` passes and proves the dependency delegates without opening a DB connection.
- Lane D report/API tests pass: 17 tests with DB smoke enabled.
- Targeted Lane D ruff passes.
- Targeted Lane D mypy passes: no issues in 25 source/test files.
- Full collection reports 243 tests.
- Full PowerShell verification passes with DB smoke enabled: 243 tests; lint clean; mypy clean (87 source files); migrations/seeds apply; DB smoke passes.

**Residual risk:**

- D-000 report surfacing is blocked until Lane C C-002 emits UNKNOWN claims for unsupported-category SOURCE_FAILURE evidence.
- Full D-001 DB-backed API wiring remains blocked until C-002 and D-000 complete; `api/dependencies.py`, `main.py`, and DB-backed API integration tests were intentionally not modified in this pass.

## 2026-06-04 Session 1 C-001 ORM stabilization

**Commands run:**

```powershell
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
Set-Location backend
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/claims_engine/test_sqlalchemy_claim_repo.py
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/evidence_ledger tests/claims_engine
ruff check app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
mypy app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
rg -n "from app\.source_registry|from app\.area_geometry|import app\.source_registry|import app\.area_geometry" app/evidence_ledger app/claims_engine
py -3.12 -m pytest --collect-only -q
Set-Location ..
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

**Results:**

- Initial full gate failed in `tests/claims_engine/test_sqlalchemy_claim_repo.py`: ORM flush could not resolve cross-schema FK metadata for `claims.claim_evidence.evidence_id -> evidence.observations.evidence_id`.
- First repair mapped cross-schema DB FKs in `backend/app/claims_engine/models.py` as scalar UUID columns, leaving DB migrations as the FK authority and avoiding cross-lane metadata requirements.
- Second repair flushed the parent `ClaimModel` before adding claim/evidence links and verification tasks, preserving DB FK order.
- Exact failing claim DB file passes: 4 tests.
- Lane C evidence/claims tests pass: 137 tests with DB smoke enabled.
- Targeted Lane C ruff passes.
- Targeted Lane C mypy passes: no issues in 25 source/test files.
- Lane C cross-lane import scan returns 0 matches.
- Full collection reports 242 tests.
- Full PowerShell verification passes with DB smoke enabled: 242 tests; lint clean; mypy clean (85 source files); migrations/seeds apply; DB smoke passes.

**Residual risk:**

- C-001 is now live-verified after repair.
- Level 6 remains partial until C-002 adds the four not-evaluated categories or equivalent explicit unknown/report surfacing without crossing lane ownership boundaries.
- D-001 remains a Level 7 dependency and should not claim pass until Lane C Level 6 gates are complete.

## 2026-06-04 Lane C TC-150 DB-backed claim persistence

**Commands run:**

```powershell
Set-Location backend
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/claims_engine/test_sqlalchemy_claim_repo.py
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/evidence_ledger tests/claims_engine
ruff check app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
mypy app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
rg -n "from app\.source_registry|from app\.area_geometry|import app\.source_registry|import app\.area_geometry" app/evidence_ledger app/claims_engine
py -3.12 -m pytest --collect-only -q
Set-Location ..
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

**Results:**

- New claim DB tests pass: 4 tests with DB smoke enabled.
- Lane C evidence/claims tests pass: 130 tests with DB smoke enabled.
- `SqlAlchemyClaimRepository` persists claims to `claims.claims`.
- Claim/evidence links persist to `claims.claim_evidence`.
- Verification tasks persist to `claims.verification_tasks`.
- Rule metadata and evidence ordering are preserved in `claims.claims.metadata`.
- DB-backed service tests cover durable claim round-trip, unknown/source-failure claim persistence, duplicate claim rejection, and rollback behavior.
- Added `docs/adr/lane-c-rules.md` for deterministic rules, evidence links, rule metadata, verification tasks, hard gates, and deferred suitability scoring.
- Targeted Lane C ruff passes.
- Targeted Lane C mypy passes: no issues in 23 source/test files.
- Lane C cross-lane import scan returns 0 matches.
- Full collection reports 235 tests.
- Full PowerShell verification passes with DB smoke enabled: 235 tests; lint clean; mypy clean (81 source files); DB smoke passes.

**Residual risk:**

- Level 6 remains partial: durable claim persistence is in place, but the remaining minimum rule categories still need fixture-backed implementation or explicit not-evaluated labeling in report/API output.
- Rule metadata remains metadata-preserved until a coordinated schema migration promotes it to first-class columns.

## 2026-06-04 Lane C TC-140 evidence geometry/spatial precision and automation guardrails

**Commands run:**

```powershell
rg -n --hidden --glob '!.git/**' --glob '!node_modules/**' --glob '!archive/**' -i "P[o]stToolUse|h[o]oks\.json|\.codex[\\/]h[o]oks|\.claude[\\/]settings|h[o]ok" .
Test-Path (Join-Path .\.claude 'settings.json'); Test-Path (Join-Path .\.codex ('h' + 'ooks.json')); Test-Path .\local_artifacts\psql.cmd
.\scripts\agent-context-check.ps1
Set-Location backend
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/evidence_ledger
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/evidence_ledger tests/claims_engine
ruff check app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
mypy app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
rg -n "from app\.source_registry|from app\.area_geometry|import app\.source_registry|import app\.area_geometry" app/evidence_ledger app/claims_engine
py -3.12 -m pytest --collect-only -q
Set-Location ..
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

**Results:**

- Automation sweep returns 0 active matches; the Claude/Codex automatic config paths are absent; `local_artifacts/psql.cmd` remains present.
- Updated `CLAUDE.md`, `AGENTS.md`, and repo-local Claude skills so Windows verification uses PowerShell wrappers instead of automatic or `.sh` execution.
- Initial evidence DB test run failed on `psycopg.errors.AmbiguousParameter` for the nullable geometry bind inside a SQL `CASE`; fixed by casting the GeoJSON bind to text in the PostGIS insert expression.
- Cleaned 22 committed `core.areas` rows with test-only label `evidence fixture area` left by the failed DB run; no linked evidence or audit rows were present.
- Lane C evidence tests pass: 62 tests with DB smoke enabled.
- Lane C evidence/claims tests pass: 126 tests with DB smoke enabled.
- Targeted Lane C ruff passes.
- Targeted Lane C mypy passes: no issues in 22 source/test files.
- Lane C cross-lane import scan returns 0 matches.
- Full collection reports 231 tests.
- Full PowerShell verification passes with DB smoke enabled: 231 tests; lint clean; mypy clean (80 source files); DB smoke passes.

**Residual risk:**

- Level 5 evidence ledger now passes for the fixture-backed DB path.
- Level 6 remains partial because claims and claim/evidence links are still in-memory, not durably persisted.
- Contract-only evidence metadata fields remain metadata-preserved until a coordinated schema migration promotes them.

## 2026-06-04 Lane C TC-130 DB-backed evidence repository and audit log

**Commands run:**

```powershell
Set-Location backend
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/evidence_ledger
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/evidence_ledger tests/claims_engine
ruff check app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
mypy app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
rg -n "from app\.source_registry|from app\.area_geometry|import app\.source_registry|import app\.area_geometry" app/evidence_ledger app/claims_engine
py -3.12 -m pytest --collect-only -q
Set-Location ..
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

**Results:**

- Lane C evidence/claims tests pass: 122 tests with DB smoke enabled.
- `SqlAlchemyEvidenceRepository` persists to `evidence.observations` and round-trips source observations, source failures, spatial intersections, derived metrics, document extracts, and human verification notes.
- Contract-only fields are preserved in `evidence.observations.metadata`: `source_id`, `evidence_code`, `observed_at`, and `superseded_by`.
- DB-backed service tests cover invalid payload rejection before storage, supersession without overwrite, deterministic retrieval by area/source/type, rollback behavior, and durable audit events.
- `SqlAlchemyEvidenceAuditLog` persists create/supersede events in `audit.events`.
- Targeted Lane C ruff passes.
- Targeted Lane C mypy passes: no issues in 22 source/test files.
- Lane C cross-lane import scan returns 0 matches.
- Full PowerShell verification passes with DB smoke enabled: 227 collected tests; lint clean; mypy clean (80 source files); DB smoke passes.

**Residual risk:**

- Level 5 remains partial: `EvidenceContract` does not yet expose geometry/SRID/spatial-precision fields, so `evidence.observations.geometry` is not mapped by the repository.
- `source_id`, `evidence_code`, `observed_at`, and `superseded_by` are metadata-preserved rather than first-class columns until a coordinated schema migration promotes them.

## 2026-06-04 Lane B TB-090 supported domain area-type mapping

**Commands run:**

```powershell
Set-Location backend
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/area_geometry
ruff check app/area_geometry app/domain/area_contracts.py tests/area_geometry
mypy app/area_geometry app/domain/area_contracts.py tests/area_geometry
py -3.12 -m pytest --collect-only -q
Set-Location ..
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

**Results:**

- Lane B area tests pass: 46 tests with DB smoke enabled.
- `SqlAlchemyAreaRepository` supports all six Level 4 domain area types: `parcel_like`, `drawn_polygon`, `multi_polygon`, `locality`, `buffer`, and `generated_candidate`.
- Exact domain area type is stored in `core.areas.metadata.domain_area_type`; `multi_polygon` uses DB bucket `polygon`, and `buffer` uses DB bucket `generated_candidate`.
- Reads fail closed when `metadata.domain_area_type` conflicts with stored `core.areas.area_type`.
- Targeted Lane B ruff passes.
- Targeted Lane B mypy passes: no issues in 10 source/test files.
- Full PowerShell verification passes with DB smoke enabled: 216 collected tests; lint clean; mypy clean (78 source files); DB smoke passes.

**Residual risk:**

- Broader spatial query/source-feature geometry support remains deferred; current relation helpers intentionally support fixture polygon/multipolygon comparison geometry only.
- Area version rows still preserve prior geometry and change reason only because that is the current schema shape; preserving prior source/confidence metadata would require a coordinated schema/ADR pass.

## 2026-06-04 Lane B TB-080 DB-backed area versioning

**Commands run:**

```powershell
Set-Location backend
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/area_geometry
ruff check app/area_geometry app/domain/area_contracts.py tests/area_geometry
mypy app/area_geometry app/domain/area_contracts.py tests/area_geometry
py -3.12 -m pytest --collect-only -q
Set-Location ..
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

**Results:**

- Lane B area tests pass: 41 tests with DB smoke enabled.
- `AreaVersionContract` captures immutable prior-geometry version rows from `core.area_versions`.
- `AreaVersionModel` maps `core.area_versions`, including the `(area_id, version_num)` uniqueness constraint and SRID 4326 MultiPolygon geometry type.
- `SqlAlchemyAreaRepository.replace_geometry` stores the prior canonical geometry in `core.area_versions` before updating `core.areas`.
- `SqlAlchemyAreaRepository.list_versions` returns ordered prior-geometry versions as typed contracts.
- DB tests cover immutable prior-geometry storage, version sequencing, missing-area no-op, invalid replacement rejection, and rollback behavior.
- Targeted Lane B ruff passes.
- Targeted Lane B mypy passes: no issues in 10 source/test files.
- Full PowerShell verification passes with DB smoke enabled: 211 collected tests; lint clean; mypy clean (78 source files); DB smoke passes.

**Residual risk:**

- Superseded by TB-090: the `multi_polygon`/`buffer` domain-to-DB area-type mismatch was resolved for the current repository path with explicit `metadata.domain_area_type` preservation.
- Version rows preserve prior geometry and change reason only because that is the current schema shape; if source/confidence history must be immutable too, a coordinated schema/ADR pass is required.

## 2026-06-04 Lane B TB-070 PostGIS spatial relation helper

**Commands run:**

```powershell
Set-Location backend
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/area_geometry
ruff check app/area_geometry app/domain/area_contracts.py tests/area_geometry
mypy app/area_geometry app/domain/area_contracts.py tests/area_geometry
py -3.12 -m pytest --collect-only -q
Set-Location ..
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

**Results:**

- Lane B area tests pass: 35 tests with DB smoke enabled.
- `AreaSpatialRelationContract` captures fixture-backed intersects, contains, distance, intersection area, intersection ratio, method, and screening caveat.
- `SqlAlchemyAreaRepository.get_spatial_relation` validates comparison GeoJSON/SRID before SQL and queries PostGIS `ST_Intersects`, `ST_Contains`, `ST_Distance`, and `ST_Intersection`.
- DB tests cover contained, disjoint, missing-area, wrong-SRID, empty-geometry, and unsupported-geometry-type behavior.
- Targeted Lane B ruff passes.
- Targeted Lane B mypy passes: no issues in 10 source/test files.
- Full PowerShell verification passes with DB smoke enabled: 205 collected tests; lint clean; mypy clean (78 source files); DB smoke passes.

**Residual risk:**

- Area versioning is still pending for Level 4.
- The spatial helper intentionally supports fixture polygon/multipolygon comparison geometry only; broader source-feature geometry types require a scoped plan.

## 2026-06-04 Lane B TB-060 PostGIS area metrics read model

**Commands run:**

```powershell
Set-Location backend
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/area_geometry
ruff check app/area_geometry app/domain/area_contracts.py tests/area_geometry
mypy app/area_geometry app/domain/area_contracts.py tests/area_geometry
py -3.12 -m pytest --collect-only -q
Set-Location ..
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

**Results:**

- Lane B area tests pass: 27 tests with DB smoke enabled.
- `AreaMetricsContract` captures SRID, centroid GeoJSON, bbox GeoJSON, geodesic area in square meters, measurement method, and screening caveat.
- `SqlAlchemyAreaRepository.get_metrics` reads PostGIS generated `centroid` and `bbox` columns and `ST_Area(geom::geography)` without modifying canonical geometry.
- Polygon and MultiPolygon fixture rows return deterministic SRID, Point centroid, Polygon bbox, positive area, and a non-survey caveat.
- Targeted Lane B ruff passes.
- Targeted Lane B mypy passes: no issues in 10 source/test files.
- Full PowerShell verification passes with DB smoke enabled: 197 collected tests; lint clean; mypy clean (78 source files); DB smoke passes.

**Residual risk:**

- Spatial query helpers and area versioning are still pending for Level 4.
- Metrics are screening values from stored geometry, not legal/survey acreage.

## 2026-06-04 Lane B TB-050 PostGIS area repository

**Commands run:**

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/area_geometry
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/area_geometry/test_sqlalchemy_area_repo.py
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/area_geometry
ruff check app/area_geometry tests/area_geometry
mypy app/area_geometry tests/area_geometry
py -3.12 -m pytest --collect-only -q
Set-Location ..
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

**Results:**

- Lane B area tests pass: 22 tests with DB smoke enabled.
- `SqlAlchemyAreaRepository` round-trips Polygon and MultiPolygon fixtures through `core.areas` as SRID 4326 PostGIS MultiPolygon geometry.
- Geometry source, confidence, and validated flags round-trip through the DB-backed repository.
- Domain area types without a safe `core.area_type` mapping (`multi_polygon`, `buffer`) fail closed rather than being silently mapped to parcel/corridor semantics.
- Targeted Lane B ruff passes.
- Targeted Lane B mypy passes: no issues in 9 source/test files.
- Full PowerShell verification passes with DB smoke enabled: 192 collected tests; lint clean; mypy clean (78 source files); DB smoke passes.

**Residual risk:**

- Area metrics/read model, spatial query helpers, and area versioning are still pending for Level 4.
- The repository intentionally does not support every `core.area_type` enum value until domain/schema alignment is planned.

## 2026-06-04 source-governance and DB verification hardening

**Commands run:**

```powershell
$env:PYTHONPATH='.'; py -3.12 -m pytest -q tests/source_registry/test_source_service.py
py -3.12 scripts/db_smoke_check.py
$env:PYTHONPATH='.'; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/reports/test_report_service.py tests/reports/test_report_repository.py
$env:PYTHONPATH='.'; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/source_registry/test_source_provenance.py tests/source_registry/test_source_service.py
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; $env:PYTHONPATH='.'; py -3.12 -m pytest --collect-only -q
```

**Results:**

- Source service tests pass: 19 tests.
- Report DB/repository and source provenance targeted tests pass with `RUN_DB_SMOKE=1`.
- PowerShell verification now selects Python 3.12.10 even when `python` on PATH points at Python 3.11.
- Full verification passes with DB smoke enabled: 186 tests pass; ruff clean; mypy clean (76 source files).
- DB smoke now validates required schemas, 18 tables, 11 column groups, 2 enums, 8 foreign keys, seeded sources, and seeded intents.

**Residual risk:**

- The new GitHub Actions PostGIS job is defined but not yet proven by a remote CI run in this local-only workspace.
- Lane D remains a partial report-run persistence harness until Lane B area persistence and Lane C durable evidence/claim/rule-execution persistence are wired underneath it.

## 2026-06-03 Windows PowerShell verification wrapper

**Commands run:**

```powershell
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

**Results:**

- PowerShell-native verification wrapper passes end to end without launching Git Bash.
- Workspace validation passes, including agent context checks and JSON file checks.
- Backend tests pass: 179 tests.
- Backend lint passes.
- Backend typecheck passes: no issues in 76 source files.
- DB migration + smoke passes using the local `psql` shim in `local_artifacts`.

**Residual risk:**

- The Bash entrypoints still exist for Linux/CI compatibility; Windows users should use `.\scripts\verify.ps1` to avoid the separate Git Bash launcher.
- The wrapper now owns the local `psql` PATH shim, so future DB-smoke changes should keep that prepend in sync.

## 2026-06-03 Lane D TD-040 persisted report runs

**Commands run:**

```bash
Set-Location .\backend; $env:PYTHONPATH='.'; python -m pytest tests/reports tests/api -q
Set-Location .\backend; $env:PYTHONPATH='.'; $env:RUN_DB_SMOKE='1'; python -m pytest tests/reports tests/api -q
Set-Location .\backend; ruff check app/reports app/api app/main.py app/domain/report_contracts.py tests/reports tests/api
Set-Location .\backend; mypy app/reports app/api app/main.py app/domain/report_contracts.py tests/reports tests/api
& 'C:\Program Files\Git\bin\bash.exe' -lc 'cd /c/Users/benny/OneDrive/Desktop/land_diligence_dual_agent_workspace && PATH="$PWD/local_artifacts:$PATH" RUN_DB_SMOKE=1 ./scripts/verify.sh'
Set-Location .\backend; $env:PYTHONPATH='.'; $env:RUN_DB_SMOKE='1'; python -m pytest --collect-only -q
```

**Results:**

- Lane D report/API tests pass: 16 tests.
- SQLAlchemy-backed report persistence round-trips through `reports.report_runs` and a machine-readable JSON artifact under `OBJECT_STORE_ROOT`.
- Lane D targeted ruff passes.
- Lane D targeted mypy passes: no issues in 21 source/test files.
- Full verification through explicit Git Bash passes: agent context check ok, workspace validation ok, JSON check ok (14 files), backend tests pass, ruff clean, mypy clean (72 source files), DB smoke passes.
- Test collection reports 173 tests.
- Docker Desktop Linux engine is running; DB smoke is available.

**Residual risk:**

- The default in-memory API scaffold still exists for fixture tests; the persisted report path is exercised through repository injection and round-trip tests.
- Shared-schema alignment remains the next coordinated pass before editing `schemas/*.json`.

## 2026-06-03 Lane D TD-050 protocol adapter wiring

**Commands run:**

```bash
cd backend && PYTHONPATH=. python -m pytest -q tests/reports/test_adapters.py tests/reports/test_report_service.py tests/api/test_api_scaffold.py
cd backend && PYTHONPATH=. python -m pytest -q tests/reports tests/api
cd backend && PYTHONPATH=. python -m pytest --collect-only -q tests/reports tests/api
cd backend && PYTHONPATH=. python -m pytest --collect-only -q
cd backend && ruff check app/reports app/api tests/reports tests/api
cd backend && mypy app/reports app/api tests/reports tests/api
C:/Program Files/Git/bin/bash.exe ./scripts/verify.sh
```

**Results:**

- Lane D report/API tests pass: 15 tests.
- Cross-lane adapter wiring preserves the existing report-service behavior and guardrails while making the `EvidenceService` protocol seam explicit.
- Lane D targeted ruff passes.
- Lane D targeted mypy passes: no issues in 16 source/test files.
- Full verification through explicit Git Bash passes: agent context check ok, workspace validation ok, JSON check ok (14 files), backend tests pass, ruff clean, mypy clean (69 source files).
- Test collection reports 172 tests.
- Docker client is installed, but Docker Desktop Linux engine is not running; DB smoke remains blocked.

**Residual risk:**

- TD-050 is intentionally in-memory only. Persisted report runs still wait on DB smoke / Lane A TA-060.
- The adapter layer is thin by design; its value is architectural clarity and protocol isolation, not new behavior.

## 2026-06-03 Lane C TC-120 water-context hard-gate fixture coverage

**Commands run:**

```bash
cd backend && PYTHONPATH=. python -m pytest -q tests/claims_engine/test_rule_engine.py tests/evidence_ledger/test_payload_validation.py
cd backend && PYTHONPATH=. python -m pytest -q tests/evidence_ledger tests/claims_engine
rg -n "from app\.source_registry|from app\.area_geometry|import app\.source_registry|import app\.area_geometry" backend/app/evidence_ledger backend/app/claims_engine
cd backend && ruff check app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
cd backend && mypy app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
C:/Program\ Files/Git/bin/bash.exe ./scripts/verify.sh
cd backend && PYTHONPATH=. python -m pytest --collect-only -q tests/claims_engine/test_rule_engine.py tests/evidence_ledger/test_payload_validation.py
cd backend && PYTHONPATH=. python -m pytest --collect-only -q tests/evidence_ledger tests/claims_engine
cd backend && PYTHONPATH=. python -m pytest --collect-only -q
docker info --format '{{.ServerVersion}}'
```

**Results:**

- Focused water/rule/payload tests pass: 71 tests.
- Lane C evidence/claims/rules tests pass: 111 tests.
- Cross-lane import scan returns no matches; Lane C still does not import Lane A/B modules.
- Lane C targeted ruff passes.
- Lane C targeted mypy passes: no issues in 20 source/test files.
- Full verification through explicit Git Bash passes: agent context check ok, workspace validation ok, JSON check ok (14 files), backend tests pass, ruff clean, mypy clean (67 source files).
- Test collection reports 168 tests.
- Docker client is installed, but Docker Desktop Linux engine is not running; DB smoke remains blocked.

**Residual risk:**

- TC-120 covers the water-context fixture hard gate only. It does not implement water-rights law, well-yield modeling, hauling legality, service availability, potable-water evaluation, or final water availability.
- A reviewer-found regression is covered: one internally contradictory water fixture record with both no-context and plausible-context true now emits review-only `WATER_EVIDENCE_NEEDS_REVIEW`, not `WATER_001`.
- The in-memory current-ruleset hard gates now cover flood, access, zoning, water, wetlands, and slope. Durable claim/rule persistence remains blocked by DB smoke and later repository work.
- `schemas/evidence_schema.json` remains broad and does not yet encode water fixture fields; shared-schema alignment remains a coordinated future pass.

## 2026-06-03 Lane C TC-110 zoning/use hard-gate fixture coverage

**Commands run:**

```bash
cd backend && PYTHONPATH=. python -m pytest -q tests/claims_engine/test_rule_engine.py tests/evidence_ledger/test_payload_validation.py
cd backend && PYTHONPATH=. python -m pytest -q tests/evidence_ledger tests/claims_engine
rg -n "from app\.source_registry|from app\.area_geometry|import app\.source_registry|import app\.area_geometry" backend/app/evidence_ledger backend/app/claims_engine
cd backend && ruff check app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
cd backend && mypy app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
C:/Program\ Files/Git/bin/bash.exe ./scripts/verify.sh
cd backend && PYTHONPATH=. python -m pytest --collect-only -q tests/claims_engine/test_rule_engine.py tests/evidence_ledger/test_payload_validation.py
cd backend && PYTHONPATH=. python -m pytest --collect-only -q tests/evidence_ledger tests/claims_engine
cd backend && PYTHONPATH=. python -m pytest --collect-only -q
docker info --format '{{.ServerVersion}}'
```

**Results:**

- Focused zoning/rule/payload tests pass: 60 tests.
- Lane C evidence/claims/rules tests pass: 100 tests.
- Cross-lane import scan returns no matches; Lane C still does not import Lane A/B modules.
- Lane C targeted ruff passes.
- Lane C targeted mypy passes: no issues in 20 source/test files.
- Full verification through explicit Git Bash passes: agent context check ok, workspace validation ok, JSON check ok (14 files), backend tests pass, ruff clean, mypy clean (67 source files).
- Test collection reports 157 tests.
- Docker client is installed, but Docker Desktop Linux engine is not running; DB smoke remains blocked.

**Residual risk:**

- TC-110 covers the zoning/use fixture hard gate only, including explicit prohibited/unsupported signals, allowed/no-claim evidence, incomplete/no-signal evidence, source failure, stale review, and mixed evidence. Water remains pending.
- Zoning/use outputs are screening-only and deliberately do not assert final legal use, zoning compliance, permit eligibility, vested rights, minimum lot-size compliance, or buildability.
- Durable claim/rule persistence remains blocked by DB smoke and later repository work.
- `schemas/evidence_schema.json` remains broad and does not yet encode zoning fixture fields; shared-schema alignment remains a coordinated future pass.

## 2026-06-03 Lane C TC-100 slope hard-gate fixture coverage

**Commands run:**

```bash
cd backend && PYTHONPATH=. python -m pytest -q tests/claims_engine/test_rule_engine.py tests/evidence_ledger/test_payload_validation.py
cd backend && PYTHONPATH=. python -m pytest -q tests/evidence_ledger tests/claims_engine
rg -n "from app\.source_registry|from app\.area_geometry|import app\.source_registry|import app\.area_geometry" backend/app/evidence_ledger backend/app/claims_engine
cd backend && ruff check app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
cd backend && mypy app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
C:/Program\ Files/Git/bin/bash.exe ./scripts/verify.sh
cd backend && PYTHONPATH=. python -m pytest --collect-only -q
docker info --format '{{.ServerVersion}}'
```

**Results:**

- Focused slope/rule/payload tests pass: 50 tests.
- Lane C evidence/claims/rules tests pass: 90 tests.
- Cross-lane import scan returns no matches; Lane C still does not import Lane A/B modules.
- Lane C targeted ruff passes.
- Lane C targeted mypy passes: no issues in 20 source/test files.
- Full verification through explicit Git Bash passes: agent context check ok, workspace validation ok, JSON check ok (14 files), backend tests pass, ruff clean, mypy clean (67 source files).
- Test collection reports 145 tests.
- Docker client is installed, but Docker Desktop Linux engine is not running; DB smoke remains blocked.

**Residual risk:**

- TC-100 covers the slope/buildability fixture hard gate only. Zoning and water hard-gate domains remain pending.
- Slope outputs are screening proxies and deliberately do not assert final buildability, site-plan approval, engineering feasibility, or a permitted building envelope.
- Durable claim/rule persistence remains blocked by DB smoke and later repository work.
- `schemas/evidence_schema.json` remains broad and does not yet encode slope fixture fields; shared-schema alignment remains a coordinated future pass.

## 2026-06-03 Lane C TC-090 wetlands hard-gate fixture coverage

**Commands run:**

```bash
cd backend && PYTHONPATH=. python -m pytest -q tests/claims_engine/test_rule_engine.py tests/evidence_ledger/test_payload_validation.py
cd backend && PYTHONPATH=. python -m pytest -q tests/evidence_ledger tests/claims_engine
rg -n "from app\.source_registry|from app\.area_geometry|import app\.source_registry|import app\.area_geometry" backend/app/evidence_ledger backend/app/claims_engine
cd backend && ruff check app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
cd backend && mypy app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
C:/Program\ Files/Git/bin/bash.exe ./scripts/verify.sh
cd backend && PYTHONPATH=. python -m pytest --collect-only -q
docker info --format '{{.ServerVersion}}'
```

**Results:**

- Focused wetlands/rule/payload tests pass: 43 tests.
- Lane C evidence/claims/rules tests pass: 83 tests.
- Cross-lane import scan returns no matches; Lane C still does not import Lane A/B modules.
- Lane C targeted ruff passes.
- Lane C targeted mypy passes: no issues in 20 source/test files.
- Full verification through explicit Git Bash passes: agent context check ok, workspace validation ok, JSON check ok (14 files), backend tests pass, ruff clean, mypy clean (67 source files).
- Test collection reports 138 tests.
- Docker client is installed, but Docker Desktop Linux engine is not running; DB smoke remains blocked.

**Residual risk:**

- TC-090 covers the wetlands fixture hard gate only. Zoning, slope, and water hard-gate domains remain pending.
- Wetland outputs are screening-only and deliberately do not assert jurisdictional wetlands, delineation results, permitting outcomes, or final buildability.
- Durable claim/rule persistence remains blocked by DB smoke and later repository work.
- `schemas/evidence_schema.json` remains broad and does not yet encode wetland fixture fields; shared-schema alignment remains a coordinated future pass.

## 2026-06-03 Lane C TC-080 access hard-gate fixture coverage

**Commands run:**

```bash
cd backend && PYTHONPATH=. python -m pytest -q tests/claims_engine/test_rule_engine.py tests/evidence_ledger/test_payload_validation.py
cd backend && PYTHONPATH=. python -m pytest -q tests/evidence_ledger tests/claims_engine
rg -n "from app\.source_registry|from app\.area_geometry|import app\.source_registry|import app\.area_geometry" backend/app/evidence_ledger backend/app/claims_engine
cd backend && ruff check app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
cd backend && mypy app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
C:/Program\ Files/Git/bin/bash.exe ./scripts/verify.sh
cd backend && PYTHONPATH=. python -m pytest --collect-only -q
docker info --format '{{.ServerVersion}}'
```

**Results:**

- Focused access/rule/payload tests pass: 36 tests.
- Lane C evidence/claims/rules tests pass: 76 tests.
- Cross-lane import scan returns no matches; Lane C still does not import Lane A/B modules.
- Lane C targeted ruff passes.
- Lane C targeted mypy passes: no issues in 20 source/test files.
- Full verification through explicit Git Bash passes: agent context check ok, workspace validation ok, JSON check ok (14 files), backend tests pass, ruff clean, mypy clean (67 source files).
- Test collection reports 131 tests.
- Docker client is installed, but Docker Desktop Linux engine is not running; DB smoke remains blocked.

**Residual risk:**

- TC-080 covers the access fixture hard gate only. Zoning, wetlands, slope, and water hard-gate domains remain pending.
- Road adjacency remains a physical proxy only; the rule output deliberately avoids asserting recorded legal access or easements.
- Durable claim/rule persistence remains blocked by DB smoke and later repository work.
- `schemas/evidence_schema.json` remains broad and does not yet encode access adjacency fixture fields; shared-schema alignment remains a coordinated future pass.

## 2026-06-03 Lane D TD-030 in-memory ReportRunService

**Commands run:**

```bash
cd backend && PYTHONPATH=. python -m pytest -q tests/reports tests/api
bash ./scripts/verify.sh
cd backend && PYTHONPATH=. python -m pytest -q
cd backend && ruff check .
cd backend && mypy app tests
docker info --format '{{.ServerVersion}}'
C:/Program\ Files/Git/bin/bash.exe ./scripts/verify.sh
cd backend && PYTHONPATH=. python -m pytest --collect-only -q
```

**Results:**

- Lane D report/API tests pass: 11 tests.
- Plain `bash ./scripts/verify.sh` fails on this machine because `bash` resolves to the Windows WSL launcher and `/bin/bash` is unavailable.
- Workspace/agent-context equivalent checks pass in PowerShell; JSON check passes: 14 files.
- Full backend test suite passes: 126 tests.
- Ruff passes.
- Mypy passes: no issues in 67 source files.
- Full verification through explicit Git Bash passes: agent context check ok, workspace validation ok, JSON check ok (14 files), backend tests pass, ruff clean, mypy clean (67 source files).
- Test collection reports 126 tests.
- Docker client is installed, but Docker Desktop Linux engine is not running; DB smoke remains blocked.

**Residual risk:**

- TD-030 is in-memory only. Report runs are stored inside the per-app ReportRunService and are not durable.
- Report output now contains evidence-linked claims, unknowns, caveats, red flags, verification tasks, source manifest, and artifact metadata, but no persisted report sections or exported artifacts exist yet.
- Report source manifest is a fixture-scope snapshot, not a durable source-version/retrieval-run snapshot.
- DB-backed report persistence remains blocked until Docker/PostGIS smoke is available.

## 2026-06-03 Lane D TD-020 in-memory API scaffold

**Commands run:**

```bash
cd backend && PYTHONPATH=. python -m pytest tests/reports/ tests/api/ -v
cd backend && ruff check app/reports app/api app/main.py app/domain/report_contracts.py tests/reports tests/api
cd backend && mypy app/reports app/api app/main.py app/domain/report_contracts.py tests/reports tests/api
C:/Program\ Files/Git/bin/bash.exe ./scripts/verify.sh
cd backend && PYTHONPATH=. python -m pytest --collect-only -q
docker info --format '{{.ServerVersion}}'
```

**Results:**

- Lane D report/API tests pass: 7 tests.
- Lane D targeted ruff passes.
- Lane D targeted mypy passes: no issues in 14 source/test files.
- Full verification through Git Bash passes: agent context check ok, workspace validation ok, JSON check ok (14 files), backend tests pass, ruff clean, mypy clean (65 source files).
- Test collection reports 122 tests.
- Docker client is installed, but Docker Desktop Linux engine is not running; DB smoke remains blocked.

**Residual risk:**

- TD-020 is an in-memory API scaffold only. ReportRunService, evidence-linked report output, unknown/source-failure report content, artifact metadata, and reproducibility snapshots remain pending.
- Report runs created through `/report-runs` are per-app in-memory records, not persisted durable report runs.
- The evidence router exposes read-only area-filtered evidence; evidence creation remains service-level and future workflow/integration work.
- DB-backed report persistence remains blocked until Docker/PostGIS smoke is available.

## 2026-06-03 Lane C TC-070 contradiction/stale rule handling

**Commands run:**

```bash
cd backend && PYTHONPATH=. python -m pytest tests/claims_engine/test_rule_engine.py tests/evidence_ledger/test_payload_validation.py -v
cd backend && PYTHONPATH=. python -m pytest tests/evidence_ledger/ tests/claims_engine/ -v
cd backend && ruff check app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
cd backend && mypy app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
rg -n "from app\.source_registry|from app\.area_geometry|import app\.source_registry|import app\.area_geometry" backend/app/evidence_ledger backend/app/claims_engine
C:/Program\ Files/Git/bin/bash.exe ./scripts/verify.sh
cd backend && PYTHONPATH=. python -m pytest --collect-only -q
docker info --format '{{.ServerVersion}}'
```

**Results:**

- Focused rule/payload tests pass: 28 tests.
- Lane C evidence/claims/rules tests pass: 69 tests.
- Lane C targeted ruff passes.
- Lane C targeted mypy passes: no issues in 20 source/test files.
- Cross-lane import scan returns no matches; Lane C still does not import Lane A/B modules.
- Full verification through Git Bash passes: agent context check ok, workspace validation ok, JSON check ok (14 files), backend tests pass, ruff clean, mypy clean (60 source files).
- Test collection reports 117 tests.
- Docker client is installed, but Docker Desktop Linux engine is not running; DB smoke remains blocked.

**Residual risk:**

- TC-070 is limited to the in-memory flood-rule slice. Broader hard-gate domains in `config/ruleset_homestead_mvp.yaml` remain pending.
- Stale evidence uses an explicit fixture `source_stale` flag. It does not implement live source freshness calculations, source-version aging, or production freshness monitoring.
- Durable claim/rule persistence and DB-backed evidence freshness remain blocked by DB smoke and later repository work.
- `schemas/evidence_schema.json` remains broad and does not yet encode the `source_stale` fixture field or other type-specific observed_value constraints; shared-schema alignment remains a coordinated future pass.

## 2026-06-03 Lane C TC-060 evidence audit events

**Commands run:**

```bash
cd backend && PYTHONPATH=. python -m pytest tests/evidence_ledger/ tests/claims_engine/ -v
cd backend && ruff check app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
cd backend && mypy app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
rg -n "from app\.source_registry|from app\.area_geometry|import app\.source_registry|import app\.area_geometry" backend/app/evidence_ledger backend/app/claims_engine
C:/Program\ Files/Git/bin/bash.exe ./scripts/verify.sh
cd backend && PYTHONPATH=. python -m pytest --collect-only -q
docker info --format '{{.ServerVersion}}'
```

**Results:**

- Lane C evidence/claims/rules tests pass: 63 tests.
- Lane C targeted ruff passes.
- Lane C targeted mypy passes: no issues in 20 source/test files.
- Cross-lane import scan returns no matches; Lane C still does not import Lane A/B modules.
- Full verification through Git Bash passes: agent context check ok, workspace validation ok, JSON check ok (14 files), backend tests pass, ruff clean, mypy clean (60 source files).
- Test collection reports 111 tests.
- Docker client is installed, but Docker Desktop Linux engine is not running; DB smoke remains blocked.

**Residual risk:**

- Audit events are implemented only for the in-memory EvidenceService path. Durable audit persistence remains blocked by DB smoke and later repository work.
- `schemas/evidence_schema.json` remains broad and does not yet encode the same type-specific observed_value constraints; update requires a coordinated shared-schema pass.
- Contradiction, needs-review, stale-evidence, and broader ruleset categories remain pending.
- DB smoke remains unavailable until Docker Desktop starts.

## 2026-06-03 Lane C TC-050 evidence payload validation

**Commands run:**

```bash
cd backend && PYTHONPATH=. python -m pytest tests/evidence_ledger/ tests/claims_engine/ -v
cd backend && ruff check app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
cd backend && mypy app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
rg -n "from app\.source_registry|from app\.area_geometry|import app\.source_registry|import app\.area_geometry" backend/app/evidence_ledger backend/app/claims_engine
C:/Program\ Files/Git/bin/bash.exe ./scripts/verify.sh
cd backend && PYTHONPATH=. python -m pytest --collect-only -q
docker info --format '{{.ServerVersion}}'
```

**Results:**

- Lane C evidence/claims/rules tests pass: 59 tests.
- Lane C targeted ruff passes.
- Lane C targeted mypy passes: no issues in 18 source/test files.
- Cross-lane import scan returns no matches; Lane C still does not import Lane A/B modules.
- Payload tests cover allowed `flood_zone_code` spatial results and reject `intersection_ratio` above 1.
- Full verification through Git Bash passes: agent context check ok, workspace validation ok, JSON check ok (14 files), backend tests pass, ruff clean, mypy clean (59 source files).
- Test collection reports 107 tests.
- Docker client is installed, but Docker Desktop Linux engine is not running; DB smoke remains blocked.

**Residual risk:**

- Payload validation is implemented in the in-memory EvidenceService path only. Durable DB enforcement remains blocked by DB smoke and later repository work.
- `schemas/evidence_schema.json` remains broad and does not yet encode the same type-specific observed_value constraints; update requires a coordinated shared-schema pass.
- L5-010 audit events remain unimplemented.

## 2026-06-03 Lane C TC-040 deterministic rule slice

**Commands run:**

```bash
cd backend && PYTHONPATH=. python -m pytest tests/claims_engine/test_rule_engine.py -v
cd backend && PYTHONPATH=. python -m pytest tests/evidence_ledger/ tests/claims_engine/ -v
cd backend && ruff check app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
cd backend && mypy app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
rg -n "from app\.source_registry|from app\.area_geometry|import app\.source_registry|import app\.area_geometry" backend/app/evidence_ledger backend/app/claims_engine
cd backend && PYTHONPATH=. python -m pytest --collect-only -q
C:/Program\ Files/Git/bin/bash.exe ./scripts/verify.sh
```

**Results:**

- Rule-engine focused tests pass: 9 tests.
- Lane C evidence/claims tests pass: 45 tests.
- Lane C targeted ruff passes.
- Lane C targeted mypy passes: no issues in 16 source/test files.
- Cross-lane import scan returns no matches; Lane C still does not import Lane A/B modules.
- Test collection reports 93 tests.
- Full verification through Git Bash passes: agent context check ok, workspace validation ok, JSON check ok (14 files), backend tests pass, ruff clean, mypy clean (56 source files).
- DB smoke skipped because `RUN_DB_SMOKE=1` was not set and Docker Desktop is not running.

**Residual risk:**

- TC-040 covers one deterministic flood hard-gate only. Full Level 6 still needs broader rules, stale evidence handling, contradiction handling, and report-run integration.
- Rules are not durably persisted; DB-backed claim/report storage remains blocked by Docker/PostGIS smoke.
- L5-002 payload schema validation and L5-010 audit events remain unimplemented.
- `schemas/claim_schema.json` and `schemas/evidence_schema.json` remain shared-contract drift risks and need a schema alignment pass.

## 2026-06-03 Lane C TC-030 claim service

**Commands run:**

```bash
cd backend && PYTHONPATH=. python -m pytest tests/evidence_ledger/ tests/claims_engine/ -v
cd backend && ruff check app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
cd backend && mypy app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
rg -n "from app\.source_registry|from app\.area_geometry|import app\.source_registry|import app\.area_geometry" backend/app/evidence_ledger backend/app/claims_engine
C:/Program\ Files/Git/bin/bash.exe ./scripts/verify.sh
cd backend && PYTHONPATH=. python -m pytest --collect-only -q
```

**Results:**

- Lane C evidence/claims tests pass: 35 tests.
- Lane C targeted ruff passes.
- Lane C targeted mypy passes: no issues in 14 source/test files.
- Cross-lane import scan returns no matches; Lane C still does not import Lane A/B modules.
- Full verification through Git Bash passes: agent context check ok, workspace validation ok, JSON check ok (14 files), backend tests pass, ruff clean, mypy clean (54 source files).
- Test collection reports 83 tests.
- DB smoke skipped because `RUN_DB_SMOKE=1` was not set and Docker Desktop is not running.

**Residual risk:**

- ClaimService is verified only against the in-memory claim and evidence repositories. Durable Postgres claim/evidence links remain blocked by DB smoke and later repository work.
- Versioned deterministic rules, contradiction handling, stale evidence handling, and broader positive/negative rule fixture coverage remain pending.
- L5-002 payload schema validation and L5-010 audit events remain unimplemented.

## 2026-06-03 Lane C TC-020 evidence supersession

**Commands run:**

```bash
cd backend && PYTHONPATH=. python -m pytest tests/evidence_ledger/ tests/claims_engine/ -v
cd backend && mypy app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
cd backend && ruff check app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
rg -n "from app\.source_registry|from app\.area_geometry|import app\.source_registry|import app\.area_geometry" backend/app/evidence_ledger backend/app/claims_engine
C:/Program\ Files/Git/bin/bash.exe ./scripts/verify.sh
cd backend && PYTHONPATH=. python -m pytest --collect-only -q
```

**Results:**

- Lane C evidence/claims tests pass: 23 tests.
- Lane C targeted mypy passes: no issues in 11 source/test files.
- Lane C targeted ruff passes.
- Cross-lane import scan returns no matches; Lane C still does not import Lane A/B modules.
- Full verification through Git Bash passes: agent context check ok, workspace validation ok, JSON check ok (14 files), backend tests pass, ruff clean, mypy clean (51 source files).
- Test collection reports 71 tests.
- DB smoke skipped because `RUN_DB_SMOKE=1` was not set and Docker Desktop is not running.

**Residual risk:**

- Supersession is verified only in the in-memory repository. Durable Postgres evidence supersession/audit behavior remains blocked by DB smoke and later repository work.
- L5-002 payload schema validation and L5-010 audit events remain unimplemented.
- ClaimService/rules engine work is still not started.

## 2026-06-03 Lane A TA-050 source provenance and license gates

**Commands run:**

```bash
cd backend && PYTHONPATH=. python -m pytest tests/source_registry/ -v
python scripts/seed_sources.py
python scripts/seed_sources.py --json
cd backend && mypy app/source_registry app/evidence_ledger app/domain/source_contracts.py app/domain/evidence_contracts.py tests/source_registry/test_source_seeds.py tests/source_registry/test_sqlalchemy_source_repo.py tests/evidence_ledger/test_evidence_service.py
python scripts/check_json_files.py
python -c "import csv; rows=list(csv.DictReader(open('./registers/data_source_registry.csv', newline='', encoding='utf-8'))); print(len(rows)); print(rows[0]['License Status'], rows[16]['License Status'], rows[16]['Cache Allowed'])"
C:/Program\ Files/Git/bin/bash.exe ./scripts/verify.sh
cd backend && PYTHONPATH=. python -m pytest --collect-only -q
```

**Results:**

- Lane A source-registry tests pass: 28 tests.
- Source seed dry-run validates 8 `Must` registry rows and JSON output returns the same 8 row summaries.
- Targeted mypy passes: no issues in 12 source/test files.
- JSON check passes: 14 files.
- Source register parses 25 rows; DS-001 has unknown license status, and DS-017 is blocked for license/cache usage.
- Full verification through Git Bash passes: agent context check ok, workspace validation ok, JSON check ok (14 files), backend tests pass, ruff clean, mypy clean (51 source files).
- Test collection reports 64 tests.
- DB smoke skipped because `RUN_DB_SMOKE=1` was not set and Docker Desktop is not running.

**Residual risk:**

- Source governance is still non-DB and non-production: DB seed apply, source-version behavior, retrieval-run behavior, and live connector enforcement are not verified.
- The license review template exists, but no source has completed human license review; unknown statuses remain fail-closed.
- Durable Level 2 and durable Level 3 claims remain blocked until Docker/PostGIS smoke runs.

## 2026-06-03 Lane C TC-010 evidence service slice

**Commands run:**

```bash
cd backend && PYTHONPATH=. python -m pytest tests/evidence_ledger/ tests/claims_engine/ -v
cd backend && ruff check app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
cd backend && mypy app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
rg -n "from app\.source_registry|from app\.area_geometry|import app\.source_registry|import app\.area_geometry" backend/app/evidence_ledger backend/app/claims_engine
C:/Program\ Files/Git/bin/bash.exe ./scripts/verify.sh
```

**Results:**

- Lane C evidence/claims tests pass: 16 tests.
- Lane C targeted ruff passes.
- Lane C targeted mypy passes: no issues in 11 source/test files.
- Cross-lane import scan returns no matches; Lane C does not import Lane A/B modules.
- Full verification through Git Bash passes: agent context check ok, workspace validation ok, JSON check ok (14 files), 59 backend tests pass, ruff clean, mypy clean (51 source files).
- DB smoke skipped because `RUN_DB_SMOKE=1` was not set and Docker Desktop is not running.

**Residual risk:**

- TC-010 is an in-memory evidence-service slice only; durable Postgres evidence persistence remains blocked by DB smoke/migration work.
- L5-002 payload schema validation, L5-006 supersession/amendment, and L5-010 audit events remain unimplemented.
- ClaimService/rules engine work is still not started.

## 2026-06-03 Lane A TA-040 source seeds + Lane B in-memory geometry slice

**Commands run:**

```bash
cd backend && PYTHONPATH=. python -m pytest tests/source_registry/ -v
python scripts/seed_sources.py
python scripts/seed_sources.py --json
cd backend && mypy app/source_registry app/domain/source_contracts.py tests/source_registry/test_source_seeds.py tests/source_registry/test_sqlalchemy_source_repo.py
cd backend && PYTHONPATH=. python -m pytest tests/area_geometry/ -v
cd backend && mypy app/area_geometry app/domain/area_contracts.py tests/area_geometry/test_area_service.py
bash ./scripts/verify.sh
C:/Program\ Files/Git/bin/bash.exe ./scripts/verify.sh
```

**Results:**

- Lane A source-registry tests pass: 23 tests.
- Source seed dry-run validates 8 `Must` registry rows: DS-001, DS-002, DS-003, DS-004, DS-010, DS-011, DS-017, DS-023.
- Source seed JSON output returns the same 8 rows with source names, organizations, and registry IDs.
- Targeted Lane A typecheck passes: no issues in 7 source/test files.
- Lane B area-geometry tests pass: 16 tests.
- Initial targeted Lane B typecheck found one `json.loads` `Any` return in `test_area_service.py`; fixed with a fixture-shape assertion and cast.
- Full verification initially failed on Lane B ruff issues in the untracked geometry slice; fixed with targeted `ruff check app/area_geometry/geometry_validator.py tests/area_geometry/test_area_service.py --fix --unsafe-fixes`.
- Plain `bash ./scripts/verify.sh` failed because `bash` resolved to the Windows WSL launcher and `/bin/bash` is unavailable.
- Canonical verification through Git Bash passes: agent context check ok, workspace validation ok, JSON check ok (14 files), 49 backend tests pass, ruff clean, mypy clean (48 source files).
- DB smoke skipped because `RUN_DB_SMOKE=1` was not set and Docker Desktop is not running.

**Residual risk:**

- DB apply path for `scripts/seed_sources.py --apply` is not live-verified until Docker/PostGIS is available.
- Level 2 remains blocked by Docker/PostGIS smoke; source and geometry work are verified non-DB slices only.
- Lane A still needs TA-050 license review/provenance ADR before source governance can be considered adequate for connector work.
- Lane B TB-050 PostGIS-backed area repository and spatial query behavior remain blocked on Lane A TA-060.

## 2026-06-03 scaffold validation alignment

**Commands run:**

```bash
git status --short --branch
cd backend && PYTHONPATH=. python -m pytest tests/area_geometry/ -v
cd backend && PYTHONPATH=. python -m pytest tests/reports/ tests/api/ -v
cd backend && mypy app/area_geometry app/domain/area_contracts.py app/reports app/api
C:/Program\ Files/Git/bin/bash.exe ./scripts/verify.sh
```

**Results:**

- Root status no longer lists the nested `001-audit/` worktree after adding it to `.gitignore`.
- Lane B scaffold command now passes: 1 test.
- Lane D scaffold command now passes: 2 tests.
- Targeted Lane B/D type check passes: no issues in 5 source files.
- Full verification passes: agent context check ok, workspace validation ok, JSON check ok (14 files), 22 tests pass, ruff clean, mypy clean (44 source files).
- DB smoke skipped because `RUN_DB_SMOKE=1` was not set and Docker Desktop is still unavailable.

**Residual risk:**

- Local baseline commit `ffb73e1` now exists on `main`, parented to `origin/main`.
- No GitHub push has been performed; `origin/main` remains at `13b75a9`, so fresh worktrees from remote `main` do not yet contain the project scaffold.
- DB smoke remains unverified until Docker Desktop is running.

## 2026-06-03 local baseline authority commit

**Commands run:**

```bash
git reset --mixed origin/main
git add -A --dry-run
rg -n "password|secret|token|api[_-]?key|private|credential|BEGIN .*KEY|sk-|ghp_|pat_" --glob '!docs/planning_pack/planning_registers.xlsx' --glob '!*.pyc' --glob '!*.db' .
git add -A
git commit -m "Establish governed scaffold baseline"
git log --oneline --decorate --max-count=5
```

**Results:**

- Local `main` was anchored to `origin/main` before committing, so the scaffold commit is not an unrelated root history.
- Secret scan found no committed secrets or paid-vendor dumps; matches were policy/planning references and `.env.example` local defaults.
- Local baseline commit created: `ffb73e1` (`Establish governed scaffold baseline`).

**Residual risk:**

- Commit is local only; no push has been performed.
- `001-audit` still points at `origin/main` (`13b75a9`) and does not contain the scaffold until a new worktree is created from local `main` or the baseline is pushed.
- DB smoke remains unverified until Docker Desktop is running.

## 2026-06-03 Lane A TA-010 shim archival

**Commands run:**

```bash
rg -n --fixed-strings "from app.repositories" ./backend/app ./backend/tests ./scripts
rg -n --fixed-strings "from app.services" ./backend/app ./backend/tests ./scripts
Move-Item backend/app/repositories archive/2026-06-03_source-registry-lane-migration/backend/app/
Move-Item backend/app/services archive/2026-06-03_source-registry-lane-migration/backend/app/
```

**Results:**

- Active-tree import checks found zero uses of `app.repositories` or `app.services`.
- Shim directories were moved to `archive/2026-06-03_source-registry-lane-migration/backend/app/`; no files were deleted.
- Lane A unit tests pass: 11 tests.
- Lane A typecheck passes: no issues in 4 source files.
- Full verification passes: 22 tests, ruff clean, mypy clean (40 active source files).

**Residual risk:**

- DB smoke remains unverified until Docker Desktop is running.

## 2026-06-03 Lane A TA-020 source ORM model

**Commands run:**

```bash
cd backend && PYTHONPATH=. python -m pytest tests/source_registry/ -v
cd backend && mypy app/source_registry app/domain/source_contracts.py tests/source_registry/test_source_models.py
C:/Program\ Files/Git/bin/bash.exe ./scripts/verify.sh
```

**Results:**

- Lane A source-registry tests pass: 15 tests.
- Targeted Lane A typecheck passes: no issues in 6 source/test files.
- Full verification passes: 26 tests, ruff clean, mypy clean (42 source files).
- `SourceModel` maps `source.sources` without DB access at import time.

**Residual risk:**

- DB smoke remains unverified until Docker Desktop is running.
- SQLAlchemy-backed repository is next (TA-030); live DB execution remains deferred.

## 2026-06-03 Lane A TA-030 SQLAlchemy repository

**Commands run:**

```bash
cd backend && PYTHONPATH=. python -m pytest tests/source_registry/ -v
cd backend && mypy app/source_registry app/domain/source_contracts.py tests/source_registry/test_sqlalchemy_source_repo.py
C:/Program\ Files/Git/bin/bash.exe ./scripts/verify.sh
```

**Results:**

- Lane A source-registry tests pass: 19 tests.
- Targeted Lane A typecheck passes: no issues in 6 source/test files.
- Full verification passes: 30 tests, ruff clean, mypy clean (43 source files).
- `SqlAlchemySourceRepository` implements `add`, `get`, `list_all`, and `exists_by_name_org` against a SQLAlchemy `Session`.

**Residual risk:**

- Repository tests do not execute against live Postgres; DB execution remains blocked until Docker Desktop is running.
- Source seed implementation is next (TA-040).

## 2026-06-03 repo bootstrap + local index

**Commands run:**

```bash
npx codesight --index
bash ./scripts/verify.sh
git status --short --branch
git remote -v
```

**Results:**

- Codesight v1.14.0 scanned 125 files and wrote `.codesight/`.
- `bash ./scripts/verify.sh` failed in PowerShell because `bash` resolved to the Windows WSL launcher and `/bin/bash` was unavailable.
- Re-ran the canonical gate via Git Bash: `C:/Program Files/Git/bin/bash.exe ./scripts/verify.sh`.
- Full verification passed: agent context check ok, workspace validation ok, JSON check ok (14 files), 19 tests pass, ruff clean, mypy clean (40 source files).
- DB smoke skipped because `RUN_DB_SMOKE=1` was not set.
- Local Git initialized on `main`; `origin` points to `https://github.com/benjmcd/land-dd.git`.

**Residual risk:**

- No commit or push has been performed.
- DB smoke remains unverified until Docker Desktop is running.
- Use Git Bash explicitly on this machine unless PATH is changed; plain `bash` currently invokes the WSL launcher.

## 2026-06-03 isolated lane prompt + generated artifact policy

**Commands run:**

```bash
git check-ignore -v ./.codesight/CODESIGHT.md
C:/Program Files/Git/bin/bash.exe ./scripts/verify.sh
git status --short --branch
```

**Results:**

- `.codesight/` is ignored by `.gitignore`.
- Full verification passed: agent context check ok, workspace validation ok, JSON check ok (14 files), 19 tests pass, ruff clean, mypy clean (40 source files).
- DB smoke skipped because `RUN_DB_SMOKE=1` was not set.
- Git status no longer lists `.codesight/`; all repo files remain untracked because no commit has been made.

**Residual risk:**

- No commit or push has been performed.
- Parallel agents must use isolated worktrees/copies; concurrent writes to the same checkout remain unsafe.

## 2026-06-03 isolated lane prompt hardening

**Commands run:**

```bash
C:/Program Files/Git/bin/bash.exe ./scripts/verify.sh
git check-ignore -v ./.codesight/CODESIGHT.md
git status --short --branch
```

**Results:**

- Full verification passed: agent context check ok, workspace validation ok, JSON check ok (14 files), 19 tests pass, ruff clean, mypy clean (40 source files).
- `.codesight/` remains ignored by `.gitignore`.
- Prompt now includes no-baseline-commit isolation guidance, Windows/Git Bash command notes, test-first protocol, tech-debt controls, shared-log conflict handling, stricter definition of done, and cross-lane stop conditions.
- DB smoke skipped because `RUN_DB_SMOKE=1` was not set.

**Residual risk:**

- No commit or push has been performed.
- DB smoke remains unverified until Docker Desktop is running.

## 2026-06-03 initial workspace generation

Commands expected:

```bash
./scripts/agent-context-check.sh
./scripts/validate_workspace.sh
cd backend && PYTHONPATH=. python -m pytest -q
./scripts/verify.sh
```

DB smoke not run by default because it requires Docker/PostGIS.

## 2026-06-03 local validation in generation environment

```bash
./scripts/verify.sh
```

Result:

```text
agent context check: ok
workspace validation: ok
json check: ok (13 files)
backend tests: 6 passed
verify: ok
```

DB smoke was not run here because it requires Docker/PostGIS. Run it locally after `docker compose up -d db`.

## 2026-06-03 (session 3) — 4-lane scaffold + dependency baseline

**Commands run:**

```bash
pip install psycopg[binary] pytest-cov types-PyYAML
./scripts/verify.sh
```

**Results:**

- Dependencies installed: psycopg[binary], pytest-cov, types-PyYAML.
- engine.py fixed: deferred/lazy initialization (no module-level DB connection).
- contracts.py split into 5 per-lane files; enums.py extended with EvidenceType, AreaType, JobStatus.
- Source registry code migrated to source_registry/ module; shims left in repositories/ + services/.
- Tests split: test_domain_contracts.py → 3 per-lane files; test_source_service.py → source_registry/.
- Full verify.sh: 19 tests passing; lint clean; mypy clean (40 source files).

**Lane scaffold created:**

| Lane | Module dir | Test dir | Plan | State |
|---|---|---|---|---|
| A | app/source_registry/ | tests/source_registry/ | plans/lane-a-*.md | state/lane-a-state.md |
| B | app/area_geometry/ | tests/area_geometry/ | plans/lane-b-*.md | state/lane-b-state.md |
| C | app/evidence_ledger/ + claims_engine/ | tests/evidence_ledger/ + claims_engine/ | plans/lane-c-*.md | state/lane-c-state.md |
| D | app/reports/ | tests/reports/ + api/ | plans/lane-d-*.md | state/lane-d-state.md |

**Residual risk:**

- Docker Desktop not running — all DB-dependent gates remain blocked.
- Backward-compat shims in repositories/ + services/ must be archived by Lane A (TA-010) once no code imports from them.
- `app/domain/contracts.py` re-export shim should be cleaned up by Lane D when all lanes have migrated.

## 2026-06-03 T020 — source registry service layer

**Blocker recorded:** Docker Desktop was not running; T010 (DB migration smoke) skipped.

**Commands run:**

```bash
./scripts/verify.sh
cd backend && PYTHONPATH=. python -m pytest tests/test_source_service.py -v
mypy app tests
./scripts/verify.sh
```

**Results:**

- Baseline lint fixed: 3 ruff errors in `config.py` (E501) and `contracts.py` (UP017, UP037).
- mypy installed in Python 3.11 env (`mypy>=1.11`); `verify.sh` typecheck step now runs.
- Source registry repository/service layer added (T020).
- 8 new tests in `tests/test_source_service.py` — all pass.
- Full `verify.sh`: 14 tests passed, lint clean, mypy clean (18 source files).

**Residual risk:**

- DB smoke unverified until Docker is running.
- `InMemorySourceRepository.exists_by_name_org` treats `None == None` as duplicate (stricter than Postgres `UNIQUE(name, organization)` which allows multiple NULL-org rows). Resolve when SQLAlchemy repo is added.
