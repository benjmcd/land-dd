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
PR #174 then made `AUTH-EVIDENCE-INTAKE` the active routing posture, and PR #175
merged the validate-only composition guard for that posture at
`0bfc4f395587956c520866a05423531e23270e21`. PR #176 synchronized current-state
wording after that guard, PR #177 added optional reporting-only `--summary` and
`--json` output, PR #178 linked that output from operator runbooks, and PR #179
forwarded wrapper arguments so the same reporting modes work through the
Windows/POSIX entrypoints without corrupting structured output. PR #180
synchronized the live authority-evidence state after wrapper support, and PR #181
added a validate-only follow-on sequencing contract so the packet's repo-local
follow-on map is machine-checked without recording authority or unlocking
implementation. PR #182 added a validate-only production authority evidence reference
contract so future cited references have a checked field shape before any stream can
move out of blocked state. PR #183 added reporting-only `--summary` and `--json`
output to that reference contract so operators can collect the required fields without
generating artifacts or changing blocker state. PR #184 synchronized the live
authority-evidence state after that output support. PR #95 then completed the
GitHub Actions checkout v7 dependency-policy update and aligned the repo-owned
validate-only policy checkers, artifact tests, and security-scan runbook example to
`actions/checkout@v7`; this was CI hygiene only and did not change the active
authority-evidence posture or any downstream blocker. PR #185 synchronized state after
that checkout v7 closeout. PR #186 added side-effect-free synthetic submitted-
reference evaluation to the production authority evidence reference checker so future
cited-reference shapes can fail closed in memory before authority recording remains
blocked. This pass adds reporting-only `--summary` and `--json` output to the
immediate ODP-BOL-001 scope-authority readiness gate so the required owner-answer
fields, pilot-scope authority-record fields, scope decisions, downstream blocked gates,
and no-overclaim controls are visible without recording authority or unlocking work.

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

Reporting extension under the same active posture:

- add optional direct checker output modes that emit a human summary or JSON view
  of missing production authority streams, Bologna owner-answer threads, P0 status,
  and blocked implementation boundaries after the same validation passes;
- keep default checker and wrapper behavior unchanged so canonical verification
  remains a pass/fail guard;
- do not write files, seed runtime state, record authority, approve sources, change
  rights, or unlock any downstream implementation surface.

Follow-on sequencing contract under the same active posture:

- add a structured validate-only map from authority received to the first
  repo-local follow-on actions listed in `state/PRODUCTION_AUTHORITY_PACKET.md`;
- require every production authority stream to be covered by a blocked follow-on
  lane, while also preserving the packet-level production workload/retention lane
  that is not a standalone production-authority-intake stream;
- keep DS-017, Bologna owner/source/corpus/report gates, hosted readiness, Level
  10, qualification `PASS`, owner-decision unfreeze, and `P0` blocked until cited
  authority is present and the matching source catalog/checker is updated.

Production authority evidence reference contract under the same active posture:

- define the required field shape for future cited authority evidence references;
- mirror every `config/production_authority_intake.yaml` stream as a blocked
  reference template with the same source catalog and required evidence list;
- require current reference lists and downstream unlock requests to remain empty;
- keep the contract validate-only so it cannot supply authority, approve sources,
  change rights, trigger follow-on lanes, unfreeze qualification, claim Level 10, or
  unblock `P0`.

Reference-contract reporting extension under the same active posture:

- add optional direct checker output modes that emit the required reference fields,
  allowed artifact types, forbidden effects, and per-stream reference templates after
  the same validation passes;
- keep default checker and wrapper behavior unchanged so canonical verification
  remains a pass/fail guard;
- avoid output paths, file writes, generated reference artifacts, source approvals,
  rights changes, downstream unlock requests, or any authority-recording behavior.

ODP-BOL-001 scope-authority reporting extension under the same active posture:

- add optional direct checker output modes that emit the blocked ODP-BOL-001
  promotion-readiness requirements as a human summary or JSON view after the same
  validation passes;
- include the required owner-answer fields, required pilot-scope authority-record
  fields, required scope decisions, downstream ODP-BOL-002/003/004 blocked gates, and
  no-overclaim controls from existing config only;
- forward wrapper arguments without appending wrapper confirmation text to JSON output;
- avoid output paths, file writes, generated artifacts, owner-answer recording,
  pilot-scope authority recording, source approvals, source-rights changes, corpus or
  fixture capture, DB/report work, or any downstream unlock.

Authority-validator consolidation under the same active posture:

- extract shared fail-closed guard, path/YAML, summary, and reporting-CLI helpers into
  `scripts/authority_check_lib.py`;
