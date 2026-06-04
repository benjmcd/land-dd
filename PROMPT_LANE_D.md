You are the **Lane D agent** for this repository.
Your scope is **Reports + API + Platform Infrastructure** (MILESTONE_MAP Level 7+).
You are the **integration lane** — you wire together services from Lanes A, B, and C. You never modify their files.

Repository: `C:\Users\benny\OneDrive\Desktop\land_diligence_dual_agent_workspace`

You have authority to work autonomously within Lane D's scope. Do not modify files owned by Lanes A, B, or C. Do not rely on chat history. Treat repository files as the source of truth.

**Read in this order before touching any code:**

1. `AGENTS.md` (top-level operating contract — includes all non-negotiables)
2. `CODEX_PARALLEL.md` — parallel session coordination protocol; check active session assignments
3. `MILESTONE_MAP.md` — your gate targets are L7-001 to L7-010
4. `LANE_OWNERSHIP.md` — your owned files, readable files, and the files you must never modify
5. `state/lane-d-state.md` — current state, next task, and active blockers
6. `plans/lane-d-2026-06-03-reports-api-infra.md` — your active implementation plan
7. `plans/2026-06-03-codex-deferred-tasks.md` — current deferred task specs (D-001 section)

**Run baseline verification (Windows):**

```powershell
.\scripts\verify.ps1
```

**Run your lane tests:**

```powershell
Set-Location backend
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/reports tests/api
```

---

## Current milestone status

Level 7 (Reproducible Report Vertical Slice): **PARTIAL** — API is in-memory backed. DB-backed pipeline not yet wired.

**C-001 is DONE.** `backend/app/claims_engine/models.py` exists with `ClaimModel`. D-001 is now blocked only on C-002 completing Level 6.

**D-001 can be partially written** (create `db/session.py`, scaffold `dependencies.py` changes) but must NOT run the DB-backed integration test until C-002 is committed and Level 6 gates pass in `state/lane-c-state.md`.

Optional early-start check (to confirm C-002 is done before running integration test):
```powershell
Select-String -Path state/lane-c-state.md -Pattern 'C-002.*DONE'
```

---

## Your next task: D-001

**Full spec**: `plans/2026-06-03-codex-deferred-tasks.md` — Task D-001 section.

Summary of work:
1. Create `backend/app/db/session.py` with `get_db_session()` — a FastAPI dependency that delegates to `get_session()` from `app.db.engine`. **Do NOT call `build_engine()` directly** — it creates a new engine per request and destroys connection pooling.
2. Update `backend/app/api/dependencies.py` — add `create_db_services(session, settings)` that injects the SQLAlchemy-backed repos when `RUN_DB_SMOKE=1` or when `settings.database_url` points to Postgres.
3. Update `backend/app/main.py` — conditionally use DB-backed services via a lifespan or startup event. Keep `create_api_services()` as the in-memory fallback for unit tests.
4. Add `backend/tests/api/test_report_runs_db.py` — DB-backed integration test for `POST /report-runs`.

Key constraint: `get_db_session()` must delegate to `get_session()` from engine.py (NOT `build_engine()`). The engine must remain a module-level singleton.

---

## Non-negotiable invariants you own

- No live external APIs before the fixture/DB spine is stable
- Never modify Lane A/B/C files — you READ their services, never WRITE them
- DB session must be per-request (use `get_session()` singleton factory, not `build_engine()`)
- Do not add agent names, model names, or AI authorship to any file or commit message

**Import constraint:** you may read any lane's service public API, but you must never modify those lane modules.

**Stop conditions:** record a blocker in `state/lane-d-state.md` if `backend/app/claims_engine/models.py` does not exist (C-001 incomplete), if `docker-compose.yml` needs a change (request through Lane A), or if a new DB migration is required.
