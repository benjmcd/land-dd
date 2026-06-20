# Release Package Runbook

## Purpose

Use `config/release_package.yaml` as the repo-local release package boundary. The package
builder creates a local ZIP bundle and sibling JSON manifest from the current worktree.
It is intended for release-candidate handoff after the release-readiness and full
verification gates pass.

This runbook does not push a registry image, create a hosted deployment, attach hosted
attestations, approve blocked sources such as DS-017, or weaken evidence/report safety
constraints.

The package carries startup/routing/state/plan/task authority for source/runtime/operator
handoff and resumability: root startup files, `MANIFEST.md`, `plans/`, selected
`state/*.md` authority files, `tasks/`, `lanes/`, `docs/`, runtime/configuration
sources, backend tests, and selected-county fixtures. It excludes state/agent-inbox
coordination dirt and local agent state such as `.omc`, `.gstack`, `.codesight`,
`.codex`, and `.claude`. It includes docs/planning_pack verification inputs because the
full local verifier and current artifact tests still read planning-pack schemas, OpenAPI,
and cost-input references.

## Validate Package Boundary

Run from the repository root:

```powershell
.\scripts\run_release_package_check.ps1
```

The check is validate-only. It verifies that:

- the Windows and POSIX wrappers delegate to the shared
  `scripts/release_package_check.py` validator;
- the Windows and POSIX package builders delegate to the shared
  `scripts/build_release_package.py` builder;
- `config/release_package.yaml` uses schema `release_package_v1`;
- every declared include path exists;
- excluded path parts cover `.git`, caches, local agent state, `local_artifacts`, and
  `worktrees`;
- the package includes startup/routing/state/plan/task authority files and directories;
- `scripts/verify.ps1` as a package gate implies backend tests are included;
- selected-county fixtures are included when the operator-cases manifest points at
  `tests/fixtures`;
- the boundary excludes `state/agent-inbox`;
- the boundary includes `docs/planning_pack` while the full verifier still depends on
  planning-pack reference artifacts;
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

## Verify A Built Package

Run post-build manifest verification against the generated sibling manifest:

```powershell
.\scripts\run_package_manifest_check.ps1 -Manifest .\local_artifacts\releases\land-diligence-2026-06-05-rc1-release-manifest.json
```

The wrapper delegates to `scripts/package_manifest_check.py`. The check verifies that
the external manifest has schema `release_package_manifest_v1`, the ZIP SHA-256 matches
`zip_sha256`, the embedded `release-manifest.json` matches the external manifest except
for the external-only ZIP hash, every declared ZIP entry has the recorded size and
SHA-256, no undeclared ZIP entries are present, packaged paths obey
`config/release_package.yaml`, and manifest limits still record no registry image push,
no hosted deployment, and no included secrets.

This is post-build manifest verification for a local source/runtime/operator package.
It is not image signing, registry publication, SLSA provenance, hosted deployment
attestation, or DS-017/source-rights approval.

## Known Limits

- The package is a local source/runtime/operator artifact bundle, not a hosted release.
- No registry image is pushed.
- No hosted deployment, domain, TLS endpoint, hosted alerting, or pager routing is
  created.
- No published registry-image attestation, signed image SBOM, or SLSA provenance
  attestation exists yet.
- `state/agent-inbox` is intentionally excluded because it is volatile local
  coordination state, not release-candidate handoff authority.
- Local agent state directories such as `.omc`, `.gstack`, `.codesight`, `.codex`, and
  `.claude` are intentionally excluded even when they appear under included source
  trees.
- The package does not approve blocked sources such as DS-017.
- `docs/planning_pack` is intentionally included because `scripts/verify.ps1` currently
  runs tests and checkers that compare planning-pack schemas, OpenAPI, and cost-input
  references against current root artifacts. Do not remove it from the package while the
  full verifier depends on it.
- The package reflects the current worktree. Run verification immediately before
  packaging and keep the manifest with the ZIP.
