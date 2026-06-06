# Release Readiness Runbook

## Purpose

Use `config/release_readiness.yaml` as the repo-local Level 10 release readiness
catalog for local PC operation. It gathers the existing verification, DB, deployment
smoke, supply-chain, image scan, backup/restore, incident, alerting, cost,
access-control, release-package, and source-readiness proofs into one local-only release
boundary.

Billing, hosted deployment, hosted deployment attestations, published registry-image
attestations, registry push/signing, automatic key rotation/external secret-manager
integration, and full user auth/RBAC/OIDC/user accounts are out of scope for local-only
production-grade. They are not local-only release blockers and should be deferred in
favor of source-rights, evidence/claim/report correctness, local reproducibility, and
operator workflow quality unless the product scope explicitly changes.

## Validate Readiness

Run from the repository root:

```powershell
.\scripts\run_release_readiness_check.ps1
```

The check is validate-only. It verifies that:

- `config/release_readiness.yaml` names all required release gates;
- referenced proof scripts, runbooks, lockfiles, SBOM, Dockerfile, Compose, CI,
  access-control, release-package, and source-readiness artifacts exist;
- CI contains `verify`, `db-verify`, `supply-chain`, `dependency-attestations`,
  `container-image-scan`, `access-control`, and `release-readiness` jobs;
- CI does not run remote-only `image-publication` or `hosted-deployment` jobs for the
  local-only release path;
- the `release-readiness` CI job runs the POSIX readiness proof;
- current Must-source readiness remains explicit about `sources=8 ready=4 blocked=4`;
- the local release package boundary and builders are validated by
  `scripts/run_release_package_check.ps1`;
- remote-only publication/hosted/auth/billing requirements remain recorded under
  `local_only_deferred` as out of scope for local-only operation;
- the real local-only release blockers remain recorded instead of silently treated as
  complete.

## Operator Workflow

1. Run `.\scripts\run_release_readiness_check.ps1` before any release candidate handoff.
2. Run the full DB-enabled gate: `$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1`.
3. Run `.\scripts\run_deployment_smoke.ps1` against an isolated Compose project before
   calling a backend image deployable.
4. Treat any failed required proof as a release blocker until fixed or explicitly
   risk-accepted in the appropriate runbook.
5. To create a local package, run `.\scripts\build_release_package.ps1 -Version <version>`
   after all release gates pass.
6. Do not spend implementation effort on billing, hosted deployment, hosted deployment
   attestation, registry image push/signing/attestation, external secret-manager
   automation, or full user auth/RBAC unless the local-only scope is explicitly changed.

## Known Limits

- Release readiness is repo-local and validate-only.
- Local release packages can be created with `scripts/build_release_package.ps1`, but this
  readiness proof itself remains validate-only.
- No container image is pushed to a registry by this proof because registry publication
  is out of scope for local-only operation.
- Image publication readiness is cataloged in `config/image_publication.yaml` only as an
  optional remote distribution checklist. Validate that optional checklist with
  `scripts/run_image_publication_check.ps1` only if remote distribution scope changes.
- Hosted deployment readiness is cataloged in `config/hosted_deployment.yaml` only as an
  optional future-hosting checklist. Validate that optional checklist with
  `scripts/run_hosted_deployment_check.ps1` only if hosted deployment scope changes.
- No hosted deployment, domain, TLS endpoint, hosted alerting, pager routing, hosted
  billing reconciliation, registry push/signing, or published registry-image attestation
  is required for local-only release.
- County parcels, county assessor, commercial parcel vendor, and local zoning sources
  remain blocked until jurisdiction, license, cost, and source-rights review decisions
  are made.
