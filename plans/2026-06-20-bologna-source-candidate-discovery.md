# Bologna Source Candidate Discovery

## Goal

Turn the Bologna preflight's `italy_source_inventory` gap into a repo-visible,
validate-only source-candidate packet. The outcome is a preliminary inventory of
official candidate surfaces and unresolved source-rights gaps for a future one-AOI
Bologna recorded-source pilot.

This is not source approval. It does not select a Bologna AOI, promote source registry
rows, commit recorded-source fixtures, run connectors, change source readiness, approve
an Italy/EU rulepack, unblock DS-017, or claim hosted production authority.

## Non-goals

- No live connector, scraper, WMS/WFS client, API route, UI route, DB seed, migration,
  report behavior, or source-readiness count change.
- No source registry promotion and no claim that any candidate can be cached,
  redistributed, exported, used in AI extraction, or included in reports.
- No legal planning, cadastral, access, title, buildability, wetland jurisdiction,
  environmental-liability, or investment conclusion.
- No hosted deployment, identity/RBAC, object-store, observability, billing, alerting,
  secret-manager, image-publication, production workload, or Level 10 proof.

## Current state

- `BP-001` is merged on live `origin/main` through PR #107 at
  `295c96a4308b39e77fee7935d3b5e465755ad6bf`.
- Current state files still route to `BP-001` as active. That is stale after merge.
- `config/bologna_preflight.yaml` pins all Bologna approval flags to false and keeps
  `italy_source_inventory` at `missing_candidate_decision`.
- `state/LEVEL_9_10_GATE_MATRIX.md` is the current Level 9/10 sequencing authority and
  keeps source, DS-017, hosted, Bologna, and multi-geography claims separated.
- Baseline validators pass from the clean `worktrees/bol-src` worktree:
  `bologna_preflight_check.py`, Must source readiness, release readiness, and readiness
  matrix.
- Official web evidence located candidate discovery surfaces: Comune di Bologna PUG and
  open-data pages, Regione Emilia-Romagna Geoportale/DBTR/CRS pages, ARPAE cartographic
  portal, and official-looking Agenzia Entrate cadastral surfaces that still require
  direct source review before use.

## Proposed design

Add `config/bologna_source_candidates.yaml` plus a checker, runbook, and source-review
stub. The catalog lists candidate official surfaces by domain and records required
reviews before any candidate can become a source registry row or recorded fixture. The
checker fails closed if any candidate is marked approved or runtime-allowed.

Talmudic debate / coherence check:

- Position A: promote source candidates directly to `registers/data_source_registry.csv`.
  Rejected because license, cache, export, AI-use, attribution, raw-data, source-version,
  and caveat reviews are incomplete.
- Position B: leave source discovery only in prose. Rejected because the next agent
  could miss the exact candidate/gap boundary and accidentally treat search notes as
  approval.
- Position C: implement source clients now for official portals. Rejected because no AOI,
  source-rights review, CRS policy, fixture corpus, or report semantics exist.
- Position D: add a validate-only candidate packet. Accepted because it narrows the
  next source-rights pass without changing runtime behavior or authority.

## Bottom-up sequence

1. Add the candidate catalog, runbook, source-review stub, and validator wrappers.
2. Add a fail-closed Python checker and focused artifact tests.
3. Update the Bologna preflight evidence path, manifest, task routing, project state,
   plan index, worklog, validation log, and production authority packet.
4. Run focused tests/checkers and canonical validation.
5. Publish, merge, and remove the temporary worktree if checks and CI pass.

## Files likely to change

