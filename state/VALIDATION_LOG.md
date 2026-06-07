# Validation Log

Record commands, results, and residual risk.

## 2026-06-07 DS-011 / DS-023 Official-Source Reconnaissance

**Scope:** Official-source reconnaissance for remaining Must-priority source-readiness gaps. This records candidate authorities only; it does not promote DS-011 or DS-023 to production-ready.

**Commands run:**

```powershell
py -3.12 .\scripts\source_readiness.py --priority Must --json
git diff --check
.\scripts\verify.ps1
```

**Result:** Source readiness remained `ready=5 blocked=3`; DS-011 and DS-023 still report `review_status=pending`, `license_status=unknown`, `production_use_allowed=false`, and `connector_ready=false`. `git diff --check` passed. Default verifier passed with backend tests, lint, and typecheck; DB smoke was skipped because `RUN_DB_SMOKE` was not set.

**Residual risk:** Official web/PDF sources exist for Buncombe, Chatham, and Brunswick, but endpoint-level access terms, caching/export/reuse policy, owner/value/situs field policy, zoning amendment tracking, and live connector design are still unresolved.

## 2026-06-06 DB-Enabled Local Verification Attempt

**Scope:** Post-Lane-5 local verification with DB smoke enabled. This records an environment blocker only; it does not claim DB-backed proof for the latest Lane 5 closeout.

**Command run:**

```powershell
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

**Result:** `.\scripts\verify.ps1` passed workspace validation, then failed closed at the DB migration step because `psql` was not available on this machine. Additional prerequisite checks found `docker` unavailable, `psql` unavailable, `pg_dump` unavailable, no local `5432` listener, and no repo-local PostgreSQL client binary under `local_artifacts`.

**Assessment:** This is a local environment blocker, not evidence of a product regression. The default verifier remains the latest successful product gate for Lane 5; DB-enabled verification remains unproven after Lane 5 until a PostgreSQL client and reachable Postgres/PostGIS runtime are available.

**Required unblock:** Install or otherwise provide `psql`, start a Postgres/PostGIS database reachable via `DATABASE_URL_SYNC` or the default `postgresql://land:land@localhost:5432/land_diligence`, then rerun `$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1`.

**Follow-up validation after recording blocker:**

```powershell
git diff --check
py -3.12 .\scripts\source_readiness.py --priority Must --json
.\scripts\verify.ps1
```

**Follow-up result:** `git diff --check` passed. Source readiness remained `ready=5 blocked=3`. Default `.\scripts\verify.ps1` passed with backend tests, lint, and typecheck; DB smoke was skipped because `RUN_DB_SMOKE` was not set.

## 2026-06-06 Chatham Parcel Report Regression + Dossier Zoning Assertion

**Scope:** Lane 5 closeout after Chatham parcel rule/dossier wiring. This records regression coverage only; it does not claim new DB-backed, hosted-production, or source-license completion.

**Commands run:**

```powershell
cd backend; python -m pytest --tb=no
cd backend; python -m pytest -q tests/reports/test_report_regression.py tests/reports/test_dossier_enrichment.py
cd backend; ruff check tests/reports/test_report_regression.py tests/reports/test_dossier_enrichment.py
cd backend; py -3.12 -m mypy tests/reports/test_report_regression.py tests/reports/test_dossier_enrichment.py
git diff --check
.\scripts\verify.ps1
```

**Result:** Full backend pytest passed with `883 passed, 70 skipped, 17 warnings`; targeted report tests passed with `7 passed`; focused ruff and mypy passed; `git diff --check` passed. Default `.\scripts\verify.ps1` passed after this state update; DB smoke was skipped because `RUN_DB_SMOKE` was not set.

**Residual risk:**

- This is an in-memory report-regression slice, not a DB-backed smoke proof.
- DS-011 and DS-023 remain pending/limited by documented source stance; DS-017 remains blocked/not required for private MVP.
- Hosted-production blockers remain separate from private MVP proof.

## 2026-06-06 Private MVP Utility Proof

**Scope:** US-001 through US-008 — fixture connector pipeline, NOT_EVALUATED extension, golden AOI fixtures, MVP regression suite, overclaim test.

**Commands run:**

```powershell
# Core test suite slices (run iteratively as each WP completed)
cd backend; PYTHONPATH=. python -m pytest tests/test_private_mvp_readiness.py -q
cd backend; PYTHONPATH=. python -m pytest tests/test_golden_aoi_manifest.py -q
cd backend; PYTHONPATH=. python -m pytest tests/claims_engine/ -q
cd backend; PYTHONPATH=. python -m pytest tests/reports/test_report_service.py tests/reports/test_report_regression.py tests/api/test_api_scaffold.py -q
cd backend; PYTHONPATH=. python -m pytest tests/source_registry/test_source_seeds.py -q
cd backend; RUN_DB_SMOKE=1 PYTHONPATH=. python -m pytest tests/private_mvp/test_mvp_regression.py -v
cd backend; PYTHONPATH=. python -m pytest tests/reports/test_report_overclaim.py -q

# Lint and typecheck
ruff check backend/
cd backend; mypy tests/private_mvp/ tests/reports/test_report_overclaim.py

# Full gate
.\scripts\verify.ps1
```

**Results:**

| Check | Result |
|---|---|
| `test_private_mvp_readiness.py` | PASS |
| `test_golden_aoi_manifest.py` | PASS |
| `tests/claims_engine/` | PASS |
| `test_report_service.py`, `test_report_regression.py`, `test_api_scaffold.py` | PASS |
| `test_source_seeds.py` | PASS |
| `test_mvp_regression.py` (RUN_DB_SMOKE=1) | PASS (3/3) |
| `test_report_overclaim.py` | PASS (4/4) |
| `ruff check backend/` | PASS (0 errors) |
| `mypy` (222 source files) | PASS (0 errors) |
| `.\scripts\verify.ps1` | `verify: ok` |

**Residual risk:**

- `parcels` and `assessor` are intentionally NOT_EVALUATED — no machine-queryable connector exists for private MVP. Operator must direct users to county Register of Deeds and Tax Administration.
- Terrain/slope and wetlands screening require DS-001 (USGS TNM) and DS-004 (NWI) live connectors; not included in fixture regression.
- DS-017 (commercial parcel data) remains license-blocked; not required for private MVP.
- Hosted-production gates (`hosted_production` section of `config/private_mvp_beta_readiness.yaml`) intentionally deferred.

## 2026-06-06 GitHub Actions Node 24 readiness

**Scope:**

- `.github/workflows/ci.yml`
- `backend/tests/test_access_control_artifacts.py`
- `backend/tests/test_container_scan_artifacts.py`
- `backend/tests/test_provenance_artifacts.py`
- `backend/tests/test_release_readiness_artifacts.py`
- `backend/tests/test_supply_chain_artifacts.py`
- `scripts/run_access_control_check.ps1` and `.sh`
- `scripts/run_container_scan_check.ps1` and `.sh`
- `scripts/run_release_readiness_check.ps1` and `.sh`
- `scripts/run_supply_chain_check.ps1` and `.sh`
- `docs/runbooks/security_scan.md`
- `state/WORKLOG.md`
- `state/VALIDATION_LOG.md`

**Commands run:**

```powershell
rg -n "actions/checkout@v4|actions/setup-python@v5" .\.github .\backend\tests .\scripts .\docs\runbooks .\config
py -3.12 -m pytest -q backend\tests\test_access_control_artifacts.py backend\tests\test_container_scan_artifacts.py backend\tests\test_provenance_artifacts.py backend\tests\test_release_readiness_artifacts.py backend\tests\test_supply_chain_artifacts.py
.\scripts\run_access_control_check.ps1
.\scripts\run_container_scan_check.ps1
.\scripts\run_release_readiness_check.ps1
.\scripts\run_supply_chain_check.ps1
git diff --check
.\scripts\verify.ps1
$env:PYTHONPATH='backend'; py -3.12 .\scripts\source_readiness.py --priority Must --json
```

**Result:**

Focused artifact tests passed; access-control, container-image-scan, release-readiness,
and supply-chain validate-only proof scripts passed; stale `actions/checkout@v4` and
`actions/setup-python@v5` references are absent from workflow/proof surfaces;
`git diff --check` passed; full Windows `.\scripts\verify.ps1` passed. Full verification
reported existing `HTTP_422_UNPROCESSABLE_ENTITY` deprecation warnings in unrelated
paths. Local DB smoke was skipped because `RUN_DB_SMOKE` was not set.

**Residual risk:**

- Must-source readiness remains `sources=8 ready=4 blocked=4`; blocked sources are
  `DS-010`, `DS-011`, `DS-017`, and `DS-023`.
- Hosted production blockers remain: billing, hosted log retention, automatic key
  rotation/external secret manager, full user auth/RBAC, hosted deployment, and hosted
  registry-image/attestation proof.

## 2026-06-06 PR #20 review-thread follow-up

**Scope:**

- `backend/app/connectors/review_queue.py`
- `backend/app/api/connectors.py`
- `schemas/source_provenance_schema.json`
- `api/openapi_stub.yaml`
- `docs/planning_pack/api/openapi_stub.yaml`
- `backend/tests/connectors/test_review_queue.py`
- `backend/tests/api/test_connector_review_actions.py`
- `backend/tests/source_registry/test_source_provenance_schema_contract.py`
- `state/PROJECT_STATE.md`
- `state/WORKLOG.md`
- `state/VALIDATION_LOG.md`
- `plans/2026-06-05-l10-production-hardening.md`

**Commands run:**

```powershell
$env:PYTHONPATH='backend'; py -3.12 -m pytest -q .\backend\tests\connectors\test_review_queue.py .\backend\tests\api\test_connector_review_actions.py .\backend\tests\source_registry\test_source_provenance_schema_contract.py .\backend\tests\api\test_openapi_contract.py .\backend\tests\test_planning_pack_schema_copies.py
ruff check .\backend\app\connectors\review_queue.py .\backend\app\api\connectors.py .\backend\tests\connectors\test_review_queue.py .\backend\tests\api\test_connector_review_actions.py .\backend\tests\source_registry\test_source_provenance_schema_contract.py
$env:PYTHONPATH='backend'; py -3.12 -m mypy .\backend\app\connectors\review_queue.py .\backend\app\api\connectors.py .\backend\tests\connectors\test_review_queue.py .\backend\tests\api\test_connector_review_actions.py .\backend\tests\source_registry\test_source_provenance_schema_contract.py
.\scripts\verify.ps1
$env:PYTHONPATH='backend'; py -3.12 .\scripts\source_readiness.py --priority Must --json
```

**Result:**

Focused pytest passed after regenerating OpenAPI stubs; focused ruff passed; focused
mypy passed; full Windows `.\scripts\verify.ps1` passed. Full verification reported
existing `HTTP_422_UNPROCESSABLE_ENTITY` deprecation warnings in unrelated paths. Local
DB smoke was skipped because `RUN_DB_SMOKE` was not set; the added DB regression remains
gated behind `RUN_DB_SMOKE=1`.

**Residual risk:**

- Must-source readiness remains `sources=8 ready=4 blocked=4`; blocked sources are
  `DS-010`, `DS-011`, `DS-017`, and `DS-023`.
- Hosted production blockers remain: billing, hosted log retention, automatic key
  rotation/external secret manager, full user auth/RBAC, hosted deployment, and hosted
  registry-image/attestation proof.
- Dependabot PRs #17/#18 remain unstable until refreshed or replaced by a controlled
  GitHub Actions upgrade slice.

## 2026-06-06 CI gate authority correction

**Scope:**

- `.github/workflows/ci.yml`
- POSIX executable bits for `scripts/*.sh`
- `scripts/run_security_scan.ps1`
- `docs/runbooks/container_image_scan.md`
- `docs/runbooks/security_scan.md`
- `docs/runbooks/mvp_operator.md`
- `docs/runbooks/dependency_provenance.md`
- `docs/runbooks/supply_chain.md`
- `backend/tests/test_container_scan_artifacts.py`
- `backend/tests/test_security_scan_artifacts.py`
- `backend/tests/test_provenance_artifacts.py`
- `backend/tests/test_supply_chain_artifacts.py`
- `backend/tests/test_release_readiness_artifacts.py`
- `scripts/run_provenance_check.sh`
- `scripts/verify.ps1`
- `scripts/verify.sh`
- `state/WORKLOG.md`
- `state/VALIDATION_LOG.md`
- `state/PROJECT_STATE.md`

**Commands run:**

```powershell
py -3.12 -m pytest -q backend\tests\test_container_scan_artifacts.py backend\tests\test_security_scan_artifacts.py backend\tests\test_release_readiness_artifacts.py backend\tests\test_supply_chain_artifacts.py
@' ... '@ | py -3.12 -
.\scripts\run_container_scan_check.ps1
.\scripts\run_release_readiness_check.ps1
.\scripts\run_security_scan.ps1
.\scripts\verify.ps1
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
py -3.12 .\scripts\source_readiness.py --priority Must --json
gh pr checks 19 --repo benjmcd/land-dd --watch --interval 35
gh run view 27053083439 --repo benjmcd/land-dd --log-failed
py -3.12 -m pytest -q backend\tests\test_supply_chain_artifacts.py backend\tests\test_provenance_artifacts.py backend\tests\test_release_readiness_artifacts.py backend\tests\test_container_scan_artifacts.py
.\scripts\run_provenance_check.ps1
.\scripts\run_supply_chain_check.ps1
.\scripts\run_release_readiness_check.ps1
.\scripts\verify.ps1
gh pr checks 19 --repo benjmcd/land-dd --watch --interval 35
```

**Result:** PASS for focused artifact tests, workflow YAML parsing, container scan static proof, dependency provenance proof, supply-chain proof, release-readiness proof, security scan wrapper, source-readiness JSON, and default `.\scripts\verify.ps1`. The default verification collected backend tests, linted clean, typechecked 216 source files cleanly, and skipped DB smoke as expected. The security scan reports 13 medium Bandit findings and 0 HIGH/CRITICAL findings, so it passes under the documented threshold. Initial PR #19 remote CI showed additional CI-only failures: private-repository GitHub artifact-attestation entitlement, missing `PyYAML` before POSIX provenance validation, missing backend dependencies before release-readiness source-readiness validation, and DB migrations running after DB-gated tests. The follow-up patch gates live attestations on entitlement, installs required CI dependencies, and moves DB migrations before DB-gated backend tests. PR #19 remote CI then passed all jobs, including `verify`, `db-verify`, `supply-chain`, `dependency-attestations`, `container-image-scan`, `security-scan`, `release-readiness`, `access-control`, `image-publication`, and `hosted-deployment`.

**Residual risk:**

- Docker Scout live CVE scanning remains blocked unless `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` are configured in GitHub secrets.
- GitHub dependency attestations remain blocked for this private repository unless repository visibility/plan changes to an artifact-attestation-supported context.
- Existing Bandit medium findings remain review debt; they are reported but not release-blocking under the current threshold.
- Local DB-enabled `.\scripts\verify.ps1` remains environment-blocked in this clean worktree because `psql` is not available locally. GitHub Actions installs `postgresql-client`, and PR #19 remote CI passed `db-verify`.
- Source readiness remains `sources=8 ready=4 blocked=4`; blocked Must sources are `DS-010`, `DS-011`, `DS-017`, and `DS-023`.

## 2026-06-05 Level 10 hardening US-073 through US-082

**Scope:**

- Added `scripts/run_load_test.ps1`, `scripts/run_load_test.sh`, `docs/runbooks/load_testing.md`, `backend/tests/test_load_test_artifacts.py`
- Added `scripts/run_security_scan.ps1`, `scripts/run_security_scan.sh`, `docs/runbooks/security_scan.md`, `backend/tests/test_security_scan_artifacts.py`
- Added `config/data_retention.yaml`, `docs/runbooks/data_retention.md`, `scripts/run_data_retention_check.ps1/.sh`, `backend/tests/test_data_retention_artifacts.py`
- Added `docs/checklists/jurisdiction_readiness.md`, `docs/checklists/rulepack_readiness.md`, `backend/tests/test_readiness_checklists.py`
- Updated `backend/app/core/config.py`, `backend/app/db/engine.py`, `backend/.env.example`; added `backend/tests/test_db_pool_config.py`
- Added `docs/runbooks/performance.md`, `backend/tests/test_performance_artifacts.py`
- Updated `backend/app/api/reports.py` (lineage + compare + diff routes + deslop); added `backend/tests/api/test_report_lineage.py`, `backend/tests/api/test_report_comparison.py`
- Updated `config/release_readiness.yaml`, `config/access_control.yaml`, `.github/workflows/ci.yml`, `docs/runbooks/mvp_operator.md`, `MANIFEST.md`
- Regenerated `docs/planning_pack/api/openapi_stub.yaml`

**Commands run:**

```powershell
cd backend; py -3.12 -m pytest 2>&1 | Select-Object -Last 2
# → 794 passed, 63 skipped, 15 warnings in 10.79s
cd backend; ruff check app tests
# → All checks passed!
cd backend; py -3.12 -m mypy app tests
# → Success: no issues found in 216 source files
```

**Result:** PASS — 794 tests pass (up from 722), ruff clean, mypy clean on 216 source files.

**Residual risk:**
- Load test script performs sequential HTTP calls; not a concurrent load test. External tooling (locust, k6) needed for concurrency testing.
- bandit finds 13 medium/low severity issues in backend/app; none HIGH/CRITICAL; all acknowledged.
- DB pool settings only apply when not using SQLite (conditional guard in engine.py).
- Remaining L10 blockers: full user auth/RBAC, hosted deployment, hosted billing, hosted log retention, automatic key rotation, non-ready Must sources.

## 2026-06-05 Level 10 API-key audit logging and DB events

**Scope:**

- Added `backend/app/api/auth_audit.py`.
- Updated `backend/app/api/api_key_auth.py`.
- Updated `backend/app/main.py`.
- Updated `backend/tests/api/test_api_key_auth.py`.
- Updated `config/access_control.yaml`.
- Updated `docs/runbooks/access_control.md`.
- Updated `docs/runbooks/mvp_operator.md`.
- Updated access-control proof scripts and artifact tests.

**Commands run:**

```powershell
cd backend; py -3.12 -m pytest -q tests\api\test_api_key_auth.py tests\test_access_control_artifacts.py
.\scripts\run_access_control_check.ps1
cd backend; ruff check app\api\auth_audit.py app\api\api_key_auth.py app\main.py tests\api\test_api_key_auth.py tests\test_access_control_artifacts.py
cd backend; py -3.12 -m mypy app\api\auth_audit.py app\api\api_key_auth.py app\main.py tests\api\test_api_key_auth.py tests\test_access_control_artifacts.py
.\scripts\run_release_readiness_check.ps1
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
git diff --check
py -3.12 .\scripts\source_readiness.py --priority Must --json
rg -n "API key.*secret|provided key.*logged|query string.*logged|hosted log-retention system exists|automatic key rotation exists|full user auth/RBAC is complete|OAuth enabled|OIDC enabled|hosted identity provider is integrated|user accounts exist|api_key_auth.*X-API-Key" .\docs .\config .\scripts .\.github .\backend\tests .\MANIFEST.md .\state .\plans
docker compose ps
docker ps --filter "name=live-connector-worker" --format "{{.Names}} {{.Status}}"
```

**Results:**

- Focused API-key auth and access-control artifact tests passed; the DB-backed
  SQLAlchemy audit-event regression is DB-gated and skipped unless `RUN_DB_SMOKE=1`.
- `.\scripts\run_access_control_check.ps1` passed.
- `.\scripts\run_release_readiness_check.ps1` passed.
- Focused ruff passed.
- Focused mypy passed.
- The first full DB-enabled `.\scripts\verify.ps1` run failed because Postgres
  `inet::text` returned `127.0.0.1/32` for the DB audit-event IP readback. The SQL
  readback now uses `host(ip_address)`, and the DB-gated regression passes.
- Full DB-enabled `.\scripts\verify.ps1` passed after that fix; backend tests, lint, typecheck,
  migrations/seeds, and DB smoke all passed.
- 722 tests are collected.
- Canonical mypy is clean over 185 source files.
- `git diff --check` reports only CRLF-normalization warnings on generated/state files.
- Source readiness remains `sources=8 ready=4 blocked=4`.
- Overclaim/secret-log search matched only benign references to configured secrets and
  prior recorded search commands, not claims that provided keys are logged.
- No Docker Compose services or live connector worker containers remain running.

**Residual risk:**

- This adds structured runtime audit logs and DB-service-mode `audit.events` rows for
  API-key decisions. It does not add hosted log-retention/SIEM integration, automatic
  key rotation, external secret-manager integration, user accounts, OAuth/OIDC, hosted
  identity, full RBAC, or per-operator API-key authorization.

## 2026-06-05 Level 10 static API-key lifecycle

**Scope:**

- Added `API_KEY_SPECS` parsing in `backend/app/core/config.py`.
- Updated `backend/tests/api/test_api_key_auth.py`.
- Updated `config/access_control.yaml`.
- Updated `docs/runbooks/access_control.md`.
- Updated `docs/runbooks/mvp_operator.md`.
- Updated `.env.example` and `docker-compose.yml`.
- Updated hosted-deployment runtime input artifacts.
- Updated access-control proof scripts and artifact tests.

**Commands run:**

```powershell
cd backend; py -3.12 -m pytest -q tests\api\test_api_key_auth.py tests\test_access_control_artifacts.py tests\test_hosted_deployment_artifacts.py
.\scripts\run_access_control_check.ps1
.\scripts\run_hosted_deployment_check.ps1
cd backend; ruff check app\core\config.py tests\api\test_api_key_auth.py tests\test_access_control_artifacts.py tests\test_hosted_deployment_artifacts.py
cd backend; py -3.12 -m mypy app\core\config.py tests\api\test_api_key_auth.py tests\test_access_control_artifacts.py tests\test_hosted_deployment_artifacts.py
.\scripts\run_release_readiness_check.ps1
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
git diff --check
py -3.12 .\scripts\source_readiness.py --priority Must --json
rg -n "automatic key rotation exists|automatic API-key rotation exists|external secret-manager integration exists|per-key usage audit ledger exists|full user auth/RBAC is complete|OAuth enabled|OIDC enabled|hosted identity provider is integrated|user accounts exist|API_KEY_SPECS.*full user auth|static key lifecycle.*full RBAC" .\docs .\config .\scripts .\.github .\backend\tests .\MANIFEST.md .\state .\plans
docker compose config | Select-String -Pattern "API_KEY_SPECS|API_KEYS|REVIEWER_ACCOUNT_SCOPES"
docker compose ps
docker ps --filter "name=live-connector-worker" --format "{{.Names}} {{.Status}}"
```

**Results:**

- Focused API-key lifecycle and access-control/hosted-deployment artifact tests passed.
- `.\scripts\run_access_control_check.ps1` passed.
- `.\scripts\run_hosted_deployment_check.ps1` passed.
- `.\scripts\run_release_readiness_check.ps1` passed.
- Focused ruff passed.
- Focused mypy passed.
- Full DB-enabled `.\scripts\verify.ps1` passed; backend tests, lint, typecheck,
  migrations/seeds, and DB smoke all passed.
- 715 tests are collected.
- Canonical mypy is clean over 184 source files.
- `git diff --check` reports only CRLF-normalization warnings on generated/state files.
- Source readiness remains `sources=8 ready=4 blocked=4`.
- Overclaim search matched only negative/current-state statements that per-key audit is
  not implemented and an older recorded search command.
- `docker compose config` renders `API_KEY_SPECS`, `API_KEYS`, and
  `REVIEWER_ACCOUNT_SCOPES`.
- No Docker Compose services or live connector worker containers remain running.

**Residual risk:**

- This adds a configured static key lifecycle for API-key auth. It does not add automatic
  key rotation, external secret-manager integration, per-key usage audit, user accounts,
  OAuth/OIDC, hosted identity-provider authorization, full RBAC, or an auth audit-event
  ledger.

## 2026-06-05 Level 10 hashed secret specs

**Scope:**

- Added `backend/app/api/secret_specs.py`.
- Updated `backend/app/api/api_key_auth.py`.
- Updated `backend/app/api/reviewer_auth.py`.
- Updated `backend/app/core/config.py`.
- Updated `backend/tests/api/test_api_key_auth.py`.
- Updated `backend/tests/api/test_reviewer_auth.py`.
- Updated access-control catalog, runbook, proof scripts, and `.env.example`.

**Commands run:**

```powershell
cd backend; py -3.12 -m pytest -q tests\api\test_api_key_auth.py tests\api\test_reviewer_auth.py
.\scripts\run_access_control_check.ps1
cd backend; ruff check app\api\api_key_auth.py app\api\reviewer_auth.py app\api\secret_specs.py app\core\config.py tests\api\test_api_key_auth.py tests\api\test_reviewer_auth.py
cd backend; py -3.12 -m mypy app\api\api_key_auth.py app\api\reviewer_auth.py app\api\secret_specs.py app\core\config.py tests\api\test_api_key_auth.py tests\api\test_reviewer_auth.py
.\scripts\run_release_readiness_check.ps1
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
git diff --check
py -3.12 .\scripts\source_readiness.py --priority Must --json
rg -n "key rotation exists|key rotation workflow exists|full user auth/RBAC is complete|OAuth enabled|OIDC enabled|hosted identity provider is integrated|user accounts exist|hashed secrets are key rotation|sha256.*full user auth" .\docs .\config .\scripts .\.github .\backend\tests .\MANIFEST.md .\state
docker compose ps
docker ps --filter "name=live-connector-worker" --format "{{.Names}} {{.Status}}"
```

**Results:**

- Focused API-key and reviewer-auth tests passed.
- `.\scripts\run_access_control_check.ps1` passed.
- `.\scripts\run_release_readiness_check.ps1` passed.
- Ruff passed for the focused auth code/tests.
- Mypy passed for the focused auth code/tests.
- Full DB-enabled `.\scripts\verify.ps1` passed; backend tests, lint, typecheck,
  migrations/seeds, and DB smoke all passed.
- 704 tests are collected.
- Canonical mypy is clean over 184 source files.
- `git diff --check` reports only CRLF-normalization warnings on generated/state files.
- Source readiness remains `sources=8 ready=4 blocked=4`.
- Auth-overclaim search matched only explicit negative statements that key rotation/full
  hosted identity are not implemented.
- No Docker Compose services or live connector worker containers remain running.

**Residual risk:**

- This supports raw or `sha256:<64-hex>` configured secrets for static API-key and local
  reviewer service-account auth. It does not add key rotation, user accounts,
  OAuth/OIDC, hosted identity-provider authorization, full RBAC, or an auth audit-event
  ledger.

## 2026-06-05 Level 10 hosted deployment readiness

**Scope:**

- Added `config/hosted_deployment.yaml`.
- Added `docs/runbooks/hosted_deployment.md`.
- Added `scripts/run_hosted_deployment_check.ps1`.
- Added `scripts/run_hosted_deployment_check.sh`.
- Added `backend/tests/test_hosted_deployment_artifacts.py`.
- Wired hosted-deployment proof into release readiness, CI, operator runbook, manifest,
  active plan, and state records.

**Commands run:**

```powershell
.\scripts\run_hosted_deployment_check.ps1
.\scripts\run_release_readiness_check.ps1
cd backend; py -3.12 -m pytest -q tests\test_hosted_deployment_artifacts.py tests\test_release_readiness_artifacts.py
cd backend; ruff check tests\test_hosted_deployment_artifacts.py tests\test_release_readiness_artifacts.py
cd backend; py -3.12 -m mypy tests\test_hosted_deployment_artifacts.py tests\test_release_readiness_artifacts.py
$errors=$null; [System.Management.Automation.PSParser]::Tokenize((Get-Content .\scripts\run_hosted_deployment_check.ps1 -Raw), [ref]$errors) | Out-Null; if ($errors) { $errors | Format-List | Out-String | Write-Error; exit 1 }; 'psparser ok'
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
```

**Results:**

- `.\scripts\run_hosted_deployment_check.ps1` passed.
- `.\scripts\run_release_readiness_check.ps1` passed with hosted-deployment wired in.
- Focused hosted-deployment and release-readiness artifact tests passed.
- Ruff passed for the focused hosted-deployment/readiness artifact tests.
- Mypy passed for the focused hosted-deployment/readiness artifact tests.
- PowerShell parser validation passed for the hosted-deployment check script.
- Full DB-enabled `.\scripts\verify.ps1` passed; backend tests, lint, typecheck,
  migrations/seeds, and DB smoke all passed.
