# Production Authority Packet

## Purpose

Record the external decisions and evidence required before the project can move from
selected-county private MVP and local release-candidate proof toward hosted,
multi-geography production. This packet is a decision request and repo-local routing
map only. It does not approve vendors, provision infrastructure, publish images, write
secrets, or create generated evidence.

## Current Baseline

- Selected-county private MVP and local release-candidate proof are not hosted,
  multi-geography production proof.
- Must-source readiness remains `sources=8 ready=7 blocked=1`; `DS-017` is blocked.
- `state/POST_RC_AUTHORITY_SPLIT.md` and `state/LEVEL_9_10_GATE_MATRIX.md` classify
  hosted deployment, full identity/RBAC, secret-manager, billing, alerting, image
  publication, production workload, and DS-017 work as blocked on external authority.
- The catalogs under `config/` are validate-only handoff contracts unless the missing
  external authority and evidence fields below are supplied.

## Fail-Closed Rule

Do not implement a DS-017 connector, hosted deployment, full identity/RBAC, billing
integration, registry image publication, hosted alert route, hosted retention scheduler,
or production workload by inference. Repo-local validators, local smoke tests, and
selected-county proof may guide the next implementation lane only after the named
external authority exists.

## DS-017 Commercial Parcel Vendor Authority

Source of current truth: `registers/data_source_registry.csv` row `DS-017`,
`scripts/source_readiness.py`, `config/ops_cost_monitoring.yaml`.

- External decisions required:
  - Vendor/source selection for normalized parcel/ownership data, including legal
    vendor entity, product or dataset name, upstream data sources, source authority
    level, geography or coverage, update cadence, data version/date, terms URL or
    redacted contract reference, and terms version or effective date.
  - Product decision to keep DS-017 in full-release Must scope, defer it, or remove it
    from Must scope.
  - License approval for commercial use, redistribution, cache, export, AI use, raw
    data handling, attribution, and derived output terms.
  - Entitlement policy for restricted/vendor data by user, workspace, report, export,
    and audit path.
  - Cost model and billing owner for paid data usage, including per-report
    `paid_data_usd_cents` attribution.
  - Field-level policy for parcel geometry, parcel ID, ownership fields, owner mailing
    address, situs address, assessed/tax/value fields, sale/comps fields, zoning or
    jurisdiction attributes, and any other raw vendor attributes.
  - Connector decision covering fixture-only, manual review, live API, batch ingest,
    refresh cadence, and failure handling.
- Evidence fields required:
  - `Source ID`, `Name`, `Organization`, `URL`, `Use`, `Caveats`.
  - `License Status`, `Commercial Use Status`, `Redistribution Status`,
    `Cache Allowed`, `Export Allowed`, `AI Use Status`, `Raw Data Allowed`,
    `Attribution Required`.
  - `Update Cadence`, `Freshness Class`, `Last Checked At`, `Review Owner`,
    `Review Status`.
  - Vendor contract or reviewed terms reference, allowed geography, source version or
    effective date, retrieval metadata requirements, entitlement owner, cost meter,
    billing approval, and connector scope.
  - Approved field allowlist/denylist, cache TTL, invalidation trigger, checksum or
    storage URI only if raw retention is allowed, and replay strategy when raw vendor
    snapshots may not be retained.
  - Failure-mode mapping for auth failure, license blocked, quota exceeded, rate limit,
    stale data, vendor outage, no coverage, ambiguous parcel match, partial response,
    schema drift, and no-data.
- Acceptable unblock criteria:
  - DS-017 has named authority for each required rights/cost/entitlement field.
  - Source-readiness can pass for the intended DS-017 scope without treating unknown,
    blocked, or pending fields as ready.
  - The approved scope explicitly states whether customer export and raw/vendor data
    exposure are allowed, restricted, or prohibited.
  - DS-017 may only provide screened parcel context within approved fields. No owner
    PII, raw vendor record, assessed or market value, comps, lending, appraisal,
    investment, or residential desirability output may enter reports unless separately
    approved and entitlement-gated.
  - Vendor no-data, outage, stale data, ambiguity, quota, auth, license, and schema
    failures become first-class source-failure or unknown evidence, not clean findings.
  - DS-017 is treated as commercial normalized data, not final parcel, title, survey,
    appraisal, lending, or official county authority.
  - Paid-source metering and report cost attribution are approved before any paid data
    can enter reports.
  - Alternative unblock: DS-017 is removed or deferred from full-release Must scope by
    explicit product decision, with release/matrix/readiness artifacts updated without
    pretending DS-017 is approved.
