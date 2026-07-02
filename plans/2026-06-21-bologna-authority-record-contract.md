# Bologna Authority Record Contract

## Goal
Make the first Bologna authority gate recordable in a concrete, machine-checked format. The slice should define the required fields and cross-checks for future product/AOI/scope authority evidence while preserving the current `missing_authority` state and keeping all downstream source-rights, corpus, DB, runtime, and report work blocked.

## Non-goals
- Do not approve product, AOI, source, source-rights, DS-017, hosted, or Level 10 authority.
- Do not move any `scope_decision_requests` row out of `missing_authority`.
- Do not change source-rights decisions from `pending_review`.
- Do not create a recorded-source corpus, fixture, source-failure fixture, source registry row, DB seed, runtime artifact, report artifact, rulepack, or source profile.
- Do not change public API, auth, DB schema, report semantics, connector behavior, or qualification status.

## Current state
- Live `origin/main` is `604f7c2739095d9cc543b675ed3b84e619cda54d`, which merged PR #138 and routes the active pursuit to the Bologna authority gate.
- `config/bologna_pilot_scope_authority.yaml` lists the required product, one-AOI, operator, non-goal, stop-condition, jurisdiction, scope, DS-017, source-selection, fixture, runtime, and no-overclaim decisions, but each row has empty `authority_references` and `decision_updates_allowed: false`.
- `config/bologna_source_authority_intake.yaml`, `config/bologna_source_rights.yaml`, and `config/bologna_recorded_source_corpus.yaml` remain validate-only and blocked or pending.
- `config/production_authority_intake.yaml` already mirrors the Bologna pilot-scope and recorded-source streams as blocked external-authority streams.
- `state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 authority context. This slice does not reinterpret hosted, DS-017, Bologna, source-rights, or production-readiness gates.
- Focused Bologna validators/tests and full `.\scripts\verify.ps1` passed at baseline in `worktrees/bol-auth`; DB smoke was skipped by default.

## Proposed design
Add an authority-record contract to the pilot-scope packet and make the checker validate it. The contract should name the required fields for any future authority record, the allowed reference classes, the required coverage of all first-gate scope decision IDs, and the no-overclaim controls that must remain true until a complete cited record is present.

Rejected alternative: update source-rights or corpus rows now. That would require product/AOI/source-review authority the repo does not have.

Rejected alternative: keep only prose decision requests. Prose is helpful for humans but does not make the future evidence packet fail closed when required fields, coverage, or boundary controls drift.

## Bottom-up sequence
1. Add failing tests that require a Bologna authority-record contract and checker coverage.
2. Add the contract to `config/bologna_pilot_scope_authority.yaml`.
3. Extend `scripts/bologna_pilot_scope_authority_check.py` to validate the contract and keep current authority records empty.
4. Update the runbook, active routing/state files, and tests that assert the active plan/task queue.
5. Run focused Bologna checks/tests, qualification status/change-impact checks, diff hygiene, and full verification.
6. Review and merge only if no authority boundary is crossed.

## Files likely to change
| File | Expected change |
|---|---|
| `plans/2026-06-21-bologna-authority-record-contract.md` | New executable plan. |
| `config/bologna_pilot_scope_authority.yaml` | Add authority-record contract while keeping records empty and blocked. |
| `scripts/bologna_pilot_scope_authority_check.py` | Validate the contract and required coverage. |
| `docs/runbooks/bologna_pilot_scope_authority.md` | Document the record format and blocked boundary. |
| `backend/tests/test_bologna_pilot_scope_authority_artifacts.py` | Assert the contract and fail-closed drift behavior. |
| `backend/tests/test_qualification_parameterization_backlog_artifacts.py` | Update active routing assertions. |
| `backend/tests/test_readiness_core_artifacts.py` | Update project-readiness active-plan/task assertions. |
| `tasks/task_queue.yaml` | Add completed/in-progress routing for this authority-record slice. |
| `plans/README.md` | Record this plan as the current authority-first slice. |
| `state/PROJECT_STATE.md` | Route current checkpoint to this authority-record contract. |
| `state/WORKLOG.md` | Record progress and preserved blockers. |
| `state/VALIDATION_LOG.md` | Record validation evidence. |

## Tests / verification
```powershell
py -3.12 scripts\bologna_pilot_scope_authority_check.py
py -3.12 scripts\bologna_source_authority_intake_check.py
py -3.12 scripts\bologna_source_rights_check.py
py -3.12 scripts\bologna_recorded_source_corpus_check.py
py -3.12 scripts\qualification_status_check.py --root .
py -3.12 scripts\qualification_change_impact_check.py --root .
$env:PYTHONPATH='backend'; py -3.12 -m pytest backend\tests\test_bologna_pilot_scope_authority_artifacts.py backend\tests\test_bologna_source_authority_intake_artifacts.py backend\tests\test_bologna_source_rights_artifacts.py backend\tests\test_bologna_recorded_source_corpus_artifacts.py backend\tests\test_readiness_core_artifacts.py backend\tests\test_qualification_parameterization_backlog_artifacts.py -q
git diff --check
git diff --name-only --diff-filter=D
.\scripts\verify.ps1
```

Expected signal: all checks pass; the authority-record contract is validated; current authority records remain empty; Bologna source/corpus/report work remains blocked; no tracked deletions; no qualification `PASS`.

## Risks and blockers
- The main blocker remains the absence of real product/AOI/source-review authority. This slice makes the evidence format stricter but cannot satisfy authority from repo-local inference.
- The main risk is making a future approval path look like current approval. The config and checker must keep current records empty and downstream updates disabled.

## Decision log
- 2026-06-21: Choose an authority-record contract as the next authority-first slice because it advances the ability to record real authority without inventing authority.

## Progress log
- 2026-06-21: Created `worktrees/bol-auth` from live `origin/main@604f7c2739095d9cc543b675ed3b84e619cda54d` on branch `codex/bol-auth-packet`.
- 2026-06-21: Baseline focused Bologna validators/tests and full `.\scripts\verify.ps1` passed; DB smoke skipped because `RUN_DB_SMOKE` was not set.
- 2026-06-21: Added failing tests for the missing `authority_record_contract`, then implemented the contract, checker validation, and runbook wording.
- 2026-06-21: Initial focused validation exposed that the active plan must cite `state/LEVEL_9_10_GATE_MATRIX.md` and preserve Level 9/10 context; updated this plan and reran `qualification_status_check.py` successfully.
- 2026-06-21: Focused Bologna validators, qualification status/change-impact checks, and focused artifact/routing pytest passed with fail-fast handling.
- 2026-06-21: Initial full `.\scripts\verify.ps1` failed because the active validation log did not list the full verify command; updated `state/VALIDATION_LOG.md`, confirmed the targeted readiness parser test passed, then reran full `.\scripts\verify.ps1` successfully.