- 694 tests are collected.
- Canonical mypy is clean over 183 source files.

**Residual risk:**

- This records and validates the local hosted deployment readiness boundary only. It does
  not create hosted infrastructure, write secrets, open a public endpoint, deploy a
  registry image, add hosted billing reconciliation, add hosted alerting, or approve
  blocked sources.

## 2026-06-05 Level 10 image publication readiness

**Scope:**

- Added `config/image_publication.yaml`.
- Added `docs/runbooks/image_publication.md`.
- Added `scripts/run_image_publication_check.ps1`.
- Added `scripts/run_image_publication_check.sh`.
- Added `backend/tests/test_image_publication_artifacts.py`.
- Wired image-publication proof into release readiness, CI, operator runbook, manifest,
  active plan, and state records.

**Commands run:**

```powershell
.\scripts\run_image_publication_check.ps1
.\scripts\run_release_readiness_check.ps1
cd backend; py -3.12 -m pytest -q tests\test_image_publication_artifacts.py tests\test_release_readiness_artifacts.py
cd backend; ruff check tests\test_image_publication_artifacts.py tests\test_release_readiness_artifacts.py
cd backend; py -3.12 -m mypy tests\test_image_publication_artifacts.py tests\test_release_readiness_artifacts.py
$errors=$null; [System.Management.Automation.PSParser]::Tokenize((Get-Content .\scripts\run_image_publication_check.ps1 -Raw), [ref]$errors) | Out-Null; if ($errors) { $errors | Format-List | Out-String | Write-Error; exit 1 }; 'psparser ok'
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
py -3.12 .\scripts\source_readiness.py --priority Must --json
git diff --check
docker compose ps
docker ps --filter "name=live-connector-worker" --format "{{.Names}} {{.Status}}"
cd backend; py -3.12 -m pytest --collect-only
rg -n "<image publication/deployment overclaim phrases>" .\docs .\config .\scripts .\.github .\backend\tests .\MANIFEST.md .\state
```

**Results:**

- `.\scripts\run_image_publication_check.ps1` passed.
- `.\scripts\run_release_readiness_check.ps1` passed with image-publication wired in.
- Focused image-publication and release-readiness artifact tests passed.
- Ruff passed for the focused image-publication/readiness artifact tests.
- Mypy passed for the focused image-publication/readiness artifact tests.
- PowerShell parser validation passed for the image-publication check script.
- Full DB-enabled `.\scripts\verify.ps1` passed; backend tests, lint, typecheck,
  migrations/seeds, and DB smoke all passed.
- 689 tests are collected.
- Canonical mypy is clean over 182 source files.
- Source readiness remains `sources=8 ready=4 blocked=4`.
- `git diff --check` reports only existing CRLF normalization warnings on
  generated/state files.
- No Docker Compose services or live connector worker containers are running.
- Overclaim search found only negative assertion strings in tests/runbooks/scripts, not
  executable push/login/sign/deploy behavior.

**Residual risk:**

- This records and validates the local registry image publication boundary only. It does
  not push a registry image, create hosted deployment, sign an image SBOM, publish SLSA
  provenance, attach registry-image attestations, approve blocked sources, or add hosted
  billing reconciliation.

## 2026-06-05 Level 10 local release package

**Scope:**

- Added `config/release_package.yaml`.
- Added `docs/runbooks/release_package.md`.
- Added `scripts/build_release_package.ps1`.
- Added `scripts/build_release_package.sh`.
- Added `scripts/run_release_package_check.ps1`.
- Added `scripts/run_release_package_check.sh`.
- Added `backend/tests/test_release_package_artifacts.py`.
- Wired release-package proof into release readiness, operator runbook, manifest, active
  plan, and state records.
- Created a clean local package:
  `local_artifacts/releases/land-diligence-us066-20260606T013648Z.zip`.
- Created a sibling package manifest:
  `local_artifacts/releases/land-diligence-us066-20260606T013648Z-release-manifest.json`.

**Commands run:**

```powershell
.\scripts\run_release_package_check.ps1
.\scripts\run_release_readiness_check.ps1
cd backend; py -3.12 -m pytest -q tests\test_release_package_artifacts.py tests\test_release_readiness_artifacts.py
cd backend; ruff check tests\test_release_package_artifacts.py tests\test_release_readiness_artifacts.py
cd backend; py -3.12 -m mypy tests\test_release_package_artifacts.py tests\test_release_readiness_artifacts.py
$errors=$null; [System.Management.Automation.PSParser]::Tokenize((Get-Content .\scripts\run_release_package_check.ps1 -Raw), [ref]$errors) | Out-Null; if ($errors) { $errors | Format-List | Out-String | Write-Error; exit 1 }; [System.Management.Automation.PSParser]::Tokenize((Get-Content .\scripts\build_release_package.ps1 -Raw), [ref]$errors) | Out-Null; if ($errors) { $errors | Format-List | Out-String | Write-Error; exit 1 }; 'psparser ok'
$version = 'us066-' + ([DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ')); .\scripts\build_release_package.ps1 -Version $version
py -3.12 <manifest-and-zip-inspection>
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
py -3.12 .\scripts\source_readiness.py --priority Must --json
git diff --check
docker compose ps
docker ps -a --filter "name=live-connector-worker-run" --format "{{.Names}} {{.Status}}"
rg -n "<release/auth overclaim phrases>" .\docs .\config .\scripts .\backend .\MANIFEST.md .\state .\plans
```

**Results:**

- `.\scripts\run_release_package_check.ps1` passed.
- `.\scripts\run_release_readiness_check.ps1` passed.
- Focused release-package and release-readiness artifact tests passed.
- Ruff passed for the focused release-package/readiness artifact tests.
- Mypy passed for the focused release-package/readiness artifact tests.
- PowerShell parser validation passed for package check/build scripts.
- Clean package build produced
  `local_artifacts/releases/land-diligence-us066-20260606T013648Z.zip`.
- The sibling manifest reports schema `release_package_manifest_v1`, 220 files, and a
  64-character ZIP SHA-256.
- ZIP inspection confirmed the package contains `release-manifest.json` and
  `.env.example`, excludes `.git`, excludes `local_artifacts`, and has zero secret-like
  `.env` files beyond allowed `.env.example`.
- Full DB-enabled `.\scripts\verify.ps1` passed; backend tests, lint, typecheck,
  migrations/seeds, and DB smoke all passed.
- 684 tests are collected.
- Canonical mypy is clean over 181 source files.
- Source readiness remains `sources=8 ready=4 blocked=4`.
- `git diff --check` reports only existing CRLF normalization warnings on
  generated/state files.
- No Docker Compose services or `live-connector-worker-run` containers are running.

**Residual risk:**

- This creates a local source/runtime/operator release ZIP and manifest from the current
  worktree. It does not push a registry image, create hosted deployment, attach
  published registry-image attestations, sign image SBOMs, add SLSA provenance, approve
  blocked sources, or add hosted billing reconciliation.

## 2026-06-05 Level 10 scoped reviewer authorization

**Scope:**

- Updated `backend/app/api/reviewer_auth.py` so `ReviewerPrincipal` carries explicit
  local service-account scopes.
- Added `REVIEWER_ACCOUNT_SCOPES` parsing to `backend/app/core/config.py` and wired it
  through in-memory and DB-backed API service construction.
- Added route-level scope checks to connector invocation/scheduling, connector review
  actions, live-job/queue health reads, failed-report retry, and manual approved-connector
  report creation.
- Updated `.env.example`, `docker-compose.yml`, `config/access_control.yaml`,
  `docs/runbooks/access_control.md`, `docs/runbooks/mvp_operator.md`, `MANIFEST.md`,
  `scripts/run_access_control_check.ps1`, `scripts/run_access_control_check.sh`,
  artifact tests, and scoped route tests.

**Commands run:**

```powershell
.\scripts\run_access_control_check.ps1
.\scripts\run_release_readiness_check.ps1
$errors=$null; [System.Management.Automation.PSParser]::Tokenize((Get-Content .\scripts\run_access_control_check.ps1 -Raw), [ref]$errors) | Out-Null; if ($errors) { $errors | Format-List | Out-String | Write-Error; exit 1 }; 'psparser ok'
cd backend; py -3.12 -m pytest -q tests\test_access_control_artifacts.py tests\api\test_reviewer_auth.py tests\api\test_connector_review_actions.py tests\api\test_operations.py tests\api\test_async_report_runs.py tests\api\test_fema_nfhl_connector_api.py::test_fema_nfhl_schedule_bbox_rejects_reviewer_without_connector_run_scope
cd backend; ruff check app\api\reviewer_auth.py app\api\connectors.py app\api\operations.py app\api\reports.py app\api\dependencies.py app\core\config.py tests\test_access_control_artifacts.py tests\api\test_reviewer_auth.py tests\api\test_connector_review_actions.py tests\api\test_operations.py tests\api\test_async_report_runs.py tests\api\test_fema_nfhl_connector_api.py
cd backend; py -3.12 -m mypy app\api\reviewer_auth.py app\api\connectors.py app\api\operations.py app\api\reports.py app\api\dependencies.py app\core\config.py tests\test_access_control_artifacts.py tests\api\test_reviewer_auth.py tests\api\test_connector_review_actions.py tests\api\test_operations.py tests\api\test_async_report_runs.py tests\api\test_fema_nfhl_connector_api.py
docker compose config
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
py -3.12 .\scripts\source_readiness.py --priority Must --json
git diff --check
docker compose ps
docker ps -a --filter "name=live-connector-worker-run" --format "{{.Names}} {{.Status}}"
rg -n "<auth overclaim phrases>" .\docs .\config .\scripts .\backend .\MANIFEST.md .\state .\plans
```

**Results:**

- `.\scripts\run_access_control_check.ps1` passed.
- `.\scripts\run_release_readiness_check.ps1` passed.
- PowerShell parser validation passed for `scripts/run_access_control_check.ps1`.
- Focused scoped-auth and access-control artifact tests passed.
- Ruff passed for the focused scoped-auth and access-control file set.
- Mypy passed for the focused scoped-auth and access-control file set.
- `docker compose config` passed with `REVIEWER_ACCOUNT_SCOPES` wired for backend and
  worker services.
- Full DB-enabled `.\scripts\verify.ps1` passed; backend tests, lint, typecheck,
  migrations/seeds, and DB smoke all passed.
- 680 tests are collected.
- Canonical mypy is clean over 180 source files.
- Source readiness remains `sources=8 ready=4 blocked=4`.
- `git diff --check` reports only existing CRLF normalization warnings on
  generated/state files.
- No Docker Compose services or `live-connector-worker-run` containers are running.
- Auth-overclaim search found no current overclaim phrases.

**Residual risk:**

- This implements scoped local reviewer service-account authorization for protected
  operator routes. It does not add user accounts, OAuth/OIDC, full user RBAC, key
  rotation, hosted identity-provider integration, or audit-log identity binding beyond
  the existing reviewer id carried by current operator actions.

## 2026-06-05 Level 10 access-control posture proof

**Scope:**

- Added `config/access_control.yaml`.
- Added `docs/runbooks/access_control.md`.
- Added `scripts/run_access_control_check.ps1`.
- Added `scripts/run_access_control_check.sh`.
- Added `backend/tests/test_access_control_artifacts.py`.
- Added a CI `access-control` job to `.github/workflows/ci.yml`.
- Wired `access_control` into `config/release_readiness.yaml`,
  `scripts/run_release_readiness_check.ps1`, `scripts/run_release_readiness_check.sh`,
  `backend/tests/test_release_readiness_artifacts.py`, release/operator runbooks,
  `MANIFEST.md`, the active Level 10 plan, and state records.

**Commands run:**

```powershell
.\scripts\run_access_control_check.ps1
.\scripts\run_release_readiness_check.ps1
cd backend; py -3.12 -m pytest -q tests\test_access_control_artifacts.py tests\test_release_readiness_artifacts.py tests\api\test_api_key_auth.py tests\api\test_reviewer_auth.py
cd backend; ruff check tests\test_access_control_artifacts.py tests\test_release_readiness_artifacts.py tests\api\test_api_key_auth.py tests\api\test_reviewer_auth.py
cd backend; py -3.12 -m mypy tests\test_access_control_artifacts.py tests\test_release_readiness_artifacts.py tests\api\test_api_key_auth.py tests\api\test_reviewer_auth.py
$errors=$null; [System.Management.Automation.PSParser]::Tokenize((Get-Content .\scripts\run_access_control_check.ps1 -Raw), [ref]$errors) | Out-Null; if ($errors) { $errors | Format-List | Out-String | Write-Error; exit 1 }; 'psparser ok'
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
py -3.12 .\scripts\source_readiness.py --priority Must --json
git diff --check
docker compose ps
docker ps -a --filter "name=live-connector-worker-run" --format "{{.Names}} {{.Status}}"
rg -n "<auth overclaim phrases>" .\docs .\config .\scripts .\backend .\MANIFEST.md .\state .\plans
```

**Results:**

- `.\scripts\run_access_control_check.ps1` passed.
- `.\scripts\run_release_readiness_check.ps1` passed.
- Focused access/release/auth artifact tests passed.
- Ruff passed for the focused access/release/auth test set.
- Mypy passed for the focused access/release/auth test set.
- PowerShell parser validation passed for `scripts/run_access_control_check.ps1`.
- Full DB-enabled `.\scripts\verify.ps1` passed; backend tests, lint, typecheck,
  migrations/seeds, and DB smoke all passed.
- 668 tests are collected.
- Canonical mypy is clean over 180 source files.
- Source readiness remains `sources=8 ready=4 blocked=4`.
- `git diff --check` reports only existing CRLF normalization warnings on
  generated/state files.
- No Docker Compose services or `live-connector-worker-run` containers are running.
- Auth-overclaim search found no current overclaim phrases.

**Residual risk:**

- This proves a repo-local access-control posture catalog and static proof for current
  API-key middleware, local reviewer service-account auth, reviewer-authenticated
  operator routes, and explicit blockers. It does not add full user auth/RBAC,
  OAuth/OIDC, user accounts, key rotation, hosted identity-provider integration, or
  role-scoped authorization.

## 2026-06-05 Level 10 release readiness proof

**Scope:**

- Added `config/release_readiness.yaml`.
- Added `docs/runbooks/release_readiness.md`.
- Added `scripts/run_release_readiness_check.ps1`.
- Added `scripts/run_release_readiness_check.sh`.
- Added `backend/tests/test_release_readiness_artifacts.py`.
- Added a CI `release-readiness` job to `.github/workflows/ci.yml`.
- Updated `docs/runbooks/mvp_operator.md`, `MANIFEST.md`, the active Level 10 plan, and
  state records.

**Commands run:**

```powershell
.\scripts\run_release_readiness_check.ps1
cd backend; py -3.12 -m pytest -q tests\test_release_readiness_artifacts.py tests\test_supply_chain_artifacts.py tests\test_container_scan_artifacts.py tests\test_cost_monitoring_artifacts.py
cd backend; ruff check tests\test_release_readiness_artifacts.py
cd backend; py -3.12 -m mypy tests\test_release_readiness_artifacts.py
$errors=$null; [System.Management.Automation.PSParser]::Tokenize((Get-Content .\scripts\run_release_readiness_check.ps1 -Raw), [ref]$errors) | Out-Null; if ($errors) { $errors | Format-List | Out-String | Write-Error; exit 1 }; 'psparser ok'
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
py -3.12 .\scripts\source_readiness.py --priority Must --json
git diff --check
docker compose ps
docker ps -a --filter "name=live-connector-worker-run" --format "{{.Names}} {{.Status}}"
rg -n "<release overclaim phrases>" .\docs .\config .\scripts .\backend\tests .\MANIFEST.md .\state .\plans
```

**Results:**

- `.\scripts\run_release_readiness_check.ps1` passed.
- Focused release/supply-chain/container/cost artifact tests passed: 18 passed.
- Ruff passed for `backend/tests/test_release_readiness_artifacts.py`.
- Mypy passed for `backend/tests/test_release_readiness_artifacts.py`.
- PowerShell parser validation passed for `scripts/run_release_readiness_check.ps1`.
- Full DB-enabled `.\scripts\verify.ps1` passed; backend tests, lint, typecheck,
  migrations/seeds, and DB smoke all passed.
- 664 tests are collected.
- Canonical mypy is clean over 179 source files.
- Source readiness remains `sources=8 ready=4 blocked=4`.
- `git diff --check` reports only existing CRLF normalization warnings on
  generated/state files.
- No Docker Compose services or `live-connector-worker-run` containers are running.

**Residual risk:**

- This proves a repo-local release readiness catalog and static release gate proof. It
  does not create a release package, push a registry image, create a hosted deployment,
  publish registry-image attestations, add hosted billing reconciliation, approve
  blocked sources, add full user auth/RBAC, or create hosted alerting.

## 2026-06-05 Level 10 report cost attribution proof

**Scope:**

- Updated `schemas/report_run_schema.json` to require non-negative count,
  USD-cent, and reviewer-minute report cost metrics.
- Updated `backend/app/reports/service.py` to emit zero-dollar attribution for current
  local-only report paths.
- Updated `backend/app/reports/report_repo.py` to fill missing attribution defaults when
  persisting older/custom report metadata.
- Updated report schema/service/repository/regression/API tests.
- Updated `config/ops_cost_monitoring.yaml`, `docs/runbooks/cost_monitoring.md`,
  `docs/runbooks/mvp_operator.md`, `docs/adr/lane-d-0010-report-manifest-metadata.md`,
  `scripts/run_cost_monitoring_check.ps1`, `scripts/run_cost_monitoring_check.sh`,
  `backend/tests/test_cost_monitoring_artifacts.py`, `MANIFEST.md`, the active Level 10
  plan, and state records.

**Commands run:**

```powershell
.\scripts\run_cost_monitoring_check.ps1
cd backend; py -3.12 -m pytest -q tests\test_cost_monitoring_artifacts.py tests\reports\test_report_schema_contract.py tests\reports\test_report_service.py tests\reports\test_report_repository.py tests\reports\test_report_regression.py tests\api\test_api_scaffold.py tests\api\test_report_runs_db.py
cd backend; ruff check app\reports tests\test_cost_monitoring_artifacts.py tests\reports\test_report_schema_contract.py tests\reports\test_report_service.py tests\reports\test_report_repository.py tests\reports\test_report_regression.py tests\api\test_api_scaffold.py tests\api\test_report_runs_db.py
cd backend; py -3.12 -m mypy app\reports tests\test_cost_monitoring_artifacts.py tests\reports\test_report_schema_contract.py tests\reports\test_report_service.py tests\reports\test_report_repository.py tests\reports\test_report_regression.py tests\api\test_api_scaffold.py tests\api\test_report_runs_db.py
$null = [System.Management.Automation.PSParser]::Tokenize((Get-Content .\scripts\run_cost_monitoring_check.ps1 -Raw), [ref]$null); 'psparser ok'
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
py -3.12 .\scripts\source_readiness.py --priority Must --json
git diff --check
docker compose ps
docker ps -a --filter "name=live-connector-worker-run" --format "{{.Names}} {{.Status}}"
rg -n "<stale count-only dollar-gap phrases>" .\backend .\docs .\config .\scripts .\schemas .\MANIFEST.md .\state .\plans
```

**Results:**

- `.\scripts\run_cost_monitoring_check.ps1` passed.
- Focused tests passed: 25 passed, 2 skipped.
- Ruff passed for touched report/test paths.
- Mypy passed for 13 touched source/test files.
- PowerShell parser validation passed for `scripts/run_cost_monitoring_check.ps1`.
- Full DB-enabled `.\scripts\verify.ps1` passed; backend tests, lint, typecheck,
  migrations/seeds, and DB smoke all passed.
- 659 tests are collected.
- Source readiness remains `sources=8 ready=4 blocked=4`.
- `git diff --check` reports only existing CRLF normalization warnings on
  generated/state files.
- No Docker Compose services or `live-connector-worker-run` containers are running.
- Stale count-only dollar-gap phrasing search returned no matches.

**Residual risk:**

- This proves local report artifacts carry explicit zero-dollar attribution for current
  no-paid-service paths. It does not add hosted cloud billing reconciliation, approved
  nonzero unit-cost thresholds, paid-vendor metering, LLM metering, map/geocoding
  metering, or durable reviewer-time capture.

## 2026-06-05 Level 10 dependency artifact attestation proof

**Scope:**

- Added the CI `dependency-attestations` job to `.github/workflows/ci.yml`.
- Updated `docs/runbooks/dependency_provenance.md`.
- Updated `docs/runbooks/supply_chain.md`.
- Updated `docs/runbooks/mvp_operator.md`.
- Updated `scripts/run_provenance_check.ps1`.
- Updated `scripts/run_provenance_check.sh`.
- Updated `scripts/run_supply_chain_check.ps1`.
- Updated `scripts/run_supply_chain_check.sh`.
- Updated `backend/tests/test_provenance_artifacts.py`.
- Updated `backend/tests/test_supply_chain_artifacts.py`.
- Updated `MANIFEST.md`, the active Level 10 plan, and state records.

**Commands run:**

```powershell
.\scripts\run_provenance_check.ps1
.\scripts\run_supply_chain_check.ps1
cd backend; py -3.12 -m pytest -q tests\test_provenance_artifacts.py tests\test_supply_chain_artifacts.py tests\test_container_scan_artifacts.py
cd backend; ruff check tests\test_provenance_artifacts.py tests\test_supply_chain_artifacts.py tests\test_container_scan_artifacts.py
cd backend; py -3.12 -m mypy tests\test_provenance_artifacts.py tests\test_supply_chain_artifacts.py tests\test_container_scan_artifacts.py
$files = @('.\scripts\run_provenance_check.ps1', '.\scripts\run_supply_chain_check.ps1'); foreach ($file in $files) { $errors=$null; [System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw $file), [ref]$errors) | Out-Null; if ($errors) { $errors | Format-List | Out-String | Write-Error; exit 1 } }; Write-Host 'powershell parser: ok'
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

**Results:**

- `.\scripts\run_provenance_check.ps1` passed, including the hash-checked pip dry run.
- `.\scripts\run_supply_chain_check.ps1` passed.
- Focused tests passed: 12 passed.
- Ruff passed for touched provenance/supply-chain/container artifact tests.
- Mypy passed for touched provenance/supply-chain/container artifact tests.
- PowerShell parser validation passed for `scripts/run_provenance_check.ps1` and
  `scripts/run_supply_chain_check.ps1`.
- Full DB-enabled `.\scripts\verify.ps1` passed after the US-061 slice.
- Canonical mypy remains clean over 178 source files.

**Residual risk:**

- This proves repo-local CI wiring for GitHub artifact attestations of the production
  lock/SBOM files and an SBOM attestation that binds the CycloneDX SBOM to the production
  lock subject. It does not prove a release package, hosted deployment, or published
  registry-image attestation; it also does not scan GitHub Actions internals or approve
  source/vendor rights.

## 2026-06-05 Level 10 digest-pinned Docker base-image proof

**Scope:**

- Updated `backend/Dockerfile` to pin `python:3.12-slim` by OCI index digest.
- Updated `docs/runbooks/container_image_scan.md`.
- Updated `scripts/run_container_scan_check.ps1`.
- Updated `scripts/run_container_scan_check.sh`.
- Updated `backend/tests/test_container_scan_artifacts.py`.
- Updated `docs/runbooks/mvp_operator.md`, `MANIFEST.md`, the active Level 10 plan, and
  state records.

**Commands run:**

```powershell
docker buildx imagetools inspect python:3.12-slim
.\scripts\run_container_scan_check.ps1
cd backend; py -3.12 -m pytest -q tests\test_container_scan_artifacts.py tests\test_supply_chain_artifacts.py tests\test_provenance_artifacts.py
cd backend; ruff check tests\test_container_scan_artifacts.py tests\test_supply_chain_artifacts.py tests\test_provenance_artifacts.py
cd backend; py -3.12 -m mypy tests\test_container_scan_artifacts.py tests\test_supply_chain_artifacts.py tests\test_provenance_artifacts.py
docker build -f backend/Dockerfile -t land-diligence-backend:pinned-check .
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

**Results:**

- Live Docker metadata reported `python:3.12-slim` OCI index digest
  `sha256:090ba77e2958f6af52a5341f788b50b032dd4ca28377d2893dcf1ecbdfdfe203`.
- `backend/Dockerfile` now uses that digest in its `FROM` line.
- `.\scripts\run_container_scan_check.ps1` passed after enforcing the pinned digest.
- Focused tests passed: 10 passed.
- Ruff passed for touched container/supply-chain/provenance artifact tests.
- Mypy passed for touched container/supply-chain/provenance artifact tests.
- `docker build -f backend/Dockerfile -t land-diligence-backend:pinned-check .`
  passed and resolved the pinned digest.
- Full DB-enabled `.\scripts\verify.ps1` passed after the US-060 slice.
- Canonical mypy remains clean over 178 source files.

**Residual risk:**

- This proves the backend Docker base image is pinned to the recorded OCI index digest
  and that the pinned Dockerfile builds locally. It does not prove any separately
  published registry image, publish or sign an image SBOM, produce a SLSA provenance
  attestation, validate hosted deployment runtime state, scan GitHub Actions internals,
  or approve source/vendor rights.

## 2026-06-05 Level 10 container image scan proof

**Scope:**

- Added the CI `container-image-scan` job to `.github/workflows/ci.yml`.
- Added `docs/runbooks/container_image_scan.md`.
- Added `scripts/run_container_scan_check.ps1`.
- Added `scripts/run_container_scan_check.sh`.
- Added `backend/tests/test_container_scan_artifacts.py`.
- Updated `docs/runbooks/supply_chain.md`, `docs/runbooks/mvp_operator.md`,
  `MANIFEST.md`, the active Level 10 plan, and state records.

**Commands run:**

```powershell
.\scripts\run_container_scan_check.ps1
.\scripts\run_supply_chain_check.ps1
cd backend; py -3.12 -m pytest -q tests\test_container_scan_artifacts.py tests\test_supply_chain_artifacts.py tests\test_provenance_artifacts.py
cd backend; ruff check tests\test_container_scan_artifacts.py tests\test_supply_chain_artifacts.py tests\test_provenance_artifacts.py
cd backend; py -3.12 -m mypy tests\test_container_scan_artifacts.py tests\test_supply_chain_artifacts.py tests\test_provenance_artifacts.py
$files = @('.\scripts\run_container_scan_check.ps1', '.\scripts\run_supply_chain_check.ps1'); foreach ($file in $files) { $errors=$null; [System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw $file), [ref]$errors) | Out-Null; if ($errors) { $errors | Format-List | Out-String | Write-Error; exit 1 } }; Write-Host 'powershell parser: ok'
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
.\scripts\run_container_scan_check.ps1
cd backend; py -3.12 -m pytest --collect-only
py -3.12 .\scripts\source_readiness.py --priority Must --json
git diff --check
docker ps -a --filter "name=land-diligence-smoke" --format "{{.Names}} {{.Status}}"; docker ps -a --filter "name=live-connector-worker-run" --format "{{.Names}} {{.Status}}"; docker compose ps; docker compose --project-name land-diligence-smoke ps
```

**Results:**

- `.\scripts\run_container_scan_check.ps1` passed.
- `.\scripts\run_supply_chain_check.ps1` passed after the container scan runbook was
  linked from the supply-chain proof.
- Focused tests passed: 10 passed.
- Ruff passed for touched container/supply-chain/provenance artifact tests.
- Mypy passed for touched container/supply-chain/provenance artifact tests.
- PowerShell parser validation passed for `scripts/run_container_scan_check.ps1` and
  `scripts/run_supply_chain_check.ps1`.
- Full DB-enabled `.\scripts\verify.ps1` passed after the US-059 slice.
- Test collection is 657 tests.
- Canonical mypy is clean over 178 source files.
- Source-readiness JSON remains `sources=8 ready=4 blocked=4`.
- `git diff --check` exits 0 with only CRLF normalization warnings on generated/state
  files.
- No smoke or worker-run containers remain running.

**Residual risk:**

- This proves repo-local CI wiring for a Docker Scout critical/high CVE scan of the
  locally built backend image and validates the Docker build context boundaries. At the
  US-059 point, it did not digest-pin the base image, attest or scan a published registry
  image, publish or sign an image SBOM, produce a SLSA provenance attestation, validate
  hosted deployment runtime state, scan GitHub Actions internals, or approve
  source/vendor rights; US-060 later added the digest-pinned base-image proof.

