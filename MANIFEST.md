# Manifest

Use this as the repo/file routing index. It is intentionally not an exhaustive file listing.

## Always-check files for a fresh session

| File | Purpose |
|---|---|
| `AGENTS.md` | Canonical operating contract for Codex and other agents |
| `CLAUDE.md` | Claude Code adapter importing `AGENTS.md` |
| `README.md` | Human/project overview |
| `MILESTONE_MAP.md` | Authoritative 10-level maturity gate map |
| `LANE_OWNERSHIP.md` | 4-lane file ownership and isolation rules (read if working in a lane) |
| `state/PROJECT_STATE.md` | Overall milestone, active plan, next task, known blockers |
| `plans/*.md` | Executable implementation plans |

## Lane-specific entry points

If you are a **lane agent**, start here after reading the always-check files above:

| Lane | Operating contract | State | Plan |
|---|---|---|---|
| Lane A — Source Registry + DB | `lanes/lane-a/AGENTS.md` | `state/lane-a-state.md` | `plans/lane-a-*.md` |
| Lane B — Area + Geometry | `lanes/lane-b/AGENTS.md` | `state/lane-b-state.md` | `plans/lane-b-*.md` |
| Lane C — Evidence + Claims | `lanes/lane-c/AGENTS.md` | `state/lane-c-state.md` | `plans/lane-c-*.md` |
| Lane D — Reports + API + Infra | `lanes/lane-d/AGENTS.md` | `state/lane-d-state.md` | `plans/lane-d-*.md` |

## Source-of-truth areas

