# Bologna ODP-BOL-003 Corpus Response Gate

## Goal
Close the completed `BOL-ODP2-GATE` implementation lane and add a validate-only
`ODP-BOL-003` recorded-source corpus response gate. The gate makes the future corpus
owner-response shape executable while preserving the missing `ODP-BOL-001` and
`ODP-BOL-002` prerequisites and all downstream fixture, DB, report, hosted, and
qualification blockers.

## Non-goals
- Do not record owner answers, corpus authority, source-authority records, source-rights
  approvals, source registry promotion, AOI selection, recorded corpus approval,
  fixture capture, source-failure fixture capture, DB seed, runtime/report artifacts,
  DS-017 approval, hosted authority, qualification `PASS`, or Level 10 claims.
- Do not touch backend runtime, API, report semantics, DB schema, source registry rows,
  source readiness, or report-run schemas.
- Do not unblock `BSA-001`, `ODP-BOL-004`, or DB-backed Bologna report proof.

## Current state
- Live `origin/main` is `fa0f67aedff19ec31981ba1dacaa5315f843f021`, the PR #155
  merge commit for the `ODP-BOL-002` source-rights response gate.
- `config/bologna_owner_answer_intake.yaml` defines `ODP-BOL-003` as the Bologna
  recorded-source corpus thread, with `ODP-BOL-001` and `ODP-BOL-002` listed as
  prerequisites, empty owner-answer references, and downstream updates disabled.
- `config/bologna_recorded_source_corpus.yaml` keeps corpus approval, fixture capture,
  source-failure fixture capture, runtime/report use, and DB seed disabled while
  defining the future required corpus decisions, manifest fields, candidate corpus
  reviews, cadastral gap, and unlock conditions.
- `config/bologna_odp2_source_rights_response_gate.yaml` keeps `ODP-BOL-001` and
  `ODP-BOL-002` unrecorded and keeps every source-rights downstream update disabled.
