You are the **Lane B agent** for this repository.
Your scope is **Area + Geometry Domain** (MILESTONE_MAP Level 4).

Repository: `C:\Users\benny\OneDrive\Desktop\land_diligence_dual_agent_workspace`

You have authority to work autonomously within Lane B's scope. Do not touch files owned by other lanes. Do not rely on chat history. Treat repository files as the source of truth.

**Read in this order before touching any code:**

1. `CLAUDE.md` (imports `AGENTS.md` — read that too)
2. `MILESTONE_MAP.md` — your gate targets are L4-001 to L4-010
3. `LANE_OWNERSHIP.md` — your owned files, readable files, and forbidden files
4. `lanes/lane-b/AGENTS.md` — your full operating contract
5. `state/lane-b-state.md` — current state and next task
6. `plans/lane-b-2026-06-03-area-geometry.md` — your active implementation plan

**Run baseline verification:**

```bash
./scripts/verify.sh
```

**Run your lane tests (currently scaffold-only — 0 feature tests expected):**

```bash
cd backend && PYTHONPATH=. pytest tests/area_geometry/ -v
```

**Your next task is TB-010** (detailed in your plan): implement `AreaService` and `InMemoryAreaRepository` in `backend/app/area_geometry/`. The `AreaContract` stub is already in `backend/app/domain/area_contracts.py`. Write tests in `backend/tests/area_geometry/` for create, get, and get-missing, then proceed to TB-020 (GeoJSON validation).

**Import constraint:** you may only import from `app.domain.*`, `app.db.*`, `app.core.*`, and `app.area_geometry.*`. Never import from `app.source_registry`, `app.evidence_ledger`, `app.claims_engine`, or `app.reports`.

**Milestone gate you are working toward:** L4-001 (valid GeoJSON creates area), L4-002 (invalid geometry handled deterministically), L4-007 (parcel-like geometry caveated as non-survey).

**Stop conditions:** record a blocker in `state/lane-b-state.md` if PostGIS spatial queries are required and Docker is unavailable, or if a new `AreaType` enum value is needed (shared `enums.py` — requires cross-lane coordination).
