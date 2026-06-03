# Lane C State — Evidence Ledger + Claims Engine

```text
Current milestone: Level 6 - Claims Engine (in-memory claim-service slice)
Target milestone: Level 5 (Evidence Ledger) → Level 6 (Claims Engine)
Milestone status: PARTIAL
Last verified: 2026-06-03
Verification command(s):
- pytest backend/tests/evidence_ledger/ backend/tests/claims_engine/ -v
- ruff check backend/app/evidence_ledger backend/app/claims_engine
  backend/app/domain/evidence_contracts.py backend/app/domain/claim_contracts.py
  backend/tests/evidence_ledger backend/tests/claims_engine
- mypy backend/app/evidence_ledger backend/app/claims_engine
  backend/app/domain/evidence_contracts.py backend/app/domain/claim_contracts.py
- rg -n "from app\.source_registry|from app\.area_geometry|import app\.source_registry|import app\.area_geometry" backend/app/evidence_ledger backend/app/claims_engine
- ./scripts/verify.sh
Verification result:
- 35 Lane C tests passing
- Lane C targeted ruff and mypy pass
- Cross-lane import scans return 0 matches (isolation clean)
- Full verification passes: 83 tests; lint clean; mypy clean (54 source files)
Failed or blocked gates:
- L5-001/L5-003/L5-004/L5-007/L5-008: PARTIAL/PASS for in-memory service scope (provenance checks, source failure records, area linkage, typed human notes, area/source/type retrieval)
- L5-002: NOT_STARTED (type-specific payload schema validation not implemented)
- L5-005: PARTIAL (confidence/caveat/method/temporal fields exist; spatial precision not implemented)
- L5-006: PARTIAL/PASS for in-memory service scope (supersession marks original and stores replacement without silent overwrite)
- L5-010: NOT_STARTED (audit events not implemented)
- L6-001: PARTIAL/PASS for in-memory service scope (ClaimService refuses missing, empty, duplicate, mismatched, and cross-area evidence links)
- L6-004: PARTIAL/PASS for in-memory service scope (create_unknown requires source-failure evidence)
- L6-005: PARTIAL (source-failure caveats propagate into generated unknown claims; broader rule-derived caveat propagation pending)
- L6-006: PASS for current contract/service scope (severity and confidence remain separate)
- L6-007: PARTIAL/PASS for in-memory service scope (ClaimService requires verification_task when verification_required is true)
- L6-002/L6-003/L6-008/L6-010: NOT_STARTED (versioned deterministic rules, contradiction handling, and non-LLM rule module pending)
- L6-009: PARTIAL (claim-service tests cover positive evidence-linked storage, missing/empty/duplicate/cross-area rejection, source-failure unknowns, and duplicate claim rejection; stale/contradiction/ruleset cases pending)
Completion evidence:
- plans/lane-c-2026-06-03-evidence-claims.md
- backend/app/evidence_ledger/evidence_repo.py (EvidenceRepository Protocol + InMemoryEvidenceRepository)
- backend/app/evidence_ledger/service.py (EvidenceService)
- backend/app/domain/evidence_contracts.py (EvidenceContract)
- backend/app/domain/claim_contracts.py (ClaimContract, with evidence_ids enforced)
- backend/app/claims_engine/claim_repo.py (ClaimRepository Protocol + InMemoryClaimRepository)
- backend/app/claims_engine/service.py (ClaimService)
- backend/tests/evidence_ledger/test_evidence_contracts.py (3 passing)
- backend/tests/evidence_ledger/test_evidence_service.py (17 passing)
- backend/tests/claims_engine/test_claim_contracts.py (3 passing)
- backend/tests/claims_engine/test_claim_service.py (12 passing)
Next lowest-dependency task:
- TC-040: YAML rules engine slice
Do not work on yet:
- Cross-lane integration wiring (Lane D's job)
- PostGIS evidence-geometry linkage (needs Lane A + Lane B DB work)
- Any Lane A/B/D files
```

## Known blockers

| Item | Status | Impact |
|---|---|---|
| SourceExistsProtocol real impl | Available for in-memory wiring | Lane A SourceService exposes source existence and fail-closed production-use checks; full integration remains Lane D's job |
| AreaExistsProtocol real impl | Available for in-memory wiring | Lane B AreaService exposes `area_is_registered`; full integration remains Lane D's job |
| Jurisdiction for rules | Undecided | Use fixture rules only |

## Active plan

`plans/lane-c-2026-06-03-evidence-claims.md`

## Lane-specific verification commands

```bash
# Lane C unit tests only:
cd backend && PYTHONPATH=. pytest tests/evidence_ledger/ tests/claims_engine/ -v

# Cross-lane import isolation check (must return 0 matches):
rg -n "from app\\.source_registry|from app\\.area_geometry|import app\\.source_registry|import app\\.area_geometry" \
  backend/app/evidence_ledger backend/app/claims_engine

# Lane C type check:
cd backend && mypy app/evidence_ledger app/claims_engine \
  app/domain/evidence_contracts.py app/domain/claim_contracts.py

# Full workspace gate:
./scripts/verify.sh
```
