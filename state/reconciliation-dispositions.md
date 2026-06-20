# Reconciliation Dispositions

## Scope

Initial retain/rework/defer/archive/discard decisions for the dirty-root candidate
workspace relative to live `origin/main` at
`c3364ea01605cef09e03da6da8551fa4d1a155e8`.

This file completes the next Lane 1 classification layer after
`state/reconciliation-inventory.md`. It is not a merge decision and it does not
change product behavior. The dirty root remains candidate evidence until each retained
concept is replayed from a clean worktree, validated, reviewed, and merged.

## Decision Vocabulary

| Decision | Meaning |
|---|---|
| `REWORK_NARROWLY` | Retain the candidate idea, but do not copy the dirty file wholesale; reconstruct the smallest current-main slice with focused tests. |
| `RETAIN_AS_SLICE` | Likely coherent enough to carry into a named focused slice after rebasing and validation. |
| `DEFER` | Do not work next; revisit only after prerequisites or external authority are resolved. |
| `ARCHIVE_REFERENCE` | Preserve as historical/candidate planning or validation evidence; do not promote as live state. |
| `COORDINATION_ONLY` | Agent coordination material; not a product landing candidate. |
| `DISCARD_GENERATED` | Generated, derivative, or ignored runtime state; do not manually carry from the dirty workspace. |

No physical archive, discard, delete, reset, or clean action was taken while preparing
this matrix.

## Disposition Table

