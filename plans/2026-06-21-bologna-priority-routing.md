# Bologna Priority Routing

## Goal
Record Bologna recorded-source pilot preparation as the preferred next pursuit after
`READINESS-CORE`, ahead of generic hosted-production, generic DS-017, and broad
production-authority lanes unless external evidence directly unblocks one of those
streams.

## Non-goals
- Do not select a Bologna AOI, approve Italy/EU/local sources, change source rights,
  promote source registry rows, capture fixtures, run connectors, seed the database, or
  create report/runtime artifacts.
- Do not approve DS-017, choose a vendor, provision hosted services, implement hosted
  identity/RBAC, publish images, add billing, or claim Level 10 authority.
- Do not generalize a multi-geography framework before a one-AOI Bologna pilot proves
  reusable contracts.

## Current state
Live `origin/main` is `fa66b561e8820273963f51642d7dc3ef56ac0491`, which merged PR
#119 (`READINESS-CORE`). The dirty root checkout remains preserved candidate evidence
only, so this routing update is isolated in `worktrees/bol-priority`.

The repo already has validate-only Bologna preparation surfaces:

- `config/bologna_preflight.yaml`
- `config/bologna_source_candidates.yaml`
- `config/bologna_source_rights.yaml`
- `config/bologna_source_authority_intake.yaml`
- `config/bologna_recorded_source_corpus.yaml`

Those catalogs intentionally keep every Bologna source/AOI/corpus/runtime decision
blocked until cited product, AOI, and source-review authority exists. `BSA-001` is the
existing task that represents the first real Bologna gate: filling the source-rights
matrix from explicit authority for exact candidate sources.

`state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 authority context for this
routing decision. Prioritizing Bologna does not change any Level 10 hosted-production
or source-entitlement gate status.

## Proposed design
Update routing/state files so `BSA-001` and the Bologna recorded-source pilot path are
the preferred next pursuit. The priority order becomes:

1. Bologna pilot authority and source-rights preparation.
2. If authority is available, cite it in the Bologna source-authority intake and source
   rights matrix before any fixture or runtime change.
3. After source/AOI rights are approved, build one recorded-source corpus with source
   versions, retrieval metadata, CRS, attribution, caveats, source-failure fixtures,
   and storage/export boundaries.
4. Only after the corpus is approved, prove one DB-backed Bologna report with claims,
   evidence, unknowns, caveats, artifacts, and lineage.
5. Only after the pilot exposes reusable contracts, design the multi-geography
   source/rulepack framework.

Rejected alternative: pursue hosted/Level 10 first. That would prove deployment
machinery before answering the more product-defining question: whether a non-US
recorded-source locality pilot can be authorized, represented, and reported without
overclaiming.

Rejected alternative: pursue generic DS-017 first. DS-017 remains important for full
release boundaries, but it should not block Bologna source-authority preparation unless
the Bologna pilot explicitly needs a DS-017 treatment decision.

## Bottom-up sequence
1. Reconfirm live `origin/main`, worktree placement, and current Bologna authority
   surfaces.
2. Add this routing plan.
3. Update project state, plan index, task queue, gate matrix, worklog, and validation
   log so Bologna source-authority preparation is the preferred next pursuit.
4. Run focused validate-only checks for Bologna/source/readiness routing.
5. Run workspace validation and full verification before publication.

## Files likely to change

| File | Expected change |
|---|---|
| `plans/2026-06-21-bologna-priority-routing.md` | New routing plan |
| `plans/README.md` | Mark Bologna priority routing as current |
| `state/PROJECT_STATE.md` | Record PR #119 baseline and new priority order |
| `state/LEVEL_9_10_GATE_MATRIX.md` | Update next-pass guidance |
| `tasks/task_queue.yaml` | Add `BOL-PRIORITY` routing task and active plan |
| `state/WORKLOG.md` | Record routing decision |
| `state/VALIDATION_LOG.md` | Record validation evidence |

## Tests / verification
```powershell
py -3.12 .\scripts\bologna_source_authority_intake_check.py
py -3.12 .\scripts\bologna_source_rights_check.py
py -3.12 .\scripts\bologna_recorded_source_corpus_check.py
py -3.12 .\scripts\bologna_preflight_check.py
py -3.12 .\scripts\production_authority_intake_check.py
py -3.12 .\scripts\source_readiness.py --priority Must --json
py -3.12 .\scripts\readiness_matrix_check.py
git diff --check
git diff --name-only --diff-filter=D
.\scripts\validate_workspace.ps1
.\scripts\verify.ps1
```

Expected signal: checks pass, no deleted files exist, DS-017 remains the only blocked
Must source, Bologna remains blocked for implementation/runtime/report use until cited
authority exists, and hosted/Level 10 authority remains blocked.

## Risks and blockers
The main risk is confusing "prioritize Bologna" with "Bologna is approved." This plan
does not lower the authority threshold. It only makes the next pursuit the Bologna
authority/source-rights path rather than generic hosted production or generic DS-017
work, while preserving the Level 9/10 boundary between repo-local proof and blocked
hosted/source authority.

## Decision log
- 2026-06-21: User directed the Bologna recorded-source path to be prioritized over
  hosted/Level 10, generic authority-fork, and generic DS-017 pursuits. Consensus:
  prioritize Bologna source/AOI/right-authority preparation first, while preserving all
  fail-closed gates.

## Progress log
- 2026-06-21: Created `worktrees/bol-priority` from live `origin/main` at
  `fa66b561e8820273963f51642d7dc3ef56ac0491`.
- 2026-06-21: Updated routing/state artifacts so `BSA-001` is the preferred next
  pursuit while all Bologna implementation, source, hosted, DS-017, and Level 10 gates
  remain blocked without cited authority.
- 2026-06-21: Focused Bologna/readiness validators, workspace validation, focused
  readiness-core artifact tests, and full `.\scripts\verify.ps1` passed.
