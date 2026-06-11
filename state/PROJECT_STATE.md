# Project State

## Current checkpoint (2026-06-11 source-readiness closure)

Authoritative current source-readiness checks:

- Must priority: `sources=8 ready=7 blocked=1`; DS-017 Commercial parcel vendor is the only Must blocker.
- All priorities: `sources=25 ready=16 blocked=9`; DS-007 BLM MLRS is now connector-ready for bounded active federal mining-claim context only. DS-015 NC Geological Survey remains connector-ready for bounded 1985 geologic map-unit context only. DS-008 USGS MRDS remains connector-ready for bounded historical mineral-occurrence screening only. DS-022 Census TIGER/ACS remains connector-ready for bounded TIGERweb tract/block-group geography context only. ACS demographic variables remain excluded.
- Active plan: `plans/2026-06-06-source-readiness-closure.md`.
- Current pass: DS-007 is promoted only for BLM MLRS Active Mining Claims MapServer layer 1 context; it does not determine private mineral rights, claim-boundary precision, title status, mine hazards, resource value, extraction feasibility, environmental liability, buildability, appraisal, lending, insurance, or investment suitability.
- Recent production-hardening pass: signed-token `POST /report-runs` now honors `Idempotency-Key` through a workspace/user-scoped job-store ledger, replays the same generated report on repeated matching requests, and returns `409 Conflict` for matching-principal payload mismatches. The accepted sync/async response-shape divergence remains: signed-token creates return a full `ReportRunContract`, while the unauthenticated operator path returns async job status.
- DB-enabled verification passed on Docker PostGIS with `RUN_DB_SMOKE=1`, `DATABASE_URL_SYNC=postgresql://land:land@localhost:55432/land_diligence`, and `DATABASE_URL=postgresql+psycopg://land:land@localhost:55432/land_diligence`. Default verification still does not prove DB readiness unless `RUN_DB_SMOKE=1` is set and PostgreSQL/PostGIS prerequisites are available.

Older entries below remain historical unless they match the checks above.

## MILESTONE_MAP status block