- Repo lane unlocked only after authority exists:
  - DS-017 source review, registry/seed updates, entitlement model tests, cost catalog
    updates, connector design, and then the narrowest approved connector slice.

## Hosted Platform Authority

Source of current truth: `config/hosted_deployment.yaml`,
`config/release_readiness.yaml`, `state/LEVEL_9_10_GATE_MATRIX.md`.

- External decisions required:
  - Hosted platform, environment name, deployment owner, hosted database, DNS/TLS
    authority, public URL, rollback target, backup/restore target, and promotion gate.
- Evidence fields required:
  - `immutable_image_digest`, `deployed_image_ref`, `platform_environment_name`,
    `database_instance_name`, `public_https_url`, `tls_certificate_status`,
    `health_endpoint_ok`, `version_endpoint_ok`, `metrics_endpoint_ok`,
    `queue_health_endpoint_ok`, `report_workflow_smoke_ok`, `rollback_target`,
    `backup_restore_proof`.
  - Evidence provenance: platform owner, environment, timestamp, commit SHA or release
    ID, command used, and external artifact location. Do not commit generated hosted
    runtime artifacts into the repo.
- Acceptable unblock criteria:
  - The hosted platform and database are provisioned or explicitly selected with an
    owner, environment, URL, DNS/TLS path, and rollback/backup proof path.
  - Required runtime inputs are supplied through approved runtime/secret references,
    not committed plaintext.
  - Deployment smoke is run against the hosted HTTPS runtime, not only local Compose.
  - Filled attestation fields are deployment evidence, not production approval, until
    reviewed by the named platform owner.
- Repo lane unlocked only after authority exists:
  - Hosted deployment attestation recording, deployment-smoke wiring for the selected
    platform, hosted DB migration/rollback proof, and release-readiness promotion gate.

## Secrets Authority

Source of current truth: `config/access_control.yaml`,
`config/hosted_deployment.yaml`.

- External decisions required:
  - Approved secret manager, per-environment secret owner, reference names, rotation
    runbook or ticket, breakglass policy, and post-rotation validation owner.
- Evidence fields required:
  - Runtime references for `API_KEY_SPECS`, `REVIEWER_ACCOUNTS`,
    `REVIEWER_ACCOUNT_SCOPES`, `UI_AUTH_COOKIE_SECRET`,
    `REPORT_IDENTITY_TOKEN_SECRET`, and `DATABASE_URL`.
  - `external_secret_manager_reference_names`, `per_environment_secret_owner`,
    `rotation_runbook_or_ticket`, `post_rotation_access_control_check`,
    `no_plaintext_committed_secret_values`.
- Acceptable unblock criteria:
  - The packet records secret reference names, owner, rotation path, and
    post-rotation validation only; secret values are not evidence and must not appear
    in repo files, logs, screenshots, or packet artifacts.
  - No production secret value is committed or copied into this repo.
  - Secret references are stable per environment and rotation proof can be reproduced.
  - Access-control validation passes after rotation or reference changes.
- Repo lane unlocked only after authority exists:
  - Secret-reference documentation, platform runtime binding checks, rotation evidence
    hooks, and hosted access-control validation.

## Identity And RBAC Authority

Source of current truth: `config/access_control.yaml`,
`state/LEVEL_9_10_GATE_MATRIX.md`.

- External decisions required:
  - IdP/OAuth/OIDC provider, user account persistence strategy, workspace model, role
    policy, audit identity requirements, service-account/breakglass policy, and
    migration path from current reviewer scopes.
