# Bologna Authority Record Validation

## Goal
Make the Bologna pilot-scope authority checker able to validate a future complete
cited authority record while preserving the committed `missing_authority` state. The
slice should prove that a complete record shape can be accepted in test isolation, that
partial or unlocking records fail closed, and that the committed packet still carries no
current authority records.

## Non-goals
- Do not approve product, AOI, source, source-rights, DS-017, hosted, or Level 10
  authority.
- Do not add any real `current_authority_records` entry to the committed config.
- Do not move any `scope_decision_requests` row out of `missing_authority`.
- Do not change source-rights decisions from `pending_review`.
- Do not create a recorded-source corpus, fixture, source-failure fixture, source
  registry row, DB seed, runtime artifact, report artifact, rulepack, or source profile.
- Do not change public API, auth, DB schema, report semantics, connector behavior, or
  qualification status.

## Current state
- Live `origin/main` is `d356cfdf20ead6ee11573cfffc502d7c21769012`, which merged PR
  #139 and added the Bologna authority-record contract.
- `config/bologna_pilot_scope_authority.yaml` has
  `authority_record_contract.current_authority_records: []`; every first-gate
  `scope_decision_requests` row remains `missing_authority`, with empty
  `authority_references` and `decision_updates_allowed: false`.
- `scripts/bologna_pilot_scope_authority_check.py` validates the authority-record
  contract fields, authority types, required coverage, and no-overclaim controls, but it
  only accepts an empty `current_authority_records` list.
- `config/bologna_source_authority_intake.yaml`, `config/bologna_source_rights.yaml`,
  and `config/bologna_recorded_source_corpus.yaml` remain validate-only and blocked or
  pending.
- `state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 authority context. This
  slice does not reinterpret hosted, DS-017, Bologna, source-rights, or production
  readiness gates.
- Focused baseline checks passed in `worktrees/bol-rec`: the pilot-scope authority
  pytest file and pilot-scope authority checker both pass before edits.

## Proposed design
Extract authority-record validation into explicit checker helpers. The helpers should
accept an in-memory complete record only when it has exactly the required fields, a
known authority type, non-empty cited artifacts, full coverage across the required
scope decisions, no unknown scope decision IDs, no downstream unlock requests, and
list-shaped caveats, stop conditions, and superseded-record references.

Committed config remains blocked by policy, not by checker ignorance: the checker should
allow an empty committed `current_authority_records` list, and tests should continue to
assert that the committed list is empty. If a future non-empty list is committed, the
checker must require full first-gate coverage and still forbid downstream unlock
requests.

Rejected alternative: keep the hard empty-list rule. That preserves safety but leaves
the next real authority packet unvalidated until authority arrives.

Rejected alternative: allow partial authority records. That would create ambiguity about
whether downstream source-authority, source-rights, corpus, or report work can begin.
The safer first validation contract is complete-record-only.

## Bottom-up sequence
1. Add failing tests for a complete in-memory record, partial-record failure, and
   downstream-unlock failure.
2. Extend `scripts/bologna_pilot_scope_authority_check.py` with authority-record helper
   validation and complete-record coverage checks.
3. Update the pilot-scope runbook to document complete-record-only validation while
   preserving the committed empty-record boundary.
4. Update active routing/state files and tests to record `BAR-001`.
5. Run focused Bologna checks/tests, qualification status/change-impact checks, diff
   hygiene, and full verification.
6. Review and merge only if no authority boundary is crossed.

## Files likely to change
| File | Expected change |
|---|---|
| `plans/2026-06-21-bologna-authority-record-validation.md` | New executable plan. |
| `scripts/bologna_pilot_scope_authority_check.py` | Validate complete future authority records in addition to the contract. |
| `docs/runbooks/bologna_pilot_scope_authority.md` | Document complete-record-only validation and blocked committed state. |
| `backend/tests/test_bologna_pilot_scope_authority_artifacts.py` | Add fail-closed tests for complete, partial, and unlocking records. |
| `backend/tests/test_qualification_parameterization_backlog_artifacts.py` | Update active routing assertions. |
| `backend/tests/test_readiness_core_artifacts.py` | Update project-readiness active-plan/task assertions. |
| `tasks/task_queue.yaml` | Add completed/in-progress routing for `BAR-001`. |
| `plans/README.md` | Record this plan as the current authority-first slice. |
| `state/PROJECT_STATE.md` | Route current checkpoint to this authority-record validation slice. |
| `state/WORKLOG.md` | Record progress and preserved blockers. |
| `state/VALIDATION_LOG.md` | Record validation evidence. |

## Tests / verification
```powershell
$env:PYTHONPATH='backend'; py -3.12 -m pytest backend\tests\test_bologna_pilot_scope_authority_artifacts.py -q
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

Expected signal: all checks pass; the checker validates a complete future authority
record shape in test isolation; partial or unlocking records fail closed; committed
authority records remain empty; Bologna source/corpus/report work remains blocked; no
tracked deletions; no qualification `PASS`.

## Risks and blockers
- The main blocker remains the absence of real product/AOI/source-review authority. This
  slice proves the validation path for future evidence; it does not satisfy the
  authority blocker.
- The main risk is making a test-only complete record look like committed authority.
  The committed config, runbook, state, and tests must keep `current_authority_records`
  empty and all downstream updates disabled.

## Decision log
- 2026-06-21: Choose complete-record-only authority validation as the next
  authority-first slice because it reduces future intake ambiguity without fabricating
  authority or unblocking downstream work.

## Progress log
- 2026-06-21: Created `worktrees/bol-rec` from live
  `origin/main@d356cfdf20ead6ee11573cfffc502d7c21769012` on branch
  `codex/bol-record-gate`.
- 2026-06-21: Baseline focused pilot-scope authority pytest and checker passed.
- 2026-06-21: Added red tests for complete, partial, and downstream-unlocking
  authority records; initial focused pytest failed because the checker rejected every
  non-empty `current_authority_records` list before validating record content.
- 2026-06-21: Implemented complete-record validation, updated the runbook, and routed
  `BAR-001` through task/state surfaces while keeping committed authority records empty.
- 2026-06-21: Focused pilot-scope, adjacent Bologna, qualification status/change-impact,
  focused artifact/routing pytest, diff hygiene, and tracked-deletion checks passed.
- 2026-06-21: Full `.\scripts\verify.ps1` passed; DB smoke was skipped because
  `RUN_DB_SMOKE` was not set.