```text
Current milestone: Level 10 - Production Hardening (partial)
Milestone status: PARTIAL PASS for Level 10 hardening and source-readiness closure. Current source readiness is Must sources=8 ready=7 blocked=1 (DS-017 only) and all-priority sources=25 ready=16 blocked=9. Recent connector-ready additions include DS-011 explicit not-evaluated assessor evidence, DS-016 OSM road access, DS-005 USGS water monitoring, DS-006 EPA ECHO, DS-021 FCC Broadband, DS-020 NOAA NWS climate/weather, DS-022 Census TIGERweb geography context, DS-008 USGS MRDS historical mineral-occurrence context, DS-015 NCGS 1985 geologic map-unit context, and DS-007 BLM MLRS active federal mining-claim context. Release-readiness validation is aligned to Must ready=7 blocked=1. DB smoke remains a separate RUN_DB_SMOKE=1 proof when PostgreSQL/PostGIS prerequisites are available. DS-017 remains vendor/license blocked.
Last verified: 2026-06-11
Verification command(s):
- cd backend; py -3.12 -m pytest tests\connectors\test_blm_mlrs_connector.py tests\api\test_blm_mlrs_connector_api.py tests\source_registry\test_source_readiness.py -q --tb=short
- py -3.12 .\scripts\source_readiness.py
- py -3.12 .\scripts\source_readiness.py --priority Must --json
- py -3.12 .\scripts\source_readiness.py --priority Should --json
- py -3.12 .\scripts\source_readiness.py --priority Later --json
- cd backend; ruff check app\connectors\blm_mlrs.py app\connectors\__init__.py app\api\dependencies.py app\api\live_connectors.py app\api\connectors.py app\evidence_ledger\payload_validation.py app\source_registry\connector_inventory.py tests\connectors\test_blm_mlrs_connector.py tests\api\test_blm_mlrs_connector_api.py tests\source_registry\test_source_readiness.py
- cd backend; py -3.12 -m mypy app\connectors\blm_mlrs.py app\connectors\__init__.py app\api\dependencies.py app\api\live_connectors.py app\api\connectors.py app\evidence_ledger\payload_validation.py app\source_registry\connector_inventory.py tests\connectors\test_blm_mlrs_connector.py tests\api\test_blm_mlrs_connector_api.py tests\source_registry\test_source_readiness.py
- py -3.12 .\scripts\export_openapi_stub.py
- cd backend; py -3.12 -m pytest tests\test_planning_pack_schema_copies.py tests\api\test_openapi_contract.py -q --tb=short
- cd backend; py -3.12 -m pytest tests\source_registry\test_source_readiness.py tests\source_registry\test_source_seeds.py -q --tb=short
- .\scripts\run_release_readiness_check.ps1
- git diff --check
- .\scripts\verify.ps1
- cd backend; py -3.12 -m pytest tests\connectors\test_usgs_mrds_connector.py tests\api\test_usgs_mrds_connector_api.py tests\source_registry\test_source_readiness.py -q --tb=short
- py -3.12 .\scripts\source_readiness.py
- py -3.12 .\scripts\source_readiness.py --priority Must
- py -3.12 .\scripts\source_readiness.py --priority Later
- cd backend; ruff check app\connectors\usgs_mrds.py app\connectors\__init__.py app\api\dependencies.py app\api\live_connectors.py app\api\connectors.py app\evidence_ledger\payload_validation.py app\source_registry\connector_inventory.py tests\connectors\test_usgs_mrds_connector.py tests\api\test_usgs_mrds_connector_api.py tests\source_registry\test_source_readiness.py
- cd backend; py -3.12 -m mypy app\connectors\usgs_mrds.py app\connectors\__init__.py app\api\dependencies.py app\api\live_connectors.py app\api\connectors.py app\evidence_ledger\payload_validation.py app\source_registry\connector_inventory.py tests\connectors\test_usgs_mrds_connector.py tests\api\test_usgs_mrds_connector_api.py tests\source_registry\test_source_readiness.py
- py -3.12 .\scripts\export_openapi_stub.py
- cd backend; py -3.12 -m pytest tests\test_planning_pack_schema_copies.py tests\api\test_openapi_contract.py -q --tb=short
- cd backend; py -3.12 -m pytest tests\source_registry\test_source_readiness.py tests\source_registry\test_source_seeds.py -q --tb=short
- .\scripts\run_release_readiness_check.ps1
- git diff --check
- .\scripts\verify.ps1
- cd backend; py -3.12 -m pytest tests\connectors\test_census_tiger_connector.py tests\api\test_census_tiger_connector_api.py tests\source_registry\test_source_readiness.py -q --tb=short
- py -3.12 .\scripts\source_readiness.py
- py -3.12 .\scripts\source_readiness.py --priority Must
- py -3.12 .\scripts\source_readiness.py --priority Later
- cd backend; ruff check app\connectors\census_tiger.py app\connectors\__init__.py app\api\dependencies.py app\api\live_connectors.py app\api\connectors.py app\evidence_ledger\payload_validation.py app\source_registry\connector_inventory.py tests\connectors\test_census_tiger_connector.py tests\api\test_census_tiger_connector_api.py tests\source_registry\test_source_readiness.py
- cd backend; py -3.12 -m mypy app\connectors\census_tiger.py app\connectors\__init__.py app\api\dependencies.py app\api\live_connectors.py app\api\connectors.py app\evidence_ledger\payload_validation.py app\source_registry\connector_inventory.py tests\connectors\test_census_tiger_connector.py tests\api\test_census_tiger_connector_api.py tests\source_registry\test_source_readiness.py
- py -3.12 .\scripts\export_openapi_stub.py
- cd backend; py -3.12 -m pytest tests\test_planning_pack_schema_copies.py tests\api\test_openapi_contract.py -q --tb=short
- cd backend; py -3.12 -m pytest tests\source_registry\test_source_readiness.py tests\source_registry\test_source_seeds.py -q --tb=short
- .\scripts\run_release_readiness_check.ps1
- py -3.12 .\scripts\source_readiness.py --priority Must --json
- .\scripts\verify.ps1
- cd backend; py -3.12 -m pytest -q tests/source_registry/test_source_readiness.py tests/test_release_readiness_artifacts.py
- py -3.12 .\scripts\source_readiness.py --priority Must --json
- .\scripts\run_release_readiness_check.ps1
- git diff --check
- .\scripts\verify.ps1
- cd backend; python -m pytest --tb=no
- cd backend; python -m pytest -q tests/reports/test_report_regression.py tests/reports/test_dossier_enrichment.py
- cd backend; ruff check tests/reports/test_report_regression.py tests/reports/test_dossier_enrichment.py
- cd backend; py -3.12 -m mypy tests/reports/test_report_regression.py tests/reports/test_dossier_enrichment.py
- .\scripts\verify.ps1
- cd backend; py -3.12 -m pytest -q tests/api/test_connector_review_actions.py tests/api/test_reviewer_auth.py tests/api/test_logging.py
- cd backend; py -3.12 -m pytest -q tests/api/test_api_key_auth.py tests/api/test_api_scaffold.py tests/api/test_reviewer_auth.py tests/api/test_connector_review_actions.py
- cd backend; py -3.12 -m pytest -q tests/api/test_rate_limit.py tests/api/test_api_key_auth.py tests/api/test_api_scaffold.py
- cd backend; py -3.12 -m pytest -q tests/api/test_metrics.py tests/api/test_rate_limit.py tests/api/test_api_key_auth.py tests/api/test_api_scaffold.py
- cd backend; py -3.12 -m pytest -q tests/api tests/test_planning_pack_schema_copies.py
- cd backend; ruff check app/core app/api app/main.py tests/api tests/test_planning_pack_schema_copies.py
- cd backend; py -3.12 -m mypy app/core app/api app/main.py tests/api
- cd backend; mypy app tests
- docker compose config
- docker compose build backend
- $env:DB_PORT='55432'; docker compose up -d db backend
- Invoke-RestMethod -Uri http://127.0.0.1:8000/health
- Invoke-RestMethod -Uri http://127.0.0.1:8000/version
- Invoke-RestMethod -Uri http://127.0.0.1:8000/metrics
- docker compose logs backend --tail 80
- docker compose down
- cd backend; py -3.12 -m pytest -q tests/connectors/test_license_guard.py tests/connectors/test_static_file_connector.py tests/source_registry/test_source_service.py
- cd backend; ruff check app/source_registry/usage_rights.py app/source_registry/service.py app/connectors/license_guard.py tests/connectors/test_license_guard.py tests/connectors/test_static_file_connector.py tests/source_registry/test_source_service.py
- cd backend; mypy app/source_registry/usage_rights.py app/source_registry/service.py app/connectors/license_guard.py tests/connectors/test_license_guard.py tests/connectors/test_static_file_connector.py tests/source_registry/test_source_service.py
- cd backend; py -3.12 -m pytest -q tests/source_registry/test_source_readiness.py tests/source_registry/test_source_seeds.py tests/source_registry/test_source_service.py
- cd backend; ruff check ../scripts/source_readiness.py ../db/seeds/source_registry_seeds.py tests/source_registry/test_source_readiness.py tests/source_registry/test_source_seeds.py tests/source_registry/test_source_service.py
- cd backend; mypy ../scripts/source_readiness.py ../db/seeds/source_registry_seeds.py tests/source_registry/test_source_readiness.py tests/source_registry/test_source_seeds.py tests/source_registry/test_source_service.py
- py -3.12 .\scripts\source_readiness.py --priority Must
- py -3.12 .\scripts\source_readiness.py --priority Must --json
- py -3.12 .\scripts\source_readiness.py --priority Must --require-ready
- cd backend; py -3.12 -m pytest -q tests\connectors\test_fema_nfhl_connector.py
- cd backend; py -3.12 -m pytest -q tests\connectors\test_nwi_connector.py
- cd backend; py -3.12 -m pytest -q tests\api\test_fema_nfhl_connector_api.py tests\connectors\test_fema_nfhl_connector.py
- cd backend; py -3.12 -m pytest -q tests\api\test_connector_review_actions.py tests\connectors\test_review_queue.py
- cd backend; py -3.12 -m pytest -q tests\evidence_ledger\test_evidence_schema_contract.py tests\evidence_ledger\test_sqlalchemy_evidence_repo.py tests\connectors\test_fema_nfhl_connector.py tests\reports\test_report_service.py
- cd backend; ruff check app\domain\evidence_contracts.py app\evidence_ledger app\connectors app\reports tests\evidence_ledger tests\connectors tests\reports
- cd backend; mypy app\domain\evidence_contracts.py app\evidence_ledger app\connectors app\reports tests\evidence_ledger tests\connectors tests\reports
- cd backend; py -3.12 -m pytest -q tests\api\test_fema_nfhl_connector_api.py
- cd backend; ruff check tests\api\test_fema_nfhl_connector_api.py app\api app\reports
- cd backend; mypy tests\api\test_fema_nfhl_connector_api.py app\api app\reports
- cd backend; py -3.12 -m pytest -q tests\connectors tests\source_registry
- cd backend; py -3.12 -m pytest -q tests\api tests\connectors tests\source_registry
- cd backend; ruff check app\connectors tests\connectors tests\source_registry
- cd backend; ruff check app\api app\connectors tests\api tests\connectors tests\source_registry
- cd backend; mypy app\connectors tests\connectors tests\source_registry
- cd backend; mypy app\api app\connectors tests\api tests\connectors tests\source_registry
- $env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
- cd backend; py -3.12 -m pytest --collect-only
- git diff --check
- cd backend; py -3.12 -m pytest -q tests/reports/test_job_store.py tests/api/test_async_report_runs.py tests/api/test_api_scaffold.py tests/api/test_intake.py tests/api/test_logging.py tests/api/test_connector_review_actions.py tests/api/test_reviewer_auth.py
- cd backend; ruff check app/core app/api app/reports tests/api tests/reports
- cd backend; py -3.12 -m mypy app/core app/api app/reports tests/api tests/reports
- docker compose config
- cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/reports/test_job_store.py tests/api/test_report_runs_db.py
- cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/api/test_async_report_runs.py tests/api/test_intake.py tests/api/test_connector_review_queue_db.py
- $env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
- cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest --tb=no -q -rA
- git diff --check
- cd backend; py -3.12 -m pytest -q tests/connectors/test_connector_policy.py tests/connectors/test_connector_observability.py tests/connectors/test_license_guard.py tests/api/test_connector_review_actions.py
- cd backend; py -3.12 -m pytest --tb=short
- cd backend; ruff check app/connectors/ app/api/connectors.py
- cd backend; py -3.12 -m mypy app/connectors/ app/api/connectors.py
- cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/evidence_ledger
- cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/evidence_ledger tests/claims_engine
- cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/claims_engine
- cd backend; py -3.12 -m pytest -q tests/reports tests/api
- cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/api tests/reports
- cd backend; py -3.12 -m pytest -q tests/reports/test_report_regression.py
- cd backend; ruff check app/api app/main.py app/reports tests/api tests/reports
- cd backend; mypy app/reports app/api tests/reports tests/api
- cd backend; ruff check app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
- cd backend; ruff check app/claims_engine tests/claims_engine
- cd backend; mypy app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
- cd backend; mypy app/claims_engine tests/claims_engine
- cd backend; py -3.12 -m pytest -q tests/connectors/test_fixture_quality.py
- cd backend; ruff check app/connectors/fixture_quality.py tests/connectors/test_fixture_quality.py
- cd backend; mypy app/connectors/fixture_quality.py tests/connectors/test_fixture_quality.py
- cd backend; py -3.12 -m pytest -q tests/connectors/test_review_status.py tests/api/test_connector_review_status.py
- cd backend; py -3.12 -m pytest -q tests/connectors/test_review_queue.py
- cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/connectors/test_review_queue.py
- cd backend; py -3.12 -m pytest -q tests/api/test_connector_review_status.py tests/api/test_connector_review_queue_db.py
- cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/api/test_connector_review_queue_db.py
- cd backend; py -3.12 -m pytest -q tests/connectors
- cd backend; py -3.12 -m pytest -q tests/connectors tests/api -rA
- cd backend; ruff check app/connectors tests/connectors
- cd backend; ruff check app/connectors app/api app/main.py tests/connectors tests/api
- cd backend; mypy app/connectors tests/connectors
- cd backend; mypy app/connectors app/api app/main.py tests/connectors tests/api
- cd backend; rg -n "from app\.source_registry|from app\.area_geometry|import app\.source_registry|import app\.area_geometry" app/evidence_ledger app/claims_engine
- cd backend; py -3.12 -m pytest --collect-only -q
- python scripts/db_smoke_check.py
- cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/area_geometry
- cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/evidence_ledger tests/claims_engine
- cd backend; py -3.12 -m pytest -q tests/test_planning_pack_schema_copies.py
- cd backend; ruff check tests/test_planning_pack_schema_copies.py
- cd backend; mypy tests/test_planning_pack_schema_copies.py
- .\scripts\verify.ps1
- cd backend; py -3.12 -m pytest -q tests/reports/test_report_schema_contract.py tests/reports/test_report_contracts.py
- cd backend; py -3.12 -m pytest -q tests/reports/test_report_schema_contract.py tests/reports/test_report_service.py tests/reports/test_report_regression.py
- cd backend; py -3.12 -m pytest -q tests/reports tests/api
- cd backend; ruff check tests/reports/test_report_schema_contract.py
- cd backend; ruff check app/reports tests/reports/test_report_schema_contract.py tests/reports/test_report_service.py tests/reports/test_report_regression.py
- cd backend; ruff check app/reports app/api app/main.py tests/reports tests/api
- cd backend; mypy tests/reports/test_report_schema_contract.py
- cd backend; mypy app/reports tests/reports/test_report_schema_contract.py tests/reports/test_report_service.py tests/reports/test_report_regression.py
- cd backend; mypy app/reports app/api app/main.py tests/reports tests/api
- git diff --check
- cd backend; py -3.12 -m pytest --collect-only
- cd backend; py -3.12 -m pytest -q tests\connectors\test_review_packet.py tests\connectors\test_review_handoff.py tests\connectors\test_review_queue.py tests\api\test_connector_review_status.py tests\api\test_fema_nfhl_connector_api.py
- cd backend; ruff check app\api\connectors.py app\connectors\review_packet.py app\connectors\review_handoff.py app\connectors\review_queue.py tests\api\test_fema_nfhl_connector_api.py tests\api\test_connector_review_status.py tests\connectors\test_review_packet.py tests\connectors\test_review_handoff.py tests\connectors\test_review_queue.py
- cd backend; mypy app\api\connectors.py app\connectors\review_packet.py app\connectors\review_handoff.py app\connectors\review_queue.py tests\api\test_fema_nfhl_connector_api.py tests\api\test_connector_review_status.py tests\connectors\test_review_packet.py tests\connectors\test_review_handoff.py tests\connectors\test_review_queue.py
- cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests\api\test_fema_nfhl_connector_api.py::test_db_live_connector_report_run_waits_for_approval_then_reports
- cd backend; py -3.12 -m pytest -q tests\test_planning_pack_schema_copies.py tests\api\test_fema_nfhl_connector_api.py tests\api\test_connector_review_actions.py tests\api\test_connector_review_status.py tests\connectors\test_review_packet.py tests\connectors\test_review_handoff.py tests\connectors\test_review_queue.py
- cd backend; py -3.12 -m pytest -q tests\connectors\test_review_queue.py tests\api\test_connector_review_actions.py tests\api\test_connector_review_status.py
- cd backend; ruff check app\connectors\review_queue.py app\api\connectors.py tests\connectors\test_review_queue.py tests\api\test_connector_review_actions.py
- cd backend; mypy app\connectors\review_queue.py app\api\connectors.py tests\connectors\test_review_queue.py tests\api\test_connector_review_actions.py
- cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests\connectors\test_review_queue.py
- cd backend; py -3.12 -m pytest -q tests\connectors\test_review_queue.py tests\api\test_connector_review_actions.py tests\api\test_connector_review_status.py tests\api\test_connector_review_queue_db.py tests\api\test_fema_nfhl_connector_api.py tests\api\test_async_report_runs.py tests\api\test_report_runs_db.py
- cd backend; py -3.12 -m pytest -q tests\api\test_fema_nfhl_connector_api.py tests\api\test_connector_review_actions.py tests\api\test_connector_review_status.py
- cd backend; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests\api\test_fema_nfhl_connector_api.py::test_db_live_connector_scheduler_enqueues_and_runs_without_report_job tests\api\test_fema_nfhl_connector_api.py::test_db_live_connector_report_run_waits_for_approval_then_reports
- cd backend; py -3.12 -m pytest -q tests\test_planning_pack_schema_copies.py tests\api\test_fema_nfhl_connector_api.py tests\api\test_connector_review_actions.py tests\api\test_connector_review_status.py tests\api\test_connector_review_queue_db.py
- cd backend; ruff check app\connectors\live_jobs.py app\api\live_connector_jobs.py app\api\connectors.py app\api\dependencies.py tests\api\test_fema_nfhl_connector_api.py tests\test_planning_pack_schema_copies.py
- cd backend; mypy app\connectors\live_jobs.py app\api\live_connector_jobs.py app\api\connectors.py app\api\dependencies.py tests\api\test_fema_nfhl_connector_api.py tests\test_planning_pack_schema_copies.py
- cd backend; py -3.12 -m pytest -q tests\api\test_live_connector_worker.py tests\api\test_fema_nfhl_connector_api.py
- cd backend; py -3.12 -m pytest -q tests\api\test_nwi_connector_api.py tests\api\test_fema_nfhl_connector_api.py tests\api\test_live_connector_worker.py
- cd backend; py -3.12 -m pytest -q tests\test_planning_pack_schema_copies.py tests\api\test_nwi_connector_api.py tests\api\test_fema_nfhl_connector_api.py tests\api\test_live_connector_worker.py
- cd backend; ruff check app\connectors\live_jobs.py app\api\live_connector_jobs.py app\api\connectors.py app\connectors\__init__.py tests\api\test_nwi_connector_api.py tests\api\test_fema_nfhl_connector_api.py tests\api\test_live_connector_worker.py ..\scripts\live_connector_worker.py
- cd backend; mypy app\connectors\live_jobs.py app\api\live_connector_jobs.py app\api\connectors.py app\connectors\__init__.py tests\api\test_nwi_connector_api.py tests\api\test_fema_nfhl_connector_api.py tests\api\test_live_connector_worker.py ..\scripts\live_connector_worker.py
- cd backend; ruff check app\api\live_connector_jobs.py tests\api\test_live_connector_worker.py ..\scripts\live_connector_worker.py
- cd backend; mypy app\api\live_connector_jobs.py tests\api\test_live_connector_worker.py ..\scripts\live_connector_worker.py
- docker compose --profile workers config
- docker compose build backend
- docker compose --profile workers run --rm --no-deps --entrypoint python live-connector-worker /app/scripts/live_connector_worker.py --help
- $env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
- cd backend; py -3.12 -m pytest --collect-only
- git diff --check
- py -3.12 .\scripts\source_readiness.py --priority Must
- cd backend; py -3.12 -m pytest -q tests\source_registry\test_source_readiness.py tests\source_registry\test_source_seeds.py
- cd backend; ruff check tests\source_registry\test_source_readiness.py tests\source_registry\test_source_seeds.py ..\db\seeds\source_registry_seeds.py ..\scripts\source_readiness.py
- cd backend; mypy tests\source_registry\test_source_readiness.py tests\source_registry\test_source_seeds.py ..\db\seeds\source_registry_seeds.py ..\scripts\source_readiness.py
- cd backend; ruff check app\connectors\nwi.py app\connectors\__init__.py tests\connectors\test_nwi_connector.py
- cd backend; mypy app\connectors\nwi.py app\connectors\__init__.py tests\connectors\test_nwi_connector.py
- cd backend; py -3.12 -m pytest -q tests\connectors\test_nwi_connector.py tests\api\test_live_connector_worker.py
- cd backend; ruff check tests\connectors\test_nwi_connector.py tests\api\test_live_connector_worker.py ..\scripts\live_connector_worker.py
- cd backend; py -3.12 -m mypy tests\connectors\test_nwi_connector.py tests\api\test_live_connector_worker.py
- cd backend; py -3.12 -m pytest -q tests\connectors\test_nwi_connector.py tests\api\test_nwi_connector_api.py tests\api\test_live_connector_worker.py
- cd backend; py -3.12 -m pytest -q -W error::DeprecationWarning tests\api\test_api_scaffold.py::test_api_scaffold_returns_422_for_bad_input tests\api\test_async_report_runs.py::test_post_report_runs_unregistered_area_returns_422 tests\api\test_intake.py::test_intake_invalid_geojson_returns_422 tests\api\test_connector_review_actions.py::test_request_fixture_fix_requires_reason tests\api\test_fema_nfhl_connector_api.py::test_fema_nfhl_query_bbox_rejects_oversized_bbox tests\api\test_nwi_connector_api.py::test_nwi_query_bbox_rejects_oversized_bbox tests\api\test_ssurgo_connector_api.py::test_ssurgo_query_bbox_rejects_oversized_bbox tests\api\test_usgs_tnm_connector_api.py::test_usgs_tnm_query_bbox_rejects_oversized_bbox
- cd backend; ruff check app\api\areas.py app\api\connectors.py app\api\intake.py app\api\live_connectors.py app\api\reports.py
- cd backend; py -3.12 -m mypy app\api\areas.py app\api\connectors.py app\api\intake.py app\api\live_connectors.py app\api\reports.py
- cd backend; py -3.12 -m pytest -q tests\test_planning_pack_schema_copies.py tests\api\test_fema_nfhl_connector_api.py::test_live_connector_sequence_schedule_bbox_enqueues_ordered_jobs_without_fetch_or_report tests\api\test_fema_nfhl_connector_api.py::test_live_connector_sequence_schedule_bbox_requires_reviewer_auth tests\api\test_fema_nfhl_connector_api.py::test_live_connector_sequence_schedule_bbox_rejects_unregistered_area
- cd backend; ruff check app\api\connectors.py tests\api\test_fema_nfhl_connector_api.py tests\test_planning_pack_schema_copies.py
- cd backend; py -3.12 -m mypy app\api\connectors.py tests\api\test_fema_nfhl_connector_api.py tests\test_planning_pack_schema_copies.py
- cd backend; py -3.12 -m pytest -q tests\test_planning_pack_schema_copies.py tests\api\test_fema_nfhl_connector_api.py tests\api\test_nwi_connector_api.py tests\api\test_ssurgo_connector_api.py tests\api\test_usgs_tnm_connector_api.py tests\api\test_live_connector_worker.py
- docker ps -a --filter "name=live-connector-worker-run" --format "{{.Names}} {{.Status}}"
- docker compose ps
Verification result:
- Level 10 partial hardening slice passes: settings-backed scoped reviewer auth, production API-key middleware with raw-or-sha256 configured secrets, configured static API-key lifecycle specs, and structured API-key auth audit logs plus DB-backed API-key auth events, default-off rate limiting, backend Docker/Compose service, structured JSON logging, structured runtime metrics, container build/runtime smoke, fail-closed connector source-use preflight, source-readiness audit reporting, reviewed source-rights candidates (DS-001 USGS The National Map, DS-002 FEMA NFHL, DS-003 USDA Web Soil Survey/SSURGO, and DS-004 National Wetlands Inventory), bounded DS-001 USGS TNM EPQS connector-layer terrain-relief screening plus controlled DS-001 API/operator invocation, explicit durable DS-001 live connector scheduling, and request-time DS-001 orchestration, bounded DS-002 FEMA NFHL live connector, bounded DS-003 USDA SSURGO connector plus controlled DS-003 API/operator invocation, explicit durable DS-003 live connector scheduling, and request-time DS-003 report integration with an UNKNOWN SSURGO screening-review claim, bounded DS-004 National Wetlands Inventory connector, controlled DS-002 API/operator invocation, controlled DS-004 API/operator invocation, explicit durable DS-002 and DS-004 live connector scheduling, read-only live connector job status API, bounded supervised live connector worker command, opt-in Compose live connector worker profile, connector review closeout actions, durable connector reviewer action history, approved connector evidence report gating, DB-backed connector approval-to-report regressions, request-time DS-001, DS-002, DS-004, and DS-003 orchestration for `/intake` and `/report-runs`, file-backed DS-004 raw response fixture corpus, API 422 deprecation cleanup, live connector sequence scheduling, failed report job retry with lineage, backup/restore proof, repo-local alert-rule catalog with validate-only proof, CI supply-chain dependency vulnerability scanning and update hygiene, backend production dependency lock/SBOM provenance proof, backend dependency lock/SBOM artifact attestation proof, backend container image/base-image scan proof, digest-pinned backend Docker base-image proof, repo-local cost monitoring catalog with validate-only guardrails and report zero-dollar cost attribution, repo-local release readiness catalog with validate-only proof, local release package ZIP/manifest builder with validate-only proof, repo-local image publication readiness catalog with validate-only proof, repo-local hosted deployment readiness catalog with validate-only proof, repo-local access-control posture catalog with validate-only proof, scoped local reviewer authorization with raw-or-sha256 configured service-account tokens for protected operator routes, explicit post-approval connector report resume, SQLAlchemy source placeholder URL hardening, and DB-backed async report job persistence through `jobs.job_queue` are implemented. Current full DB-enabled Windows PowerShell verification passes after the DB-backed API-key auth audit-event slice: 722 tests are collected; ruff clean; canonical mypy clean over 185 source files; migrations/seeds apply; DB smoke passes; hosted log retention, automatic key rotation, user accounts, OAuth/OIDC, hosted identity, full RBAC, hosted deployment, hosted billing reconciliation, and hosted alerting remain blocked.
- 362 tests pass in the DB-enabled Windows PowerShell verification path after TD-083 report validation metadata; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes.
- 363 tests pass in the DB-enabled Windows PowerShell verification path after CON-027 connector fixture retrieval metric quality; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes.
- 363 tests pass in the DB-enabled Windows PowerShell verification path after TD-084 job-schema boundary; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes.
- 364 tests pass in the DB-enabled Windows PowerShell verification path after CON-028 connector source-failure payload type quality; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes.
- 365 tests pass in the DB-enabled Windows PowerShell verification path after CON-029 connector source-failure reason consistency; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes.
- 365 tests pass in the DB-enabled Windows PowerShell verification path after CON-030 connector retrieval failure-reason metric quality; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes.
- 365 tests pass in the DB-enabled Windows PowerShell verification path after CON-031 connector succeeded-retrieval failure-metric quality; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes.
- 366 tests pass in the DB-enabled Windows PowerShell verification path after CON-032 connector fixture evidence domain quality; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes.
- 367 tests pass in the DB-enabled Windows PowerShell verification path after CON-033 connector fixture retrieval name quality; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes.
- 368 tests pass in the DB-enabled Windows PowerShell verification path after CON-034 connector fixture evidence source consistency; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes.
- 369 tests pass in the DB-enabled Windows PowerShell verification path after CON-035 connector fixture evidence area consistency; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes.
- 370 tests pass in the DB-enabled Windows PowerShell verification path after CON-036 connector fixture source-failure type consistency; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes.
- 371 tests pass in the DB-enabled Windows PowerShell verification path after CON-037 connector fixture method-code consistency; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes.
- 401 non-DB tests + 49 skipped DB tests pass in worktree ralph/production-advance after full Level 9 MVP workflow (US-009 through US-014): AsyncReportJobStore, async POST /report-runs (202), GET /report-runs/{id} status polling, POST /intake one-shot GeoJSON endpoint, web UI fixed end-to-end (calls /intake, correct intent codes, async status display), MVP operator runbook, and OpenAPI stub refresh. Lint clean; mypy clean (12 source files verified). L9-001 through L9-010 gates all pass.
- 383 non-DB tests + 49 skipped DB tests pass in worktree ralph/production-advance after full Level 8 + Level 9 groundwork (US-001 through US-008): ConnectorPolicy, ConnectorRunObservabilityLog, check_connector_source_license, review action routes (request_fixture_fix/requeue_after_fix/cancel_review), connector runbook, StaticLocalFileConnector (second connector integrating all three modules), minimal web UI at GET /ui/, and OpenAPI stub refresh. Lint clean; mypy clean (18 source files verified). DB-enabled path carries forward 372+ from prior baseline.
- 372 tests pass in the DB-enabled Windows PowerShell verification path after CON-038 connector fixture source-failure geometry absence; lint clean; mypy clean (123 source files); migrations/seeds apply; DB smoke passes.
- 350 tests pass in the DB-enabled Windows PowerShell verification path after TA-080 source provenance-family schema parity; lint clean; mypy clean (121 source files); migrations/seeds apply; DB smoke passes.
- 343 tests pass in the DB-enabled Windows PowerShell verification path after TD-081 report manifest metadata schema tightening; lint clean; mypy clean (120 source files); migrations/seeds apply; DB smoke passes.
- 344 tests pass in the DB-enabled Windows PowerShell verification path after rebasing TD-090 planning-pack OpenAPI refresh onto TD-081 report manifest metadata schema tightening; lint clean; mypy clean (120 source files); migrations/seeds apply; DB smoke passes.
- 331 tests pass in the DB-enabled Windows PowerShell verification path after combined Lane C TC-180 plus CON-017/CON-018 integration rehearsal; lint clean; mypy clean (118 source files); migrations/seeds apply; DB smoke passes.
- 330 tests pass in the DB-enabled Windows PowerShell verification path after aligning the Lane A source schema with serialized `SourceContract`; lint clean; mypy clean (119 source files); migrations/seeds apply; DB smoke passes.
- 335 tests pass in the DB-enabled Windows PowerShell verification path after merging Lane A TA-070 and CON-019 connector source-failure ID adoption into the Session 2 integration branch; lint clean; mypy clean (119 source files); migrations/seeds apply; DB smoke passes.
- 337 tests pass in the DB-enabled Windows PowerShell verification path after CON-020 connector fixture identity/timing quality; lint clean; mypy clean (119 source files); migrations/seeds apply; DB smoke passes.
- 339 tests pass in the DB-enabled Windows PowerShell verification path after adding the Lane D report-run schema contract; lint clean; mypy clean (120 source files); migrations/seeds apply; DB smoke passes.
- 341 tests pass in the DB-enabled Windows PowerShell verification path after merging CON-020 connector fixture quality with Lane D TD-080 report-run schema; lint clean; mypy clean (120 source files); migrations/seeds apply; DB smoke passes.
- 342 tests pass in the DB-enabled Windows PowerShell verification path after TD-090 planning-pack OpenAPI refresh; lint clean; mypy clean (120 source files); migrations/seeds apply; DB smoke passes.
- Local Postgres/PostGIS migrations and seeds apply cleanly, and DB smoke validates required schemas, tables, columns, enums, foreign keys, and seeds
- Source versioning, retrieval lifecycle, caveats, freshness, authority, and license/review/usage-right metadata are implemented and surfaced downstream; canonical `schemas/source_schema.json` is aligned to serialized `SourceContract` with parity tests
- Lane B area/geometry slice now includes a SQLAlchemy/PostGIS `core.areas` repository that round-trips Polygon/MultiPolygon GeoJSON as SRID 4326 MultiPolygon geometry, supports all six Level 4 domain area types with explicit metadata-preserved domain type mapping, preserves source/confidence/validated fields, reads PostGIS-derived area/centroid/bbox metrics, queries fixture spatial relations through PostGIS, stores immutable prior-geometry rows in `core.area_versions` on geometry replacement, and rejects non-finite or out-of-range EPSG:4326 lon/lat positions
- Lane C evidence/claim/rule-engine/schema slices pass targeted runtime, type, lint, schema-contract, and import-isolation checks; the evidence ledger now has a SQLAlchemy/Postgres repository for `evidence.observations`, durable evidence audit events in `audit.events`, first-class optional evidence geometry mapped to `evidence.observations.geometry`, spatial precision preserved in evidence metadata, DB-backed claim/evidence/verification-task persistence, source-failure evidence ID preservation through the public Lane C service, evidence-backed not-evaluated UNKNOWN claims for unsupported soil/septic, environmental hazard, resource-context, and market-context categories, and canonical evidence/claim JSON schemas aligned to serialized domain contracts
- Lane D report runs now persist through `reports.report_runs` and a machine-readable JSON artifact under `OBJECT_STORE_ROOT`; report/API output now surfaces stored not-evaluated unsupported-category source failures as UNKNOWN claims
- Lane D API DB mode now wires SQLAlchemy-backed source, area, evidence, claim, and report repositories through request-scoped services; `POST /areas`, `POST /report-runs`, and `GET /report-runs/{id}` are covered by a DB-backed integration test
- Lane D report artifact semantics are now pinned by a normalized regression test that ignores dynamic UUID/timestamp/path fields while asserting source manifest, evidence, claims, unknowns, red flags, caveats, and artifact metadata
- Shared schema gaps for job schema remain recorded with future lane ownership in `plans/2026-06-04-l7-closeout-l8-entry.md`; Lane A source and source provenance-family schemas, Lane C evidence/claim root schemas, Lane D report-run schema plus stable generated report manifest metadata keys and report metadata extension boundaries, planning-pack evidence/claim schema copies, and planning-pack OpenAPI are now aligned to their serialized/generated contract authorities
- Level 8 connector gates L8-001 through L8-010 are mapped to lane owners, and the first fixture-only connector runtime contract slice is implemented as a static local flood fixture with no live network, explicit idempotency, blocked/source-failure behavior, and source retrieval provenance
- D-005 is complete: `LANE_OWNERSHIP.md` assigns a coordinator-owned connector integration zone, `docs/adr/lane-d-0002-connector-entry-ownership.md` is accepted, source retrieval runs are connector lifecycle/provenance authority, and jobs remain future async orchestration
- CON-001 is complete: `StaticFloodFixtureConnector` reads local flood fixture JSON, rejects URI-like paths, emits `SourceRetrievalRunContract` plus `EvidenceContract` inputs, covers success/failure source-failure fixtures, and stays before claims/reports
- CON-002 is complete: connector evidence-ingestion handoff is defined; the connector-zone adapter must use injected public Lane C EvidenceService methods, direct Lane C repository/private-helper access is rejected, and durable retrieval-run/evidence linkage gaps are recorded for future coordination
- CON-003 is complete: `ConnectorEvidenceIngestionAdapter` uses an injected public evidence-ingestion port, routes normal evidence to `create_observation`, routes source failures to `create_source_failure`, skips duplicate deterministic evidence IDs, fingerprints source failures for repeated fixture idempotency, and stays before claims/reports
- CON-004 is complete: `ConnectorRetrievalProvenanceAdapter` uses an injected source retrieval provenance port, preserves connector-supplied retrieval-run identity, skips duplicate `ingest_run_id` values, and records the Lane A concrete wiring gap without importing Lane A repositories/services
- CON-005 is complete: `FixtureConnectorIngestWorkflow` composes the fixture connector, retrieval provenance adapter, and evidence ingestion adapter so retrieval provenance is recorded before evidence ingestion, repeated fixture workflow runs are idempotent, and the workflow remains fixture-only/injected-port based before claims/reports
- CON-006 is complete: connector-owned public-service wiring now composes the fixture workflow with public Lane C `EvidenceService` methods while preserving the Lane A retrieval-run identity requirement behind an explicit provenance port; flood source-failure fixture payloads are aligned to Lane C validation
- CON-007 is complete: Lane A public provenance service now records supplied `SourceRetrievalRunContract` values while preserving `ingest_run_id`, and connector public wiring can use that service without Lane A repository imports
- CON-008 is complete: the fixture success workflow now runs against DB-backed public Lane A provenance and public Lane C evidence services, records the supplied retrieval-run identity, persists evidence through public evidence methods, and skips the existing retrieval/evidence records on a repeated run
- CON-009 is complete: the fixture source-failure workflow now runs against DB-backed public Lane A provenance and public Lane C evidence services, records the supplied blocked retrieval-run identity, persists source-failure evidence through public source-failure methods, and skips the existing retrieval/source-failure fingerprint on a repeated run
- CON-010 is complete: connector run/status review packets now summarize fixture workflow retrieval status, provenance action, evidence counts, source-failure counts, idempotent skips, review signals, and human-review tasks without API, claims, reports, schema edits, live I/O, or persistence changes
- CON-011 is complete: connector review handoffs now consume review packets and classify them into `needs_human_review`, `ready_for_connector_qa`, or `idempotent_noop` records without API, durable queue persistence, claims, reports, schema edits, live I/O, or Lane A/B/C/D implementation changes
- CON-012 is complete: connector fixture quality profiles now flag fixture-local provenance, dataset-version, row-count, spatial evidence, retrieval-status/evidence consistency, and source-failure payload/confidence gaps without API, durable queue persistence, claims, reports, schema edits, live I/O, or Lane A/B/C/D implementation changes
- CON-013 is complete: connector review status now composes handoff and fixture-quality data, and `GET /connector-runs/{ingest_run_id}/review-status` exposes stored in-memory status without durable queue persistence, connector status tables, claims, reports, schema edits, live I/O, or DB-backed connector status
- CON-014 is complete: connector review status can now be persisted as idempotent `connector_review_status` jobs in `jobs.job_queue` with payload references to `source.ingest_runs.ingest_run_id`, preserving source retrieval runs as connector provenance and lifecycle authority
- CON-015 is complete: `GET /connector-runs/{ingest_run_id}/review-queue` retrieves in-memory or DB-backed connector review queue items by `ingest_run_id` without job mutation, worker execution, schema edits, live I/O, claims, reports, or DB-backed evidence linkage
- CON-016 is complete: connector review queue repositories can lease eligible `connector_review_status` jobs, mark running jobs succeeded, and mark running jobs failed without adding a scheduler, API mutation route, retry/requeue policy, live I/O, claims, reports, schema edits, or provenance mutation
- TC-180 is complete for Lane C public service scope: `EvidenceService.create_source_failure(...)` preserves caller-supplied source-failure evidence IDs through in-memory and SQLAlchemy-backed evidence storage while still rejecting duplicate IDs without overwrite; CON-019 completes connector-zone adapter adoption in the Session 2 integration branch
- CON-017 is complete: `GET /connector-runs/{ingest_run_id}/review-queue` exposes queue attempts, lock/start/finish metadata, and last error for in-memory and DB-backed queue rows without adding API-side job mutation, worker execution, retry/requeue policy, live I/O, claims, reports, schema edits, or provenance mutation
- CON-018 is complete: connector review queue repositories can requeue failed `connector_review_status` jobs only when attempts remain and cancel nonfinal jobs with reasons, without adding API-side mutation, automatic retry policy, scheduler, live I/O, claims, reports, schema edits, or provenance mutation
- CON-019 is complete in the Session 2 integration branch: connector evidence ingestion now passes deterministic source-failure evidence IDs into Lane C's public `create_source_failure(...)` method and DB-backed public wiring proves the ID round-trips; no Lane C implementation/schema edits, live I/O, queue mutation/API route, claim/report shortcut, or durable `ingest_run_id` evidence-row linkage was added
- CON-020 is complete: connector fixture quality now flags duplicate evidence IDs and evidence observed outside the retrieval-run time window without adding API mutation routes, persistence, live I/O, shared schema edits, claims, reports, or durable `ingest_run_id` evidence-row linkage
- TD-081 is complete: stable generated report `source_manifest`, `source_details`, `artifact_metadata`, and `cost_metrics` schema keys are constrained with parity tests and ADR `docs/adr/lane-d-0010-report-manifest-metadata.md`, without adding runtime validation, API behavior changes, DB migrations, connector behavior, live I/O, hook config, or POSIX scripts
- TD-090 is complete: the planning-pack OpenAPI reference now matches the live FastAPI-generated OpenAPI contract and the planning-pack API spec separates implemented endpoints from future roadmap endpoints.
- CON-021 is complete as a planning-only human-review action semantics pass. Future connector review actions are named before any API mutation route, worker, scheduler, dashboard, connector runtime change, schema, or migration.
- CON-022 is complete as a planning-only human-review API semantics pass. Future route/reviewer/auth/idempotency semantics are accepted before API mutation implementation or OpenAPI change.
- TA-080 is complete: the separate source provenance-family schema now covers serialized source dataset, dataset-version, and retrieval-run contracts without changing runtime validation, migrations, connector behavior, queue semantics, live I/O, or durable evidence-row linkage.
- CON-023 is complete: connector-local fixture quality now fails closed when evidence provenance text, caveats, or non-failure source dates are missing, without changing APIs, schemas, queues, source/evidence/claim/report behavior, or live I/O.
- TD-082 is complete as a planning-only report metadata extension boundary. Future report metadata extension families and promotion rules are accepted without changing report runtime behavior, APIs, schemas, queues, migrations, or live I/O.
- CON-024 is complete as a connector review action API auth blocker decision. The future review-action mutation route remains blocked until an authenticated reviewer/operator principal dependency or accepted service-account delegation rule is added and tested.
- CON-025 is complete as a local service-account reviewer principal dependency for future connector review mutation routes, without registering a route or changing OpenAPI.
- CON-026 is complete as a connector review action route-subset decision for `request_fixture_fix`, `requeue_after_fix`, and `cancel_review`; route/OpenAPI implementation remains deferred to avoid Session 1's Lane C evidence-linkage/OpenAPI branch.
- TD-083 is complete as a report validation metadata implementation: `artifact_metadata.validation` records report contract/profile and ruleset identity, with schema/regression coverage, without claiming verification-command execution or changing routes, OpenAPI, DB schema, connector runtime, queue behavior, live I/O, hook config, POSIX scripts, or Lane A/B/C modules.
- CON-027 is complete: connector-local fixture quality now fails closed when succeeded retrievals have nonzero errors or missing/mismatched row counts, and when blocked/failed retrievals lack explicit zero row count or positive error count, without changing API/OpenAPI, DB schema, queue behavior, connector runtime, live I/O, hook config, POSIX scripts, durable evidence-row lineage, or lane-owned modules outside connector quality.
- TD-084 is complete as a job-schema boundary decision: `schemas/job_schema.json` remains unedited and is not promoted to a live connector-run/API contract until a future schema/test slice chooses `jobs.job_queue`, `ConnectorReviewQueueItem`, or a new `JobContract` as authority; source retrieval runs remain connector provenance authority.
- CON-028 is complete: connector-local fixture quality now fails closed when source-failure payload values have empty/non-string `failure_reason` or `error_message`, or non-boolean `retryable`, without changing API/OpenAPI, DB schema, queue behavior, connector runtime, live I/O, hook config, POSIX scripts, durable evidence-row lineage, or lane-owned modules outside connector quality.
- CON-029 is complete: connector-local fixture quality now fails closed when source-failure payload `failure_reason` disagrees with retrieval `metrics.failure_reason`, without changing API/OpenAPI, DB schema, queue behavior, connector runtime, live I/O, hook config, POSIX scripts, durable evidence-row lineage, or lane-owned modules outside connector quality.
- CON-030 is complete: connector-local fixture quality now fails closed when blocked/failed retrievals lack non-empty `metrics.failure_reason`, without changing API/OpenAPI, DB schema, queue behavior, connector runtime, live I/O, hook config, POSIX scripts, durable evidence-row lineage, or lane-owned modules outside connector quality.
- CON-031 is complete: connector-local fixture quality now fails closed when succeeded retrievals carry non-empty `metrics.failure_reason`, without changing API/OpenAPI, DB schema, queue behavior, connector runtime, live I/O, hook config, POSIX scripts, durable evidence-row lineage, or lane-owned modules outside connector quality.
- CON-032 is complete: connector-local fixture quality now fails closed when flood fixture evidence has a domain other than `flood`, without changing API/OpenAPI, DB schema, queue behavior, connector runtime, live I/O, hook config, POSIX scripts, durable evidence-row lineage, or lane-owned modules outside connector quality.
- CON-033 is complete: connector-local fixture quality now fails closed when flood fixture retrievals have a connector name other than `fixture_flood_static`, without changing API/OpenAPI, DB schema, queue behavior, connector runtime, live I/O, hook config, POSIX scripts, durable evidence-row lineage, or lane-owned modules outside connector quality.
- CON-034 is complete: connector-local fixture quality now fails closed when one flood fixture retrieval emits evidence with mixed `source_id` values, without changing API/OpenAPI, DB schema, queue behavior, connector runtime, live I/O, hook config, POSIX scripts, durable evidence-row lineage, or lane-owned modules outside connector quality.
- CON-035 is complete: connector-local fixture quality now fails closed when one flood fixture retrieval emits evidence with mixed `area_id` values, without changing API/OpenAPI, DB schema, queue behavior, connector runtime, live I/O, hook config, POSIX scripts, durable evidence-row lineage, or lane-owned modules outside connector quality.
- CON-036 is complete: connector-local fixture quality now fails closed when `is_source_failure` disagrees with `evidence_type == "source_failure"`, without changing API/OpenAPI, DB schema, queue behavior, connector runtime, live I/O, hook config, POSIX scripts, durable evidence-row lineage, or lane-owned modules outside connector quality.
- CON-037 is complete: connector-local fixture quality now fails closed when non-empty flood fixture evidence `method_code` values do not start with `fixture_flood_`, without changing API/OpenAPI, DB schema, queue behavior, connector runtime, live I/O, hook config, POSIX scripts, durable evidence-row lineage, or lane-owned modules outside connector quality.
- CON-038 is complete: connector-local fixture quality now fails closed when source-failure fixture evidence carries geometry or spatial precision, without changing API/OpenAPI, DB schema, queue behavior, connector runtime, live I/O, hook config, POSIX scripts, durable evidence-row lineage, or lane-owned modules outside connector quality.
Failed or blocked gates:
- No Level 5 blockers remain in the fixture-backed DB repository path verified on 2026-06-04.
- L5-001 through L5-010: PASS for the DB-backed evidence repository/service scope (source observations, source failures, spatial intersections, derived metrics, document extracts, human verification notes, geometry/SRID/spatial precision, invalid payload rejection, supersession, deterministic retrieval, rollback behavior, durable audit events, and the evidence-ledger persistence ADR are tested or documented)
- L6-001 through L6-010: PASS for Lane C claim/rule scope (claims require evidence links, unknowns require source-failure evidence, severity/confidence stay separate, verification tasks persist, rules are versioned/deterministic, caveats propagate, contradiction/stale/incomplete/source-failure/not-evaluated cases are tested, and rule logic lives in code/config rather than an LLM/UI prompt)
- L7-001 through L7-010: PASS for the fixture-backed report/API vertical slice (persisted report run, source/evidence/rule manifest data, API create/retrieve path, evidence-linked claims, unknown/source-failure surfacing, caveats/verification tasks, repeatable fixture behavior, API contract coverage, artifact metadata, and no live external APIs)
Completion evidence:
- state/VALIDATION_LOG.md
- backend/tests/source_registry/ (48 tests collected)
- backend/tests/area_geometry/ (49 tests)
- backend/app/domain/area_contracts.py (`AreaContract`, `AreaMetricsContract`, `AreaSpatialRelationContract`, `AreaVersionContract`)
- backend/app/area_geometry/models.py (`AreaModel`, `AreaVersionModel`)
- backend/app/area_geometry/area_repo.py (`SqlAlchemyAreaRepository`)
- backend/tests/evidence_ledger/ and backend/tests/claims_engine/ (153 tests)
- backend/app/domain/evidence_contracts.py (`EvidenceContract` with optional GeoJSON/SRID/spatial precision fields)
- backend/app/evidence_ledger/evidence_repo.py (`SqlAlchemyEvidenceRepository`)
- backend/app/evidence_ledger/audit_log.py (`SqlAlchemyEvidenceAuditLog`)
- docs/adr/lane-c-evidence.md
- backend/app/claims_engine/claim_repo.py (`SqlAlchemyClaimRepository`)
- backend/app/claims_engine/not_evaluated.py
- backend/tests/claims_engine/test_not_evaluated_claims.py
- backend/tests/evidence_ledger/test_evidence_schema_contract.py
- backend/tests/claims_engine/test_claim_schema_contract.py
- schemas/evidence_schema.json
- schemas/claim_schema.json
- docs/adr/lane-c-schemas.md
- docs/adr/lane-c-rules.md
- backend/app/reports/service.py
- backend/app/reports/models.py
- backend/app/reports/report_repo.py
- backend/app/reports/adapters.py
- docs/adr/lane-d-0001-report-persistence.md
- backend/tests/reports/test_report_repository.py (1 test)
- backend/tests/reports/test_adapters.py (4 tests)
- backend/tests/reports/ and backend/tests/api/ (20 tests)
- backend/tests/api/test_report_runs_db.py
- backend/tests/reports/test_report_regression.py
- schemas/report_run_schema.json
- backend/tests/reports/test_report_schema_contract.py
- docs/adr/lane-d-0010-report-manifest-metadata.md
- docs/adr/lane-d-0013-report-metadata-extension-boundary.md
- docs/adr/lane-d-0011-connector-human-review-actions.md
- docs/adr/lane-d-0014-connector-review-api-auth-blocker.md
- docs/adr/lane-d-0012-connector-human-review-api-semantics.md
- docs/adr/lane-d-0015-connector-reviewer-principal.md
- docs/adr/lane-d-0016-connector-review-action-route-subset.md
- docs/adr/lane-d-0017-report-validation-metadata.md
- docs/adr/lane-d-0018-job-schema-boundary.md
- docs/adr/lane-d-0019-connector-review-closeout-api.md
- backend/app/api/reviewer_auth.py
- backend/tests/api/test_reviewer_auth.py
- docs/planning_pack/api/openapi_stub.yaml
- backend/tests/test_planning_pack_schema_copies.py
- db/seeds/source_registry_seeds.py
- scripts/seed_sources.py
- docs/adr/lane-a-0001-provenance-model.md
- templates/data_source_license_review.md
- registers/data_source_registry.csv
- schemas/source_schema.json
- schemas/source_provenance_schema.json
- backend/tests/source_registry/test_source_schema_contract.py
- backend/tests/source_registry/test_source_provenance_schema_contract.py
- backend/tests/connectors/test_fixture_quality.py
- tests/fixtures/geometries/
- plans/2026-06-05-l10-production-hardening.md
- backend/Dockerfile
- .dockerignore
- docker-compose.yml
- backend/app/core/logging.py
- backend/app/core/metrics.py
- backend/app/api/metrics.py
- backend/app/api/rate_limit.py
- backend/app/source_registry/usage_rights.py
- backend/app/connectors/license_guard.py
- backend/app/connectors/nwi.py
- scripts/source_readiness.py
- scripts/live_connector_worker.py
- backend/tests/source_registry/test_source_readiness.py
- backend/tests/api/test_live_connector_worker.py
- docs/source-reviews/ds-002.md
- backend/app/reports/job_store.py (`SqlAlchemyAsyncReportJobStore`)
- backend/app/api/reports.py (`POST /report-runs/{report_run_id}/retry`)
- backend/tests/api/test_logging.py
- backend/tests/api/test_metrics.py
- backend/tests/api/test_rate_limit.py
- backend/tests/api/test_async_report_runs.py
- backend/tests/connectors/test_license_guard.py
- backend/tests/connectors/test_nwi_connector.py
- backend/tests/connectors/test_static_file_connector.py
- backend/tests/reports/test_job_store.py
- backend/app/api/operations.py
- backend/app/domain/job_health.py
- backend/tests/api/test_operations.py
- backend/tests/api/test_app_runtime_mode.py
- backend/tests/test_deployment_smoke_scripts.py
- scripts/run_deployment_smoke.ps1
- scripts/run_deployment_smoke.sh
- docs/runbooks/incident_response.md
- scripts/run_incident_rollback_check.ps1
- scripts/run_incident_rollback_check.sh
- backend/tests/test_incident_rollback_artifacts.py
- config/ops_alert_rules.yaml
- docs/runbooks/alerting.md
- scripts/run_alert_rules_check.ps1
- scripts/run_alert_rules_check.sh
- backend/tests/test_alerting_artifacts.py
- .github/workflows/ci.yml
- .github/dependabot.yml
- docs/runbooks/supply_chain.md
- scripts/run_supply_chain_check.ps1
- scripts/run_supply_chain_check.sh
- backend/tests/test_supply_chain_artifacts.py
- backend/requirements-prod.lock
- docs/sbom/backend-prod-sbom.json
- docs/runbooks/dependency_provenance.md
- scripts/run_provenance_check.ps1
- scripts/run_provenance_check.sh
- backend/tests/test_provenance_artifacts.py
- config/ops_cost_monitoring.yaml
- docs/runbooks/cost_monitoring.md
- scripts/run_cost_monitoring_check.ps1
- scripts/run_cost_monitoring_check.sh
- backend/tests/test_cost_monitoring_artifacts.py
- docs/planning_pack/api/openapi_stub.yaml
- backend/tests/api/test_report_runs_db.py
- scripts/run_backup_restore_check.ps1
- scripts/run_backup_restore_check.sh
- docs/runbooks/backup_restore.md
Next lowest-dependency task:
- Finish the interrupted tail cleanup: keep OSM/NOAA connector API tests in the repo test
  surface, keep release-readiness scripts/runbook aligned to Must `sources=8 ready=7
  blocked=1`, and run focused plus default verification.
- Next source-readiness expansion candidate: DS-022 Census TIGER/ACS, because it is public
  and non-vendor-blocked. Start with source review/terms/field policy before registry,
  seed, connector inventory, connector/API, or report changes.
- Remaining L10 hardening: DB-enabled local verifier proof, hosted auth/RBAC, secret-manager
  integration, key rotation, hosted log retention, billing reconciliation, image publication
  attestation, hosted deployment proof, hosted alerting, and recovery/ops drills.
Do not work on yet:
- Live connectors other than DS-001 USGS TNM, DS-002 FEMA NFHL, DS-003 SSURGO, DS-004 NWI,
  DS-005 USGS water monitoring, DS-006 EPA ECHO, DS-010 county GIS parcels (Chatham/Buncombe/Brunswick),
  DS-011 assessor (not-evaluated), DS-016 OSM road access, and DS-023 county zoning (Chatham/Brunswick
  UDO) unless source rights are reviewed and the work is explicitly bounded
- LLM summary generation (Level 10 scope)
- New jurisdictions or intents until the DS-002 connector slice or another registered/licensed live connector is implemented
- Paid APIs without explicit license review and plan approval
```