- Evidence fields required:
  - Identity claims: `subject`, `email`, `display_name`, `workspace_id`, `user_id`,
    `groups_or_roles`.
  - Audit fields: `idp_subject`, `workspace_id`, `user_id`, `role_ids`,
    `route_scope`, `session_or_token_id`, `decision_outcome`.
  - Role mappings for platform admin, workspace admin, reviewer, operator, and
    read-only users.
- Acceptable unblock criteria:
  - Hosted IdP, account persistence, and role policy are approved together.
  - Report identity tokens and reviewer scopes have a migration path to user-bound
    audit records.
  - Full RBAC work does not weaken current fail-closed API-key and reviewer-scope
    behavior.
- Repo lane unlocked only after authority exists:
  - User/account schema planning, OAuth/OIDC integration plan, role enforcement tests,
    user-bound audit migration, and hosted route-scope validation.

## Image Publication Authority

Source of current truth: `config/image_publication.yaml`,
`config/release_readiness.yaml`.

- External decisions required:
  - Registry repository, registry access owner, image signing/attestation authority,
    SBOM signing authority, vulnerability scan requirement, and deployment image
    promotion policy, including immutable tag/digest policy, severity threshold, and
    exception approver.
- Evidence fields required:
  - `image_digest`, `registry_image_ref`, `vulnerability_scan`, `dependency_sbom`,
    `provenance`.
- Acceptable unblock criteria:
  - Registry repository authority exists and names where images may be pushed.
  - Digest, SBOM, vulnerability scan, and provenance evidence can be attached without
    publishing secrets or generated artifacts into the repo.
  - A pushed image is not deployable until digest, SBOM, provenance, vulnerability
    result, and exception status are attached and approved.
  - Hosted deployment authority identifies which digest is deployed.
- Repo lane unlocked only after authority exists:
  - Registry publication workflow, attestation capture, release package linkage, and
    image-to-hosted-deployment verification.

## Billing And Cost Authority

Source of current truth: `config/ops_cost_monitoring.yaml`,
`config/release_readiness.yaml`.

- External decisions required:
  - Hosted billing owner, budget/thresholds, unit-cost policy, paid-source metering
    policy, vendor spend approval, and alert/escalation owner for cost overruns.
- Evidence fields required:
  - Approved thresholds for compute, storage, LLM-if-used, maps, geocoding, and
    data vendors.
  - Per-report cost fields including `paid_data_usd_cents` before DS-017 or any
    paid source can enter production reports.
  - Billing reconciliation reference and owner.
- Acceptable unblock criteria:
  - Nonzero spend categories have explicit owner-approved thresholds.
  - Paid/commercial sources remain blocked until license authority and cost attribution
    are both approved.
  - Cost monitoring validation can distinguish zero-dollar local proof from hosted or
    vendor-billed production use.
- Repo lane unlocked only after authority exists:
  - Hosted billing reconciliation checks, paid-source cost instrumentation, cost alert
    proof, and batch/concurrency guardrails.

## Alerting Authority

Source of current truth: `config/ops_alert_rules.yaml`,
`config/release_readiness.yaml`.

- External decisions required:
  - Hosted alert manager, dashboard/log-retention system, pager route, named rotation,
    severity ownership, and source freshness review owner.
- Evidence fields required:
  - Alert manager route, dashboard/log retention reference, pager/on-call rotation,
    owner for `operations-on-call`, and proof for health, metrics, queue health,
    connector failure, source-readiness, stale registry, safety-contract, backup, and
    cost alerts.
- Acceptable unblock criteria:
  - Every SEV0/SEV1/SEV2 catalog rule has a hosted signal route, named owning
    rotation, escalation path, and validation proof.
  - Placeholder owners such as `operations-on-call` are replaced by concrete rotation
    authority before alerting is treated as production-ready.
  - Source-readiness and stale-source alerts are wired to a human owner rather than
    silently interpreting stale or failed sources as clean.
  - Alerting proof is hosted or staging-hosted, not only static catalog validation.
