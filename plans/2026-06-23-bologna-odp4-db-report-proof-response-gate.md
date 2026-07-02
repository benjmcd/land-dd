# Bologna ODP-BOL-004 DB Report Proof Response Gate

## Goal
Close the completed `BOL-ODP3-GATE` implementation lane and add a validate-only
`ODP-BOL-004` DB-backed Bologna report proof response gate. The gate makes the future
report-proof owner-response shape executable while preserving the missing
`ODP-BOL-001`, `ODP-BOL-002`, and `ODP-BOL-003` prerequisites and all downstream DB,
runtime, report-artifact, API, hosted, and qualification blockers.

## Non-goals
- Do not record owner answers, report-proof authority, corpus authority,
  source-authority records, source-rights approvals, recorded corpus approval, source
  registry promotion, AOI selection, fixture capture, source-failure fixture capture, DB
  seed, DB report run, runtime/report artifacts, API changes, report semantics changes,
  DS-017 approval, hosted authority, qualification `PASS`, or Level 10 claims.
- Do not touch backend runtime, API, report semantics, DB schema, source registry rows,
  source readiness, or report-run/evidence/claim schemas.
- Do not unblock `BSA-001`, recorded corpus work, or actual DB-backed Bologna report
  proof.

## Current state
- Live `origin/main` is `9d06cdeb79999c235b66c1589e972bfae5a55976`, the PR #156 merge
  commit for the `ODP-BOL-003` recorded-source corpus response gate.
- `config/bologna_owner_answer_intake.yaml` defines `ODP-BOL-004` as the DB-backed
  Bologna report proof thread, with `ODP-BOL-001`, `ODP-BOL-002`, and `ODP-BOL-003`
  listed as prerequisites, empty owner-answer references, and downstream updates
  disabled.
- `schemas/report_run_schema.json`, `schemas/evidence_schema.json`, and
  `schemas/claim_schema.json` define the report-run, evidence-row, and claim-link
  contract surfaces that a future DB-backed report proof must cite.
- `config/bologna_odp3_corpus_response_gate.yaml` keeps `ODP-BOL-001`,
  `ODP-BOL-002`, and `ODP-BOL-003` unrecorded and keeps every corpus/report downstream
  update disabled.
