# Bologna Source Rights Matrix

## Goal

Advance the Bologna recorded-source pilot from candidate discovery to a fail-closed
source-rights review matrix. The outcome is a machine-readable packet that maps every
Bologna source candidate to the rights, provenance, source-schema, and no-overclaim
decisions required before any candidate can become a source registry row, recorded
fixture, runtime input, or report source.

This is not source approval. It does not select a Bologna AOI, promote source registry
rows, commit recorded-source fixtures, run connectors, change source readiness, approve
an Italy/EU rulepack, unblock DS-017, or claim hosted production authority.

## Non-goals

- No live connector, scraper, WMS/WFS client, API route, UI route, DB seed, migration,
  report behavior, or source-readiness count change.
- No approval for cache, redistribution, export, AI use, raw-data handling, fixture
  capture, runtime use, or report use.
- No legal planning, cadastral, access, title, buildability, wetland jurisdiction,
  environmental-liability, appraisal, lending, or investment conclusion.
- No hosted deployment, identity/RBAC, object-store, observability, billing, alerting,
  secret-manager, image-publication, production workload, or Level 10 proof.

## Current state

- Live `origin/main` is at merged PR #108
  `ec6d3e2e7fb0fbfb88c20d5424437d2ebfbb19d9`.
- `BSC-001` added `config/bologna_source_candidates.yaml` and kept every candidate
  not approved, not source-registry-promoted, disallowed for runtime use, and
  disallowed for fixture-corpus use.
- `config/bologna_preflight.yaml` still keeps `italy_source_rights_review` blocked on
  external authority and `italy_source_inventory` at `missing_candidate_decision`.
- `schemas/source_schema.json` defines the source contract fields that any promoted
  source registry row must answer.
- `state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 sequencing authority and
  keeps source, DS-017, hosted, Bologna, and multi-geography claims separated.
- Baseline Bologna source-candidates, Bologna preflight, Must-source readiness,
  release-readiness, and readiness-matrix validators passed before edits.

## Proposed design

Add `config/bologna_source_rights.yaml` plus a checker, runbook, and source-review stub.
The matrix imports the candidate ids from `config/bologna_source_candidates.yaml` and
requires a pending rights-review row for each candidate. It pins every permission field
to `pending_review` and every approval/runtime flag to false.

Talmudic debate / coherence check:

- Position A: approve obvious public sources now. Rejected because exact source
  selection, terms version, source version/date, AI-use, raw-data, export, attribution,
  fixture, CRS, and caveat decisions are not reviewed.
- Position B: move straight to recorded fixtures. Rejected because no one-AOI scope or
  source-rights approval exists.
- Position C: only update state to mark BSC-001 complete. Rejected because it fixes
  routing but does not make the source-rights blocker more actionable.
- Position D: add a fail-closed rights matrix. Accepted because it is the narrowest
  repo-local step that converts candidate discovery into executable review criteria.

## Bottom-up sequence

1. Add `config/bologna_source_rights.yaml`, runbook, source-review stub, and wrappers.
2. Add a Python checker and focused artifact tests.
3. Compose the rights matrix into Bologna preflight and route `BSC-001` complete,
   `BSR-001` active.
4. Update manifest, plan index, task queue, project state, production authority packet,
   worklog, validation log, and Level 9/10 next-pass text.
5. Run focused tests/checkers, source/readiness validators, workspace validation,
   diff/no-deletion checks, and default `.\scripts\verify.ps1`.

## Files likely to change

| File | Expected change |
|---|---|
| `config/bologna_source_rights.yaml` | New fail-closed rights matrix. |
| `docs/runbooks/bologna_source_rights.md` | Operator interpretation and promotion sequence. |
| `docs/source-reviews/bologna-source-rights.md` | Pending source-rights review stub. |
| `scripts/bologna_source_rights_check.py` | Static checker for candidate/source-schema alignment. |
| `scripts/run_bologna_source_rights_check.ps1` | Windows wrapper. |
| `scripts/run_bologna_source_rights_check.sh` | POSIX wrapper. |
| `backend/tests/test_bologna_source_rights_artifacts.py` | Focused artifact and fail-closed tests. |
| `config/bologna_preflight.yaml` | Reference rights matrix as evidence for source-rights blocker. |
| `scripts/bologna_preflight_check.py` | Require/check the rights matrix remains unapproved. |
| `backend/tests/test_bologna_preflight_artifacts.py` | Confirm preflight composes rights matrix. |
| `MANIFEST.md` | Route the new authority surface. |
| `plans/README.md` | Mark BSC-001 complete and route BSR-001 active. |
| `tasks/task_queue.yaml` | Add active BSR-001. |
| `state/PROJECT_STATE.md` | New current checkpoint and roadmap. |
| `state/PRODUCTION_AUTHORITY_PACKET.md` | Add rights matrix to Bologna authority. |
| `state/WORKLOG.md` | Worklog entry. |
| `state/VALIDATION_LOG.md` | Validation entry. |

## Tests / verification

```powershell
py -3.12 -m pytest backend\tests\test_bologna_source_rights_artifacts.py backend\tests\test_bologna_source_candidates_artifacts.py backend\tests\test_bologna_preflight_artifacts.py -q
py -3.12 .\scripts\bologna_source_rights_check.py
.\scripts\run_bologna_source_rights_check.ps1
py -3.12 .\scripts\bologna_source_candidates_check.py
py -3.12 .\scripts\bologna_preflight_check.py
py -3.12 .\scripts\source_readiness.py --priority Must --json
py -3.12 .\scripts\release_readiness_check.py
py -3.12 .\scripts\readiness_matrix_check.py
git diff --check
git diff --name-only --diff-filter=D
.\scripts\validate_workspace.ps1
.\scripts\verify.ps1
```

Expected signal: every Bologna rights row remains pending and blocked; candidate ids
match the candidate catalog; source-schema required fields are represented; Bologna
preflight still blocks source approval; Must source readiness remains
`sources=8 ready=7 blocked=1` with only `DS-017` blocked.

## Risks and blockers

- Source pages and dataset licenses can drift. This matrix is a review contract, not a
  current terms approval.
- Cadastral cartography remains a direct official-source review gap and cannot be used
  as parcel, owner, title, access, or buildability authority.
- A recorded-source pilot still needs an authorized AOI, exact source selections,
  source reviews, CRS policy, fixture corpus, source-failure fixtures,
  rulepack/evidence-only scope, and DB-backed report proof.

## Decision log

- 2026-06-20: Chose a fail-closed rights matrix instead of source approval or fixtures
  because the repo has candidates but no authorized AOI, exact source selection, or
  completed source-rights reviews.

## Progress log

- 2026-06-20: Created clean `worktrees/bol-rights` on `codex/bol-rights` from live
  `origin/main` at `ec6d3e2e7fb0fbfb88c20d5424437d2ebfbb19d9`.
- 2026-06-20: Baseline Bologna source-candidates, Bologna preflight, Must-source
  readiness, release-readiness, and readiness-matrix validators passed before edits.
- 2026-06-20: Added the source-rights matrix, runbook, review stub, checker, wrappers,
  focused tests, and Bologna preflight composition while keeping every rights decision
  pending and every promotion/runtime/report/raw-export flag false.
- 2026-06-20: Focused tests/checkers, wrapper, ruff, mypy, Must-source readiness,
  release-readiness, readiness-matrix, workspace validation, and diff/no-deletion
  checks passed. Final default `.\scripts\verify.ps1` passed with DB smoke skipped by
  default.