## 2026-06-05 Level 10 dependency provenance proof

**Scope:**

- Added `backend/requirements-prod.lock`.
- Added `docs/sbom/backend-prod-sbom.json`.
- Added `docs/runbooks/dependency_provenance.md`.
- Added `scripts/run_provenance_check.ps1`.
- Added `scripts/run_provenance_check.sh`.
- Added `backend/tests/test_provenance_artifacts.py`.
- Updated `.github/workflows/ci.yml`, `docs/runbooks/supply_chain.md`,
  `docs/runbooks/mvp_operator.md`, `MANIFEST.md`, the active Level 10 plan, and state
  records.

**Commands run:**

```powershell
.\scripts\run_provenance_check.ps1
.\scripts\run_supply_chain_check.ps1
cd backend; py -3.12 -m pytest -q tests\test_provenance_artifacts.py tests\test_supply_chain_artifacts.py tests\test_cost_monitoring_artifacts.py
cd backend; ruff check tests\test_provenance_artifacts.py tests\test_supply_chain_artifacts.py tests\test_cost_monitoring_artifacts.py
cd backend; py -3.12 -m mypy tests\test_provenance_artifacts.py tests\test_supply_chain_artifacts.py tests\test_cost_monitoring_artifacts.py
$files = @('.\scripts\run_provenance_check.ps1', '.\scripts\run_supply_chain_check.ps1'); foreach ($file in $files) { $errors=$null; [System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw $file), [ref]$errors) | Out-Null; if ($errors) { $errors | Format-List | Out-String | Write-Error; exit 1 } }; Write-Host 'powershell parser: ok'
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
py -3.12 .\scripts\source_readiness.py --priority Must --json
git diff --check
docker ps -a --filter "name=land-diligence-smoke" --format "{{.Names}} {{.Status}}"; docker ps -a --filter "name=live-connector-worker-run" --format "{{.Names}} {{.Status}}"; docker compose ps; docker compose --project-name land-diligence-smoke ps
```

**Results:**

- `.\scripts\run_provenance_check.ps1` passed, including the hash-checked pip dry run
  for CPython 3.12 manylinux binary wheels.
- `.\scripts\run_supply_chain_check.ps1` passed after adding the provenance CI step.
- Focused tests passed: 11 passed.
- Ruff passed for touched provenance/supply-chain/cost artifact tests.
- Mypy passed for touched provenance/supply-chain/cost artifact tests.
- PowerShell parser validation passed for `scripts/run_provenance_check.ps1` and
  `scripts/run_supply_chain_check.ps1`.
- Full DB-enabled `.\scripts\verify.ps1` passed after the US-058 slice.
- Test collection is 653 tests.
- Canonical mypy is clean over 177 source files.
- Source-readiness JSON remains `sources=8 ready=4 blocked=4`.
- `git diff --check` exits 0 with only CRLF normalization warnings on generated/state
  files.
- No smoke or worker-run containers remain running.

**Residual risk:**

- This proves repo-local backend Python production dependency lock/SBOM artifacts and CI
  wiring. At the US-058 point, it did not publish or sign the SBOM, produce a SLSA
  provenance attestation, scan Docker base-image packages, attest GitHub Actions runtime
  internals, or approve new production dependencies; US-059 later added the repo-local
  container image scan proof.

## 2026-06-05 Level 10 cost monitoring proof

**Scope:**

- Added `config/ops_cost_monitoring.yaml`.
- Added `docs/runbooks/cost_monitoring.md`.
- Added `scripts/run_cost_monitoring_check.ps1`.
- Added `scripts/run_cost_monitoring_check.sh`.
- Added `backend/tests/test_cost_monitoring_artifacts.py`.
- Updated `config/ops_alert_rules.yaml`, `docs/runbooks/alerting.md`,
  `docs/runbooks/mvp_operator.md`, `MANIFEST.md`, the active Level 10 plan, and state
  records.

**Commands run:**

```powershell
.\scripts\run_cost_monitoring_check.ps1
cd backend; py -3.12 -m pytest -q tests\test_cost_monitoring_artifacts.py tests\test_supply_chain_artifacts.py tests\test_alerting_artifacts.py
cd backend; ruff check tests\test_cost_monitoring_artifacts.py tests\test_supply_chain_artifacts.py tests\test_alerting_artifacts.py
cd backend; py -3.12 -m mypy tests\test_cost_monitoring_artifacts.py tests\test_supply_chain_artifacts.py tests\test_alerting_artifacts.py
$errors=$null; [System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw .\scripts\run_cost_monitoring_check.ps1), [ref]$errors) | Out-Null; if ($errors) { $errors | Format-List | Out-String | Write-Error; exit 1 }; Write-Host 'powershell parser: ok'
.\scripts\run_alert_rules_check.ps1
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
py -3.12 .\scripts\source_readiness.py --priority Must --json
git diff --check
docker ps -a --filter "name=land-diligence-smoke" --format "{{.Names}} {{.Status}}"; docker ps -a --filter "name=live-connector-worker-run" --format "{{.Names}} {{.Status}}"; docker compose ps; docker compose --project-name land-diligence-smoke ps
```

**Results:**

- `.\scripts\run_cost_monitoring_check.ps1` passed.
- `.\scripts\run_alert_rules_check.ps1` passed after the cost-monitoring alert rule was
  added.
- Focused tests passed: 12 passed.
- Ruff passed for touched cost/supply-chain/alerting artifact tests.
- Mypy passed for touched cost/supply-chain/alerting artifact tests.
- PowerShell parser validation passed for `scripts/run_cost_monitoring_check.ps1`.
- Full DB-enabled `.\scripts\verify.ps1` passed after the US-057 slice.
- Test collection is 650 tests.
- Canonical mypy is clean over 176 source files.
- Source-readiness JSON remains `sources=8 ready=4 blocked=4`.
- `git diff --check` exits 0 with only CRLF normalization warnings on generated/state
  files.
- No smoke or worker-run containers remain running.

**Residual risk:**

- This proves repo-local cost monitoring artifacts and guardrails. It does not create
  hosted cloud billing integration, vendor billing ingestion, dollar-cost attribution,
  production unit-cost thresholds, human-review minute capture, or batch spend controls.
- Current `cost_metrics` are report-shape counts, not actual dollars.

## 2026-06-05 Level 10 supply-chain scan configuration

**Scope:**

- Updated `.github/workflows/ci.yml` with a `supply-chain` job.
- Added `.github/dependabot.yml`.
- Added `docs/runbooks/supply_chain.md`.
- Added `scripts/run_supply_chain_check.ps1`.
- Added `scripts/run_supply_chain_check.sh`.
- Added `backend/tests/test_supply_chain_artifacts.py`.
- Updated `docs/runbooks/mvp_operator.md`, `MANIFEST.md`, the active Level 10 plan, and
  state records.

**Commands run:**

