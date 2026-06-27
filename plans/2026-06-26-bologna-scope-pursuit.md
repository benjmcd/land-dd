# Bologna Scope Pursuit

## Goal
Record the owner directive "pursue Bologna scope" as an `ODP-BOL-001`
`approve_review_only` owner answer, while preserving the missing pilot-scope authority
boundary for exact AOI, source rights, corpus, fixture, DB, report, hosted, and Level 10
work.

## Non-goals
- Do not record a pilot-scope authority record.
- Do not select a Bologna AOI or boundary.
- Do not approve Bologna sources, source rights, DS-017, fixture capture, corpus work,
  source-failure fixtures, DB seed, connector/runtime/report proof, API/UI/report
  semantics, hosted authority, Level 10 status, or qualification `PASS`.
- Do not infer the 12 required ODP-BOL-001 scope decisions from the short owner
  directive.

## Current state
- Live `origin/main` is `828053d1b5e62845dc736551871e13f1ae89f0c4`.
- `config/bologna_owner_answer_intake.yaml` accepts a complete future owner-answer
  record shape in test isolation, but the committed `current_owner_answers` list is
  empty.
- `config/bologna_odp1_owner_response_gate.yaml` lists `approve_review_only` as an
  allowed outcome, but currently requires empty owner-answer references.
- `config/bologna_pilot_scope_authority.yaml` remains
  `blocked_no_pilot_scope_authority` with `current_authority_records: []`.
- `state/owner-decision-packet.md` says ODP-BOL-001 can approve product/AOI/scope,
  approve evidence-only scope, or keep the path blocked; it does not authorize anything
  by itself.
- `docs/ARCHITECTURE.md` and ADR 0002 require evidence-before-claim behavior; this
  slice touches only authority routing, not evidence, claims, DB, reports, or runtime.
- ADR 0004 requires owner decisions to remain blocked unless explicit authority exists;
  this slice records an owner answer but not full scope authority.
