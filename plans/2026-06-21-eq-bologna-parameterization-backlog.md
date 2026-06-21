# Bologna-First Qualification Parameterization Backlog

## Goal
Pull the empirical-qualification parameterization backlog forward for the
prioritized Bologna path, without landing the qualification validator/catalog spine or
approving any owner/source/AOI decision. The result is a repo-local blocked backlog
that makes `P0 = BLOCKED` and the Bologna product/AOI/source-rights sequence visible
before any downstream corpus or report proof work.

## Non-goals
- Do not copy the qualification vocabulary, criterion catalog, schemas, validator,
  selftest, status file, source profiles, domain profiles, or CI gate.
- Do not mark any qualification gate `PASS`, change the intended blocked status, or
  unfreeze owner decisions.
- Do not select a Bologna AOI, approve Italy/EU/local sources, change source rights,
  promote source registry rows, capture fixtures, create source-failure fixtures,
  seed the database, run connectors, create report/runtime artifacts, or implement a
  Bologna rulepack.
- Do not approve DS-017, hosted authority, identity/RBAC, observability, billing, image
  publication, production workload, multi-geography coverage, or Level 10 status.

## Current state
Live `origin/main` is `6d671875aee1c0a7fcba1d6124c2ffbb05841457`, which merged PR
#124 (`EQ-1`). The root checkout remains a dirty preserved lane; this work is isolated
in `worktrees/eq-bol` on `eq/bol-backlog`.

ADR 0004 makes the empirical-qualification catalog the future canonical
empirical-validity authority. The spine itself has not landed. The read-only framework
package at `C:\Users\benny\Downloads\land-dd_empirical_qualification` says project
qualification remains blocked because active targets, criterion contracts, judgment
rubrics, domain profiles, source profiles, source versions, reviewers, and empirical
evidence are not frozen. Bologna validate-only packets already exist for pilot scope,
source candidates, source rights, source-authority intake, and recorded-source corpus,
and they all remain blocked with empty authority references.
`state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 authority context for this
lane; this backlog does not change any gate status or create Level 10 evidence.

The user elevated the Bologna recorded-source path over broad EQ-2/EQ-3/EQ-4 work.
The coherent narrow slice is to surface the blocked Bologna and P0 parameterization
backlog now, while leaving the self-validating spine as the next mechanical EQ step.

## Proposed design
Add `state/QUALIFICATION_PARAMETERIZATION_BACKLOG.md` as a concise, exhaustive blocker
register. It will quote counts and active blocker IDs from
`PROJECT_PARAMETERIZATION_BLOCKERS.md`, cross-reference the existing Bologna authority
catalogs, and list every blocker as `BLOCKED (external/owner authority)`.

Update task routing with an `EQ-BOL` completed visibility lane plus grouped `BLOCKED`
follow-ons for targets/contracts, rubrics, domain profiles, source profiles,
scope/version fields, Bologna pilot-scope authority, Bologna source rights, Bologna
recorded corpus, and Bologna report proof. This satisfies the user's Bologna priority
without pretending that full EQ-2/EQ-3/EQ-4 are done.

Rejected alternative: run full EQ-2 first. That would make the spine available, but it
would ignore the user's explicit priority to advance the Bologna path first.

Rejected alternative: approve any Bologna source/AOI from repo-local inference. That
would violate the existing authority packets and the project non-negotiable that source
rights must be reviewed before source-derived use.

## Bottom-up sequence
1. Reconfirm live main, worktree isolation, and current Bologna/qualification authority
   surfaces.
2. Add a failing artifact test that requires the backlog doc and task routing to exist.
3. Add the backlog doc with blocker counts, active gates, target bindings, rubrics,
   domain/source profile blockers, scope/version blockers, and Bologna decision chain.
4. Update routing/state surfaces and adoption-plan decision log to record the pulled
   forward Bologna backlog slice.
5. Run focused artifact tests, Bologna validators, readiness validators, no-deletion
   checks, workspace validation, and full verification.

## Files likely to change

| File | Expected change |
|---|---|
| `plans/2026-06-21-eq-bologna-parameterization-backlog.md` | New executable plan |
| `state/QUALIFICATION_PARAMETERIZATION_BACKLOG.md` | New blocked parameterization backlog |
| `backend/tests/test_qualification_parameterization_backlog_artifacts.py` | Focused artifact/routing tests |
| `plans/2026-06-21-empirical-qualification-adoption.md` | Decision log note for pulled-forward Bologna backlog |
| `MANIFEST.md` | Route the backlog state file |
| `plans/README.md` | Mark the current lane and preserved blockers |
| `state/PROJECT_STATE.md` | Record the current checkpoint and next steps |
| `tasks/task_queue.yaml` | Add `EQ-BOL` and grouped blocked follow-ons |
| `state/WORKLOG.md` | Record implementation facts |
| `state/VALIDATION_LOG.md` | Record validation evidence |

## Tests / verification
```powershell
py -3.11 -c "import yaml; yaml.safe_load(open('tasks/task_queue.yaml', encoding='utf-8')); print('task queue parses')"
py -3.12 .\scripts\bologna_pilot_scope_authority_check.py
py -3.12 .\scripts\bologna_source_rights_check.py
py -3.12 .\scripts\bologna_recorded_source_corpus_check.py
py -3.12 .\scripts\bologna_preflight_check.py
py -3.12 .\scripts\readiness_matrix_check.py
cd backend; py -3.12 -m pytest tests\test_qualification_parameterization_backlog_artifacts.py tests\test_bologna_pilot_scope_authority_artifacts.py tests\test_bologna_recorded_source_corpus_artifacts.py tests\test_readiness_core_artifacts.py -q
git diff --check
git diff --name-only --diff-filter=D
.\scripts\validate_workspace.ps1
.\scripts\verify.ps1
```

Expected signal: backlog and task routing are present, every blocker remains blocked,
Bologna authority packets remain validate-only and unapproved, no tracked deletions
exist, and the default verification gate passes.

## Risks and blockers
The main risk is making a backlog look like progress toward approval. The backlog must
therefore use blocked statuses, explicit external/owner-authority language, empty
authority-reference assumptions, and no fixture/runtime/report unlocks.

## Decision log
- 2026-06-21: User elevated the Bologna path above broad EQ-2/EQ-3/EQ-4 work.
  Consensus: pull the parameterization/backlog visibility slice forward, but leave all
  Bologna and qualification approvals blocked.

## Progress log
- 2026-06-21: Created `worktrees/eq-bol` on `eq/bol-backlog` from live `origin/main`
  at `6d671875aee1c0a7fcba1d6124c2ffbb05841457`.
- 2026-06-21: Added the red backlog artifact test, implemented the blocked backlog and
  routing/state updates, fixed the active-plan Level 9/10 citation required by
  `readiness_matrix_check.py`, and reran focused Bologna/readiness checks green.
