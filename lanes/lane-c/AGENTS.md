# Lane C — Evidence Ledger + Claims Engine

You are the Lane C agent. Read this file first, then read the files listed below.

## Required startup reads

1. `../../AGENTS.md` — root operating contract (always applies)
2. `../../MILESTONE_MAP.md` — authoritative maturity gates
3. `../../LANE_OWNERSHIP.md` — file ownership and isolation rules
4. `../../state/lane-c-state.md` — current Lane C state and next task
5. The active plan referenced in `state/lane-c-state.md`

## Your scope

You own MILESTONE_MAP.md Levels 5-6: Evidence Ledger and Claims + Rules Engine.

## Your milestone gates

| Level | Gates | Pass condition |
|---|---|---|
| L5 | L5-001 to L5-010 | Evidence cannot be stored without provenance; source failure stored as evidence; evidence is auditable; human notes separate from observations |
| L6 | L6-001 to L6-010 | No claim without evidence; rules versioned; deterministic output; unknown/blocker claims generated; contradiction handling |

## Your owned directories and files

See `LANE_OWNERSHIP.md` Lane C section for the full list.

Key:
- `backend/app/evidence_ledger/` — evidence module code
- `backend/app/claims_engine/` — claims and rules engine code
- `backend/app/domain/evidence_contracts.py` — EvidenceContract (you own this)
- `backend/app/domain/claim_contracts.py` — ClaimContract (you own this)
- `backend/tests/evidence_ledger/` + `backend/tests/claims_engine/` — Lane C tests
- `config/ruleset_homestead_mvp.yaml` — ruleset definitions

## What you MUST NOT touch

- `backend/app/source_registry/` (Lane A)
- `backend/app/area_geometry/` (Lane B)
- `backend/app/reports/` or `api/` (Lane D)
- Any other lane's plans, state, or ADR files

## Import constraint (CRITICAL)

You may import from: `app.domain.*`, `app.db.*`, `app.core.*`, `app.evidence_ledger.*`, `app.claims_engine.*`.

You MUST NOT import from: `app.source_registry`, `app.area_geometry`, `app.reports`.

For cross-lane validation, use ONLY the shared Protocol interfaces:
```python
from app.domain.protocols import SourceExistsProtocol, AreaExistsProtocol
```
Your services accept these as constructor parameters (dependency injection). Tests provide stubs.

## Non-negotiables

- Source failure MUST create an evidence record (L5-003, G-II-003). Missing data is never "no issue."
- Evidence CANNOT be created without source_id + method_code (L5-001, G-II-002).
- Claims CANNOT be created without at least one evidence_id (L6-001, G-II-001).
- Suitability and confidence are SEPARATE fields on ClaimContract (L6-006, G-II-004).
- Evidence can be superseded but not silently overwritten (L5-006).

## Verification commands (Lane C specific)

```bash
pytest backend/tests/evidence_ledger/ backend/tests/claims_engine/ -v
mypy backend/app/evidence_ledger backend/app/claims_engine \
     backend/app/domain/evidence_contracts.py backend/app/domain/claim_contracts.py
# Verify cross-lane import isolation:
grep -r "from app.source_registry" backend/app/evidence_ledger/ backend/app/claims_engine/
grep -r "from app.area_geometry" backend/app/evidence_ledger/ backend/app/claims_engine/
# Both greps must return 0 matches.
.\scripts\verify.ps1
```

## Stop conditions

Stop and record a blocker in `state/lane-c-state.md` if:
- The rules engine requires a new EvidenceType or ConfidenceBand (shared enums — cross-lane change needed).
- Claim generation requires spatial query results that depend on Lane B's PostGIS service.
- A rule requires jurisdiction-specific logic but no MVP jurisdiction is decided.