```powershell
.\scripts\run_supply_chain_check.ps1
cd backend; py -3.12 -m pytest -q tests\test_supply_chain_artifacts.py tests\test_alerting_artifacts.py
cd backend; ruff check tests\test_supply_chain_artifacts.py tests\test_alerting_artifacts.py
cd backend; py -3.12 -m mypy tests\test_supply_chain_artifacts.py tests\test_alerting_artifacts.py
$errors=$null; [System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw .\scripts\run_supply_chain_check.ps1), [ref]$errors) | Out-Null; if ($errors) { $errors | Format-List | Out-String | Write-Error; exit 1 }; Write-Host 'powershell parser: ok'
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

**Results:**

- `.\scripts\run_supply_chain_check.ps1` passed.
- Focused tests passed after fixing one runbook wording assertion.
- Ruff passed for touched supply-chain/alerting artifact tests.
- Mypy passed for touched supply-chain/alerting artifact tests.
- PowerShell parser validation passed for `scripts/run_supply_chain_check.ps1`.
- Full DB-enabled `.\scripts\verify.ps1` passed after the US-056 slice.
- Canonical mypy is clean over 175 source files.

**Residual risk:**

- Local validation proves the CI configuration and runbook shape. It does not perform the
  live advisory-backed vulnerability scan locally.
- The CI `supply-chain` job performs Python dependency vulnerability scanning. At the
  US-056 point the repo still had no fully locked production dependency file, signed
  SBOM, SLSA provenance attestation, Docker base-image package scan, or GitHub Actions
  runtime attestation; US-058 later added the repo-local production lock/SBOM proof.

## 2026-06-05 Level 10 alert rules proof

**Scope:**

- Added `config/ops_alert_rules.yaml`.
- Added `docs/runbooks/alerting.md`.
- Added `scripts/run_alert_rules_check.ps1`.
- Added `scripts/run_alert_rules_check.sh`.
- Added `backend/tests/test_alerting_artifacts.py`.
- Updated `docs/runbooks/mvp_operator.md`, `docs/runbooks/incident_response.md`,
  `MANIFEST.md`, the active Level 10 plan, and state records.

**Commands run:**

```powershell
.\scripts\run_alert_rules_check.ps1
cd backend; py -3.12 -m pytest -q tests\test_alerting_artifacts.py tests\test_incident_rollback_artifacts.py tests\test_deployment_smoke_scripts.py
cd backend; ruff check tests\test_alerting_artifacts.py tests\test_incident_rollback_artifacts.py tests\test_deployment_smoke_scripts.py
cd backend; py -3.12 -m mypy tests\test_alerting_artifacts.py tests\test_incident_rollback_artifacts.py tests\test_deployment_smoke_scripts.py
$errors=$null; [System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw .\scripts\run_alert_rules_check.ps1), [ref]$errors) | Out-Null; if ($errors) { $errors | Format-List | Out-String | Write-Error; exit 1 }; Write-Host 'powershell parser: ok'
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
py -3.12 .\scripts\source_readiness.py --priority Must --json
git diff --check
docker ps -a --filter "name=land-diligence-smoke" --format "{{.Names}} {{.Status}}"; docker ps -a --filter "name=live-connector-worker-run" --format "{{.Names}} {{.Status}}"; docker compose ps; docker compose --project-name land-diligence-smoke ps
```

**Results:**

- `.\scripts\run_alert_rules_check.ps1` passed.
- Focused tests passed: 8 passed.
- Ruff passed for touched alerting/ops artifact tests.
- Mypy passed for touched alerting/ops artifact tests.
- PowerShell parser validation passed for `scripts/run_alert_rules_check.ps1`.
- Full DB-enabled `.\scripts\verify.ps1` passed after the US-055 slice.
- Test collection is 642 tests.
- Source-readiness JSON remains `sources=8 ready=4 blocked=4`.
- `git diff --check` exits 0 with only CRLF normalization warnings on generated/state
  files.
- No `land-diligence-smoke` or `live-connector-worker-run` containers remain running.

**Residual risk:**

- This proves a repo-local alert-rule catalog and validate-only artifact check. It does
  not create hosted alert routing, dashboards, pager delivery, a named on-call rotation,
  or production log/metric aggregation.
- Source freshness rules validate registry metadata and operator review cadence; they do
  not independently verify every upstream dataset in real time.

## 2026-06-05 Level 10 incident response and rollback proof

**Scope:**

- Added `docs/runbooks/incident_response.md`.
- Added `scripts/run_incident_rollback_check.ps1`.
- Added `scripts/run_incident_rollback_check.sh`.
- Added `backend/tests/test_incident_rollback_artifacts.py`.
- Updated `docs/runbooks/mvp_operator.md`, `MANIFEST.md`, the active Level 10 plan, and
  state records.

**Commands run:**

```powershell
.\scripts\run_incident_rollback_check.ps1
cd backend; py -3.12 -m pytest -q tests\test_incident_rollback_artifacts.py tests\test_deployment_smoke_scripts.py tests\api\test_app_runtime_mode.py
cd backend; ruff check tests\test_incident_rollback_artifacts.py tests\test_deployment_smoke_scripts.py tests\api\test_app_runtime_mode.py
cd backend; py -3.12 -m mypy tests\test_incident_rollback_artifacts.py tests\test_deployment_smoke_scripts.py tests\api\test_app_runtime_mode.py
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
py -3.12 .\scripts\source_readiness.py --priority Must --json
git diff --check
docker ps -a --filter "name=land-diligence-smoke" --format "{{.Names}} {{.Status}}"; docker compose --project-name land-diligence-smoke ps
```

**Results:**

- `.\scripts\run_incident_rollback_check.ps1` passed.
- Focused tests passed: 7 passed.
- Ruff passed for touched incident/runtime artifact tests.
- Mypy passed for touched incident/runtime artifact tests.
- Full DB-enabled `.\scripts\verify.ps1` passed after the US-054 slice.
- Test collection is 638 tests.
- Source-readiness JSON remains `sources=8 ready=4 blocked=4`.
- `git diff --check` exits 0 with only CRLF normalization warnings on generated/state
  files.
- No `land-diligence-smoke` or `live-connector-worker-run` containers remain running.
- POSIX script static coverage exists, but local `bash -n` could not run because the
  available `bash` command is a broken WSL relay in this environment.

**Residual risk:**

- This proves the repo-local incident/rollback runbook and validation check. It does not
  create a real hosted on-call rotation, pager escalation, alert routing, production
  rollback pipeline, or automatic down migrations.
- Incident owner identities remain role-based until a production deployment owner defines
  a named rotation outside the repo.

## 2026-06-05 Level 10 deployment smoke automation

**Scope:**

- Added `scripts/run_deployment_smoke.ps1`.
- Added `scripts/run_deployment_smoke.sh`.
- Added `USE_DB_SERVICES` runtime config and Compose `COMPOSE_USE_DB_SERVICES=true`.
- Updated `docs/runbooks/mvp_operator.md`, `MANIFEST.md`, `.env.example`, the active
  Level 10 plan, and state records.
- Guarded repeated application of `rule_execution_report_fk` in
  `db/migrations/0001_initial_spine.sql`.

**Commands run:**

```powershell
.\scripts\run_deployment_smoke.ps1
cd backend; py -3.12 -m pytest -q tests\api\test_app_runtime_mode.py tests\test_deployment_smoke_scripts.py tests\api\test_operations.py tests\reports\test_job_store.py tests\test_planning_pack_schema_copies.py
cd backend; ruff check app\core\config.py app\main.py app\api\operations.py app\reports\job_store.py app\connectors\live_jobs.py tests\api\test_app_runtime_mode.py tests\test_deployment_smoke_scripts.py tests\api\test_operations.py tests\reports\test_job_store.py tests\test_planning_pack_schema_copies.py
cd backend; py -3.12 -m mypy app\core\config.py app\main.py app\api\operations.py app\reports\job_store.py app\connectors\live_jobs.py tests\api\test_app_runtime_mode.py tests\test_deployment_smoke_scripts.py tests\api\test_operations.py tests\reports\test_job_store.py tests\test_planning_pack_schema_copies.py
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
py -3.12 .\scripts\source_readiness.py --priority Must --json
git diff --check
docker ps -a --filter "name=land-diligence-smoke" --format "{{.Names}} {{.Status}}"; docker compose --project-name land-diligence-smoke ps
```

**Results:**

- Initial deployment smoke failed because migrations ran before the DB accepted local
  socket connections inside the container. The script now waits for `pg_isready`.
- The next deployment smoke exposed non-idempotent repeated migration application for
  `rule_execution_report_fk`. The migration now guards the FK through `pg_constraint`.
- Final deployment smoke passed. It built the backend image, started the DB-backed
  Compose backend, applied migrations/seeds, probed health/version/metrics/queue health,
  created an area, created a report job, and observed the report reach `succeeded`.
- Focused tests passed: 17 passed, 4 skipped DB-smoke tests, plus OpenAPI parity.
- Ruff passed for touched config/app/API/store/test paths.
- Mypy passed for touched config/app/API/store/test paths.
- Full DB-enabled `.\scripts\verify.ps1` passed after the US-053 slice.
- Test collection is 636 tests.
- Source-readiness JSON remains `sources=8 ready=4 blocked=4`.
- `git diff --check` exits 0 with only CRLF normalization warnings on generated/state
  files.
- No `land-diligence-smoke` or `live-connector-worker-run` containers remain running.

**Residual risk:**

- This proves local Compose deployment smoke for the DB-backed backend path. It does not
  yet prove hosted infrastructure deployment, CI/CD deploy gating, alert routing,
  rollback execution, production secrets rotation, or external source outage handling.
- Smoke volumes are intentionally not removed by default; the script reuses the isolated
  `land-diligence-smoke` project unless `DEPLOYMENT_SMOKE_PROJECT` is overridden.

## 2026-06-05 Level 10 operator queue health

**Scope:**

- Added reviewer-authenticated `GET /operations/queue-health`.
- Added shared `JobQueueHealth` DTO plus in-memory and DB-backed health aggregation for
  `report_run` and `live_connector_run` jobs.
- Updated `docs/runbooks/mvp_operator.md`, the active Level 10 plan, state records, and
  regenerated `docs/planning_pack/api/openapi_stub.yaml`.

**Commands run:**

```powershell
cd backend; py -3.12 -m pytest -q tests\api\test_operations.py tests\reports\test_job_store.py
cd backend; ruff check app\api\operations.py app\main.py app\reports\job_store.py app\connectors\live_jobs.py tests\api\test_operations.py tests\reports\test_job_store.py
cd backend; py -3.12 -m mypy app\api\operations.py app\main.py app\reports\job_store.py app\connectors\live_jobs.py tests\api\test_operations.py tests\reports\test_job_store.py
cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests\api\test_operations.py tests\reports\test_job_store.py tests\test_planning_pack_schema_copies.py
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
py -3.12 .\scripts\source_readiness.py --priority Must --json
git diff --check
docker ps -a --filter "name=live-connector-worker-run" --format "{{.Names}} {{.Status}}"; docker compose ps
```

**Results:**

- Focused tests passed: 12 passed, 4 skipped DB-smoke tests.
- Ruff passed for touched operation/job-store/API paths.
- Mypy passed for touched operation/job-store/API paths after tightening the SQL row
  helper type boundary.
- DB-enabled focused tests passed: 18 passed, including OpenAPI parity.
- Full DB-enabled `.\scripts\verify.ps1` passed after the US-052 slice.
- Test collection is 631 tests.
- Source-readiness JSON remains `sources=8 ready=4 blocked=4`.
- `git diff --check` exits 0 with only CRLF normalization warnings on generated/state
  files.
- `docker compose ps` reports no repo services running and no `live-connector-worker-run`
  containers remain.

**Residual risk:**

- Queue health is an authenticated, read-only operator surface. It does not define alert
  thresholds, paging policy, dashboards, stuck-job remediation, deployment smoke
  automation, or incident/rollback execution.

## 2026-06-05 Level 10 backup/restore proof

**Scope:**

- Added `scripts/run_backup_restore_check.ps1`.
- Added `scripts/run_backup_restore_check.sh`.
- Added `docs/runbooks/backup_restore.md`.
- Updated `MANIFEST.md`, `.env.example`, `docs/runbooks/mvp_operator.md`, the active
  Level 10 plan, and state records.

**Commands run:**

```powershell
.\scripts\run_backup_restore_check.ps1
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
py -3.12 .\scripts\source_readiness.py --priority Must --json
git diff --check
docker ps -a --filter "name=live-connector-worker-run" --format "{{.Names}} {{.Status}}"; docker compose ps
docker run --rm postgis/postgis:16-3.4 psql postgresql://land:land@host.docker.internal:5432/postgres -tAc "SELECT 1 FROM pg_database WHERE datname = 'land_diligence_restore_check'"
```

**Results:**

- Initial run failed closed because local `pg_dump` was not installed and the existing
  `psql` wrapper targets the repo's compose `db` service, which was not running.
- The scripts were updated to use Docker's `postgis/postgis:16-3.4` image as a PostgreSQL
  client fallback for both `pg_dump` and `psql` when local `pg_dump` is absent.
- Re-run passed. It dumped the configured source DB, restored into
  `land_diligence_restore_check`, ran `scripts/db_smoke_check.py` against the restored DB,
  printed `backup/restore check: ok`, and dropped the restore DB.
- Full DB-enabled `.\scripts\verify.ps1` passed after the US-051 slice.
- Test collection is 627 tests.
- Source-readiness JSON remains `sources=8 ready=4 blocked=4`.
- `git diff --check` exits 0 with only CRLF normalization warnings on generated/state
  files.
- `docker compose ps` reports no repo services running, no `live-connector-worker-run`
  containers remain, and a Docker psql query returned no row for
  `land_diligence_restore_check` after cleanup.

**Residual risk:**

- This proves a local logical dump/restore path and DB smoke invariants. It does not yet
  define production backup retention, encryption, offsite replication, RPO/RTO targets, or
  scheduled backup monitoring.
- The default dump path is under ignored `local_artifacts/backup_restore`; production
  backups must use an approved encrypted artifact location.

## 2026-06-05 Level 10 failed report job retry

**Scope:**

- Added reviewer-authenticated `POST /report-runs/{report_run_id}/retry`.
- The route accepts only failed report jobs, preserves the failed job, and creates a new
  queued report job from the failed job's stored area and intent.
- Added `retry_of_report_run_id` lineage to in-memory and DB-backed async report job
  records.
- Updated `docs/runbooks/mvp_operator.md` and regenerated
  `docs/planning_pack/api/openapi_stub.yaml`.

**Commands run:**

```powershell
cd backend; py -3.12 -m pytest -q tests\reports\test_job_store.py tests\api\test_async_report_runs.py
cd backend; ruff check app\reports\job_store.py app\api\reports.py tests\reports\test_job_store.py tests\api\test_async_report_runs.py
cd backend; py -3.12 -m mypy app\reports\job_store.py app\api\reports.py tests\reports\test_job_store.py tests\api\test_async_report_runs.py
cd backend; py -3.12 -c "from pathlib import Path; import yaml; from app.main import create_app; Path('../docs/planning_pack/api/openapi_stub.yaml').write_text(yaml.dump(create_app().openapi(), sort_keys=True), encoding='utf-8')"
cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests\reports\test_job_store.py tests\api\test_async_report_runs.py tests\test_planning_pack_schema_copies.py
cd backend; ruff check app\reports\job_store.py app\api\reports.py tests\reports\test_job_store.py tests\api\test_async_report_runs.py tests\test_planning_pack_schema_copies.py
cd backend; py -3.12 -m mypy app\reports\job_store.py app\api\reports.py tests\reports\test_job_store.py tests\api\test_async_report_runs.py tests\test_planning_pack_schema_copies.py
cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests\api\test_async_report_runs.py tests\api\test_report_runs_db.py tests\api\test_api_scaffold.py tests\api\test_intake.py tests\api\test_reviewer_auth.py tests\api\test_metrics.py tests\api\test_fema_nfhl_connector_api.py::test_db_live_connector_report_run_waits_for_approval_then_reports tests\api\test_nwi_connector_api.py::test_approved_nwi_connector_run_feeds_report_without_refetch tests\reports\test_job_store.py tests\reports\test_report_service.py tests\test_planning_pack_schema_copies.py
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
py -3.12 .\scripts\source_readiness.py --priority Must --json
git diff --check
docker compose ps
docker ps -a --filter "name=live-connector-worker-run" --format "{{.Names}} {{.Status}}"
```

**Results:**

- Focused retry/job-store tests passed with expected DB-smoke skips before DB smoke.
- DB-enabled retry/job-store/OpenAPI parity tests passed: 22 tests.
- Broader report/API regression passed: 64 tests.
- Focused ruff and mypy passed.
- Full DB-enabled `.\scripts\verify.ps1` passed after the US-050 slice.
- Test collection is 627 tests.
- Source-readiness JSON remains `sources=8 ready=4 blocked=4`.
- `git diff --check` exits 0 with only CRLF normalization warnings on generated/state
  files.
- `docker compose ps` reports no running services, and no `live-connector-worker-run`
  containers remain.

**Residual risk:**

- Retry is explicit and operator-driven; it does not add automatic retry/backoff,
  distributed workers, or a queue dashboard.
- The failed job remains the failure record; the retry creates a new job instead of
  mutating the original.

## 2026-06-05 Level 10 live connector sequence scheduler

**Scope:**

- Added reviewer-authenticated `POST /connector-runs/live-sequence/schedule-bbox`.
- The route validates a registered area and bounded bbox, then enqueues the reviewed live
  connector sequence as separate durable jobs in order: DS-001, DS-002, DS-004, DS-003.
- The sequence request uses a source-neutral bbox schema instead of a FEMA-specific
  public model.
- Added ADR `docs/adr/live-sequence.md`.
- Updated `docs/runbooks/mvp_operator.md` with the reviewed live sequence scheduling
  workflow and current live-connector limitations.
- Regenerated `docs/planning_pack/api/openapi_stub.yaml` from `create_app().openapi()`.

**Commands run:**

```powershell
cd backend; py -3.12 -m pytest -q tests\api\test_fema_nfhl_connector_api.py::test_live_connector_sequence_schedule_bbox_enqueues_ordered_jobs_without_fetch_or_report tests\api\test_fema_nfhl_connector_api.py::test_live_connector_sequence_schedule_bbox_requires_reviewer_auth tests\api\test_fema_nfhl_connector_api.py::test_live_connector_sequence_schedule_bbox_rejects_unregistered_area
cd backend; ruff check app\api\connectors.py tests\api\test_fema_nfhl_connector_api.py
cd backend; py -3.12 -m mypy app\api\connectors.py tests\api\test_fema_nfhl_connector_api.py
cd backend; py -3.12 -c "from pathlib import Path; import yaml; from app.main import create_app; Path('../docs/planning_pack/api/openapi_stub.yaml').write_text(yaml.dump(create_app().openapi(), sort_keys=True), encoding='utf-8')"
cd backend; py -3.12 -m pytest -q tests\test_planning_pack_schema_copies.py tests\api\test_fema_nfhl_connector_api.py::test_live_connector_sequence_schedule_bbox_enqueues_ordered_jobs_without_fetch_or_report tests\api\test_fema_nfhl_connector_api.py::test_live_connector_sequence_schedule_bbox_requires_reviewer_auth tests\api\test_fema_nfhl_connector_api.py::test_live_connector_sequence_schedule_bbox_rejects_unregistered_area
cd backend; ruff check app\api\connectors.py tests\api\test_fema_nfhl_connector_api.py tests\test_planning_pack_schema_copies.py
cd backend; py -3.12 -m mypy app\api\connectors.py tests\api\test_fema_nfhl_connector_api.py tests\test_planning_pack_schema_copies.py
cd backend; py -3.12 -m pytest -q tests\test_planning_pack_schema_copies.py tests\api\test_fema_nfhl_connector_api.py tests\api\test_nwi_connector_api.py tests\api\test_ssurgo_connector_api.py tests\api\test_usgs_tnm_connector_api.py tests\api\test_live_connector_worker.py
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
py -3.12 .\scripts\source_readiness.py --priority Must --json
git diff --check
docker compose ps
docker ps -a --filter "name=live-connector-worker-run" --format "{{.Names}} {{.Status}}"
```

**Results:**

- Focused sequence scheduler tests passed: 3 tests.
- OpenAPI parity plus focused sequence scheduler tests passed: 5 tests.
- Broader connector API/worker regression passed with expected DB-smoke skips.
- Focused ruff and mypy passed.
- Full DB-enabled `.\scripts\verify.ps1` passed: workspace validation, backend tests,
  ruff, canonical mypy over 167 source files, migrations/seeds, and DB smoke are clean.
- Re-ran the full DB-enabled gate after the neutral sequence bbox schema cleanup.
- Test collection is 622 tests.
- Source-readiness JSON remains `sources=8 ready=4 blocked=4`.
- `git diff --check` exits 0 with only CRLF normalization warnings on generated/state
  files.
- `docker compose ps` reports no running services, and no `live-connector-worker-run`
  containers remain.

**Residual risk:**

- This is an operator scheduling convenience only. It does not fetch live sources,
  persist evidence, approve connector review items, retry or requeue jobs, create
  reports, or define source-specific cadence/autonomous scheduling policy.
- Remaining `Must` source blockers outside DS-001/DS-002/DS-003/DS-004 still require
  jurisdiction/vendor/license decisions before production connector work.

## 2026-06-05 Level 10 API 422 deprecation cleanup

**Scope:**

- Replaced deprecated `status.HTTP_422_UNPROCESSABLE_ENTITY` usages in API route
  exception paths with `status.HTTP_422_UNPROCESSABLE_CONTENT`.
- Kept the wire-level status code unchanged at 422.
- Touched API route modules only: areas, connectors, intake, live connectors, and
  reports.

**Commands run:**

```powershell
cd backend; py -3.12 -m pytest -q -W error::DeprecationWarning tests\api\test_api_scaffold.py::test_api_scaffold_returns_422_for_bad_input tests\api\test_async_report_runs.py::test_post_report_runs_unregistered_area_returns_422 tests\api\test_intake.py::test_intake_invalid_geojson_returns_422 tests\api\test_connector_review_actions.py::test_request_fixture_fix_requires_reason tests\api\test_fema_nfhl_connector_api.py::test_fema_nfhl_query_bbox_rejects_oversized_bbox tests\api\test_nwi_connector_api.py::test_nwi_query_bbox_rejects_oversized_bbox tests\api\test_ssurgo_connector_api.py::test_ssurgo_query_bbox_rejects_oversized_bbox tests\api\test_usgs_tnm_connector_api.py::test_usgs_tnm_query_bbox_rejects_oversized_bbox
cd backend; ruff check app\api\areas.py app\api\connectors.py app\api\intake.py app\api\live_connectors.py app\api\reports.py
cd backend; py -3.12 -m mypy app\api\areas.py app\api\connectors.py app\api\intake.py app\api\live_connectors.py app\api\reports.py
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
py -3.12 .\scripts\source_readiness.py --priority Must --json
git diff --check
docker compose ps
docker ps -a --filter "name=live-connector-worker-run" --format "{{.Names}} {{.Status}}"
```

**Results:**

- Warning-producing API tests passed with deprecations promoted to errors: 8 tests.
- Focused ruff passed.
- Focused mypy passed for 5 API modules.
- Full DB-enabled `.\scripts\verify.ps1` passed without the prior 422 deprecation warning
  summary: workspace validation, backend tests, ruff, canonical mypy over 167 source
  files, migrations/seeds, and DB smoke are clean.
- Test collection remains 619 tests.
- Source-readiness JSON remains `sources=8 ready=4 blocked=4`.
- `git diff --check` exits 0 with only CRLF normalization warnings on generated/state
  files.
- `docker compose ps` reports no running services, and no `live-connector-worker-run`
  containers remain.

**Residual risk:**

- This is a warning cleanup only. It does not alter validation semantics, response
  payloads, connector behavior, source rights, report semantics, or database schema.

## 2026-06-05 Level 10 DS-004 NWI fixture corpus and worker metadata

**Scope:**

- Added file-backed raw DS-004 NWI response fixtures for a representative success
  FeatureCollection and an empty FeatureCollection.
- Added connector tests that load those fixtures directly and prove success parsing plus
  empty-response source-failure behavior.
- Updated live connector worker CLI help text to name DS-001, DS-002, DS-003, and DS-004
  as supported queued live connector sources.
- Added a worker help regression so supported-source metadata cannot silently omit
  DS-001 again.

**Commands run:**

```powershell
cd backend; py -3.12 -m pytest -q tests\connectors\test_nwi_connector.py tests\api\test_live_connector_worker.py
cd backend; ruff check tests\connectors\test_nwi_connector.py tests\api\test_live_connector_worker.py ..\scripts\live_connector_worker.py
cd backend; py -3.12 -m mypy tests\connectors\test_nwi_connector.py tests\api\test_live_connector_worker.py
cd backend; py -3.12 -m pytest -q tests\connectors\test_nwi_connector.py tests\api\test_nwi_connector_api.py tests\api\test_live_connector_worker.py
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
py -3.12 .\scripts\source_readiness.py --priority Must --json
git diff --check
docker compose ps
docker ps -a --filter "name=live-connector-worker-run" --format "{{.Names}} {{.Status}}"
```

**Results:**

- Focused NWI connector and live-worker tests passed: 21 tests.
- Focused ruff passed.
- Focused mypy passed for the touched NWI/worker test paths.
- Broader DS-004 API/connector/worker regression passed: 30 passed, 1 skipped, with one
  pre-existing `HTTP_422_UNPROCESSABLE_ENTITY` deprecation warning.
- Full DB-enabled `.\scripts\verify.ps1` passed: workspace validation, backend tests,
  ruff, canonical mypy over 167 source files, migrations/seeds, and DB smoke are clean.
- Test collection is 619 tests.
- Source-readiness JSON remains `sources=8 ready=4 blocked=4`.
- `git diff --check` exits 0 with only CRLF normalization warnings on generated/state
  files.
- `docker compose ps` reports no running services, and no `live-connector-worker-run`
  containers remain.

**Residual risk:**

- This slice adds deterministic DS-004 connector-response fixtures and worker metadata
  coverage only. It does not add live NWI calls, source-specific autonomous scheduling,
  retry policy, queue mutation, report scheduling, or new wetland/buildability/legal
  conclusions.
- Empty NWI feature responses remain source-failure evidence, not proof that no mapped
  wetland/deepwater feature intersects the query area.

## 2026-06-05 Level 10 DS-001 request-time orchestration gate

**Scope:**

- Added DS-001 as the first default-off request-time live connector gate for `/intake`
  and `/report-runs` when `ENABLE_LIVE_CONNECTORS=true`.
- Preserved the existing fixed review-gated sequence after DS-001 approval:
  DS-002, then DS-004, then DS-003, with no report job created until all connector review
  items are approved.
- Proved approved DS-001 evidence can enter reports as buildability-domain terrain
  screening evidence without creating a DS-001 claim or terrain/buildability conclusion.
- Kept the explicit connector-run resume route as a one-approved-connector manual path;
  operators should use repeated `/report-runs` calls for the full request-time sequence.

**Commands run:**

```powershell
cd backend; py -3.12 -m pytest -q tests\api\test_usgs_tnm_connector_api.py tests\api\test_fema_nfhl_connector_api.py
cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests\api\test_fema_nfhl_connector_api.py::test_db_live_connector_report_run_waits_for_approval_then_reports
cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests\api\test_usgs_tnm_connector_api.py tests\api\test_fema_nfhl_connector_api.py tests\api\test_nwi_connector_api.py tests\api\test_ssurgo_connector_api.py tests\api\test_live_connector_worker.py
cd backend; ruff check app\api\live_connectors.py tests\api\test_fema_nfhl_connector_api.py
cd backend; py -3.12 -m mypy app\api\live_connectors.py tests\api\test_fema_nfhl_connector_api.py
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
py -3.12 .\scripts\source_readiness.py --priority Must --json
git diff --check
docker compose ps
docker ps -a --filter "name=live-connector-worker-run" --format "{{.Names}} {{.Status}}"
```

**Results:**

- Focused DS-001 plus DS-002 API regression passed with DB skips in the first pass.
- DB-smoke DS-001 request-time approval-to-report regression passed.
- Combined DS-001/DS-002/DS-003/DS-004 connector API and worker suite passed with
  `RUN_DB_SMOKE=1`: 45 passed.
- Focused ruff passed.
- Focused mypy passed.
- Full DB-enabled `.\scripts\verify.ps1` passed: backend tests, ruff, canonical mypy over
  167 source files, migrations/seeds, and DB smoke are clean.
- Test collection remains 616 tests.
- Source-readiness JSON remains `sources=8 ready=4 blocked=4`.
- `git diff --check` exits 0 with only CRLF normalization warnings on generated/state
  files.
- `docker compose ps` reports no running services, and no `live-connector-worker-run`
  containers remain.

**Residual risk:**

- DS-001 remains screening-only: no DEM downloads, surveyed elevation, engineering,
  legal, buildability, lending, appraisal, investment conclusion, or DS-001-specific
  claim has been added.
- Remaining source-readiness blockers outside DS-001/DS-002/DS-003/DS-004 remain out of
  scope for this slice.

## 2026-06-05 Level 10 DS-001 USGS TNM EPQS durable scheduling

**Scope:**

- Added reviewer-authenticated `POST /connector-runs/usgs-tnm/schedule-bbox`.
- Extended durable `live_connector_run` job storage to DS-001, including in-memory and
  SQLAlchemy-backed enqueue/lease support with `max_sample_points` payload metadata.
- Extended the shared live connector worker dispatch to route DS-001 jobs by
  `source_registry_id`, run existing DS-001 orchestration, persist provenance/evidence,
  enqueue connector review state, and mark the live job succeeded or failed.
- Scheduling does not call EPQS, persist evidence, create report jobs, approve connector
  review items, or bypass review.
- The slice adds no DS-001 request-time `/intake` or `/report-runs` orchestration,
  DS-001-specific report semantics, DEM download, surveyed elevation, engineering,
  site-plan, legal, buildability, lending, appraisal, or investment conclusion.

**Commands run:**

```powershell
cd backend; py -3.12 -m pytest -q tests\api\test_usgs_tnm_connector_api.py tests\api\test_live_connector_worker.py
cd backend; ruff check app\connectors\live_jobs.py app\api\live_connector_jobs.py app\api\connectors.py app\connectors\__init__.py tests\api\test_usgs_tnm_connector_api.py
cd backend; py -3.12 -m mypy app\connectors\live_jobs.py app\api\live_connector_jobs.py app\api\connectors.py app\connectors\__init__.py tests\api\test_usgs_tnm_connector_api.py
cd backend; py -3.12 -m pytest -q tests\test_planning_pack_schema_copies.py tests\api\test_usgs_tnm_connector_api.py tests\api\test_nwi_connector_api.py tests\api\test_ssurgo_connector_api.py tests\api\test_fema_nfhl_connector_api.py tests\api\test_live_connector_worker.py
cd backend; ruff check app\connectors\live_jobs.py app\api\live_connector_jobs.py app\api\connectors.py app\connectors\__init__.py tests\api\test_usgs_tnm_connector_api.py tests\test_planning_pack_schema_copies.py
cd backend; py -3.12 -m mypy app\connectors\live_jobs.py app\api\live_connector_jobs.py app\api\connectors.py app\connectors\__init__.py tests\api\test_usgs_tnm_connector_api.py tests\test_planning_pack_schema_copies.py
cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests\api\test_usgs_tnm_connector_api.py::test_db_usgs_tnm_live_connector_job_store_persists_and_leases_ds001_payload
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
py -3.12 .\scripts\source_readiness.py --priority Must --json
git diff --check
docker compose ps
docker ps -a --filter "name=live-connector-worker-run" --format "{{.Names}} {{.Status}}"
```

**Results:**

- Focused DS-001 scheduler/API plus worker tests passed with expected DB-smoke skip.
- OpenAPI parity plus DS-001/DS-002/DS-003/DS-004 API regressions passed with expected
  DB-smoke skips.
- DB-smoke-gated DS-001 SQLAlchemy live-job enqueue/lease regression passed.
- Focused ruff and mypy passed for touched live-job, API, connector-export, and test
  paths.
- Full DB-enabled `.\scripts\verify.ps1` passed: workspace validation ok; backend tests
  passed; ruff passed; canonical mypy passed over 167 source files; migrations/seeds
  applied; DB smoke passed.
- `cd backend; py -3.12 -m pytest --collect-only` reports 616 collected tests.
- Source-readiness JSON remains `sources=8 ready=4 blocked=4`, with DS-001, DS-002,
  DS-003, and DS-004 ready by source-rights fields.
- `git diff --check` exited 0 with CRLF-to-LF warnings only for
  `docs/planning_pack/api/openapi_stub.yaml`,
  `docs/planning_pack/registers/data_source_registry.csv`, `state/PROJECT_STATE.md`,
  `state/VALIDATION_LOG.md`, and `state/WORKLOG.md`.
- `docker compose ps` showed no running services, and no worker-run containers remained.

**Residual risk:**

- DS-001 durable scheduling is an explicit operator queue/worker path only. DS-001 still
  has no request-time `/intake` or `/report-runs` orchestration, DS-001-specific report
  semantics, DEM download, surveyed elevation, slope/buildable-area calculation,
  engineering design, legal finding, buildability conclusion, lending conclusion,
  appraisal conclusion, or investment recommendation.
- The existing generic connector review/report gate remains shared infrastructure; this
  slice does not add DS-001-specific report claims or request-time report sequencing.

## 2026-06-05 Level 10 DS-001 USGS TNM EPQS API/operator invocation

**Scope:**

- Added reviewer-authenticated `POST /connector-runs/usgs-tnm/query-bbox`.
- The route requires a registered `area_id`, DS-001 source authority, and a bounded
  EPSG:4326 bbox no larger than 0.25 degrees in either dimension.
- The route invokes only `UsgsTnmElevationConnector`, records retrieval provenance,
  persists terrain-relief derived metric or source-failure evidence, builds review
  status, and enqueues connector review state.
- The slice refreshes OpenAPI parity and adds no DS-001 scheduler jobs, request-time
  `/intake` or `/report-runs` orchestration, report creation, DEM download, survey-grade
  elevation, engineering, site-plan, legal, buildability, lending, appraisal, or
  investment conclusion.

**Commands run:**

```powershell
cd backend; py -3.12 -m pytest -q tests\api\test_usgs_tnm_connector_api.py tests\connectors\test_usgs_tnm_connector.py
cd backend; ruff check app\api\connectors.py app\api\live_connectors.py app\api\dependencies.py tests\api\test_usgs_tnm_connector_api.py
cd backend; py -3.12 -m mypy app\api\connectors.py app\api\live_connectors.py app\api\dependencies.py tests\api\test_usgs_tnm_connector_api.py
cd backend; py -3.12 -m pytest -q tests\test_planning_pack_schema_copies.py tests\api\test_usgs_tnm_connector_api.py tests\api\test_nwi_connector_api.py tests\api\test_ssurgo_connector_api.py
cd backend; ruff check app\api\connectors.py app\api\live_connectors.py app\api\dependencies.py tests\api\test_usgs_tnm_connector_api.py tests\test_planning_pack_schema_copies.py
cd backend; py -3.12 -m mypy app\api\connectors.py app\api\live_connectors.py app\api\dependencies.py tests\api\test_usgs_tnm_connector_api.py tests\test_planning_pack_schema_copies.py
cd backend; py -3.12 -m mypy tests\test_planning_pack_schema_copies.py
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
py -3.12 .\scripts\source_readiness.py --priority Must --json
git diff --check
docker compose ps
docker ps -a --filter "name=live-connector-worker-run" --format "{{.Names}} {{.Status}}"
```

**Results:**

- Focused DS-001 API plus connector tests passed: 17 passed.
- OpenAPI parity plus DS-001/DS-003/DS-004 API regressions passed with expected
  DB-smoke skips.
- Focused ruff passed for touched API/dependency/test paths.
- Focused mypy passed for touched API/dependency/test paths after annotating the
  planning-pack parity test's PyYAML import through an `importlib`/`Any` cast that is
  clean in both direct and canonical mypy modes.
- Full DB-enabled `.\scripts\verify.ps1` passed: workspace validation ok; backend tests
  passed; ruff passed; canonical mypy passed over 167 source files; migrations/seeds
  applied; DB smoke passed.
- `cd backend; py -3.12 -m pytest --collect-only` reports 614 collected tests.
- Source-readiness JSON remains `sources=8 ready=4 blocked=4`, with DS-001, DS-002,
  DS-003, and DS-004 ready by source-rights fields.
- `git diff --check` exited 0 with CRLF-to-LF warnings only for
  `docs/planning_pack/api/openapi_stub.yaml`,
  `docs/planning_pack/registers/data_source_registry.csv`, `state/PROJECT_STATE.md`,
  `state/VALIDATION_LOG.md`, and `state/WORKLOG.md`.
- `docker compose ps` showed no running services, and no worker-run containers remained.

**Residual risk:**

- DS-001 still has no durable scheduler, request-time `/intake` or `/report-runs`
  orchestration, DS-001-specific report semantics, DEM download, surveyed elevation,
  slope/buildable-area calculation, engineering design, legal finding, buildability
  conclusion, lending conclusion, appraisal conclusion, or investment recommendation.
- The existing generic connector review/report gate remains shared infrastructure; this
  slice does not add DS-001-specific report claims or request-time report sequencing.

## 2026-06-05 Level 10 DS-001 USGS TNM EPQS connector layer

**Scope:**

- Added bounded connector-layer DS-001 USGS TNM EPQS terrain-relief screening.
- The connector samples the official EPQS JSON service at the EPSG:4326 bbox center and
  corners, requires a bbox no larger than 0.25 degrees in either dimension, and caps
  sample counts.
- Success emits one low-confidence `DERIVED_METRIC` screening observation with
  `metric_code="tnm_epqs_sampled_relief_m"` and source-ingest-run lineage.
- No-data, malformed, and request errors emit `SOURCE_FAILURE` evidence instead of
  negative evidence.
- At this connector-layer checkpoint, the slice reused existing retrieval provenance and
  evidence-ingestion adapters and added no DS-001 API/operator route, scheduler,
  request-time orchestration, report integration, DEM download, survey-grade elevation,
  engineering, site-plan, legal, buildability, lending, appraisal, or investment
  conclusions.

**Commands run:**

```powershell
cd backend; py -3.12 -m pytest -q tests\connectors\test_usgs_tnm_connector.py
cd backend; ruff check app\connectors\usgs_tnm.py app\connectors\__init__.py tests\connectors\test_usgs_tnm_connector.py
cd backend; py -3.12 -m mypy app\connectors\usgs_tnm.py app\connectors\__init__.py tests\connectors\test_usgs_tnm_connector.py
cd backend; py -3.12 -m pytest -q tests\connectors tests\evidence_ledger\test_payload_validation.py tests\claims_engine\test_rule_engine.py
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
py -3.12 .\scripts\source_readiness.py --priority Must --json
git diff --check
docker compose ps
docker ps -a --filter "name=live-connector-worker-run" --format "{{.Names}} {{.Status}}"
rg -n "DS-001.*no live|No DS-001 live connector|future DS-001 connector|does not add or imply a live USGS connector|DS-001 live connector was not added|future DS-001 connector work" .\state .\plans .\docs .\backend\app\connectors\usgs_tnm.py .\backend\tests\connectors\test_usgs_tnm_connector.py
```

**Results:**

- Focused DS-001 connector tests passed: 11 passed.
- Focused ruff passed for the DS-001 connector, connector exports, and DS-001 tests.
- Focused mypy passed for the DS-001 connector, connector exports, and DS-001 tests.
- Broader connector/evidence-payload/claim-rule regression passed with expected DB-smoke
  skips.
- Full DB-enabled `.\scripts\verify.ps1` passed: workspace validation ok; backend tests
  passed; ruff passed; canonical mypy passed over 166 source files; migrations/seeds
  applied; DB smoke passed.
- `cd backend; py -3.12 -m pytest --collect-only` reports 608 collected tests.
- Source-readiness JSON remains `sources=8 ready=4 blocked=4`, with DS-001, DS-002,
  DS-003, and DS-004 ready by source-rights fields.
- `git diff --check` exited 0 with CRLF-to-LF warnings only for
  `docs/planning_pack/api/openapi_stub.yaml`,
  `docs/planning_pack/registers/data_source_registry.csv`, `state/PROJECT_STATE.md`,
  `state/VALIDATION_LOG.md`, and `state/WORKLOG.md`.
- `docker compose ps` showed no running services, and no worker-run containers remained.
- Stale DS-001 "no live connector" scan hits are confined to historical source-review
  checkpoint entries; current state, plan, and runbook describe the DS-001 connector-layer
  slice and preserve the no-API/no-report boundary.

**Residual risk:**

- DS-001 terrain relief is sparse point-sample screening only. It is not a surveyed
  elevation product, DEM analysis, slope/buildable-area calculation, engineering design,
  site-plan approval, legal boundary/access finding, wetland jurisdiction finding,
  buildability conclusion, lending conclusion, appraisal conclusion, or investment
  recommendation.
- At this connector-layer checkpoint, DS-001 had no operator API, durable scheduler,
  request-time `/intake` or `/report-runs` orchestration, or report integration yet.
- Historical validation/worklog entries from the earlier DS-001 source-review checkpoint
  still state that no DS-001 live connector existed at that time; they are retained as
  historical records, not current authority.

## 2026-06-05 Level 10 DS-003 request-time orchestration

**Scope:**

- Extended shared request-time live connector orchestration for `/intake` and
  `/report-runs`: DS-002 runs first; after DS-002 approval, DS-004 runs for the same
  area; after DS-004 approval, DS-003 runs for the same area; report jobs are created
  only after all three connector review items are approved.
- Added a cautious rule-engine path for approved SSURGO spatial-intersection evidence:
  it emits an UNKNOWN, verification-required `SOIL_NOT_EVALUATED` screening-review claim
  rather than a septic approval, perc result, soil-suitability, permitting, buildability,
  lending, appraisal, or investment conclusion.
- Added in-memory API regressions proving `/report-runs` and `/intake` can progress
  through DS-002 approval, DS-004 approval, DS-003 approval, and then produce a report
  containing `FLOOD_001`, `WETLAND_001`, `SOIL_NOT_EVALUATED`, and approved DS-003
  soil/septic screening evidence.
- Updated the connector runbook and active Level 10 plan to distinguish the full
  request-time sequence from the manual one-connector report-resume route.

**Commands run:**

```powershell
cd backend; py -3.12 -m pytest -q tests\claims_engine\test_not_evaluated_claims.py tests\api\test_fema_nfhl_connector_api.py::test_live_connector_report_run_waits_for_ds004_ds003_then_reports tests\api\test_fema_nfhl_connector_api.py::test_live_connector_intake_can_continue_through_ds004_and_ds003_report_flow tests\api\test_ssurgo_connector_api.py
cd backend; ruff check app\api\live_connectors.py app\claims_engine\rule_engine.py tests\api\test_fema_nfhl_connector_api.py tests\claims_engine\test_not_evaluated_claims.py
cd backend; py -3.12 -m mypy app\api\live_connectors.py app\claims_engine\rule_engine.py tests\api\test_fema_nfhl_connector_api.py tests\claims_engine\test_not_evaluated_claims.py
cd backend; py -3.12 -m pytest -q tests\api\test_fema_nfhl_connector_api.py tests\api\test_ssurgo_connector_api.py tests\api\test_nwi_connector_api.py tests\reports tests\claims_engine
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
py -3.12 .\scripts\source_readiness.py --priority Must --json
git diff --check
docker compose ps
docker ps -a --filter "name=live-connector-worker-run" --format "{{.Names}} {{.Status}}"
```

**Results:**

- Focused DS-003 request-time/report tests passed: 14 passed, 1 skipped as expected for
  the DB-smoke-gated DS-003 job-store regression.
- Focused ruff passed for touched API, rule-engine, and regression-test paths.
- Focused mypy passed for touched API, rule-engine, and regression-test paths.
- Broader DS-002/DS-003/DS-004 API, reports, and claims regression passed with expected
  DB-smoke skips.
- Full DB-enabled `.\scripts\verify.ps1` passed: workspace validation ok; backend tests
  passed; ruff passed; canonical mypy passed over 164 source files; migrations/seeds
  applied; DB smoke passed.
- `cd backend; py -3.12 -m pytest --collect-only` reports 597 collected tests.
- Source-readiness JSON remains `sources=8 ready=4 blocked=4`, with DS-001, DS-002,
  DS-003, and DS-004 ready by source-rights fields.
- `git diff --check` exited 0 with CRLF-to-LF warnings only for
  `docs/planning_pack/api/openapi_stub.yaml`,
  `docs/planning_pack/registers/data_source_registry.csv`, `state/PROJECT_STATE.md`,
  `state/VALIDATION_LOG.md`, and `state/WORKLOG.md`.
- `docker compose ps` showed no running services, and no worker-run containers remained.

**Residual risk:**

- DS-003 report integration is SSURGO mapunit/component screening only. It does not run
  WSS interpretations/ratings, create pAOI state, or determine septic approval, perc
  results, soil suitability, permitting, buildability, lending, appraisal, or investment
  conclusions.
- The explicit connector-run report-resume endpoint remains a manual one-connector report
  path; operators should use repeated `/report-runs` calls with the same `area_id` when
  they intend to complete the full request-time DS-001, DS-002, DS-004, and DS-003
  sequence.

## 2026-06-05 Level 10 DS-004 request-time orchestration

**Scope:**

- Added shared request-time live connector orchestration for `/intake` and
  `/report-runs`: DS-002 runs first; after DS-002 approval, DS-004 runs for the same
  area; report jobs are created only after both connector review items are approved.
- Added in-memory API regressions proving `/report-runs` and `/intake` can progress
  through DS-002 approval, DS-004 approval, and then produce a report containing both
  `FLOOD_001` and `WETLAND_001`.
- Updated the connector runbook and active Level 10 plan to distinguish the full
  request-time sequence from the manual one-connector report-resume route.
- No DS-003 request-time orchestration, DS-003 claims/reports, autonomous polling,
  new live sources, source-rights changes, or schema migrations were added.

**Commands run:**

```powershell
cd backend; py -3.12 -m pytest -q tests\api\test_fema_nfhl_connector_api.py::test_live_connector_report_run_waits_for_ds004_after_ds002_approval_then_reports tests\api\test_fema_nfhl_connector_api.py::test_live_connector_report_run_pauses_for_connector_review tests\api\test_fema_nfhl_connector_api.py::test_live_connector_intake_pauses_for_connector_review tests\api\test_nwi_connector_api.py::test_approved_nwi_connector_run_feeds_report_without_refetch
cd backend; ruff check app\api\live_connectors.py app\api\reports.py app\api\intake.py tests\api\test_fema_nfhl_connector_api.py
cd backend; py -3.12 -m mypy app\api\live_connectors.py app\api\reports.py app\api\intake.py tests\api\test_fema_nfhl_connector_api.py
cd backend; py -3.12 -m pytest -q tests\api\test_fema_nfhl_connector_api.py tests\api\test_nwi_connector_api.py tests\api\test_intake.py tests\api\test_async_report_runs.py tests\api\test_report_runs_db.py
cd backend; py -3.12 -m pytest -q tests\reports tests\claims_engine\test_rule_engine.py
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
py -3.12 .\scripts\source_readiness.py --priority Must --json
git diff --check
docker compose ps
docker ps -a --filter "name=live-connector-worker-run" --format "{{.Names}} {{.Status}}"
```

**Results:**

- Focused request-time DS-002-to-DS-004 progression tests passed.
- Focused ruff passed for touched API and API regression paths.
- Focused mypy passed for touched API and API regression paths.
- Broader API report/intake connector regression passed with expected DB-smoke skips.
- Reports plus rule-engine regression passed with expected DB-smoke skips.
- Full DB-enabled `.\scripts\verify.ps1` passed: workspace validation ok; backend tests
  passed; ruff passed; canonical mypy passed over 164 source files; migrations/seeds
  applied; DB smoke passed.
- `cd backend; py -3.12 -m pytest --collect-only` reports 596 collected tests.
- Source-readiness JSON remains `sources=8 ready=4 blocked=4`, with DS-001, DS-002,
  DS-003, and DS-004 ready by source-rights fields.
- `git diff --check` exited 0 with CRLF-to-LF warnings only for
  `docs/planning_pack/api/openapi_stub.yaml`,
  `docs/planning_pack/registers/data_source_registry.csv`, `state/PROJECT_STATE.md`,
  `state/VALIDATION_LOG.md`, and `state/WORKLOG.md`.
- `docker compose ps` showed no running services, and no worker-run containers remained.

**Residual risk:**

- The request-time sequence currently covers DS-002 and DS-004 only. DS-003 remains
  immediate/scheduled operator-visible but is not request-time or report-integrated.
- The explicit connector-run report-resume endpoint remains a manual one-connector report
  path; operators should use repeated `/report-runs` calls with the same `area_id` when
  they intend to complete the full request-time DS-002 plus DS-004 sequence.

## 2026-06-05 Level 10 DS-003 USDA SSURGO durable scheduling

**Scope:**

- Added reviewer-authenticated `POST /connector-runs/ssurgo/schedule-bbox`.
- Added DS-003 support to the durable `live_connector_run` job store, including
  in-memory and SQLAlchemy-backed enqueue/leasing paths.
- Added DS-003 worker dispatch in `run_next_live_connector_job(...)`; scheduled jobs
  run the existing DS-003 orchestration with `max_rows` after leasing.
- Updated worker help text, connector runbook language, and the generated OpenAPI stub.
- No DS-003 request-time `/intake` or `/report-runs` orchestration, pAOI state, WSS
  interpretation/rating execution, claims, reports, or final septic/soil-suitability/
  buildability conclusions were added.

**Commands run:**

```powershell
cd backend; py -3.12 -m pytest -q tests\api\test_ssurgo_connector_api.py tests\api\test_live_connector_worker.py
cd backend; ruff check app\connectors\live_jobs.py app\api\live_connector_jobs.py app\api\connectors.py tests\api\test_ssurgo_connector_api.py ..\scripts\live_connector_worker.py
cd backend; py -3.12 -m mypy app\connectors\live_jobs.py app\api\live_connector_jobs.py app\api\connectors.py tests\api\test_ssurgo_connector_api.py ..\scripts\live_connector_worker.py
cd backend; py -3.12 -c "from pathlib import Path; import yaml; from app.main import create_app; Path('../docs/planning_pack/api/openapi_stub.yaml').write_text(yaml.dump(create_app().openapi(), sort_keys=True))"
cd backend; py -3.12 -m pytest -q tests\test_planning_pack_schema_copies.py tests\api\test_ssurgo_connector_api.py tests\api\test_nwi_connector_api.py tests\api\test_fema_nfhl_connector_api.py tests\api\test_live_connector_worker.py
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
py -3.12 .\scripts\source_readiness.py --priority Must --json
git diff --check
docker compose ps
docker ps -a --filter "name=live-connector-worker-run" --format "{{.Names}} {{.Status}}"
```

**Results:**

- Focused DS-003 scheduler plus worker command tests passed: 10 passed, 1 skipped
  as expected for the DB-smoke-gated DS-003 job-store regression.
- DS-002/DS-003/DS-004 API, worker, and OpenAPI parity regression passed: 33 passed,
  5 skipped as expected for DB-smoke-gated cases.
- Focused ruff passed for touched API, job-store, worker, and DS-003 API test paths.
- Focused mypy passed for touched API, job-store, worker, and DS-003 API test paths.
- Full DB-enabled `.\scripts\verify.ps1` passed: workspace validation ok; backend tests
  passed; ruff passed; canonical mypy passed over 164 source files; migrations/seeds
  applied; DB smoke passed.
- `cd backend; py -3.12 -m pytest --collect-only` reports 595 collected tests.
- Source-readiness JSON remains `sources=8 ready=4 blocked=4`, with DS-001, DS-002,
  DS-003, and DS-004 ready by source-rights fields.
- `git diff --check` exited 0 with CRLF-to-LF warnings only for
  `docs/planning_pack/api/openapi_stub.yaml`,
  `docs/planning_pack/registers/data_source_registry.csv`, `state/PROJECT_STATE.md`,
  `state/VALIDATION_LOG.md`, and `state/WORKLOG.md`.
- `docker compose ps` showed no running services, and no worker-run containers remained.

**Residual risk:**

- DS-003 now has immediate and durable queued-worker operator paths, but still has no
  request-time `/intake` or `/report-runs` orchestration and no report/claim
  integration.
- DS-003 remains SSURGO mapunit/component screening only; it does not run WSS
  interpretations, create pAOI state, or assert septic approval, soil suitability,
  engineering, permitting, legal, buildability, lending, appraisal, or investment
  conclusions.

## 2026-06-05 Level 10 DS-003 USDA SSURGO API/operator invocation

**Scope:**

- Added reviewer-authenticated immediate operator invocation at
  `POST /connector-runs/ssurgo/query-bbox`.
- The route requires a registered area, rewrites the request bbox into a bounded
  EPSG:4326 polygon for the connector, invokes DS-003 only, records retrieval
  provenance, persists ledger-safe soil/septic/ag spatial or source-failure evidence,
  and enqueues connector review status through the existing review queue.
- Added a DS-003 fetcher injection seam to `ApiServices` for deterministic tests.
- Regenerated `docs/planning_pack/api/openapi_stub.yaml` from `create_app().openapi()`.
- No DS-003 durable scheduling, worker dispatch, request-time `/intake` or
  `/report-runs` orchestration, pAOI state, WSS interpretation/rating execution,
  claims, reports, or final septic/soil-suitability/buildability conclusions were
  added.

**Commands run:**

```powershell
cd backend; py -3.12 -m pytest -q tests\api\test_ssurgo_connector_api.py tests\connectors\test_ssurgo_connector.py
cd backend; ruff check app\api\connectors.py app\api\live_connectors.py app\api\dependencies.py tests\api\test_ssurgo_connector_api.py tests\connectors\test_ssurgo_connector.py
cd backend; py -3.12 -m mypy app\api\connectors.py app\api\live_connectors.py app\api\dependencies.py tests\api\test_ssurgo_connector_api.py tests\connectors\test_ssurgo_connector.py
cd backend; py -3.12 -c "from pathlib import Path; import yaml; from app.main import create_app; Path('../docs/planning_pack/api/openapi_stub.yaml').write_text(yaml.dump(create_app().openapi(), sort_keys=True))"
cd backend; py -3.12 -m pytest -q tests\test_planning_pack_schema_copies.py tests\api\test_ssurgo_connector_api.py tests\connectors\test_ssurgo_connector.py
cd backend; py -3.12 -m pytest -q tests\api\test_ssurgo_connector_api.py tests\api\test_nwi_connector_api.py tests\api\test_fema_nfhl_connector_api.py
cd backend; ruff check app\api\connectors.py app\api\live_connectors.py app\api\dependencies.py tests\api\test_ssurgo_connector_api.py tests\test_planning_pack_schema_copies.py
cd backend; py -3.12 -m mypy app\api\connectors.py app\api\live_connectors.py app\api\dependencies.py tests\api\test_ssurgo_connector_api.py
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
py -3.12 .\scripts\source_readiness.py --priority Must --json
git diff --check
docker compose ps
docker ps -a --filter "name=live-connector-worker-run" --format "{{.Names}} {{.Status}}"
```

**Results:**

- Focused DS-003 API/connector tests passed: 23 tests.
- Focused ruff passed.
- Focused mypy passed for the touched API and DS-003 API test paths. A direct mypy run
  that included `tests\test_planning_pack_schema_copies.py` reported the existing
  untyped `yaml` import, so the final focused mypy command excludes that parity test
  file while runtime parity remains covered by pytest.
- Planning-pack OpenAPI parity plus DS-003 connector/API regression passed: 25 tests.
- DS-002/DS-003/DS-004 immediate/scheduled API regression passed: 26 passed, 4 skipped
  as expected for DB-smoke-gated cases.
- Full DB-enabled `.\scripts\verify.ps1` passed: workspace validation ok; backend tests
  passed; ruff passed; canonical mypy passed over 164 source files; migrations/seeds
  applied; DB smoke passed.
- `cd backend; py -3.12 -m pytest --collect-only` reports 593 collected tests.
- Source-readiness JSON remains `sources=8 ready=4 blocked=4`, with DS-001, DS-002,
  DS-003, and DS-004 ready by source-rights fields.
- `git diff --check` exited 0 with CRLF-to-LF warnings only for
  `docs/planning_pack/api/openapi_stub.yaml`,
  `docs/planning_pack/registers/data_source_registry.csv`, `state/PROJECT_STATE.md`,
  `state/VALIDATION_LOG.md`, and `state/WORKLOG.md`.
- `docker compose ps` showed no running services, and no worker-run containers remained.

**Residual risk:**

- DS-003 is now operator-visible for immediate reviewer-authenticated runs, but it is
  still not wired into durable live connector scheduling, worker dispatch, request-time
  intake/report-run orchestration, claims, or reports.
- DS-003 still emits SSURGO mapunit/component screening evidence only. It does not run
  WSS interpretations, create pAOI state, or assert septic approval, soil suitability,
  engineering, permitting, legal, buildability, lending, appraisal, or investment
  conclusions.

## 2026-06-05 Level 10 DS-003 USDA SSURGO connector layer

**Scope:**

- Added `backend/app/connectors/ssurgo.py`, a bounded connector-layer-only USDA NRCS
  Soil Data Access / SSURGO integration.
- The connector posts official SDA SQL to `https://SDMDataAccess.sc.egov.usda.gov/Tabular/post.rest`
  with `JSON+COLUMNNAME` output, using the documented
  `SDA_Get_Mukey_from_intersection_with_WktWgs84` function for small EPSG:4326 bboxes.
