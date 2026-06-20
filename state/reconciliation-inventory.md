# Reconciliation Inventory

## Scope

Initial file-level inventory for dirty-root candidate work relative to refreshed
`origin/main` at `c3364ea01605cef09e03da6da8551fa4d1a155e8`.

This inventory classifies recoverability and authority status. It does not decide that
any product file should be retained or landed. Retain/rework/defer decisions require
content review, dependency mapping, and focused validation from a clean worktree.

## Summary

| Class | Count | Meaning |
|---|---:|---|
| `LOCAL_UNCOMMITTED` | 126 | Product or state candidate file in the dirty root; not merged authority. |
| `COORDINATION_ONLY` | 2 | Agent inbox material; not product authority and not a landing candidate by default. |
| `GENERATED_IGNORED` | 5 dirs | Runtime/cache/artifact directories ignored by Git and not product authority. |

Ignored/generated directories observed separately: `.codesight/`, `.mypy_cache/`,
`.pytest_cache/`, `.ruff_cache/`, and `local_artifacts/`.

## File Inventory

| Git status | Path | Initial class |
|---|---|---|
| M | `state/agent-inbox/for-claude.md` | `COORDINATION_ONLY` |
| M | `state/agent-inbox/for-codex.md` | `COORDINATION_ONLY` |
| M | `.env.example` | `LOCAL_UNCOMMITTED` |
| M | `.github/workflows/ci.yml` | `LOCAL_UNCOMMITTED` |
| M | `api/openapi_stub.yaml` | `LOCAL_UNCOMMITTED` |
| M | `backend/app/api/ui.py` | `LOCAL_UNCOMMITTED` |
| M | `backend/app/api/ui_auth.py` | `LOCAL_UNCOMMITTED` |
| M | `backend/app/api/ui_lineage.py` | `LOCAL_UNCOMMITTED` |
| M | `backend/app/api/ui_live_connector_jobs.py` | `LOCAL_UNCOMMITTED` |
| M | `backend/app/api/ui_operations.py` | `LOCAL_UNCOMMITTED` |
| M | `backend/app/api/ui_shared.py` | `LOCAL_UNCOMMITTED` |
| ?? | `backend/app/deployment_readiness.py` | `LOCAL_UNCOMMITTED` |
| ?? | `backend/app/dossier_readiness.py` | `LOCAL_UNCOMMITTED` |
| ?? | `backend/app/expansion_readiness.py` | `LOCAL_UNCOMMITTED` |
| M | `backend/app/main.py` | `LOCAL_UNCOMMITTED` |
| ?? | `backend/app/observability_readiness.py` | `LOCAL_UNCOMMITTED` |
| ?? | `backend/app/operations_guardrails.py` | `LOCAL_UNCOMMITTED` |
| M | `backend/app/operator_cases/__init__.py` | `LOCAL_UNCOMMITTED` |
| ?? | `backend/app/performance_guardrails.py` | `LOCAL_UNCOMMITTED` |
| ?? | `backend/app/product_correctness.py` | `LOCAL_UNCOMMITTED` |
| ?? | `backend/app/production_authority.py` | `LOCAL_UNCOMMITTED` |
| ?? | `backend/app/project_readiness.py` | `LOCAL_UNCOMMITTED` |
| ?? | `backend/app/release_readiness.py` | `LOCAL_UNCOMMITTED` |
| M | `backend/app/reports/report_repo.py` | `LOCAL_UNCOMMITTED` |
| M | `backend/app/reports/service.py` | `LOCAL_UNCOMMITTED` |
| ?? | `backend/app/security_guardrails.py` | `LOCAL_UNCOMMITTED` |
| ?? | `backend/app/selected_geography_coverage.py` | `LOCAL_UNCOMMITTED` |
| ?? | `backend/app/source_registry/readiness.py` | `LOCAL_UNCOMMITTED` |
| ?? | `backend/tests/api/test_operator_cases_runtime_provenance.py` | `LOCAL_UNCOMMITTED` |
| M | `backend/tests/api/test_ui_api_key_auth.py` | `LOCAL_UNCOMMITTED` |
| ?? | `backend/tests/api/test_ui_deployment_readiness.py` | `LOCAL_UNCOMMITTED` |
| ?? | `backend/tests/api/test_ui_dossier_readiness.py` | `LOCAL_UNCOMMITTED` |
| ?? | `backend/tests/api/test_ui_expansion_readiness.py` | `LOCAL_UNCOMMITTED` |
| M | `backend/tests/api/test_ui_live_connector_jobs.py` | `LOCAL_UNCOMMITTED` |
| ?? | `backend/tests/api/test_ui_observability_readiness.py` | `LOCAL_UNCOMMITTED` |
| ?? | `backend/tests/api/test_ui_operations_guardrails.py` | `LOCAL_UNCOMMITTED` |
| M | `backend/tests/api/test_ui_operations_routes.py` | `LOCAL_UNCOMMITTED` |
| ?? | `backend/tests/api/test_ui_performance_guardrails.py` | `LOCAL_UNCOMMITTED` |
| ?? | `backend/tests/api/test_ui_product_correctness.py` | `LOCAL_UNCOMMITTED` |
| ?? | `backend/tests/api/test_ui_production_authority.py` | `LOCAL_UNCOMMITTED` |
| ?? | `backend/tests/api/test_ui_raw_data_inventory.py` | `LOCAL_UNCOMMITTED` |
| ?? | `backend/tests/api/test_ui_readiness_overview.py` | `LOCAL_UNCOMMITTED` |
| ?? | `backend/tests/api/test_ui_release_readiness.py` | `LOCAL_UNCOMMITTED` |
| M | `backend/tests/api/test_ui_review_routes.py` | `LOCAL_UNCOMMITTED` |
| M | `backend/tests/api/test_ui_routes.py` | `LOCAL_UNCOMMITTED` |
| ?? | `backend/tests/api/test_ui_security_guardrails.py` | `LOCAL_UNCOMMITTED` |
| ?? | `backend/tests/api/test_ui_selected_geography_coverage.py` | `LOCAL_UNCOMMITTED` |
| M | `backend/tests/source_registry/test_source_readiness.py` | `LOCAL_UNCOMMITTED` |
| M | `backend/tests/test_deployment_smoke_scripts.py` | `LOCAL_UNCOMMITTED` |
| ?? | `backend/tests/test_local_deployment_artifacts.py` | `LOCAL_UNCOMMITTED` |
| ?? | `backend/tests/test_observability_readiness_artifacts.py` | `LOCAL_UNCOMMITTED` |
| ?? | `backend/tests/test_package_manifest_check.py` | `LOCAL_UNCOMMITTED` |
| M | `backend/tests/test_private_mvp_readiness.py` | `LOCAL_UNCOMMITTED` |
| M | `backend/tests/test_release_package_artifacts.py` | `LOCAL_UNCOMMITTED` |
| M | `backend/tests/test_release_readiness_artifacts.py` | `LOCAL_UNCOMMITTED` |
| M | `backend/tests/test_ui_browser_smoke_scripts.py` | `LOCAL_UNCOMMITTED` |
| M | `backend/tests/test_ui_runtime_smoke_script.py` | `LOCAL_UNCOMMITTED` |
| M | `config/access_control.yaml` | `LOCAL_UNCOMMITTED` |
| ?? | `config/local_deployment.yaml` | `LOCAL_UNCOMMITTED` |
| ?? | `config/observability_readiness.yaml` | `LOCAL_UNCOMMITTED` |
| M | `config/private_mvp_beta_readiness.yaml` | `LOCAL_UNCOMMITTED` |
| M | `config/release_readiness.yaml` | `LOCAL_UNCOMMITTED` |
| M | `DESIGN.md` | `LOCAL_UNCOMMITTED` |
| M | `docs/IMPLEMENTATION_READINESS.md` | `LOCAL_UNCOMMITTED` |
| M | `docs/planning_pack/api/openapi_stub.yaml` | `LOCAL_UNCOMMITTED` |
| M | `docs/runbooks/access_control.md` | `LOCAL_UNCOMMITTED` |
| M | `docs/runbooks/mvp_operator.md` | `LOCAL_UNCOMMITTED` |
| M | `docs/runbooks/release_package.md` | `LOCAL_UNCOMMITTED` |
| M | `docs/runbooks/release_readiness.md` | `LOCAL_UNCOMMITTED` |
| M | `MANIFEST.md` | `LOCAL_UNCOMMITTED` |
| ?? | `plans/2026-06-19-account-free-runtime.md` | `LOCAL_UNCOMMITTED` |
| ?? | `plans/2026-06-19-ci-package-manifest-gate.md` | `LOCAL_UNCOMMITTED` |
| ?? | `plans/2026-06-19-db-backed-local-ui-smoke.md` | `LOCAL_UNCOMMITTED` |
| ?? | `plans/2026-06-19-dossier-ui.md` | `LOCAL_UNCOMMITTED` |
| ?? | `plans/2026-06-19-evidence-deps.md` | `LOCAL_UNCOMMITTED` |
| ?? | `plans/2026-06-19-local-account-disabled-raw-ui.md` | `LOCAL_UNCOMMITTED` |
| ?? | `plans/2026-06-19-local-auth-surface-hardening.md` | `LOCAL_UNCOMMITTED` |
| ?? | `plans/2026-06-19-local-deployment-readiness-ui.md` | `LOCAL_UNCOMMITTED` |
| ?? | `plans/2026-06-19-local-expansion-readiness-ui.md` | `LOCAL_UNCOMMITTED` |
| ?? | `plans/2026-06-19-local-only-raw-data-ui.md` | `LOCAL_UNCOMMITTED` |
| ?? | `plans/2026-06-19-local-production-authority-ui.md` | `LOCAL_UNCOMMITTED` |
| ?? | `plans/2026-06-19-local-production-profile.md` | `LOCAL_UNCOMMITTED` |
| ?? | `plans/2026-06-19-local-project-trajectory-ui.md` | `LOCAL_UNCOMMITTED` |
| ?? | `plans/2026-06-19-local-readiness-overview-ui.md` | `LOCAL_UNCOMMITTED` |
| ?? | `plans/2026-06-19-local-release-readiness-ui.md` | `LOCAL_UNCOMMITTED` |
| ?? | `plans/2026-06-19-local-selected-geography-coverage-ui.md` | `LOCAL_UNCOMMITTED` |
| ?? | `plans/2026-06-19-local-validation-evidence-ui.md` | `LOCAL_UNCOMMITTED` |
| ?? | `plans/2026-06-19-observability-readiness-ui.md` | `LOCAL_UNCOMMITTED` |
| ?? | `plans/2026-06-19-operations-guardrails-ui.md` | `LOCAL_UNCOMMITTED` |
| ?? | `plans/2026-06-19-performance-guardrails-ui.md` | `LOCAL_UNCOMMITTED` |
| ?? | `plans/2026-06-19-product-correctness-guardrails-ui.md` | `LOCAL_UNCOMMITTED` |
| ?? | `plans/2026-06-19-raw-claim-task-inventory.md` | `LOCAL_UNCOMMITTED` |
| ?? | `plans/2026-06-19-raw-evidence-provenance-ui.md` | `LOCAL_UNCOMMITTED` |
| ?? | `plans/2026-06-19-raw-source-readiness-ui.md` | `LOCAL_UNCOMMITTED` |
| ?? | `plans/2026-06-19-release-package-manifest-verification.md` | `LOCAL_UNCOMMITTED` |
| ?? | `plans/2026-06-19-release-readiness-deployment-smoke-guard.md` | `LOCAL_UNCOMMITTED` |
| ?? | `plans/2026-06-19-report-list-contract-overlay.md` | `LOCAL_UNCOMMITTED` |
| ?? | `plans/2026-06-19-report-run-inventory-ui.md` | `LOCAL_UNCOMMITTED` |
| ?? | `plans/2026-06-19-security-guardrails-ui.md` | `LOCAL_UNCOMMITTED` |
| ?? | `plans/2026-06-19-selected-county-provenance-status-ui.md` | `LOCAL_UNCOMMITTED` |
| ?? | `plans/2026-06-19-selected-county-runtime-provenance-bridge.md` | `LOCAL_UNCOMMITTED` |
| ?? | `plans/2026-06-19-selected-county-source-provenance-catalog.md` | `LOCAL_UNCOMMITTED` |
| ?? | `plans/2026-06-19-source-provenance-ui.md` | `LOCAL_UNCOMMITTED` |
| ?? | `plans/2026-06-19-validation-proof-ui.md` | `LOCAL_UNCOMMITTED` |
| M | `plans/README.md` | `LOCAL_UNCOMMITTED` |
| M | `scripts/access_control_check.py` | `LOCAL_UNCOMMITTED` |
| ?? | `scripts/local_deployment_check.py` | `LOCAL_UNCOMMITTED` |
| ?? | `scripts/observability_readiness_check.py` | `LOCAL_UNCOMMITTED` |
| ?? | `scripts/package_manifest_check.py` | `LOCAL_UNCOMMITTED` |
| M | `scripts/private_mvp_readiness_check.py` | `LOCAL_UNCOMMITTED` |
| M | `scripts/release_package_check.py` | `LOCAL_UNCOMMITTED` |
| M | `scripts/release_readiness_check.py` | `LOCAL_UNCOMMITTED` |
| M | `scripts/run_deployment_smoke.ps1` | `LOCAL_UNCOMMITTED` |
| M | `scripts/run_deployment_smoke.sh` | `LOCAL_UNCOMMITTED` |
| ?? | `scripts/run_local_deployment_check.ps1` | `LOCAL_UNCOMMITTED` |
| ?? | `scripts/run_local_deployment_check.sh` | `LOCAL_UNCOMMITTED` |
| ?? | `scripts/run_observability_readiness_check.ps1` | `LOCAL_UNCOMMITTED` |
| ?? | `scripts/run_observability_readiness_check.sh` | `LOCAL_UNCOMMITTED` |
| ?? | `scripts/run_package_manifest_check.ps1` | `LOCAL_UNCOMMITTED` |
| ?? | `scripts/run_package_manifest_check.sh` | `LOCAL_UNCOMMITTED` |
| M | `scripts/source_readiness.py` | `LOCAL_UNCOMMITTED` |
| M | `scripts/ui_browser_smoke.mjs` | `LOCAL_UNCOMMITTED` |
| M | `scripts/ui_runtime_smoke.py` | `LOCAL_UNCOMMITTED` |
| M | `state/LEVEL_9_10_GATE_MATRIX.md` | `LOCAL_UNCOMMITTED` |
| M | `state/PROJECT_STATE.md` | `LOCAL_UNCOMMITTED` |
| M | `state/VALIDATION_LOG.md` | `LOCAL_UNCOMMITTED` |
| M | `state/WORKLOG.md` | `LOCAL_UNCOMMITTED` |
| M | `tasks/task_queue.yaml` | `LOCAL_UNCOMMITTED` |