## Current objective

Harden the MVP workflow toward production operation while preserving the evidence-ledger-first spine:

```text
source registry -> area geometry -> evidence -> claim -> report run -> API response -> durable jobs/runtime packaging
```

## Active plan (overall)

`plans/2026-06-06-source-readiness-closure.md` is active for the current tail cleanup and
next source-readiness pass. The operator-complete surface plan remains completed history.

## 4-lane agent architecture (active)

This workspace uses 4 isolated agent lanes, each with dedicated scope, plans, and state files.
See `LANE_OWNERSHIP.md` for ownership boundaries.

| Lane | Scope | Active plan | State | Milestone gates |
|---|---|---|---|---|
| Lane A | Source Registry + DB Infrastructure | `plans/lane-a-2026-06-03-source-registry.md` | `state/lane-a-state.md` | L2-*, L3-* |
| Lane B | Area + Geometry Domain | `plans/lane-b-2026-06-03-area-geometry.md` | `state/lane-b-state.md` | L4-* |
| Lane C | Evidence Ledger + Claims Engine | `plans/lane-c-2026-06-03-evidence-claims.md` | `state/lane-c-state.md` | L5-*, L6-* |
| Lane D | Reports + API + Platform | `plans/lane-d-2026-06-03-reports-api-infra.md` | `state/lane-d-state.md` | L7-* |