- Repo lane unlocked only after authority exists:
  - Hosted alert-route configuration, dashboard/runbook links, queue/source freshness
    monitors, and incident-response validation.

## Production Workload And Retention Authority

Source of current truth: `config/performance_baseline.yaml`,
`config/data_retention.yaml`, `state/LEVEL_9_10_GATE_MATRIX.md`.

- External decisions required:
  - Staging or hosted load target, formal SLO/SLA target if any, production capacity
    assumptions, representative workload, batch/concurrency policy, hosted object
    storage policy, hosted scheduler, hosted log retention, and deletion approval flow.
- Evidence fields required:
  - Load-test scenario, base URL, thresholds, request counts, failures, summary, queue
    depth/latency proof, SLI/SLO definitions, p95/p99 latency and error-rate targets,
    test duration, representative workload, concurrency assumptions, error budget or
    rollback criteria, DB/object-store capacity notes, retention class approvals, hosted
    scheduler reference, hosted log-retention reference, backup/export proof before
    destructive retention applies.
- Acceptable unblock criteria:
  - Local release-candidate load results are not reused as hosted SLO proof.
  - Hosted workload proof runs against the selected hosted/staging runtime and records
    thresholds and failures without committing generated runtime artifacts.
  - Retention automation remains dry-run/default-off until hosted scheduler, approval,
    and backup/export authority exist.
- Repo lane unlocked only after authority exists:
  - Hosted load-test proof, queue/backpressure threshold tuning, object-store capacity
    checks, hosted retention scheduler integration, and production workload dashboards.

## Bologna Recorded-Source Pilot Authority

Source of current truth: `config/bologna_preflight.yaml`,
`config/bologna_source_candidates.yaml`, `config/bologna_source_rights.yaml`,
`config/bologna_source_authority_intake.yaml`,
`docs/runbooks/bologna_preflight.md`, `docs/runbooks/bologna_source_candidates.md`,
`docs/runbooks/bologna_source_rights.md`,
`docs/runbooks/bologna_source_authority_intake.md`,
`docs/source-reviews/bologna-source-candidates.md`,
`docs/source-reviews/bologna-source-rights.md`,
`docs/checklists/jurisdiction_readiness.md`, `docs/checklists/rulepack_readiness.md`,
`state/LEVEL_9_10_GATE_MATRIX.md`.

This packet does not approve or start Bologna. It records the authority and evidence
required before a future one-AOI recorded-source pilot can begin.

The Bologna source-candidates packet is candidate-only. It does not approve municipal,
regional, environmental, cadastral, or open-data sources, and it does not promote any
source into `registers/data_source_registry.csv`.

The Bologna source-rights matrix is validate-only. It records the exact source-schema,
license, cache, export, AI-use, raw-data, attribution, retrieval, caveat, CRS, fixture,
and report-use decisions required before any candidate can be promoted.

The Bologna source-authority intake guard is validate-only and blocked. It records the
exact authority evidence slots that must be cited before any pending source-rights
decision can change.

- External decisions required:
  - Product decision that authorizes a Bologna recorded-source pilot and names the
    exact one-AOI scope, intended operator, non-goals, and stop conditions.
  - Italy/EU/local source review for each recorded source, including source owner,
    source version/date, retrieval metadata, license/terms reference, redistribution,
    cache, export, AI-use, attribution, raw-data handling, and caveats.
  - Candidate-source promotion decision that selects exact PUG, open-data, regional
    topographic, environmental, CRS/reference, and any cadastral source surfaces from
    `config/bologna_source_candidates.yaml` only after per-source rights review.
  - Completion of `config/bologna_source_authority_intake.yaml` and then
    `config/bologna_source_rights.yaml` for every promoted candidate, including all
    pending authority evidence, rights decisions, and required evidence fields.
  - Jurisdiction and locality boundary model for the pilot, including country,
    regional, municipal, cadastral, CRS/geometry, local professional-review, and
    legal-interpretation boundaries.
  - Rulepack decision: evidence-only pilot, constrained locality dossier, or new
    rulepack. Do not reuse the US homestead rulepack outside its documented geography.
  - DS-017 broader-release treatment: approve under reviewed contract, defer or remove
    from Must scope, or substitute approved public/official sources.