| Area | Files | Notes |
|---|---|---|
| Product scope | `docs/PRODUCT_SPEC.md`, `docs/planning_pack/05_MVP_US_RURAL_LAND_DOSSIER_SPEC.md` | Product behavior and non-goals |
| Operator UI design | `DESIGN.md` | Active private operator console contract: UI information architecture, visual language, accessibility target, auth posture, and implementation constraints |
| Architecture | `docs/ARCHITECTURE.md`, `docs/adr/*.md` | Stable component boundaries and decisions |
| Maturity gates | `MILESTONE_MAP.md` | Authoritative maturity levels and gates |
| Empirical qualification | `docs/adr/0004-empirical-qualification-control-plane.md`, `docs/qualification/**`, `docs/qualification/P0_AUTO_EVIDENCE.yaml`, `docs/qualification/readiness-crosswalk.md`, `config/qualification/**`, `config/qualification/readiness_crosswalk.yaml`, `schemas/qualification/**`, `state/EMPIRICAL_QUALIFICATION_STATUS.yaml`, `state/QUALIFICATION_PARAMETERIZATION_BACKLOG.md`, `state/owner-decision-packet.md`, `scripts/validate_qualification.py`, `scripts/selftest_qualification_validator.py`, `scripts/qualification_checker_advertisement.py`, `scripts/qualification_status_check.py`, `scripts/qualification_change_impact_check.py`, `scripts/qualification_p0_evidence_check.py`, `plans/2026-06-21-empirical-qualification-adoption.md`, `plans/2026-06-21-eqp2-1-status-check.md`, `plans/2026-06-21-eqp2-2-change-impact.md`, `plans/2026-06-21-eqp2-3-p0-auto-evidence.md`, `plans/2026-06-21-eqp2-4-checker-parity.md` | Canonical empirical-validity control plane; the imported spine validates structurally, backlog records blocked owner/source/AOI decisions, owner-decision packet maps consequences without authorizing changes, readiness/authority gates report into qualification through a checked crosswalk, status is derived from real checker exits and checker-advertised criterion IDs, change-impact invalidation is executable and advisory from matrix-owned path globs plus crosswalk surfaces, selected P0 repo-local evidence rows are linked as blocked evidence only, checker advertisement parity is validated, and no qualification `PASS` exists until owner decisions and empirical evidence are frozen |
| Lane isolation | `LANE_OWNERSHIP.md` | File ownership per lane |
| DB/schema | `docs/POSTGRES_FIRST_STORAGE.md`, `db/migrations/**`, `db/seeds/**`, `db/migrations/MIGRATION_REGISTRY.md` | Postgres/PostGIS is authoritative; Lane A stewards migrations |
| Backend source | `backend/app/**` | Application code organized by lane module |
| Backend tests | `backend/tests/**` | Per-lane subdirectories: source_registry/, area_geometry/, evidence_ledger/, claims_engine/, reports/, api/ |
| Shared domain | `backend/app/domain/` | Shared enums, protocols, per-lane contracts; see LANE_OWNERSHIP.md for ownership |
| Data/source strategy | `docs/DATA_SOURCE_STRATEGY.md`, `registers/data_source_registry.csv`, `docs/source-reviews/*.md`, `schemas/source_schema.json`, `backend/app/source_registry/readiness.py`, `scripts/source_readiness.py` | Source metadata, licensing, provenance, and source-readiness proof |
| Source entitlements | `config/source_entitlements.yaml`, `docs/runbooks/source_entitlements.md`, `scripts/source_entitlement_check.py`, `scripts/run_source_entitlement_check.ps1`, `scripts/run_source_entitlement_check.sh`, `state/PRODUCTION_AUTHORITY_PACKET.md` | Validate-only DS-017 decision packet and checker for vendor/license/rights/field/cost/connector authority; does not approve DS-017 |
| Production authority intake | `config/production_authority_intake.yaml`, `docs/runbooks/production_authority_intake.md`, `scripts/production_authority_intake_check.py`, `scripts/run_production_authority_intake_check.ps1`, `scripts/run_production_authority_intake_check.sh`, `state/PRODUCTION_AUTHORITY_PACKET.md` | Validate-only cross-catalog intake guard for DS-017, hosted, secrets, identity/RBAC, image-publication, billing, hosted-observability, and Bologna recorded-source authority; every stream remains blocked until cited external evidence exists |
| Bologna preflight | `config/bologna_preflight.yaml`, `docs/runbooks/bologna_preflight.md`, `scripts/bologna_preflight_check.py`, `scripts/run_bologna_preflight_check.ps1`, `scripts/run_bologna_preflight_check.sh`, `state/PRODUCTION_AUTHORITY_PACKET.md` | Validate-only recorded-source pilot preflight for Bologna authority, source-rights, rulepack scope, DS-017 treatment, hosted boundary, and multi-geography sequencing; does not start Bologna |
| Bologna source candidates | `config/bologna_source_candidates.yaml`, `docs/runbooks/bologna_source_candidates.md`, `docs/source-reviews/bologna-source-candidates.md`, `scripts/bologna_source_candidates_check.py`, `scripts/run_bologna_source_candidates_check.ps1`, `scripts/run_bologna_source_candidates_check.sh` | Validate-only candidate inventory for future Bologna source-rights review; does not approve sources, promote source registry rows, run connectors, or allow report/runtime use |
| Bologna source rights | `config/bologna_source_rights.yaml`, `docs/runbooks/bologna_source_rights.md`, `docs/source-reviews/bologna-source-rights.md`, `scripts/bologna_source_rights_check.py`, `scripts/run_bologna_source_rights_check.ps1`, `scripts/run_bologna_source_rights_check.sh` | Validate-only rights matrix for Bologna source candidates; every candidate remains pending and blocked until source-schema, license, cache, export, AI-use, raw-data, attribution, fixture, and report-use decisions are reviewed |
| Bologna pilot-scope authority | `config/bologna_pilot_scope_authority.yaml`, `docs/runbooks/bologna_pilot_scope_authority.md`, `scripts/bologna_pilot_scope_authority_check.py`, `scripts/run_bologna_pilot_scope_authority_check.ps1`, `scripts/run_bologna_pilot_scope_authority_check.sh` | Validate-only first-gate product/AOI/scope authority packet for Bologna; keeps source-authority updates, source-rights changes, recorded corpus work, runtime/report proof, DS-017 approval, and Bologna implementation blocked |
| Bologna owner answer intake | `config/bologna_owner_answer_intake.yaml`, `docs/runbooks/bologna_owner_answer_intake.md`, `scripts/bologna_owner_answer_intake_check.py`, `scripts/run_bologna_owner_answer_intake_check.ps1`, `scripts/run_bologna_owner_answer_intake_check.sh` | Validate-only owner-answer intake for ODP-BOL-001 through ODP-BOL-004; aligns product/AOI, source-rights, recorded-corpus, and DB-report-proof questions with existing authority packets without recording authority or unlocking work |
| Bologna ODP-BOL-001 owner response gate | `config/bologna_odp1_owner_response_gate.yaml`, `docs/runbooks/bologna_odp1_owner_response_gate.md`, `scripts/bologna_odp1_owner_response_gate_check.py`, `scripts/run_bologna_odp1_owner_response_gate_check.ps1`, `scripts/run_bologna_odp1_owner_response_gate_check.sh` | Validate-only product/AOI owner-response gate for ODP-BOL-001; cross-checks the required owner answer and pilot-scope authority evidence while keeping owner answers, authority records, and downstream updates empty |
| Bologna source-authority intake | `config/bologna_source_authority_intake.yaml`, `docs/runbooks/bologna_source_authority_intake.md`, `scripts/bologna_source_authority_intake_check.py`, `scripts/run_bologna_source_authority_intake_check.ps1`, `scripts/run_bologna_source_authority_intake_check.sh` | Validate-only intake guard for future Bologna source/AOI authority; cross-checks candidate evidence slots against the source-rights matrix and remains blocked until cited authority exists |
| Bologna recorded-source corpus | `config/bologna_recorded_source_corpus.yaml`, `docs/runbooks/bologna_recorded_source_corpus.md`, `scripts/bologna_recorded_source_corpus_check.py`, `scripts/run_bologna_recorded_source_corpus_check.ps1`, `scripts/run_bologna_recorded_source_corpus_check.sh` | Validate-only recorded-source corpus contract for future Bologna fixture manifests; cross-checks source-authority and source-rights evidence slots and keeps fixture capture, source-failure fixtures, runtime use, report use, and DB seeds blocked |
| Evidence/claims | `schemas/evidence_schema.json`, `schemas/claim_schema.json`, `config/ruleset_homestead_mvp.yaml` | Claim-first semantics |
| Reports | `backend/app/domain/report_contracts.py`, `schemas/report_run_schema.json`, `backend/tests/reports/test_report_regression.py` | Report-run contract, JSON schema, and stable artifact semantics |
| Agent operations | `.agent/PLANS.md`, `docs/AGENT_OPERATING_MODEL.md`, `.claude/skills/**`, `.claude/agents/**` | Long-form agent procedures; not startup context |
| Validation | `scripts/verify.sh`, `scripts/verify.ps1`, `scripts/validate_workspace.sh`, `scripts/validate_workspace.ps1`, `scripts/run_ui_browser_smoke.ps1`, `scripts/run_ui_browser_smoke.sh`, `scripts/ui_browser_smoke.mjs`, `scripts/ui_runtime_smoke.py`, `.github/workflows/ci.yml` | Executable gates, including explicit UI smoke gates |
| Deployment smoke | `scripts/run_deployment_smoke.ps1`, `scripts/run_deployment_smoke.sh` | Compose-backed deployment smoke for health, metrics, queue health, and report workflow |
| Connector runbook | `docs/connectors/connector_runbook.md` | Connector interface, run lifecycle, failure taxonomy, quality gates, and the two fixture corpora (embedded API vs. county golden) and their reachability gap |
| MVP operator runbook | `docs/runbooks/mvp_operator.md` | Startup, API workflow, configuration, known limitations |
| Backup/restore runbook | `docs/runbooks/backup_restore.md`, `scripts/run_backup_restore_check.ps1`, `scripts/run_backup_restore_check.sh` | Restore-proof workflow for Level 10 DB recovery validation |
| Incident/rollback runbook | `docs/runbooks/incident_response.md`, `scripts/incident_rollback_check.py`, `scripts/run_incident_rollback_check.ps1`, `scripts/run_incident_rollback_check.sh` | Severity, ownership, escalation, rollback, and recovery proof |
| Data retention | `config/data_retention.yaml`, `docs/runbooks/data_retention.md`, `scripts/data_retention_check.py`, `scripts/run_data_retention_check.ps1`, `scripts/run_data_retention_check.sh`, `scripts/purge_audit_events.py` | Retention classes, audit purge tooling, and manual deletion guardrails |
| Alerting runbook | `config/ops_alert_rules.yaml`, `docs/runbooks/alerting.md`, `scripts/alert_rules_check.py`, `scripts/run_alert_rules_check.ps1`, `scripts/run_alert_rules_check.sh` | Repo-local alert rules for high-severity failures, queue health, and stale source metadata |
| Operations guardrails | `backend/app/operations_guardrails.py`, `config/ops_alert_rules.yaml`, `config/data_retention.yaml`, `config/ops_cost_monitoring.yaml`, `docs/runbooks/alerting.md`, `docs/runbooks/incident_response.md`, `docs/runbooks/backup_restore.md`, `docs/runbooks/data_retention.md`, `docs/runbooks/cost_monitoring.md` | Local read-only operations guardrails UI data for alerting, incident, backup/restore, retention, queue/recovery, and cost boundaries; hosted alerting/pager/scheduler/billing/backup authority remains blocked |
| Performance guardrails | `backend/app/performance_guardrails.py`, `config/performance_baseline.yaml`, `config/spatial_query_plan.yaml`, `docs/runbooks/performance.md`, `docs/runbooks/load_testing.md`, `backend/app/operations/backpressure.py`, `scripts/performance_baseline_check.py`, `scripts/spatial_query_plan_check.py`, `scripts/spatial_query_plan_runtime_check.py` | Local read-only performance guardrails UI data for load-test baseline, spatial query-plan, and queue-backpressure boundaries; live load, runtime DB EXPLAIN, hosted SLO/capacity, and Level 10 authority remain blocked |
| Observability readiness | `backend/app/observability_readiness.py`, `config/observability_readiness.yaml`, `backend/app/core/metrics.py`, `backend/app/api/metrics.py`, `backend/app/connectors/observability.py`, `config/ops_alert_rules.yaml`, `config/hosted_deployment.yaml`, `config/data_retention.yaml`, `scripts/observability_readiness_check.py`, `scripts/run_observability_readiness_check.ps1`, `scripts/run_observability_readiness_check.sh` | Local read-only observability readiness UI data for metrics, queue/recovery, connector events, source-failure evidence, deployment-smoke references, alert-rule coverage, and hosted-observability blockers; hosted dashboards, alert routing, pager/on-call, hosted log retention, production traffic observability, and Level 10 authority remain blocked |
| Supply-chain checks | `.github/workflows/ci.yml`, `.github/dependabot.yml`, `docs/runbooks/supply_chain.md`, `scripts/supply_chain_check.py`, `scripts/run_supply_chain_check.ps1`, `scripts/run_supply_chain_check.sh` | CI dependency vulnerability scan, dependency update hygiene, and dependency artifact attestation wiring |
| Dependency provenance | `backend/requirements-prod.lock`, `docs/sbom/backend-prod-sbom.json`, `docs/runbooks/dependency_provenance.md`, `scripts/provenance_check.py`, `scripts/run_provenance_check.ps1`, `scripts/run_provenance_check.sh` | Hashed backend production lock, SBOM, GitHub artifact attestation wiring, and validate-only provenance proof |
| Container image scan | `backend/Dockerfile`, `.dockerignore`, `.github/workflows/ci.yml`, `docs/runbooks/container_image_scan.md`, `scripts/container_scan_check.py`, `scripts/run_container_scan_check.ps1`, `scripts/run_container_scan_check.sh` | Digest-pinned backend base image plus CI Docker Scout scan for the locally built backend image and runtime base packages |
| Cost monitoring | `config/ops_cost_monitoring.yaml`, `docs/runbooks/cost_monitoring.md`, `scripts/cost_monitoring_check.py`, `scripts/run_cost_monitoring_check.ps1`, `scripts/run_cost_monitoring_check.sh` | Cost categories, report cost metrics, zero-dollar attribution, and paid-source guardrails |
| Access control | `config/access_control.yaml`, `backend/app/security_guardrails.py`, `docs/runbooks/access_control.md`, `docs/runbooks/mvp_operator.md`, `DESIGN.md`, `scripts/access_control_check.py`, `scripts/run_access_control_check.ps1`, `scripts/run_access_control_check.sh` | API-key, UI API-key cookie bridge, scoped reviewer service-account, protected-route posture, full user-RBAC blockers, and local read-only security guardrails UI data |
| Threat/proxy audit | `config/threat_proxy_audit.yaml`, `docs/runbooks/threat_proxy_audit.md`, `scripts/threat_proxy_audit_check.py`, `scripts/run_threat_proxy_audit_check.ps1`, `scripts/run_threat_proxy_audit_check.sh` | Validate-only map for security, access-control, protected-class, demographic-proxy, residential-steering, recommendation/ranking, suitability, overclaim, source-rights, and error-leakage boundaries |
| Readiness core | `backend/app/project_readiness.py`, `backend/app/release_readiness.py`, `backend/tests/test_readiness_core_artifacts.py`, `state/PROJECT_STATE.md`, `state/LEVEL_9_10_GATE_MATRIX.md`, `tasks/task_queue.yaml`, `state/VALIDATION_LOG.md` | Read-only app-layer parser models for current project routing and release readiness; these are views over existing authority files, not new authority |
| Release readiness | `config/release_readiness.yaml`, `backend/app/release_readiness.py`, `docs/runbooks/release_readiness.md`, `scripts/run_release_readiness_check.ps1`, `scripts/run_release_readiness_check.sh` | Repo-local release gate catalog, read-only app model, and validate-only readiness proof |
| Release package | `config/release_package.yaml`, `docs/runbooks/release_package.md`, `scripts/build_release_package.py`, `scripts/build_release_package.ps1`, `scripts/build_release_package.sh`, `scripts/package_manifest_check.py`, `scripts/release_package_check.py`, `scripts/run_package_manifest_check.ps1`, `scripts/run_package_manifest_check.sh`, `scripts/run_release_package_check.ps1`, `scripts/run_release_package_check.sh` | Local source/runtime/operator ZIP package boundary, manifest, post-build manifest verification, and validate-only package proof |
| Image publication | `config/image_publication.yaml`, `docs/runbooks/image_publication.md`, `scripts/image_publication_check.py`, `scripts/run_image_publication_check.ps1`, `scripts/run_image_publication_check.sh` | Registry image publication boundary, required evidence, blockers, and validate-only proof |
| Hosted deployment | `config/hosted_deployment.yaml`, `docs/runbooks/hosted_deployment.md`, `scripts/hosted_deployment_check.py`, `scripts/run_hosted_deployment_check.ps1`, `scripts/run_hosted_deployment_check.sh` | Hosted deployment runtime input/evidence boundary, blockers, and validate-only proof |
| Private MVP readiness | `config/private_mvp_beta_readiness.yaml`, `backend/app/source_provenance.py`, `scripts/run_private_mvp_readiness_check.ps1`, `scripts/run_private_mvp_readiness_check.sh`, `scripts/private_mvp_readiness_check.py` | Private beta gate catalog separating DS-017/hosted-production blockers from the selected NC county private-MVP utility proof, including selected-county source scope, county manifest scope, source-provenance expectations, and local read-only source-provenance UI data |
| Readiness checklists | `docs/checklists/jurisdiction_readiness.md`, `docs/checklists/rulepack_readiness.md`, `config/checklist_dry_run.yaml`, `docs/runbooks/checklist_dry_run.md`, `scripts/checklist_dry_run_check.py`, `scripts/run_checklist_dry_run_check.ps1`, `scripts/run_checklist_dry_run_check.sh` | Mandatory pre-release checklists for new jurisdictions/rulepacks plus validate-only dry-run proof that each checklist item is classified before expansion |
| Comprehensive reference | `docs/planning_pack/**` | Read only when needed for ambiguity or major changes |

## Protected files

- `.env*`, except `.env.example`
- production secrets, credentials, private keys
- paid/vendor data dumps
- migration history after it is applied outside local development
- generated artifacts unless regenerated by the documented command

## Generated or derivative files

| Path | Source | Rule |
|---|---|---|
| `.codesight/` | local Codesight index | ignore in git; regenerate with `npx codesight --index` when needed |
| `docs/planning_pack/planning_registers.xlsx` | earlier planning pass | do not edit manually unless regenerating registers |
| future API clients | OpenAPI contract | do not edit generated clients directly |
| future report PDFs | report compiler | store output under ignored local artifact path |

## Update rule

Update this file only when source-of-truth locations, protected areas, or generated-file rules change.
