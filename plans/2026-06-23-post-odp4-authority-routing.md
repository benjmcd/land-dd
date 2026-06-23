# Post-ODP4 Bologna Authority Routing

## Goal
Record the post-merge state after `BOL-ODP4-GATE` and make the next Bologna/qualification boundary explicit: no DB-backed Bologna report proof can be built until cited owner authority exists for `ODP-BOL-001`, `ODP-BOL-002`, `ODP-BOL-003`, and then `ODP-BOL-004`.

## Non-goals
- Do not record owner answers or authority records.
- Do not select a Bologna AOI, approve sources, change source rights, capture fixtures, seed the DB, create report artifacts, change API/report semantics, or claim hosted/Level 10 readiness.
- Do not freeze additional qualification targets, domain profiles, criterion contracts, judgment rubrics, or source profiles.

## Current state
- `BOL-ODP4-GATE` merged through PR #157 at `a1d6c7dcf90133ad2cf382357f6b202f852c0f5b`.
- `config/bologna_owner_answer_intake.yaml` keeps all ODP-BOL owner answers missing.
- `config/bologna_odp4_db_report_proof_response_gate.yaml` validates the required DB-backed report-proof owner-answer shape while preserving missing `ODP-BOL-001` through `ODP-BOL-003` prerequisites.
- `state/owner-decisions.md` records only QFREEZE-1 authority; it does not authorize Bologna AOI/source/corpus/report work.
- `state/LEVEL_9_10_GATE_MATRIX.md` remains an authority boundary for hosted/Level 10 claims; this routing update does not change any Level 9/10 gate status.
- `P0` remains `BLOCKED`; all non-P0 qualifications and overlays remain `NOT_RUN`.

## Proposed design
Update routing/state only. The post-ODP4 route should say the response-gate scaffold is complete and the next substantive Bologna work is owner-authority dependent. This avoids both false implementation progress and another layer of blocked YAML.

Rejected alternatives:
- Build a DB-backed Bologna report now: rejected because the required owner answers and corpus/source authority are absent.
- Add another Bologna response gate: rejected because ODP-BOL-001 through ODP-BOL-004 are already represented and another gate would not reduce the authority blocker.
- Freeze more qualification targets from inference: rejected because QFREEZE-1 explicitly excludes those values.

## Bottom-up sequence
1. Update plan/task/state routing to mark `BOL-ODP4-GATE` complete.
2. Record the next authority-dependent milestone and fallback EQ-5-style non-authorizing backlog path.
3. Re-run ODP4, owner-intake, qualification status, qualification validation, and routing-focused tests.

## Files likely to change
| File | Expected change |
|---|---|
| `plans/2026-06-23-post-odp4-authority-routing.md` | New routing plan |
| `plans/README.md` | Mark ODP4 complete and name post-ODP4 authority routing |
| `tasks/task_queue.yaml` | Mark `BOL-ODP4-GATE` done and add/route the post-ODP4 authority boundary |
| `state/PROJECT_STATE.md` | Update top checkpoint from active ODP4 to post-ODP4 authority boundary |
| `state/WORKLOG.md` | Log the routing correction |
| `state/VALIDATION_LOG.md` | Log validation evidence |

## Tests / verification
```powershell
py -3.12 scripts\bologna_odp4_db_report_proof_response_gate_check.py
py -3.12 scripts\bologna_owner_answer_intake_check.py
py -3.12 scripts\qualification_status_check.py --root .
py -3.12 scripts\validate_qualification.py
$env:PYTHONPATH='backend'; py -3.12 -m pytest -q backend\tests\test_bologna_odp4_db_report_proof_response_gate_artifacts.py backend\tests\test_bologna_owner_answer_intake_artifacts.py backend\tests\test_qualification_parameterization_backlog_artifacts.py backend\tests\test_readiness_core_artifacts.py
.\scripts\verify.ps1
```

## Risks and blockers
- If state routing claims ODP4 is complete before live `main` contains PR #157, it would overstate authority. This plan is based on live `origin/main@a1d6c7dcf90133ad2cf382357f6b202f852c0f5b`.
- The next Bologna implementation remains externally blocked until owner authority is cited. This routing update should not hide that blocker.

## Decision log
- 2026-06-23: Selected routing correction over more Bologna scaffolding because existing gates already cover the four required owner-answer threads.

## Progress log
- 2026-06-23: Baseline ODP4 gate, owner-answer intake, qualification status, and qualification validation passed before edits.
- 2026-06-23: Routed ODP4 to complete, added post-ODP4 authority boundary, updated task/state/plan surfaces, updated routing tests, and passed focused gates plus full `.\scripts\verify.ps1`.