- `state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 authority context; this gate
  does not change hosted, production, qualification, source, release, or maturity
  blocker statuses.
- Baseline focused checks passed: the ODP3 gate, owner-answer intake, qualification
  status (`BLOCKED=1 NOT_RUN=20`), and focused Bologna/routing tests.

## Proposed design
Add `config/bologna_odp4_db_report_proof_response_gate.yaml` plus a validate-only
checker, wrappers, runbook, tests, crosswalk mapping, and routing updates. The gate is
narrower than an actual report proof:

- It targets only `ODP-BOL-004`.
- It records that `ODP-BOL-001`, `ODP-BOL-002`, and `ODP-BOL-003` remain missing
  prerequisites.
- It cross-checks required owner-answer fields and required report-proof fields from the
  owner-answer intake.
- It cross-checks report-run, evidence, and claim required fields from the committed JSON
  schemas.
- It explains approve / keep-blocked / review-only / defer outcomes while keeping every
  downstream update disabled.

Talmudic coherence check:
- Position A, build the actual DB-backed Bologna report proof now because the long-term
  goal names it: rejected because no cited product/AOI authority, per-source rights
  authority, or corpus authority exists.
- Position B, stop repo-local progress until ODP-BOL-001 through ODP-BOL-003 are
  answered: rejected because an ODP4 response gate can clarify the final owner-driven
  report-proof decision without fabricating authority.
- Position C, close `BOL-ODP3-GATE` and route to a validate-only ODP4 report-proof
  response gate that remains blocked behind ODP-BOL-001, ODP-BOL-002, and ODP-BOL-003.
  Choose C because it advances the DB-backed report-proof path while preserving
  evidence-ledger, source-rights, and owner-authority boundaries.

## Bottom-up sequence
1. Add the ODP-BOL-004 DB report proof response gate config, checker, wrappers, and
   runbook.
2. Add focused artifact tests proving the gate aligns with the owner-answer intake, ODP3
   gate, and report/evidence/claim schemas.
3. Map the checker into the qualification readiness crosswalk.
4. Route `BOL-ODP3-GATE` to done and `BOL-ODP4-GATE` to active.
5. Run focused Bologna, qualification, lint/type, diff, and full verification gates.

## Files likely to change
| File | Expected change |
|---|---|
| `config/bologna_odp4_db_report_proof_response_gate.yaml` | New validate-only ODP-BOL-004 gate. |
| `scripts/bologna_odp4_db_report_proof_response_gate_check.py` | New checker. |
| `scripts/run_bologna_odp4_db_report_proof_response_gate_check.ps1` | Windows wrapper. |
| `scripts/run_bologna_odp4_db_report_proof_response_gate_check.sh` | POSIX wrapper. |
| `docs/runbooks/bologna_odp4_db_report_proof_response_gate.md` | Operator runbook. |
| `backend/tests/test_bologna_odp4_db_report_proof_response_gate_artifacts.py` | Focused artifact tests. |
| `config/qualification/readiness_crosswalk.yaml` | Map the checker to qualification criteria. |
| `docs/qualification/readiness-crosswalk.md` | Human crosswalk row. |
| `MANIFEST.md` | Routing index entry. |
| `tasks/task_queue.yaml` | Route BOL-ODP3-GATE done and BOL-ODP4-GATE active. |
| `plans/README.md` | Plan index update. |
| `state/PROJECT_STATE.md` | Current checkpoint update. |
| `state/QUALIFICATION_PARAMETERIZATION_BACKLOG.md` | Backlog pointer update. |
| `state/WORKLOG.md` | Execution notes. |
| `state/VALIDATION_LOG.md` | Validation evidence. |

## Tests / verification
- `py -3.12 scripts\bologna_odp4_db_report_proof_response_gate_check.py`
- `.\scripts\run_bologna_odp4_db_report_proof_response_gate_check.ps1`
- `py -3.12 scripts\bologna_odp3_corpus_response_gate_check.py`
- `py -3.12 scripts\bologna_owner_answer_intake_check.py`
- `py -3.12 scripts\qualification_status_check.py --root .`
- `cd backend; py -3.12 -m pytest -q tests\test_bologna_odp4_db_report_proof_response_gate_artifacts.py tests\test_bologna_odp3_corpus_response_gate_artifacts.py tests\test_bologna_owner_answer_intake_artifacts.py tests\test_qualification_parameterization_backlog_artifacts.py tests\test_readiness_core_artifacts.py`
- `py -3.12 scripts\validate_qualification.py`
- `py -3.12 scripts\readiness_matrix_check.py`
- `py -3.12 scripts\qualification_checker_advertisement.py --checker scripts\bologna_odp4_db_report_proof_response_gate_check.py`
- `py -3.12 scripts\qualification_change_impact_check.py --changed-path <changed path> [...]`
- `py -3.12 scripts\selftest_qualification_validator.py`
- Focused ruff/mypy on touched checker/tests.
- `git diff --check`
- `git diff --name-only --diff-filter=D`
- `.\scripts\verify.ps1`

## Risks and blockers
- The artifact must not be mistaken for a DB report proof. It keeps owner-answer,
  report-proof authority, DB seed, DB report run, report artifacts, API, hosted, and
  Level 10 updates disabled.
- A valid `ODP-BOL-004` answer still depends on cited `ODP-BOL-001`,
  `ODP-BOL-002`, and `ODP-BOL-003` authority first.
- Bologna remains blocked until real cited owner/source-rights/corpus/report-proof
  authority is recorded in later slices.

## Decision log
- 2026-06-23: Close completed BOL-ODP3-GATE routing and add a validate-only
  `ODP-BOL-004` DB-backed report proof response gate as the next Bologna-first step.

## Progress log
- 2026-06-23: Created `worktrees/bol-odp4` from live
  `origin/main@9d06cdeb79999c235b66c1589e972bfae5a55976`, read routing/Bologna/report
  artifacts, confirmed focused baseline checks pass, and drafted this plan.
- 2026-06-23: Added the ODP-BOL-004 config, checker, wrappers, runbook, focused tests,
  crosswalk mapping, manifest entry, routing updates, and state/backlog references while
  keeping owner answers, report-proof authority, DB report runs, report artifacts, DB
  seed, API/report changes, hosted authority, and Level 10 authority disabled.
- 2026-06-23: Initial ODP4 crosswalk mapping included caveat/artifact criteria
  `Q1-018` and `Q2-020`; `qualification_status_check` correctly rejected the resulting
  overlay-status drift. The mapping was narrowed to authority/report-lineage criteria
  while preserving caveat/artifact requirements inside the ODP4 gate contract itself.
- 2026-06-23: Focused Bologna validators/tests, qualification validation/status,
  readiness matrix check, checker advertisement, focused ruff/mypy, explicit
  change-impact with untracked paths, and qualification selftest passed before final
  full verification.