- Success output is ledger-safe soil/septic/ag screening spatial-intersection evidence
  for SSURGO mapunit/component rows. Empty, errored, or malformed source responses
  become source-failure evidence.
- Added soil mapunit/component payload keys to evidence observed-value validation and
  covered ingestion through the real `EvidenceService`.
- No DS-003 API route, durable scheduler, worker dispatch, request-time orchestration,
  pAOI state, WSS interpretation/rating execution, claims, or reports were added.

**Commands run:**

```powershell
cd backend; py -3.12 -m pytest -q tests\connectors\test_ssurgo_connector.py tests\evidence_ledger\test_payload_validation.py
cd backend; ruff check app\connectors\ssurgo.py app\connectors\__init__.py app\evidence_ledger\payload_validation.py tests\connectors\test_ssurgo_connector.py tests\evidence_ledger\test_payload_validation.py
cd backend; py -3.12 -m mypy app\connectors\ssurgo.py app\connectors\__init__.py app\evidence_ledger\payload_validation.py tests\connectors\test_ssurgo_connector.py tests\evidence_ledger\test_payload_validation.py
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
py -3.12 .\scripts\source_readiness.py --priority Must --json
git diff --check
docker compose ps
docker ps -a --filter "name=live-connector-worker-run" --format "{{.Names}} {{.Status}}"
```

**Results:**

- Focused pytest passed: 43 tests.
- Focused ruff passed after import-order formatting in `backend/app/connectors/__init__.py`.
- Focused mypy passed for the touched connector, export, payload-validation, and test paths.
- Full DB-enabled `.\scripts\verify.ps1` passed: workspace validation ok; backend tests
  passed; ruff passed; canonical mypy passed over 163 source files; migrations/seeds
  applied; DB smoke passed.
- `cd backend; py -3.12 -m pytest --collect-only` reports 589 collected tests.
- Source-readiness JSON remains `sources=8 ready=4 blocked=4`, with DS-001, DS-002,
  DS-003, and DS-004 ready by source-rights fields.
- `git diff --check` exited 0 with CRLF-to-LF warnings only for
  `docs/planning_pack/api/openapi_stub.yaml`,
  `docs/planning_pack/registers/data_source_registry.csv`, and `state/PROJECT_STATE.md`.
- `docker compose ps` showed no running services, and no worker-run containers remained.

**Residual risk:**

- This slice proves source access shape, connector parsing, source-failure behavior, and
  ledger payload compatibility, but it is not yet operator/API-visible.
- It intentionally does not run WSS interpretations or emit septic approval,
  soil-suitability, engineering, permitting, legal, buildability, lending, appraisal, or
  investment conclusions.

## 2026-06-05 Level 10 live connector job status API

**Scope:**

- Added reviewer-authenticated read-only status for durable live connector jobs at
  `GET /connector-runs/live-jobs/{job_id}`.
- The route returns the existing `LiveConnectorJobResponse` projection and does not
  lease jobs, retry/requeue/cancel, fetch live sources, create reports, or mutate queue
  state.
- Added DS-004 scheduler regressions covering queued and finished job reads, missing
  reviewer auth, and unknown-job 404.
- Regenerated `docs/planning_pack/api/openapi_stub.yaml` from `create_app().openapi()`.

**Commands run:**

```powershell
cd backend; py -3.12 -m pytest -q tests\api\test_nwi_connector_api.py tests\api\test_fema_nfhl_connector_api.py tests\api\test_live_connector_worker.py
cd backend; ruff check app\api\connectors.py tests\api\test_nwi_connector_api.py
cd backend; mypy app\api\connectors.py tests\api\test_nwi_connector_api.py
cd backend; py -3.12 -m pytest -q tests\test_planning_pack_schema_copies.py tests\api\test_nwi_connector_api.py tests\api\test_fema_nfhl_connector_api.py tests\api\test_live_connector_worker.py
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
py -3.12 .\scripts\source_readiness.py --priority Must --json
git diff --check
docker compose ps
docker ps -a --filter "name=live-connector-worker-run" --format "{{.Names}} {{.Status}}"
```

**Results:**

- Focused DS-004/DS-002 API plus worker tests passed: 30 passed/skipped as expected.
- Focused ruff passed.
- Focused mypy passed.
- Planning-pack OpenAPI parity plus focused API/worker regression passed:
  32 passed/skipped as expected.
- Full DB-enabled `.\scripts\verify.ps1` passed: workspace validation ok; backend tests
  passed; ruff passed; canonical mypy passed over 161 source files; migrations/seeds
  applied; DB smoke passed.
- `cd backend; py -3.12 -m pytest --collect-only` reports 569 collected tests.
- Source-readiness JSON remains `sources=8 ready=4 blocked=4`, with DS-001, DS-002,
  DS-003, and DS-004 ready by source-rights fields.
- `git diff --check` exited 0 with CRLF-to-LF warnings only for
  `docs/planning_pack/api/openapi_stub.yaml`,
  `docs/planning_pack/registers/data_source_registry.csv`, and `state/PROJECT_STATE.md`.
- `docker compose ps` showed no running services, and no worker-run containers remained.

**Residual risk:**

- This is read-only observability, not a queue dashboard or mutation API. Retry,
  requeue, cancellation, worker supervision, and report scheduling remain outside this
  slice.
- DS-004 remains without request-time `/intake` or `/report-runs` orchestration,
  autonomous polling, or separate fixture corpus.

## 2026-06-05 Level 10 DS-004 National Wetlands Inventory durable scheduler

**Scope:**

- Added explicit reviewer-authenticated DS-004 scheduling at
  `POST /connector-runs/nwi/schedule-bbox`.
- Generalized `backend/app/connectors/live_jobs.py` so durable `live_connector_run`
  jobs support DS-002 FEMA NFHL and DS-004 NWI with separate source ids, connector
  names, bbox validation, and idempotency namespaces.
- Generalized `run_next_live_connector_job(...)` to dispatch leased jobs by
  `source_registry_id` and fail closed for unsupported sources.
- Added focused API/worker tests proving DS-004 scheduling does not fetch NWI or create
  report payloads at schedule time, and the worker later creates the connector review
  item through the existing DS-004 orchestration path.
- Added a DB-smoke-gated store regression proving DS-004 durable payloads persist and
  lease back as `NwiBbox` jobs.
- Regenerated `docs/planning_pack/api/openapi_stub.yaml` from `create_app().openapi()`.

**Commands run:**

```powershell
cd backend; py -3.12 -m pytest -q tests\api\test_nwi_connector_api.py tests\api\test_fema_nfhl_connector_api.py tests\api\test_live_connector_worker.py
cd backend; ruff check app\connectors\live_jobs.py app\api\live_connector_jobs.py app\api\connectors.py app\connectors\__init__.py tests\api\test_nwi_connector_api.py tests\api\test_fema_nfhl_connector_api.py tests\api\test_live_connector_worker.py ..\scripts\live_connector_worker.py
cd backend; mypy app\connectors\live_jobs.py app\api\live_connector_jobs.py app\api\connectors.py app\connectors\__init__.py tests\api\test_nwi_connector_api.py tests\api\test_fema_nfhl_connector_api.py tests\api\test_live_connector_worker.py ..\scripts\live_connector_worker.py
cd backend; py -3.12 -m pytest -q tests\test_planning_pack_schema_copies.py tests\api\test_nwi_connector_api.py tests\api\test_fema_nfhl_connector_api.py tests\api\test_live_connector_worker.py
cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests\api\test_nwi_connector_api.py::test_db_nwi_live_connector_job_store_persists_and_leases_ds004_payload
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
py -3.12 .\scripts\source_readiness.py --priority Must --json
git diff --check
docker compose ps
docker ps -a --filter "name=live-connector-worker-run" --format "{{.Names}} {{.Status}}"
```

**Results:**

- Focused DS-004/DS-002 API plus worker tests passed: 28 passed/skipped as expected
  before OpenAPI regeneration.
- Focused ruff passed.
- Focused mypy passed over 8 checked source/test/script paths.
- Planning-pack OpenAPI parity plus focused API/worker regression passed:
  30 passed/skipped as expected.
- DB-smoke-gated DS-004 live connector job-store regression passed.
- Full DB-enabled `.\scripts\verify.ps1` passed: workspace validation ok; backend tests
  passed; ruff passed; canonical mypy passed over 161 source files; migrations/seeds
  applied; DB smoke passed.
- `cd backend; py -3.12 -m pytest --collect-only` reports 567 collected tests.
- Source-readiness JSON remains `sources=8 ready=4 blocked=4`, with DS-001, DS-002,
  DS-003, and DS-004 ready by source-rights fields.
- `git diff --check` exited 0 with CRLF-to-LF warnings only for
  `docs/planning_pack/api/openapi_stub.yaml`,
  `docs/planning_pack/registers/data_source_registry.csv`, and `state/PROJECT_STATE.md`.
- `docker compose ps` showed no running services, and no worker-run containers remained.

**Residual risk:**

- DS-004 durable scheduling remains operator-triggered only. It is not wired into
  request-time `/intake` or `/report-runs`, autonomous polling, or a separate fixture
  corpus.
- DS-004 report output remains screening-only and cannot be represented as
  jurisdictional wetland/CWA/permit/buildability/legal/lending/appraisal/investment
  advice.
- Empty NWI feature responses remain source-failure evidence, not proof that no mapped
  wetlands/deepwater feature intersects the query area.
- `mapped_wetland_area_sq_m` remains source feature area converted from NWI acres, not a
  clipped parcel-overlap area.

## 2026-06-05 Level 10 DS-004 National Wetlands Inventory API/operator path

**Scope:**

- Added controlled reviewer-authenticated DS-004 NWI operator invocation at
  `POST /connector-runs/nwi/query-bbox`.
- Added DS-004 orchestration in `backend/app/api/live_connectors.py` using the same
  source lookup, retrieval provenance, evidence-ingestion adapter, review packet, review
  status, and connector review queue path as DS-002.
- Added a test fetcher hook on `ApiServices` for deterministic NWI API tests.
- Added focused API tests covering successful spatial evidence persistence, empty
  response source-failure evidence, reviewer auth, missing DS-004 source authority,
  oversized bbox rejection, review queue/status surfacing, and approved connector
  report resume without re-fetching NWI.
- Regenerated `docs/planning_pack/api/openapi_stub.yaml` from `create_app().openapi()`.

**Commands run:**

```powershell
cd backend; py -3.12 -m pytest -q tests\api\test_nwi_connector_api.py tests\connectors\test_nwi_connector.py
cd backend; ruff check app\api\connectors.py app\api\live_connectors.py app\api\dependencies.py tests\api\test_nwi_connector_api.py
cd backend; mypy app\api\connectors.py app\api\live_connectors.py app\api\dependencies.py tests\api\test_nwi_connector_api.py
cd backend; py -3.12 -m pytest -q tests\test_planning_pack_schema_copies.py tests\api\test_fema_nfhl_connector_api.py tests\api\test_nwi_connector_api.py
cd backend; ruff check app\api tests\api\test_nwi_connector_api.py tests\api\test_fema_nfhl_connector_api.py tests\test_planning_pack_schema_copies.py
cd backend; mypy app\api tests\api\test_nwi_connector_api.py tests\api\test_fema_nfhl_connector_api.py tests\test_planning_pack_schema_copies.py
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
py -3.12 .\scripts\source_readiness.py --priority Must --json
git diff --check
docker compose ps
docker ps -a --filter "name=live-connector-worker-run" --format "{{.Names}} {{.Status}}"
```

**Results:**

- Focused DS-004 API plus connector tests passed: 19 passed.
- DS-002/DS-004 API regression plus planning-pack schema/OpenAPI parity passed:
  20 passed, 3 skipped.
- Focused and API-scope ruff passed.
- Focused and API-scope mypy passed.
- Full DB-enabled `.\scripts\verify.ps1` passed: workspace validation ok; backend tests
  passed; ruff passed; canonical mypy passed over 161 source files; migrations/seeds
  applied; DB smoke passed.
- `cd backend; py -3.12 -m pytest --collect-only` reports 565 collected tests.
- Source-readiness JSON remains `sources=8 ready=4 blocked=4`, with DS-001, DS-002,
  DS-003, and DS-004 ready by source-rights fields.
- `git diff --check` exited 0 with CRLF-to-LF warnings only for
  `docs/planning_pack/api/openapi_stub.yaml`,
  `docs/planning_pack/registers/data_source_registry.csv`, and `state/PROJECT_STATE.md`.
- `docker compose ps` showed no running services, and no worker-run containers remained.

**Residual risk:**

- DS-004 is now operator/API and approved-report-resume capable only. It is not wired
  into durable scheduling, the worker profile, request-time `/intake` or `/report-runs`
  orchestration, autonomous polling, or a separate fixture corpus.
- DS-004 report output is limited to the existing screening-only wetlands rule semantics.
  It must not be presented as jurisdictional wetlands, Clean Water Act coverage,
  permitting status, buildability, legal access/title, lending, appraisal, or investment
  advice.
- Empty NWI feature responses remain source-failure evidence, not proof that no mapped
  wetland/deepwater feature intersects the query area.
- `mapped_wetland_area_sq_m` remains source feature area converted from NWI acres, not a
  clipped parcel-overlap area.

## 2026-06-05 Level 10 DS-004 National Wetlands Inventory connector

**Scope:**

- Added `backend/app/connectors/nwi.py` as a bounded connector-layer-only DS-004
  National Wetlands Inventory connector.
- The connector queries the official USFWS-linked Wetlands ArcGIS REST layer 0 with a
  small EPSG:4326 bbox and feature limit, requires source-rights preflight, records
  retrieval provenance, and emits evidence contracts compatible with existing connector
  adapters.
- Usable features produce wetlands spatial-intersection evidence with NWI caveats.
  Empty, errored, malformed, or transfer-limited responses produce source-failure
  evidence instead of an implicit "no wetlands" result.
- Exported the connector through `backend/app/connectors/__init__.py` and added focused
  unit coverage in `backend/tests/connectors/test_nwi_connector.py`.

**Commands run:**

```powershell
cd backend; py -3.12 -m pytest -q tests\connectors\test_nwi_connector.py
cd backend; py -3.12 -m pytest -q tests\connectors\test_nwi_connector.py tests\connectors\test_fema_nfhl_connector.py
cd backend; ruff check app\connectors\nwi.py app\connectors\__init__.py tests\connectors\test_nwi_connector.py
cd backend; ruff check app\connectors tests\connectors\test_nwi_connector.py
cd backend; mypy app\connectors\nwi.py app\connectors\__init__.py tests\connectors\test_nwi_connector.py
cd backend; mypy app\connectors tests\connectors\test_nwi_connector.py
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
py -3.12 .\scripts\source_readiness.py --priority Must --json
git diff --check
docker compose ps
docker ps -a --filter "name=live-connector-worker-run" --format "{{.Names}} {{.Status}}"
```

**Results:**

- Focused DS-004 connector tests passed: 13 passed.
- Focused DS-004 plus DS-002 connector regression passed: 26 passed.
- Focused ruff passed for the touched connector, connector export, and NWI test paths.
- Connector-scope ruff passed for `app\connectors` plus the NWI tests.
- Focused mypy passed for the touched paths; connector-scope mypy passed over 20
  source/test files.
- Full DB-enabled `.\scripts\verify.ps1` passed: workspace validation ok; backend tests
  passed; ruff passed; canonical mypy passed over 160 source files; migrations/seeds
  applied; DB smoke passed.
- `cd backend; py -3.12 -m pytest --collect-only` reports 559 collected tests.
- Source-readiness JSON remains `sources=8 ready=4 blocked=4`, with DS-001, DS-002,
  DS-003, and DS-004 ready by source-rights fields.
- `git diff --check` exited 0 with CRLF-to-LF warnings only for
  `docs/planning_pack/api/openapi_stub.yaml`,
  `docs/planning_pack/registers/data_source_registry.csv`, and `state/PROJECT_STATE.md`.
- `docker compose ps` showed no running services, and no worker-run containers remained.

**Residual risk:**

- This is connector-layer-only. No DS-004 API route, durable scheduler, worker profile
  integration, report resume path, fixtures, request-time orchestration, or report/claim
  generation path was added.
- NWI output remains screening-only and must not be presented as jurisdictional wetlands,
  Clean Water Act coverage, permitting status, buildability, legal access/title, lending,
  appraisal, or investment advice.
- `mapped_wetland_area_sq_m` is source feature area converted from NWI acres, not a clipped
  parcel-overlap area.
- Empty NWI feature responses are source-failure evidence, not proof that no mapped
  wetland/deepwater feature intersects the query area.

## 2026-06-05 Level 10 DS-004 National Wetlands Inventory source review

**Scope:**

- Reviewed DS-004 National Wetlands Inventory against official USFWS/NWI source,
  data download, disclaimer, data limitations, geodatabase caution, and metadata pages.
- Added `docs/source-reviews/ds-004.md` with public official source evidence,
  attribution, biannual update, metadata, project/source-date, imagery, exclusion,
  non-endorsement, and non-jurisdictional caveats.
- Updated `registers/data_source_registry.csv` and the intentionally scoped
  planning-pack registry mirror for DS-004 source identity/caveats.
- Updated `db/seeds/002_seed_source_registry.sql` so re-seeding refreshes DS-004
  first-class source usage-rights fields and source-review metadata.
- Updated source-readiness/source-seed tests to expect DS-001, DS-002, DS-003, and
  DS-004 as source-rights-ready current `Must` sources.

**Commands run:**

```powershell
py -3.12 .\scripts\source_readiness.py --priority Must
cd backend; py -3.12 -m pytest -q tests\source_registry\test_source_readiness.py tests\source_registry\test_source_seeds.py
cd backend; ruff check tests\source_registry\test_source_readiness.py tests\source_registry\test_source_seeds.py ..\db\seeds\source_registry_seeds.py ..\scripts\source_readiness.py
cd backend; mypy tests\source_registry\test_source_readiness.py tests\source_registry\test_source_seeds.py ..\db\seeds\source_registry_seeds.py ..\scripts\source_readiness.py
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
py -3.12 .\scripts\source_readiness.py --priority Must --json
cd backend; py -3.12 -m pytest --collect-only
git diff --check
docker compose ps
docker ps -a --filter "name=live-connector-worker-run" --format "{{.Names}} {{.Status}}"
```

**Results:**

- Source-readiness audit reports `sources=8 ready=4 blocked=4`, with DS-001,
  DS-002, DS-003, and DS-004 ready by source-rights fields.
- Focused source-readiness and source-seed tests passed: 15 passed.
- Focused ruff passed for the touched source-registry tests and scripts.
- Focused mypy passed for the touched source-registry tests and scripts.
- Full DB-enabled `.\scripts\verify.ps1` passed: workspace validation ok; backend tests
  passed; ruff passed; canonical mypy passed over 158 source files; migrations/seeds
  applied; DB smoke passed.
- `cd backend; py -3.12 -m pytest --collect-only` reports 546 collected tests.
- `git diff --check` exited 0 with CRLF-to-LF warnings only for
  `docs/planning_pack/api/openapi_stub.yaml`,
  `docs/planning_pack/registers/data_source_registry.csv`, and
  `state/PROJECT_STATE.md`.
- `docker compose ps` showed no running services, and no worker-run containers remained.

**Residual risk:**

- At source-review closeout, DS-004 was rights-ready only. The later connector entry
  above supersedes only the "no connector" part; DS-004 API, fixtures, and report
  integration still remain outside that source-review slice.
- DS-004 retrieval must still preserve source URL, access date, metadata published date,
  project metadata, imagery/source dates, wetland/deepwater classification codes,
  exclusions, update/currency caveats, and USFWS/NWI attribution.
- DS-004 output must remain screening-only and must not assert jurisdictional wetlands,
  Clean Water Act coverage, permitting status, legal conclusions, buildability,
  appraisal, lending, or investment advice.
- Remaining `Must` sources DS-010, DS-011, DS-017, and DS-023 are still blocked by
  source-readiness fields.

## 2026-06-05 Level 10 DS-003 USDA Web Soil Survey/SSURGO source review

**Scope:**

- Reviewed DS-003 USDA Web Soil Survey/SSURGO against official USDA/NRCS source and
  license pages.
- Added `docs/source-reviews/ds-003.md` with USDA public-domain evidence, WSS/SSURGO
  download/citation evidence, Annual Soils Refresh evidence, and site-specific testing,
  scale, survey-area, and no-legal-conclusion caveats.
- Updated `registers/data_source_registry.csv` and the intentionally scoped
  planning-pack registry mirror for DS-003 source identity/caveats.