- Evidence fields required:
  - Authorized AOI, recorded-source manifest, source-rights decisions, source versions,
    retrieval metadata, CRS and geometry precision, fixture corpus, source-failure
    fixtures, rulepack or evidence-only scope, caveat language, and no-overclaim review.
  - Candidate-source review evidence showing why each promoted source is allowed for
    cache, redistribution, export, AI use, raw retention, attribution, fixture capture,
    and report use.
  - Completed `SourceContract` field values from `schemas/source_schema.json` before
    any source registry row is created.
  - DB-backed report proof only after the recorded-source corpus is approved: evidence,
    claims or unknowns, caveats, artifact persistence, and lineage.
- Acceptable unblock criteria:
  - All candidate, source, jurisdiction, rulepack, DS-017-treatment, and fixture-corpus
    prerequisites are explicit and reviewed.
  - Every candidate source promoted out of `config/bologna_source_candidates.yaml` has
    a completed source review and source registry row; no pending-review candidate may
    enter runtime or reports.
  - Every promoted source has completed `config/bologna_source_authority_intake.yaml`
    authority references and `config/bologna_source_rights.yaml` decisions; pending
    intake or rights rows cannot unlock fixtures, runtime use, reports, or raw export.
  - Source failures, no-data, stale data, ambiguity, license blocks, CRS ambiguity, and
    partial records become first-class evidence or unknowns, not clean findings.
  - The pilot remains recorded-source and local unless hosted platform, identity/RBAC,
    object-store, observability, alerting, billing, and secret-manager authority exists.
  - Do not generalize into a multi-geography framework until Bologna pilot evidence
    exposes the actual shared contracts and country-specific boundaries.
- Repo lane unlocked only after authority exists:
  - Bologna recorded-source fixture corpus, source-rights catalog updates, pilot
    rulepack or evidence-only configuration, DB-backed runtime proof, and then a
    post-pilot multi-geography framework plan.

## Repo-Local Follow-On Map

| Authority received | Repo-local follow-on |
|---|---|
| DS-017 vendor/license/cost/entitlement authority | Source review, registry/seed updates, entitlement tests, cost meter, connector plan, then approved connector slice. |
| Hosted platform/database/DNS/TLS authority | Hosted attestation, platform-specific deployment smoke, migration/rollback proof, backup/restore proof. |
| Secret-manager authority | Secret reference catalog update, runtime binding checks, rotation proof, access-control validation. |
| IdP/RBAC authority | Account/role schema plan, OAuth/OIDC integration, route-scope enforcement, user-bound audit migration. |
| Registry/image authority | Image publish workflow, digest/SBOM/provenance evidence capture, release package and deployment linkage. |
| Billing/cost authority | Hosted billing reconciliation, paid-source cost attribution, spend alerts, batch/concurrency guardrails. |
| Alerting/on-call authority | Hosted alert routes, dashboards, queue/source freshness monitors, incident validation. |
| Production workload/retention authority | Hosted load proof, SLO threshold checks, retention scheduler, log retention, object-store capacity proof. |
| Bologna recorded-source pilot authority | Complete source-authority intake, source-rights matrix, recorded-source fixture corpus, Italy/EU/local source-rights checks, evidence-only or rulepack scope, DB-backed pilot proof, then multi-geography framework plan. |

## Open Blockers

- DS-017 has no vendor, license, cost, entitlement, or connector authority.
- Bologna has no selected AOI, promoted source inventory, Italy/EU/local source-rights
  authority, cadastral source review, pilot rulepack scope, recorded-source fixture
  corpus, or DB-backed pilot proof.
- Hosted platform, database, DNS/TLS, registry, public URL, and production smoke
  authority are not available.
- External secret manager, IdP/OAuth/OIDC, full user RBAC, billing reconciliation,
  hosted alert routing, hosted workload proof, hosted scheduler, and hosted log
  retention remain blocked.
