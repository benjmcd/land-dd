You are the **Lane A agent** for this repository.
Your scope is **Source Registry + DB Infrastructure** (MILESTONE_MAP Levels 2-3).

Repository: `C:\Users\benny\OneDrive\Desktop\land_diligence_dual_agent_workspace`

You have authority to work autonomously within Lane A's scope. Do not touch files owned by other lanes. Do not rely on chat history. Treat repository files as the source of truth.

**Read in this order before touching any code:**

1. `CLAUDE.md` (imports `AGENTS.md` — read that too)
2. `MILESTONE_MAP.md` — your gate targets are L2-* and L3-001 to L3-010
3. `LANE_OWNERSHIP.md` — your owned files, readable files, and forbidden files
4. `lanes/lane-a/AGENTS.md` — your full operating contract
5. `state/lane-a-state.md` — current state and next task
6. `plans/lane-a-2026-06-03-source-registry.md` — your active implementation plan

**Run baseline verification:**

```bash
./scripts/verify.sh
```

**Run your lane tests:**

```bash
cd backend && PYTHONPATH=. pytest tests/source_registry/ -v
```

Both must pass before you start any new work. If either fails, investigate and fix before proceeding.

**Your next task is TA-010** (detailed in your plan): archive the backward-compat shims at `backend/app/repositories/` and `backend/app/services/` — these re-export from your module and Lane A owns them. First grep to confirm nothing still imports from them, then move both directories to `archive/<today>_source-registry-lane-migration/backend/app/`. Verify tests still pass, then proceed to TA-020 (SQLAlchemy ORM model for `source.sources`).

**Milestone gate you are working toward:** L2-003 (migrations apply cleanly) and L3-001 to L3-010 (source registry fully seeded and license-tracked).

**Stop conditions:** record a blocker in `state/lane-a-state.md` if Docker is unavailable for DB smoke, if a license/terms status is unknown, or if a migration would conflict with another lane.
