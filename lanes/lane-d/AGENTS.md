# Lane D — Reports + API + Platform Infrastructure

You are the Lane D agent. Read this file first, then read the files listed below.

## Required startup reads

1. `../../AGENTS.md` — root operating contract (always applies)
2. `../../MILESTONE_MAP.md` — authoritative maturity gates
3. `../../LANE_OWNERSHIP.md` — file ownership and isolation rules
4. `../../state/lane-d-state.md` — current Lane D state and next task
5. The active plan referenced in `state/lane-d-state.md`

## Your scope

You own MILESTONE_MAP.md Level 7 (reproducible report vertical slice) and setup for Levels 8-10.
You are the INTEGRATION LANE: you wire together services from Lanes A, B, C into report runs and API endpoints.

## Your milestone gates

| Level | Gates | Pass condition |
|---|---|---|
| L7 | L7-001 to L7-010 | Report run persisted with status; stores source/rule versions; API creates/retrieves reports; output includes evidence-linked claims, unknowns, caveats; fixture-only (no live APIs) |

## Your owned directories and files

See `LANE_OWNERSHIP.md` Lane D section for the full list.

Key:
- `backend/app/reports/` — ReportRunService and related code
- `backend/app/api/` — FastAPI routers (sources, areas, evidence, reports)
- `backend/tests/reports/` + `backend/tests/api/` — Lane D tests
- `Makefile` — build/run shortcuts

## What you MUST NOT touch (CRITICAL)

- `backend/app/source_registry/` — Lane A owns this; read only
- `backend/app/area_geometry/` — Lane B owns this; read only
- `backend/app/evidence_ledger/` — Lane C owns this; read only
- `backend/app/claims_engine/` — Lane C owns this; read only
- `backend/app/domain/source_contracts.py`, `area_contracts.py`, `evidence_contracts.py`, `claim_contracts.py`
- `docker-compose.yml` — Lane A owns this; read only
- Any other lane's plans, state, or ADR files

## Import constraint

You may import from ALL lane modules' service APIs, but ONLY for reading/calling — never for modifying those modules.
You implement `SourceExistsProtocol` and `AreaExistsProtocol` from `app.domain.protocols` and inject them into Lane C's services.

## Integration responsibilities

1. Wire real SQLAlchemy-backed repositories from A/B into C's evidence service via protocols.
2. Assemble `ReportRunContract` from areas + sources + evidence + claims.
3. Persist report runs to `reports.report_runs` DB table.
4. Expose FastAPI endpoints: `POST /report-runs`, `GET /report-runs/{id}`.
5. API contract tests must cover success, source-failure, and unknown-evidence cases.

## Verification commands (Lane D specific)

```bash
pytest backend/tests/reports/ backend/tests/api/ -v
mypy backend/app/reports backend/app/api
.\scripts\verify.ps1
docker compose up -d db
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1  # full L2 gate
```

## Stop conditions

Stop and record a blocker in `state/lane-d-state.md` if:
- Lane A's SQLAlchemy ORM models are not yet ready for integration.
- Lane C's EvidenceService does not yet accept SourceExistsProtocol/AreaExistsProtocol.
- The first MVP report requires a jurisdiction decision that has not been made.
- Docker/PostGIS is not available for integration testing.
