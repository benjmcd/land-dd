# ODP-BOL-002 Owner Answer Packet

## Goal
Make the next source-rights owner decision executable by adding a validate-only
ODP-BOL-002 owner-answer packet aligned to the existing owner-answer intake,
ODP-BOL-002 response gate, source-authority intake, and source-rights matrix.

## Non-goals
- Do not record a new owner answer, source-authority record, or source-rights approval.
- Do not select or change the Bologna AOI.
- Do not approve sources, promote source registry rows, capture fixtures, run
  connectors, seed or mutate the database, create report artifacts, change report
  semantics, approve DS-017, claim hosted authority, claim qualification PASS, or claim
  Level 10 readiness.
- Do not bypass the missing ODP-BOL-001 cited pilot-scope authority prerequisite.

## Current state
- `config/bologna_owner_answer_intake.yaml` contains one review-only
  `ODP-BOL-001` answer and keeps `ODP-BOL-002` through `ODP-BOL-004` missing.
- `config/bol_scope_auth.yaml` proves that the review-only `ODP-BOL-001` answer is
  not cited pilot-scope authority.
- `config/bologna_odp2_source_rights_response_gate.yaml` defines the ODP-BOL-002
  response acceptance criteria, candidate evidence requirements, rights decisions,
  and no-overclaim controls, but it is gate-side rather than owner-packet-side.
- `config/bologna_source_authority_intake.yaml` defines the future
  `source_authority_record_contract` and keeps `current_source_authority_records: []`.
- `config/bologna_source_rights.yaml` keeps every candidate source pending and every
  promotion/runtime/report flag false.
- `state/LEVEL_9_10_GATE_MATRIX.md` remains the hosted and Level 9/10 authority
  boundary; this slice must not claim hosted readiness or Level 10 completion.

## Proposed design
Add a new `bologna_odp2_owner_answer_packet` validate-only surface that mirrors the
proven ODP-BOL-001 owner-answer-packet pattern, but derives source-rights checklists
from the ODP-BOL-002 gate and source-authority/right matrices.

Rejected alternatives:
- Directly record an ODP-BOL-002 answer or approve source rights. Rejected because
  ODP-BOL-001 cited authority is still missing and there is no cited source-rights
  authority.
- Start corpus or fixture work. Rejected because source rights and corpus authority are
  sequential prerequisites.
- Leave only the response gate. Rejected because the owner-facing source-rights packet
  is the actual next decision artifact and should be checked before any external answer
  is recorded.

## Bottom-up sequence
1. Add `config/bologna_odp2_owner_answer_packet.yaml` with owner-answer and
   source-authority templates, source/candidate decision checklist, outcome policy,
   submission policy, and no-overclaim controls.
2. Add `scripts/bologna_odp2_owner_answer_packet_check.py` and PowerShell/POSIX wrappers.
3. Add focused artifact tests proving alignment, blocked current state, fail-closed
   checklist coverage, and validate-only wrapper behavior.
4. Route the new surface through the manifest, qualification crosswalk, task queue,
   plans README, project state, backlog, worklog, and validation log.
5. Run focused checks, qualification validation, readiness/backlog checks, lint/type
   checks, and full `.\scripts\verify.ps1`.

## Files likely to change
| File | Expected change |
|---|---|
| `config/bologna_odp2_owner_answer_packet.yaml` | New validate-only owner packet. |
| `docs/runbooks/bologna_odp2_owner_answer_packet.md` | New runbook. |
| `scripts/bologna_odp2_owner_answer_packet_check.py` | New checker. |
| `scripts/run_bologna_odp2_owner_answer_packet_check.ps1` | Windows wrapper. |
| `scripts/run_bologna_odp2_owner_answer_packet_check.sh` | POSIX wrapper. |
| `backend/tests/test_bologna_odp2_owner_answer_packet_artifacts.py` | Focused tests. |
| `config/qualification/readiness_crosswalk.yaml` | Map the new surface. |
| `docs/qualification/readiness-crosswalk.md` | Human crosswalk row. |
| `MANIFEST.md` | Route the new packet. |
| `tasks/task_queue.yaml` | Add completed packet task and active plan routing. |
| `plans/README.md` | Document the current plan. |
| `state/PROJECT_STATE.md` | Update checkpoint and next steps. |
| `state/QUALIFICATION_PARAMETERIZATION_BACKLOG.md` | Reference the packet. |
| `state/WORKLOG.md` | Record implementation. |
| `state/VALIDATION_LOG.md` | Record verification. |

## Tests / verification
Expected focused checks:

```powershell
py -3.12 scripts\bologna_odp2_owner_answer_packet_check.py
.\scripts\run_bologna_odp2_owner_answer_packet_check.ps1
py -3.12 -m pytest backend\tests\test_bologna_odp2_owner_answer_packet_artifacts.py -q
py -3.12 scripts\validate_qualification.py --root . --layout repo
py -3.12 scripts\qualification_parameterization_backlog_check.py --root .
```

Final gate:

```powershell
.\scripts\verify.ps1
```

Expected signal: all checks pass while `ODP-BOL-002` remains missing, source-authority
records remain empty, source-rights rows remain pending, and no source/corpus/report
work is unlocked.

## Risks and blockers
- The true blocker remains cited owner authority. This packet cannot create
  ODP-BOL-001 or ODP-BOL-002 authority by itself.
- The new packet must stay data-derived from existing ODP-BOL-002/source-rights
  contracts to avoid drift.
- Adding a new checker requires qualification crosswalk routing or validation will
  correctly fail closed.

## Decision log
- 2026-06-27: Chose an ODP-BOL-002 owner-answer packet because it is the next
  owner-facing artifact needed after the scope-authority readiness gate and advances
  source-rights approval without approving any source.

## Progress log
- 2026-06-27: Live audit found current `origin/main` at
  `16566ea88ba8e4930ef476c48f558c5c076bb2ee`, a clean isolated
  `worktrees/bol-rights` branch, existing source-rights and ODP-BOL-002 response gate
  checks passing, and no existing ODP-BOL-002 owner-answer packet.
- 2026-06-27: Added the ODP-BOL-002 owner-answer packet, checker, wrappers, runbook,
  focused artifact tests, manifest/crosswalk/backlog routing, and task/project/plan
  state updates while keeping source-authority records and source-rights approval
  references empty.
- 2026-06-27: Focused packet, Bologna blocker, backlog, crosswalk, readiness,
  qualification, change-impact, ruff, mypy, and full `.\scripts\verify.ps1` checks
  passed. DB smoke was skipped by default because `RUN_DB_SMOKE=1` was not set.
