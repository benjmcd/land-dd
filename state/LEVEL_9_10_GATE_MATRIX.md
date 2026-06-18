# Level 9/10 Gate Matrix

Last updated: 2026-06-18

Purpose: classify current Level 9 and Level 10 readiness against current repo evidence.
This matrix is not a completion claim for Level 10. It exists to choose the next
lowest-dependency implementation slice without confusing private-MVP proof,
validate-only release artifacts, and blocked hosted-production work.

Canonical inputs used here:

- `MILESTONE_MAP.md`
- `config/private_mvp_beta_readiness.yaml`
- `config/release_readiness.yaml`
- `config/hosted_deployment.yaml`
- `config/access_control.yaml`
- `registers/data_source_registry.csv`
- `scripts/source_readiness.py --priority Must --json`
- `state/POST_RC_AUTHORITY_SPLIT.md`
- `state/PRODUCTION_AUTHORITY_PACKET.md`

Status legend:

| Status | Meaning |
|---|---|
| `PROVEN_PRIVATE_MVP` | Current repo tests/runbooks prove the gate for selected-county private MVP/local operation. |
| `PROVEN_REPO_LOCAL` | Current repo tests/CI prove the technical behavior locally or in CI, but not hosted production. |
| `VALIDATE_ONLY` | Catalog/runbook/checker exists and passes, but no external hosted operation is performed. |
| `PARTIAL` | Meaningful implementation exists, but required hosted, multi-user, scale, or governance proof is incomplete. |
| `BLOCKED` | External authority, vendor/license decision, hosted platform, billing, or identity decision is required. |
| `MISSING` | No adequate current proof was identified. |

## Level 9 - Product-Grade MVP Workflow

| Gate | Status | Current evidence | Next action |
|---|---|---|---|
| L9-001 operator can complete workflow | `PROVEN_PRIVATE_MVP` | `docs/runbooks/mvp_operator.md`; `config/private_mvp_beta_readiness.yaml`; UI runtime smoke guidance | Re-run full UI/runtime smoke during the next release-candidate pass. |
| L9-002 area/select intent flow | `PROVEN_PRIVATE_MVP` | `/ui/`, `/intake`, `/operator-cases`; private-MVP and API tests | Keep scope limited to selected counties until jurisdiction readiness passes. |
| L9-003 report status tracking | `PROVEN_REPO_LOCAL` | async report job store, `/report-runs/{id}`, UI status pages, retry lineage tests | Hosted monitoring remains Level 10 work. |
| L9-004 evidence behind claims inspectable | `PROVEN_REPO_LOCAL` | `GET /report-runs/{id}/lineage`; `/ui/report-runs/{id}/lineage`; lineage UI/API tests; selected-county runtime smoke now follows approved-report lineage | Re-run lineage smoke during each release-candidate pass. |
| L9-005 red flags, unknowns, blockers, verification tasks visible | `PROVEN_PRIVATE_MVP` | report regression tests, dossier tests, private-MVP overclaim/unknown checks | Keep adding red-flag/unknown fixtures with new sources or rulepacks. |
| L9-006 export preserves source/caveat appendix | `PROVEN_REPO_LOCAL` | Markdown dossier and JSON artifact endpoints; artifact path trust tests; DB artifact persistence tests | Hosted artifact storage evidence remains Level 10 deployment work. |
| L9-007 human review without overwriting source evidence | `PROVEN_REPO_LOCAL` | reviewer-scoped approval/review actions, action history, connector review queue tests | Full user-bound audit identity remains blocked with production RBAC. |
| L9-008 compare at least two candidate areas | `PROVEN_REPO_LOCAL` | `GET /report-runs/compare`; `/ui/compare`; compare API/UI tests | Keep compare logic tied to report summaries and approved delivery gating. |
| L9-009 scope and coverage limitations visible | `PROVEN_PRIVATE_MVP` | MVP operator runbook, private-MVP readiness catalog, selected-county manifests | Re-check after any new geography/source/rulepack. |
| L9-010 regression tests and release checklist | `PROVEN_PRIVATE_MVP` | private-MVP regression/readiness tests; release-readiness catalog | Release checklist remains validate-only until hosted blockers resolve. |
| L9-011 failure paths visible and recoverable | `PROVEN_REPO_LOCAL` | report retry route/UI coverage; operations recovery-preview API/UI/smoke coverage | Hosted alerting/on-call recovery remains blocked. |
| L9-012 basic auth/roles if multiple users/operators access data | `PARTIAL` | API-key middleware, scoped reviewer service accounts, UI reviewer/identity cookies | Full user accounts, OAuth/OIDC, org/user RBAC, and hosted identity remain blocked. |