| File | Expected change |
|---|---|
| `config/bologna_source_candidates.yaml` | New validate-only candidate-source catalog. |
| `docs/runbooks/bologna_source_candidates.md` | Operator/runbook boundary for candidate sources. |
| `docs/source-reviews/bologna-source-candidates.md` | Candidate-only source review stub. |
| `scripts/bologna_source_candidates_check.py` | Static fail-closed validator. |
| `scripts/run_bologna_source_candidates_check.ps1` | Windows wrapper. |
| `scripts/run_bologna_source_candidates_check.sh` | POSIX wrapper. |
| `backend/tests/test_bologna_source_candidates_artifacts.py` | Focused artifact and fail-closed tests. |
| `config/bologna_preflight.yaml` | Reference the candidate packet as evidence while keeping approval blocked. |
| `scripts/bologna_preflight_check.py` | Require the candidate packet artifacts. |
| `backend/tests/test_bologna_preflight_artifacts.py` | Confirm preflight references candidate packet without approval. |
| `MANIFEST.md` | Route the new authority surface. |
| `plans/README.md` | Mark BP-001 complete and route this active slice. |
| `tasks/task_queue.yaml` | Mark BP-001 done and add active `BSC-001`. |
| `state/PROJECT_STATE.md` | New current checkpoint and roadmap. |
| `state/PRODUCTION_AUTHORITY_PACKET.md` | Add candidate-source packet to Bologna authority. |
| `state/WORKLOG.md` | Worklog entry. |
| `state/VALIDATION_LOG.md` | Validation entry. |

## Tests / verification

```powershell
py -3.12 -m pytest backend\tests\test_bologna_source_candidates_artifacts.py backend\tests\test_bologna_preflight_artifacts.py -q
py -3.12 .\scripts\bologna_source_candidates_check.py
.\scripts\run_bologna_source_candidates_check.ps1
py -3.12 .\scripts\bologna_preflight_check.py
.\scripts\run_bologna_preflight_check.ps1
py -3.12 .\scripts\source_readiness.py --priority Must --json
py -3.12 .\scripts\release_readiness_check.py
py -3.12 .\scripts\readiness_matrix_check.py
git diff --check
git diff --name-only --diff-filter=D
.\scripts\validate_workspace.ps1
.\scripts\verify.ps1
```

Expected signal: the source-candidate checker passes while every approval/runtime flag
remains false; Bologna preflight still passes with `italy_source_inventory` blocked;
Must source readiness remains `sources=8 ready=7 blocked=1` with only `DS-017`
blocked; no tracked deletions are present; default verify passes.

## Risks and blockers

- Candidate source pages can drift. Every candidate must be re-reviewed before source
  registry promotion or fixture capture.
- PUG/open-data pages may expose terms per dataset, not a blanket grant. Each dataset
  needs its own review.
- Regional DBTR layers may be useful for context but cannot substitute for cadastral,
  legal, planning, or environmental-review authority.
- Italian cadastral cartography is a separate review path and may not include owner,
  title, legal access, or buildability authority.
- A recorded-source pilot still needs an authorized AOI, source-rights decisions, CRS
  policy, fixture corpus, source-failure fixtures, rulepack/evidence-only scope, and
  DB-backed report proof.

## Decision log

- 2026-06-20: Chose a candidate-source packet rather than registry promotion because
  official candidate surfaces were found, but source rights and pilot authority remain
  unresolved.

## Progress log

- 2026-06-20: Created clean `worktrees/bol-src` on `codex/bol-src` from live
  `origin/main` at `295c96a4308b39e77fee7935d3b5e465755ad6bf` after confirming the
  dirty root checkout is preserved candidate evidence only.
- 2026-06-20: Baseline Bologna preflight, Must source readiness, release-readiness, and
  readiness-matrix validators passed before edits.
- 2026-06-20: Added the candidate catalog, runbook, source-review stub, checker,
  wrappers, focused tests, and preflight composition while keeping all source approval,
  registry-promotion, runtime, and fixture-corpus flags false.
- 2026-06-20: Focused tests/checkers, ruff, mypy, Must-source readiness,
  release-readiness, readiness-matrix, workspace validation, diff/no-deletion checks,
  and default `.\scripts\verify.ps1` passed. DB smoke was skipped by default.
