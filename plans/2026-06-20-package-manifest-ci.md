# Package Manifest CI Gate

## Goal

Land the first retained post-reconciliation product slice: a standalone verifier for
built release-package manifests, plus an additive CI gate that builds a local package and
checks the generated sibling manifest against the ZIP contents.

## Non-goals

- Do not publish a release package, push a registry image, sign artifacts, or deploy.
- Do not add hosted deployment, hosted identity/RBAC, hosted observability, billing, or
  source-entitlement authority.
- Do not change public APIs, database schema, report semantics, source registry policy,
  source-readiness decisions, or selected-geography behavior.
- Do not commit generated ZIP/manifest artifacts under `local_artifacts/releases`.
- Do not copy unrelated dirty-root readiness/UI changes into this branch.

## Current state

Live `origin/main` was refreshed before this worktree was created and pointed at
`52b167a96643befa863f9501d1171385c4a25383`. No open GitHub PRs were present. The clean
worktree for this slice is `worktrees/pkg-manifest` on `codex/pkg-manifest`; the dirty
root branch remains preserved candidate evidence only.

The merged reconciliation disposition ranks `G7a` first after `REC-001`: package-manifest
validator, release-package manifest verification, and an additive CI gate. Live main
already has `config/release_package.yaml`, `scripts/build_release_package.py`,
`scripts/release_package_check.py`, Windows/POSIX release-package wrappers, and release
readiness cataloging. It does not have a standalone checker that validates a generated
external manifest against the ZIP's embedded manifest and file entries.

`state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 release-readiness authority for
hosted/source/identity/artifact claims. This slice may strengthen local release-package
artifact proof, but it must not change matrix statuses or imply hosted release authority.

## Proposed design

Add `scripts/package_manifest_check.py` as a read-only checker that accepts a generated
external release manifest path. The checker validates:

- manifest schema/source/package id and local-only limit flags;
- external `zip_sha256` against the ZIP bytes;
- embedded `release-manifest.json` equality after removing the external-only ZIP hash;
- declared file count, path uniqueness, sizes, and SHA-256 hashes;
- absence of undeclared ZIP entries;
- package paths against `config/release_package.yaml` include/exclude boundaries.

Add thin Windows/POSIX wrappers that require an existing manifest path. Update the
release-package validator so it fails closed if the checker/wrappers or runbook wording
drift. Map the existing `release_package` release-readiness check to a new
`release-package-manifest` CI job. That CI job has read-only repository permissions, runs
the package-boundary proof, builds an ignored local package, and validates the generated
manifest.

Talmudic debate:

| Position | Argument | Resolution |
|---|---|---|
| Only add a local script | Smallest change and enough for operators. | Rejected because `G7a` explicitly includes a CI gate, and omission would let artifact verification drift. |
| Add a separate release-readiness check id for the manifest | Makes the manifest proof first-class. | Rejected because the wrapper requires a generated manifest path; a no-arg readiness proof would be misleading or would have to generate artifacts. |
| Map `release_package` to a CI job that builds and validates locally | Keeps one package authority while proving the generated manifest in CI. | Accepted because it matches the current catalog model and avoids overstating publish/sign/deploy authority. |

## Bottom-up sequence

1. Re-ground live `origin/main`, open a clean worktree under `worktrees/pkg-manifest`,
   and verify no open PR supersedes the slice.
2. Audit live release-package/readiness files and dirty-root G7a candidates.
3. Add failing focused tests for manifest checker behavior, release-package artifact
   guardrails, and release-readiness CI mapping.
4. Add the checker, wrappers, CI job, catalog updates, and runbook/routing updates.
5. Run focused tests and validators, then broader verification.
6. Publish and merge only after CI and post-merge proof agree with local validation.

## Files likely to change

| File | Expected change |
|---|---|
| `.github/workflows/ci.yml` | Add `release-package-manifest` job. |
| `backend/tests/test_package_manifest_check.py` | New focused behavior tests for checker failures and success. |
| `backend/tests/test_release_package_artifacts.py` | Require checker, wrappers, and runbook coverage. |
| `backend/tests/test_release_readiness_artifacts.py` | Require release-package CI mapping and job shape. |
| `config/release_readiness.yaml` | Map `release_package` to `release-package-manifest`. |
| `docs/runbooks/release_package.md` | Document post-build manifest verification and limits. |
| `docs/runbooks/release_readiness.md` | Document the new CI gate. |
| `MANIFEST.md` | Route release-package work to the checker/wrappers. |
| `scripts/package_manifest_check.py` | New read-only package manifest checker. |
| `scripts/run_package_manifest_check.ps1` | Windows wrapper for existing manifest checks. |
| `scripts/run_package_manifest_check.sh` | POSIX wrapper for existing manifest checks. |
| `scripts/release_package_check.py` | Require checker artifacts and docs. |
| `scripts/release_readiness_check.py` | Require the CI job and release-readiness mapping. |
| `state/PROJECT_STATE.md`, `state/WORKLOG.md`, `state/VALIDATION_LOG.md` | Record active slice and validation evidence. |

## Tests / verification

```powershell
cd backend
python -m pytest -q .\tests\test_package_manifest_check.py .\tests\test_release_package_artifacts.py .\tests\test_release_readiness_artifacts.py
python -m ruff check .\tests\test_package_manifest_check.py .\tests\test_release_package_artifacts.py .\tests\test_release_readiness_artifacts.py ..\scripts\package_manifest_check.py ..\scripts\release_package_check.py ..\scripts\release_readiness_check.py
python -m mypy .\tests\test_package_manifest_check.py .\tests\test_release_package_artifacts.py .\tests\test_release_readiness_artifacts.py ..\scripts\package_manifest_check.py ..\scripts\release_package_check.py ..\scripts\release_readiness_check.py
cd ..
python .\scripts\release_package_check.py
.\scripts\run_release_package_check.ps1
python .\scripts\release_readiness_check.py
.\scripts\build_release_package.ps1 -Version <proof-version>
.\scripts\run_package_manifest_check.ps1 -Manifest .\local_artifacts\releases\land-diligence-<proof-version>-release-manifest.json
git diff --check
git diff --name-only --diff-filter=D
.\scripts\verify.ps1
```

## Risks and blockers

- The CI job creates ignored local package artifacts; they must not be committed.
- The checker proves package/manifest integrity only for local source/runtime/operator
  handoff. It is not signing, SLSA provenance, registry publication, hosted deployment,
  or source-rights approval.
- Existing release-readiness source blockers remain unchanged, especially DS-017.
- Full DB smoke remains separate and is not implied unless `RUN_DB_SMOKE=1` is set.

## Decision log

- 2026-06-20: Selected `G7a` after re-checking live `origin/main`, no open PRs, and the
  merged reconciliation disposition sequence.
- 2026-06-20: Chose a manifest-path-required checker so validate-only wrapper calls do
  not generate package artifacts.
- 2026-06-20: Chose to map `release_package` to `release-package-manifest` in
  `config/release_readiness.yaml` instead of adding a misleading no-arg manifest check.

## Progress log

- 2026-06-20: Focused red tests failed for the intended reasons: missing checker,
  missing wrappers, missing runbook text, missing CI job, and no release-package CI
  mapping.
- 2026-06-20: Added checker, wrappers, release-package validator coverage,
  release-readiness CI mapping, CI job, docs, and manifest routing. Focused tests passed
  (`32 passed`).