## Level 10 - Deployment and Operations

| Gate | Status | Current evidence | Next action |
|---|---|---|---|
| L10-OPS-001 deploy from documented commands/pipeline | `VALIDATE_ONLY` | `config/hosted_deployment.yaml`; hosted-deployment checker; CI hosted-deployment job | Select hosted platform and produce real deployment attestation. |
| L10-OPS-002 env config and secrets not committed | `PARTIAL` | non-local secret hygiene; access-control catalog; `.env.example` guidance | Choose external secret manager and record secret references/rotation authority. |
| L10-OPS-003 CI/CD required checks before deploy | `PROVEN_REPO_LOCAL` | `.github/workflows/ci.yml`; release-readiness CI jobs | Tie CI to future hosted deployment promotion gate. |
| L10-OPS-004 migrations forward-tested and rollback strategy exists | `PARTIAL` | DB smoke, migration checks, incident/rollback runbook | Add hosted migration/rollback evidence once platform/database authority exists. |
| L10-OPS-005 backup and restore tested | `PROVEN_REPO_LOCAL` | backup/restore scripts, runbook, release-readiness gate | Repeat against hosted/staging database before production claim. |
| L10-OPS-006 production smoke after deploy | `BLOCKED` | deployment smoke scripts exist, no hosted deployment exists | Run smoke against deployed HTTPS runtime after platform is provisioned. |
| L10-OPS-007 observability covers API/DB/jobs/connectors/errors | `PARTIAL` | metrics endpoint, logs, queue health, recovery preview | Add hosted dashboard/log-retention proof and alert routing. |
| L10-OPS-008 alerts for high severity and stale data | `VALIDATE_ONLY` | alert-rule catalog/checker | Hosted alert manager/pager route remains blocked. |
| L10-OPS-009 incident response names severity/owner/escalation/rollback | `VALIDATE_ONLY` | incident response and rollback runbook/checker | Attach owner/escalation evidence for hosted operation. |
| L10-OPS-010 cost monitoring for compute/storage/vendors | `VALIDATE_ONLY` | cost-monitoring catalog/checker and zero-dollar report metrics | Hosted billing reconciliation and paid-source metering remain blocked. |

## Level 10 - Security

| Gate | Status | Current evidence | Next action |
|---|---|---|---|
| L10-SEC-001 authentication for restricted data | `PARTIAL` | API-key auth, reviewer service accounts, UI identity bridge | Implement full hosted user identity when IdP authority exists. |
| L10-SEC-002 authorization for user/org/report/data entitlements | `PARTIAL` | workspace-scoped report/connector paths, reviewer scopes | Full org/user RBAC and data entitlements remain blocked. |
| L10-SEC-003 secrets through approved store/env, never repo | `PARTIAL` | hashed non-local specs and no committed secret values | External secret-manager integration remains blocked. |
| L10-SEC-004 dependency and supply-chain scanning in CI | `PROVEN_REPO_LOCAL` | supply-chain, dependency-attestations, image-scan CI jobs | Registry image attestation remains blocked until publication authority exists. |
| L10-SEC-005 static/security checks for API/auth/input/injection | `PROVEN_REPO_LOCAL` | security-scan and access-control CI/jobs/checkers | Expand with threat-model review before hosted launch. |
| L10-SEC-006 audit logs for decision-impacting actions | `PARTIAL` | API-key audit events, review actions, report status/review records | Hosted log retention/SIEM and user-bound identity audit remain blocked. |
| L10-SEC-007 data retention/deletion policy | `VALIDATE_ONLY` | data-retention catalog/runbook/checker | Run policy against hosted data stores before production claim. |
| L10-SEC-008 protected-class/residential steering safeguards | `PROVEN_PRIVATE_MVP` | Private-MVP negative coverage only: no protected-class inputs, demographic desirability scoring, or residential steering features in current rules/connectors | Add production proxy-audit review before hosted residential expansion. |
| L10-SEC-009 production errors avoid leaks | `PARTIAL` | route error tests and auth failure pages | Add hosted error/log review before production launch. |
| L10-SEC-010 paid/vendor data entitlement control | `BLOCKED` | DS-017 remains blocked; no paid vendor data in private MVP | Resolve vendor license/entitlement model before paid data enters reports. |