- Updated `db/seeds/002_seed_source_registry.sql` so re-seeding refreshes DS-003
  first-class source usage-rights fields and source-review metadata.
- Updated source-readiness/source-seed tests to expect DS-001, DS-002, and DS-003 as
  source-rights-ready current `Must` sources.

**Commands run:**

```powershell
py -3.12 .\scripts\source_readiness.py --priority Must
cd backend; py -3.12 -m pytest -q tests\source_registry\test_source_readiness.py tests\source_registry\test_source_seeds.py
cd backend; ruff check tests\source_registry\test_source_readiness.py tests\source_registry\test_source_seeds.py ..\db\seeds\source_registry_seeds.py ..\scripts\source_readiness.py
cd backend; mypy tests\source_registry\test_source_readiness.py tests\source_registry\test_source_seeds.py ..\db\seeds\source_registry_seeds.py ..\scripts\source_readiness.py
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
py -3.12 .\scripts\source_readiness.py --priority Must --json
cd backend; py -3.12 -m pytest --collect-only
git diff --check
docker compose ps
docker ps -a --filter "name=live-connector-worker-run" --format "{{.Names}} {{.Status}}"
```

**Results:**

- Source-readiness audit reports `sources=8 ready=3 blocked=5`, with DS-001, DS-002,
  and DS-003 ready by source-rights fields.
- Focused source-readiness and source-seed tests passed: 14 passed.
- Focused ruff passed for the touched source-registry tests and scripts.
- Focused mypy passed for the touched source-registry tests and scripts.
- Full DB-enabled `.\scripts\verify.ps1` passed: workspace validation ok; backend tests
  passed; ruff passed; canonical mypy passed over 158 source files; migrations/seeds
  applied; DB smoke passed.
- `cd backend; py -3.12 -m pytest --collect-only` reports 545 collected tests.
- `git diff --check` exited 0 with CRLF-to-LF warnings only for
  `docs/planning_pack/api/openapi_stub.yaml`,
  `docs/planning_pack/registers/data_source_registry.csv`, and
  `state/PROJECT_STATE.md`.
- `docker compose ps` showed no running services, and no worker-run containers remained.

**Residual risk:**

- DS-003 is rights-ready only. No DS-003 live connector, fixtures, connector tests, or
  report integration were added in this slice.
- DS-003 product/layer retrieval must still preserve source metadata, access date,
  survey-area identifiers, refresh/source date, map-unit identifiers, scale caveats, and
  USDA/NRCS citation.
- Remaining `Must` sources DS-004, DS-010, DS-011, DS-017, and DS-023 are still blocked
  by source-readiness fields.

## 2026-06-05 Level 10 DS-001 USGS The National Map source review

**Scope:**

- Reviewed DS-001 USGS The National Map against official USGS source/license pages.
- Added `docs/source-reviews/ds-001.md` with public-domain/open-data evidence,
  attribution, metadata, third-party notice, scale/accuracy, and no-legal-conclusion
  caveats.
- Updated `registers/data_source_registry.csv` and the intentionally scoped planning-pack
  registry mirror for DS-001 source identity/caveats.
- Updated `db/seeds/002_seed_source_registry.sql` so re-seeding refreshes DS-001
  first-class source usage-rights fields and source-review metadata.
- Updated source-readiness/source-seed tests to expect DS-001 and DS-002 as the two
  source-rights-ready current `Must` sources.

**Commands run:**

```powershell
py -3.12 .\scripts\source_readiness.py --priority Must
cd backend; py -3.12 -m pytest -q tests\source_registry\test_source_readiness.py tests\source_registry\test_source_seeds.py
cd backend; ruff check tests\source_registry\test_source_readiness.py tests\source_registry\test_source_seeds.py ..\db\seeds\source_registry_seeds.py ..\scripts\source_readiness.py
cd backend; mypy tests\source_registry\test_source_readiness.py tests\source_registry\test_source_seeds.py ..\db\seeds\source_registry_seeds.py ..\scripts\source_readiness.py
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
py -3.12 .\scripts\source_readiness.py --priority Must --json
cd backend; py -3.12 -m pytest --collect-only
git diff --check
docker compose ps
docker ps -a --filter "name=live-connector-worker-run" --format "{{.Names}} {{.Status}}"
```

**Results:**

- Source-readiness audit reports `sources=8 ready=2 blocked=6`, with DS-001 and
  DS-002 ready by source-rights fields.
- Focused source-readiness and source-seed tests passed: 13 passed.
- Focused ruff passed for the touched source-registry tests and scripts.
- Focused mypy passed for the touched source-registry tests and scripts.
- Full DB-enabled `.\scripts\verify.ps1` passed: workspace validation ok; backend tests
  passed; ruff passed; canonical mypy passed over 158 source files; migrations/seeds
  applied; DB smoke passed.
- `cd backend; py -3.12 -m pytest --collect-only` reports 544 collected tests.
- `git diff --check` exited 0 with CRLF-to-LF warnings only for
  `docs/planning_pack/api/openapi_stub.yaml`,
  `docs/planning_pack/registers/data_source_registry.csv`, and
  `state/PROJECT_STATE.md`.
- `docker compose ps` showed no running services, and no worker-run containers remained.

**Residual risk:**

- DS-001 is rights-ready only. No DS-001 live connector, fixtures, connector tests, or
  report integration were added in this slice.
- DS-001 product/layer retrieval must still preserve source metadata, source date/version
  when available, scale/accuracy caveats, and marked third-party notices.
- Remaining `Must` sources DS-003, DS-004, DS-010, DS-011, DS-017, and DS-023 are still
  blocked by source-readiness fields.

## 2026-06-05 Level 10 supervised live connector worker profile

**Scope:**

- Added explicit polling mode to `scripts/live_connector_worker.py` with
  `--poll-seconds` and `--idle-polls`.
- Preserved one-shot mode as the default worker behavior.
- Added `live-connector-worker` as an opt-in Compose `workers` profile service with
  `restart: unless-stopped`, DB health dependency, shared object-store volume, and
  environment-driven worker settings.
- Updated `backend/Dockerfile` to copy the root worker script into the runtime image.
- The worker profile processes only existing `live_connector_run` jobs and still does
  not enqueue jobs, approve reviews, create reports, or bypass report gating.

**Commands run:**

```powershell
cd backend; py -3.12 -m pytest -q tests\api\test_live_connector_worker.py
cd backend; ruff check tests\api\test_live_connector_worker.py ..\scripts\live_connector_worker.py
cd backend; mypy tests\api\test_live_connector_worker.py ..\scripts\live_connector_worker.py
docker compose --profile workers config
py -3.12 .\scripts\live_connector_worker.py --help
docker compose build backend
docker compose --profile workers run --rm --no-deps --entrypoint python live-connector-worker /app/scripts/live_connector_worker.py --help
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
py -3.12 .\scripts\source_readiness.py --priority Must
git diff --check
docker compose config
docker compose ps
```

**Results:**

- Focused worker tests passed.
- Focused ruff and mypy passed for the worker script and tests.
- `docker compose --profile workers config` rendered the opt-in worker service with the
  expected command, restart policy, DB health dependency, and object-store volume.
- Worker CLI help passed locally and inside the built container image.
- `docker compose build backend` passed and showed
  `COPY scripts/live_connector_worker.py /app/scripts/live_connector_worker.py`.
- Full DB-enabled `.\scripts\verify.ps1` passed: workspace validation ok; backend tests
  passed; ruff passed; canonical mypy passed over 158 source files; migrations/seeds
  applied; DB smoke passed.
- `py -3.12 -m pytest --collect-only` reports 543 collected tests.
- `py -3.12 .\scripts\source_readiness.py --priority Must` still reports
  `sources=8 ready=1 blocked=7`, with DS-002 ready.
- `git diff --check` exited 0 with CRLF-to-LF warnings only for
  `docs/planning_pack/api/openapi_stub.yaml`,
  `docs/planning_pack/registers/data_source_registry.csv`, and
  `state/PROJECT_STATE.md`.
- Default `docker compose config` excludes the profiled worker service; profile config
  includes it.
- `docker compose ps` showed no running services, and no worker-run containers remained
  after the container help smoke.

**Residual risk:**

- The worker profile is opt-in and still requires operators to start the `workers`
  profile.
- Live DS-002 execution still depends on the same source-readiness, review approval, DB,
  and live FEMA behavior already documented for the connector path.
- Non-DS-002 source reviews remain blocked by usage-rights/source-readiness work.

## 2026-06-05 Level 10 bounded live connector worker command

**Scope:**

- Added `scripts/live_connector_worker.py` as a supervisor-callable command for queued
  `live_connector_run` jobs.
- The command opens fresh DB-backed services per processed job, calls
  `run_next_live_connector_job(...)`, commits succeeded and failed job state, and exits
  after one job by default.
- The command emits compact text or JSON summaries, exits `0` for idle/success, and exits
  `1` for a processed failed job.
- The command does not enqueue jobs, call schedule routes, create reports, approve
  connector review items, or bypass report gating.

**Commands run:**

```powershell
cd backend; py -3.12 -m pytest -q tests\api\test_live_connector_worker.py tests\api\test_fema_nfhl_connector_api.py
cd backend; ruff check app\api\live_connector_jobs.py tests\api\test_live_connector_worker.py ..\scripts\live_connector_worker.py
cd backend; mypy app\api\live_connector_jobs.py tests\api\test_live_connector_worker.py ..\scripts\live_connector_worker.py
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
py -3.12 .\scripts\source_readiness.py --priority Must
git diff --check
py -3.12 .\scripts\live_connector_worker.py --help
docker compose ps
```

**Results:**

- Focused worker plus DS-002 API tests passed with DB-gated tests skipped outside DB
  smoke.
- Focused ruff passed for the worker command, worker helper, and new worker tests.
- Focused mypy passed for the worker command, worker helper, and new worker tests.
- Full DB-enabled `.\scripts\verify.ps1` passed: workspace validation ok; backend tests
  passed; ruff passed; canonical mypy passed over 158 source files; migrations/seeds
  applied; DB smoke passed.
- `py -3.12 -m pytest --collect-only` reports 541 collected tests.
- `py -3.12 .\scripts\source_readiness.py --priority Must` still reports
  `sources=8 ready=1 blocked=7`, with DS-002 ready.
- `git diff --check` exited 0 with CRLF-to-LF warnings only for
  `docs/planning_pack/api/openapi_stub.yaml` and
  `docs/planning_pack/registers/data_source_registry.csv`.
- `py -3.12 .\scripts\live_connector_worker.py --help` exits 0 and documents
  `--worker-id`, `--max-jobs`, `--object-store-root`, and `--json`.
- `docker compose ps` showed no running services after verification.

**Residual risk:**

- This is a bounded worker command, not an autostarted or supervised daemon process.
- Real DB execution still depends on the same migrated Postgres database, DS-002 source
  readiness, and live FEMA behavior already documented for the DS-002 connector path.
- Remaining non-DS-002 `Must` sources are still blocked by source readiness and usage
  rights review.

## 2026-06-05 Level 10 explicit DS-002 live connector scheduling

**Scope:**

- Added durable `live_connector_run` jobs backed by existing `jobs.job_queue`.
- Added reviewer-authenticated `POST /connector-runs/fema-nfhl/schedule-bbox`.
- Added `run_next_live_connector_job(...)` worker helper that leases one queued job,
  runs the existing bounded DS-002 orchestration, persists provenance/evidence, and
  enqueues the normal connector review item.
- Scheduling does not call FEMA, persist evidence, create claims, or create report jobs.
- Report creation remains gated on connector review approval and the existing
  post-approval connector report-resume route.

**Commands run:**

```powershell
cd backend; py -3.12 -m pytest -q tests\api\test_fema_nfhl_connector_api.py tests\api\test_connector_review_actions.py tests\api\test_connector_review_status.py
cd backend; ruff check app\connectors\live_jobs.py app\api\live_connector_jobs.py app\api\connectors.py app\api\dependencies.py tests\api\test_fema_nfhl_connector_api.py
cd backend; mypy app\connectors\live_jobs.py app\api\live_connector_jobs.py app\api\connectors.py app\api\dependencies.py tests\api\test_fema_nfhl_connector_api.py
cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests\api\test_fema_nfhl_connector_api.py::test_db_live_connector_scheduler_enqueues_and_runs_without_report_job tests\api\test_fema_nfhl_connector_api.py::test_db_live_connector_report_run_waits_for_approval_then_reports
cd backend; py -3.12 -m pytest -q tests\test_planning_pack_schema_copies.py tests\api\test_fema_nfhl_connector_api.py tests\api\test_connector_review_actions.py tests\api\test_connector_review_status.py tests\api\test_connector_review_queue_db.py
cd backend; ruff check app\connectors\live_jobs.py app\api\live_connector_jobs.py app\api\connectors.py app\api\dependencies.py tests\api\test_fema_nfhl_connector_api.py tests\test_planning_pack_schema_copies.py
cd backend; mypy app\connectors\live_jobs.py app\api\live_connector_jobs.py app\api\connectors.py app\api\dependencies.py tests\api\test_fema_nfhl_connector_api.py tests\test_planning_pack_schema_copies.py
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
git diff --check
py -3.12 .\scripts\source_readiness.py --priority Must
docker compose ps
```

**Results:**

- Focused DS-002/review API tests passed with DB-gated tests skipped outside DB smoke.
- Focused ruff and mypy passed for the new scheduler store, worker helper, API wiring,
  and tests.
- DB-gated scheduler regression passed, proving `schedule-bbox` enqueues without fetching
  or creating report jobs, and `run_next_live_connector_job(...)` creates the connector
  review item after worker execution.
- Planning-pack OpenAPI parity passed after regenerating
  `docs/planning_pack/api/openapi_stub.yaml`.
- Full DB-enabled `.\scripts\verify.ps1` passed: workspace validation ok; backend tests
  passed; ruff passed; canonical mypy passed over 157 source files; migrations/seeds
  applied; DB smoke passed.
- `py -3.12 -m pytest --collect-only` reports 538 collected tests.
- `py -3.12 .\scripts\source_readiness.py --priority Must` still reports
  `sources=8 ready=1 blocked=7`, with DS-002 ready.
- `git diff --check` exited 0 with CRLF-to-LF warnings only for
  `docs/planning_pack/api/openapi_stub.yaml` and
  `docs/planning_pack/registers/data_source_registry.csv`.
- `docker compose ps` showed no running services after verification.

**Residual risk:**

- This is an explicit durable queue/worker path, not an autonomous supervised daemon.
- The scheduler is bounded to DS-002; other `Must` sources remain blocked by source
  readiness and license/usage-right fields.
- Report creation remains operator-driven after connector review approval.

## 2026-06-05 Level 10 connector reviewer action-history gate

**Scope:**

- Connector review queue payloads now append reviewer action history for approve/fix,
  requeue, and cancel actions.
- `review_decision` remains the latest approve/fix decision used by report gating.
- `review_action_history` preserves the reviewer action sequence, reviewer id, reason,
  and timestamp in both in-memory and SQLAlchemy-backed queue implementations.
- No DB migration or separate audit-event auth ledger was added.

**Commands run:**

```powershell
cd backend; py -3.12 -m pytest -q tests\connectors\test_review_queue.py tests\api\test_connector_review_actions.py tests\api\test_connector_review_status.py
cd backend; ruff check app\connectors\review_queue.py app\api\connectors.py tests\connectors\test_review_queue.py tests\api\test_connector_review_actions.py
cd backend; mypy app\connectors\review_queue.py app\api\connectors.py tests\connectors\test_review_queue.py tests\api\test_connector_review_actions.py
cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests\connectors\test_review_queue.py
cd backend; py -3.12 -m pytest -q tests\connectors\test_review_queue.py tests\api\test_connector_review_actions.py tests\api\test_connector_review_status.py tests\api\test_connector_review_queue_db.py tests\api\test_fema_nfhl_connector_api.py tests\api\test_async_report_runs.py tests\api\test_report_runs_db.py
cd backend; py -3.12 -m pytest --collect-only -q
git diff --check
py -3.12 .\scripts\source_readiness.py --priority Must
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
docker compose ps
```

**Results:**

- Focused review queue/action/status tests passed: 29 passed, 5 DB-gated tests skipped
  outside DB smoke.
- Focused ruff passed for the touched connector/API/test files.
- Focused mypy passed for 4 source/test files.
- DB-enabled review queue tests passed: 13 passed.
- Adjacent connector/review/report API tests passed with DB-gated tests skipped where
  `RUN_DB_SMOKE` was not enabled.
- One broadened pytest command initially referenced stale nonexistent
  `tests\api\test_connector_report_runs.py`; the corrected command used the live report
  API test files and passed.
- Full DB-enabled `.\scripts\verify.ps1` passed: workspace validation ok; backend tests
  passed; ruff passed; canonical mypy passed over 155 source files; migrations/seeds
  applied; DB smoke passed.
- `py -3.12 -m pytest --collect-only -q` reports 536 collected tests.
- `py -3.12 .\scripts\source_readiness.py --priority Must` still reports
  `sources=8 ready=1 blocked=7`, with DS-002 ready.
- `git diff --check` exited 0 with CRLF-to-LF warnings only for
  `docs/planning_pack/api/openapi_stub.yaml` and
  `docs/planning_pack/registers/data_source_registry.csv`.
- `docker compose ps` showed no running services after verification.

**Residual risk:**

- This is durable queue-payload history, not a separate audit-event auth ledger.
- This is still operator-driven connector review and report resume, not a background
  connector scheduler.
- Remaining `Must` sources other than DS-002 are still blocked by source-readiness
  fields.

## 2026-06-05 Level 10 connector report-resume gate

**Scope:**

- Connector review packets and queue payloads now carry the originating `area_id` derived
  from connector evidence inputs.
- Added reviewer-authenticated `POST /connector-runs/{ingest_run_id}/report-runs`.
- The resume route creates a normal async report job only when the connector review queue
  item is `SUCCEEDED` with latest `review_decision.action` equal to
  `approve_for_connector_qa`.
- The route requires only `intent_code`, derives the report area from stored connector
  queue metadata, fails closed on missing/invalid area metadata or unapproved review, and
  does not re-fetch DS-002/FEMA NFHL.
- Planning-pack OpenAPI refreshed for the new route and connector review `area_id` field.

**Commands run:**

```powershell
cd backend; py -3.12 -m pytest -q tests\connectors\test_review_packet.py tests\connectors\test_review_handoff.py tests\connectors\test_review_queue.py tests\api\test_connector_review_status.py tests\api\test_fema_nfhl_connector_api.py
cd backend; ruff check app\api\connectors.py app\connectors\review_packet.py app\connectors\review_handoff.py app\connectors\review_queue.py tests\api\test_fema_nfhl_connector_api.py tests\api\test_connector_review_status.py tests\connectors\test_review_packet.py tests\connectors\test_review_handoff.py tests\connectors\test_review_queue.py
cd backend; mypy app\api\connectors.py app\connectors\review_packet.py app\connectors\review_handoff.py app\connectors\review_queue.py tests\api\test_fema_nfhl_connector_api.py tests\api\test_connector_review_status.py tests\connectors\test_review_packet.py tests\connectors\test_review_handoff.py tests\connectors\test_review_queue.py
cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests\api\test_fema_nfhl_connector_api.py::test_db_live_connector_report_run_waits_for_approval_then_reports
cd backend; py -3.12 -m pytest -q tests\test_planning_pack_schema_copies.py tests\api\test_fema_nfhl_connector_api.py tests\api\test_connector_review_actions.py tests\api\test_connector_review_status.py tests\connectors\test_review_packet.py tests\connectors\test_review_handoff.py tests\connectors\test_review_queue.py
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
git diff --check
py -3.12 .\scripts\source_readiness.py --priority Must
docker compose ps
```

**Results:**

- Focused connector/API tests passed, including in-memory pre-approval rejection and
  post-approval resume without a second FEMA fetch.
- DB-backed test passed, proving no report job is inserted before approval and the
  post-approval connector-run resume route creates a report with `FLOOD_001` and matching
  connector `source_ingest_run_id`.
- Focused ruff and mypy passed for the touched connector, API, and test files.
- Planning-pack OpenAPI parity passed after regeneration.
- Full DB-enabled `.\scripts\verify.ps1` passed: workspace validation ok; backend tests
  passed; ruff passed; canonical mypy passed over 155 source files; migrations/seeds
  applied; DB smoke passed.
- `py -3.12 -m pytest --collect-only` reports 534 collected tests.
- `py -3.12 .\scripts\source_readiness.py --priority Must` still reports
  `sources=8 ready=1 blocked=7`, with DS-002 ready.
- `git diff --check` exited 0 with CRLF-to-LF warnings only for
  `docs/planning_pack/api/openapi_stub.yaml` and
  `docs/planning_pack/registers/data_source_registry.csv`.
- `docker compose ps` showed no running services after verification.

**Residual risk:**

- This is still operator-driven report resume, not a background connector scheduler.
- The connector review queue still stores the latest reviewer decision, not a durable
  append-only reviewer action history.
- Existing queued connector review items created before this metadata slice may lack
  `area_id` and will fail closed on the resume endpoint.
- Remaining `Must` sources other than DS-002 are still blocked by source-readiness fields.

## 2026-06-05 Level 10 request-time DS-002 orchestration gate

**Scope:**

- Shared DS-002 FEMA NFHL orchestration helper for manual route, `/intake`, and
  `/report-runs`.
- Default-off request-time live connector orchestration behind `ENABLE_LIVE_CONNECTORS`.
- `/intake` and `/report-runs` invoke bounded DS-002 when live connectors are enabled,
  persist provenance/evidence/review queue state, and return `pending_connector_review`
  instead of scheduling report generation while connector evidence is unapproved.
- After `approve_for_connector_qa`, calling `/report-runs` again continues to normal
  report job creation and the approved connector-lineage evidence can contribute to
  report claims.
- Planning-pack OpenAPI refreshed for nullable report ids and connector-review response
  fields.

**Commands run:**

```powershell
cd backend; py -3.12 -m pytest -q tests\api\test_fema_nfhl_connector_api.py
cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests\api\test_fema_nfhl_connector_api.py::test_db_live_connector_report_run_waits_for_approval_then_reports
cd backend; ruff check app\api\live_connectors.py app\api\connectors.py app\api\reports.py app\api\intake.py tests\api\test_fema_nfhl_connector_api.py
cd backend; mypy app\api\live_connectors.py app\api\connectors.py app\api\reports.py app\api\intake.py tests\api\test_fema_nfhl_connector_api.py
cd backend; py -3.12 -m pytest -q tests\api\test_fema_nfhl_connector_api.py tests\api\test_async_report_runs.py tests\api\test_intake.py tests\test_planning_pack_schema_copies.py
cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests\api\test_fema_nfhl_connector_api.py::test_db_live_connector_report_run_waits_for_approval_then_reports tests\api\test_fema_nfhl_connector_api.py::test_db_fema_nfhl_approval_feeds_report_api
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
git diff --check
py -3.12 .\scripts\source_readiness.py --priority Must
docker compose ps
```

**Results:**

- Automatic DS-002 request-time orchestration is implemented only when
  `ENABLE_LIVE_CONNECTORS=true`; default local behavior remains unchanged.
- In-memory tests prove `/report-runs` and `/intake` return
  `pending_connector_review` with connector review ids instead of creating a report
  while DS-002 evidence is unapproved.
- In-memory and DB-backed tests prove `/report-runs` continues to normal queued report
  generation after the connector review item is approved for connector QA.
- DB-backed test proves no `report_run` job is inserted before DS-002 approval, then
  proves the post-approval report includes `FLOOD_001` and the matching
  `source_ingest_run_id`.
- Focused ruff and mypy passed for the touched API and test surfaces.
- Full DB-enabled `.\scripts\verify.ps1` passed: workspace validation ok; backend tests
  passed; ruff passed; canonical mypy passed over 155 source files; migrations/seeds
  applied; DB smoke passed.
- `py -3.12 -m pytest --collect-only` reports 532 collected tests.
- `py -3.12 .\scripts\source_readiness.py --priority Must` still reports
  `sources=8 ready=1 blocked=7`, with DS-002 ready.
- `git diff --check` exited 0 with CRLF-to-LF warnings only for
  `docs/planning_pack/api/openapi_stub.yaml` and
  `docs/planning_pack/registers/data_source_registry.csv`.
- `docker compose ps` showed no running services after verification.

**Residual risk:**

- This is request-time orchestration, not a background connector scheduler.
- Operators must still approve the connector review item and call `/report-runs` again
  to create the report after approval.
- The connector review queue still stores latest reviewer decision state, not a
  durable action-history ledger.
- Remaining `Must` sources other than DS-002 are still blocked by source-readiness
  fields.

## 2026-06-05 Level 10 DB-backed DS-002 approval-to-report regression

**Scope:**

- DB-backed FastAPI regression for the manual DS-002 operator sequence:
  register area, query FEMA NFHL bbox, approve connector review item, create report,
  and retrieve report evidence/claim output.
- SQLAlchemy source repository hardening for stale local seed rows with placeholder
  homepage URLs such as `TBD`.
- FEMA NFHL success evidence now emits an ISO source date compatible with the
  evidence DB `date` column while preserving the access timestamp through
  `observed_at` and retrieval metrics.
- Test-local DS-002 snapshot/refresh/restore lets the DB regression run against
  canonical reviewed DS-002 source-use state without leaving that source row mutated.

**Commands run:**

```powershell
cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests\api\test_fema_nfhl_connector_api.py::test_db_fema_nfhl_approval_feeds_report_api
cd backend; py -3.12 -m pytest -q tests\connectors\test_fema_nfhl_connector.py::test_success_query_builds_bounded_fema_request_and_evidence
cd backend; py -3.12 -m pytest -q tests\api\test_fema_nfhl_connector_api.py tests\source_registry\test_sqlalchemy_source_repo.py tests\connectors\test_fema_nfhl_connector.py tests\evidence_ledger\test_sqlalchemy_evidence_repo.py
cd backend; ruff check app\source_registry\source_repo.py app\connectors\fema_nfhl.py tests\source_registry\test_sqlalchemy_source_repo.py tests\api\test_fema_nfhl_connector_api.py tests\connectors\test_fema_nfhl_connector.py app\api app\reports
cd backend; mypy app\source_registry\source_repo.py app\connectors\fema_nfhl.py tests\source_registry\test_sqlalchemy_source_repo.py tests\api\test_fema_nfhl_connector_api.py tests\connectors\test_fema_nfhl_connector.py app\api app\reports
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
git diff --check
py -3.12 .\scripts\source_readiness.py --priority Must
docker compose ps
```

**Results:**

- DB-backed DS-002 operator regression passed. The API path persisted the connector
  retrieval, connector-lineage evidence, review queue approval, report run, and
  report output with `FLOOD_001` plus the matching `source_ingest_run_id`.
- SQLAlchemy source repository now normalizes invalid placeholder homepage URLs to
  `None` and preserves the raw placeholder in source metadata as `raw_url`.
- FEMA NFHL success evidence now uses `observed_at.date().isoformat()` for
  `source_date`; the access timestamp remains available from `observed_at` and
  retrieval metrics.
- Focused tests, ruff, and mypy passed for the touched API, connector, source
  repository, evidence, report, and test surfaces.
- Full DB-enabled `.\scripts\verify.ps1` passed: workspace validation ok; 528 backend
  tests passed; ruff passed; canonical mypy passed over 154 source files;
  migrations/seeds applied; DB smoke passed.
- `py -3.12 -m pytest --collect-only` reports 528 collected tests.
- `py -3.12 .\scripts\source_readiness.py --priority Must` still reports
  `sources=8 ready=1 blocked=7`, with DS-002 ready.
- `git diff --check` exited 0 with CRLF-to-LF warnings only for
  `docs/planning_pack/api/openapi_stub.yaml` and
  `docs/planning_pack/registers/data_source_registry.csv`.
- `docker compose ps` showed no running services after verification.

**Residual risk:**

- The approved DS-002 path is still manually operator-driven. Automatic DS-002
  scheduling, intake integration, or report-run orchestration remains open.
- The connector review queue still stores latest reviewer decision state, not a
  durable action-history ledger.
- Remaining `Must` sources other than DS-002 are still blocked by source-readiness
  fields.

## 2026-06-05 Level 10 approved connector evidence report gate

**Scope:**

- `EvidenceContract.source_ingest_run_id` lineage for connector-produced evidence.
- SQLAlchemy evidence metadata persistence and round-trip for connector run lineage.
- DS-002 FEMA NFHL connector stamps successful spatial evidence and source-failure
  evidence with the retrieval run id.
