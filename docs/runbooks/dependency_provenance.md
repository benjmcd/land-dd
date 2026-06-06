# Dependency Provenance Runbook

## Purpose

Use `backend/requirements-prod.lock` and `docs/sbom/backend-prod-sbom.json` as the
repo-local Level 10 production dependency provenance artifacts for the backend runtime.
The CI `dependency-attestations` job validates those artifacts, publishes GitHub
artifact attestations for them, and publishes an SBOM attestation that binds the
CycloneDX SBOM to the production lock subject.

The lock is derived from `backend/pyproject.toml` production dependencies for CPython
3.12 on `manylinux2014_x86_64` with binary wheels only. It pins the resolved runtime
dependency closure and records a SHA-256 hash for each wheel. The SBOM mirrors the same
component set and hashes in CycloneDX JSON form.

This runbook does not approve new production dependencies. Dependency source authority
remains `backend/pyproject.toml`; update that file first, then refresh the lock and SBOM
through a reviewed dependency-change slice.

## Validation

Run the validate-only proof from the repository root:

```powershell
.\scripts\run_provenance_check.ps1
```

The check verifies:

- the production lock exists and every entry is exactly pinned with a SHA-256 hash;
- direct production dependencies from `backend/pyproject.toml` are present in the lock;
- `uvicorn[standard]` and `psycopg[binary]` runtime packages are represented;
- the CycloneDX SBOM component set, versions, package URLs, and hashes match the lock;
- CI runs the provenance check before the advisory-backed `pip-audit --local` scan;
- CI has a `dependency-attestations` job with GitHub OIDC, attestation, and artifact
  metadata write permissions;
- the attestation job uses `actions/attest@v4` for the lock/SBOM provenance artifacts
  and for the backend dependency SBOM;
- pip can perform a hash-checked dry run for the Linux production target without
  installing packages.

## Operator Workflow

1. Treat a failing provenance check as a release blocker until the lock, SBOM, or
   declared dependency authority is reconciled.
2. For dependency updates, change `backend/pyproject.toml` only when the new dependency
   or version range is justified and reviewed.
3. Refresh `backend/requirements-prod.lock` and `docs/sbom/backend-prod-sbom.json` from
   a pip dry-run report for the production target.
4. Run `.\scripts\run_provenance_check.ps1`, `.\scripts\run_supply_chain_check.ps1`, and
   the normal verification gate.
5. Do not edit the lock or SBOM to silence a scanner finding. Upgrade, remove, or
   explicitly risk-accept the affected dependency instead.
6. Treat a failing `dependency-attestations` job as a release blocker until the artifact
   subject paths, SBOM path, GitHub token permissions, or artifact metadata write path
   are corrected.

## Known Limits

- The SBOM is repo-local; CI publishes a GitHub SBOM attestation for it, but the repo
  does not yet publish a release artifact, package, or container image with a registry
  attached SBOM.
- CI publishes GitHub artifact attestations for the lock/SBOM files. This is not a
  hosted deployment attestation and does not prove a published container image.
- The lock targets the backend Python runtime, not Docker base-image packages, GitHub
  Actions internals, OS packages, frontend packages, or source dataset licensing.
- The hash dry run verifies available wheels for the declared Linux target; it does not
  deploy the image or prove runtime behavior by itself.