## Level 10 - Data Governance

| Gate | Status | Current evidence | Next action |
|---|---|---|---|
| L10-DATA-001 production source license/terms reviewed | `PARTIAL` | Must-source readiness `8 total, 7 ready, 1 blocked`; DS-017 blocked | Resolve DS-017 or remove it from full-release Must scope by explicit product decision. |
| L10-DATA-002 attribution/redistribution/export/AI-use constraints enforced | `PARTIAL` | source registry rights fields, source-readiness checker, report caveats, and repo-local source-rights report exposure guard | Add entitlement enforcement for restricted/vendor datasets after DS-017/vendor authority exists. |
| L10-DATA-003 source freshness monitoring flags stale data | `PARTIAL` | source-readiness metadata, alert catalog, repo-local freshness/review-drift readiness guard, and source-review cadence prose guard | Hosted alert manager/pager/dashboard evidence remains blocked on external authority. |
| L10-DATA-004 connector failures/outages visible | `PROVEN_REPO_LOCAL` | source_failure evidence, connector review queue, operations recovery preview | Wire hosted alerts/dashboards for connector outages. |
| L10-DATA-005 jurisdiction readiness before new geography | `VALIDATE_ONLY` | jurisdiction readiness checklist and release-readiness gate | Complete checklist for each new county/state before expansion. |
| L10-DATA-006 rulepack readiness before new intent | `VALIDATE_ONLY` | rulepack readiness checklist and release-readiness gate | Complete checklist before new intent/rulepack. |
| L10-DATA-007 source-to-report lineage queryable | `PROVEN_REPO_LOCAL` | lineage API/UI, evidence IDs in claims/artifacts, DB-backed artifact tests, selected-county DB-backed runtime smoke follows approved-report lineage | Re-run against hosted DB/object store after deployment. |
| L10-DATA-008 human verification separate/auditable | `PROVEN_REPO_LOCAL` | review status/actions, connector review queues, report approval gate | Bind to hosted user identity/RBAC later. |
| L10-DATA-009 coverage limitations visible | `PROVEN_PRIVATE_MVP` | selected-county manifests, MVP operator runbook, private-MVP readiness catalog | Keep limitation checks in every release-candidate proof. |
| L10-DATA-010 data-quality failures fail closed | `PROVEN_REPO_LOCAL` | fixture quality gates, connector source-use preflight, artifact path trust checks | Extend gates for every new source and connector. |

## Level 10 - Performance and Scalability

| Gate | Status | Current evidence | Next action |
|---|---|---|---|
| L10-PERF-001 async report jobs with status/retry/failure | `PROVEN_REPO_LOCAL` | async job store, DB-backed jobs, retry lineage, status APIs/UI | Validate under hosted workload. |
| L10-PERF-002 batch screening bounded concurrency/cost | `PARTIAL` | live sequence scheduler, cost catalog | Batch workflow and concurrency guardrails need explicit hosted-scale proof. |
| L10-PERF-003 spatial indexes/query plans for workloads | `PARTIAL` | PostGIS schema, DB smoke, static `spatial_query_plan_v1` contract/checker, opt-in runtime checker, and R-016 isolated release-candidate runtime proof for the configured target GIST indexes | Re-run read-only runtime `EXPLAIN ANALYZE` against hosted or externally accepted representative selected-county DB workloads before promoting beyond PARTIAL. |
| L10-PERF-004 large artifacts use object storage/reference pattern | `PROVEN_REPO_LOCAL` | `OBJECT_STORE_ROOT`, DB artifact metadata, artifact path trust tests | Map object store to hosted storage service during deployment. |
| L10-PERF-005 cache strategy and invalidation are source-version aware | `VALIDATE_ONLY` | performance runbook | Implement/cache only when a real cache is introduced. |
| L10-PERF-006 load tests cover MVP workload | `VALIDATE_ONLY` | workflow-valid load-test scripts/runbook/checker and R-016 isolated local runtime proof for area creation -> report-run admission, including sequential and concurrent request evidence | Run against staging/hosted target with recorded thresholds before promoting beyond repo-local release-candidate proof. |
| L10-PERF-007 queue depth/job latency/failure metrics monitored | `PARTIAL` | metrics, queue health, recovery preview | Add hosted dashboard/alert evidence. |
| L10-PERF-008 backpressure/degraded mode for outages/load | `PARTIAL` | fail-closed source failures, runbook guidance, and default-off runtime queue backpressure for report/live-connector admission | Add hosted workload, dashboard, alert-routing, and threshold-tuning evidence before promoting beyond repo-local proof. |
| L10-PERF-009 DB pooling and transaction boundaries configured | `PROVEN_REPO_LOCAL` | DB pool settings/tests and SQLAlchemy request-scoped sessions | Tune values under hosted workload. |
| L10-PERF-010 performance regressions observable before release | `VALIDATE_ONLY` | performance runbook, baseline contract, optional JSON result output, release-readiness gate, and R-016 local measured rehearsal evidence | Repeat the local rehearsal for each release candidate and add hosted workload proof before any SLO/capacity claim. |