- `state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 authority context for this
  routing slice; this work introduces no hosted, release, or Level 10 completion claim.

## Proposed design
Record exactly one owner-answer row:

- `owner_answer_id`: `odp-bol-001-scope-pursuit-2026-06-26`
- `answer_type`: `approve_review_only`
- `authority_reference`: `owner directive 2026-06-26: pursue Bologna scope`

Update the ODP1 thread and response gate to reference that answer, set the answer
recording flag true, and keep every downstream update false. Leave
`config/bologna_pilot_scope_authority.yaml` unchanged except for tests proving it stays
blocked.

Alternative A, treating the directive as full `approve_with_cited_authority`, is
rejected because it does not provide the exact AOI, jurisdiction, DS-017 treatment,
fixture boundary, runtime boundary, or no-overclaim owner required for a complete
authority record. Alternative B, adding another owner-facing scaffold, is rejected
because the packet already exists. Alternative C, doing nothing, is rejected because
`approve_review_only` is an existing allowed outcome and the owner has now supplied a
directive to pursue Bologna scope.

## Bottom-up sequence
1. Update the owner-answer intake config/checker/tests to allow exactly the recorded
   review-only ODP1 answer while keeping ODP-BOL-002/003/004 missing.
2. Update the ODP1 response gate config/checker/tests to reference the answer while
   keeping pilot-scope authority records empty.
3. Update downstream ODP2/ODP3/ODP4 gates so they block on missing ODP1 authority
   rather than the now-stale idea that ODP1 has no owner answer.
4. Update runbooks, backlog/state/task routing, and plan index to distinguish
   review-only scope pursuit from full pilot-scope authority.
5. Run focused Bologna, backlog, readiness, qualification, change-impact, diff, and
   full verification gates.

## Files likely to change
| File | Expected change |
|---|---|
| `plans/2026-06-26-bologna-scope-pursuit.md` | New executable plan. |
| `config/bologna_owner_answer_intake.yaml` | Record one review-only ODP1 answer. |
| `scripts/bologna_owner_answer_intake_check.py` | Validate the recorded answer and references. |
| `docs/runbooks/bologna_owner_answer_intake.md` | Describe the recorded review-only answer boundary. |
| `backend/tests/test_bologna_owner_answer_intake_artifacts.py` | Cover the committed answer and fail-closed behavior. |
| `config/bologna_odp1_owner_response_gate.yaml` | Reference the recorded owner answer. |
| `scripts/bologna_odp1_owner_response_gate_check.py` | Allow the recorded answer while authority remains empty. |
| `docs/runbooks/bologna_odp1_owner_response_gate.md` | Describe review-only scope pursuit. |
| `backend/tests/test_bologna_odp1_owner_response_gate_artifacts.py` | Update response-gate expectations. |
| `state/PROJECT_STATE.md` | Route current state to this completed scope-pursuit boundary. |
| `state/QUALIFICATION_PARAMETERIZATION_BACKLOG.md` | Reflect that ODP1 has a review-only answer but not authority. |
| `state/LEVEL_9_10_GATE_MATRIX.md` | Referenced authority context only; no content change expected. |
| `config/bologna_odp2_source_rights_response_gate.yaml` | Block on missing ODP1 authority instead of missing ODP1 answer. |
| `config/bologna_odp3_corpus_response_gate.yaml` | Block on missing required authority. |
| `config/bologna_odp4_db_report_proof_response_gate.yaml` | Block on missing required authority. |
| `scripts/bologna_odp2_source_rights_response_gate_check.py` | Validate the review-only ODP1 answer as non-authorizing. |
| `scripts/bologna_odp3_corpus_response_gate_check.py` | Validate the review-only ODP1 answer as non-authorizing. |
| `scripts/bologna_odp4_db_report_proof_response_gate_check.py` | Validate the review-only ODP1 answer as non-authorizing. |
| `backend/tests/test_bologna_odp2_source_rights_response_gate_artifacts.py` | Update prerequisite expectations. |
| `backend/tests/test_bologna_odp3_corpus_response_gate_artifacts.py` | Update prerequisite expectations. |
| `backend/tests/test_bologna_odp4_db_report_proof_response_gate_artifacts.py` | Update prerequisite expectations. |
| `tasks/task_queue.yaml` | Add completed `BOL-SCOPE-PURSUIT`. |
| `MANIFEST.md` | Route the current review-only answer boundary accurately. |
| `plans/README.md` | Mark this as the latest completed plan. |
| `backend/tests/test_readiness_core_artifacts.py` | Update active-plan/completed-task assertions. |
| `backend/tests/test_qualification_parameterization_backlog_artifacts.py` | Update backlog/task expectations. |
| `state/WORKLOG.md` | Record execution. |
| `state/VALIDATION_LOG.md` | Record validation. |

## Tests / verification
```powershell
py -3.12 scripts\bologna_owner_answer_intake_check.py
py -3.12 scripts\bologna_odp1_owner_response_gate_check.py
py -3.12 scripts\bologna_pilot_scope_authority_check.py
py -3.12 scripts\bologna_odp1_owner_answer_packet_check.py
py -3.12 scripts\bologna_odp2_source_rights_response_gate_check.py
py -3.12 scripts\bologna_odp3_corpus_response_gate_check.py
py -3.12 scripts\bologna_odp4_db_report_proof_response_gate_check.py
py -3.12 scripts\qualification_parameterization_backlog_check.py --root .
py -3.12 scripts\readiness_matrix_check.py
$python = py -3.12 -c "import sys; print(sys.executable)"
& $python scripts\qualification_status_check.py --root . --python-command $python
py -3.12 scripts\validate_qualification.py --root . --layout repo
$env:PYTHONPATH='backend'; py -3.12 -m pytest -q backend\tests\test_bologna_owner_answer_intake_artifacts.py backend\tests\test_bologna_odp1_owner_response_gate_artifacts.py backend\tests\test_bologna_odp1_owner_answer_packet_artifacts.py backend\tests\test_bologna_odp2_source_rights_response_gate_artifacts.py backend\tests\test_bologna_odp3_corpus_response_gate_artifacts.py backend\tests\test_bologna_odp4_db_report_proof_response_gate_artifacts.py backend\tests\test_readiness_core_artifacts.py backend\tests\test_qualification_parameterization_backlog_artifacts.py
py -3.12 scripts\qualification_change_impact_check.py --root . --changed-path <changed path> [...]
git diff --check
git diff --name-only --diff-filter=D
.\scripts\verify.ps1
```

## Risks and blockers
- A review-only owner answer can be mistaken for full product/AOI/scope authority. The
  config, checkers, runbooks, and state must keep `current_authority_records: []` and
  downstream updates false.
- The directive does not name an exact AOI or boundary, so source/corpus/report work
  remains blocked after this slice.
- Any later full authority record must cover all 12 required ODP-BOL-001 scope
  decisions and request no downstream unlocks.

## Decision log
- 2026-06-26: Chose `approve_review_only` because the owner directive "pursue Bologna
  scope" is enough to record scope pursuit, but not enough to infer complete pilot
  authority.

## Progress log
- 2026-06-26: Created isolated `worktrees/bol-scope` worktree from live
  `origin/main`.
- 2026-06-26: Recorded the review-only ODP1 owner answer and updated downstream
  response gates to require missing authority, not a missing ODP1 answer.
