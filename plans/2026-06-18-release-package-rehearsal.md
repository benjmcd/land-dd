# Release-Candidate Package Rehearsal

## Goal

Prove the local release-candidate package boundary is adequate for source/runtime/operator
handoff from the current repo state, without publishing a registry image, creating hosted
infrastructure, writing secrets, or claiming hosted production readiness.

## Non-goals

- No registry push, image signing, hosted deployment, hosted smoke test, domain/TLS setup,
  pager route, or external attestation.
- No DS-017 vendor/source approval, connector implementation, paid-source use, or product
  decision removing DS-017 from Must scope.
- No committed ZIP, generated package manifest, runtime artifact, secret, or paid-vendor
  data dump.
- No DB schema, API contract, report-semantics, source-status, geography, or rulepack
  change.

## Current state

- `state/LEVEL_9_10_GATE_MATRIX.md` preserves the current Level 9/10 distinction between
  repo-local release-candidate proof and blocked hosted production evidence.
- `state/POST_RC_AUTHORITY_SPLIT.md` says local implementation can continue with a
  release-candidate package rehearsal while hosted/source/vendor authority remains blocked.
- `config/release_package.yaml` defines a local package boundary under
  `local_artifacts/releases`.
- `scripts/build_release_package.py` creates a ZIP plus JSON manifest and fails instead
  of deleting or overwriting existing outputs.
- `scripts/release_package_check.py` validates the package catalog, builders, wrappers,
  and runbook limits without creating package artifacts.
- `docs/runbooks/release_package.md` documents the local-only package workflow and
  explicitly separates it from image publication and hosted deployment.
- `R-014` completed source-review cadence consistency, so package rehearsal should prove
  the current source-review/runbook/checker surfaces are included or intentionally
  excluded by the package boundary.

## Proposed design

Audit the release-package include/exclude catalog against the current handoff authority
surfaces, then add the narrowest package-boundary guard or runbook wording needed to prove
that a local release candidate contains the source/runtime/operator materials required to
resume or inspect the build. If a generated package is built for proof, keep it under
ignored `local_artifacts/releases` and do not commit it.

## Bottom-up sequence

1. Audit `config/release_package.yaml`, `scripts/build_release_package.py`,
   `scripts/release_package_check.py`, `docs/runbooks/release_package.md`, and the current
   state/plan/task routing surfaces.
2. Determine whether `plans/`, `state/`, `tasks/`, source-review docs, runbooks,
   registries, and validation scripts are intentionally included, intentionally excluded,
   or inconsistently omitted from the local package boundary.
3. Extend validate-only release-package checks only where an omission would make handoff
   evidence incomplete or ambiguous.
4. Update runbook/catalog wording narrowly, preserving the local-only/no-publish boundary.
5. Run focused release-package/release-readiness checks and full verification before
   handoff.

## Files likely to change

| File | Expected change |
|---|---|
| `config/release_package.yaml` | Include/exclude adjustment only if audit finds a real handoff boundary gap. |
| `scripts/release_package_check.py` | Static guard for package boundary completeness if needed. |
| `backend/tests/test_release_package_artifacts.py` | Focused regression coverage for any new package guard. |
| `docs/runbooks/release_package.md` | Clarify local package rehearsal workflow and limits if needed. |
| `state/PROJECT_STATE.md` | Record scope and validation. |
| `state/WORKLOG.md` | Record completion summary. |
| `state/VALIDATION_LOG.md` | Record validators and result. |
| `tasks/task_queue.yaml` | Mark task active/done as appropriate. |

## Tests / verification

```powershell
python .\scripts\release_package_check.py
.\scripts\run_release_package_check.ps1
python .\scripts\release_readiness_check.py
python .\scripts\readiness_matrix_check.py
cd backend; python -m pytest -q .\tests\test_release_package_artifacts.py .\tests\test_release_readiness_artifacts.py
cd backend; python -m ruff check <touched files>
cd backend; python -m mypy <touched files>
git diff --check
git diff --name-only --diff-filter=D
.\scripts\verify.ps1
```

## Risks and blockers

- A local package rehearsal must not be mistaken for registry image publication or hosted
  release evidence.
- Generated package ZIPs/manifests must stay ignored under `local_artifacts/releases` and
  must not be committed.
- The package boundary should be intentionally scoped; do not add broad repo dumps unless
  the package purpose requires them.
- DS-017, hosted deployment, image publication, alerting, billing, IdP/RBAC, and secret
  manager blockers remain external-authority requirements.

## Decision log

- 2026-06-18: Selected as the next repo-local follow-on after `R-014` because hosted
  alerting and DS-017 remain externally blocked, while local release-candidate package
  rehearsal is explicitly allowed by `state/POST_RC_AUTHORITY_SPLIT.md`.

## Progress log

- 2026-06-18: Plan opened after source review cadence consistency was guarded.
- 2026-06-18: Rehearsal gap audit found the package omitted backend tests,
  selected-county fixture roots, startup/state/plan/task routing surfaces, lanes, and
  `.dockerignore`; it also lacked an explicit volatile exclusion for
  `state/agent-inbox` and a positive guard that `docs/planning_pack` stays packaged
  while verifier inputs depend on it.
- 2026-06-18: Updated the package catalog, static checker, artifact tests, and runbook
  to include source/runtime/operator handoff authority while preserving local-only
  limits. Focused package/readiness tests, release-package validators, ruff, mypy,
  whitespace check, and deletion check passed.