## Level 10 - Product Correctness

| Gate | Status | Current evidence | Next action |
|---|---|---|---|
| L10-PROD-001 end-to-end workflow from clean deployment | `PARTIAL` | local deployment smoke and DB-backed private-MVP paths | Hosted clean-deployment smoke remains blocked. |
| L10-PROD-002 reports include claims/evidence/unknowns/caveats/tasks | `PROVEN_REPO_LOCAL` | report contract/regression/dossier tests | Preserve in schema and artifact checks. |
| L10-PROD-003 exports preserve run identity/evidence links | `PROVEN_REPO_LOCAL` | JSON artifact/dossier endpoints and tests | Re-run against hosted object store. |
| L10-PROD-004 reruns show source/rule/version differences | `PROVEN_REPO_LOCAL` | report diff API, compare UI change review tests, and local release-candidate same-area diff smoke | Re-run against hosted runtime before production claim. |
| L10-PROD-005 human review workflow usable and audited | `PROVEN_REPO_LOCAL` | UI reviewer paths, approval, connector review, action history | Bind to hosted user identity/RBAC later. |
| L10-PROD-006 candidate comparison consistent with reports | `PROVEN_REPO_LOCAL` | compare API/UI tests, shared summary helpers, and local release-candidate compare smoke | Keep compare coupled to report contract; do not add ranking/recommendation semantics. |
| L10-PROD-007 user-facing language caveated/no overclaim | `PROVEN_PRIVATE_MVP` | overclaim tests, report language tests, source caveats | Revalidate for every source/geography/rulepack addition. |
| L10-PROD-008 error states understandable/actionable | `PARTIAL` | UI/API error pages, retry, recovery preview | Add hosted operator incident workflow proof. |
| L10-PROD-009 MVP scope boundaries enforced | `PROVEN_PRIVATE_MVP` | selected-county readiness catalog/manifests and runbook | Enforce jurisdiction readiness before expansion. |
| L10-PROD-010 red-flag and clean-ish regression suite | `PROVEN_PRIVATE_MVP` | nine golden AOIs and private-MVP regression tests | Add new fixtures for each expansion source/geography. |

## Post-RC Authority Split

`state/POST_RC_AUTHORITY_SPLIT.md` records the current split between external
authority blockers, repo-local implementation candidates, and audit-only evidence
candidates. The split preserves the conclusion that local selected-county
release-candidate proof is not hosted production proof.

`state/PRODUCTION_AUTHORITY_PACKET.md` now turns the external blockers into decision
and evidence requests. It does not approve DS-017, hosted deployment, full IdP/RBAC,
secret-manager, billing, alerting, image publication, or production workload work.

## Next Unblocked Pass

The lowest-dependency next pass is not hosted deployment. Hosted production remains
blocked by external platform, secret-manager, billing, alerting, identity/RBAC, and
source/vendor authority. `R-010` completed the post-RC authority split, `R-011`
completed the production authority packet, `R-012` added repo-local source-rights
report exposure guarding, `R-013` added repo-local source freshness review-drift
readiness guarding, `R-014` added source-review cadence consistency guarding, `R-015`
proved the local source/runtime/operator package boundary, `R-016` completed
representative local performance rehearsal while preserving hosted SLO/capacity
blockers, and `R-017` included compare/diff in local release-candidate workflow smoke
without ranking/recommendation semantics. The next active pass is `R-018`
threat-model/proxy audit update: map security, access-control, protected-class, and
residential-steering risks to existing repo-local controls without replacing external
security review, legal review, hosted IdP/RBAC, production error/log review, DS-017
entitlement work, or hosted production proof.

Do not start external hosted deployment work until `config/hosted_deployment.yaml`
blockers have named authorities and evidence. Do not start DS-017 connector work until
source/vendor blockers have named authorities and evidence.