**Each lane agent must read `LANE_OWNERSHIP.md` before any code change.**

## Key constraints

- Bottom-up implementation only.
- Postgres/PostGIS is system of record.
- Evidence-before-claim invariant is non-negotiable.
- No live data connectors before license/source registry/fixture tests.
- No UI or LLM work until the storage/evidence/claim/report spine works.
- Lane agents MUST NOT modify files owned by other lanes.

## Known blockers / undecided items

| Item | Status | Impact |
|---|---|---|
| MVP state/counties | Undecided | Do not hard-code jurisdiction-specific logic |
| Parcel vendor | Undecided | Use fixtures/public source registry only |
| Live connector credentials | Not required for DS-002 public FEMA NFHL; unavailable for commercial vendors | DS-002 may proceed to a bounded public live connector slice; vendor connectors remain blocked |
| Docker availability | Available | DB smoke now passes locally |
| Connector integration zone | Canonical in `LANE_OWNERSHIP.md` | CON-001 through CON-020 complete; next Level 8 connector pass needs selection |

## Last verified state

Dossier confidence band fix on 2026-06-11: `_confidence_band()` in `dossier.py` was
always returning `'low'` because structural NOT_EVALUATED UNKNOWN claims (5 domains:
soil_septic, parcels, resource_context, market_context, assessor; plus the
ZONING_NOT_SCREENED sentinel injected by `_with_zoning_sentinel_if_missing()` in
`service.py`) are always present in every report run regardless of whether any real
connector ran. Fixed by evidence-ID correlation: `_STRUCTURAL_DOMAINS` and
`_STRUCTURAL_EVIDENCE_CODES = frozenset({'ZONING_NOT_SCREENED'})` identify structural
evidence; UNKNOWN claims backed exclusively by structural evidence no longer reduce
confidence. Band now returns `'unknown'` (no non-structural evidence), `'medium'`
(non-structural evidence, no UNKNOWN claims), or `'low'` (non-structural evidence with
at least one UNKNOWN claim). Three new tests cover all three bands. 1310 tests
collected; committed `98afd51`.