| Path | Decision | Slice | Reason / dependency |
|---|---|---|---|
| `state/agent-inbox/for-claude.md` | `COORDINATION_ONLY` | n/a | Agent inbox material; do not publish as product state. |
| `state/agent-inbox/for-codex.md` | `COORDINATION_ONLY` | n/a | Agent inbox material; do not publish as product state. |
| `.env.example` | `REWORK_NARROWLY` | G1/G4 | Local/account-free env posture must follow proven auth behavior only. |
| `.github/workflows/ci.yml` | `RETAIN_AS_SLICE` | G7 | Small additive package-manifest CI job; land with validator and no publish/deploy behavior. |
| `api/openapi_stub.yaml` | `DISCARD_GENERATED` | G3/G5 | Regenerate from the final retained route/API set; do not manually carry the dirty aggregate. |
| `backend/app/api/ui.py` | `REWORK_NARROWLY` | G1-G8 | Broad mixed UI surface; do not copy wholesale. |
| `backend/app/api/ui_auth.py` | `REWORK_NARROWLY` | G1/G6 | Local auth posture is useful but must preserve non-local fail-closed behavior. |
| `backend/app/api/ui_lineage.py` | `DEFER` | G5 | Report lineage/provenance display touches report semantics; revisit after raw-data/auth baseline. |
| `backend/app/api/ui_live_connector_jobs.py` | `REWORK_NARROWLY` | G5 | Source/runtime provenance surface depends on source-rights boundaries. |
| `backend/app/api/ui_operations.py` | `REWORK_NARROWLY` | G6 | Guardrail/readiness view should not be bundled with local-auth work. |
| `backend/app/api/ui_shared.py` | `REWORK_NARROWLY` | G1 | Local operator helpers are plausible first-slice material. |
| `backend/app/deployment_readiness.py` | `RETAIN_AS_SLICE` | G3/G7 | Good read-only view over package/image/hosted catalogs; land after package manifest slice. |
| `backend/app/dossier_readiness.py` | `DEFER` | G5 | Dossier readiness is orientation-heavy; revisit after source/evidence/report contracts settle. |
| `backend/app/expansion_readiness.py` | `DEFER` | G3/G10 | Expansion readiness should wait for selected-geography baseline. |
| `backend/app/main.py` | `REWORK_NARROWLY` | G1-G8 | Route registration should happen only per accepted UI/API slice. |
| `backend/app/observability_readiness.py` | `RETAIN_AS_SLICE` | G8 | Local-only observability catalog/parser is useful; keep hosted dashboard/log-retention/pager blocked. |
| `backend/app/operations_guardrails.py` | `RETAIN_AS_SLICE` | G6 | Read-only parser/UI surface over existing catalogs; land as isolated operations PR. |
| `backend/app/operator_cases/__init__.py` | `REWORK_NARROWLY` | G5 | Runtime provenance bridge requires source/report contract review. |
| `backend/app/performance_guardrails.py` | `RETAIN_AS_SLICE` | G6 | Read-only parser/UI surface; keep hosted SLO/capacity claims blocked. |
| `backend/app/product_correctness.py` | `DEFER` | G6 | Broad guardrail aggregation is brittle until lower claim/report/source slices settle. |
| `backend/app/production_authority.py` | `DEFER` | G3/G6 | External authority blockers remain; do not imply production readiness. |
| `backend/app/project_readiness.py` | `REWORK_NARROWLY` | G3 | Readiness overview should be consolidated after lower UI posture lands. |
| `backend/app/release_readiness.py` | `REWORK_NARROWLY` | G3/G7 | Release readiness depends on smoke/package gate separation. |
| `backend/app/reports/report_repo.py` | `REWORK_NARROWLY` | G5 | Report listing is useful but must be workspace-safe before non-local/protected UI use. |
| `backend/app/reports/service.py` | `REWORK_NARROWLY` | G5 | Evidence/report dependency behavior must stay claim-safe. |
| `backend/app/security_guardrails.py` | `RETAIN_AS_SLICE` | G6 | Read-only parser/UI surface over existing catalogs; land as isolated security PR. |
| `backend/app/selected_geography_coverage.py` | `DEFER` | G3/G10 | Coverage view is tied to later provenance/coverage authority review. |
| `backend/app/source_registry/readiness.py` | `RETAIN_AS_SLICE` | G3/G5 | Clean extraction of source-readiness logic; land before source-readiness UI work. |
| `backend/tests/api/test_operator_cases_runtime_provenance.py` | `REWORK_NARROWLY` | G5 | Keep only with runtime provenance bridge slice. |
| `backend/tests/api/test_ui_api_key_auth.py` | `REWORK_NARROWLY` | G1/G6 | Auth tests should lead the local-auth reconstruction. |
| `backend/tests/api/test_ui_deployment_readiness.py` | `RETAIN_AS_SLICE` | G3/G7 | Pair with the read-only deployment readiness surface after package manifest lands. |
| `backend/tests/api/test_ui_dossier_readiness.py` | `DEFER` | G5 | Dossier readiness tests wait until the orientation surface is deliberately selected. |
| `backend/tests/api/test_ui_expansion_readiness.py` | `DEFER` | G3/G10 | Expansion tests wait for expansion readiness decision. |
| `backend/tests/api/test_ui_live_connector_jobs.py` | `REWORK_NARROWLY` | G5 | Source/runtime route tests need source-rights review. |
| `backend/tests/api/test_ui_observability_readiness.py` | `RETAIN_AS_SLICE` | G8 | Pair with local-only observability readiness surface; hosted blockers stay explicit. |
| `backend/tests/api/test_ui_operations_guardrails.py` | `RETAIN_AS_SLICE` | G6 | Pair with isolated operations guardrails surface. |
| `backend/tests/api/test_ui_operations_routes.py` | `REWORK_NARROWLY` | G6 | Existing operations route changes need isolated replay. |
| `backend/tests/api/test_ui_performance_guardrails.py` | `RETAIN_AS_SLICE` | G6 | Pair with isolated performance guardrails surface. |
| `backend/tests/api/test_ui_product_correctness.py` | `DEFER` | G6 | Product-correctness tests wait until lower semantic surfaces settle. |
| `backend/tests/api/test_ui_production_authority.py` | `DEFER` | G3/G6 | Production authority view waits on external-authority framing. |
| `backend/tests/api/test_ui_raw_data_inventory.py` | `RETAIN_AS_SLICE` | G1 | Best focused raw-data inventory test target; implementation must remain read-only and avoid hidden seeding. |
| `backend/tests/api/test_ui_readiness_overview.py` | `DEFER` | G3 | Later readiness surface; land after raw-data/auth baseline and helper contracts. |
| `backend/tests/api/test_ui_release_readiness.py` | `DEFER` | G3/G7 | Later release-readiness surface; pair with release catalog/checker when selected. |
| `backend/tests/api/test_ui_review_routes.py` | `REWORK_NARROWLY` | G1/G6 | Reviewer route tests must preserve protected route behavior. |
| `backend/tests/api/test_ui_routes.py` | `REWORK_NARROWLY` | G1 | Use as the main local browser posture test source. |
| `backend/tests/api/test_ui_security_guardrails.py` | `RETAIN_AS_SLICE` | G6 | Pair with isolated security guardrails surface. |
| `backend/tests/api/test_ui_selected_geography_coverage.py` | `DEFER` | G3/G10 | Later coverage surface; wait for selected-geography authority review. |
| `backend/tests/source_registry/test_source_readiness.py` | `RETAIN_AS_SLICE` | G3/G5 | Focused proof for the source-readiness packaged module. |
| `backend/tests/test_deployment_smoke_scripts.py` | `REWORK_NARROWLY` | G2/G7 | Smoke wrapper tests should follow runtime smoke boundaries. |
| `backend/tests/test_local_deployment_artifacts.py` | `DEFER` | G3/G7 | Local deployment catalog asserts many later routes; wait for retained route set. |
| `backend/tests/test_observability_readiness_artifacts.py` | `RETAIN_AS_SLICE` | G8 | Pair with local-only observability catalog/checker. |
| `backend/tests/test_package_manifest_check.py` | `RETAIN_AS_SLICE` | G7 | Standalone package manifest gate candidate; validate before CI hook. |
| `backend/tests/test_private_mvp_readiness.py` | `RETAIN_AS_SLICE` | G3/G5 | Static selected-county source-provenance catalog proof is useful and validate-only. |
| `backend/tests/test_release_package_artifacts.py` | `RETAIN_AS_SLICE` | G7 | Narrow release-package manifest verification extension. |
| `backend/tests/test_release_readiness_artifacts.py` | `REWORK_NARROWLY` | G3/G7 | Pair with release readiness checker/catalog only. |
| `backend/tests/test_ui_browser_smoke_scripts.py` | `REWORK_NARROWLY` | G2 | Browser smoke expectations depend on accepted UI slices. |
| `backend/tests/test_ui_runtime_smoke_script.py` | `REWORK_NARROWLY` | G2 | Runtime smoke expectations depend on accepted UI slices. |
| `config/access_control.yaml` | `REWORK_NARROWLY` | G1/G6 | Config must match proven local/non-local auth behavior. |
| `config/local_deployment.yaml` | `DEFER` | G3/G7 | Catalog asserts many later routes; wait for retained route set. |
| `config/observability_readiness.yaml` | `RETAIN_AS_SLICE` | G8 | Local-only observability catalog; keep hosted blockers explicit. |
| `config/private_mvp_beta_readiness.yaml` | `RETAIN_AS_SLICE` | G3/G5 | Static selected-county source-provenance catalog; keep fixture/non-live labels explicit. |
| `config/release_readiness.yaml` | `REWORK_NARROWLY` | G3/G7 | Release readiness catalog changes pair with checker proof. |
| `DESIGN.md` | `REWORK_NARROWLY` | G1-G8 | Keep only paragraphs matching landed behavior; defer broad readiness/guardrail/deployment claims. |
| `docs/IMPLEMENTATION_READINESS.md` | `DEFER` | G3/G7 | Readiness status doc should follow merged proof only. |
| `docs/planning_pack/api/openapi_stub.yaml` | `DISCARD_GENERATED` | G3/G5 | Regenerate the planning-pack mirror from the final retained API set. |
| `docs/runbooks/access_control.md` | `REWORK_NARROWLY` | G1/G6 | Runbook must track proven local-auth behavior only. |
| `docs/runbooks/mvp_operator.md` | `REWORK_NARROWLY` | G1/G3 | Operator runbook should update per merged UI slice. |
| `docs/runbooks/release_package.md` | `RETAIN_AS_SLICE` | G7 | Narrowly document post-build manifest verification with package checker proof. |
| `docs/runbooks/release_readiness.md` | `REWORK_NARROWLY` | G3/G7 | Pair with release readiness checker proof. |
| `MANIFEST.md` | `DEFER` | G1-G8 | Routing index changes only after source-of-truth files are retained. |
| `plans/2026-06-19-account-free-runtime.md` | `ARCHIVE_REFERENCE` | G4 | Preserve as candidate plan evidence; do not publish as active plan. |
| `plans/2026-06-19-ci-package-manifest-gate.md` | `ARCHIVE_REFERENCE` | G7 | Preserve plan facts for package gate slice. |
| `plans/2026-06-19-db-backed-local-ui-smoke.md` | `ARCHIVE_REFERENCE` | G2 | Preserve plan facts for smoke slice. |
| `plans/2026-06-19-dossier-ui.md` | `ARCHIVE_REFERENCE` | G5 | Preserve plan facts for dossier UI slice. |
| `plans/2026-06-19-evidence-deps.md` | `ARCHIVE_REFERENCE` | G5 | Preserve plan facts for evidence dependencies. |
| `plans/2026-06-19-local-account-disabled-raw-ui.md` | `ARCHIVE_REFERENCE` | G4 | Preserve plan facts for account-free runtime. |
| `plans/2026-06-19-local-auth-surface-hardening.md` | `ARCHIVE_REFERENCE` | G6 | Preserve plan facts for auth hardening. |
| `plans/2026-06-19-local-deployment-readiness-ui.md` | `ARCHIVE_REFERENCE` | G3/G7 | Preserve plan facts for deployment readiness. |
| `plans/2026-06-19-local-expansion-readiness-ui.md` | `ARCHIVE_REFERENCE` | G3/G10 | Preserve plan facts; implementation deferred. |
| `plans/2026-06-19-local-only-raw-data-ui.md` | `ARCHIVE_REFERENCE` | G1 | Preserve plan facts; R-023 must be reconstructed. |
| `plans/2026-06-19-local-production-authority-ui.md` | `ARCHIVE_REFERENCE` | G3/G6 | Preserve plan facts; external authority remains blocked. |
| `plans/2026-06-19-local-production-profile.md` | `ARCHIVE_REFERENCE` | G4 | Preserve plan facts for local profile only. |
| `plans/2026-06-19-local-project-trajectory-ui.md` | `ARCHIVE_REFERENCE` | G4 | Preserve plan facts for later route consolidation. |
| `plans/2026-06-19-local-readiness-overview-ui.md` | `ARCHIVE_REFERENCE` | G3 | Preserve plan facts for readiness overview. |
| `plans/2026-06-19-local-release-readiness-ui.md` | `ARCHIVE_REFERENCE` | G3/G7 | Preserve plan facts for release readiness. |
| `plans/2026-06-19-local-selected-geography-coverage-ui.md` | `ARCHIVE_REFERENCE` | G3/G10 | Preserve plan facts for coverage review. |
| `plans/2026-06-19-local-validation-evidence-ui.md` | `ARCHIVE_REFERENCE` | G4 | Preserve plan facts for validation evidence UI. |
| `plans/2026-06-19-observability-readiness-ui.md` | `ARCHIVE_REFERENCE` | G8 | Preserve plan facts; implementation deferred. |
| `plans/2026-06-19-operations-guardrails-ui.md` | `ARCHIVE_REFERENCE` | G6 | Preserve plan facts for operations guardrails. |
| `plans/2026-06-19-performance-guardrails-ui.md` | `ARCHIVE_REFERENCE` | G6 | Preserve plan facts for performance guardrails. |
| `plans/2026-06-19-product-correctness-guardrails-ui.md` | `ARCHIVE_REFERENCE` | G6 | Preserve plan facts for product correctness guardrails. |
| `plans/2026-06-19-raw-claim-task-inventory.md` | `ARCHIVE_REFERENCE` | G5 | Preserve plan facts for claim/task inventory. |
| `plans/2026-06-19-raw-evidence-provenance-ui.md` | `ARCHIVE_REFERENCE` | G5 | Preserve plan facts for evidence provenance UI. |
| `plans/2026-06-19-raw-source-readiness-ui.md` | `ARCHIVE_REFERENCE` | G3/G5 | Preserve plan facts for source readiness. |
| `plans/2026-06-19-release-package-manifest-verification.md` | `ARCHIVE_REFERENCE` | G7 | Preserve plan facts for package manifest gate. |
| `plans/2026-06-19-release-readiness-deployment-smoke-guard.md` | `ARCHIVE_REFERENCE` | G2/G7 | Preserve plan facts for deployment smoke guard. |
| `plans/2026-06-19-report-list-contract-overlay.md` | `ARCHIVE_REFERENCE` | G5 | Preserve plan facts for report list contract. |
| `plans/2026-06-19-report-run-inventory-ui.md` | `ARCHIVE_REFERENCE` | G5 | Preserve plan facts for report-run inventory UI. |
| `plans/2026-06-19-security-guardrails-ui.md` | `ARCHIVE_REFERENCE` | G6 | Preserve plan facts for security guardrails. |
| `plans/2026-06-19-selected-county-provenance-status-ui.md` | `ARCHIVE_REFERENCE` | G5 | Preserve plan facts for provenance status. |
| `plans/2026-06-19-selected-county-runtime-provenance-bridge.md` | `ARCHIVE_REFERENCE` | G5 | Preserve plan facts for runtime provenance bridge. |
| `plans/2026-06-19-selected-county-source-provenance-catalog.md` | `ARCHIVE_REFERENCE` | G5 | Preserve plan facts for source provenance catalog. |
| `plans/2026-06-19-source-provenance-ui.md` | `ARCHIVE_REFERENCE` | G5 | Preserve plan facts for source provenance UI. |
| `plans/2026-06-19-validation-proof-ui.md` | `ARCHIVE_REFERENCE` | G4 | Preserve plan facts for validation proof UI. |
| `plans/README.md` | `ARCHIVE_REFERENCE` | REC-001 | Dirty-root plan routing must not become live routing. |
| `scripts/access_control_check.py` | `REWORK_NARROWLY` | G1/G6 | Checker changes must match auth config/runbook updates. |
| `scripts/local_deployment_check.py` | `DEFER` | G3/G7 | Checker asserts many later routes; wait for retained route set. |
| `scripts/observability_readiness_check.py` | `RETAIN_AS_SLICE` | G8 | Local-only observability checker; hosted evidence remains blocked. |
| `scripts/package_manifest_check.py` | `RETAIN_AS_SLICE` | G7 | Standalone package manifest checker candidate. |
| `scripts/private_mvp_readiness_check.py` | `RETAIN_AS_SLICE` | G3/G5 | Static selected-county source-provenance validator; land before runtime provenance bridge. |
| `scripts/release_package_check.py` | `RETAIN_AS_SLICE` | G7 | Narrow extension to require/check package manifest validator. |
| `scripts/release_readiness_check.py` | `REWORK_NARROWLY` | G3/G7 | Pair with release readiness catalog/test slice. |
| `scripts/run_deployment_smoke.ps1` | `REWORK_NARROWLY` | G2/G7 | Wrapper should follow accepted deployment smoke behavior. |
| `scripts/run_deployment_smoke.sh` | `REWORK_NARROWLY` | G2/G7 | POSIX wrapper mirrors PowerShell wrapper after behavior lands. |
| `scripts/run_local_deployment_check.ps1` | `DEFER` | G3/G7 | Wrapper waits with local deployment checker. |
| `scripts/run_local_deployment_check.sh` | `DEFER` | G3/G7 | Wrapper waits with local deployment checker. |
| `scripts/run_observability_readiness_check.ps1` | `RETAIN_AS_SLICE` | G8 | Wrapper pairs with local-only observability checker. |
| `scripts/run_observability_readiness_check.sh` | `RETAIN_AS_SLICE` | G8 | Wrapper pairs with local-only observability checker. |
| `scripts/run_package_manifest_check.ps1` | `RETAIN_AS_SLICE` | G7 | Wrapper pairs with package manifest checker. |
| `scripts/run_package_manifest_check.sh` | `RETAIN_AS_SLICE` | G7 | Wrapper pairs with package manifest checker. |
| `scripts/source_readiness.py` | `RETAIN_AS_SLICE` | G3/G5 | Wrapper for packaged source-readiness logic; pair with module/tests. |
| `scripts/ui_browser_smoke.mjs` | `REWORK_NARROWLY` | G2 | Broad smoke script references later routes; rebuild per accepted UI slice. |
| `scripts/ui_runtime_smoke.py` | `REWORK_NARROWLY` | G2 | Broad smoke script references later routes; rebuild per accepted UI slice. |
| `state/LEVEL_9_10_GATE_MATRIX.md` | `ARCHIVE_REFERENCE` | REC-001 | Candidate readiness claims must not replace live gate state. |
| `state/PROJECT_STATE.md` | `ARCHIVE_REFERENCE` | REC-001 | Candidate state prose preserved as evidence only. |
| `state/VALIDATION_LOG.md` | `ARCHIVE_REFERENCE` | REC-001 | Candidate validation prose preserved; rerun per slice. |
| `state/WORKLOG.md` | `ARCHIVE_REFERENCE` | REC-001 | Candidate worklog preserved; not live completion proof. |
| `tasks/task_queue.yaml` | `ARCHIVE_REFERENCE` | REC-001 | Candidate task progression must not become live routing. |

