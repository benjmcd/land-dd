# Project State

## MILESTONE_MAP status block

```text
Current milestone: Level 1 — Governed Repo Scaffold
Milestone status: PASS
Last verified: 2026-06-03
Verification command(s):
- C:/Program Files/Git/bin/bash.exe ./scripts/verify.sh
- cd backend && PYTHONPATH=. python -m pytest tests/source_registry/ -v
- cd backend && PYTHONPATH=. python -m pytest tests/area_geometry/ -v
- python scripts/seed_sources.py
- python scripts/seed_sources.py --json
Verification result:
- 49 tests pass; lint clean; mypy clean (48 source files)
- Lane A source seeds validate 8 `Must` registry rows without DB access
- Lane B in-memory area/geometry fixture slice passes targeted runtime and type checks
- DB smoke skipped/blocked because Docker Desktop is not running
Failed or blocked gates:
- L2-001 to L2-010: BLOCKED (Docker Desktop not running)
- L3-001/L3-002/L3-005: PARTIAL (source metadata/seeds/caveats exist; license review workflow pending)
- L3-003/L3-004: PARTIAL/BLOCKED (source versions/retrieval runs present in schema, not behavior-verified)
- L4-001/L4-002/L4-006/L4-007: PARTIAL (in-memory geometry validation and caveats exist)
- L4-008: PASS for current fixture scope (polygon, multipolygon, invalid, empty, wrong SRID, and large geometry)
- L4-003: PARTIAL (AreaContract defaults to SRID 4326; persisted SRID still pending)
- L4-004/L4-005/L4-010: BLOCKED/PENDING (PostGIS-backed metrics, spatial queries, and versioned geometry)
Completion evidence:
- state/VALIDATION_LOG.md
- backend/tests/source_registry/ (23 tests)
- backend/tests/area_geometry/ (16 tests)
- db/seeds/source_registry_seeds.py
- scripts/seed_sources.py
- tests/fixtures/geometries/
Next lowest-dependency task:
- Lane A: TA-050 (license review template and provenance ADR)
- Lane C: TC-010 (EvidenceService + InMemoryEvidenceRepository)
- Lane D: TD-020 (thin routers) after services are ready enough to expose safely
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

49 tests pass; lint clean; mypy clean (48 source files). DB smoke blocked until Docker Desktop starts.

## Local repo bootstrap state

- Local Git initialized on `main`.
- `origin` is configured as `https://github.com/benjmcd/land-dd.git`.
- Local baseline commit exists on `main`: `ffb73e1` (`Establish governed scaffold baseline`).
- No GitHub push has been performed; `origin/main` remains at `13b75a9`.
- Local Codesight index exists at `.codesight/`; regenerate after significant code changes.

