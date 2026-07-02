# Bologna Owner Answer Intake

## Goal
Advance the prioritized Bologna recorded-source path by adding a validate-only,
machine-checkable owner-answer intake for `ODP-BOL-001` through `ODP-BOL-004`. The
intake must make future owner answers executable while preserving the rule that no
source/AOI/corpus/report authority exists until cited evidence is supplied.

## Non-goals
- Do not record owner authority, owner answers, AOI selection, source approval, source
  rights approval, corpus approval, fixture capture, DB seed, report artifact, runtime
  proof, DS-017 approval, hosted authority, qualification `PASS`, or Level 10 claim.
- Do not change report semantics, API behavior, DB schema, source registry rows, or
  source readiness.
- Do not make `BSA-001` unblocked.

## Current state
- Live `origin/main` is `a6f5ac7a1accbce67dfbeadc02bd10cd6514085a`, the PR #152
  merge commit for OWNER-DEC-1.
- `state/owner-decision-packet.md` maps the owner-facing consequences for
  `ODP-BOL-001` through `ODP-BOL-004`, but it is prose-oriented and non-authorizing.
- `config/bologna_pilot_scope_authority.yaml`,
  `config/bologna_source_authority_intake.yaml`, `config/bologna_source_rights.yaml`,
  and `config/bologna_recorded_source_corpus.yaml` already validate future authority
  shapes and keep downstream updates blocked.
- `state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 authority context; this
  owner-answer intake does not change hosted, production, qualification, source, or
  release blocker statuses.
- Baseline Bologna validators pass; qualification status remains `BLOCKED=1
  NOT_RUN=20`.
- `state/PROJECT_STATE.md` and routing still describe OWNER-DEC-1 as active and cite
  the pre-PR #152 live SHA, so this pass also closes that routing loop.

## Proposed design
Add `config/bologna_owner_answer_intake.yaml` plus a validate-only checker and wrappers.
The config becomes the machine-readable bridge from the owner decision packet to the
existing Bologna authority packets:

- `ODP-BOL-001` aligns to required pilot-scope decisions.
- `ODP-BOL-002` aligns to source-rights decisions and current candidate/cadastral rows.
- `ODP-BOL-003` aligns to recorded-corpus decisions and manifest fields.
- `ODP-BOL-004` defines the DB-backed report proof fields that must be decided before
  any report artifact is claimed.

Talmudic coherence check:
- Position A, fill authority records now: rejected because owner evidence is absent.
- Position B, keep only the prose packet: accurate but too weak for future validation.
- Position C, add a validate-only answer intake that cross-checks the existing Bologna
  contracts and keeps all unlocks false. Choose C because it converts owner answers
  into a testable future input without fabricating them.

## Bottom-up sequence
1. Add artifact tests for the new owner-answer intake.
2. Add config, checker, wrappers, and runbook.
3. Map the checker into the qualification readiness crosswalk.
4. Route OWNER-DEC-1 to done and BOL-ODP-1 to active.
5. Run focused Bologna, qualification, lint/type, diff, and full verification gates.

## Files likely to change
| File | Expected change |
|---|---|
| `config/bologna_owner_answer_intake.yaml` | New validate-only owner-answer intake. |
| `scripts/bologna_owner_answer_intake_check.py` | New checker. |
| `scripts/run_bologna_owner_answer_intake_check.ps1` | Windows wrapper. |
| `scripts/run_bologna_owner_answer_intake_check.sh` | POSIX wrapper. |
| `docs/runbooks/bologna_owner_answer_intake.md` | Operator runbook. |
| `config/qualification/readiness_crosswalk.yaml` | Map the new checker to qualification criteria. |
| `backend/tests/test_bologna_owner_answer_intake_artifacts.py` | Focused artifact tests. |
| `backend/tests/test_qualification_parameterization_backlog_artifacts.py` | Routing assertions. |
| `backend/tests/test_readiness_core_artifacts.py` | Current active task/plan assertions. |
| `MANIFEST.md` | Routing index entry. |
| `tasks/task_queue.yaml` | Route OWNER-DEC-1 done and BOL-ODP-1 active. |
| `plans/README.md` | Plan index update. |
| `state/PROJECT_STATE.md` | Current checkpoint update. |
| `state/WORKLOG.md` | Execution notes. |
| `state/VALIDATION_LOG.md` | Validation evidence. |

## Tests / verification
- `py -3.12 scripts\bologna_owner_answer_intake_check.py`
- `.\scripts\run_bologna_owner_answer_intake_check.ps1`
- `py -3.12 scripts\bologna_pilot_scope_authority_check.py`
- `py -3.12 scripts\bologna_source_authority_intake_check.py`
- `py -3.12 scripts\bologna_source_rights_check.py`
- `py -3.12 scripts\bologna_recorded_source_corpus_check.py`
- `cd backend; py -3.12 -m pytest -q tests\test_bologna_owner_answer_intake_artifacts.py tests\test_bologna_pilot_scope_authority_artifacts.py tests\test_bologna_source_authority_intake_artifacts.py tests\test_bologna_source_rights_artifacts.py tests\test_bologna_recorded_source_corpus_artifacts.py tests\test_qualification_parameterization_backlog_artifacts.py tests\test_readiness_core_artifacts.py`
- `py -3.12 scripts\validate_qualification.py --root . --now 2026-06-23T12:00:00Z`
- `py -3.12 scripts\qualification_status_check.py --root .`
- `py -3.12 scripts\selftest_qualification_validator.py`
- `py -3.12 scripts\readiness_matrix_check.py`
- Focused ruff/mypy on touched checker/tests.
- `git diff --check`
- `git diff --name-only --diff-filter=D`
- `.\scripts\verify.ps1`

## Risks and blockers
- The intake must not be confused with authority. `current_owner_answers` remains empty
  and downstream unlocks stay false.
- ODP-BOL-004 report-proof fields are a pre-authority proof contract, not a report
  implementation or report semantics change.
- Bologna remains externally blocked until real owner/source/AOI evidence is cited.

## Decision log
- 2026-06-23: Add a validate-only owner-answer intake as the next Bologna-first slice
  after OWNER-DEC-1; keep all authority and runtime changes blocked.

## Progress log
- 2026-06-23: Created `worktrees/bol-owner` from live `origin/main@a6f5ac7`, read
  startup/routing/Bologna artifacts, confirmed baseline Bologna validators and focused
  tests pass, and drafted this plan.