## Ignored Runtime State

| Path | Decision | Reason |
|---|---|---|
| `.codesight/` | `DISCARD_GENERATED` | Local index; regenerate when needed. |
| `.mypy_cache/` | `DISCARD_GENERATED` | Tool cache; never product authority. |
| `.pytest_cache/` | `DISCARD_GENERATED` | Tool cache; never product authority. |
| `.ruff_cache/` | `DISCARD_GENERATED` | Tool cache; never product authority. |
| `local_artifacts/` | `DISCARD_GENERATED` | Runtime proof artifacts remain local/ignored unless a package boundary explicitly includes a derived artifact. |

## Focused PR Sequence

1. `REC-001`: Merge the reconciliation control plane after validation. No product
   behavior changes.
2. `G7a`: Land package-manifest validator, release-package manifest verification, and
   the additive CI gate. This is the cleanest early retained slice because it is
   validate-only, package-boundary scoped, and does not depend on broad UI routes.
3. `G3a`: Extract source-readiness logic into the packaged module and keep CLI/tests
   focused on source-rights/freshness fail-closed behavior.
4. `G1a`: Reconstruct local account-free/auth posture from live `origin/main`.
   Start with auth/reviewer UI tests, access-control catalog/checker/docs, and
   explicit `APP_ENV` versus `REQUIRE_API_KEY` protected-mode behavior.
