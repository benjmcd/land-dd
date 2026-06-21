# Release Readiness Runbook

## Purpose

Use `config/release_readiness.yaml` as the repo-local Level 10 release readiness
catalog. It gathers the existing verification, DB, deployment smoke, supply-chain,
security-scan, image scan, backup/restore, incident, alerting, cost, access-control,
threat-proxy-audit, release-package, image-publication, hosted-deployment,
source-readiness, data-retention, load-test, performance, data-lineage,
jurisdiction-readiness, rulepack-readiness, checklist-dry-run, source-entitlement, and
production-authority intake proofs into one release boundary. It also composes the
Bologna pilot-scope authority and recorded-source corpus checks so future expansion
cannot bypass the blocked product/AOI/scope gate or fixture-corpus contract.

This runbook does not publish a release package, push an image, create a hosted
deployment, attach registry attestations, approve paid vendors, approve hosted billing,
or weaken evidence/report safety constraints. Local package creation is handled by
`scripts/build_release_package.ps1` after the release gates pass.

## Validate Readiness

Run from the repository root:

```powershell
.\scripts\run_release_readiness_check.ps1
```

The check is validate-only. It verifies that:

- `config/release_readiness.yaml` names all required release gates;
- referenced proof scripts, runbooks, lockfiles, SBOM, Dockerfile, Compose, CI,
  access-control, release-package, image-publication, hosted-deployment,
  threat-proxy-audit, source-readiness, security-scan, data-retention, load-testing,
  performance, checklist, and data-lineage artifacts exist;
- CI contains `verify`, `db-verify`, `supply-chain`, `dependency-attestations`,
  `container-image-scan`, `access-control`, `release-package-manifest`,
  `image-publication`, `hosted-deployment`, and `security-scan`, and
  `release-readiness` jobs;
- `db-verify` explicitly passes both `DATABASE_URL_SYNC` and `DATABASE_URL` when
  `RUN_DB_SMOKE='1'` is enabled;
- the `release-readiness` CI job runs the POSIX readiness proof;
- current Must-source readiness remains explicit about `sources=8 ready=7 blocked=1`;
- the local source-entitlement packet is `config/source_entitlements.yaml`, and the
  release proof composes `scripts/run_source_entitlement_check.ps1` /
  `scripts/source_entitlement_check.py` as a validate-only source-entitlement check for
  DS-017 decision requirements;
- the local production-authority intake packet is
  `config/production_authority_intake.yaml`, and the release proof composes
  `scripts/run_production_authority_intake_check.ps1` /
  `scripts/production_authority_intake_check.py` as a validate-only
  production-authority intake check across DS-017, hosted platform, secrets, identity,
  image publication, billing, hosted observability, Bologna pilot-scope, and Bologna
  recorded-source blockers;
- the local Bologna pilot-scope authority packet is
  `config/bologna_pilot_scope_authority.yaml`, and the release proof composes
  `scripts/run_bologna_pilot_scope_authority_check.ps1` /
  `scripts/bologna_pilot_scope_authority_check.py` as a validate-only first-gate
  Bologna pilot-scope authority check that keeps product, one-AOI, jurisdiction,
  rulepack/evidence scope, DS-017 treatment, fixture boundary, and runtime/report
  boundary decisions blocked until cited authority exists;
- the local Bologna recorded-source corpus contract is
  `config/bologna_recorded_source_corpus.yaml`, and the release proof composes
  `scripts/run_bologna_recorded_source_corpus_check.ps1` /
  `scripts/bologna_recorded_source_corpus_check.py` as a validate-only
  Bologna recorded-source corpus check that keeps fixture capture blocked until
  authority exists;
- Must current-effective source reviews keep `Last Checked At` within the 90-day
  repo-local freshness horizon enforced by `scripts/source_readiness.py` and
  `scripts/alert_rules_check.py`, while source-specific upstream/update cadence and
  terms/source-page triggers remain separate prose;
- the local release package boundary and builders are validated by
  `scripts/run_release_package_check.ps1`;
- the `release-package-manifest` CI job runs the release-package boundary proof, builds a
  local package, and validates the generated manifest with
  `scripts/run_package_manifest_check.ps1`;
- the image publication boundary is validated by `scripts/run_image_publication_check.ps1`;
- the hosted deployment boundary, including the non-local hosted runtime secret input
  contract, is validated by `scripts/run_hosted_deployment_check.ps1`;
- the aggregate release proof executes the image-publication and hosted-deployment validators
  so stricter lower-level contracts fail the release gate;
- security scanning is represented by `scripts/run_security_scan.ps1`;
- data retention is represented by `scripts/run_data_retention_check.ps1`;
- load testing is represented by `scripts/run_load_test.ps1` and documented in
  `docs/runbooks/load_testing.md`;
- performance posture is documented in `docs/runbooks/performance.md`;
- the local performance baseline contract is `config/performance_baseline.yaml`, and
  the release proof composes `scripts/run_performance_baseline_check.ps1` /
  `scripts/performance_baseline_check.py` as validate-only proof;
- the local spatial query-plan contract is `config/spatial_query_plan.yaml`, and the
  release proof composes `scripts/run_spatial_query_plan_check.ps1` /
  `scripts/spatial_query_plan_check.py` as validate-only static proof; the DB-enabled
  `scripts/run_spatial_query_plan_runtime_check.ps1` harness remains manual and opt-in;
