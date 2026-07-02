# Authority Evidence Intake Routing

## Goal
Route the project after PR #173 so the completed post-geology closeout is no
longer active and the current posture is explicit: the next substantive work
requires cited external authority evidence before any Bologna, DS-017, hosted,
Level 10, or empirical-qualification implementation can proceed.

## Non-goals
- Do not record a new owner answer, authority record, source approval, source-
  rights decision, recorded-source corpus, DB report proof, or source profile.
- Do not start `BSA-001`, ODP-BOL-002, ODP-BOL-003, ODP-BOL-004, DS-017,
  hosted deployment, identity/RBAC, billing, observability, image publication,
  Level 10, or empirical qualification execution without cited evidence.
- Do not add connectors, run live source calls, capture fixtures, seed the DB,
  change schema/API/auth/UI/report semantics, unfreeze owner decisions, claim
  qualification `PASS`, or unblock `P0`.

## Current state
PR #173 merged the post-geology routing closeout at
`1d7c722bd8c1b6ab2ca20458b4fd1e309dd014e3`. The owner-independent
extended-domain fixture-ingestion sequence is complete through minerals,
broadband, environmental hazard, water, and NCGS 1985 geologic map-unit context.

The remaining sequence is authority-dependent:

1. Product/AOI/scope authority for the Bologna pursuit.
2. Source authority and source-rights authority for ODP-BOL-002 / `BSA-001`.
3. Recorded-source corpus authority for ODP-BOL-003.
4. DB-backed report-proof authority for ODP-BOL-004.
5. Bologna rulepack/runtime/report implementation only after the above.
6. Separate DS-017, hosted, identity/RBAC, observability, billing, image
   publication, and Level 10 authority streams.
7. Empirical qualification `P0` only after targets, contracts, rubrics, domain
   profiles, source profiles, and required evidence are frozen/approved.

`state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 authority context. This
routing update does not change any gate status in that matrix.

## Proposed design
Make a routing-only update:

- mark `POST-GEOLOGY-ROUTING` done after PR #173;
- make `AUTH-EVIDENCE-INTAKE` the only active task;
- keep `BSA-001` and every downstream authority task blocked until cited
  evidence exists;
- keep qualification status at `P0 = BLOCKED`.

Follow-up guard under the same active posture:

- add a thin validate-only composition check that proves the active routing,
  production authority streams, Bologna ODP/source/corpus/report gates, empty
  authority records, and empirical qualification status agree as one blocked
  authority-evidence intake posture;
- run existing specialized validators instead of re-implementing source-rights,
  production-authority, owner-answer, corpus, report-proof, readiness, or
  qualification rules;
- wire that composition check into the canonical verifier so the posture fails
  closed if any required authority stream is omitted or promoted without cited
  authority.

Rejected alternatives:

- Start `BSA-001` now: rejected because complete cited product/AOI/source-review
  authority is still absent.
- Start another fixture-ingestion lane: rejected because the named owner-
  independent extended-domain fixture sequence is complete, and no authority file
  selects DS-020, DS-022, or another source as the next required lane.
- Treat the post-geology closeout itself as still active: rejected because PR
  #173 merged it and live routing should no longer point at completed branch work.

## Bottom-up sequence
1. Update plan, project state, plan index, and task queue routing.
2. Update backlog and readiness guardrails to expect `AUTH-EVIDENCE-INTAKE`.
3. Record validation evidence in worklog and validation log.
4. Run focused routing/authority checks, diff hygiene checks, and the full
   Windows verifier.

## Files likely to change
| File | Expected change |
|---|---|
| `plans/2026-07-02-authority-evidence-intake.md` | New authority-evidence routing plan. |
| `plans/README.md` | Mark post-geology routing complete and route here. |
| `state/PROJECT_STATE.md` | Record post-PR #173 authority-evidence checkpoint. |
| `tasks/task_queue.yaml` | Mark `POST-GEOLOGY-ROUTING` done and add active `AUTH-EVIDENCE-INTAKE`. |
| `scripts/qualification_parameterization_backlog_check.py` | Guard the authority-evidence routing boundary. |
| `scripts/authority_evidence_intake_check.py` | Compose existing authority validators and active routing into one fail-closed posture check. |
| `scripts/run_authority_evidence_intake_check.ps1` | Windows wrapper for the authority-evidence posture check. |
| `scripts/run_authority_evidence_intake_check.sh` | POSIX wrapper for the authority-evidence posture check. |
| `backend/tests/test_qualification_parameterization_backlog_artifacts.py` | Mirror backlog checker expectations. |
| `backend/tests/test_readiness_core_artifacts.py` | Mirror readiness model expectations. |
| `backend/tests/test_authority_evidence_intake_artifacts.py` | Prove the authority-evidence guard passes current artifacts and fails closed on omitted streams, downstream unlocks, or P0 promotion. |
| `state/WORKLOG.md` | Record sync work and validation. |
| `state/VALIDATION_LOG.md` | Record exact commands, results, and residual risk. |

## Tests / verification
```powershell
$env:PYTHONPATH='backend'; py -3.12 -m pytest backend\tests\test_readiness_core_artifacts.py backend\tests\test_qualification_parameterization_backlog_artifacts.py -q
py -3.12 scripts\qualification_parameterization_backlog_check.py --root .
py -3.12 scripts\bologna_pilot_scope_authority_check.py
py -3.12 scripts\bologna_source_authority_intake_check.py
py -3.12 scripts\bologna_source_rights_check.py
py -3.12 scripts\bologna_recorded_source_corpus_check.py
py -3.12 scripts\authority_evidence_intake_check.py
py -3.12 scripts\readiness_matrix_check.py
py -3.12 scripts\qualification_status_check.py --root .
$env:PYTHONPATH='backend'; py -3.12 -m pytest backend\tests\test_authority_evidence_intake_artifacts.py -q
git diff --check
git diff --name-only --diff-filter=D
.\scripts\verify.ps1
```

Pass/fail requirements:
- `POST-GEOLOGY-ROUTING` is done, not active.
- `AUTH-EVIDENCE-INTAKE` is the only active task and depends on
  `POST-GEOLOGY-ROUTING`.
- `BSA-001`, ODP-BOL-002, ODP-BOL-003, ODP-BOL-004, DS-017, hosted/Level 10,
  qualification `PASS`, owner-decision unfreeze, and `P0` remain blocked until
  cited authority evidence exists.
- `scripts\authority_evidence_intake_check.py` passes and fails closed if the
  active task drifts, a production authority stream is omitted, downstream
  Bologna updates are enabled, authority records are recorded, or `P0` is
  promoted.
- No new source approval, source-rights change, corpus, fixture capture, DB seed,
  report proof, runtime behavior, schema/API/auth/UI change, or production
  authority is introduced.

## Decision log
- 2026-07-02: Selected an authority-evidence intake posture after PR #173 because
  the owner-independent fixture sequence is complete and every remaining
  substantive milestone depends on cited external authority.
- 2026-07-02: Added a thin composition guard for the active posture because the
  existing authority validators were strong individually but did not expose one
  current-route check proving that all required authority streams are present,
  blocked, and wired into the canonical verification gate.
