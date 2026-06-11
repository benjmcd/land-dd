# Release Package Runbook

## Purpose

Use `config/release_package.yaml` as the repo-local release package boundary. The package
builder creates a local ZIP bundle and sibling JSON manifest from the current worktree.
It is intended for release-candidate handoff after the release-readiness and full
verification gates pass.

This runbook does not push a registry image, create a hosted deployment, attach hosted
attestations, approve blocked sources, or weaken evidence/report safety constraints.

## Validate Package Boundary

Run from the repository root:

```powershell
.\scripts\run_release_package_check.ps1
```

The check is validate-only. It verifies that:

- the Windows and POSIX wrappers delegate to the shared
  `scripts/release_package_check.py` validator;
- `config/release_package.yaml` uses schema `release_package_v1`;
- every declared include path exists;
- excluded path parts cover `.git`, caches, `local_artifacts`, and `worktrees`;
- the Windows and POSIX builders use exclusive ZIP creation and write a JSON manifest;
- release package outputs stay under `local_artifacts/releases`;
- package builders record that they do not push registry images, create hosted
  deployments, or include secrets.

## Build A Local Package

Run the full release gate first:

```powershell
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
.\scripts\run_release_readiness_check.ps1
.\scripts\run_release_package_check.ps1
```

Then create a local release candidate package:

```powershell
.\scripts\build_release_package.ps1 -Version 2026-06-05-rc1
```

The builder writes:

- `local_artifacts/releases/land-diligence-<version>.zip`
- `local_artifacts/releases/land-diligence-<version>-release-manifest.json`

The builder fails if either output already exists. It does not delete, overwrite, push, deploy, or publish anything.

## Known Limits

- The package is a local source/runtime/operator artifact bundle, not a hosted release.
- No registry image is pushed.
- No hosted deployment, domain, TLS endpoint, hosted alerting, or pager routing is
  created.
- No published registry-image attestation, signed image SBOM, or SLSA provenance
  attestation exists yet.
- The package reflects the current worktree. Run verification immediately before
  packaging and keep the manifest with the ZIP.
