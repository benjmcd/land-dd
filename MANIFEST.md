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
| Architecture | `docs/ARCHITECTURE.md`, `docs/adr/*.md` | Stable component boundaries and decisions |
| Maturity gates | `MILESTONE_MAP.md` | Authoritative maturity levels and gates |
| Lane isolation | `LANE_OWNERSHIP.md` | File ownership per lane |
| DB/schema | `docs/POSTGRES_FIRST_STORAGE.md`, `db/migrations/**`, `db/seeds/**`, `db/migrations/MIGRATION_REGISTRY.md` | Postgres/PostGIS is authoritative; Lane A stewards migrations |
| Backend source | `backend/app/**` | Application code organized by lane module |
| Backend tests | `backend/tests/**` | Per-lane subdirectories: source_registry/, area_geometry/, evidence_ledger/, claims_engine/, reports/, api/ |
| Shared domain | `backend/app/domain/` | Shared enums, protocols, per-lane contracts; see LANE_OWNERSHIP.md for ownership |
| Data/source strategy | `docs/DATA_SOURCE_STRATEGY.md`, `registers/data_source_registry.csv`, `docs/source-reviews/*.md`, `schemas/source_schema.json` | Source metadata, licensing, provenance |
| Evidence/claims | `schemas/evidence_schema.json`, `schemas/claim_schema.json`, `config/ruleset_homestead_mvp.yaml` | Claim-first semantics |
| Reports | `backend/app/domain/report_contracts.py`, `schemas/report_run_schema.json`, `backend/tests/reports/test_report_regression.py` | Report-run contract, JSON schema, and stable artifact semantics |
| Agent operations | `.agent/PLANS.md`, `docs/AGENT_OPERATING_MODEL.md`, `.claude/skills/**`, `.claude/agents/**` | Long-form agent procedures; not startup context |
| Validation | `scripts/verify.sh`, `scripts/verify.ps1`, `scripts/validate_workspace.sh`, `scripts/validate_workspace.ps1`, `.github/workflows/ci.yml` | Executable gates |
| Deployment smoke | `scripts/run_deployment_smoke.ps1`, `scripts/run_deployment_smoke.sh` | Compose-backed deployment smoke for health, metrics, queue health, and report workflow |
| Connector runbook | `docs/connectors/connector_runbook.md` | Connector interface, run lifecycle, failure taxonomy, quality gates |
| MVP operator runbook | `docs/runbooks/mvp_operator.md` | Startup, API workflow, configuration, known limitations |
| Backup/restore runbook | `docs/runbooks/backup_restore.md`, `scripts/run_backup_restore_check.ps1`, `scripts/run_backup_restore_check.sh` | Restore-proof workflow for Level 10 DB recovery validation |
| Incident/rollback runbook | `docs/runbooks/incident_response.md`, `scripts/run_incident_rollback_check.ps1`, `scripts/run_incident_rollback_check.sh` | Severity, ownership, escalation, rollback, and recovery proof |
| Alerting runbook | `config/ops_alert_rules.yaml`, `docs/runbooks/alerting.md`, `scripts/run_alert_rules_check.ps1`, `scripts/run_alert_rules_check.sh` | Repo-local alert rules for high-severity failures, queue health, and stale source metadata |
| Supply-chain checks | `.github/workflows/ci.yml`, `.github/dependabot.yml`, `docs/runbooks/supply_chain.md`, `scripts/run_supply_chain_check.ps1`, `scripts/run_supply_chain_check.sh` | CI dependency vulnerability scan, dependency update hygiene, and dependency artifact attestation wiring |
| Dependency provenance | `backend/requirements-prod.lock`, `docs/sbom/backend-prod-sbom.json`, `docs/runbooks/dependency_provenance.md`, `scripts/run_provenance_check.ps1`, `scripts/run_provenance_check.sh` | Hashed backend production lock, SBOM, GitHub artifact attestation wiring, and validate-only provenance proof |
| Container image scan | `backend/Dockerfile`, `.dockerignore`, `.github/workflows/ci.yml`, `docs/runbooks/container_image_scan.md`, `scripts/run_container_scan_check.ps1`, `scripts/run_container_scan_check.sh` | Digest-pinned backend base image plus CI Docker Scout scan for the locally built backend image and runtime base packages |
| Cost monitoring | `config/ops_cost_monitoring.yaml`, `docs/runbooks/cost_monitoring.md`, `scripts/run_cost_monitoring_check.ps1`, `scripts/run_cost_monitoring_check.sh` | Cost categories, report cost metrics, zero-dollar attribution, and paid-source guardrails |
| Access control | `config/access_control.yaml`, `docs/runbooks/access_control.md`, `scripts/access_control_check.py`, `scripts/run_access_control_check.ps1`, `scripts/run_access_control_check.sh` | API-key, scoped reviewer service-account, protected-route posture, and full user-RBAC blockers |
| Release readiness | `config/release_readiness.yaml`, `docs/runbooks/release_readiness.md`, `scripts/run_release_readiness_check.ps1`, `scripts/run_release_readiness_check.sh` | Repo-local release gate catalog and validate-only readiness proof |
| Release package | `config/release_package.yaml`, `docs/runbooks/release_package.md`, `scripts/build_release_package.ps1`, `scripts/build_release_package.sh`, `scripts/release_package_check.py`, `scripts/run_release_package_check.ps1`, `scripts/run_release_package_check.sh` | Local source/runtime/operator ZIP package boundary, manifest, and validate-only package proof |
| Image publication | `config/image_publication.yaml`, `docs/runbooks/image_publication.md`, `scripts/image_publication_check.py`, `scripts/run_image_publication_check.ps1`, `scripts/run_image_publication_check.sh` | Registry image publication boundary, required evidence, blockers, and validate-only proof |
| Hosted deployment | `config/hosted_deployment.yaml`, `docs/runbooks/hosted_deployment.md`, `scripts/hosted_deployment_check.py`, `scripts/run_hosted_deployment_check.ps1`, `scripts/run_hosted_deployment_check.sh` | Hosted deployment runtime input/evidence boundary, blockers, and validate-only proof |
| Private MVP readiness | `config/private_mvp_beta_readiness.yaml`, `scripts/run_private_mvp_readiness_check.ps1`, `scripts/run_private_mvp_readiness_check.sh`, `scripts/private_mvp_readiness_check.py` | Private beta gate catalog separating DS-017/hosted-production blockers from the selected NC county private-MVP utility proof |
| Readiness checklists | `docs/checklists/jurisdiction_readiness.md`, `docs/checklists/rulepack_readiness.md` | Mandatory pre-release checklists for new jurisdictions and rulepacks |
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