- the local threat/proxy audit contract is `config/threat_proxy_audit.yaml`, and the
  release proof composes `scripts/run_threat_proxy_audit_check.ps1` /
  `scripts/threat_proxy_audit_check.py` as validate-only static proof for protected-class,
  demographic-proxy, residential-steering, recommendation/ranking, suitability,
  access-control, source-rights, overclaim, and error-leakage boundaries;
- the local checklist dry-run contract is `config/checklist_dry_run.yaml`, and the
  release proof composes `scripts/run_checklist_dry_run_check.ps1` /
  `scripts/checklist_dry_run_check.py` as validate-only static proof that every
  jurisdiction and rulepack checklist item is classified before future expansion;
- the local load-test JSON result schema is `load_test_result_v1`;
- jurisdiction and rulepack expansion stay gated by
  `docs/checklists/jurisdiction_readiness.md` and `docs/checklists/rulepack_readiness.md`;
- report data lineage remains represented by the report API lineage surface
  (`data_lineage`);
- the release blockers remain recorded instead of silently treated as complete.

## Operator Workflow

1. Run `.\scripts\run_release_readiness_check.ps1` before any release candidate handoff.
2. Run the full DB-enabled gate with both sync and app URLs set:
   ```powershell
   $env:RUN_DB_SMOKE='1'
   $env:DATABASE_URL_SYNC='postgresql://land:land@localhost:5432/land_diligence'
   $env:DATABASE_URL='postgresql+psycopg://land:land@localhost:5432/land_diligence'
   .\scripts\verify.ps1
   ```
3. Run `.\scripts\run_deployment_smoke.ps1` against an isolated Compose project before
   calling a backend image deployable.
4. Treat any failed required proof as a release blocker until fixed or explicitly
   risk-accepted in the appropriate runbook.
5. To create a local package, run `.\scripts\build_release_package.ps1 -Version <version>`
   after all release gates pass.
   Then run `.\scripts\run_package_manifest_check.ps1 -Manifest <manifest-path>` against
   the generated sibling manifest before sharing the package.
6. Do not publish a release package or registry image until hosted deployment authority,
   registry-image attestation, and billing/source blockers are resolved.

## Known Limits

- Release readiness is repo-local and validate-only.
- Threat/proxy audit readiness is repo-local drift control only. It does not replace
  external security review, legal fair-housing review, hosted IdP/RBAC design,
  production error/log review, DS-017 entitlement work, or hosted alerting.
- Checklist dry-run readiness proves checklist executability only. It does not approve a
  new geography, rulepack, source, connector, vendor, legal review, local professional
  review, hosted deployment, or DS-017 entitlement.
- Local release packages can be created with `scripts/build_release_package.ps1`, but this
  readiness proof itself remains validate-only.
- Performance baseline readiness is release-candidate/local evidence only. It is not a
  production SLO, hosted production proof, or capacity benchmark.
- The performance baseline checker and load-test validate-only modes must not send HTTP
  requests or create measured result artifacts.
- Spatial query-plan readiness is a static repo contract only. It validates canonical
  DDL/index coverage and runbook alignment, but does not run `EXPLAIN ANALYZE` against a live or hosted database by default.
  Runtime plan proof requires explicit `DATABASE_URL_SYNC`/`--db-url` and
  `SPATIAL_QUERY_PLAN_AREA_ID`/`--area-id` inputs.
- No live-load CI gate is added; CI does not start a server or fail on latency
  thresholds.
- No container image is pushed to a registry by this proof.
- Image publication readiness is cataloged in `config/image_publication.yaml`, but
  registry push and attestation publication remain blocked.
- Hosted deployment readiness is cataloged in `config/hosted_deployment.yaml`, but
  hosted infrastructure mutation, public endpoint creation, and hosted secret-manager
  authority remain blocked.
- Production-authority intake is cataloged in `config/production_authority_intake.yaml`,
  but it is only a validate-only map of missing external authority. It does not approve
  DS-017, select vendors, provision hosted infrastructure, publish images, write
  secrets, create billing integration, create hosted observability, select a Bologna
  AOI, promote source decisions, or claim Level 10 authority.
- Bologna pilot-scope authority is cataloged in
  `config/bologna_pilot_scope_authority.yaml`, but it is only a validate-only first
  gate. It does not select an AOI, approve sources, change source rights, capture
  fixtures, start runtime/report proof, approve DS-017, or start Bologna.
- Bologna recorded-source corpus readiness is cataloged in
  `config/bologna_recorded_source_corpus.yaml`, but it is only a validate-only manifest
  contract. It does not capture fixtures, create source-failure fixtures, approve
  report use, promote source registry rows, mutate the database, or start Bologna.
- No hosted deployment, domain, TLS endpoint, hosted alerting, or pager routing is
  created by this proof.
- No published registry-image attestation, signed image SBOM, or SLSA provenance
  attestation exists yet.
- Commercial parcel vendor data (DS-017) remains blocked until vendor, license, cost,
  source-rights, entitlement, and connector-surface decisions are made. The
  source-entitlement check proves those decision requirements are explicit; it does not
  approve DS-017, select a vendor, call a live vendor, implement paid-source metering,
  or change source readiness. DS-011 is connector-ready only as explicit
  not-evaluated source-failure evidence, not live assessor data.
  DS-010 parcel connectors are ready only for immediate operator API and request-time
  orchestration surfaces; durable live-job support is not claimed for DS-010.
