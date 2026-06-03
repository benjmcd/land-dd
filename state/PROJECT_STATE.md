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
- cd backend && PYTHONPATH=. python -m pytest tests/evidence_ledger/ tests/claims_engine/ -v
- python scripts/seed_sources.py
- python scripts/seed_sources.py --json
Verification result:
- 117 tests pass; lint clean; mypy clean (60 source files)
- Lane A source seeds validate 8 `Must` registry rows without DB access
- Lane A source governance fields, license review template, provenance ADR, and fail-closed production-use check are present
- Lane B in-memory area/geometry fixture slice passes targeted runtime and type checks
- Lane C in-memory evidence/claim/rule-engine slices pass targeted runtime, type, lint, and import-isolation checks
- DB smoke skipped/blocked because Docker Desktop is not running
Failed or blocked gates:
- L2-001 to L2-010: BLOCKED (Docker Desktop not running)
- L3-001/L3-002/L3-005: PARTIAL (source metadata/seeds/caveats and review fields exist; persisted review workflow pending)
- L3-003/L3-004: PARTIAL/BLOCKED (source versions/retrieval runs present in schema, not behavior-verified)
- L3-007: PARTIAL (SourceService fails closed for production use; DB/live connector enforcement unverified)
- L3-010: PARTIAL (license review template exists; source metadata export/review workflow not implemented)
- L4-001/L4-002/L4-006/L4-007: PARTIAL (in-memory geometry validation and caveats exist)
- L4-008: PASS for current fixture scope (polygon, multipolygon, invalid, empty, wrong SRID, and large geometry)
- L4-003: PARTIAL (AreaContract defaults to SRID 4326; persisted SRID still pending)
- L4-004/L4-005/L4-010: BLOCKED/PENDING (PostGIS-backed metrics, spatial queries, and versioned geometry)
- L5-001/L5-002/L5-003/L5-004/L5-007/L5-008: PARTIAL/PASS for in-memory evidence service scope
- L5-010: PARTIAL/PASS for in-memory service scope (observation, source-failure, human-note, and supersede paths emit evidence audit events; durable audit persistence remains DB-blocked)
- L5-006: PARTIAL/PASS for in-memory service scope (supersession marks original without deleting or overwriting)
- L6-001/L6-004/L6-006/L6-007: PARTIAL/PASS for in-memory claim/rule scope (stored claims require evidence links, unknown claims require source-failure evidence, severity/confidence stay separate, and verification tasks are enforced when required)
- L6-002/L6-003/L6-010: PARTIAL/PASS for one flood hard-gate rule (ruleset ID/version load, deterministic claim IDs, and rule logic lives in `rule_engine.py`, not an LLM/UI prompt)
- L6-005/L6-008/L6-009: PARTIAL/PASS for current flood-rule scope (rule-generated flood claims propagate caveats and cover positive, negative/no-claim, unknown/source-failure, explicit stale fixture signal, contradiction/needs-review, superseded-evidence, empty-input, multi-area, input-order-determinism, and invalid-rule-config cases; broader rule domains pending)
Completion evidence:
- state/VALIDATION_LOG.md
- backend/tests/source_registry/ (28 tests)
- backend/tests/area_geometry/ (16 tests)
- backend/tests/evidence_ledger/ and backend/tests/claims_engine/ (69 tests)
- db/seeds/source_registry_seeds.py
- scripts/seed_sources.py
- docs/adr/lane-a-0001-provenance-model.md
- templates/data_source_license_review.md
- registers/data_source_registry.csv
- schemas/source_schema.json
- tests/fixtures/geometries/
Next lowest-dependency task:
- Lane A: TA-060 DB smoke (blocked until Docker/PostGIS is available)
- Lane D: TD-020 (thin routers) is the next unblocked vertical-slice integration step; TD-030 report integration should stay fixture-only until DB persistence gaps are addressed
- Lane C: TC-080 (broader fixture hard-gate coverage) can proceed in parallel if integration is not prioritized
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

117 tests pass; lint clean; mypy clean (60 source files). DB smoke blocked until Docker Desktop starts.

## Local repo bootstrap state

- Local Git initialized on `main`.
- `origin` is configured as `https://github.com/benjmcd/land-dd.git`.
- Local baseline commit exists on `main`: `ffb73e1` (`Establish governed scaffold baseline`).
- No GitHub push has been performed; `origin/main` remains at `13b75a9`.
- Local Codesight index exists at `.codesight/`; regenerate after significant code changes.

