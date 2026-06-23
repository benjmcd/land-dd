# Bologna ODP-BOL-002 Source-Rights Response Gate

## Goal
Close the completed `BOL-ODP1-GATE` implementation lane and add a validate-only
`ODP-BOL-002` source-authority/source-rights response gate. The gate makes the next
Bologna owner-response shape executable while preserving the missing `ODP-BOL-001`
product/AOI prerequisite and all downstream blockers.

## Non-goals
- Do not record owner answers, source-authority records, source-rights approvals,
  source registry promotion, AOI selection, recorded corpus approval, fixture capture,
  DB seed, runtime/report artifacts, DS-017 approval, hosted authority, qualification
  `PASS`, or Level 10 claims.
- Do not touch backend runtime, API, report semantics, DB schema, source registry rows,
  source readiness, or report-run schemas.
- Do not unblock `BSA-001`, `ODP-BOL-003`, or `ODP-BOL-004`.

## Current state
- Live `origin/main` is `e1d3593a3c5d8c203a721ccde6dde2eb0658a862`, the PR #154
  merge commit for the `ODP-BOL-001` owner-response gate.
- `config/bologna_owner_answer_intake.yaml` defines `ODP-BOL-002` as the Bologna
  source authority and rights thread, with `ODP-BOL-001` listed as a prerequisite,
  empty owner-answer references, and downstream updates disabled.
- `config/bologna_source_authority_intake.yaml` keeps
  `current_source_authority_records` empty and provides the future cited
  source-authority record contract.
- `config/bologna_source_rights.yaml` keeps every candidate rights review pending,
  keeps the cadastral gap at direct source review required, and keeps all promotion,
  fixture, runtime, report, raw-export, and cadastral approvals false.
