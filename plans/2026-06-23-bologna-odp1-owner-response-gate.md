# Bologna ODP-BOL-001 Owner Response Gate

## Goal
Close the completed `BOL-ODP-1` implementation lane and add a validate-only
`ODP-BOL-001` owner-response gate that makes the next required Bologna
product/AOI/scope owner answer executable without recording authority.

## Non-goals
- Do not record owner answers, pilot-scope authority records, AOI selection, source
  approval, source-rights changes, corpus approval, fixture capture, DB seed,
  runtime/report artifacts, DS-017 approval, hosted authority, qualification `PASS`, or
  Level 10 claims.
- Do not touch backend runtime, API, report semantics, DB schema, source registry rows,
  source readiness, or report-run schemas.
- Do not make `BSA-001` unblocked.

## Current state
- Live `origin/main` is `f2c815028e5a17044079de492f254546cacedfeb`, the PR #153 merge
  commit for the Bologna owner-answer intake.
- `config/bologna_owner_answer_intake.yaml` now defines a complete validate-only
  owner-answer shape for `ODP-BOL-001` through `ODP-BOL-004`.
- `config/bologna_pilot_scope_authority.yaml` still has no authority records and keeps
  every scope decision at `missing_authority`.
- `state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 authority context; this
  gate does not change hosted, production, qualification, source, release, or maturity
  blocker statuses.
- `state/PROJECT_STATE.md`, `tasks/task_queue.yaml`, and tests still route
  `BOL-ODP-1` as active because that was the just-completed implementation lane.
- Baseline focused checks passed: owner-answer intake checker, pilot-scope checker,
  qualification status (`BLOCKED=1 NOT_RUN=20`), and focused Bologna/routing tests.

## Proposed design
Add `config/bologna_odp1_owner_response_gate.yaml` plus a validate-only checker,
wrappers, runbook, tests, and crosswalk mapping. The gate is narrower than the existing
owner-answer intake:

- It targets only `ODP-BOL-001`.
- It cross-checks the required owner-answer fields from the owner-answer intake.
- It cross-checks the required scope decisions and authority-record fields from the
  pilot-scope authority packet.
- It records the owner-facing consequences of approve / keep-blocked / review-only /
  defer outcomes while keeping every downstream update disabled.

Talmudic coherence check:
- Position A, mark `ODP-BOL-001` answered from the existing handoff context: rejected
  because no cited owner answer exists in the live repo.
- Position B, leave BOL-ODP-1 active until external owner authority arrives: rejected
  because the implementation lane is complete and should not obscure the real blocker.
- Position C, close BOL-ODP-1 and route to a validate-only owner-response gate for
  `ODP-BOL-001`. Choose C because it moves the next external decision into a checked
  artifact without fabricating authority.

## Bottom-up sequence
1. Add the ODP-BOL-001 owner-response gate config, checker, wrappers, and runbook.
2. Add focused artifact tests that prove the gate aligns with the owner-answer intake
   and pilot-scope authority packet.
3. Map the checker into the qualification readiness crosswalk.
4. Route `BOL-ODP-1` to done and `BOL-ODP1-GATE` to active.
5. Run focused Bologna, qualification, lint/type, diff, and full verification gates.

## Files likely to change
| File | Expected change |
|---|---|
| `config/bologna_odp1_owner_response_gate.yaml` | New validate-only ODP-BOL-001 gate. |
| `scripts/bologna_odp1_owner_response_gate_check.py` | New checker. |
| `scripts/run_bologna_odp1_owner_response_gate_check.ps1` | Windows wrapper. |
| `scripts/run_bologna_odp1_owner_response_gate_check.sh` | POSIX wrapper. |
| `docs/runbooks/bologna_odp1_owner_response_gate.md` | Operator runbook. |
| `backend/tests/test_bologna_odp1_owner_response_gate_artifacts.py` | Focused artifact tests. |
| `config/qualification/readiness_crosswalk.yaml` | Map the checker to qualification criteria. |
| `docs/qualification/readiness-crosswalk.md` | Human crosswalk row. |
| `MANIFEST.md` | Routing index entry. |
| `tasks/task_queue.yaml` | Route BOL-ODP-1 done and BOL-ODP1-GATE active. |
| `plans/README.md` | Plan index update. |
| `state/PROJECT_STATE.md` | Current checkpoint update. |
| `state/WORKLOG.md` | Execution notes. |
| `state/VALIDATION_LOG.md` | Validation evidence. |

## Tests / verification
- `py -3.12 scripts\bologna_odp1_owner_response_gate_check.py`
- `.\scripts\run_bologna_odp1_owner_response_gate_check.ps1`
- `py -3.12 scripts\bologna_owner_answer_intake_check.py`
- `py -3.12 scripts\bologna_pilot_scope_authority_check.py`
- `cd backend; py -3.12 -m pytest -q tests\test_bologna_odp1_owner_response_gate_artifacts.py tests\test_bologna_owner_answer_intake_artifacts.py tests\test_bologna_pilot_scope_authority_artifacts.py tests\test_qualification_parameterization_backlog_artifacts.py tests\test_readiness_core_artifacts.py`
- `py -3.12 scripts\validate_qualification.py --root . --now 2026-06-23T12:00:00Z`
- `py -3.12 scripts\qualification_status_check.py --root .`
- `py -3.12 scripts\readiness_matrix_check.py`
- `py -3.12 scripts\selftest_qualification_validator.py`
- Focused ruff/mypy on touched checker/tests.
- `git diff --check`
- `git diff --name-only --diff-filter=D`
- `.\scripts\verify.ps1`

## Risks and blockers
- The artifact must not be mistaken for an owner response. It keeps owner answers and
  authority records empty and every downstream update disabled.
- A valid `ODP-BOL-001` answer still requires external owner authority and cited
  evidence. This slice only defines the checked response gate.
- Bologna remains blocked until a real cited owner answer is recorded in a later slice.

## Decision log
- 2026-06-23: Close completed BOL-ODP-1 routing and add a validate-only
  `ODP-BOL-001` owner-response gate as the next Bologna-first step.

## Progress log
- 2026-06-23: Created `worktrees/bol-odp1` from live
  `origin/main@f2c815028e5a17044079de492f254546cacedfeb`, read routing/Bologna
  artifacts, confirmed focused baseline checks pass, and drafted this plan.
- 2026-06-23: Added the validate-only ODP-BOL-001 owner-response gate artifacts,
  crosswalk mapping, routing updates, and focused tests. Focused validators/tests,
  qualification validation/status, readiness-matrix checking, ruff, mypy, and
  qualification selftest passed.
- 2026-06-23: Diff hygiene, no-deletion check, and final full `.\scripts\verify.ps1`
  passed. DB smoke was skipped by default.