Dossier Section 8 (Soil/Septic) SSURGO surfacing fix on 2026-06-11: Section 8 was
hardcoding "Soil map units: not evaluated" even when SSURGO evidence (domain
`soil_septic`, evidence code `SSURGO_SOIL_MAPUNIT_INTERSECTION`) was present. Added
`_soil_septic_result()` helper that reads `soil_mapunit_name`/`soil_mapunit_symbol`/
`soil_mapunit_key` observed_value keys and renders a deduplicated mapunit list; also
fixed `_domain_verification` and `_domain_caveats` calls from wrong domain string
`'soil'` to `'soil_septic'`. Added caveats line to Section 8. Two new tests
(`test_dossier_renders_ssurgo_mapunit_from_evidence`,
`test_dossier_renders_soil_source_failure_from_evidence`). 1228 tests pass, mypy
clean on 120 source files. Committed `9b40dd4`. DS-013 NC well logs blocked review
also committed (`ceff1b4`).

Latest DS-016/DS-005/DS-006 connector verification on 2026-06-11: three Should-priority
live connectors are implemented and all 1222 tests pass with mypy clean over 120 source
files. DS-016 OSM road access (`OsmRoadAccessConnector` via Overpass API) and DS-005 USGS
water monitoring (`UsgsWaterMonitoringConnector` via USGS NWIS REST) were committed as
`af940bf` and `77a8ece`. DS-006 EPA ECHO (`EpaEchoConnector` via EPA FRS REST, 3 req/min
rate limit, bbox-to-centroid+radius spatial query) promotes `env_hazard` from
NOT_EVALUATED_DOMAINS to a real evaluation domain: ENV_G001 now gates on
`env_hazard_facility_proximity` (severity=high), and two claims paths are generated
(proximity found → ENV_001; no proximity or failure → UNKNOWN/review claims). Payload
validation, connector inventory, live-connector orchestration, API route, openapi_stub,
source-readiness tests, and rule-engine tests are all updated. Source readiness: 7/8
Must (DS-017 remains blocked by vendor/license), 3 Should (DS-005, DS-006, DS-016)
connector-ready; 10/25 total connector-ready. Next-task candidates: DS-012 county
recorder source-rights review + connector (Should, county deeds/easements, NC counties),
DS-013 state well logs source-rights review + connector (Should, NC Division of Water
Resources), dossier/report surfacing of water/env_hazard/road-access claims, or
consolidating the job_repo.py idempotency path. DS-017 (Must, commercial parcel) and
DS-018 (Should, commercial comps) remain blocked by license/cost.