- `state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 authority context; this
  gate does not change hosted, production, qualification, source, release, or maturity
  blocker statuses.
- Baseline focused checks passed: the ODP1 gate, owner-answer intake,
  source-authority intake, source-rights, qualification status (`BLOCKED=1 NOT_RUN=20`),
  and focused Bologna/routing tests.

## Proposed design
Add `config/bologna_odp2_source_rights_response_gate.yaml` plus a validate-only
checker, wrappers, runbook, tests, crosswalk mapping, and routing updates. The gate is
narrower than the existing owner-answer intake and source-rights matrix:

- It targets only `ODP-BOL-002`.
- It records that `ODP-BOL-001` remains a missing prerequisite.
- It cross-checks required owner-answer fields from the owner-answer intake.
- It cross-checks source-authority record fields and candidate evidence slots from the
  source-authority intake.
- It cross-checks required rights decisions and candidate review IDs from the
  source-rights matrix, including the cadastral gap.
- It explains the consequences of approve / keep-blocked / review-only / defer
  outcomes while keeping every downstream update disabled.

Talmudic coherence check:
- Position A, proceed directly to source-rights approval because the user prioritized
  Bologna: rejected because no cited `ODP-BOL-001` product/AOI authority or
  `ODP-BOL-002` per-source rights authority exists.
- Position B, stop all repo-local progress until the owner answers `ODP-BOL-001`:
  rejected because a validate-only ODP2 response gate clarifies the next owner-driven
  decision without fabricating authority.
- Position C, close `BOL-ODP1-GATE` and route to a validate-only ODP2 gate that
  explicitly remains blocked behind `ODP-BOL-001`. Choose C because it advances the
  prioritized Bologna path while preserving evidence-ledger and owner-authority
  boundaries.

## Bottom-up sequence
1. Add the ODP-BOL-002 source-rights response gate config, checker, wrappers, and
   runbook.
2. Add focused artifact tests that prove the gate aligns with the owner-answer intake,
   source-authority intake, and source-rights matrix.
3. Map the checker into the qualification readiness crosswalk.
4. Route `BOL-ODP1-GATE` to done and `BOL-ODP2-GATE` to active.
5. Run focused Bologna, qualification, lint/type, diff, and full verification gates.

## Files likely to change
| File | Expected change |
|---|---|
| `config/bologna_odp2_source_rights_response_gate.yaml` | New validate-only ODP-BOL-002 gate. |
| `scripts/bologna_odp2_source_rights_response_gate_check.py` | New checker. |
| `scripts/run_bologna_odp2_source_rights_response_gate_check.ps1` | Windows wrapper. |
| `scripts/run_bologna_odp2_source_rights_response_gate_check.sh` | POSIX wrapper. |
| `docs/runbooks/bologna_odp2_source_rights_response_gate.md` | Operator runbook. |
| `backend/tests/test_bologna_odp2_source_rights_response_gate_artifacts.py` | Focused artifact tests. |
| `config/qualification/readiness_crosswalk.yaml` | Map the checker to qualification criteria. |
| `docs/qualification/readiness-crosswalk.md` | Human crosswalk row. |
| `MANIFEST.md` | Routing index entry. |
| `tasks/task_queue.yaml` | Route BOL-ODP1-GATE done and BOL-ODP2-GATE active. |
| `plans/README.md` | Plan index update. |
| `state/PROJECT_STATE.md` | Current checkpoint update. |
| `state/QUALIFICATION_PARAMETERIZATION_BACKLOG.md` | Backlog pointer update. |
| `state/WORKLOG.md` | Execution notes. |
| `state/VALIDATION_LOG.md` | Validation evidence. |

## Tests / verification
- `py -3.12 scripts\bologna_odp2_source_rights_response_gate_check.py`
- `.\scripts\run_bologna_odp2_source_rights_response_gate_check.ps1`
- `py -3.12 scripts\bologna_odp1_owner_response_gate_check.py`
- `py -3.12 scripts\bologna_owner_answer_intake_check.py`
- `py -3.12 scripts\bologna_source_authority_intake_check.py`
- `py -3.12 scripts\bologna_source_rights_check.py`
- `cd backend; py -3.12 -m pytest -q tests\test_bologna_odp2_source_rights_response_gate_artifacts.py tests\test_bologna_odp1_owner_response_gate_artifacts.py tests\test_bologna_owner_answer_intake_artifacts.py tests\test_bologna_source_authority_intake_artifacts.py tests\test_bologna_source_rights_artifacts.py tests\test_qualification_parameterization_backlog_artifacts.py tests\test_readiness_core_artifacts.py`
- `py -3.12 scripts\validate_qualification.py --root . --now 2026-06-23T12:00:00Z`
- `py -3.12 scripts\qualification_status_check.py --root .`
- `py -3.12 scripts\readiness_matrix_check.py`
- `py -3.12 scripts\selftest_qualification_validator.py`
- Focused ruff/mypy on touched checker/tests.
- `git diff --check`
- `git diff --name-only --diff-filter=D`
- `.\scripts\verify.ps1`

## Risks and blockers
- The artifact must not be mistaken for source-rights approval. It keeps owner-answer,
  source-authority, source-rights, corpus, fixture, DB, report, hosted, and Level 10
  updates disabled.
- A valid `ODP-BOL-002` answer still depends on cited `ODP-BOL-001` authority first.
- Bologna remains blocked until real cited owner/source-rights authority is recorded in
  later slices.

## Decision log
- 2026-06-23: Close completed BOL-ODP1-GATE routing and add a validate-only
  `ODP-BOL-002` source-authority/source-rights response gate as the next Bologna-first
  step.

## Progress log
- 2026-06-23: Created `worktrees/bol-odp2` from live
  `origin/main@e1d3593a3c5d8c203a721ccde6dde2eb0658a862`, read routing/Bologna
  artifacts, confirmed focused baseline checks pass, and drafted this plan.
- 2026-06-23: Added the validate-only ODP-BOL-002 source-rights response gate
  artifacts, crosswalk mapping, routing updates, and focused tests. Focused
  validators/tests, qualification validation/status, readiness-matrix checking, and
  qualification selftest passed after adding the required Level 9/10 matrix citation
  to this plan.
- 2026-06-23: Focused ruff/mypy, diff hygiene, no-deletion check, and final default
  `.\scripts\verify.ps1` passed. DB smoke was skipped by default.
