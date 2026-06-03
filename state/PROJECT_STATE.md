# Project State

## MILESTONE_MAP status block

```text
Current milestone: Level 1 — Governed Repo Scaffold
Milestone status: PARTIAL
Last verified: 2026-06-03
Verification command(s):
- ./scripts/verify.sh
- pytest backend/tests/ -v (22 tests)
Verification result:
- 22 tests pass; lint clean; mypy clean (44 source files)
- DB smoke blocked (Docker Desktop not running)
Failed or blocked gates:
- L2-001 to L2-010: BLOCKED (Docker Desktop not running)
- L3-001 to L3-010: PARTIAL (source contract + in-memory service done; DB/seeds pending)
Completion evidence:
- state/VALIDATION_LOG.md
- backend/tests/source_registry/ (11 tests)
Next lowest-dependency task:
- Lane A: TA-010 (clean up shims) → TA-020 (ORM model)
- Lane B: TB-010 (AreaService + InMemoryAreaRepository)
- Lane C: TC-010 (EvidenceService + InMemoryEvidenceRepository)
- Lane D: TD-020 (API scaffold — thin routers)
Do not work on yet:
- Live connectors
- UI or LLM summaries
- Production ops/security/observability
- New jurisdictions or intents until Level 4-5 DB gates pass
```

---

## Current objective

Build the foundation vertical slice for the land/locality due-diligence compiler:

```text
source registry -> area geometry -> evidence -> claim -> report run -> API response
```

## Active plan (overall)

`plans/2026-06-03-foundation-vertical-slice.md`

## 4-lane agent architecture (active)

This workspace uses 4 isolated agent lanes, each with dedicated scope, plans, and state files.
See `LANE_OWNERSHIP.md` for ownership boundaries.

| Lane | Scope | Active plan | State | Milestone gates |
|---|---|---|---|---|
| Lane A | Source Registry + DB Infrastructure | `plans/lane-a-2026-06-03-source-registry.md` | `state/lane-a-state.md` | L2-*, L3-* |
| Lane B | Area + Geometry Domain | `plans/lane-b-2026-06-03-area-geometry.md` | `state/lane-b-state.md` | L4-* |
| Lane C | Evidence Ledger + Claims Engine | `plans/lane-c-2026-06-03-evidence-claims.md` | `state/lane-c-state.md` | L5-*, L6-* |
| Lane D | Reports + API + Platform | `plans/lane-d-2026-06-03-reports-api-infra.md` | `state/lane-d-state.md` | L7-* |

**Each lane agent must read `LANE_OWNERSHIP.md` before any code change.**

## Key constraints

- Bottom-up implementation only.
- Postgres/PostGIS is system of record.
- Evidence-before-claim invariant is non-negotiable.
- No live data connectors before license/source registry/fixture tests.
- No UI or LLM work until the storage/evidence/claim/report spine works.
- Lane agents MUST NOT modify files owned by other lanes.

## Known blockers / undecided items

| Item | Status | Impact |
|---|---|---|
| MVP state/counties | Undecided | Do not hard-code jurisdiction-specific logic |
| Parcel vendor | Undecided | Use fixtures/public source registry only |
| Live connector credentials | Unavailable | No live API/vendor integrations |
| Docker availability | Not running | DB smoke blocked for all lanes |

## Last verified state

22 tests pass; lint clean; mypy clean (44 source files). DB smoke blocked until Docker Desktop starts.

## Local repo bootstrap state

- Local Git initialized on `main`.
- `origin` is configured as `https://github.com/benjmcd/land-dd.git`.
- No local commit or GitHub push has been performed.
- Local Codesight index exists at `.codesight/`; regenerate after significant code changes.

