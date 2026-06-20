# Residual Reconciliation Inventory

## Scope

Residual classification of the preserved dirty-root candidate checkout after PR #102. This file compares the dirty root against current live `origin/main` and does not modify, archive, delete, or clean the dirty-root files.

## Authority

- **Current live main**: `47913930ea6b5fc0af71e463d998f57535b7cad4`.
- **Dirty-root candidate branch**: `codex/r026-raw-readiness-ui` at `c3364ea01605cef09e03da6da8551fa4d1a155e8`.
- **Comparison source**: `git status --porcelain=v1 -uall` from the dirty root plus content comparison against the clean `res-rec` worktree at current main.
- **Prior disposition source**: `state/reconciliation-dispositions.md`.
- **Boundary**: candidate files remain evidence only. A retained concept still needs a fresh worktree, focused tests, validation, PR review, and merge before it becomes live authority.

## Summary

| Residual class | Count | Meaning |
|---|---:|---|
| `ALREADY_LANDED` | 8 | Dirty-root bytes match current main; no further carry-forward needed. |
| `LANDED_DIFFERENTLY` | 64 | Current main has the path, but the dirty-root content differs; treat current main as authority and do not copy the dirty file wholesale. |
| `REWORKED_IN_SLICE` | 1 | The dirty-root candidate concept has been reconstructed against current main in a focused slice instead of copied wholesale. |
| `STILL_DIVERGENT` | 2 | The candidate path is absent on current main and was not previously deferred/reference-only; it needs focused review before any implementation. |
| `DEFER_STILL_BLOCKED` | 17 | The candidate remains outside the current unblocked path, usually due to hosted/source/geography/report-semantics prerequisites. |
| `OBSOLETE` | 34 | Historical/reference/generated candidate material; do not promote as live state. |
| `COORDINATION_OR_GENERATED` | 2 | Agent coordination or generated/runtime state; not product work. |

## Focused Review Results

After `SRP-001`, the only paths still classified as `STILL_DIVERGENT` are:

| Path | Prior slice | Current determination |
|---|---|---|
| `backend/app/project_readiness.py` | `G3` | Read-only orientation/control-plane parser candidate. It should not be next unless a later control-plane consolidation slice is explicitly selected. |
| `backend/app/release_readiness.py` | `G3/G7` | Read-only release-readiness parser candidate. Existing `scripts/release_readiness_check.py` and release catalog remain authority; defer until real control-plane consolidation is needed. |

`backend/tests/api/test_operator_cases_runtime_provenance.py` is reworked by
`plans/2026-06-20-selected-county-runtime-provenance-regression.md` as a current-main
test-only regression for selected-county fixture review-bundle/idempotency behavior.

## Next-Slice Determination

REC-002 does not find a dirty-root implementation slice that should be copied forward wholesale. The highest-leverage unblocked engineering path is not hosted deployment, DS-017 connector work, or Bologna. Those remain gated by external authority or prerequisites. The next active slice should be a generic supported-AOI evidence-rich workflow plan that audits and then proves arbitrary AOIs inside the selected counties through DB-backed report, approval, artifact, lineage, caveat, unknown, and unsupported-area behavior.

The selected-county runtime-provenance regression candidate remains retained as a later focused G5 test-hardening slice if generic AOI audit shows the same provenance gap matters for the generic path. The project/release readiness orientation modules remain deferred until repeated merged control-plane patterns justify consolidation.

## Residual Path Table