5. `G1b`: Reconstruct the raw-data inventory route from live `origin/main`.
   Use the focused raw-data test and keep GET behavior read-only with no hidden seeding.
6. `G3b`: Land the selected-county source-provenance catalog and validate-only checker
   with explicit fixture/non-live labels.
7. `G2`: Rebuild runtime/browser smoke around the accepted G1 UI only, then add
   DB-backed/local deployment smoke if still required.
8. `G3`: Add readiness/source/selected-geography views only after route ownership and
   OpenAPI/update scope are clear.
9. `G5`: Add report/source/evidence provenance surfaces only with report contract,
   source-rights, source-failure, non-live labeling, and workspace-scope proof.
10. `G6`: Add local guardrail/auth-hardening surfaces separately from readiness pages.
11. `G8`: Revisit observability readiness after local deployment/release boundaries are
   merged and external hosted-observability blockers remain explicit.

## Current Lane 1 Status

The initial disposition table remains historical authority for how the dirty-root
candidate stack was first classified relative to `c3364ea...`. It is no longer a fresh
next-slice queue: `REC-001` and retained G-slices through `G9a` have now landed on live
`origin/main`, with PR #101 merged at `b525439e6bcddefba81c7d6bf12290b3f8551b55`.

Lane 1 is still not complete. The preserved dirty-root candidate workspace must now be
reconciled against the current live baseline and each path/concept should be marked as
already landed, landed differently, still divergent, still blocked/deferred, obsolete,
or coordination/generated. The next safe action is `REC-002`: regenerate that residual
inventory from current `origin/main`, then choose the next retained engineering slice
from fresh evidence.
