# Source Provenance UI G5

## Goal

Add a read-only `/ui/source-provenance` operator view over the selected-county
source-provenance catalog and current Must-source readiness records. The page should
make DS-010, DS-011, DS-023, and the DS-017 blocker visible before any generic AOI,
Bologna, or multi-geography expansion work.

## Non-goals

- No connector execution, fixture seeding, runtime provenance creation, evidence row
  creation, report creation, or source registry mutation.
- No DS-017 approval, paid/vendor source selection, license decision, source expansion,
  county expansion, Bologna pilot, jurisdiction/rulepack approval, or hosted production
  proof.
- No DB schema, public JSON API, report semantics, claim/rule behavior, auth/RBAC,
  hosted identity, hosted deployment, or Level 10 completion claim.

## Current state

- `state/reconciliation-dispositions.md` identifies G5 as the next report/source/evidence
  provenance slice after the accepted G1/G2/G3 prerequisites.
- `config/private_mvp_beta_readiness.yaml` already contains
  `selected_county_source_provenance_scope` for Buncombe, Chatham, and Brunswick across
  DS-010, DS-011, and DS-023.
- `backend/app/source_registry/readiness.py` is the packaged authority for Must-source
  readiness records; `scripts/source_readiness.py --priority Must --json` currently
  reports 8 Must sources, 7 ready, and DS-017 as the only blocked Must source.
- `state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 gate authority for this
  pass; this plan exposes provenance/source-authority expectations but does not promote
  any hosted, entitlement, jurisdiction, rulepack, or production gate.
- County source manifests record the human-readable selected-county source stance and
  DS-017 private-MVP deferral.
- G3 deployment readiness is merged on `origin/main`, but state routing still needs the
  next active-plan update.

## Proposed design

Add a packaged helper in `backend/app/source_provenance.py` that reads
`config/private_mvp_beta_readiness.yaml` and `registers/data_source_registry.csv`, builds
Must-source readiness records with `app.source_registry.readiness`, and validates the
selected-county provenance catalog before the UI renders it. Add a GET-only
`/ui/source-provenance` route linked from the current local operator pages.

Rejected alternatives:

- Copy the dirty-root provenance UI stack wholesale: the reconciliation matrix requires
  replay from live main with narrow tests.
- Render unchecked YAML: this would turn catalog drift into apparent authority instead
  of failing closed.
- Jump directly to runtime provenance or generic AOI expansion: the selected-county
  source/version/retrieval expectations and DS-017 boundaries need inspectable authority
  first.

## Bottom-up sequence

1. Add failing parser and route tests for the selected-county source-provenance helper
   and UI route.
2. Implement the read-only helper over current repo-owned config/registry files.
3. Add `/ui/source-provenance` and navigation from home, raw-data, and deployment
   readiness pages.
4. Regenerate OpenAPI stubs for the new FastAPI UI route.
5. Update routing/state/worklog/validation records after verification.

## Files likely to change

| File | Expected change |
|---|---|
| `backend/tests/api/test_ui_source_provenance.py` | Parser, fail-closed, route, and navigation tests. |
| `backend/app/source_provenance.py` | Read-only parser/model for selected-county source provenance and Must-source readiness. |
| `backend/app/api/ui.py` | Add GET-only source-provenance route and current-page nav links. |
| `api/openapi_stub.yaml` | Regenerated FastAPI contract stub. |
| `docs/planning_pack/api/openapi_stub.yaml` | Regenerated planning-pack mirror. |
| `DESIGN.md` | Add local operator source-provenance route boundary. |
| `docs/runbooks/mvp_operator.md` | Add operator route and non-goal boundary. |
| `plans/README.md` | Active-plan pointer. |
| `tasks/task_queue.yaml` | Active-plan routing. |
| `state/PROJECT_STATE.md` | Current checkpoint and boundaries. |
| `state/WORKLOG.md` | Work summary. |
| `state/VALIDATION_LOG.md` | Commands, results, residual risk. |

## Tests / verification

```powershell
cd backend
py -3.12 -m pytest -q .\tests\api\test_ui_source_provenance.py
ruff check .\app\source_provenance.py .\app\api\ui.py .\tests\api\test_ui_source_provenance.py
py -3.12 -m mypy .\app\source_provenance.py .\app\api\ui.py .\tests\api\test_ui_source_provenance.py
cd ..
py -3.12 .\scripts\export_openapi_stub.py
cd backend
py -3.12 -m pytest -q .\tests\api\test_openapi_contract.py::test_openapi_stub_path_methods_match_runtime_schema .\tests\test_planning_pack_schema_copies.py::test_planning_pack_openapi_stub_matches_generated_fastapi_contract
cd ..
py -3.12 .\scripts\source_readiness.py --priority Must --json
py -3.12 .\scripts\private_mvp_readiness_check.py
py -3.12 .\scripts\release_readiness_check.py
py -3.12 .\scripts\readiness_matrix_check.py
git diff --check
git diff --name-only --diff-filter=D
.\scripts\validate_workspace.ps1
.\scripts\verify.ps1
```

## Risks and blockers

- The page can overclaim if it implies runtime provenance exists for every catalog row.
  Tests and copy must keep it a source/version/retrieval expectation view only.
- DS-017 must remain a full-release Must blocker and private-MVP deferral unless external
  vendor/license authority changes.
- Catalog and source-readiness logic overlap; the helper should pin request-critical UI
  invariants while existing validators remain the broader readiness authority.

## Decision log

- 2026-06-20: Selected the narrow G5 source-provenance UI because G3 deployment
  readiness is merged, G5 is the next retained slice in the disposition sequence, and
  source/version/retrieval expectations are prerequisite to generic AOI, Bologna, and
  multi-geography expansion work.

## Progress log

- 2026-06-20: Live `origin/main`, worktrees, inboxes, state routing, reconciliation
  dispositions, selected-county provenance catalog, source manifests, Must-source
  readiness, and private-MVP readiness were audited before edits. Narrow baseline
  workspace, Must-source, and private-MVP checks passed.
- 2026-06-20: Implemented `app.source_provenance`, `/ui/source-provenance`, current-page
  navigation, OpenAPI refresh, and docs/state routing. Focused source-provenance tests
  passed (`6 passed`), OpenAPI parity passed (`2 passed`), focused ruff/mypy passed,
  source-readiness/private-MVP/release-readiness/readiness-matrix validators passed,
  diff/no-deletion/workspace checks passed, and full `.\scripts\verify.ps1` passed with
  backend tests, ruff, and mypy over `332` source files. DB smoke was skipped by
  default.
