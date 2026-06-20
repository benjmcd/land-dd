# Selected-County Source Provenance Catalog

## Goal
Make selected-county source-provenance expectations machine-checkable before raw
source/dataset/retrieval records are interpreted in UI or report flows. The catalog
declares which DS-010, DS-011, and DS-023 connector outputs should have dataset,
version, and retrieval provenance expectations for Buncombe, Chatham, and Brunswick,
and which combinations remain intentionally out of scope.

## Non-goals
- Do not run connectors, seed fixture/runtime data, create provenance records, or
  require Docker/Postgres.
- Do not approve DS-017, add county/vendor coverage, or change source licensing
  decisions.
- Do not change source, evidence, claim, report, DB, connector, UI, or public API
  runtime semantics.
- Do not create accounts, alter auth/security boundaries, implement OAuth/OIDC/full
  RBAC, or claim hosted identity.
- Do not provision hosted deployment, publish images/packages, write secrets, or claim
  Level 10 completion.

## Current state
- Live `origin/main` at slice start was
  `5440934218182b309b784bfde29a5bc7d34d870e`, after PR #91 merged the `G1b`
  raw-data inventory UI.
- `state/reconciliation-dispositions.md` ranks `G3b` after `G1b`: selected-county
  source-provenance catalog and validate-only checker with explicit fixture/non-live
  labels.
- `config/private_mvp_beta_readiness.yaml` already declares selected-county source
  scope and county manifest scope for DS-010, DS-011, and DS-023.
- The missing lower-layer authority is a machine-readable selected-county provenance
  expectation matrix, not runtime provenance hydration.
- `state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 gate authority. This pass
  improves private-MVP selected-county source-provenance guardrails only and must not
  promote any gate.

## Proposed design
Add `selected_county_source_provenance_scope` to the private-MVP readiness catalog.
For each selected county and selected source, declare connector names, dataset
expectation, version expectation, retrieval expectation, and explicit out-of-scope
state. Extend `scripts/private_mvp_readiness_check.py` to validate the catalog against
the selected source scope, county manifest scope, DS-017 exclusion, and Buncombe DS-023
out-of-scope boundary.

Rejected alternatives:
- Seeding runtime provenance records would violate validate-only behavior and hide
  empty runtime state.
- Copying broad dirty-root UI/readiness changes would mix later route work into this
  source-provenance authority slice.
- Treating DS-017 as an out-of-scope catalog row would blur the current private-MVP
  decision; DS-017 remains blocked and excluded from the selected-county provenance
  scope.

## Bottom-up sequence
1. Add focused tests that fail on the missing provenance scope and validator.
2. Add the provenance catalog section to the private-MVP readiness YAML.
3. Add validator helpers and compose them into the existing private-MVP checker.
4. Update narrow routing docs/state so future source/UI work uses this catalog as
   selected-county provenance authority.
5. Run focused tests, validate-only checkers, hygiene checks, workspace validation, and
   full verification.

## Files likely to change
| File | Expected change |
|---|---|
| `config/private_mvp_beta_readiness.yaml` | Add selected-county source-provenance scope. |
| `scripts/private_mvp_readiness_check.py` | Validate provenance catalog cross-links. |
| `backend/tests/test_private_mvp_readiness.py` | Add structure and rejection tests. |
| `MANIFEST.md` | Route private-MVP readiness to the provenance catalog. |
| `docs/IMPLEMENTATION_READINESS.md` | Note the catalog as the raw-data/source-provenance authority. |
| `docs/runbooks/mvp_operator.md` | Preserve selected-county provenance/non-live limits. |
| `plans/README.md` | Route active/latest checkpoint. |
| `tasks/task_queue.yaml` | Add `G3b` task routing. |
| `state/PROJECT_STATE.md` | Record current checkpoint. |
| `state/WORKLOG.md` | Record implementation summary. |
| `state/VALIDATION_LOG.md` | Record verification evidence. |

## Tests / verification
```powershell
py -3.12 -m pytest -q .\backend\tests\test_private_mvp_readiness.py
py -3.12 .\scripts\private_mvp_readiness_check.py
py -3.12 .\scripts\release_readiness_check.py
py -3.12 .\scripts\readiness_matrix_check.py
cd backend; ruff check .\tests\test_private_mvp_readiness.py ..\scripts\private_mvp_readiness_check.py
cd backend; py -3.12 -m mypy .\tests\test_private_mvp_readiness.py ..\scripts\private_mvp_readiness_check.py
git diff --check
git diff --name-only --diff-filter=D
.\scripts\validate_workspace.ps1
.\scripts\verify.ps1
```

## Risks and blockers
- This is static provenance expectation proof, not runtime dataset/retrieval record
  creation.
- DS-011 remains a NOT_EVALUATED sentinel and must not imply live assessor data.
- DS-023 must remain Chatham/Brunswick only; Buncombe zoning stays explicitly out of
  scope until a separate source and connector decision exists.
- The raw-data UI can show only existing runtime records; this catalog does not hydrate
  missing source-provenance bundles.

## Decision log
- 2026-06-20: Chose the narrowed `G3b` catalog guard because live main already has
  selected-county source scope, while the missing authority is the per-county
  dataset/version/retrieval provenance expectation matrix.

## Progress log
- 2026-06-20: Opened from clean `worktrees/prov-cat` on live `origin/main` at
  `5440934218182b309b784bfde29a5bc7d34d870e`; no active inbox collision found.
- 2026-06-20: Added focused tests first. The intentional red run failed on the missing
  `selected_county_source_provenance_scope` section, then passed after adding the
  catalog and validator composition.
- 2026-06-20: Private-MVP, release-readiness, readiness-matrix, Must-source readiness,
  focused ruff, focused mypy, private-MVP wrapper, diff/no-deletion, workspace
  validation, and full `.\scripts\verify.ps1` passed. Full verify ran backend tests,
  ruff, and mypy over `328` source files; DB smoke was skipped by default.