| Class | Git | Main path | Path | Prior decision | Prior slice | Note |
|---|---|---|---|---|---|---|
| `ALREADY_LANDED` | `M` | yes | `backend/tests/test_private_mvp_readiness.py` | `RETAIN_AS_SLICE` | `G3/G5` | Dirty-root bytes match current main. |
| `ALREADY_LANDED` | `M` | yes | `config/private_mvp_beta_readiness.yaml` | `RETAIN_AS_SLICE` | `G3/G5` | Dirty-root bytes match current main. |
| `ALREADY_LANDED` | `M` | yes | `.github/workflows/ci.yml` | `RETAIN_AS_SLICE` | `G7` | Dirty-root bytes match current main. |
| `ALREADY_LANDED` | `M` | yes | `backend/tests/test_release_package_artifacts.py` | `RETAIN_AS_SLICE` | `G7` | Dirty-root bytes match current main. |
| `ALREADY_LANDED` | `M` | yes | `docs/runbooks/release_package.md` | `RETAIN_AS_SLICE` | `G7` | Dirty-root bytes match current main. |
| `ALREADY_LANDED` | `M` | yes | `scripts/release_package_check.py` | `RETAIN_AS_SLICE` | `G7` | Dirty-root bytes match current main. |
| `ALREADY_LANDED` | `??` | yes | `scripts/run_package_manifest_check.ps1` | `RETAIN_AS_SLICE` | `G7` | Dirty-root bytes match current main. |
| `ALREADY_LANDED` | `??` | yes | `scripts/run_package_manifest_check.sh` | `RETAIN_AS_SLICE` | `G7` | Dirty-root bytes match current main. |
| `COORDINATION_OR_GENERATED` | `M` | yes | `state/agent-inbox/for-claude.md` | `COORDINATION_ONLY` | `n/a` | Agent inbox material; not product authority. |
| `COORDINATION_OR_GENERATED` | `M` | yes | `state/agent-inbox/for-codex.md` | `COORDINATION_ONLY` | `n/a` | Agent inbox material; not product authority. |
| `DEFER_STILL_BLOCKED` | `??` | no | `backend/tests/api/test_ui_readiness_overview.py` | `DEFER` | `G3` | Initial disposition remains deferred or externally gated. |
| `DEFER_STILL_BLOCKED` | `??` | no | `backend/app/expansion_readiness.py` | `DEFER` | `G3/G10` | Initial disposition remains deferred or externally gated. |
| `DEFER_STILL_BLOCKED` | `??` | no | `backend/app/selected_geography_coverage.py` | `DEFER` | `G3/G10` | Initial disposition remains deferred or externally gated. |
| `DEFER_STILL_BLOCKED` | `??` | no | `backend/tests/api/test_ui_expansion_readiness.py` | `DEFER` | `G3/G10` | Initial disposition remains deferred or externally gated. |
| `DEFER_STILL_BLOCKED` | `??` | no | `backend/tests/api/test_ui_selected_geography_coverage.py` | `DEFER` | `G3/G10` | Initial disposition remains deferred or externally gated. |
| `DEFER_STILL_BLOCKED` | `??` | no | `backend/app/production_authority.py` | `DEFER` | `G3/G6` | Initial disposition remains deferred or externally gated. |
| `DEFER_STILL_BLOCKED` | `??` | no | `backend/tests/api/test_ui_production_authority.py` | `DEFER` | `G3/G6` | Initial disposition remains deferred or externally gated. |
| `DEFER_STILL_BLOCKED` | `??` | no | `backend/tests/api/test_ui_release_readiness.py` | `DEFER` | `G3/G7` | Initial disposition remains deferred or externally gated. |
| `DEFER_STILL_BLOCKED` | `??` | no | `backend/tests/test_local_deployment_artifacts.py` | `DEFER` | `G3/G7` | Initial disposition remains deferred or externally gated. |
| `DEFER_STILL_BLOCKED` | `??` | no | `config/local_deployment.yaml` | `DEFER` | `G3/G7` | Initial disposition remains deferred or externally gated. |
| `DEFER_STILL_BLOCKED` | `??` | no | `scripts/local_deployment_check.py` | `DEFER` | `G3/G7` | Initial disposition remains deferred or externally gated. |
| `DEFER_STILL_BLOCKED` | `??` | no | `scripts/run_local_deployment_check.ps1` | `DEFER` | `G3/G7` | Initial disposition remains deferred or externally gated. |
| `DEFER_STILL_BLOCKED` | `??` | no | `scripts/run_local_deployment_check.sh` | `DEFER` | `G3/G7` | Initial disposition remains deferred or externally gated. |
| `DEFER_STILL_BLOCKED` | `??` | no | `backend/app/dossier_readiness.py` | `DEFER` | `G5` | Initial disposition remains deferred or externally gated. |
| `DEFER_STILL_BLOCKED` | `??` | no | `backend/tests/api/test_ui_dossier_readiness.py` | `DEFER` | `G5` | Initial disposition remains deferred or externally gated. |
| `DEFER_STILL_BLOCKED` | `??` | no | `backend/app/product_correctness.py` | `DEFER` | `G6` | Initial disposition remains deferred or externally gated. |
| `DEFER_STILL_BLOCKED` | `??` | no | `backend/tests/api/test_ui_product_correctness.py` | `DEFER` | `G6` | Initial disposition remains deferred or externally gated. |
| `LANDED_DIFFERENTLY` | `M` | yes | `backend/app/api/ui_shared.py` | `REWORK_NARROWLY` | `G1` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `??` | yes | `backend/tests/api/test_ui_raw_data_inventory.py` | `RETAIN_AS_SLICE` | `G1` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `M` | yes | `backend/tests/api/test_ui_routes.py` | `REWORK_NARROWLY` | `G1` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `M` | yes | `DESIGN.md` | `REWORK_NARROWLY` | `G1-G8` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `M` | yes | `MANIFEST.md` | `DEFER` | `G1-G8` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `M` | yes | `backend/app/api/ui.py` | `REWORK_NARROWLY` | `G1-G8` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `M` | yes | `backend/app/main.py` | `REWORK_NARROWLY` | `G1-G8` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `M` | yes | `docs/runbooks/mvp_operator.md` | `REWORK_NARROWLY` | `G1/G3` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `M` | yes | `.env.example` | `REWORK_NARROWLY` | `G1/G4` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `M` | yes | `backend/app/api/ui_auth.py` | `REWORK_NARROWLY` | `G1/G6` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `M` | yes | `backend/tests/api/test_ui_api_key_auth.py` | `REWORK_NARROWLY` | `G1/G6` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `M` | yes | `backend/tests/api/test_ui_review_routes.py` | `REWORK_NARROWLY` | `G1/G6` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `M` | yes | `config/access_control.yaml` | `REWORK_NARROWLY` | `G1/G6` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `M` | yes | `docs/runbooks/access_control.md` | `REWORK_NARROWLY` | `G1/G6` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `M` | yes | `scripts/access_control_check.py` | `REWORK_NARROWLY` | `G1/G6` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `M` | yes | `backend/tests/test_ui_browser_smoke_scripts.py` | `REWORK_NARROWLY` | `G2` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `M` | yes | `backend/tests/test_ui_runtime_smoke_script.py` | `REWORK_NARROWLY` | `G2` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `M` | yes | `scripts/ui_browser_smoke.mjs` | `REWORK_NARROWLY` | `G2` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `M` | yes | `scripts/ui_runtime_smoke.py` | `REWORK_NARROWLY` | `G2` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `M` | yes | `backend/tests/test_deployment_smoke_scripts.py` | `REWORK_NARROWLY` | `G2/G7` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `M` | yes | `scripts/run_deployment_smoke.ps1` | `REWORK_NARROWLY` | `G2/G7` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `M` | yes | `scripts/run_deployment_smoke.sh` | `REWORK_NARROWLY` | `G2/G7` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `M` | yes | `api/openapi_stub.yaml` | `DISCARD_GENERATED` | `G3/G5` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `??` | yes | `backend/app/source_registry/readiness.py` | `RETAIN_AS_SLICE` | `G3/G5` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `M` | yes | `backend/tests/source_registry/test_source_readiness.py` | `RETAIN_AS_SLICE` | `G3/G5` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `M` | yes | `docs/planning_pack/api/openapi_stub.yaml` | `DISCARD_GENERATED` | `G3/G5` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `M` | yes | `scripts/private_mvp_readiness_check.py` | `RETAIN_AS_SLICE` | `G3/G5` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `M` | yes | `scripts/source_readiness.py` | `RETAIN_AS_SLICE` | `G3/G5` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `??` | yes | `backend/app/deployment_readiness.py` | `RETAIN_AS_SLICE` | `G3/G7` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `??` | yes | `backend/tests/api/test_ui_deployment_readiness.py` | `RETAIN_AS_SLICE` | `G3/G7` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `M` | yes | `backend/tests/test_release_readiness_artifacts.py` | `REWORK_NARROWLY` | `G3/G7` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `M` | yes | `config/release_readiness.yaml` | `REWORK_NARROWLY` | `G3/G7` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `M` | yes | `docs/IMPLEMENTATION_READINESS.md` | `DEFER` | `G3/G7` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `M` | yes | `docs/runbooks/release_readiness.md` | `REWORK_NARROWLY` | `G3/G7` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `M` | yes | `scripts/release_readiness_check.py` | `REWORK_NARROWLY` | `G3/G7` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `M` | yes | `backend/app/api/ui_lineage.py` | `DEFER` | `G5` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `M` | yes | `backend/app/api/ui_live_connector_jobs.py` | `REWORK_NARROWLY` | `G5` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `M` | yes | `backend/app/operator_cases/__init__.py` | `REWORK_NARROWLY` | `G5` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `M` | yes | `backend/app/reports/report_repo.py` | `REWORK_NARROWLY` | `G5` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `M` | yes | `backend/app/reports/service.py` | `REWORK_NARROWLY` | `G5` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `M` | yes | `backend/tests/api/test_ui_live_connector_jobs.py` | `REWORK_NARROWLY` | `G5` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `M` | yes | `backend/app/api/ui_operations.py` | `REWORK_NARROWLY` | `G6` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `??` | yes | `backend/app/operations_guardrails.py` | `RETAIN_AS_SLICE` | `G6` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `??` | yes | `backend/app/performance_guardrails.py` | `RETAIN_AS_SLICE` | `G6` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `??` | yes | `backend/app/security_guardrails.py` | `RETAIN_AS_SLICE` | `G6` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `??` | yes | `backend/tests/api/test_ui_operations_guardrails.py` | `RETAIN_AS_SLICE` | `G6` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `M` | yes | `backend/tests/api/test_ui_operations_routes.py` | `REWORK_NARROWLY` | `G6` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `??` | yes | `backend/tests/api/test_ui_performance_guardrails.py` | `RETAIN_AS_SLICE` | `G6` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `??` | yes | `backend/tests/api/test_ui_security_guardrails.py` | `RETAIN_AS_SLICE` | `G6` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `??` | yes | `backend/tests/test_package_manifest_check.py` | `RETAIN_AS_SLICE` | `G7` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `??` | yes | `scripts/package_manifest_check.py` | `RETAIN_AS_SLICE` | `G7` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `??` | yes | `backend/app/observability_readiness.py` | `RETAIN_AS_SLICE` | `G8` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `??` | yes | `backend/tests/api/test_ui_observability_readiness.py` | `RETAIN_AS_SLICE` | `G8` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `??` | yes | `backend/tests/test_observability_readiness_artifacts.py` | `RETAIN_AS_SLICE` | `G8` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `??` | yes | `config/observability_readiness.yaml` | `RETAIN_AS_SLICE` | `G8` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `??` | yes | `scripts/observability_readiness_check.py` | `RETAIN_AS_SLICE` | `G8` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `??` | yes | `scripts/run_observability_readiness_check.ps1` | `RETAIN_AS_SLICE` | `G8` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `??` | yes | `scripts/run_observability_readiness_check.sh` | `RETAIN_AS_SLICE` | `G8` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `M` | yes | `plans/README.md` | `ARCHIVE_REFERENCE` | `REC-001` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `M` | yes | `state/LEVEL_9_10_GATE_MATRIX.md` | `ARCHIVE_REFERENCE` | `REC-001` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `M` | yes | `state/PROJECT_STATE.md` | `ARCHIVE_REFERENCE` | `REC-001` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `M` | yes | `state/VALIDATION_LOG.md` | `ARCHIVE_REFERENCE` | `REC-001` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `M` | yes | `state/WORKLOG.md` | `ARCHIVE_REFERENCE` | `REC-001` | Current main has the path; dirty-root content must not be copied wholesale. |
| `LANDED_DIFFERENTLY` | `M` | yes | `tasks/task_queue.yaml` | `ARCHIVE_REFERENCE` | `REC-001` | Current main has the path; dirty-root content must not be copied wholesale. |
| `OBSOLETE` | `??` | no | `plans/2026-06-19-local-only-raw-data-ui.md` | `ARCHIVE_REFERENCE` | `G1` | Historical/reference/generated candidate; do not publish as live state. |
| `OBSOLETE` | `??` | no | `plans/2026-06-19-db-backed-local-ui-smoke.md` | `ARCHIVE_REFERENCE` | `G2` | Historical/reference/generated candidate; do not publish as live state. |
| `OBSOLETE` | `??` | no | `plans/2026-06-19-release-readiness-deployment-smoke-guard.md` | `ARCHIVE_REFERENCE` | `G2/G7` | Historical/reference/generated candidate; do not publish as live state. |
| `OBSOLETE` | `??` | no | `plans/2026-06-19-local-readiness-overview-ui.md` | `ARCHIVE_REFERENCE` | `G3` | Historical/reference/generated candidate; do not publish as live state. |
| `OBSOLETE` | `??` | no | `plans/2026-06-19-local-expansion-readiness-ui.md` | `ARCHIVE_REFERENCE` | `G3/G10` | Historical/reference/generated candidate; do not publish as live state. |
| `OBSOLETE` | `??` | no | `plans/2026-06-19-local-selected-geography-coverage-ui.md` | `ARCHIVE_REFERENCE` | `G3/G10` | Historical/reference/generated candidate; do not publish as live state. |
| `OBSOLETE` | `??` | no | `plans/2026-06-19-raw-source-readiness-ui.md` | `ARCHIVE_REFERENCE` | `G3/G5` | Historical/reference/generated candidate; do not publish as live state. |
| `OBSOLETE` | `??` | no | `plans/2026-06-19-local-production-authority-ui.md` | `ARCHIVE_REFERENCE` | `G3/G6` | Historical/reference/generated candidate; do not publish as live state. |
| `OBSOLETE` | `??` | no | `plans/2026-06-19-local-deployment-readiness-ui.md` | `ARCHIVE_REFERENCE` | `G3/G7` | Historical/reference/generated candidate; do not publish as live state. |
| `OBSOLETE` | `??` | no | `plans/2026-06-19-local-release-readiness-ui.md` | `ARCHIVE_REFERENCE` | `G3/G7` | Historical/reference/generated candidate; do not publish as live state. |
| `OBSOLETE` | `??` | no | `plans/2026-06-19-account-free-runtime.md` | `ARCHIVE_REFERENCE` | `G4` | Historical/reference/generated candidate; do not publish as live state. |
| `OBSOLETE` | `??` | no | `plans/2026-06-19-local-account-disabled-raw-ui.md` | `ARCHIVE_REFERENCE` | `G4` | Historical/reference/generated candidate; do not publish as live state. |
| `OBSOLETE` | `??` | no | `plans/2026-06-19-local-production-profile.md` | `ARCHIVE_REFERENCE` | `G4` | Historical/reference/generated candidate; do not publish as live state. |
| `OBSOLETE` | `??` | no | `plans/2026-06-19-local-project-trajectory-ui.md` | `ARCHIVE_REFERENCE` | `G4` | Historical/reference/generated candidate; do not publish as live state. |
| `OBSOLETE` | `??` | no | `plans/2026-06-19-local-validation-evidence-ui.md` | `ARCHIVE_REFERENCE` | `G4` | Historical/reference/generated candidate; do not publish as live state. |
| `OBSOLETE` | `??` | no | `plans/2026-06-19-validation-proof-ui.md` | `ARCHIVE_REFERENCE` | `G4` | Historical/reference/generated candidate; do not publish as live state. |
| `OBSOLETE` | `??` | no | `plans/2026-06-19-dossier-ui.md` | `ARCHIVE_REFERENCE` | `G5` | Historical/reference/generated candidate; do not publish as live state. |
| `OBSOLETE` | `??` | no | `plans/2026-06-19-evidence-deps.md` | `ARCHIVE_REFERENCE` | `G5` | Historical/reference/generated candidate; do not publish as live state. |
| `OBSOLETE` | `??` | no | `plans/2026-06-19-raw-claim-task-inventory.md` | `ARCHIVE_REFERENCE` | `G5` | Historical/reference/generated candidate; do not publish as live state. |
| `OBSOLETE` | `??` | no | `plans/2026-06-19-raw-evidence-provenance-ui.md` | `ARCHIVE_REFERENCE` | `G5` | Historical/reference/generated candidate; do not publish as live state. |
| `OBSOLETE` | `??` | no | `plans/2026-06-19-report-list-contract-overlay.md` | `ARCHIVE_REFERENCE` | `G5` | Historical/reference/generated candidate; do not publish as live state. |
| `OBSOLETE` | `??` | no | `plans/2026-06-19-report-run-inventory-ui.md` | `ARCHIVE_REFERENCE` | `G5` | Historical/reference/generated candidate; do not publish as live state. |
| `OBSOLETE` | `??` | no | `plans/2026-06-19-selected-county-provenance-status-ui.md` | `ARCHIVE_REFERENCE` | `G5` | Historical/reference/generated candidate; do not publish as live state. |
| `OBSOLETE` | `??` | no | `plans/2026-06-19-selected-county-runtime-provenance-bridge.md` | `ARCHIVE_REFERENCE` | `G5` | Historical/reference/generated candidate; do not publish as live state. |
| `OBSOLETE` | `??` | no | `plans/2026-06-19-selected-county-source-provenance-catalog.md` | `ARCHIVE_REFERENCE` | `G5` | Historical/reference/generated candidate; do not publish as live state. |
| `OBSOLETE` | `??` | no | `plans/2026-06-19-source-provenance-ui.md` | `ARCHIVE_REFERENCE` | `G5` | Historical/reference/generated candidate; do not publish as live state. |
| `OBSOLETE` | `??` | no | `plans/2026-06-19-local-auth-surface-hardening.md` | `ARCHIVE_REFERENCE` | `G6` | Historical/reference/generated candidate; do not publish as live state. |
| `OBSOLETE` | `??` | no | `plans/2026-06-19-operations-guardrails-ui.md` | `ARCHIVE_REFERENCE` | `G6` | Historical/reference/generated candidate; do not publish as live state. |
| `OBSOLETE` | `??` | no | `plans/2026-06-19-performance-guardrails-ui.md` | `ARCHIVE_REFERENCE` | `G6` | Historical/reference/generated candidate; do not publish as live state. |
| `OBSOLETE` | `??` | no | `plans/2026-06-19-product-correctness-guardrails-ui.md` | `ARCHIVE_REFERENCE` | `G6` | Historical/reference/generated candidate; do not publish as live state. |
| `OBSOLETE` | `??` | no | `plans/2026-06-19-security-guardrails-ui.md` | `ARCHIVE_REFERENCE` | `G6` | Historical/reference/generated candidate; do not publish as live state. |
| `OBSOLETE` | `??` | no | `plans/2026-06-19-ci-package-manifest-gate.md` | `ARCHIVE_REFERENCE` | `G7` | Historical/reference/generated candidate; do not publish as live state. |
| `OBSOLETE` | `??` | no | `plans/2026-06-19-release-package-manifest-verification.md` | `ARCHIVE_REFERENCE` | `G7` | Historical/reference/generated candidate; do not publish as live state. |
| `OBSOLETE` | `??` | no | `plans/2026-06-19-observability-readiness-ui.md` | `ARCHIVE_REFERENCE` | `G8` | Historical/reference/generated candidate; do not publish as live state. |
| `STILL_DIVERGENT` | `??` | no | `backend/app/project_readiness.py` | `REWORK_NARROWLY` | `G3` | Unlanded candidate concept needs focused review before any implementation. |
| `STILL_DIVERGENT` | `??` | no | `backend/app/release_readiness.py` | `REWORK_NARROWLY` | `G3/G7` | Unlanded candidate concept needs focused review before any implementation. |
| `REWORKED_IN_SLICE` | `??` | yes | `backend/tests/api/test_operator_cases_runtime_provenance.py` | `REWORK_NARROWLY` | `G5` | Reworked as `SRP-001`; current-main test targets selected-county fixture package review bundles and repeated-run idempotency instead of stale dirty-root per-DS helper assumptions. |

## Validation Plan

- Parse `tasks/task_queue.yaml` and confirm the active follow-on task after REC-002.
- Run `git diff --check` and `git diff --name-only --diff-filter=D`.
- Run `py -3.12 .\scripts\readiness_matrix_check.py` because this updates Level 9/10 routing context.
- Run `py -3.12 -m pytest backend\tests\test_readiness_matrix_artifacts.py -q`.
- Run `..\scripts\validate_workspace.ps1` from the worktree root.
- Run `..\scripts\verify.ps1` from the worktree root before publication.