- `state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 authority context; this gate
  does not change hosted, production, qualification, source, release, or maturity
  blocker statuses.
- Baseline focused checks passed: the ODP2 gate, owner-answer intake, recorded-source
  corpus, qualification status (`BLOCKED=1 NOT_RUN=20`), and focused Bologna/routing
  tests.

## Proposed design
Add `config/bologna_odp3_corpus_response_gate.yaml` plus a validate-only checker,
wrappers, runbook, tests, crosswalk mapping, and routing updates. The gate is narrower
than the existing recorded-source corpus contract:

- It targets only `ODP-BOL-003`.
- It records that `ODP-BOL-001` and `ODP-BOL-002` remain missing prerequisites.
- It cross-checks required owner-answer fields from the owner-answer intake.
- It cross-checks required corpus decisions, manifest fields, candidate review IDs,
  candidate manifest evidence, and cadastral-gap evidence from the recorded-source
  corpus contract.
- It explains the consequences of approve / keep-blocked / review-only / defer
  outcomes while keeping every downstream update disabled.

Talmudic coherence check:
- Position A, proceed directly to a recorded-source corpus because the user prioritized
  Bologna: rejected because no cited product/AOI authority, per-source rights authority,
  or corpus authority exists.
- Position B, stop repo-local progress until ODP-BOL-001 and ODP-BOL-002 are answered:
  rejected because an ODP3 response gate can clarify the next owner-driven corpus
  decision without fabricating authority.
- Position C, close `BOL-ODP2-GATE` and route to a validate-only ODP3 corpus response
  gate that remains blocked behind ODP-BOL-001 and ODP-BOL-002. Choose C because it
  advances the prioritized recorded-source path while preserving evidence-ledger and
  owner-authority boundaries.

## Bottom-up sequence
1. Add the ODP-BOL-003 corpus response gate config, checker, wrappers, and runbook.
2. Add focused artifact tests proving the gate aligns with the owner-answer intake,
   ODP2 gate, and recorded-source corpus contract.
3. Map the checker into the qualification readiness crosswalk.
4. Route `BOL-ODP2-GATE` to done and `BOL-ODP3-GATE` to active.
5. Run focused Bologna, qualification, lint/type, diff, and full verification gates.

## Files likely to change
| File | Expected change |
|---|---|
| `config/bologna_odp3_corpus_response_gate.yaml` | New validate-only ODP-BOL-003 gate. |
| `scripts/bologna_odp3_corpus_response_gate_check.py` | New checker. |
| `scripts/run_bologna_odp3_corpus_response_gate_check.ps1` | Windows wrapper. |
| `scripts/run_bologna_odp3_corpus_response_gate_check.sh` | POSIX wrapper. |
| `docs/runbooks/bologna_odp3_corpus_response_gate.md` | Operator runbook. |
| `backend/tests/test_bologna_odp3_corpus_response_gate_artifacts.py` | Focused artifact tests. |
| `config/qualification/readiness_crosswalk.yaml` | Map the checker to qualification criteria. |
| `docs/qualification/readiness-crosswalk.md` | Human crosswalk row. |
| `MANIFEST.md` | Routing index entry. |
| `tasks/task_queue.yaml` | Route BOL-ODP2-GATE done and BOL-ODP3-GATE active. |
| `plans/README.md` | Plan index update. |
| `state/PROJECT_STATE.md` | Current checkpoint update. |
| `state/QUALIFICATION_PARAMETERIZATION_BACKLOG.md` | Backlog pointer update. |
| `state/WORKLOG.md` | Execution notes. |
| `state/VALIDATION_LOG.md` | Validation evidence. |

## Tests / verification
- `py -3.12 scripts\bologna_odp3_corpus_response_gate_check.py`
- `.\scripts\run_bologna_odp3_corpus_response_gate_check.ps1`
- `py -3.12 scripts\bologna_odp2_source_rights_response_gate_check.py`
- `py -3.12 scripts\bologna_owner_answer_intake_check.py`
- `py -3.12 scripts\bologna_recorded_source_corpus_check.py`
- `cd backend; py -3.12 -m pytest -q tests\test_bologna_odp3_corpus_response_gate_artifacts.py tests\test_bologna_odp2_source_rights_response_gate_artifacts.py tests\test_bologna_owner_answer_intake_artifacts.py tests\test_bologna_recorded_source_corpus_artifacts.py tests\test_qualification_parameterization_backlog_artifacts.py tests\test_readiness_core_artifacts.py`
- `py -3.12 scripts\validate_qualification.py --root . --layout repo`
- `py -3.12 scripts\qualification_status_check.py --root .`
- `py -3.12 scripts\readiness_matrix_check.py`
- `py -3.12 scripts\selftest_qualification_validator.py`
- Focused ruff/mypy on touched checker/tests.
- `git diff --check`
- `git diff --name-only --diff-filter=D`
- `.\scripts\verify.ps1`

## Risks and blockers
- The artifact must not be mistaken for corpus approval. It keeps owner-answer, corpus,
  source authority, source rights, fixture, source-failure fixture, DB, report, hosted,
  and Level 10 updates disabled.
- A valid `ODP-BOL-003` answer still depends on cited `ODP-BOL-001` and
  `ODP-BOL-002` authority first.
- Bologna remains blocked until real cited owner/source-rights/corpus authority is
  recorded in later slices.

## Decision log
- 2026-06-23: Close completed BOL-ODP2-GATE routing and add a validate-only
  `ODP-BOL-003` recorded-source corpus response gate as the next Bologna-first step.

## Progress log
- 2026-06-23: Created `worktrees/bol-odp3` from live
  `origin/main@fa0f67aedff19ec31981ba1dacaa5315f843f021`, read routing/Bologna
  artifacts, confirmed focused baseline checks pass, and drafted this plan.
- 2026-06-23: Added the ODP-BOL-003 config, checker, wrappers, runbook, focused tests,
  crosswalk mapping, manifest entry, routing updates, and state/backlog references while
  keeping owner answers, corpus authority, recorded corpus references, fixtures, DB,
  report proof, hosted authority, and Level 10 authority disabled.
- 2026-06-23: Focused Bologna validators/tests, qualification validation/status,
  readiness matrix check, checker advertisement, focused ruff/mypy, explicit
  change-impact with untracked paths, and qualification selftest passed before final
  full verification.