- Report generation excludes connector-lineage evidence unless the matching connector
  review queue item is `SUCCEEDED` with latest `review_decision.action` equal to
  `approve_for_connector_qa`.
- Evidence schema and planning-pack schema/OpenAPI copies refreshed for lineage.
- API-level manual operator sequence from DS-002 query through reviewer approval to report
  retrieval.
- ADR `docs/adr/lane-d-0020-approved-connector-evidence-report-gate.md` records the
  report eligibility boundary.

**Commands run:**

```powershell
cd backend; py -3.12 -m pytest -q tests\evidence_ledger\test_evidence_schema_contract.py tests\evidence_ledger\test_sqlalchemy_evidence_repo.py tests\connectors\test_fema_nfhl_connector.py tests\reports\test_report_service.py
cd backend; ruff check app\domain\evidence_contracts.py app\evidence_ledger app\connectors app\reports tests\evidence_ledger tests\connectors tests\reports
cd backend; mypy app\domain\evidence_contracts.py app\evidence_ledger app\connectors app\reports tests\evidence_ledger tests\connectors tests\reports
cd backend; mypy app\domain\evidence_contracts.py app\evidence_ledger app\connectors app\reports app\api tests\evidence_ledger tests\connectors tests\reports tests\api
cd backend; py -3.12 -m pytest -q tests\reports\test_report_service.py tests\api\test_connector_review_actions.py
cd backend; py -3.12 -m pytest -q tests\api\test_fema_nfhl_connector_api.py
cd backend; ruff check tests\api\test_fema_nfhl_connector_api.py app\api app\reports
cd backend; mypy tests\api\test_fema_nfhl_connector_api.py app\api app\reports
cd backend; py -3.12 -m pytest -q tests\test_planning_pack_schema_copies.py::test_planning_pack_evidence_and_claim_schemas_match_root_contract_schemas
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
git diff --check
py -3.12 .\scripts\source_readiness.py --priority Must
docker compose ps
```

**Results:**

- Focused evidence schema, SQLAlchemy evidence repository, FEMA connector, and report
  service tests passed. DB-specific SQLAlchemy cases are covered by the full
  `RUN_DB_SMOKE=1` gate.
- Focused ruff and mypy passed for touched evidence, connector, report, API, and test
  surfaces.
- Planning-pack evidence schema parity passed after refreshing the copied schema.
- API-level DS-002 operator regression passed: connector run, approval action, report
  creation, and report retrieval returned `FLOOD_001` with connector evidence lineage.
- Full DB-enabled `.\scripts\verify.ps1` passed: workspace validation ok; backend tests
  passed; ruff passed; canonical mypy passed over 154 source files; migrations/seeds
  applied; DB smoke passed.
- `py -3.12 -m pytest --collect-only` reports 526 collected tests.
- `py -3.12 .\scripts\source_readiness.py --priority Must` still reports
  `sources=8 ready=1 blocked=7`, with DS-002 ready.
- `git diff --check` exited 0 with CRLF-to-LF warnings only for
  `docs/planning_pack/api/openapi_stub.yaml` and
  `docs/planning_pack/registers/data_source_registry.csv`.
- `docker compose ps` showed no running services after verification.

**Residual risk:**

- The connector review queue stores the latest reviewer decision, not a durable
  action-history ledger.
- Report generation is gated for already persisted connector evidence, but there is still
  no automatic live DS-002 scheduler or `/intake`/`/report-runs` orchestration.
- Remaining `Must` sources other than DS-002 are still blocked by source-readiness fields.

## 2026-06-05 Level 10 connector review closeout actions

**Scope:**

- Real queue-state mutation for connector review closeout.
- `approve_for_connector_qa` route and repository transition.
- `request_fixture_fix` route now fails review items with a required reason instead of
  returning a non-mutating acknowledgement.
- `requeue_after_fix` and `cancel_review` now require non-empty reasons.
- Latest reviewer decision is recorded in the connector review queue payload.
- No mutation of source retrieval provenance, evidence observations, claims, reports,
  schemas, connector runtime behavior, or live source data.

**Commands run:**

```powershell
cd backend; py -3.12 -m pytest -q tests\api\test_connector_review_actions.py tests\connectors\test_review_queue.py
cd backend; ruff check app\api\connectors.py app\connectors\review_queue.py tests\api\test_connector_review_actions.py tests\connectors\test_review_queue.py
cd backend; mypy app\api\connectors.py app\connectors\review_queue.py tests\api\test_connector_review_actions.py tests\connectors\test_review_queue.py
cd backend; py -3.12 -m pytest -q tests\api\test_connector_review_actions.py tests\api\test_connector_review_status.py tests\api\test_fema_nfhl_connector_api.py tests\connectors\test_review_queue.py tests\test_planning_pack_schema_copies.py
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
git diff --check
py -3.12 .\scripts\source_readiness.py --priority Must
docker compose ps
```

**Results:**

- Added `approve_for_connector_qa` and `request_fixture_fix` closeout transitions to
  in-memory and SQLAlchemy connector review queue repositories.
- Added `docs/adr/lane-d-0019-connector-review-closeout-api.md` to record the queue-only
  closeout decision boundary.
- Updated review action API responses to include the updated queue item.
- `request_fixture_fix`, `requeue_after_fix`, and `cancel_review` now fail closed with
  `422` on missing/blank reasons.
- Focused review action and queue tests passed with DB-specific cases skipped outside
  `RUN_DB_SMOKE=1`.
- Focused ruff and mypy passed for touched API, queue, and test files.
- Broader connector review, DS-002 API, and OpenAPI parity tests passed.
- Full DB-enabled `.\scripts\verify.ps1` passed: workspace validation ok; backend tests
  passed; ruff passed; canonical mypy passed over 154 source files; migrations/seeds
  applied; DB smoke passed.
- `py -3.12 -m pytest --collect-only` reports 523 collected tests.
- `py -3.12 .\scripts\source_readiness.py --priority Must` still reports
  `sources=8 ready=1 blocked=7`.
- `git diff --check` exited 0 with CRLF-to-LF warnings only for
  `docs/planning_pack/api/openapi_stub.yaml` and
  `docs/planning_pack/registers/data_source_registry.csv`.
- `docker compose ps` showed no services running after verification.

**Residual risk:**

- The queue item stores the latest reviewer decision, not a durable action-history ledger.
- Approved connector review state is not yet consumed by report generation.
- There is still no scheduler or automatic `/intake` invocation for live DS-002 runs.

## 2026-06-05 Level 10 DS-002 FEMA NFHL controlled API invocation

**Scope:**

- Reviewer-authenticated `POST /connector-runs/fema-nfhl/query-bbox`.
- DS-002-only source lookup and connector source-use preflight.
- Registered-area requirement and bbox/max-feature validation.
- Retrieval provenance recording through the existing connector adapter.
- Ledger-safe spatial or source-failure evidence persistence through the existing
  evidence-ingestion adapter.
- Connector review status build and review-queue enqueue without claims, reports,
  scheduler jobs, or `/intake` shortcuts.
- Planning-pack OpenAPI regeneration from the live FastAPI contract.

**Commands run:**

```powershell
cd backend; py -3.12 -m pytest -q tests\api\test_fema_nfhl_connector_api.py tests\connectors\test_fema_nfhl_connector.py
cd backend; ruff check app\api\connectors.py app\api\dependencies.py app\connectors\review_packet.py app\connectors\__init__.py app\connectors\fema_nfhl.py tests\api\test_fema_nfhl_connector_api.py tests\connectors\test_fema_nfhl_connector.py
cd backend; mypy app\api\connectors.py app\api\dependencies.py app\connectors\review_packet.py app\connectors\__init__.py app\connectors\fema_nfhl.py tests\api\test_fema_nfhl_connector_api.py tests\connectors\test_fema_nfhl_connector.py
cd backend; py -3.12 -m pytest -q tests\api tests\connectors tests\source_registry
cd backend; ruff check app\api app\connectors tests\api tests\connectors tests\source_registry
cd backend; mypy app\api app\connectors tests\api tests\connectors tests\source_registry
cd backend; py -3.12 -m pytest -q tests\test_planning_pack_schema_copies.py::test_planning_pack_openapi_stub_matches_generated_fastapi_contract
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
.\scripts\agent-context-check.ps1
py -3.12 .\scripts\source_readiness.py --priority Must
git diff --check
docker compose ps
```

**Results:**

- Added `backend/tests/api/test_fema_nfhl_connector_api.py`.
- Updated `backend/app/api/connectors.py` with controlled DS-002 invocation route.
- Updated `backend/app/api/dependencies.py` so API services expose source provenance
  service wiring and an injectable FEMA NFHL JSON fetcher for deterministic tests.
- Generalized connector review packet input typing so live and fixture connector
  workflows share the same review status path.
- Adjusted `FemaNfhlConnector` evidence output to match canonical evidence-ledger
  observed-value keys while retaining source transport details in retrieval metrics.
- Focused DS-002 API plus connector tests passed: 18 passed.
- Broader API/connectors/source-registry tests passed with existing skips.
- Ruff passed for the focused changed surface and broader API/connectors/source-registry
  surface.
- Mypy passed for the focused changed surface and for 73 API/connectors/source-registry
  source files.
- Planning-pack OpenAPI parity test passed after regenerating
  `docs/planning_pack/api/openapi_stub.yaml` from `create_app().openapi()`.
- Full DB-enabled `.\scripts\verify.ps1` passed: workspace validation ok; backend tests
  passed; ruff passed; canonical mypy passed over 154 source files; migrations/seeds
  applied; DB smoke passed.
- `py -3.12 -m pytest --collect-only` reports 518 collected tests.
- `.\scripts\agent-context-check.ps1` reports `agent context check: ok`.
- `py -3.12 .\scripts\source_readiness.py --priority Must` reports
  `sources=8 ready=1 blocked=7`.
- `git diff --check` exited 0 with CRLF-to-LF warnings only for
  `docs/planning_pack/api/openapi_stub.yaml` and
  `docs/planning_pack/registers/data_source_registry.csv`.
- `docker compose ps` showed no services running after verification.

**Residual risk:**

- The route does not create claims or reports; DS-002 evidence must still be reviewed and
  integrated into report generation in a later slice.
- There is no scheduler, worker, or automatic `/intake` trigger for the live connector.
- Manual-review action semantics for accepting/rejecting live connector runs remain a
  next-step workflow gap.
- Deterministic tests cover successful spatial evidence and source-failure persistence.
  The prior live validate-only FEMA smoke in this environment exercised the transfer-limit
  source-failure path, not a successful live spatial-evidence response.

## 2026-06-05 Level 10 DS-002 FEMA NFHL bounded live connector

**Scope:**

- Bounded DS-002-only FEMA NFHL effective-data connector.
- ArcGIS REST layer 28 (`Flood Hazard Zones`) query construction.
- EPSG:4326 bounding-box and feature-count limits.
- Spatial-intersection evidence for usable flood hazard features.
- Source-failure evidence for no-data, service error, malformed feature, request error,
  and FEMA transfer-limit cases.
- Adapter compatibility with existing connector retrieval-provenance and evidence-ingestion
  ports.
- Connector runbook, plan, project-state, and worklog updates.

**Commands run:**

```powershell
cd backend; py -3.12 -m pytest -q tests\connectors\test_fema_nfhl_connector.py
cd backend; py -3.12 -m pytest -q tests\connectors\test_fema_nfhl_connector.py tests\connectors\test_evidence_ingestion_adapter.py tests\connectors\test_retrieval_provenance_adapter.py tests\connectors\test_fixture_workflow.py
cd backend; py -3.12 -m pytest -q tests\connectors tests\source_registry
cd backend; ruff check app\connectors tests\connectors tests\source_registry
cd backend; mypy app\connectors tests\connectors tests\source_registry
cd backend; @'
# Validate-only live smoke: instantiate FemaNfhlConnector with DS-002 rights and query
# a small bbox with max_features=1. No persistence, seeding, or artifact generation.
'@ | py -3.12 -
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
.\scripts\agent-context-check.ps1
py -3.12 .\scripts\source_readiness.py --priority Must
git diff --check
docker compose ps
```

**Results:**

- Added `backend/app/connectors/fema_nfhl.py`.
- Added `backend/app/connectors/result.py` so fixture and live connector results can both
  use the existing retrieval-provenance and evidence-ingestion adapters.
- Added `backend/tests/connectors/test_fema_nfhl_connector.py`.
- Focused FEMA NFHL connector tests passed: 12 passed.
- Focused connector adapter regression tests passed: 27 passed.
- Broader connector/source-registry tests passed with existing source-registry skips.
- Ruff passed for connector and source-registry files.
- Mypy passed over 43 connector/source-registry source files.
- Validate-only live FEMA NFHL smoke calls returned FEMA transfer-limit responses for the
  tested bboxes; the connector emitted failed retrieval contracts and non-retryable
  source-failure evidence instead of throwing or treating the response as negative
  flood evidence.
- Full DB-enabled `.\scripts\verify.ps1` passed: workspace validation ok; backend tests
  passed; ruff passed; canonical mypy passed over 153 source files; migrations/seeds
  applied; DB smoke passed.
- `py -3.12 -m pytest --collect-only` reports 513 collected tests.
- `.\scripts\agent-context-check.ps1` reports `agent context check: ok`.
- `py -3.12 .\scripts\source_readiness.py --priority Must` still reports
  `sources=8 ready=1 blocked=7`.
- `git diff --check` exited 0 with CRLF-to-LF warnings only for
  `docs/planning_pack/api/openapi_stub.yaml` and
  `docs/planning_pack/registers/data_source_registry.csv`.
- `docker compose ps` showed no services running after verification.

**Residual risk:**

- At the time of this connector-layer slice, it did not add an API route, background
  scheduler, review-queue worker, report-run shortcut, or automatic invocation from
  `/intake` or `/report-runs`. The later controlled DS-002 API invocation is recorded in
  the validation-log section above.
- Live FEMA NFHL success with spatial features is covered by deterministic unit tests with
  injected payloads. The live validate-only smoke in this environment exercised the
  transfer-limit source-failure path, not a successful live spatial-evidence response.
- DS-002 remains approved only with restrictions: screening use, citation, non-endorsement,
  service limits, no raw-export default, and no final legal/insurance/lending/buildability
  determinations.

## 2026-06-05 Level 10 DS-002 FEMA NFHL source review

**Scope:**

- Official-source terms/caveat review for FEMA NFHL.
- Root source registry DS-002 production-use status update.
- DB seed DS-002 production-use metadata/status alignment.
- Planning-pack DS-002 caveat alignment without expanding the planning-pack register schema.
- Source-readiness audit update proving DS-002 is the only ready current `Must` source.
- Static SQL seed first-class usage-rights refresh for re-seeding existing DB rows.

**Commands run:**

```powershell
cd backend; py -3.12 -m pytest -q tests/source_registry/test_source_readiness.py tests/source_registry/test_source_seeds.py tests/source_registry/test_source_service.py
cd backend; ruff check ../scripts/source_readiness.py ../db/seeds/source_registry_seeds.py tests/source_registry/test_source_readiness.py tests/source_registry/test_source_seeds.py tests/source_registry/test_source_service.py
cd backend; mypy ../scripts/source_readiness.py ../db/seeds/source_registry_seeds.py tests/source_registry/test_source_readiness.py tests/source_registry/test_source_seeds.py tests/source_registry/test_source_service.py
py -3.12 .\scripts\source_readiness.py --priority Must
py -3.12 .\scripts\source_readiness.py --priority Must --json
py -3.12 .\scripts\source_readiness.py --priority Must --require-ready
cd backend; py -3.12 -m pytest -q tests/source_registry
cd backend; ruff check ../scripts/source_readiness.py ../db/seeds/source_registry_seeds.py tests/source_registry
cd backend; mypy ../scripts/source_readiness.py ../db/seeds/source_registry_seeds.py tests/source_registry
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
.\scripts\agent-context-check.ps1
git diff --check
docker compose ps
```

**Results:**

- Added `docs/source-reviews/ds-002.md` from official FEMA/NFHL/OpenFEMA evidence.
- DS-002 is now `approved-with-restrictions` in `registers/data_source_registry.csv`.
- DS-002 production-use fields are aligned in `db/seeds/002_seed_source_registry.sql`.
- The SQL seed now inserts first-class `attribution_required` and refreshes first-class
  usage-rights columns on conflict, instead of updating only JSON metadata.
- Focused source-readiness/source-seed/source-service tests passed before the SQL
  re-seed correction: 30 passed.
- Focused `tests/source_registry` passed after the SQL re-seed correction, with the
  existing source-registry skip.
- Ruff passed for the readiness script, source seed loader, and source-registry tests.
- Mypy passed for the readiness script, source seed loader, and source-registry tests:
  13 source files.
- `py -3.12 .\scripts\source_readiness.py --priority Must` reports
  `sources=8 ready=1 blocked=7`.
- JSON output uses `schema_version=source_readiness_v1` and reports
  `source_count=8`, `ready_count=1`, and `blocked_count=7`.
- `--require-ready` exits 0 for current `Must` sources because DS-002 is ready.
- Full DB-enabled `.\scripts\verify.ps1` passed: workspace validation ok; backend tests
  passed; ruff passed; canonical mypy passed over 150 source files; migrations/seeds
  applied; DB smoke passed.
- `py -3.12 -m pytest --collect-only` reports 500 collected tests.
- `.\scripts\agent-context-check.ps1` reports `agent context check: ok`.
- `git diff --check` exited 0 with CRLF-to-LF warnings only for
  `docs/planning_pack/api/openapi_stub.yaml` and
  `docs/planning_pack/registers/data_source_registry.csv`.
- `docker compose ps` showed no services running after verification.

**Residual risk:**

- This does not implement a live FEMA NFHL connector or call the NFHL service.
- DS-002 remains approved only with restrictions: screening use, citation, non-endorsement,
  service limits, no raw-export default, and no final legal/insurance/lending/buildability
  determinations.
- The other seven MVP `Must` sources remain blocked by pending review and unknown or blocked
  production-use fields.
- The persistent local DB smoke reported 26 source rows after re-seeding. The current
  registry seed contains 25 rows; this indicates an older local DB row remains because
  seeding is additive/upsert-only and does not delete historical local rows.

## 2026-06-05 Level 10 source-readiness audit

**Scope:**

- Read-only source registry readiness reporting for connector candidate selection.
- All-registry and MVP-priority filtered source loading.
- JSON and human-readable readiness output.
- Optional `--require-ready` gate that fails when no source in scope is connector-ready.

**Commands run:**

```powershell
cd backend; py -3.12 -m pytest -q tests/source_registry/test_source_readiness.py tests/source_registry/test_source_seeds.py tests/source_registry/test_source_service.py
cd backend; ruff check ../scripts/source_readiness.py ../db/seeds/source_registry_seeds.py tests/source_registry/test_source_readiness.py tests/source_registry/test_source_seeds.py tests/source_registry/test_source_service.py
cd backend; mypy ../scripts/source_readiness.py ../db/seeds/source_registry_seeds.py tests/source_registry/test_source_readiness.py tests/source_registry/test_source_seeds.py tests/source_registry/test_source_service.py
py -3.12 .\scripts\source_readiness.py --priority Must
py -3.12 .\scripts\source_readiness.py --priority Must --json
py -3.12 .\scripts\source_readiness.py --priority Should --require-ready
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only -q
git diff --check
docker compose ps
```

**Results:**

- Focused source-readiness/source-seed/source-service tests passed before DS-002 review: 28 passed.
- Ruff passed for the readiness script, source seed loader, and focused tests.
- Mypy passed for the readiness script, source seed loader, and focused tests: 5 source files.
- Initial `py -3.12 .\scripts\source_readiness.py --priority Must` reported
  `sources=8 ready=0 blocked=8` before DS-002 review.
- JSON output used `schema_version=source_readiness_v1` and reported the same
  `source_count=8`, `ready_count=0`, and `blocked_count=8` before DS-002 review.
- `--require-ready` exited with code 2 before DS-002 review, as intended for a readiness
  gate when no selected source is ready.
- Full DB-enabled `.\scripts\verify.ps1` passed: workspace validation ok; backend tests
  passed; ruff passed; canonical mypy passed over 150 source files; migrations/seeds
  applied; DB smoke passed.
- `py -3.12 -m pytest --collect-only -q` reported 497 collected tests before DS-002
  source review.
- `git diff --check` exited 0 with only the existing CRLF-to-LF warning for regenerated
  `docs/planning_pack/api/openapi_stub.yaml` before DS-002 source review.
- `docker compose ps` showed no services running after verification.

**Residual risk:**

- This is a readiness report only. It does not approve source rights, mutate the registry,
  seed the DB, call live sources, or create connector artifacts.
- Current MVP `Must` sources remain blocked by pending review and unknown or blocked
  production-use fields.

## 2026-06-05 Level 10 connector source-use preflight

**Scope:**

- Shared source production-use rights helper.
- Connector preflight license/source-use guard.
- Fail-closed behavior for unapproved review status and unknown/blocked license,
  commercial, redistribution, cache, export, raw-data, or AI-use rights.
- Connector runbook alignment with the source registry production-use contract.

**Commands run:**

```powershell
cd backend; py -3.12 -m pytest -q tests/connectors/test_license_guard.py tests/connectors/test_static_file_connector.py tests/source_registry/test_source_service.py
cd backend; ruff check app/source_registry/usage_rights.py app/source_registry/service.py app/connectors/license_guard.py tests/connectors/test_license_guard.py tests/connectors/test_static_file_connector.py tests/source_registry/test_source_service.py
cd backend; mypy app/source_registry/usage_rights.py app/source_registry/service.py app/connectors/license_guard.py tests/connectors/test_license_guard.py tests/connectors/test_static_file_connector.py tests/source_registry/test_source_service.py
cd backend; py -3.12 -m pytest -q tests/connectors tests/source_registry tests/api/test_connector_review_actions.py tests/api/test_connector_review_status.py tests/api/test_connector_review_queue_db.py
cd backend; ruff check app/source_registry app/connectors tests/source_registry tests/connectors tests/api/test_connector_review_actions.py tests/api/test_connector_review_status.py tests/api/test_connector_review_queue_db.py
cd backend; mypy app/source_registry app/connectors tests/source_registry tests/connectors tests/api/test_connector_review_actions.py tests/api/test_connector_review_status.py tests/api/test_connector_review_queue_db.py
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only -q
git diff --check
```

**Results:**

- Focused connector/source-registry tests passed: 56 passed.
- Ruff passed for touched source-registry, connector, and test surfaces.
- Mypy passed for touched source-registry, connector, and test surfaces: 6 source files.
- Broader connector/source/API tests passed with existing DB-gated skips.
- Broader ruff passed for source-registry, connector, and connector API test surfaces.
- Broader mypy passed for 49 source files.
- Full DB-enabled `.\scripts\verify.ps1` passed: workspace validation ok; backend tests
  passed; ruff passed; canonical mypy passed over 149 source files; migrations/seeds
  applied; DB smoke passed.
- `py -3.12 -m pytest --collect-only -q` reports 493 collected tests.
- `git diff --check` exited 0 with only the existing CRLF-to-LF warning for regenerated
  `docs/planning_pack/api/openapi_stub.yaml`.
- `check_connector_source_license` now blocks connector runs unless source review and
  production-use rights are explicitly approved. The guard reports blocked fields so
  operators can see which source authority fields need review.

**Residual risk:**

- This does not approve any live source or call any live API.
- The current registry remains unreviewed/unknown for public sources and blocked for
  commercial vendors, so live connector integration remains blocked until source reviews
  and any needed credentials are available.

## 2026-06-05 Level 10 container build/runtime smoke

**Scope:**

- Backend image build through Compose.
- Compose startup for `db` and `backend`.
- Runtime HTTP smoke for `/health`, `/version`, and `/metrics`.
- Configurable host DB port through `DB_PORT`.
- Stack cleanup after smoke.

**Commands run:**

```powershell
docker compose build backend
docker compose up -d db backend
docker ps --format "{{.Names}} {{.Ports}}"
docker compose ps -a
$env:DB_PORT='55432'; docker compose up -d db backend
docker compose ps
Invoke-RestMethod -Uri http://127.0.0.1:8000/health
Invoke-RestMethod -Uri http://127.0.0.1:8000/version
Invoke-RestMethod -Uri http://127.0.0.1:8000/metrics
docker compose logs backend --tail 80
docker compose down
```

**Results:**

- `docker compose build backend` passed and produced `land_diligence_dual_agent_workspace-backend:latest`.
- Initial `docker compose up -d db backend` failed because host port `5432` was already allocated by `001-audit-db-1`.
- Added configurable Compose host DB port `DB_PORT`; reran the stack with `DB_PORT=55432`.
- DB and backend containers reached healthy state. Compose published backend on `8000` and DB on host port `55432`.
- `GET /health` returned `{"status":"ok","app":"land-diligence","environment":"local"}`.
- `GET /version` returned `{"version":"0.1.0"}`.
- `GET /metrics` returned `schema_version=runtime_metrics_v1` with HTTP route metrics.
- Backend logs showed clean Uvicorn startup and successful endpoint requests.
- `docker compose down` stopped and removed the smoke containers/network after validation.

**Residual risk:**

- Runtime smoke verifies packaged startup and operational endpoints. It does not run a full DB-backed API workflow inside the container.
- DB-backed API behavior remains covered by `RUN_DB_SMOKE=1` tests and migration smoke.
- Live connectors remain blocked on source/license review and credentials.

## 2026-06-05 Level 10 structured runtime metrics

**Scope:**

- Dependency-free structured runtime metrics collector.
- `/metrics` JSON endpoint.
- Route-template HTTP request counts, status counts, and duration aggregates.
- `ENABLE_METRICS` env/config wiring.
- API-key and rate-limit composition for `/metrics`.
- Planning-pack OpenAPI refresh.

**Commands run:**

```powershell
cd backend; py -3.12 -m pytest -q tests/api/test_metrics.py tests/api/test_rate_limit.py tests/api/test_api_key_auth.py tests/api/test_api_scaffold.py
cd backend; ruff check app/core/metrics.py app/api/metrics.py app/core/config.py app/main.py tests/api/test_metrics.py
cd backend; py -3.12 -m mypy app/core/metrics.py app/api/metrics.py app/core/config.py app/main.py tests/api/test_metrics.py
cd backend; py -3.12 -m pytest -q tests/api tests/test_planning_pack_schema_copies.py
cd backend; ruff check app/core app/api app/main.py tests/api tests/test_planning_pack_schema_copies.py
cd backend; mypy app tests
docker compose config
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
git diff --check
```

**Results:**

- Focused metrics/auth/rate/API tests passed: 30 passed.
- Broader API and OpenAPI parity tests passed after regenerating `docs/planning_pack/api/openapi_stub.yaml` from the live FastAPI contract.
- Ruff passed for touched API/core/test surfaces.
- Focused `py -3.12 -m mypy` passed for 5 source files.
- Canonical `mypy app tests` passed through the installed repo gate executable: 148 source files.
- `docker compose config` passed and rendered `ENABLE_METRICS=true` into the backend service environment.
- Full DB-enabled `.\scripts\verify.ps1` passed: workspace validation ok; backend tests passed; ruff passed; canonical mypy passed over 148 source files; migrations/seeds applied; DB smoke passed.
- `py -3.12 -m pytest --collect-only` reports 484 collected tests.
- `git diff --check` exited 0 with only the existing CRLF-to-LF warning for regenerated `docs/planning_pack/api/openapi_stub.yaml`.

**Residual risk:**

- Runtime metrics are in-memory process-local telemetry and reset on process restart.
- Metrics are not persisted, distributed, or exported to Prometheus/OpenTelemetry in this slice.
- Container syntax is verified; backend image build/runtime smoke remains open.

## 2026-06-05 Level 10 rate limiting

**Scope:**

- Default-off fixed-window runtime rate limiting.
- Settings parser for `RATE_LIMIT_REQUESTS` and `RATE_LIMIT_WINDOW_SECONDS`.
- Runtime protection for API/UI/docs when `ENABLE_RATE_LIMIT=true`.
- Public health/version probes for container/operator liveness.
- API-key identity buckets when `X-API-Key` is present, client-host buckets otherwise.
- `.env.example` and Compose environment wiring.

**Commands run:**

