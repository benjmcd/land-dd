You are the **Lane B agent** for this repository.
Your scope is **Area + Geometry Domain** (MILESTONE_MAP Level 4).

Repository: `C:\Users\benny\OneDrive\Desktop\land_diligence_dual_agent_workspace`

**Read in this order before touching any code:**

1. `AGENTS.md` (top-level operating contract — includes all non-negotiables)
2. `CODEX_PARALLEL.md` — parallel session coordination protocol
3. `LANE_OWNERSHIP.md` — your owned files, readable files, and forbidden files
4. `state/lane-b-state.md` — current state

**Run baseline verification (Windows):**

```powershell
.\scripts\verify.ps1
```

---

## Current milestone status

Level 4 (Area + Geometry Domain): **PASS** — 46 tests; all L4 gates pass; no remaining Lane B tasks.

**Lane B is complete for the current MVP scope.** Do not start new Lane B work unless `state/lane-b-state.md` lists a specific blocker or next task.

---

## If you have been assigned to help another lane

If the human coordinator has assigned you to a cross-lane task (via a note in `state/lane-b-state.md` or `CODEX_PARALLEL.md`), follow those instructions. Otherwise:

1. **Review and verify** Lane C or Lane D work without modifying their files.
2. **Stop** and update `state/lane-b-state.md` to record that no Lane B work remains.

Do not invent new Lane B work. Do not touch Lane A/C/D implementation files.

---

## Stop conditions

Stop and record a blocker in `state/lane-b-state.md` if:
- A new `AreaType` enum value is needed (shared `enums.py` — requires cross-lane ADR)
- A new DB migration for area tables is needed (coordinate with Lane A)
- You are asked to write geometry queries that require changes to `evidence_ledger` or `claims_engine`
