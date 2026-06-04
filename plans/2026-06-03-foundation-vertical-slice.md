# Foundation Vertical Slice

## Goal

Build the lowest-layer working product spine:

```text
source registry -> area geometry -> evidence -> claim -> report run -> API response
```

A fresh agent should be able to continue this plan without chat history.

## Non-goals

- No frontend.
- No live source connectors.
- No paid/commercial data.
- No LLM extraction.
- No global legal-grade coverage.
- No final legal/appraisal/investment conclusions.

## Current state

- Root governance is in `AGENTS.md` and `CLAUDE.md`.
- Durable architecture is in `docs/ARCHITECTURE.md`.
- Initial SQL spine exists in `db/migrations/0001_initial_spine.sql`.
- Backend scaffold has health/version endpoints and domain contracts.
- Existing tests check health endpoints and basic source/evidence/claim contracts.

## Proposed design

Implement fixture-backed behavior before live connectors. Use Postgres/PostGIS schema as the storage spine and Pydantic contracts as the API/domain boundary. Claims must be derived from evidence IDs, even for fixture data.

## Bottom-up sequence

1. Verify workspace and test commands.
2. Ensure DB migration applies locally and smoke test checks extensions/tables.
3. Add repository/service layer for sources and areas.
4. Add evidence creation service with explicit failure evidence.
5. Add claim creation service enforcing evidence IDs.
6. Add report-run service storing area + intent + ruleset/source metadata.
7. Add API endpoints around the services.
8. Add fixture connector for one synthetic area and deterministic evidence.
9. Add rule-engine slice for one or two red flags.
10. Add report response with evidence-linked claims and unknowns.

## Files likely to change

| File | Expected change |
|---|---|
| `backend/app/domain/**` | domain contracts and validation |
| `backend/app/db/**` | DB session/repository helpers |
| `backend/app/api/**` | thin endpoint adapters |
| `backend/tests/**` | contract, service, API tests |
| `db/migrations/**` | schema updates when necessary |
| `db/seeds/**` | source/intent/ruleset seeds |
| `config/ruleset_homestead_mvp.yaml` | deterministic rule slice |
| `state/**` | progress/validation updates |

## Tests / verification

```bash
./scripts/agent-context-check.sh
./scripts/validate_workspace.sh
cd backend && PYTHONPATH=. python -m pytest -q
.\scripts\verify.ps1
```

Optional DB verification:

```bash
docker compose up -d db
.\scripts\db_apply_migrations.ps1
python scripts/db_smoke_check.py
```

## Risks and blockers

- DB smoke requires Docker.
- Live data sources are intentionally blocked until fixture behavior, license review, and source registry entries exist.
- The first MVP state/county is undecided; do not hard-code one without a decision.
- The current API is a scaffold; do not pretend it is product-complete.

## Decision log

- 2026-06-03: Use fixture-backed vertical slice before live data.
- 2026-06-03: Keep UI and LLM features out of this plan.

## Progress log

- 2026-06-03: Initial plan created with dual Codex/Claude governance.
- 2026-06-03: Baseline lint fixed (3 ruff errors). mypy installed and passing.
- 2026-06-03: T010 blocked — Docker Desktop not running. Recorded in VALIDATION_LOG.
- 2026-06-03: T020 complete — `SourceRepository` Protocol, `InMemorySourceRepository`,
  `SourceService`, 8 fixture-backed tests. verify.sh: 14 tests / lint / mypy all clean.
- 2026-06-03: 4-lane scaffold complete. Work split into lane-specific plans. This plan is
  superseded by the 4-lane architecture. Continue in per-lane plans: lane-a-*.md etc.
