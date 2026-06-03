# Lane C State — Evidence Ledger + Claims Engine

```text
Current milestone: Level 1 — Governed Repo Scaffold (Lane C scaffold complete)
Target milestone: Level 5 (Evidence Ledger) → Level 6 (Claims Engine)
Milestone status: NOT_STARTED
Last verified: 2026-06-03
Verification command(s):
- pytest backend/tests/evidence_ledger/ backend/tests/claims_engine/ -v
- mypy backend/app/evidence_ledger backend/app/claims_engine
  backend/app/domain/evidence_contracts.py backend/app/domain/claim_contracts.py
- grep -r "from app.source_registry" backend/app/evidence_ledger/ backend/app/claims_engine/
- grep -r "from app.area_geometry" backend/app/evidence_ledger/ backend/app/claims_engine/
- ./scripts/verify.sh
Verification result:
- 6 Lane C contract tests passing; greps return 0 matches (isolation clean)
Failed or blocked gates:
- All L5 gates: NOT_STARTED (EvidenceService not yet implemented)
- All L6 gates: NOT_STARTED (ClaimService not yet implemented)
Completion evidence:
- plans/lane-c-2026-06-03-evidence-claims.md
- backend/app/domain/evidence_contracts.py (EvidenceContract)
- backend/app/domain/claim_contracts.py (ClaimContract, with evidence_ids enforced)
- backend/tests/evidence_ledger/test_evidence_contracts.py (3 passing)
- backend/tests/claims_engine/test_claim_contracts.py (3 passing)
Next lowest-dependency task:
- TC-010: Implement EvidenceService + InMemoryEvidenceRepository
Do not work on yet:
- Cross-lane integration wiring (Lane D's job)
- PostGIS evidence-geometry linkage (needs Lane A + Lane B DB work)
- Any Lane A/B/D files
```

## Known blockers

| Item | Status | Impact |
|---|---|---|
| SourceExistsProtocol real impl | Pending | Lane A SourceService does not yet expose SourceExistsProtocol methods; TC-010 uses stub; full integration in Lane D |
| AreaExistsProtocol real impl | Available for in-memory wiring | Lane B AreaService exposes `area_is_registered`; full integration remains Lane D's job |
| Jurisdiction for rules | Undecided | Use fixture rules only |

## Active plan

`plans/lane-c-2026-06-03-evidence-claims.md`

## Lane-specific verification commands

```bash
# Lane C unit tests only:
cd backend && PYTHONPATH=. pytest tests/evidence_ledger/ tests/claims_engine/ -v

# Cross-lane import isolation check (must return 0 matches each):
grep -r "from app.source_registry" backend/app/evidence_ledger/ backend/app/claims_engine/
grep -r "from app.area_geometry" backend/app/evidence_ledger/ backend/app/claims_engine/

# Lane C type check:
cd backend && mypy app/evidence_ledger app/claims_engine \
  app/domain/evidence_contracts.py app/domain/claim_contracts.py

# Full workspace gate:
./scripts/verify.sh
```
