# Post-Geology Routing Closeout

## Goal
Close the owner-independent extended-domain fixture-ingestion sequence after the
geology fixture proof merged through PR #172. This pass updates routing and
control-plane checks so the repo no longer treats `GEOLOGY-FIXTURE` as active,
records that all named owner-independent US-MVP extended-domain fixture proofs
have landed, and routes remaining work back to authority-dependent milestones.

## Non-goals
- No new fixture connector, source registry promotion, live source call, source
  approval, source-rights decision, vendor authority, or source expansion.
- No DB schema, API contract, auth/security, report semantic, UI, runtime, or
  hosted infrastructure change.
- No Bologna fixture capture, recorded-source corpus, DB seed, report proof, or
  rulepack implementation.
- No DS-017 approval, hosted authority, Level 10 claim, qualification `PASS`,
  owner-decision unfreeze, or `P0` unblock.

## Current state
PR #172 landed the NCGS 1985 geologic map-unit context fixture-ingestion proof at
`71b9c41611ac256eee6e1dd5126779c2472c5b2b`. The named owner-independent
extended-domain fixture-ingestion proofs are now complete:

- `MINERALS-FIXTURE` through PR #168.
- `BROADBAND-FIXTURE` through PR #169.
- `ENV-FIXTURE` through PR #170.
- `WATER-FIXTURE` through PR #171.
- `GEOLOGY-FIXTURE` through PR #172.

These completions prove local fixture ingestion through evidence, claim, and
dossier surfaces for selected US-MVP extended domains. They do not approve
sources, change source rights, resolve external owner authority, make Bologna
usable, approve DS-017, create hosted production authority, satisfy Level 10, or
change empirical qualification status.

`state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 authority context for
hosted and production-readiness claims. This routing closeout does not change
any gate status in that matrix.

## Consensus decision
Three options were considered:

1. Start another fixture-ingestion lane immediately. Rejected because the live
   routing names geology as the remaining extended-domain fixture lane and no
   current authority file selects DS-020, DS-022, or another source as the next
   required owner-independent proof.
2. Start Bologna/source-authority implementation. Rejected because `BSA-001` and
   the ODP-BOL-002/003/004 authority chain remain blocked until cited external
   product/AOI/source-review/source-rights/corpus/report-proof authority exists.
3. Perform a routing-only post-geology closeout. Selected because it reconciles
   live state after PR #172 while preserving the correct blocker boundary for
   the next real milestones.

## Bottom-up sequence
1. Add this plan as the current routing plan.
2. Update `plans/README.md`, `state/PROJECT_STATE.md`, and
   `tasks/task_queue.yaml` so `GEOLOGY-FIXTURE` is done and
   `POST-GEOLOGY-ROUTING` is the only active task.
3. Update the qualification backlog checker and readiness tests to enforce the
   post-geology routing boundary.
4. Record worklog and validation evidence after checks run.
5. Run focused routing checks, authority guardrails, and the full Windows
   verifier.

## Files likely to change
| File | Expected change |
|---|---|
| `plans/2026-07-02-post-geology-routing.md` | New routing-only closeout plan. |
| `plans/README.md` | Record geology as completed and route to this plan. |
| `state/PROJECT_STATE.md` | Record post-PR #172 checkpoint and remaining blockers. |
| `tasks/task_queue.yaml` | Mark geology done and add active routing closeout task. |
| `scripts/qualification_parameterization_backlog_check.py` | Guard post-geology active routing. |
| `backend/tests/test_qualification_parameterization_backlog_artifacts.py` | Mirror backlog checker expectations. |
| `backend/tests/test_readiness_core_artifacts.py` | Mirror readiness model expectations. |
| `state/WORKLOG.md` | Record closeout work and validation. |
| `state/VALIDATION_LOG.md` | Record exact commands, results, and residual risk. |

## Tests / verification
Expected focused commands:

```powershell
$env:PYTHONPATH='backend'; py -3.12 -m pytest backend\tests\test_readiness_core_artifacts.py backend\tests\test_qualification_parameterization_backlog_artifacts.py -q
py -3.12 -m ruff check backend\tests\test_readiness_core_artifacts.py backend\tests\test_qualification_parameterization_backlog_artifacts.py scripts\qualification_parameterization_backlog_check.py
$env:PYTHONPATH='backend'; $env:MYPYPATH='backend'; py -3.12 -m mypy backend\tests\test_readiness_core_artifacts.py backend\tests\test_qualification_parameterization_backlog_artifacts.py scripts\qualification_parameterization_backlog_check.py
py -3.12 scripts\source_readiness.py
py -3.12 scripts\qualification_parameterization_backlog_check.py --root .
py -3.12 scripts\readiness_matrix_check.py
py -3.12 scripts\qualification_status_check.py --root .
git diff --check
.\scripts\verify.ps1
```

Pass/fail requirements:
- `GEOLOGY-FIXTURE` is done, not active.
- `POST-GEOLOGY-ROUTING` is the only active task and depends on
  `GEOLOGY-FIXTURE`.
- All named extended-domain fixture-ingestion plans remain linked from the plan
  index and backlog checker inputs.
- `BSA-001`, ODP-BOL-002, ODP-BOL-003, ODP-BOL-004, DS-017, hosted production,
  Level 10, qualification `PASS`, owner-decision unfreeze, and `P0` unblock
  remain blocked by cited external authority requirements.
- The closeout introduces no new runtime behavior, source approval, source
  rights, fixture capture, DB seed, report proof, schema/API/auth/UI change, or
  production authority.

## Future sequence
Immediate next milestone after this routing closeout is not implementation; it
is owner/source authority evidence intake. The first executable authority lane is
`BSA-001` or a narrower ODP-BOL authority packet only when cited product/AOI and
source-review authority exists. After that, the ordered Bologna path remains:
source authority/source rights, recorded-source corpus, DB-backed report proof,
then rulepack/runtime/report work. In parallel, DS-017, hosted deployment,
identity/RBAC, observability, billing, image publication, and Level 10 remain
separate authority-dependent streams. DS-020/DS-022 or other additional fixture
lanes should be selected only by an explicit future routing decision.

## Decision log
- 2026-07-02: Selected a routing-only closeout after PR #172 because the named
  owner-independent extended-domain fixture-ingestion sequence is complete and
  the remaining work is authority-dependent. This preserves `P0 = BLOCKED`,
  DS-017, Bologna, hosted, Level 10, and qualification blockers.