Latest batch-round-2 verification on 2026-06-10 (merged to `main`, PRs #23–#33): the
operator surface is merged and live on main, plus ten parallel units: source-rights
reviews for DS-005/006/010/011/016 (DS-010 county parcels — a previously blocked Must
source — is now approved-with-restrictions for Buncombe/Chatham/Brunswick NC), an
audit-event retention purge tool (closing the not_yet_automated retention blocker),
per-claim evidence identifiers in the dossier, a concurrent-user load-test scenario,
an executed live-connector smoke for a bounded Buncombe bbox (USGS TNM/NWI/SSURGO
succeeded with real evidence; FEMA NFHL recorded a first-class source failure; a real
SSURGO null-field bug was found and fixed), shared UI styling consolidation, and
Idempotency-Key support on POST /report-runs and /intake. Full DB-enabled
`.\scripts\verify.ps1` is green on merged main; every PR passed GitHub CI before
merge; attribution scan clean. Known CI caveat: `dependency-attestations` fails at the
attestation publish step on pull_request events (entitlement/OIDC boundary) while the
push-event run passes. Next-task candidates: Buncombe/Brunswick parcel connectors
(DS-010 restrictions permitting), DS-005/006 connectors for water/enviro context,
consolidating the unwired reports.report_runs idempotency mechanism (job_repo.py)
with the wired job-store path, and the hosted-production lane when infrastructure
exists.

Previous operator-surface verification on 2026-06-10 (branch
`worktree-prod-advance-20260610`): the operator web UI is now workflow-complete and
auth-consistent with the API. UI report approval requires reviewer credentials with
`report:approve` scope and records the authenticated reviewer in `reviewed_by` and
`review_actions` (the prior credential-free first-account approval path is removed —
this was a falsified-attribution audit defect). New approved-only export endpoints
serve the Markdown dossier as a download and the machine-readable JSON report artifact
(persisted artifact in DB mode) with a forbidden-phrase regression on the artifact body.
New UI surfaces: connector review queue list/detail with approve/reject/requeue/cancel
and resume-report actions (reviewer-scope model), pending-connector-review intake
surfacing, failed-report retry, operations queue-health dashboard, report list status
filter + pagination (plus a bounded `GET /report-runs` list endpoint and job-store
offset/status support in both implementations), evidence lineage page, and report
comparison page sharing the API's summary/parsing helpers.
`scripts/export_openapi_stub.py` now regenerates the planning-pack OpenAPI stub; the
parity test is environment-sensitive and must run under `py -3.12`. Full DB-enabled
`.\scripts\verify.ps1` passes with `RUN_DB_SMOKE=1` (suite grew from 871 to 975+ passed
tests); a three-lens adversarial review with per-finding re-verification confirmed 9
findings, all fixed. The UI targets the default trusted-network posture;
`REQUIRE_API_KEY=true` locks all `/ui` routes fail-closed (runbook documents this).
Next-task recommendation: live-connector exercise of the operator workflow end-to-end
against the three NC counties, source-rights review progress on the four blocked Must
sources (DS-010/011/017/023), or hosted-production lane items if infrastructure becomes
available.

Latest US-052 verification on 2026-06-05: reviewer-authenticated
`GET /operations/queue-health` is implemented for in-memory and DB-backed report/live
connector job stores. Full DB-enabled `.\scripts\verify.ps1` passes with
`RUN_DB_SMOKE=1`; 631 tests are collected; source-readiness remains
`sources=8 ready=4 blocked=4`; `git diff --check` reports only CRLF normalization
warnings on generated/state files; no repo Docker services or worker-run containers
remain running. Queue health is read-only and does not lease jobs, retry jobs, call live
sources, persist evidence, or create reports.

Latest US-053 verification on 2026-06-05: DB-backed deployment smoke automation is
implemented through `scripts/run_deployment_smoke.ps1` and
`scripts/run_deployment_smoke.sh`. `USE_DB_SERVICES` lets deployed `app.main:app` use
Postgres-backed services, and Compose opts into that mode with
`COMPOSE_USE_DB_SERVICES=true`. Final Windows deployment smoke passed after adding DB
readiness waiting and guarding repeated `rule_execution_report_fk` migration
application. Full DB-enabled `.\scripts\verify.ps1` passes with `RUN_DB_SMOKE=1`; 636
tests are collected; source-readiness remains `sources=8 ready=4 blocked=4`; the diff
whitespace check reports only CRLF normalization warnings on generated/state files; no
repo, smoke, or worker-run containers remain running. Deployment smoke validates local
Compose build/start, migrations/seeds, `/health`, `/version`, `/metrics`,
`/operations/queue-health`, and an area-to-report HTTP workflow.

Latest US-054 verification on 2026-06-05: incident response and rollback proof is
implemented through `docs/runbooks/incident_response.md`,
`scripts/run_incident_rollback_check.ps1`, and `scripts/run_incident_rollback_check.sh`.
The runbook names severity levels, owner roles, escalation criteria, deployment rollback,
database rollback/mitigation, connector outage handling, queue/report failure handling,
recovery criteria, and closure records. The Windows incident/rollback check passed, full
DB-enabled `.\scripts\verify.ps1` passes with `RUN_DB_SMOKE=1`; 638 tests are collected;
source-readiness remains `sources=8 ready=4 blocked=4`; the diff whitespace check reports
only CRLF normalization warnings on generated/state files; no repo, smoke, or worker-run
containers remain running. Production on-call identities, alert routing, hosted rollback
pipeline, and automated down migrations remain outside this proof.

Latest US-055 verification on 2026-06-05: repo-local alert rules are implemented through
`config/ops_alert_rules.yaml`, `docs/runbooks/alerting.md`,
`scripts/run_alert_rules_check.ps1`, and `scripts/run_alert_rules_check.sh`. The catalog
maps SEV0 safety-contract failure, SEV1 health/deployment/DB/restore failures, SEV2
metrics/queue/live-connector failures, source-readiness ready-count drops, and stale
source-registry `Last Checked At` metadata to owners, escalation, runbooks, and validation
proofs. The Windows alert-rules check passed, full DB-enabled `.\scripts\verify.ps1`
passes with `RUN_DB_SMOKE=1`; 642 tests are collected; source-readiness remains
`sources=8 ready=4 blocked=4`; the diff whitespace check reports only CRLF normalization
warnings on generated/state files; no repo, smoke, or worker-run containers remain
running. Hosted alert routing, dashboards, pager delivery, a named on-call rotation, and
independent real-time upstream dataset freshness verification remain outside this proof.

Latest US-056 verification on 2026-06-05: CI supply-chain dependency vulnerability
scanning and update hygiene are implemented through `.github/workflows/ci.yml`,
`.github/dependabot.yml`, `docs/runbooks/supply_chain.md`,
`scripts/run_supply_chain_check.ps1`, and `scripts/run_supply_chain_check.sh`. The CI
workflow now has a `supply-chain` job that installs the backend dependency environment
and runs `pip-audit --local`; Dependabot requests weekly checks for GitHub Actions and
backend Python dependency metadata. The Windows supply-chain check passed, full
DB-enabled `.\scripts\verify.ps1` passes with `RUN_DB_SMOKE=1`; canonical mypy is clean
over 175 source files. At the US-056 point, a production dependency lockfile, signed
SBOM, SLSA provenance attestation, Docker base-image package scan, and GitHub Actions
runtime attestation remained outside that proof; US-058 later added the repo-local
production lock/SBOM proof, and US-059 later added the repo-local container image scan
proof.

Latest US-058 verification on 2026-06-05: backend production dependency provenance is
implemented through `backend/requirements-prod.lock`, `docs/sbom/backend-prod-sbom.json`,
`docs/runbooks/dependency_provenance.md`, `scripts/run_provenance_check.ps1`,
`scripts/run_provenance_check.sh`, and `backend/tests/test_provenance_artifacts.py`.
The lock pins the CPython 3.12 manylinux backend runtime dependency closure with
SHA-256 hashes, the repo-local CycloneDX SBOM mirrors that component set, and the CI
`supply-chain` job now runs the provenance proof before `pip-audit --local`. The Windows
provenance proof, updated supply-chain proof, focused tests, ruff, mypy, PowerShell
parser validation, and full DB-enabled `.\scripts\verify.ps1` passed; 653 tests are
collected and canonical mypy is clean over 177 source files. Signed/published SBOM,
SLSA provenance attestation, Docker base-image scanning, and GitHub Actions runtime
attestation remained outside the US-058 proof; US-059 later added the repo-local
container image scan proof.

Latest US-059 verification on 2026-06-05: backend container image/base-image
vulnerability scanning is implemented through the CI `container-image-scan` job,
`docs/runbooks/container_image_scan.md`, `scripts/run_container_scan_check.ps1`,
`scripts/run_container_scan_check.sh`, and
`backend/tests/test_container_scan_artifacts.py`. The CI job builds
`backend/Dockerfile` into `land-diligence-backend:${{ github.sha }}` and runs
`docker/scout-action@v1` with `command: cves`, `local://` image resolution,
`only-severities: critical,high`, and `exit-code: true`. The Windows container scan
proof, updated supply-chain proof, focused tests, ruff, mypy, PowerShell parser
validation, and full DB-enabled `.\scripts\verify.ps1` passed; 657 tests are collected
and canonical mypy is clean over 178 source files. Digest-pinned base images remained
outside the US-059 proof; US-060 later added the repo-local digest-pinned backend
base-image proof. Published-registry image attestation, signed image SBOM, SLSA
provenance attestation, hosted deployment runtime scanning, GitHub Actions runtime
attestation, and source/vendor rights remain outside this proof.

Latest US-060 verification on 2026-06-05: the backend Docker runtime base image is pinned
by OCI index digest in `backend/Dockerfile`:
`python:3.12-slim@sha256:090ba77e2958f6af52a5341f788b50b032dd4ca28377d2893dcf1ecbdfdfe203`.
The digest was verified from live `docker buildx imagetools inspect python:3.12-slim`
output before editing. The Windows container scan proof, focused tests, ruff, mypy, an
actual pinned `docker build`, and full DB-enabled `.\scripts\verify.ps1` passed;
canonical mypy remains clean over 178 source files. Published-registry image
attestation, signed image SBOM, SLSA provenance attestation, hosted deployment runtime
scanning, GitHub Actions runtime attestation, and source/vendor rights remain outside
this proof.

Latest US-061 verification on 2026-06-05: GitHub dependency lock/SBOM artifact
attestations are wired through the CI `dependency-attestations` job. The job validates
dependency provenance first, then uses `actions/attest@v4` with `id-token: write`,
`attestations: write`, and `artifact-metadata: write` to create a provenance
attestation for `backend/requirements-prod.lock` and `docs/sbom/backend-prod-sbom.json`,
plus an SBOM attestation binding `docs/sbom/backend-prod-sbom.json` to the production
lock subject. The Windows provenance proof, supply-chain proof, focused tests, ruff,
mypy, PowerShell parser validation, and full DB-enabled `.\scripts\verify.ps1` passed;
canonical mypy remains clean over 178 source files. Release package, hosted deployment,
published registry-image attestation, GitHub Actions runtime attestation, and
source/vendor rights remain outside this proof.

Latest US-062 verification on 2026-06-05: report `artifact_metadata.cost_metrics` now
requires and emits explicit zero-dollar attribution fields for current local-only paths:
`estimated_total_usd_cents`, `compute_usd_cents`, `storage_usd_cents`,
`llm_usd_cents`, `map_tile_usd_cents`, `geocoding_usd_cents`,
`paid_data_usd_cents`, `human_review_usd_cents`, and `human_review_minutes`.
The report repository fills missing attribution defaults for older/custom metadata on
persistence while preserving extension fields. The Windows cost-monitoring proof,
focused report schema/service/repository/regression/API tests, ruff, mypy, PowerShell
parser validation, and full DB-enabled `.\scripts\verify.ps1` passed; 659 tests are
collected, canonical mypy remains clean over 178 source files, source readiness remains
`sources=8 ready=4 blocked=4`, and no Docker services or worker-run containers remain
running. Hosted billing reconciliation, approved nonzero unit-cost thresholds, paid
vendor metering, LLM metering, map/geocoding metering, and durable reviewer-time capture
remain outside this proof.

Latest US-063 verification on 2026-06-05: `config/release_readiness.yaml` now gathers
the repo-local release gates for workspace verification, DB verification, deployment
smoke, dependency provenance, supply-chain scanning, dependency attestations, container
image scanning, backup/restore, incident/rollback, alerting, cost monitoring, and
source readiness. `scripts/run_release_readiness_check.ps1` and `.sh` validate the
catalog, CI `release-readiness` job, current Must-source readiness counts, and explicit
release blockers. The Windows release-readiness proof, focused artifact tests, ruff,
mypy, PowerShell parser validation, and full DB-enabled `.\scripts\verify.ps1` passed;
664 tests are collected, canonical mypy is clean over 179 source files, source readiness
remains `sources=8 ready=4 blocked=4`, and no Docker services or worker-run containers
remain running. Release package creation, pushed registry image, hosted deployment,
published registry-image attestations, hosted billing reconciliation, blocked source
approval, full user auth/RBAC, and hosted alerting remain outside this proof.

Latest US-064 verification on 2026-06-05: `config/access_control.yaml` now records
current default-off API-key middleware, local reviewer service-account auth,
reviewer-authenticated operator routes, intentionally public health/version routes, and
production auth/RBAC blockers. `scripts/run_access_control_check.ps1` and `.sh`
validate the catalog, referenced auth authority files, failure-mode test coverage,
protected-route reviewer dependencies, `access-control` CI job, and runbook limits. The
Windows access-control proof, release-readiness proof, focused artifact/auth tests, ruff,
mypy, PowerShell parser validation, and full DB-enabled `.\scripts\verify.ps1` passed;
668 tests are collected, canonical mypy is clean over 180 source files, source readiness
remains `sources=8 ready=4 blocked=4`, and no Docker services or worker-run containers
remain running. Full user auth/RBAC, OAuth/OIDC, user accounts, key rotation, hosted
identity-provider integration, and role-scoped authorization remain outside this proof.

Latest US-065 verification on 2026-06-05: protected operator routes now enforce scoped
local reviewer service-account authorization. `REVIEWER_ACCOUNT_SCOPES` is required for
custom reviewer accounts; connector invocation/scheduling requires `connector:run`,
connector review decisions require `connector:review`, queue/live-job health reads
require `operations:read`, failed-report retry requires `report:retry`, and manual
approved-connector report creation requires `report:run`. The Windows access-control
proof, release-readiness proof, focused scoped-auth tests, ruff, mypy, PowerShell parser
validation, Compose config, and full DB-enabled `.\scripts\verify.ps1` passed; 680 tests
are collected, canonical mypy is clean over 180 source files, source readiness remains
`sources=8 ready=4 blocked=4`, auth-overclaim search has no matches, and no Docker
services or worker-run containers remain running. This is a scoped local service-account
authorization substrate, not full user auth/RBAC, OAuth/OIDC, user accounts, key
rotation, or hosted identity-provider authorization.

Latest US-066 verification on 2026-06-05: local release package creation is now
implemented through `config/release_package.yaml`, `scripts/build_release_package.ps1`,
`scripts/build_release_package.sh`, and validate-only package proofs. A clean package
build produced `local_artifacts/releases/land-diligence-us066-20260606T013648Z.zip`
and `local_artifacts/releases/land-diligence-us066-20260606T013648Z-release-manifest.json`
with 220 files, an embedded manifest, no `.git`, no `local_artifacts`, and no secret-like
`.env` files beyond allowed `.env.example`. Full DB-enabled `.\scripts\verify.ps1`
passed after the package slice; 684 tests are collected, canonical mypy is clean over
181 source files, source readiness remains `sources=8 ready=4 blocked=4`, and no Docker
services or worker-run containers remain running. Pushed registry images, hosted
deployment, registry-image attestations, signed image SBOM, SLSA provenance, hosted
billing reconciliation, and blocked-source approval remain outside this proof.

Latest US-067 verification on 2026-06-05: registry image publication readiness is now
cataloged through `config/image_publication.yaml`, `docs/runbooks/image_publication.md`,
`scripts/run_image_publication_check.ps1`, `scripts/run_image_publication_check.sh`, and
`backend/tests/test_image_publication_artifacts.py`. The proof is wired into
`config/release_readiness.yaml`, the read-only `image-publication` CI job, release
readiness proofs, `docs/runbooks/mvp_operator.md`, `MANIFEST.md`, and this plan/state
set. Full DB-enabled `.\scripts\verify.ps1` passed after the image publication slice;
689 tests are collected, canonical mypy is clean over 182 source files, source readiness
remains `sources=8 ready=4 blocked=4`, `git diff --check` reports only CRLF warnings on
generated/state files, and no Docker services or worker-run containers remain running.
This is a validate-only publication-readiness boundary; it does not push a registry
image, create hosted deployment, sign an image SBOM, publish SLSA provenance, or attach
registry-image attestations.

Latest US-068 verification on 2026-06-05: hosted deployment readiness is now
cataloged through `config/hosted_deployment.yaml`,
`docs/runbooks/hosted_deployment.md`, `scripts/run_hosted_deployment_check.ps1`,
`scripts/run_hosted_deployment_check.sh`, and
`backend/tests/test_hosted_deployment_artifacts.py`. The proof is wired into
`config/release_readiness.yaml`, the read-only `hosted-deployment` CI job,
release readiness proofs, `docs/runbooks/mvp_operator.md`, `MANIFEST.md`, and this
plan/state set. Full DB-enabled `.\scripts\verify.ps1` passed after the hosted
deployment readiness slice; 694 tests are collected, canonical mypy is clean over
183 source files, source readiness remains `sources=8 ready=4 blocked=4`, and no
Docker services or worker-run containers remain running. This is a validate-only
hosted deployment readiness boundary; it does not provision infrastructure,
publish a registry image, deploy the service, configure DNS/TLS, attach hosted
identity, or enable hosted alerting.

Latest US-069 verification on 2026-06-05: API-key and local reviewer
service-account secrets now accept raw local values or normalized
`sha256:<64-hex>` configured secret specs through the shared
`backend/app/api/secret_specs.py` helper. `API_KEYS` and `REVIEWER_ACCOUNTS`
parsing now fail closed for blank or malformed hash specs, compare configured
hashes using SHA-256 plus constant-time comparison, keep raw fixture secrets
available for local use, and update access-control catalogs/runbooks/proofs to
document the boundary. The Windows access-control proof, release-readiness proof,
focused auth tests, ruff, mypy, and full DB-enabled `.\scripts\verify.ps1` passed
after the hashed secret specs slice; 704 tests are collected, canonical mypy is
clean over 184 source files, migrations/seeds apply, and DB smoke passes. This is
not key rotation, user accounts, OAuth/OIDC, hosted identity, or full RBAC.

Latest US-070 verification on 2026-06-05: `API_KEY_SPECS` now provides a configured
static API-key lifecycle substrate with comma-separated `id|status|secret` entries.
Only `active` specs authenticate; `retired` specs do not; secrets may be raw or
`sha256:<64-hex>`; malformed status, duplicate IDs, duplicate secrets, and malformed
hashes fail closed during settings parsing. The access-control catalog now records
`api_key_rotation` as an implemented configured static lifecycle control and keeps
`automatic_api_key_rotation` blocked. `.env.example`, Compose, hosted deployment
readiness, access-control proofs, hosted-deployment proofs, and operator runbooks expose
the runtime knob without adding hosted secret writes. Focused API-key lifecycle tests,
access-control and hosted-deployment artifact tests, access-control proof,
hosted-deployment proof, focused ruff, and focused mypy passed before full verification.
This is not automatic rotation, external secret-manager integration, per-key usage
audit, user accounts, OAuth/OIDC, hosted identity, or full RBAC.

Latest US-071 verification on 2026-06-05: protected-path API-key auth now emits
structured runtime audit log events for accepted, missing, invalid, and unconfigured
decisions. Events include `event_type=api_key_auth`, outcome, status code, method, path,
auth source, and configured `api_key_id` for accepted `API_KEY_SPECS` credentials; they
do not include the provided key, configured secret, or query string. The access-control
catalog now records `api_key_audit_logging` as implemented structured runtime logs.
Focused API-key auth/access-control tests, access-control proof, focused ruff, focused
mypy, release-readiness proof, and full DB-enabled `.\scripts\verify.ps1` passed after
this slice; 718 tests are collected, canonical mypy is clean over 184 source files,
migrations/seeds apply, and DB smoke passes. This is not a durable database audit
ledger, hosted log-retention system, automatic rotation, external secret-manager
integration, user accounts, OAuth/OIDC, hosted identity, or full RBAC.

Latest US-072 verification on 2026-06-05: protected-path API-key auth now records
accepted, missing, invalid, and unconfigured decisions through an optional API-key auth
audit sink. In DB-service mode, the SQLAlchemy sink writes those decisions to existing
`audit.events` rows with `event_type=api_key_auth` and `target_table='api.api_key_auth'`.
The middleware fails closed with 503 if configured audit persistence fails, and the
runtime log plus DB-event payloads still exclude provided keys, configured secrets, and
query strings. Focused API-key auth/access-control tests, access-control proof, focused
ruff, and focused mypy passed before full verification. This is not hosted log retention,
SIEM export, automatic rotation, external secret-manager integration, user accounts,
OAuth/OIDC, hosted identity, or full RBAC.

Latest US-073 through US-082 verification on 2026-06-05: load test baseline (scripts/run_load_test.ps1/.sh, docs/runbooks/load_testing.md), security static analysis CI gate (scripts/run_security_scan.ps1/.sh, bandit 0 HIGH/CRITICAL, security-scan CI job), data retention policy catalog (config/data_retention.yaml with 7 classes, docs/runbooks/data_retention.md), jurisdiction and rulepack readiness checklists (docs/checklists/jurisdiction_readiness.md, docs/checklists/rulepack_readiness.md), DB connection pool explicit configuration (DB_POOL_SIZE/MAX_OVERFLOW/TIMEOUT/RECYCLE in config.py, conditional pool kwargs in engine.py), performance runbook (docs/runbooks/performance.md covering cache, batch controls, spatial indexes, backpressure), report lineage endpoint (GET /report-runs/{id}/lineage), candidate comparison endpoint (GET /report-runs/compare), and report rerun diff endpoint (GET /report-runs/{id}/diff) are implemented. Full `py -3.12 -m pytest` passes with 794 passed and 63 skipped (DB-layer); ruff clean; mypy clean over 216 source files. `config/release_readiness.yaml` now has 22 required_checks entries. The MANIFEST.md references docs/checklists/. Remaining L10 blockers: full user auth/RBAC, hosted deployment, hosted billing, hosted log retention, automatic key rotation, non-ready Must sources.

Level 10 partial hardening verified 2026-06-05 on local `main`: settings-backed scoped reviewer auth, production API-key middleware with raw-or-sha256 configured secrets, configured static API-key lifecycle specs, and structured API-key auth audit logs plus DB-backed API-key auth events, default-off fixed-window rate limiting, backend Docker/Compose service, JSON runtime logging, structured runtime metrics, container build/runtime smoke, fail-closed connector source-use preflight, source-readiness audit reporting, reviewed source-rights candidates (DS-001 USGS The National Map, DS-002 FEMA NFHL, DS-003 USDA Web Soil Survey/SSURGO, and DS-004 National Wetlands Inventory), bounded DS-001 USGS TNM EPQS connector-layer terrain-relief screening plus controlled DS-001 API/operator invocation, explicit durable DS-001 live connector scheduling, and request-time DS-001 orchestration, bounded DS-002 FEMA NFHL live connector, bounded DS-003 USDA SSURGO connector plus controlled DS-003 API/operator invocation, explicit durable DS-003 live connector scheduling, and request-time DS-003 report integration with an UNKNOWN SSURGO screening-review claim, bounded DS-004 National Wetlands Inventory connector, controlled DS-002 API/operator invocation, controlled DS-004 API/operator invocation, explicit durable DS-002 and DS-004 live connector scheduling, read-only live connector job status API, bounded supervised live connector worker command, opt-in Compose live connector worker profile, connector review closeout actions, durable connector reviewer action history, approved connector evidence report gating, DB-backed connector approval-to-report regressions, request-time DS-001, DS-002, DS-004, and DS-003 orchestration for intake/report-run flows, file-backed DS-004 raw response fixture corpus, API 422 deprecation cleanup, live connector sequence scheduling, failed report job retry with lineage, backup/restore proof, repo-local alert-rule catalog with validate-only proof, CI supply-chain dependency vulnerability scanning and update hygiene, backend production dependency lock/SBOM provenance proof, backend dependency lock/SBOM artifact attestation proof, backend container image/base-image scan proof, digest-pinned backend Docker base-image proof, repo-local cost monitoring catalog with validate-only guardrails and report zero-dollar cost attribution, repo-local release readiness catalog with validate-only proof, local release package ZIP/manifest builder with validate-only proof, repo-local image publication readiness catalog with validate-only proof, repo-local hosted deployment readiness catalog with validate-only proof, repo-local access-control posture catalog with validate-only proof, scoped local reviewer authorization with raw-or-sha256 configured service-account tokens for protected operator routes, explicit post-approval connector report resume, SQLAlchemy source placeholder URL hardening, and Postgres-backed async report job state are implemented. Full DB-enabled `.\scripts\verify.ps1` passes with `RUN_DB_SMOKE=1` after the DB-backed API-key auth audit-event slice; 722 tests are collected; ruff is clean and canonical mypy is clean over 185 source files; migrations/seeds apply; DB smoke passes. Backend image build passes with the pinned base image; Compose runtime smoke serves `/health`, `/version`, and `/metrics`. Source-readiness audit reports current `Must` sources as `sources=8 ready=4 blocked=4`; DS-001 is approved-with-restrictions plus implemented as a bounded connector-layer EPQS terrain-relief screening slice with controlled API/operator invocation, durable scheduling, and request-time orchestration, DS-002 is approved-with-restrictions for bounded FEMA NFHL screening use, DS-003 is approved-with-restrictions plus implemented as a bounded connector-layer SSURGO mapunit/component screening slice with immediate, durable queued-worker, and request-time report paths, DS-004 is approved-with-restrictions for wetland/deepwater screening source-rights use only, and the SQL seed refreshes first-class DS-001/DS-002/DS-003/DS-004 usage-rights fields on re-seed. The DS-001 connector samples the official USGS TNM EPQS JSON service at the bbox center and corners with EPSG:4326 coordinates, emits one low-confidence terrain-relief `DERIVED_METRIC` for screening, emits source-failure evidence for no-data/error/malformed cases, and reuses existing retrieval provenance plus evidence-ingestion adapters. The reviewer-authenticated DS-001 route at `POST /connector-runs/usgs-tnm/query-bbox` invokes the bounded connector, records retrieval provenance, persists terrain-relief derived metric or source-failure evidence, and enqueues connector review status. `POST /connector-runs/usgs-tnm/schedule-bbox` enqueues durable DS-001 `live_connector_run` jobs without fetching EPQS or creating reports; the shared worker leases by `source_registry_id`, executes the existing DS-001 orchestration, and records the resulting connector review item. When `ENABLE_LIVE_CONNECTORS=true`, `/intake` and `/report-runs` run bounded DS-001 first, returning `pending_connector_review` until DS-001 approval before advancing to DS-002, DS-004, and DS-003; approved DS-001 evidence may enter reports as buildability-domain terrain screening evidence, but DS-001 still does not add DEM downloads, survey-grade elevation, engineering, site-plan, legal, buildability, lending, appraisal, investment conclusions, or a DS-001-specific claim. The DS-002 connector is implemented with reviewer-authenticated immediate, request-time, and queued-worker paths that record retrieval provenance, persist evidence, enqueue review status, support authenticated review closeout with queue-payload action history, and gate report use of connector-lineage evidence on succeeded `approve_for_connector_qa` queue state. The DS-003 connector/API/scheduler/request-time slice uses official USDA NRCS Soil Data Access `post.rest` with `JSON+COLUMNNAME` output and the documented WGS84 WKT mapunit-intersection function, exposes reviewer-authenticated immediate operator invocation at `POST /connector-runs/ssurgo/query-bbox`, records retrieval provenance, persists ledger-safe soil/septic/ag screening evidence or source-failure evidence, supports explicit durable scheduling at `POST /connector-runs/ssurgo/schedule-bbox`, and participates in request-time `/intake` and `/report-runs` after DS-004 approval. Approved DS-003 evidence can produce only an UNKNOWN `SOIL_NOT_EVALUATED` professional-review claim; it still has no pAOI state, WSS interpretation/rating execution, or final septic/soil-suitability/buildability conclusions. The DS-004 connector is implemented with reviewer-authenticated immediate, queued-worker, and request-time paths: `POST /connector-runs/nwi/query-bbox` runs the official USFWS-linked Wetlands ArcGIS REST layer 0 with EPSG:4326 bbox/feature limits immediately, and `POST /connector-runs/nwi/schedule-bbox` enqueues durable `live_connector_run` jobs without fetching NWI or creating reports. `GET /connector-runs/live-jobs/{job_id}` returns durable live connector job state without mutating, leasing, retrying, fetching, or scheduling reports. The shared worker dispatches by `source_registry_id`, executes existing DS-001, DS-002, DS-003, or DS-004 orchestration, records provenance, persists evidence, enqueues review status, and can feed the existing approved connector report-resume path without re-fetching live sources where report integration exists. DS-004 still has no source-specific autonomous scheduling policy. File-backed raw NWI fixtures now cover representative DS-004 success and empty-response source-failure behavior. API route validation/error paths now use the current FastAPI/Starlette 422 status constant name without changing the wire-level 422 status code. `POST /connector-runs/live-sequence/schedule-bbox` now enqueues the reviewed DS-001, DS-002, DS-004, and DS-003 durable live connector jobs for a registered area without fetching live sources, persisting evidence, approving review, or creating reports; its request body uses a source-neutral bbox schema rather than a FEMA-specific public model. `POST /report-runs/{report_run_id}/retry` now lets authenticated reviewers with `report:retry` create a new queued report job from a failed report job while preserving the failed job and recording `retry_of_report_run_id` lineage in in-memory and DB-backed job stores. `scripts/run_backup_restore_check.ps1` and `scripts/run_backup_restore_check.sh` now provide a Level 10 backup/restore proof that dumps the configured source DB, restores into a dedicated `land_diligence_restore_check*` database, runs `scripts/db_smoke_check.py` against the restored database, and drops the restore DB by default. The supply-chain CI job validates the backend production dependency lock/SBOM, installs the backend dependency environment, and runs `pip-audit --local`; the dependency-attestations CI job publishes GitHub artifact attestations for the production lock/SBOM files and an SBOM attestation binding the CycloneDX SBOM to the lock subject; the container-image scan CI job builds the backend image locally from a digest-pinned base image and scans it with Docker Scout for critical/high CVEs; the access-control CI job validates the repo-local access posture catalog; the hosted-deployment CI job validates the repo-local hosted deployment readiness boundary without provisioning infrastructure; the image-publication CI job validates the repo-local registry publication boundary without registry login, push, signing, or deployment; the release-readiness CI job validates the repo-local release gate catalog; Dependabot checks GitHub Actions and backend Python dependency metadata weekly. The repo-local cost monitoring catalog covers compute, storage, LLM-if-used, maps, geocoding, and data vendors, and the validate-only proof checks report `cost_metrics` counts plus zero-dollar attribution fields, planning cost inputs, alert integration, and DS-017 blocked vendor status. The repo-local release readiness catalog gathers verification, DB, deployment smoke, dependency provenance, supply-chain, dependency attestation, container scan, backup/restore, incident, alerting, cost, access-control, release-package, image-publication, hosted-deployment, and source-readiness gates while preserving release blockers for registry image publishing, hosted deployment, billing reconciliation, non-ready sources, full user auth/RBAC, and hosted alerting. The repo-local access-control catalog records current API-key middleware with raw-or-sha256 configured secrets, configured static API-key lifecycle specs, structured API-key auth audit logs, DB-service-mode API-key auth events in `audit.events`, scoped local reviewer service-account auth with raw-or-sha256 configured tokens, protected operator-route scope posture, intentionally public health/version routes, and production auth/RBAC blockers without adding full user identity, OAuth/OIDC, automatic key rotation, hosted log retention, or hosted identity-provider authorization. `docs/runbooks/mvp_operator.md` now documents reviewed live connectors, repo-local alert rules, CI supply-chain checks, dependency provenance guardrails, dependency artifact attestation guardrails, container image scan guardrails, digest-pinned base-image guardrails, cost-monitoring guardrails, scoped access-control guardrails, release-package guardrails, image-publication guardrails, hosted-deployment guardrails, and release-readiness guardrails as bounded, screening-only/review-gated or validate-only operator flows instead of describing the current app as fixture-only/no-auth. The approval-to-report operator sequence is proven in both in-memory and DB-backed API service configurations. When `ENABLE_LIVE_CONNECTORS=true`, `/intake` and `/report-runs` run bounded DS-001 first, bounded DS-002 after DS-001 approval, bounded DS-004 after DS-002 approval, and bounded DS-003 after DS-004 approval, returning `pending_connector_review` without creating report jobs until each connector review item is approved. Operators should keep the returned `area_id` and continue with `/report-runs` to complete the full request-time sequence; `POST /connector-runs/{ingest_run_id}/report-runs` remains the explicit manual one-connector report path and now requires `report:run`. Remaining Level 10 work is remaining non-DS-001/DS-002/DS-003/DS-004 source reviews, hosted billing integration and deeper spend controls, hosted log retention, automatic key rotation, external secret-manager integration, full user auth/RBAC, hosted deployment / published image attestation, any future DS-001 advanced terrain/report semantics beyond approved screening evidence, and any future DS-004 source-specific autonomous scheduling work.

Latest CI gate correction on 2026-06-06: current `origin/main` was locally green on
Windows but not CI-clean because GitHub Actions invoked tracked POSIX scripts that were
not executable, the `security-scan` job bypassed the documented wrapper and failed on
medium Bandit findings, and Docker Scout failed before scanning because the repository
had no Docker Scout entitlement. The corrective slice tracks `scripts/*.sh` as
executable, runs `./scripts/run_security_scan.sh` from CI so the gate fails on
HIGH/CRITICAL while reporting medium findings, fixes the Windows security-scan wrapper
to use Python 3.12, and makes `container-image-scan` build the image while recording the
live Docker Scout CVE scan as blocked unless `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN`
are configured. This does not prove the container image is CVE-clean without Docker
Scout entitlement; it makes the blocked state explicit instead of silently overclaiming
or hard-failing every PR. Focused artifact tests, workflow YAML parsing, container-scan
static proof, release-readiness proof, and the security-scan wrapper pass. Remaining
review debt includes unresolved merged-PR threads, source-rights blockers
`DS-010`/`DS-011`/`DS-017`/`DS-023`, Bandit medium findings, and hosted production
blockers.

PR #19 remote CI follow-up on 2026-06-06 corrected additional CI-only failures: DB
migrations now run before DB-gated backend tests in `verify.ps1`/`verify.sh`,
`supply-chain` installs `PyYAML` before POSIX provenance validation, `release-readiness`
installs backend dependencies before source-readiness validation, and
`dependency-attestations` records private-repository GitHub attestation entitlement as a
blocked live attestation instead of claiming publication or hard-failing. GitHub
artifact attestations remain a real release blocker until repository visibility/plan
supports them; the lock/SBOM provenance artifacts still validate locally and in CI.
After the follow-up, PR #19 remote CI passed all configured jobs, including DB-enabled
verification.

Review-debt closeout pass on 2026-06-06 landed via PR #20 after PR and main CI passed.
Live defects from unresolved merged-PR review threads were patched
for source retrieval count validation, source-provenance review-bundle schema parity,
flood fixture quality fail-closed checks, fixture workflow quality gating before
side effects, source-failure evidence provenance preservation, raw
`SourceProvenanceService` retrieval adapter compatibility, atomic SQL connector review
queue enqueue, primary connector review-action OpenAPI required-reason parity, and
Windows API runner `OBJECT_STORE_ROOT` preservation. Focused pytest, ruff, mypy,
OpenAPI parity, `git diff --check`, full `.\scripts\verify.ps1`, post-merge detached
verification, and main CI passed for touched surfaces. Follow-up PR #20 review threads
then identified three remaining live issues now handled in an isolated follow-up:
connector review queue cross-workspace idempotency collisions fail closed instead of
returning another workspace item, source-provenance review bundles embed the strict
`SourceContract` schema, and reason-required primary review actions now require a
non-null request body in OpenAPI/runtime signatures. Focused pytest, ruff, mypy, and
full `.\scripts\verify.ps1` pass for that follow-up; DB smoke remains skipped locally
unless `RUN_DB_SMOKE=1`. Must-source readiness remains `sources=8 ready=4 blocked=4`
with `DS-010`, `DS-011`, `DS-017`, and `DS-023` blocked.

## Active lane: Source Readiness Closure (2026-06-07)

Goal: keep source-readiness truth aligned with live repo evidence, complete interrupted
OSM/NOAA/release-readiness tail cleanup, continue public-source readiness passes, and
choose the next source pass without overclaiming private MVP or Level 10 production
readiness.

Current state:

| Item | Status | Evidence |
|---|---|---|
| DB-enabled local verifier | separate proof | Run `$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1` only when PostgreSQL/PostGIS prerequisites are available; default verify does not prove DB smoke |
| DS-007 BLM MLRS | connector-ready | Active federal mining-claim geospatial context only; no private mineral-rights, claim-boundary, title, mine-hazard, resource-value, extraction, environmental-liability, buildability, appraisal, lending, insurance, or investment conclusion claimed |
| DS-008 USGS MRDS | connector-ready | Historical mineral-occurrence screening only; no mineral-rights, hazard, resource-value, extraction, environmental-liability, buildability, appraisal, lending, insurance, or investment conclusion claimed |
| DS-011 County assessor | connector-ready as not-evaluated evidence | `AssessorNotEvaluatedConnector.query_area()` records explicit ASSESSOR_NOT_EVALUATED SOURCE_FAILURE evidence; this is not live assessor data |
| DS-015 State geological survey | connector-ready | NCGS 1985 statewide geologic map-unit context only; deprecated, generalized map scale; no hazard, mineral-resource, engineering, buildability, appraisal, lending, insurance, or investment conclusion claimed |
| DS-017 Commercial parcel vendor | blocked | Vendor/license/cost decision deferred; not required for private MVP |
| DS-020 NOAA NWS climate/weather | connector-ready | Bounded point/forecast-zone connector; administrative weather-zone context only, not climate normals or agricultural risk conclusions |
| DS-022 Census TIGER/ACS | connector-ready | Bounded TIGERweb tract/block-group geography context only; ACS demographic variables, protected-class analytics, neighborhood desirability, market/investment/lending suitability, and residential steering are excluded |
| DS-023 Local zoning ordinance PDFs | connector-ready, wired | Recorded-fixture zoning district connectors for reviewed county UDO tables; no live PDF retrieval or legal zoning conclusion claimed |
| DS-023 orchestration wiring | complete | Chatham/Brunswick zoning recorded-fixture orchestration and operator routes wired |
| DS-010 Buncombe parcel connector | complete | `buncombe_parcels.py`; ArcGIS property_bc_dis MapServer/1; pinnum/Acreage (no zoning field); county dispatch via centroid bounds |
| DS-010 Brunswick parcel connector | complete | `brunswick_parcels.py`; ArcGIS TaxParcels FeatureServer/0; PIN/CALCAC/Zoning; county dispatch; zoning available |
| DS-010 county dispatch | complete | `_classify_area_county()` with NC coordinate bounds; Buncombe/Brunswick orchestration functions wired; API routes added |
| Source readiness gate | hardened | `scripts/source_readiness.py` now reports `production_use_allowed`, `connector_implemented`, `connector_surfaces`, and `connector_ready` separately |

Key artifacts:
- `plans/2026-06-06-source-readiness-closure.md`
- `docs/source-reviews/ds-011.md`
- `docs/source-reviews/ds-023.md`
- `docs/source-reviews/ds-023-chatham-live-scope.md`
- `backend/app/source_registry/connector_inventory.py`
- `backend/app/api/live_connectors.py`
- `backend/app/api/connectors.py`
- `backend/app/connectors/__init__.py`
- `backend/app/connectors/usgs_mrds.py`
- `docs/source-reviews/ds-008.md`
- `backend/tests/api/test_usgs_mrds_connector_api.py`
- `backend/tests/connectors/test_usgs_mrds_connector.py`
- `backend/app/connectors/nc_geologic_map.py`
- `docs/source-reviews/ds-015.md`
- `backend/tests/api/test_nc_geologic_map_connector_api.py`
- `backend/tests/connectors/test_nc_geologic_map_connector.py`
- `backend/app/connectors/census_tiger.py`
- `docs/source-reviews/ds-022.md`
- `backend/tests/api/test_census_tiger_connector_api.py`
- `backend/tests/connectors/test_census_tiger_connector.py`
- `backend/tests/api/test_chatham_zoning_connector_api.py`
- `scripts/source_readiness.py`
- `backend/tests/source_registry/test_source_readiness.py`

Current Must-source readiness: `sources=8 ready=7 blocked=1`. DS-001, DS-002,
DS-003, DS-004, DS-010, DS-011, and DS-023 are connector-ready. DS-017 remains
blocked by license/cost/vendor decision. DS-023 readiness uses recorded-fixture
district-code lookup only; no raw PDF redistribution, live amendment tracking, or
legal zoning conclusion is claimed. DS-010 readiness is scoped to
`immediate_operator_api` and `request_time_orchestration`; durable live-job support
is not claimed for DS-010. Current all-priority readiness: `sources=25 ready=16
blocked=9`; DS-007 is connector-ready only for active federal mining-claim
context, DS-015 is connector-ready only for historical NCGS 1985 map-unit
context, DS-008 is connector-ready only for historical mineral-occurrence screening
context, and DS-022 is connector-ready only for administrative TIGERweb geography
context, not ACS demographics or protected-class analytics.

Last verified in this pass: 2026-06-11 focused DS-007 connector/API/readiness tests
passed (`22 passed`), OpenAPI parity tests passed (`3 passed`), source registry
readiness/seed tests passed (`16 passed`), source readiness reported all-priority
`sources=25 ready=16 blocked=9`, Must `sources=8 ready=7 blocked=1`, Should
`sources=6 ready=3 blocked=3`, and Later `sources=8 ready=5 blocked=3`.
Release-readiness proof passed, focused ruff/mypy passed, and default
`.\scripts\verify.ps1` passed with workspace validation, structural checks, backend
tests, ruff, and mypy on 287 source files green. `git diff --check` reported no
whitespace errors; it warned that touched CSV/Markdown/OpenAPI files will normalize
line endings when Git next touches them. DB smoke was skipped because `RUN_DB_SMOKE=1`
was not set.

## Completed lane: Selected-County Evidence Utility Closure (completed 2026-06-06)

Active plan: `plans/2026-06-06-private-mvp-utility-proof.md` (extended for utility closure).
Geography: North Carolina — Buncombe, Chatham, Brunswick counties.
Goal: close the highest-value evidence gaps (terrain/Buncombe, parcels/Chatham,
wetlands+soils/Brunswick) so that promoted county cases have approved DB-backed dossiers
with useful evidence or explicit unknowns.

**Status: ALL 12 WORK PACKAGES COMPLETE (WP-1 through WP-12)**

| Work Package | Title | Status |
|---|---|---|
| WP-1..8 | Private MVP Utility Proof (US-001..US-008) | PASS |
| WP-9 | Buncombe terrain fixture connector + 3 terrain JSONs | PASS |
| WP-10 | Chatham parcel fixture connector + 3 parcel JSONs | PASS |
| WP-11 | Brunswick wetlands + soils fixture connectors + 5 JSONs | PASS |
| WP-12 | Tests/manifest/state updates + verify.ps1 clean | PASS |

Key artifacts added in WP-9..WP-12:
- `backend/app/connectors/terrain_fixture.py` — StaticTerrainFixtureConnector (DERIVED_METRIC)
- `backend/app/connectors/parcel_fixture.py` — StaticParcelFixtureConnector (SPATIAL_INTERSECTION)
- `backend/app/connectors/wetlands_fixture.py` — StaticWetlandsFixtureConnector (SPATIAL_INTERSECTION)
- `backend/app/connectors/soils_fixture.py` — StaticSoilsFixtureConnector (SPATIAL_INTERSECTION)
- `tests/fixtures/connectors/` — 11 new fixture JSON files (3 terrain, 3 parcel, 3 wetlands, 2 soils)
- `tests/fixtures/golden_aois/manifest.yaml` — terrain/parcels/wetlands/soils wired into 9 cases
- `backend/tests/private_mvp/test_utility_closure.py` — 2 RUN_DB_SMOKE-gated promoted-case tests
- `backend/tests/private_mvp/test_mvp_regression.py` — terrain added to Buncombe regression

Prior WP-1..8 artifacts:
- `tests/fixtures/golden_aois/` — 9 GeoJSON cases (3 per county)
- `config/private_mvp_beta_readiness.yaml` — private MVP gate registry
- `docs/geographies/nc/{buncombe,chatham,brunswick}/source_manifest.md`
- `backend/tests/private_mvp/test_mvp_regression.py` — 3 DB-smoke-gated county tests
- `backend/tests/reports/test_report_overclaim.py` — 4 Markdown overclaim checks
- `scripts/run_mvp_regression.ps1`
- `docs/runbooks/mvp_operator.md` — Private MVP path section added

Last verified: 2026-06-06 — `.\scripts\verify.ps1` → `verify: ok`; ruff clean; mypy clean 233 source files.
Residual risk: assessor NOT_EVALUATED for all 9 cases (no connector); DS-011/023 source-rights pending; DS-010 reviewed and approved-with-restrictions (Chatham live connector active).

## Completed lane: Local Source Readiness Closure — DS-010 / DS-011 / DS-023 (2026-06-06)

Goal: Write source review docs and promote DS-010 to connector-ready; document NOT_EVALUATED stance for DS-011 and DS-023.

| Source | Status | Outcome |
|---|---|---|
| DS-010 County GIS parcels (Chatham County) | approved-with-restrictions | Live connector unblocked; ready=true in source_readiness |
| DS-011 County assessor | pending | NOT_EVALUATED; no live connector; review doc written |
| DS-023 Local zoning ordinance PDFs | pending | fixture-backed; no live connector; review doc written |

Key artifacts:
- `docs/source-reviews/ds-010.md`, `ds-011.md`, `ds-023.md`
- `registers/data_source_registry.csv` DS-010 row updated
- `db/seeds/002_seed_source_registry.sql` DS-010 entry updated
- Historical 2026-06-06 source-readiness snapshot recorded here is superseded by the current checkpoint above.

Last verified for this historical lane: 2026-06-06; current source-readiness counts are recorded at the top of this file.

Prior lane (L10 production hardening) plans remain in `plans/` for reference. Production
hardening continues as a separate blocked lane and does not gate private MVP utility proof.

## Local repo bootstrap state

- Local Git initialized on `main`.
- `origin` is configured as `https://github.com/benjmcd/land-dd.git`.
- Local baseline commit exists on `main`: `ffb73e1` (`Establish governed scaffold baseline`).
- No GitHub push has been performed; `origin/main` remains at `13b75a9`.
- Local Codesight index exists at `.codesight/`; regenerate after significant code changes.
