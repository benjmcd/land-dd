# Bologna Source Authority Record Contract

## Goal
Make the Bologna source-authority intake guard able to validate the shape of future
cited per-source authority records. The slice should define the source-authority record
contract, prove a complete hypothetical source record can be validated in memory, prove
partial or downstream-unlocking records fail closed, and keep the committed intake
packet blocked with no current source-authority records.

## Non-goals
- Do not approve product, AOI, source, source-rights, DS-017, hosted, or Level 10
  authority.
- Do not add any real source-authority record to the committed config.
- Do not move any `candidate_authority_reviews` row out of `missing_authority`.
- Do not change source-rights decisions from `pending_review`.
- Do not create a recorded-source corpus, fixture, source-failure fixture, source
  registry row, DB seed, runtime artifact, report artifact, rulepack, or source profile.
- Do not change public API, auth, DB schema, report semantics, connector behavior, or
  qualification status.

## Current state
- Live `origin/main` is `e511aa28fc265c8c1f2cdeb25cbce6553709a37c`, which merged PR
  #140 and made the pilot-scope authority checker validate complete future
  authority-record shapes while keeping `current_authority_records: []`.
- `config/bologna_source_authority_intake.yaml` remains `blocked_no_authority`. Every
  candidate row has `authority_state: missing_authority`, empty
  `authority_references`, and `decision_updates_allowed: false`.
- `config/bologna_source_rights.yaml` remains `repo_local_validate_only`; every
  candidate source has `decision_state: pending_external_review`, all rights decisions
  are `pending_review`, and promotion/runtime/report/export flags are false.
- The source-authority checker currently cross-checks candidate IDs, required evidence
  slots, cadastral gap evidence slots, promotion blockers, preflight references, and
  runbook boundary phrases. It does not yet define or validate a future per-source
  authority-record shape.
- `docs/ARCHITECTURE.md` and `docs/DATA_SOURCE_STRATEGY.md` require source-linked
  evidence, license/provenance metadata, fixture-first connector behavior, explicit
  source failures, source versions, caveats, and no live connector use before
  license/terms/reuse constraints are recorded.
- `docs/adr/0004-empirical-qualification-control-plane.md` requires owner/source/AOI
  authority and empirical evidence to remain blocked rather than inferred from repo-local
  preparation.
- `state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 authority context. This
  slice does not reinterpret hosted, DS-017, Bologna, source-rights, or production
  readiness gates.
- Focused baseline checks passed in `worktrees/bol-sa`: source-authority artifact
  pytest, source-authority checker, source-rights checker, recorded-source corpus
  checker, and pilot-scope authority checker.

## Proposed design
Add `source_authority_record_contract` to the source-authority intake config. The
contract should name required source-authority record fields, allowed authority types,
required rights-decision coverage, evidence-slot policy, decision-update policy, and
no-overclaim controls.

Extend `scripts/bologna_source_authority_intake_check.py` with source-authority record
helpers. A future record should pass only if it has exactly the required fields, links
to an upstream pilot-scope authority record, targets a known candidate source or the
cadastral gap, covers every source-rights decision ID, provides every required evidence
slot for that candidate, carries terms/version/retrieval/CRS/attribution/caveat/storage
and source-failure policy text, and requests no downstream unlocks. The committed
`current_source_authority_records` list remains empty.

Rejected alternative: jump to source-rights row decisions. That would require cited
product/AOI/source-review authority the repo does not have.

Rejected alternative: keep only prose evidence slots. Prose names what is missing, but
does not make future source-authority records fail closed when required fields,
candidate evidence slots, rights-decision coverage, or downstream unlock boundaries
drift.

## Bottom-up sequence
1. Add failing tests for source-authority record contract presence, complete in-memory
   candidate record acceptance, missing evidence-slot failure, and downstream-unlock
   failure.
2. Add the contract to `config/bologna_source_authority_intake.yaml` while keeping the
   committed record list empty.
3. Extend `scripts/bologna_source_authority_intake_check.py` to validate the contract
   and future record shapes without changing current approval state.
4. Update the source-authority runbook, active routing/state files, and routing tests
   to record `BSA-REC`.
5. Run focused Bologna checks/tests, qualification status/change-impact checks, diff
   hygiene, and full verification.
6. Review and merge only if no authority boundary is crossed.

## Files likely to change
| File | Expected change |
|---|---|
| `plans/2026-06-21-bologna-source-authority-record-contract.md` | New executable plan. |
| `config/bologna_source_authority_intake.yaml` | Add blocked source-authority record contract. |
| `scripts/bologna_source_authority_intake_check.py` | Validate the source-authority record contract and hypothetical records. |
| `docs/runbooks/bologna_source_authority_intake.md` | Document the record format and blocked boundary. |
| `backend/tests/test_bologna_source_authority_intake_artifacts.py` | Add fail-closed tests for complete, partial, and unlocking records. |
| `backend/tests/test_qualification_parameterization_backlog_artifacts.py` | Update active routing assertions. |
| `backend/tests/test_readiness_core_artifacts.py` | Update project-readiness active-plan/task assertions. |
| `tasks/task_queue.yaml` | Add routing for `BSA-REC`. |
| `plans/README.md` | Record this plan as the current authority-first slice. |
| `state/PROJECT_STATE.md` | Route current checkpoint to this source-authority record contract. |
| `state/WORKLOG.md` | Record progress and preserved blockers. |
| `state/VALIDATION_LOG.md` | Record validation evidence. |

## Tests / verification
```powershell
$env:PYTHONPATH='backend'; py -3.12 -m pytest backend\tests\test_bologna_source_authority_intake_artifacts.py -q
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

Expected signal: all checks pass; the checker validates a complete future
source-authority record shape in test isolation; missing candidate evidence slots and
downstream unlock requests fail closed; committed source-authority records remain empty;
BSA-001/source-rights/corpus/report work remains blocked; no tracked deletions; no
qualification `PASS`.

## Risks and blockers
- The main blocker remains the absence of real product/AOI/source-review authority.
  This slice proves the validation path for future source-authority evidence; it does
  not satisfy the authority blocker.
- The main risk is making a test-only source-authority record look like committed
  source approval. The committed config, runbook, state, and tests must keep
  `current_source_authority_records` empty and all downstream updates disabled.

## Decision log
- 2026-06-21: Choose a source-authority record contract as the next authority-first
  slice because it advances the source-rights authority step without changing any
  source-rights row or fabricating authority.

## Progress log
- 2026-06-21: Created `worktrees/bol-sa` from live
  `origin/main@e511aa28fc265c8c1f2cdeb25cbce6553709a37c` on branch
  `codex/bol-src-auth-contract`.
- 2026-06-21: Baseline focused source-authority artifact pytest, source-authority
  checker, source-rights checker, recorded-source corpus checker, and pilot-scope
  authority checker passed.
- 2026-06-21: Initial focused qualification status check failed because the active plan
  did not cite `state/LEVEL_9_10_GATE_MATRIX.md` or preserve explicit Level 9/10
  context; updated this plan before rerunning.
- 2026-06-21: Focused Bologna validators, qualification status/change-impact checks,
  focused artifact/routing pytest, diff hygiene, and tracked-deletion checks passed.
- 2026-06-21: Full `.\scripts\verify.ps1` passed; DB smoke was skipped because
  `RUN_DB_SMOKE` was not set.
