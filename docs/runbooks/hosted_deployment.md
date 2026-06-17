# Hosted Deployment Runbook

## Purpose

Use `config/hosted_deployment.yaml` as the repo-local hosted deployment readiness
boundary. It records the required pre-deploy gates, runtime inputs, runtime evidence,
and blockers that must be resolved before a hosted environment can be treated as
production-ready.

This runbook is validate-only. It does not create hosted infrastructure, write secrets,
open a public endpoint, publish DNS, issue TLS certificates, or deploy a registry image.

## Validate Readiness

Run from the repository root:

```powershell
.\scripts\run_hosted_deployment_check.ps1
```

The check verifies that:

- the Windows and POSIX wrappers delegate to the shared
  `scripts/hosted_deployment_check.py` validator;
- `config/hosted_deployment.yaml` links to the image-publication and release-readiness
  catalogs;
- required local gates exist before any hosted handoff;
- required hosted runtime inputs stay explicit and match the non-local auth contract:
  `REGISTRY_IMAGE`, `IMAGE_DIGEST`, `PUBLIC_BASE_URL`, `DATABASE_URL`,
  `API_KEY_SPECS`, `REVIEWER_ACCOUNTS`, `REVIEWER_ACCOUNT_SCOPES`,
  `UI_AUTH_COOKIE_SECRET`, and `REPORT_IDENTITY_TOKEN_SECRET`;
- hosted API-key auth uses `API_KEY_SPECS`; `API_KEYS` is local/dev/development/test
  only and is not a required hosted runtime input;
- required hosted runtime evidence stays explicit: immutable image digest, deployed image
  ref, public HTTPS URL, TLS status, health/version/metrics/queue-health checks, report
  workflow smoke, rollback target, and backup/restore proof;
- `attestation_evidence` records the future hosted production proof contract with
  `status: not_available`, the required fields, the current blockers, and an empty
  evidence template;
- hosted platform, DNS/TLS, secrets, database, billing, alerting, and image-digest
  blockers remain recorded.

## Operator Workflow

1. Run `.\scripts\run_hosted_deployment_check.ps1`.
2. Run `$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1`.
3. Run `.\scripts\run_deployment_smoke.ps1` against isolated local Compose.
4. Run `.\scripts\run_release_readiness_check.ps1`.
5. Do not create a hosted deployment until registry image digest, hosted platform,
   database instance, secrets manager, domain/TLS, billing, alerting, rollback, and
   evidence-capture authority are explicitly available.
6. After a future hosted deployment, record the deployed image digest, public HTTPS URL,
   TLS status, health/version/metrics/queue-health results, report workflow smoke result,
   rollback target, and backup/restore proof before calling it production-ready. Fill
   every field in the `attestation_evidence.evidence_template` contract before changing
   its status away from `not_available`.

## Known Limits

- This proof is local and validate-only.
- No hosted deployment, domain, TLS endpoint, hosted alert route, or pager route is
  created.
- No secrets are written or validated against a hosted secrets manager, and this
  proof does not claim that a hosted secrets manager exists.
- No registry image is deployed by this proof.
- No hosted billing reconciliation exists yet.
- The structured attestation template is intentionally empty while hosted deployment
  authority is unavailable.
