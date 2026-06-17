# Release Readiness Runbook

## Purpose

Use `config/release_readiness.yaml` as the repo-local Level 10 release readiness
catalog. It gathers the existing verification, DB, deployment smoke, supply-chain,
security-scan, image scan, backup/restore, incident, alerting, cost, access-control,
release-package, image-publication, hosted-deployment, source-readiness, data-retention,
load-test, performance, data-lineage, jurisdiction-readiness, and rulepack-readiness
proofs into one release boundary.

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
  source-readiness, security-scan, data-retention, load-testing, performance, checklist,
  and data-lineage artifacts exist;
- CI contains `verify`, `db-verify`, `supply-chain`, `dependency-attestations`,
  `container-image-scan`, `access-control`, `image-publication`, `hosted-deployment`, and
  `security-scan`, and `release-readiness` jobs;
- `db-verify` explicitly passes both `DATABASE_URL_SYNC` and `DATABASE_URL` when
  `RUN_DB_SMOKE='1'` is enabled;
- the `release-readiness` CI job runs the POSIX readiness proof;
- current Must-source readiness remains explicit about `sources=8 ready=7 blocked=1`;
- the local release package boundary and builders are validated by
  `scripts/run_release_package_check.ps1`;
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
6. Do not publish a release package or registry image until hosted deployment authority,
   registry-image attestation, and billing/source blockers are resolved.

## Known Limits

- Release readiness is repo-local and validate-only.
- Local release packages can be created with `scripts/build_release_package.ps1`, but this
  readiness proof itself remains validate-only.
- No container image is pushed to a registry by this proof.
- Image publication readiness is cataloged in `config/image_publication.yaml`, but
  registry push and attestation publication remain blocked.
- Hosted deployment readiness is cataloged in `config/hosted_deployment.yaml`, but
  hosted infrastructure mutation, public endpoint creation, and hosted secret-manager
  authority remain blocked.
- No hosted deployment, domain, TLS endpoint, hosted alerting, or pager routing is
  created by this proof.
- No published registry-image attestation, signed image SBOM, or SLSA provenance
  attestation exists yet.
- Commercial parcel vendor data (DS-017) remains blocked until vendor, license, cost,
  source-rights, and connector-surface decisions are made. DS-011 is connector-ready
  only as explicit not-evaluated source-failure evidence, not live assessor data.
  DS-010 parcel connectors are ready only for immediate operator API and request-time
  orchestration surfaces; durable live-job support is not claimed for DS-010.
