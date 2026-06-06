# Hosted Deployment Runbook

## Purpose

Use `config/hosted_deployment.yaml` as an optional future-hosting checklist. Hosted
deployment is out of scope for local-only production-grade and is not required for a
local-only release.

This runbook is validate-only. It does not create hosted infrastructure, write secrets,
open a public endpoint, publish DNS, issue TLS certificates, or deploy a registry image.

## Validate Readiness

Run from the repository root:

```powershell
.\scripts\run_hosted_deployment_check.ps1
```

The check verifies that:

- `config/hosted_deployment.yaml` links to the image-publication and release-readiness
  catalogs;
- optional local gates exist before any future hosted handoff;
- future hosted runtime inputs stay explicit: `REGISTRY_IMAGE`, `IMAGE_DIGEST`,
  `PUBLIC_BASE_URL`, `DATABASE_URL`, `API_KEYS`, `API_KEY_SPECS`,
  `REVIEWER_ACCOUNTS`, and `REVIEWER_ACCOUNT_SCOPES`;
- future hosted runtime evidence stays explicit: immutable image digest, deployed image
  ref, public HTTPS URL, TLS status, health/version/metrics/queue-health checks, report
  workflow smoke, rollback target, and backup/restore proof;
- hosted platform, DNS/TLS, secrets manager, managed database, billing reconciliation,
  alerting, and image-digest requirements remain deferred remote requirements.

## Operator Workflow

1. Run `.\scripts\run_hosted_deployment_check.ps1`.
2. Run `$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1`.
3. Run `.\scripts\run_deployment_smoke.ps1` against isolated local Compose.
4. Run `.\scripts\run_release_readiness_check.ps1`.
5. For local-only release, stop here. Do not create hosted infrastructure, write hosted
   secrets, open a public endpoint, or deploy a registry image.
6. After an explicit future-hosting scope change, record the deployed image digest,
   public HTTPS URL, TLS status, health/version/metrics/queue-health results, report
   workflow smoke result, rollback target, and backup/restore proof before calling the
   hosted environment production-ready.

## Known Limits

- This proof is local and validate-only.
- Hosted deployment is out of scope for local-only operation.
- The catalog is an optional future-hosting checklist.
- No hosted deployment, domain, TLS endpoint, hosted alert route, or pager route is
  created.
- No secrets are written or validated against a hosted secrets manager.
- No registry image is deployed by this proof.
- No hosted billing reconciliation is planned for local-only operation.
