# Image Publication Runbook

## Purpose

Use `config/image_publication.yaml` as an optional remote distribution checklist. Image
publication is out of scope for local-only production-grade and is not required for a
local-only release.

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
- optional remote pre-publish gates exist when remote distribution is later approved;
- local-only evidence remains limited to local image build, vulnerability scan,
  dependency SBOM, and release package manifest evidence;
- registry push, registry image ref, immutable published digest, signed image SBOM, and
  published provenance/attestation requirements remain deferred remote requirements;
- CI and local scripts do not push registry images as part of validate-only checks.

## Operator Workflow

1. Run `.\scripts\run_image_publication_check.ps1`.
2. Run `$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1`.
3. Run `.\scripts\run_container_scan_check.ps1`.
4. Run `.\scripts\run_deployment_smoke.ps1` against an isolated Compose project.
5. For local-only release, stop here. Do not push, sign, or attest a registry image.
6. After any explicit future remote-distribution scope change, record the immutable image
   digest and registry image ref before considering the image deployable.

## Known Limits

- This proof is local and validate-only.
- Image publication is out of scope for local-only operation.
- The catalog is an optional remote distribution checklist.
- No registry image is pushed.
- No hosted deployment, domain, TLS endpoint, or runtime deployment smoke for a hosted
  environment exists.
- No signed image SBOM, SLSA provenance, or published registry-image attestation is
  required for local-only release.
- `REGISTRY_IMAGE` is intentionally only an expected future input; it is not required for
  the current validate-only check.
