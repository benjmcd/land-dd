# Image Publication Runbook

## Purpose

Use `config/image_publication.yaml` as the repo-local image publication readiness
boundary. It records the backend image source, required pre-publish gates, required
post-publish evidence, and blockers that prevent treating the current local image as a
published production artifact.

This runbook is validate-only. It does not push a registry image, create a hosted
deployment, sign an image SBOM, or publish registry-image attestations.

## Validate Readiness

Run from the repository root:

```powershell
.\scripts\run_image_publication_check.ps1
```

The check verifies that:

- `config/image_publication.yaml` points at `backend/Dockerfile` and the repo root build
  context;
- required release, deployment smoke, container scan, and verification gates exist;
- required publication evidence remains explicit: image digest, registry image ref,
  vulnerability scan, dependency SBOM, and provenance;
- registry and hosted-deployment blockers remain recorded;
- CI and local scripts do not push registry images as part of validate-only checks.

## Operator Workflow

1. Run `.\scripts\run_image_publication_check.ps1`.
2. Run `$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1`.
3. Run `.\scripts\run_container_scan_check.ps1`.
4. Run `.\scripts\run_deployment_smoke.ps1` against an isolated Compose project.
5. Do not push an image unless `REGISTRY_IMAGE`, registry ownership, deployment
   authority, and attestation authority have been explicitly approved outside this repo.
6. After any future push, record the immutable image digest and registry image ref before
   considering the image deployable.

## Known Limits

- This proof is local and validate-only.
- No registry image is pushed.
- No hosted deployment, domain, TLS endpoint, or runtime deployment smoke for a hosted
  environment exists.
- No signed image SBOM, SLSA provenance, or published registry-image attestation exists.
- `REGISTRY_IMAGE` is intentionally only an expected future input; it is not required for
  the current validate-only check.