- refactor the overlapping authority validator family to consume that helper instead
  of repeating local validate-only plumbing;
- add pilot-scope authority `--summary` and `--json` output through the shared helper
  so the committed missing-evidence request table, authority-record contract,
  downstream blocked targets, and no-overclaim controls are visible without recording
  authority;
- preserve existing frozen invariants: pilot/source authority records stay empty,
  downstream unlocks stay disabled, qualification `P0` stays `BLOCKED`, and all other
  qualification rows stay `NOT_RUN`.

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
| `scripts/authority_check_lib.py` | Shared fail-closed guard, path/YAML, summary, and reporting CLI helper for consolidated authority validators. |
| `scripts/authority_evidence_intake_check.py` | Compose existing authority validators and active routing into one fail-closed posture check. |
| `scripts/run_authority_evidence_intake_check.ps1` | Windows wrapper for the authority-evidence posture check. |
| `scripts/run_authority_evidence_intake_check.sh` | POSIX wrapper for the authority-evidence posture check. |
| `config/production_authority_evidence_references.yaml` | Validate-only evidence-reference contract for future cited authority references. |
| `scripts/production_authority_evidence_references_check.py` | Fail closed if reference fields, stream templates, evidence lists, or blocked boundaries drift; evaluates synthetic submitted-reference shapes in memory; optionally emits reporting-only summary/JSON. |
| `scripts/run_production_authority_evidence_references_check.ps1` | Windows wrapper for the evidence-reference contract check and reporting modes. |
| `scripts/run_production_authority_evidence_references_check.sh` | POSIX wrapper for the evidence-reference contract check and reporting modes. |
| `config/authority_follow_on_sequence.yaml` | Validate-only authority-dependent follow-on sequence contract. |
| `scripts/authority_follow_on_sequence_check.py` | Fail closed if the follow-on map, authority streams, or blocker boundaries drift. |
| `scripts/run_authority_follow_on_sequence_check.ps1` | Windows wrapper for the follow-on sequence check. |
| `scripts/run_authority_follow_on_sequence_check.sh` | POSIX wrapper for the follow-on sequence check. |
| `scripts/bol_scope_auth_check.py` | Optionally emits reporting-only summary/JSON for ODP-BOL-001 promotion-readiness requirements. |
| `scripts/run_bol_scope_auth_check.ps1` | Windows wrapper forwards ODP-BOL-001 scope-authority reporting modes without corrupting JSON. |
| `scripts/run_bol_scope_auth_check.sh` | POSIX wrapper forwards ODP-BOL-001 scope-authority reporting modes without corrupting JSON. |
| `docs/runbooks/bol_scope_auth.md` | Documents the reporting modes and their validate-only boundary. |
| `backend/tests/test_bol_scope_auth_artifacts.py` | Proves the reporting output and wrapper passthrough remain validate-only and blocked. |
| `backend/tests/test_qualification_parameterization_backlog_artifacts.py` | Mirror backlog checker expectations. |
| `backend/tests/test_readiness_core_artifacts.py` | Mirror readiness model expectations. |
| `backend/tests/test_authority_evidence_intake_artifacts.py` | Prove the authority-evidence guard passes current artifacts and fails closed on omitted streams, downstream unlocks, or P0 promotion. |
| `backend/tests/test_bologna_pilot_scope_authority_artifacts.py` | Prove pilot-scope reporting output and wrapper passthrough remain validate-only and blocked. |
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
py -3.12 scripts\authority_evidence_intake_check.py --summary
py -3.12 scripts\authority_evidence_intake_check.py --json
py -3.12 scripts\production_authority_evidence_references_check.py
py -3.12 scripts\production_authority_evidence_references_check.py --summary
py -3.12 scripts\production_authority_evidence_references_check.py --json
.\scripts\run_production_authority_evidence_references_check.ps1
py -3.12 scripts\bol_scope_auth_check.py
py -3.12 scripts\bol_scope_auth_check.py --summary
py -3.12 scripts\bol_scope_auth_check.py --json
.\scripts\run_bol_scope_auth_check.ps1 --summary
.\scripts\run_bol_scope_auth_check.ps1 --json
py -3.12 scripts\bologna_pilot_scope_authority_check.py --summary
py -3.12 scripts\bologna_pilot_scope_authority_check.py --json
.\scripts\run_bologna_pilot_scope_authority_check.ps1 --summary
.\scripts\run_bologna_pilot_scope_authority_check.ps1 --json
py -3.12 scripts\authority_follow_on_sequence_check.py
.\scripts\run_authority_follow_on_sequence_check.ps1
py -3.12 scripts\readiness_matrix_check.py
py -3.12 scripts\qualification_status_check.py --root .
$env:PYTHONPATH='backend'; py -3.12 -m pytest backend\tests\test_authority_evidence_intake_artifacts.py backend\tests\test_production_authority_evidence_references_artifacts.py backend\tests\test_authority_follow_on_sequence_artifacts.py backend\tests\test_bol_scope_auth_artifacts.py -q
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
- Optional `--summary` and `--json` outputs report the same blocked posture and
  missing evidence from existing config/state files only, without generating or
  mutating artifacts.
