# CODEX_PARALLEL.md — Parallel Session Coordination Protocol

This file governs how two simultaneous Codex sessions share the repository without conflict.
Read this file at the start of every session. Update the `## Active sessions` table when you begin work.

---

## Current task chain (as of 2026-06-04)

```
C-001 (Lane C — claim ORM models)
  └─> C-002 (Lane C — not-evaluated rule claim logic)
         └─> D-000 (Lane D — report surfacing for not-evaluated categories)
                └─> D-001 (Lane D — Level 7 DB wiring)
```

Lanes A and B are **DONE** (L3/L4 PASS). No new Lane A or Lane B work is needed.

---

## Session assignment table

| Session slot | Assigned lane | Current task | Status | File lock |
|---|---|---|---|---|
| Slot 1 | Lane C | C-002 | Pending | `backend/app/claims_engine/`, `config/ruleset_homestead_mvp.yaml` |
| Slot 2 | Lane D | D-000 then D-001 | D-001 pre-work only | `backend/app/reports/`, `backend/app/api/`, `backend/app/db/session.py` |

**Rules:**
1. Check this table before starting any work. If another session owns your target files, stop and read its lane state file to see if the work is complete.
2. Update the table when you begin a task. Update status to `In progress` and add your session ID.
3. Each slot maps to exactly one lane. Do not cross into another slot's lane files.

---

## Parallel execution rules

### C-001 and D-001 pre-work CAN run in parallel with caveats

C-001 owns: `backend/app/claims_engine/models.py` (new), `backend/app/claims_engine/claim_repo.py`
D-001 owns: `backend/app/db/session.py` (new), `backend/app/api/dependencies.py`, `backend/app/main.py`

These file sets do not overlap. However:
- D-001's integration test requires C-001's ORM models to be importable.
- D-001's `create_db_services()` must inject `SqlAlchemyClaimRepository` — which should be ORM-backed after C-001.
- Therefore, D-001 **must not run its integration test** until C-001 is committed and verified.

**Safe parallel sequence:**
1. Session 1 starts C-001.
2. Session 2 can write D-001's `session.py` after C-001 is committed and verified.
3. Session 2 must not update `dependencies.py`, update `main.py`, or run the DB-backed API integration test until C-002 and D-000 are complete.

### C-002 and D-000 must stay split by lane ownership

C-002 owns: `backend/app/claims_engine/not_evaluated.py` (new), `backend/app/claims_engine/rule_engine.py`, `config/ruleset_homestead_mvp.yaml`, `backend/tests/claims_engine/test_not_evaluated_claims.py` (new)
D-000 owns: `backend/app/reports/service.py`, report tests, and API tests needed to surface unsupported categories in report output.
D-001 owns: `backend/app/db/session.py`, `backend/app/api/dependencies.py`, `backend/app/main.py`, and DB-backed API integration tests.

Lane C must not modify `backend/app/reports/service.py`. Lane D must wait for C-002's claim/rule behavior before implementing D-000 report surfacing.

---

## Pre-condition checks (machine-verifiable)

Before starting each task, verify the pre-conditions by checking file existence:

**C-001 pre-conditions:** (all already met)
```powershell
Test-Path backend/app/db/base.py          # AppBase exists
Test-Path backend/app/db/types.py         # severity_band_enum exists
```

**C-002 pre-conditions:**
```powershell
Test-Path backend/app/claims_engine/models.py  # C-001 complete
# AND grep ClaimModel in models.py
Select-String -Path backend/app/claims_engine/models.py -Pattern 'class ClaimModel'
```

**D-001 pre-conditions:**
```powershell
Test-Path backend/app/claims_engine/models.py  # C-001 complete
Select-String -Path backend/app/claims_engine/models.py -Pattern 'class ClaimModel'
Select-String -Path state/lane-c-state.md -Pattern 'C-002.*DONE'
Select-String -Path tasks/task_queue.yaml -Pattern 'id: D-000|status: done'
# Note: backend/app/db/session.py can be written before C-002/D-000 complete.
# DB-backed service wiring and integration tests must wait.
```

---

## How to signal task completion

When you complete a task:
1. Update your lane's `state/lane-*.md` — mark the task PASS in the milestone gates.
2. Add a WORKLOG entry to `state/WORKLOG.md`.
3. Commit with a clear message (no agent attribution).
4. The other session will see the commit in `git log` and the state file update.

**Do NOT** update this table yourself after completing a task — the human coordinator updates the assignment table. You only need to update the lane state and worklog files.

---

## File ownership at a glance (relevant to active tasks)

| File | Owner | Notes |
|---|---|---|
| `backend/app/claims_engine/models.py` | Lane C (new) | C-001 creates this |
| `backend/app/claims_engine/claim_repo.py` | Lane C | C-001 refactors this |
| `backend/app/claims_engine/not_evaluated.py` | Lane C (new) | C-002 creates this |
| `backend/app/claims_engine/rule_engine.py` | Lane C | C-002 modifies this |
| `config/ruleset_homestead_mvp.yaml` | Lane C | C-002 adds 4 new hard_gates |
| `backend/app/reports/service.py` | Lane D | D-000 adds unsupported-category report surfacing |
| `backend/app/db/session.py` | Lane D (new) | D-001 creates this |
| `backend/app/api/dependencies.py` | Lane D | D-001 modifies this |
| `backend/app/main.py` | Shared Interface Zone | D-001 modifies via plan — requires ADR |
| `backend/app/db/base.py` | Shared Interface Zone | DO NOT modify — single AppBase |
| `backend/app/db/types.py` | Shared Interface Zone | DO NOT modify without ADR |
| `backend/app/domain/enums.py` | Shared Interface Zone | DO NOT modify without ADR |

---

## Verification commands

After any Lane C task:
```powershell
Set-Location backend
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/claims_engine
ruff check app/claims_engine
mypy app/claims_engine
Set-Location ..
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

After D-001:
```powershell
Set-Location backend
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/api tests/reports
ruff check app/api app/reports app/db
mypy app/api app/reports app/db
Set-Location ..
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

Full gate (run before any commit):
```powershell
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```
