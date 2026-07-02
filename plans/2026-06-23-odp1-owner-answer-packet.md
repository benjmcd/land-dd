# ODP-BOL-001 Owner Answer Packet

## Goal
Make the next owner-authorized Bologna step executable by adding a single
validate-only ODP-BOL-001 owner-answer packet that is mechanically tied to the
existing owner-answer intake, ODP-BOL-001 response gate, and pilot-scope authority
packet.

The packet should let an owner or future agent see exactly what must be answered and
cited for product/AOI/scope authority without selecting an AOI, approving sources,
capturing fixtures, changing source rights, or starting DB-backed report work.

## Non-goals
- Do not record an owner answer or authority record.
- Do not select a Bologna AOI or approve any source.
- Do not change source rights, source readiness, source registry rows, fixture
  capture, source-failure fixtures, DB seed, report/API/runtime behavior, hosted
  authority, Level 10 status, or qualification status.
- Do not make P0 or any non-P0 qualification pass.

## Current state
- Live `origin/main` for this branch is
  `b5ed59e7143773f306ab216865df0133ca7b0451`.
- `state/PROJECT_STATE.md`, `plans/README.md`, and `tasks/task_queue.yaml` still
  route to completed EQ-R and need to move to the next active repo-local bridge.
- `config/bologna_owner_answer_intake.yaml` defines the owner-answer record contract
  and keeps `current_owner_answers` empty.
- `config/bologna_odp1_owner_response_gate.yaml` defines the ODP-BOL-001 response
  gate, decision requirements, outcome matrix, and downstream blockers.
- `config/bologna_pilot_scope_authority.yaml` defines required scope decisions and
  the future pilot-scope authority-record contract, with
  `current_authority_records` empty.
- `state/LEVEL_9_10_GATE_MATRIX.md` remains the Level 9/10 authority context for
  active follow-on plans; this slice does not change any gate status.

## Proposed design
Add `config/bologna_odp1_owner_answer_packet.yaml` as the owner-facing, machine-
checked answer packet for ODP-BOL-001. The packet will contain:

- a response template for the future owner answer record;
- a companion pilot-scope authority-record template;
- one checklist row for each required scope decision;
- allowed outcomes copied from the owner-answer intake/gate vocabulary;
- explicit downstream blockers and no-overclaim controls;
- a submission policy that keeps all committed owner/authority references empty.

Add a validate-only checker and wrappers that prove the packet stays aligned with
the canonical intake/gate/pilot-scope contracts. Route it into the manifest,
readiness crosswalk, backlog, project state, worklog, validation log, and task queue.

Alternative A, directly editing `current_owner_answers`, is rejected because no cited
owner authority exists. Alternative B, asking only in prose, is rejected because it
would not be machine-checked and could drift from the gate contract. Alternative C,
starting ODP-BOL-002 source-rights work, violates the required sequence because
ODP-BOL-001 is still missing.

## Bottom-up sequence
1. Add focused tests for the new packet and checker behavior.
2. Add the packet YAML, checker, wrappers, and runbook.
3. Wire the packet into manifest/crosswalk/backlog/state/task routing.
4. Run focused checks, qualification/readiness validation, change-impact, diff
   hygiene, and full verification before publication.

## Files likely to change
| File | Expected change |
|---|---|
| `config/bologna_odp1_owner_answer_packet.yaml` | New validate-only ODP-BOL-001 owner-answer packet. |
| `scripts/bologna_odp1_owner_answer_packet_check.py` | New checker for packet/gate/intake alignment. |
| `scripts/run_bologna_odp1_owner_answer_packet_check.ps1` | PowerShell wrapper. |
| `scripts/run_bologna_odp1_owner_answer_packet_check.sh` | POSIX wrapper for CI/Linux parity. |
| `docs/runbooks/bologna_odp1_owner_answer_packet.md` | Operator runbook. |
| `backend/tests/test_bologna_odp1_owner_answer_packet_artifacts.py` | Focused artifact/checker tests. |
| `MANIFEST.md` | Route the new authority packet/checker. |
| `config/qualification/readiness_crosswalk.yaml` | Map the new authority surface to qualification criteria. |
| `docs/qualification/readiness-crosswalk.md` | Human crosswalk row. |
| `state/QUALIFICATION_PARAMETERIZATION_BACKLOG.md` | Reference the ODP-BOL-001 packet without unblocking it. |
| `scripts/qualification_parameterization_backlog_check.py` | Require packet wiring in backlog controls. |
| `backend/tests/test_qualification_parameterization_backlog_artifacts.py` | Update backlog/routing assertions. |
| `backend/tests/test_readiness_core_artifacts.py` | Update active plan/completed task assertions. |
| `state/PROJECT_STATE.md` | Route current checkpoint and preserve blockers. |
| `plans/README.md` | Mark EQ-R completed and route current packet slice. |
| `tasks/task_queue.yaml` | Add done/active routing for the packet slice. |
| `state/WORKLOG.md` | Record execution. |
| `state/VALIDATION_LOG.md` | Record validation. |

## Tests / verification
```powershell
py -3.12 scripts\bologna_odp1_owner_answer_packet_check.py
.\scripts\run_bologna_odp1_owner_answer_packet_check.ps1
py -3.12 scripts\bologna_owner_answer_intake_check.py
py -3.12 scripts\bologna_odp1_owner_response_gate_check.py
py -3.12 scripts\qualification_parameterization_backlog_check.py --root .
py -3.12 scripts\readiness_matrix_check.py
$python = py -3.12 -c "import sys; print(sys.executable)"
& $python scripts\qualification_status_check.py --root . --python-command $python
py -3.12 scripts\validate_qualification.py --root . --layout repo
$env:PYTHONPATH='backend'; py -3.12 -m pytest -q backend\tests\test_bologna_odp1_owner_answer_packet_artifacts.py backend\tests\test_bologna_owner_answer_intake_artifacts.py backend\tests\test_bologna_odp1_owner_response_gate_artifacts.py backend\tests\test_readiness_core_artifacts.py backend\tests\test_qualification_parameterization_backlog_artifacts.py
py -3.12 scripts\qualification_change_impact_check.py --root . --changed-path <changed path> [...]
git diff --check
git diff --name-only --diff-filter=D
.\scripts\verify.ps1
```

## Risks and blockers
- The packet can improve executability but cannot create authority. Owner decisions
  and cited artifacts remain external blockers.
- Any future owner response still needs a later slice to record cited owner answers
  and pilot-scope authority records; this packet keeps committed references empty.
- Bologna source-rights, recorded corpus, and DB-backed report proof remain blocked
  behind ODP-BOL-001.

## Decision log
- 2026-06-23: Chose a machine-checked ODP-BOL-001 owner-answer packet because the
  next true milestone is external owner authority and the repo can still make that
  next input exact, auditable, and drift-resistant.

## Progress log
- 2026-06-23: Baseline owner-answer intake, ODP1 response gate, EQ-5 backlog checker,
  readiness matrix, and focused routing tests passed before edits.
- 2026-06-23: Added the validate-only ODP-BOL-001 owner-answer packet, checker,
  wrappers, runbook, crosswalk/backlog routing, and focused tests.
- 2026-06-23: Focused packet/intake/ODP1/readiness/backlog tests passed (`32`
  passed). Qualification status remained `BLOCKED=1 NOT_RUN=20`; structural
  qualification validation passed with existing blocked-readiness warnings.
