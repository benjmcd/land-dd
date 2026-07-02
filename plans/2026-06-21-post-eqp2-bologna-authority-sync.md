# Post-EQP2 Bologna Authority Sync

## Goal
Close the completed EQ Phase 2 routing loop and make the next authoritative pursuit the prioritized Bologna product/AOI/source-rights authority gate. This should move the repo's active routing away from the completed checker-parity lane and toward the first blocked Bologna authority decision surface without approving sources, selecting an AOI, capturing fixtures, or starting report/runtime work.

## Non-goals
- Do not approve product, AOI, source, source-rights, DS-017, hosted, or Level 10 authority.
- Do not change source-rights rows from pending review.
- Do not create a recorded-source corpus, source-failure fixture, DB seed, runtime artifact, report artifact, source registry row, source profile, domain profile, or qualification result.
- Do not move any qualification, overlay, conditional overlay, or criterion to `PASS`.
- Do not change public API, auth, DB schema, report semantics, connector behavior, or checker gate behavior.

## Current state
- `origin/main` is `e6b1fe1c75111abc3a7dabd625fa186b2b72115f`, which merged PR #137 for `EQP2-4`.
- `EQP2-1` through `EQP2-4` are merged and post-merge verified; status derivation, change-impact reporting, P0 auto-evidence, and checker advertisement parity are all repo-local executable checks.
- Before this sync, routing still pointed `active_plan` at `plans/2026-06-21-eqp2-4-checker-parity.md`, and the current project-state section still described EQP2-4 as pending merge/proof.
- The Bologna path is the prioritized product pursuit, but all implementation steps remain blocked: `config/bologna_pilot_scope_authority.yaml` has empty authority references, `config/bologna_source_authority_intake.yaml` is `blocked_no_authority`, `config/bologna_source_rights.yaml` keeps every candidate pending review, and `config/bologna_recorded_source_corpus.yaml` is `blocked_no_authority`.
- `state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 authority context. This routing sync does not reinterpret hosted, DS-017, Bologna, source-rights, or production-readiness gates.
- `BSA-001` is the first substantive Bologna task, but it cannot proceed until explicit product/AOI/source-review authority exists.

## Proposed design
Add a routing-only sync task that records EQ Phase 2 as complete and makes the next active plan this Bologna authority sync. The sync should explicitly point the next substantive work at the existing Bologna authority packets and keep `BSA-001` blocked until cited authority exists.

Rejected alternatives:
- Start `BSA-001` now: rejected because the authority packets have no cited product/AOI/source-review evidence.
- Build the recorded-source corpus contract further: rejected because the contract already exists and remains blocked until scope/source rights are approved.
- Promote `EQ-5` ahead of Bologna: rejected because the active product goal is the Bologna pilot; EQ-5 remains a useful repo-local fallback if external Bologna authority does not arrive.

## Bottom-up sequence
1. Reconcile live `origin/main`, worktree ownership, and current Bologna authority packet status.
2. Add this plan.
3. Update `tasks/task_queue.yaml`, `plans/README.md`, `state/PROJECT_STATE.md`, `state/WORKLOG.md`, and `state/VALIDATION_LOG.md` so EQP2-4 is complete and Bologna authority is the next pursuit.
4. Update project-readiness/routing tests that assert the active plan.
5. Run focused Bologna and qualification checks, project-readiness tests, diff hygiene checks, and full verification.
6. Publish/merge only if checks and review confirm no authority boundary was crossed.

## Files likely to change
| File | Expected change |
|---|---|
| `plans/2026-06-21-post-eqp2-bologna-authority-sync.md` | New routing sync plan. |
| `tasks/task_queue.yaml` | Active plan and routing note update; add completed routing-sync task. |
| `plans/README.md` | Mark EQP2-4 latest completed and this plan as current routing. |
| `state/PROJECT_STATE.md` | Replace current checkpoint with post-EQP2 Bologna authority routing. |
| `state/LEVEL_9_10_GATE_MATRIX.md` | Referenced authority context; no planned content change. |
| `state/WORKLOG.md` | Record sync work and preserved boundaries. |
| `state/VALIDATION_LOG.md` | Record validation evidence. |
| `backend/tests/test_qualification_parameterization_backlog_artifacts.py` | Assert the new active plan and completed sync task. |
| `backend/tests/test_readiness_core_artifacts.py` | Assert project-readiness view follows the new active plan. |

## Tests / verification
```powershell
py -3.12 scripts\bologna_pilot_scope_authority_check.py
py -3.12 scripts\bologna_source_authority_intake_check.py
py -3.12 scripts\bologna_source_rights_check.py
py -3.12 scripts\bologna_recorded_source_corpus_check.py
py -3.12 scripts\qualification_status_check.py --root .
py -3.12 scripts\qualification_change_impact_check.py --root .
py -3.12 scripts\qualification_p0_evidence_check.py --root .
$env:PYTHONPATH='backend'; py -3.12 -m pytest backend\tests\test_readiness_core_artifacts.py backend\tests\test_qualification_parameterization_backlog_artifacts.py backend\tests\test_bologna_pilot_scope_authority_artifacts.py backend\tests\test_bologna_source_authority_intake_artifacts.py backend\tests\test_bologna_source_rights_artifacts.py backend\tests\test_bologna_recorded_source_corpus_artifacts.py -q
git diff --check
git diff --name-only --diff-filter=D
.\scripts\verify.ps1
```

Expected signal: all checks pass; Bologna authority artifacts remain blocked and validate-only; no tracked deletions; no qualification `PASS`; `BSA-001` remains blocked until external authority is cited.

## Risks and blockers
- The main risk is overclaiming routing progress as source/corpus/report authority. This plan deliberately syncs routing only.
- The substantive Bologna goal remains blocked by missing external product/AOI/source-rights authority. This pass can make that blocker clearer, but it cannot satisfy it from repo-local inference.
- The root checkout is a dirty preservation lane; all implementation must remain in `worktrees/bol-sync` from live `origin/main`.

## Decision log
- 2026-06-21: Treat EQP2 as complete after PR #137 and detached proof, then make Bologna authority intake the next active pursuit while preserving every source/corpus/report blocker.

## Progress log
- 2026-06-21: Created `worktrees/bol-sync` from live `origin/main@e6b1fe1c75111abc3a7dabd625fa186b2b72115f` on branch `codex/bol-auth-routing`.
- 2026-06-21: Updated routing/state/test surfaces so `EQP2-4` is complete, `BOL-AUTH-SYNC` records the transition, and `BSA-001` remains blocked on cited product/AOI/source-review authority.
- 2026-06-21: Focused Bologna/qualification/routing checks, diff hygiene checks, and full `.\scripts\verify.ps1` passed; DB smoke skipped because `RUN_DB_SMOKE` was not set.