```powershell
cd backend; py -3.12 -m pytest -q tests/api/test_rate_limit.py tests/api/test_api_key_auth.py tests/api/test_api_scaffold.py
cd backend; ruff check app/api/rate_limit.py app/api/api_key_auth.py app/core/config.py app/main.py tests/api/test_rate_limit.py tests/api/test_api_key_auth.py
cd backend; py -3.12 -m mypy app/api/rate_limit.py app/api/api_key_auth.py app/core/config.py app/main.py tests/api/test_rate_limit.py tests/api/test_api_key_auth.py
cd backend; py -3.12 -m pytest -q tests/api tests/test_planning_pack_schema_copies.py
cd backend; ruff check app/core app/api app/main.py tests/api tests/test_planning_pack_schema_copies.py
cd backend; mypy app tests
docker compose config
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
git diff --check
```

**Results:**

- Focused rate-limit/API tests passed: 25 passed.
- Broader API and OpenAPI parity tests passed: 78 passed, 3 skipped.
- Ruff passed for touched API/core/test surfaces.
- Focused `py -3.12 -m mypy` passed for 6 source files.
- Canonical `mypy app tests` passed through the installed repo gate executable: 145 source files.
- `docker compose config` passed and rendered `ENABLE_RATE_LIMIT`, `RATE_LIMIT_REQUESTS`, and `RATE_LIMIT_WINDOW_SECONDS` into the backend service environment.
- Full DB-enabled `.\scripts\verify.ps1` passed: workspace validation ok; backend tests passed; ruff passed; canonical mypy passed over 145 source files; migrations/seeds applied; DB smoke passed.
- `py -3.12 -m pytest --collect-only` reports 479 collected tests.
- `git diff --check` exited 0 with only the existing CRLF-to-LF warning for regenerated `docs/planning_pack/api/openapi_stub.yaml`.

**Residual risk:**

- The rate limiter is in-process only. It does not coordinate across multiple workers, hosts, containers, or restarts.
- Structured metrics, security-event logging, and distributed rate-limit storage remain future Level 10 work.
- Container syntax is verified; backend image build/runtime smoke remains open.

## 2026-06-05 Level 10 API-key auth middleware

**Scope:**

- Default-off production API-key middleware.
- Settings parser for `API_KEYS`.
- Runtime protection for API/UI/docs/OpenAPI when `REQUIRE_API_KEY=true`.
- Public health/version probes for container/operator liveness.
- `.env.example` and Compose environment wiring.

**Commands run:**

```powershell
cd backend; py -3.12 -m pytest -q tests/api/test_api_key_auth.py tests/api/test_api_scaffold.py tests/api/test_reviewer_auth.py tests/api/test_connector_review_actions.py
cd backend; ruff check app/api/api_key_auth.py app/core/config.py app/main.py tests/api/test_api_key_auth.py
cd backend; py -3.12 -m mypy app/api/api_key_auth.py app/core/config.py app/main.py tests/api/test_api_key_auth.py
cd backend; py -3.12 -m pytest -q tests/api tests/test_planning_pack_schema_copies.py
cd backend; ruff check app/core app/api app/main.py tests/api tests/test_planning_pack_schema_copies.py
cd backend; py -3.12 -m mypy app/core app/api app/main.py tests/api
cd backend; mypy app tests
docker compose config
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest --collect-only
git diff --check
```

**Results:**

- Focused auth/API tests passed: 45 passed.
- Broader API and OpenAPI parity tests passed: 71 passed, 3 skipped.
- Ruff passed for touched API/core/test surfaces.
- `py -3.12 -m mypy` passed for touched API/core/test surfaces: 29 source files.
- Canonical `mypy app tests` passed through the installed repo gate executable: 143 source files.
- `docker compose config` passed and rendered `REQUIRE_API_KEY` plus `API_KEYS` into the backend service environment.
- Full DB-enabled `.\scripts\verify.ps1` passed: workspace validation ok; backend tests passed; ruff passed; canonical mypy passed over 143 source files; migrations/seeds applied; DB smoke passed.
- `py -3.12 -m pytest --collect-only` reports 472 collected tests.
- `git diff --check` exited 0 with only the existing CRLF-to-LF warning for regenerated `docs/planning_pack/api/openapi_stub.yaml`.
- An ad hoc `py -3.12 -m mypy app/core app/api app/main.py tests/api tests/test_planning_pack_schema_copies.py` command failed because the Python 3.12 environment does not have `types-PyYAML`; the repo's canonical `mypy app tests` executable path passes and `types-PyYAML` remains declared in `backend/pyproject.toml` dev extras.

**Residual risk:**

- API-key auth is a shared-secret production gate, not full identity or authorization.
- Rate limiting, key rotation, structured security metrics, and auth audit events remain future Level 10 work.
- Container syntax is verified; backend image build/runtime smoke remains open.

## 2026-06-05 Level 10 partial production hardening

**Scope:**

- Settings-backed connector reviewer auth.
- Backend Docker/Compose service wiring.
- Structured JSON logging.
- DB-backed async report job state in `jobs.job_queue`.

**Commands run:**

```powershell
cd backend; py -3.12 -m pytest -q tests/api/test_connector_review_actions.py tests/api/test_reviewer_auth.py
cd backend; py -3.12 -m pytest -q tests/api/test_connector_review_actions.py tests/api/test_reviewer_auth.py tests/api/test_logging.py
cd backend; py -3.12 -m pytest -q tests/reports/test_job_store.py tests/api/test_async_report_runs.py tests/api/test_api_scaffold.py tests/api/test_intake.py tests/api/test_logging.py tests/api/test_connector_review_actions.py tests/api/test_reviewer_auth.py
cd backend; ruff check app/core app/api app/reports tests/api tests/reports
cd backend; py -3.12 -m mypy app/core app/api app/reports tests/api tests/reports
docker compose config
cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/reports/test_job_store.py tests/api/test_report_runs_db.py
cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/api/test_async_report_runs.py tests/api/test_intake.py tests/api/test_connector_review_queue_db.py
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; py -3.12 -m pytest -q tests/test_planning_pack_schema_copies.py
cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest --tb=no -q -rA
git diff --check
```

**Results:**

- Targeted auth/logging tests passed: 30 passed.
- Targeted report/API non-DB tests passed: 55 passed, 2 skipped DB-gated tests.
- Targeted DB report job-store/report-run tests passed: 11 passed.
- Connector queue DB control plus intake/async API tests passed: 12 passed.
- Initial full `.\scripts\verify.ps1` failed on planning-pack OpenAPI parity after the live API contract changed.
- Regenerated `docs/planning_pack/api/openapi_stub.yaml` from `create_app().openapi()`; parity tests then passed.
- Full DB-enabled `.\scripts\verify.ps1` passed: workspace validation ok, backend tests passed, ruff passed, mypy passed over 141 source files, migrations/seeds applied, DB smoke passed.
- DB-enabled backend pytest count: 461 passed.
- `docker compose config` passed and rendered the new backend service with container-safe DB/object-store settings; `.dockerignore` keeps agent state, caches, archives, local artifacts, and worktrees out of the build context.
- `git diff --check` exited 0 with a CRLF-to-LF warning for regenerated `docs/planning_pack/api/openapi_stub.yaml`.

**Residual risk:**

- This is a partial Level 10 pass, not full production readiness.
- Production auth middleware, rate limiting, structured metrics, container build/runtime smoke, and live connector integration remain open.
- Live connectors remain blocked on source/license review and credentials.
- Compose syntax is verified; the backend image was not built or run in this pass.

## 2026-06-05 Level 9 PASS — MVP Workflow (worktree ralph/production-advance)

**L9 gate evidence:**

| Gate | Status | Evidence |
|---|---|---|
| L9-001 Async report job queue | PASS | AsyncReportJobStore (backend/app/reports/job_store.py); thread-safe in-memory dict with QUEUED/RUNNING/SUCCEEDED/FAILED states (US-009) |
| L9-002 Non-blocking POST /report-runs | PASS | POST /report-runs returns 202 Accepted with {report_run_id, status: "queued"}; BackgroundTask generates report (US-010) |
| L9-003 Job status polling | PASS | GET /report-runs/{id} returns slim ReportRunContract(status=QUEUED|RUNNING) for in-progress, full report when SUCCEEDED, error caveats when FAILED (US-010) |
| L9-004 One-shot GeoJSON intake | PASS | POST /intake accepts {area_geojson, intent_code}, creates area + async job, returns 202 {report_run_id, area_id} (US-011) |
| L9-005 UI end-to-end correctness | PASS | GET /ui/ calls POST /intake with correct intent_code values; /ui/report-runs/{id} shows pending/failed/complete states (US-012) |
| L9-006 Intent code alignment | PASS | UI intent values match IntentCode enum exactly (rural_land_purchase, homestead_feasibility); homestead_screen removed (US-012) |
| L9-007 OpenAPI parity | PASS | docs/planning_pack/api/openapi_stub.yaml regenerated; test_planning_pack_openapi_stub_matches_generated_fastapi_contract passes (US-014) |
| L9-008 Regression clean | PASS | 401 passed, 49 skipped (DB), 0 failed; lint and mypy clean on 12 source files (US-014) |
| L9-009 MVP operator runbook | PASS | docs/runbooks/mvp_operator.md: startup, config, API workflow, health check, limitations, troubleshooting (US-013) |
| L9-010 Async integration tests | PASS | tests/api/test_async_report_runs.py (5 tests), tests/api/test_intake.py (5 tests), tests/reports/test_job_store.py (8 tests) |

**Commands run:**

```powershell
cd backend
py -3.12 -m pytest tests/reports/test_job_store.py tests/api/test_async_report_runs.py tests/api/test_intake.py tests/api/test_ui_routes.py -q
py -3.12 -m pytest
ruff check app/reports/job_store.py app/reports/service.py app/api/reports.py app/api/dependencies.py app/api/intake.py app/api/ui.py app/main.py tests/reports/test_job_store.py tests/api/test_async_report_runs.py tests/api/test_intake.py tests/api/test_ui_routes.py tests/api/test_api_scaffold.py
mypy app/reports/job_store.py app/reports/service.py app/api/reports.py app/api/dependencies.py app/api/intake.py app/api/ui.py app/main.py tests/reports/test_job_store.py tests/api/test_async_report_runs.py tests/api/test_intake.py tests/api/test_ui_routes.py tests/api/test_api_scaffold.py
py -c "from app.main import create_app; import yaml; yaml.dump(create_app().openapi(), open('../docs/planning_pack/api/openapi_stub.yaml', 'w'), sort_keys=True)"
```

**Results:**

- New tests (US-009 to US-012): 18 passed.
- Full suite (non-DB): 401 passed, 49 skipped, 0 failed.
- Ruff: All checks passed (2 auto-fixed unused imports).
- Mypy: Success, no issues found in 12 source files.
- OpenAPI stub regenerated to include POST /intake and updated /report-runs (202); parity test passes.

**Residual risk:**

- AsyncReportJobStore is in-memory only; job status lost on server restart. Future Level 10 work should persist job state to Postgres.
- POST /intake creates a new area per call; no deduplication of identical GeoJSON submissions. Acceptable for MVP.
- Background tasks run synchronously in TestClient; production behavior (true async) is covered by design but not integration-tested against a real async server. Acceptable at this level.
- DB-backed full verification (RUN_DB_SMOKE=1) carries forward from the prior L8 baseline.

## 2026-06-05 Global Claude /ipc promotion

**Scope:** global Claude skill/command installation plus repo state logging. No Codex IPC
prompt/write send.

**Commands run:**

```powershell
Get-ChildItem -Force C:/Users/benny/.claude/skills
Get-ChildItem -Force C:/Users/benny/.claude/commands
Test-Path C:/Users/benny/.claude/skills/ipc
Test-Path C:/Users/benny/.claude/commands/ipc.md
Get-Content C:/Users/benny/.claude/commands/ipc.md
Get-Content C:/Users/benny/.claude/skills/ipc/SKILL.md -TotalCount 70
Select-String -Path C:/Users/benny/.claude/skills/ipc/SKILL.md -Pattern "IPC_TOOLKIT_ROOT|codex_ipc_write_proof|allow-any-thread|land_diligence_dual_agent_workspace|project6_REPO_MCP_FOLDER"
Test-Path C:/Users/benny/.claude/skills/ipc/SKILL.md
Test-Path C:/Users/benny/.claude/commands/ipc.md
Test-Path C:/Users/benny/OneDrive/Desktop/land_diligence_dual_agent_workspace/scripts/codex_ipc_client.mjs
Select-String -Path C:/Users/benny/.claude/commands/ipc.md -SimpleMatch 'C:\Users\benny\.claude\skills\ipc\SKILL.md'
Select-String -Path C:/Users/benny/.claude/commands/ipc.md -SimpleMatch '$ARGUMENTS'
Select-String -Path C:/Users/benny/.claude/skills/ipc/SKILL.md -SimpleMatch 'IPC_TOOLKIT_ROOT'
Select-String -Path C:/Users/benny/.claude/skills/ipc/SKILL.md -SimpleMatch 'codex_ipc_write_proof.mjs'
py -3.12 .\scripts\check_json_files.py
.\scripts\agent-context-check.ps1
git diff --check
.\scripts\verify.ps1
```

**Results:**

- No pre-existing global `ipc` skill or root-level `/ipc` command was present.
- Added `C:\Users\benny\.claude\skills\ipc\SKILL.md`.
- Added `C:\Users\benny\.claude\commands\ipc.md`.
- The global command points to the global skill and passes `$ARGUMENTS` as the `/ipc` invocation.
- The global skill includes toolkit-root resolution, known project paths, inspect-before-send,
  `--allow-any-thread`, post-update revalidation, and controlled write-proof harness instructions.
- The global skill, global command, and IPC toolkit script root all exist.
- Literal checks confirmed the global command points at the global skill and passes `$ARGUMENTS`;
  the global skill includes `IPC_TOOLKIT_ROOT` and `codex_ipc_write_proof.mjs`.
- `py -3.12 .\scripts\check_json_files.py`, `.\scripts\agent-context-check.ps1`, and
  `git diff --check` passed.
- Full `.\scripts\verify.ps1` passed: workspace validation ok, backend tests passed with skips,
  ruff passed, mypy passed over 123 source files, DB smoke skipped by default.

**Residual risk:**

- An already-running Claude Code process may need a command/skill refresh or restart before the new
  global `/ipc` command appears in its slash-command index.

## 2026-06-05 Codex IPC controlled re-proof harness

**Scope:** agent-coordination tooling/docs only. No product/backend, DB schema, API, report
behavior, or live Desktop IPC prompt/write send. The new proof harness was exercised in dry-run and
fail-closed modes only.

**Commands run:**

```powershell
node --check .\scripts\codex_ipc_write_proof.mjs
node --check .\scripts\codex_ipc_contract_audit.mjs
node .\scripts\codex_ipc_contract_audit.mjs
node .\scripts\codex_ipc_write_proof.mjs --thread 019e932e-385b-7ee3-ad58-3157c9accaf5 --marker CODEX_IPC_DRYRUN_PROOF_2026_06_05
node .\scripts\codex_ipc_write_proof.mjs --thread 019e0000-0000-0000-0000-000000000000 --marker CODEX_IPC_FAIL_CLOSED_2026_06_05 --send --ack-live-write
node --check .\scripts\codex_ipc_revalidate.mjs
node .\scripts\codex_ipc_revalidate.mjs --thread 019e932e-385b-7ee3-ad58-3157c9accaf5 --allow-live-ipc-read --timeout-ms 1500
node -e "JSON.parse(require('fs').readFileSync('.\\.omc\\prd.json','utf8')); console.log('prd ok')"
rg -n "10/10|ten IPC|all ten|Still open:|Remaining: controlled|PARTIALLY DONE.*Phase 6|future Desktop update write re-proof" .\plans\2026-06-04-codex-ipc-injection.md .\state\agent-inbox\README.md .\.claude\skills\ipc\SKILL.md .\.omc\progress.txt .\.omc\prd.json .\scripts\codex_ipc_contract_audit.mjs
py -3.12 .\scripts\check_json_files.py
.\scripts\agent-context-check.ps1
git diff --check
.\scripts\verify.ps1
```

**Results:**

- `codex_ipc_write_proof.mjs` and `codex_ipc_contract_audit.mjs` passed Node syntax checks.
- The static IPC contract audit passed and now reports 11/11 requirements evidenced from repo
  artifacts, including the controlled write re-proof harness.
- The post-update revalidation wrapper now includes `codex_ipc_write_proof.mjs` in required-file
  and Node syntax checks. Runtime-read-probe mode passed, sending only router `initialize` and no
  prompt or `thread-follower-start-turn`.
- The proof harness dry-run inspected target thread `019e932e-385b-7ee3-ad58-3157c9accaf5` and
  reported `maybeMidTurn:false`, model `gpt-5.5`, reasoning `xhigh`, rollout line 147, and a
  proof sequence of inspect -> revalidate -> before snapshot -> one live send -> rollout poll ->
  after snapshot -> compare. It did not send a prompt.
- The non-test live proof command without `--allow-any-thread` exited non-zero before any live
  operation with the expected error requiring `--allow-any-thread` for another explicit
  conversationId.
- `.omc/prd.json` parsed as JSON.
- Stale-count/status search returned no remaining current references to the old 10/10 audit count
  or Phase 6 remaining-open wording in the active IPC docs/state files.
- `py -3.12 .\scripts\check_json_files.py` passed: 594 source JSON files.
- Agent context check passed.
- `git diff --check` passed.
- Full `.\scripts\verify.ps1` passed after the revalidation-wrapper update: workspace validation ok, backend tests passed with skips,
  ruff passed, mypy passed over 123 source files, DB smoke skipped by default.
- No live IPC prompt/write send was attempted.

**Residual risk:**

- `--ipc` remains experimental because it depends on undocumented Codex Desktop IPC internals.
- A future Desktop update may still require an explicitly approved live re-proof; the new harness
  makes that proof dry-run-first, target-inspected, runtime-revalidated, marker-backed, and
  isolation-compared.
- File-drop remains the default and fallback.

## 2026-06-05 Level 8 PASS — Connector + Operational Hardening (worktree ralph/production-advance)

**L8 gate evidence:**

| Gate | Status | Evidence |
|---|---|---|
| L8-001 Shared connector interface | PASS | StaticFloodFixtureConnector + ConnectorReviewQueueRepository protocol |
| L8-002 Connector runs persisted | PASS | source.ingest_runs via Lane A provenance; jobs.job_queue for review lifecycle (CON-007, CON-008, CON-014) |
| L8-003 Idempotent ingestion | PASS | Duplicate ingest_run_id detection + evidence ID fingerprinting (CON-003, CON-008, CON-009) |
| L8-004 Failures → source_failure evidence | PASS | Flood fixture source-failure path; blocked retrieval records (CON-004, CON-009) |
| L8-005 Rate limits/timeouts/retry policies | PASS | ConnectorPolicy + DEFAULT_FIXTURE_POLICY in backend/app/connectors/policy.py (US-001) |
| L8-006 Data quality gates | PASS | 29 fixture quality issue codes in ConnectorFixtureQualityProfile (CON-012 through CON-038) |
| L8-007 Evidence before claims | PASS | FixtureConnectorIngestWorkflow: provenance → evidence → (claims not called by connector) (CON-002, CON-007) |
| L8-008 No live network in normal tests | PASS | All connector tests fixture-backed; 49 DB-backed tests opt-in via RUN_DB_SMOKE=1 |
| L8-009 License enforcement | PASS | check_connector_source_license() blocks incompatible/unknown_blocking statuses (US-003) |
| L8-010 Observability for connector failures | PASS | ConnectorRunObservabilityLog + 7 event types in backend/app/connectors/observability.py (US-002) |

**Commands run:**

```powershell
cd backend
py -3.12 -m pytest -q tests/connectors/test_connector_policy.py tests/connectors/test_connector_observability.py tests/connectors/test_license_guard.py tests/api/test_connector_review_actions.py
py -3.12 -m pytest --tb=short
ruff check app/connectors/ app/api/connectors.py
py -3.12 -m mypy app/connectors/ app/api/connectors.py
```

**Results:**

- New tests (US-001 to US-004): 39 passed.
- Full suite (non-DB): 362 passed, 49 skipped, 0 failed.
- Ruff: All checks passed after import-order autofix on connectors/__init__.py.
- Mypy: Success, no issues found in 15 source files.
- OpenAPI stub regenerated to include 3 new review-action routes; parity test passes.

**Residual risk:**

- ConnectorPolicy and observability modules define the interface but are not yet wired into the fixture connector workflow (no behavioral change to existing connectors). Future connector implementations should adopt these modules.
- License enforcement is enforced at the guard level but the existing flood fixture source has license_status="unknown" in seeds; future live connectors must have reviewed license status before use.
- Review action routes use a hardcoded fixture service account for auth; production deployment needs settings-backed service account configuration.
- DB-backed full verification (RUN_DB_SMOKE=1) carries forward from the prior CON-038 baseline (372 tests + new tests).

## 2026-06-04 Connector CON-038 fixture source-failure geometry absence

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

- Focused fixture-quality tests: 20 passed.
- Focused connector ruff: clean.
- Focused connector mypy: clean over 2 source files.
- Whitespace check: clean.
- Default Windows PowerShell verification passed with 372 backend tests collected, lint clean, mypy clean over 123 source files, and DB smoke skipped by default.
- DB-enabled Windows PowerShell verification passed with 372 backend tests collected/passing, lint clean, mypy clean over 123 source files, migrations/seeds applied, and DB smoke passed.
- Backend collection: 372 tests collected.

**Residual risk:**

- CON-038 is connector-local fixture quality only. It does not add API routes, OpenAPI changes, DB schema changes, queue behavior, connector runtime behavior, live I/O, hook config, POSIX scripts, durable evidence-row `ingest_run_id` linkage, or Lane A/B/C/D module changes outside connector quality. Connector review route/OpenAPI implementation remains deferred while Session 1's Lane C evidence-linkage/OpenAPI branch is parked.

## 2026-06-04 Connector CON-037 fixture method-code consistency

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

- Focused fixture-quality tests: 19 passed.
- Focused connector ruff: clean.
- Focused connector mypy: clean over 2 source files.
- Whitespace check: clean.
- Default Windows PowerShell verification passed with 371 backend tests collected, lint clean, mypy clean over 123 source files, and DB smoke skipped by default.
- DB-enabled Windows PowerShell verification passed with 371 backend tests collected/passing, lint clean, mypy clean over 123 source files, migrations/seeds applied, and DB smoke passed.
- Backend collection: 371 tests collected.

**Residual risk:**

- CON-037 is connector-local fixture quality only. It does not add API routes, OpenAPI changes, DB schema changes, queue behavior, connector runtime behavior, live I/O, hook config, POSIX scripts, durable evidence-row `ingest_run_id` linkage, or Lane A/B/C/D module changes outside connector quality. Connector review route/OpenAPI implementation remains deferred while Session 1's Lane C evidence-linkage/OpenAPI branch is parked.

## 2026-06-04 Connector CON-036 fixture source-failure type consistency

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

- Focused fixture-quality tests: 18 passed.
- Focused connector ruff: clean.
- Focused connector mypy: clean over 2 source files.
- Whitespace check: clean.
- Default Windows PowerShell verification passed with 370 backend tests collected, lint clean, mypy clean over 123 source files, and DB smoke skipped by default.
- DB-enabled Windows PowerShell verification passed with 370 backend tests collected/passing, lint clean, mypy clean over 123 source files, migrations/seeds applied, and DB smoke passed.
- Backend collection: 370 tests collected.

**Residual risk:**

- CON-036 is connector-local fixture quality only. It does not add API routes, OpenAPI changes, DB schema changes, queue behavior, connector runtime behavior, live I/O, hook config, POSIX scripts, durable evidence-row `ingest_run_id` linkage, or Lane A/B/C/D module changes outside connector quality. Connector review route/OpenAPI implementation remains deferred while Session 1's Lane C evidence-linkage/OpenAPI branch is parked.

## 2026-06-04 Connector CON-035 fixture evidence area consistency

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

- Focused fixture-quality tests: 17 passed.
- Focused connector ruff: clean.
- Focused connector mypy: clean over 2 source files.
- Whitespace check: clean.
- Default Windows PowerShell verification passed with 369 backend tests collected, lint clean, mypy clean over 123 source files, and DB smoke skipped by default.
- DB-enabled Windows PowerShell verification passed with 369 backend tests collected/passing, lint clean, mypy clean over 123 source files, migrations/seeds applied, and DB smoke passed.
- Backend collection: 369 tests collected.

**Residual risk:**

- CON-035 is connector-local fixture quality only. It does not add API routes, OpenAPI changes, DB schema changes, queue behavior, connector runtime behavior, live I/O, hook config, POSIX scripts, durable evidence-row `ingest_run_id` linkage, or Lane A/B/C/D module changes outside connector quality. Connector review route/OpenAPI implementation remains deferred while Session 1's Lane C evidence-linkage/OpenAPI branch is parked.

## 2026-06-04 Connector CON-034 fixture evidence source consistency

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

- Focused fixture-quality tests: 16 passed.
- Focused connector ruff: clean.
- Focused connector mypy: clean over 2 source files.
- Whitespace check: clean.
- Default Windows PowerShell verification passed with 368 backend tests collected, lint clean, mypy clean over 123 source files, and DB smoke skipped by default.
- DB-enabled Windows PowerShell verification passed with 368 backend tests collected/passing, lint clean, mypy clean over 123 source files, migrations/seeds applied, and DB smoke passed.
- Backend collection: 368 tests collected.

**Residual risk:**

- CON-034 is connector-local fixture quality only. It does not add API routes, OpenAPI changes, DB schema changes, queue behavior, connector runtime behavior, live I/O, hook config, POSIX scripts, durable evidence-row `ingest_run_id` linkage, or Lane A/B/C/D module changes outside connector quality. Connector review route/OpenAPI implementation remains deferred while Session 1's Lane C evidence-linkage/OpenAPI branch is parked.

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

## 2026-06-06 review-debt focused validation

```powershell
cd backend
py -3.12 -m pytest -q tests\source_registry\test_source_provenance.py tests\source_registry\test_source_provenance_schema_contract.py tests\connectors\test_fixture_quality.py tests\connectors\test_fixture_workflow.py tests\connectors\test_evidence_ingestion_adapter.py tests\connectors\test_retrieval_provenance_adapter.py tests\connectors\test_review_queue.py tests\test_run_api_script.py tests\api\test_connector_review_actions.py tests\api\test_openapi_contract.py tests\test_planning_pack_schema_copies.py
ruff check app\domain\source_contracts.py app\evidence_ledger\service.py app\connectors app\api\connectors.py tests\source_registry\test_source_provenance.py tests\source_registry\test_source_provenance_schema_contract.py tests\connectors\test_fixture_quality.py tests\connectors\test_fixture_workflow.py tests\connectors\test_evidence_ingestion_adapter.py tests\connectors\test_retrieval_provenance_adapter.py tests\connectors\test_review_queue.py tests\test_run_api_script.py tests\api\test_connector_review_actions.py tests\api\test_openapi_contract.py tests\test_planning_pack_schema_copies.py
mypy app\domain\source_contracts.py app\evidence_ledger\service.py app\connectors app\api\connectors.py tests\source_registry\test_source_provenance.py tests\source_registry\test_source_provenance_schema_contract.py tests\connectors\test_fixture_quality.py tests\connectors\test_fixture_workflow.py tests\connectors\test_evidence_ingestion_adapter.py tests\connectors\test_retrieval_provenance_adapter.py tests\connectors\test_review_queue.py tests\test_run_api_script.py tests\api\test_connector_review_actions.py tests\api\test_openapi_contract.py tests\test_planning_pack_schema_copies.py
git diff --check
```

Result: focused pytest passed, ruff passed, mypy passed for 39 source files, and
`git diff --check` passed with only CRLF normalization warnings on generated OpenAPI
stub files.

```powershell
.\scripts\verify.ps1
py -3.12 .\scripts\source_readiness.py --priority Must --json
```

Result: full Windows verification passed. Backend tests, ruff, mypy, workspace
validation, and structural invariants passed; DB smoke was skipped because
`RUN_DB_SMOKE` was not set. The full test run still reports existing
`HTTP_422_UNPROCESSABLE_ENTITY` deprecation warnings in unrelated API paths.
Must-source readiness remains `sources=8 ready=4 blocked=4`; blocked Must sources are
`DS-010`, `DS-011`, `DS-017`, and `DS-023`.

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