- `scripts\production_authority_evidence_references_check.py` passes and fails
  closed if a current evidence reference is recorded, a stream template is omitted, a
  required evidence list drifts from production authority intake, decision updates are
  allowed, or downstream unlocks are requested.
- Side-effect-free submitted-reference evaluation accepts complete synthetic reference
  shapes in memory, rejects malformed/unknown/unlocking reference shapes, and does not
  mutate the catalog or reference inputs.
- Optional reference-contract `--summary` and `--json` outputs report the same blocked
  reference shape from existing config files only, without appending wrapper text,
  generating artifacts, or mutating state.
- Optional ODP-BOL-001 scope-authority `--summary` and `--json` outputs report the
  same blocked promotion-readiness requirements from existing config files only,
  without appending wrapper text to JSON output, generating artifacts, recording an
  owner answer, recording pilot-scope authority, or allowing downstream unlocks.
- The overlapping authority validator family consumes `scripts\authority_check_lib.py`
  for common validate-only plumbing while preserving checker-specific frozen
  invariants and reducing net validator line count.
- Optional pilot-scope authority `--summary` and `--json` outputs report the committed
  missing-evidence requirements from existing config files only, without appending
  wrapper text to JSON output, generating artifacts, recording authority, selecting an
  AOI, approving sources, changing source rights, or allowing downstream unlocks.
- `scripts\authority_follow_on_sequence_check.py` passes and fails closed if the
  packet follow-on map drifts, a production authority stream is not covered by a
  follow-on lane, a lane is marked unblocked, or a lane omits the required cited-
  authority/catalog/checker prerequisites.
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
- 2026-07-02: Synchronized current-state and checker wording after PR #175 so live
  repo controls describe the merged authority-evidence composition guard while keeping
  `AUTH-EVIDENCE-INTAKE` active and all downstream authority blockers intact.
- 2026-07-02: Added optional summary/JSON output to the composition guard so the
  current missing authority evidence can be collected from machine-checked configs
  without creating a new runbook, generating artifacts, or changing blocker state.
- 2026-07-02: Linked the summary/JSON output from the production authority, Bologna
  owner-answer, and DS-017 source-entitlement runbooks, then forwarded wrapper
  arguments so operators can use the reporting modes through the same entrypoints
  without adding wrapper text to JSON output.
- 2026-07-02: Added a validate-only follow-on sequencing contract so the
  production authority packet's repo-local follow-on map is machine-checked while
  every covered lane remains blocked until cited authority updates the matching
  source catalog and checker.
- 2026-07-02: Added a validate-only production authority evidence reference contract
  so future cited authority references have a checked field shape before any
  production authority stream or follow-on lane can be unblocked.
- 2026-07-02: Added reporting-only summary/JSON output for the production authority
  evidence reference contract so operators can collect required reference fields from
  validated config without recording authority or unlocking work.
- 2026-07-02: Synchronized routing/state wording after PR #183 so the merged
  reference-contract reporting modes are recorded as complete while
  `AUTH-EVIDENCE-INTAKE`, external authority requirements, and `P0 = BLOCKED` remain
  unchanged.
- 2026-07-04: Synchronized routing/state wording after PR #95 so the checkout v7
  dependency-policy closeout is recorded as complete while `AUTH-EVIDENCE-INTAKE`,
  external authority requirements, and `P0 = BLOCKED` remain unchanged.
- 2026-07-04: Added side-effect-free synthetic submitted-reference evaluation to the
  production authority evidence reference checker so future cited-reference shapes can
  fail closed in memory while current references, downstream unlocks, and all authority
  blockers remain empty/blocked.
- 2026-07-04: Added reporting-only summary/JSON output for `bol_scope_auth` so the
  immediate ODP-BOL-001 cited-authority acceptance requirements are visible without
  creating artifacts, recording authority, or unblocking ODP-BOL-002/003/004.
- 2026-07-06: Consolidated the overlapping authority-validator helper/reporting
  plumbing into `scripts/authority_check_lib.py` and routed pilot-scope authority
  summary/JSON output through the shared helper while preserving empty authority
  records, blocked downstream updates, and `P0 = BLOCKED`.
