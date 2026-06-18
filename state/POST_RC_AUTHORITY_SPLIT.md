# Post-RC Authority Split

Last updated: 2026-06-18

## Purpose

Classify the remaining Level 9/10 work after the selected-county release-candidate
proof refresh and lineage smoke proof. This file separates repo-local work from
external decisions so local private-MVP evidence is not overused as hosted,
multi-user, or production-source proof.

## Current Proof Baseline

- Private-MVP selected-county readiness validates locally.
- Must-source readiness is `sources=8 ready=7 blocked=1`; DS-017 remains blocked.
- Release, hosted-deployment, access-control, and readiness-matrix validators pass as
  repo-local checks.
- Hosted-deployment, image-publication, alerting, access-control, and cost catalogs are
  validate-only handoff contracts unless external authority is supplied.

## External-Authority Blockers

These should not be implemented around or silently promoted from local proof.

| Area | Required authority/evidence | Current authority |
|---|---|---|
| Hosted deployment | Hosted platform, DNS/TLS, hosted database, public URL, immutable image digest, rollback target, backup/restore proof | `config/hosted_deployment.yaml` |
| Secret management | External secret manager references, owner, rotation runbook/ticket, post-rotation proof | `config/access_control.yaml` |
| Identity/RBAC | IdP/OAuth/OIDC decision, user account persistence, org/user role policy, user-bound audit requirements | `config/access_control.yaml` |
| DS-017 commercial parcel vendor | Vendor, license, redistribution/export/cache/AI-use rights, cost model, entitlement policy, connector decision | `registers/data_source_registry.csv`; `scripts/source_readiness.py` |
| Registry/image publication | Registry repository, image digest, attestation and signed SBOM authority | `config/image_publication.yaml` |
| Hosted alerting/on-call | Hosted alert manager, dashboard/log retention, pager route, named rotation | `config/ops_alert_rules.yaml`; `docs/runbooks/alerting.md` |
| Billing/cost approval | Hosted billing reconciliation, nonzero unit-cost thresholds, paid-source metering authority | `config/ops_cost_monitoring.yaml` |
| Hosted workload/SLO | Staging/hosted load target, formal SLO, production-capacity evidence | `docs/runbooks/performance.md` |

## Repo-Local Implementation Candidates

These can move without external hosted/source decisions, but they must stay scoped as
local or release-candidate evidence.

| Candidate | Why it is repo-local | Boundary |
|---|---|---|
| Release-candidate package rehearsal | Existing package builders/checkers can prove local handoff completeness | Does not publish package/image or attestations |
| Representative local performance evidence | Existing load-test and spatial-runtime harnesses can run against an isolated local candidate runtime/DB | Does not prove hosted SLO or capacity |
| Compare/diff workflow smoke | Existing compare/diff surfaces can be included in release-candidate UI/API smoke | Does not imply arbitrary multi-geography utility |
| Threat-model/proxy audit update | Existing security/access-control/protected-class surfaces can be reviewed and documented | Does not replace external security review or IdP work |
| Jurisdiction/rulepack checklist dry run | Existing checklists can be dry-run against the next candidate expansion target | Does not select a new geography or rulepack |
| Source-rights/export fail-closed guard | Existing source registry and connector policy can be checked for deny-by-default restricted/vendor export behavior | Does not approve DS-017 or implement customer entitlement |
| Source freshness/review-drift guard | Existing registry freshness metadata and source-readiness output can be audited for stale review evidence | Does not create hosted alert routing |
| Route-scope/RBAC handoff coverage | Existing protected routes and reviewer scopes can be checked against the future identity/RBAC contract | Does not implement OAuth/OIDC or user tables |
| Audit-retention proof hardening | Existing audit purge tooling can be exercised in isolated DB dry-run/apply tests | Does not provision hosted scheduler or log retention |
| Error-state/no-leak hardening | Existing API/UI error pages and recovery-preview routes can be covered with more failure regressions | Does not prove hosted error/log review |

## Audit-Only Evidence Candidates

These are useful to reduce ambiguity but do not by themselves change product readiness.

| Candidate | Output | Boundary |
|---|---|---|
| Exhaustive repository audit | External or untracked report using `C:/Users/benny/Downloads/land_dd_handoff.md` as prompt input | Read-only evidence; not implementation authority |
| Production authority packet | One decision package listing required external decisions, owners, and evidence templates | Does not provision infrastructure or approve vendors |
| Hosted-readiness checklist rehearsal | Filled readiness checklist with current known unknowns | Does not satisfy hosted attestation fields |

## Decision

Do not start hosted deployment, DS-017 connector implementation, full IdP/RBAC,
external secret-manager, billing, alerting, or production workload implementation from
the repo alone. The next best step is a production authority packet that turns the
blockers above into explicit decision requests and evidence templates for the user or
external systems. DS-017 should be first in that packet because it is the only current
Must-source readiness blocker and also drives paid-source entitlement, export/cache/raw
data, AI-use, and cost decisions.

If local implementation work continues before those decisions arrive, prefer the
release-candidate package/performance rehearsal lane and label all output as local
release-candidate evidence only.
