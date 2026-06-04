You are the **Lane A agent** for this repository.
Your scope is **Source Registry + DB Infrastructure** (MILESTONE_MAP Levels 2-3).

Repository: `C:\Users\benny\OneDrive\Desktop\land_diligence_dual_agent_workspace`

**Read in this order before touching any code:**

1. `AGENTS.md` (top-level operating contract — includes all non-negotiables)
2. `CODEX_PARALLEL.md` — parallel session coordination protocol
3. `LANE_OWNERSHIP.md` — your owned files, readable files, and forbidden files
4. `state/lane-a-state.md` — current state

**Run baseline verification (Windows):**

```powershell
.\scripts\verify.ps1
```

---

## Current milestone status

Level 2/3 (Source Registry + Provenance): **PASS** — 41 tests; no remaining Lane A tasks.

**Lane A is complete for the current MVP scope.** Do not start new Lane A work unless `state/lane-a-state.md` lists a specific blocker or next task.

---

## If you have been assigned to help another lane

If the human coordinator has assigned you to a cross-lane task (via a note in `state/lane-a-state.md` or `CODEX_PARALLEL.md`), follow those instructions. Otherwise, your options are:

1. **Review and verify** Lane C or Lane D work without modifying their files.
2. **Archive backward-compat shims** if any remain (check `state/lane-a-state.md`).
3. **Stop** and update `state/lane-a-state.md` to record that no Lane A work remains.

Do not invent new Lane A work. Do not touch Lane B/C/D implementation files.

---

## Stop conditions

Stop and record a blocker in `state/lane-a-state.md` if:
- A needed license/terms status is unknown
- A migration is required that conflicts with another lane
- You are asked to create live connector credentials
