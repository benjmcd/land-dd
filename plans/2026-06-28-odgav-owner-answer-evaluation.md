# ODGAV Owner-Answer Gate Evaluation

## Goal
Prove the Bologna owner-decision gates can evaluate complete future owner answers in
memory while preserving the current blocked state. The pass also records live worktree
branch reconciliation so no unmerged worktree is removed without branch-specific proof.

## Non-goals
- Do not record real owner authority, source authority, source-rights approval, corpus
  authority, or DB report-proof authority.
- Do not alter committed Bologna config approvals, current owner-answer records,
  authority records, source-rights rows, fixture state, DB state, report semantics, API
  surfaces, UI surfaces, or schemas.
- Do not change `backend/app/**`, `backend/app/api/ui.py`, or OpenAPI stubs; PR #166 is
  Claude-owned and remains out of scope.
- Do not retire a worktree merely because it is old, inconvenient, or unmerged.

## Current state
- `config/bologna_owner_answer_intake.yaml` records exactly one review-only
  `ODP-BOL-001` answer and keeps `ODP-BOL-002` through `ODP-BOL-004` missing.
- `state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 authority boundary; this
  pass cannot move any blocked or validate-only gate to ready.
- `scripts/bologna_odp1_owner_response_gate_check.py`,
  `scripts/bologna_odp2_source_rights_response_gate_check.py`,
  `scripts/bologna_odp3_corpus_response_gate_check.py`,
  `scripts/bologna_odp4_db_report_proof_response_gate_check.py`,
  `scripts/bol_scope_auth_check.py`, and
  `scripts/bologna_owner_answer_intake_check.py` validate committed blocked state and
  structural contracts.
- Existing artifact tests check blocked-state invariants and selected failure cases, but
  they do not consistently exercise a complete synthetic
  `approve_with_cited_authority` answer through every Bologna gate.
- Live `origin/main` is `8b24cffc1f253c9237bce78c85cd05b99631e7cf`; PR #166 is open on
  `claude/harvest-readiness`, so its worktree is not Codex-owned to retire.

## Proposed design
Add one side-effect-free owner-answer evaluator helper under `scripts/` and expose
small per-checker wrapper functions from the six Bologna checker scripts. The wrappers
accept in-memory synthetic answers and companion authority/proof payloads, return a
structured accepted/rejected result, and do not read or write production authority
state beyond the already-loaded checker inputs.

Rejected alternatives:
- Mutating YAML in temp copies to simulate authority. Rejected because it proves file
  mutation paths rather than the pure gate-decision logic and risks confusing
  validate-only semantics.
- Adding more response-acceptance prose checks. Rejected because non-empty prose is
  already covered; the missing proof is executable acceptance/rejection logic.
- Removing any unmerged worktree during this pass. Rejected because branch preservation
  alone is not enough when the worktree may be active, dirty, or not superseded.

## Bottom-up sequence
1. Add a reusable pure evaluator for owner-answer records, prerequisite coverage,
   decision coverage, companion record field coverage, and no-downstream-unlock policy.
2. Add per-checker evaluator wrappers for `ODP-BOL-001` through `ODP-BOL-004`,
   `bol_scope_auth`, and owner-answer intake.
3. Add selftests to `scripts/selftest_qualification_validator.py` that prove complete
   synthetic inputs are accepted and malformed, partial, downstream-unlock, and
   dependency-violating inputs are rejected.
4. Add focused pytest coverage for the six wrapper surfaces.
5. Record live worktree branch classification in
   `state/worktree-reconciliation-2026-06-28.md`; retire only worktrees proven clean,
   merged, superseded, and not owner-excluded.
6. Update routing/state/worklog/validation only to reflect the validation layer.

## Files likely to change
| File | Expected change |
|---|---|
| `scripts/bologna_owner_answer_evaluator.py` | New pure evaluator helper. |
| `scripts/bologna_*_check.py`, `scripts/bol_scope_auth_check.py` | Add in-memory evaluator wrappers. |
| `scripts/selftest_qualification_validator.py` | Add ODGAV accept/reject selftests run by verify. |
| `backend/tests/test_bologna_owner_answer_gate_evaluation.py` | Focused wrapper tests. |
| `state/worktree-reconciliation-2026-06-28.md` | Live classification report. |
| `state/LEVEL_9_10_GATE_MATRIX.md` | Referenced authority boundary; no gate status change. |
| `plans/README.md`, `tasks/task_queue.yaml`, `state/PROJECT_STATE.md` | Routing updates. |
| `state/WORKLOG.md`, `state/VALIDATION_LOG.md` | Implementation and check records. |

## Tests / verification
Expected focused checks:

```powershell
py -3.12 scripts\selftest_qualification_validator.py
$env:PYTHONPATH='backend'; py -3.12 -m pytest backend\tests\test_bologna_owner_answer_gate_evaluation.py -q
py -3.12 scripts\bologna_owner_answer_intake_check.py
py -3.12 scripts\bol_scope_auth_check.py
py -3.12 scripts\bologna_odp1_owner_response_gate_check.py
py -3.12 scripts\bologna_odp2_source_rights_response_gate_check.py
py -3.12 scripts\bologna_odp3_corpus_response_gate_check.py
py -3.12 scripts\bologna_odp4_db_report_proof_response_gate_check.py
py -3.12 scripts\validate_qualification.py --root . --layout repo
py -3.12 scripts\qualification_status_check.py --root . --python-command <python>
py -3.12 scripts\qualification_parameterization_backlog_check.py --root .
```

Final gate:

```powershell
.\scripts\verify.ps1
```

Expected signal: all checks pass, synthetic complete inputs are accepted in memory,
malformed/partial/dependency-violating inputs are rejected, committed authority records
remain empty, P0 remains `BLOCKED`, and no worktree is retired unless live evidence
meets the safe-retirement rule.

## Risks and blockers
- The handoff body was overwritten by a shorter pickup note. The recovered transcript
  and workflow result support M1/M2 scope, but absent detailed EXCLUDE text requires
  conservative reconciliation.
- PR #166 is still open and Claude-owned; do not remove its worktree or touch its owned
  backend/app/UI/OpenAPI surface.
- The substantive Bologna path remains blocked on cited external owner authority for
  `ODP-BOL-001` first.

## Decision log
- 2026-06-28: Chose a pure evaluator plus wrapper functions because it tests the future
  acceptance path without recording real authority or modifying committed config.
- 2026-06-28: Chose classification-only worktree reconciliation unless live proof shows
  a clean, merged, superseded, non-excluded worktree.

## Progress log
- 2026-06-28: Reconciled live main/worktree state; found root at `8b24cffc`, only the
  inbox file dirty in root, many repo-local worktrees, and PR #166 still open.
