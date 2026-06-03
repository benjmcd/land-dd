# Lane C State — Evidence Ledger + Claims Engine

```text
Current milestone: Level 6 - Claims Engine (in-memory flood/access/wetlands rule slice)
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
- 83 Lane C tests passing
- Lane C targeted ruff and mypy pass
- Cross-lane import scans return 0 matches (isolation clean)
- Full verification passes: 138 tests; lint clean; mypy clean (67 source files)
Failed or blocked gates:
- L5-001/L5-003/L5-004/L5-007/L5-008: PARTIAL/PASS for in-memory service scope (provenance checks, source failure records, area linkage, typed human notes, area/source/type retrieval)
- L5-002: PARTIAL/PASS for in-memory service scope (type-specific observed_value validation covers source observation, spatial intersection, derived metric, document extract, source failure, and human-note guardrails)
- L5-005: PARTIAL (confidence/caveat/method/temporal fields exist; spatial precision not implemented)
- L5-006: PARTIAL/PASS for in-memory service scope (supersession marks original and stores replacement without silent overwrite)
- L5-010: PARTIAL/PASS for in-memory service scope (observation, source-failure, human-note, and supersede paths emit audit events; durable audit persistence remains DB-blocked)
- L6-001: PARTIAL/PASS for in-memory service/rule scope (ClaimService refuses missing, empty, duplicate, mismatched, superseded, and cross-area evidence links; rule-generated claims cite evidence IDs)
- L6-004: PARTIAL/PASS for in-memory service scope (create_unknown requires source-failure evidence)
- L6-005: PARTIAL/PASS for current flood/access/wetlands rule scope (positive, unknown, needs-review, and stale-review claims propagate evidence caveats; zoning/slope/water pending)
- L6-006: PASS for current contract/service scope (severity and confidence remain separate)
- L6-007: PARTIAL/PASS for in-memory service scope (ClaimService requires verification_task when verification_required is true)
- L6-002: PARTIAL/PASS for current rule-engine scope (ruleset ID/version load from `config/ruleset_homestead_mvp.yaml` and are copied into generated flood/access/wetlands claims)
- L6-003: PARTIAL/PASS for flood, access, and wetlands hard-gate rules (deterministic claim IDs and deterministic output when input order changes)
- L6-008: PARTIAL/PASS for current flood/access/wetlands rule scope (conflicting active evidence and positive-plus-source-failure evidence emit needs-review claims where implemented)
- L6-009: PARTIAL/PASS for current flood/access/wetlands rule scope (claim-service and rule-engine tests cover positive evidence-linked storage, negative/no-claim, unknown/source-failure, explicit stale fixture signal, contradiction/needs-review, superseded evidence, deterministic order, invalid rule config, and duplicate claim rejection; zoning/slope/water pending)
- L6-010: PARTIAL/PASS for current rule-engine scope (business logic lives in `backend/app/claims_engine/rule_engine.py`, not an LLM prompt or UI copy)
Completion evidence:
- plans/lane-c-2026-06-03-evidence-claims.md
- backend/app/evidence_ledger/evidence_repo.py (EvidenceRepository Protocol + InMemoryEvidenceRepository)
- backend/app/evidence_ledger/audit_log.py (EvidenceAuditEvent + InMemoryEvidenceAuditLog)
- backend/app/evidence_ledger/service.py (EvidenceService)
- backend/app/evidence_ledger/payload_validation.py (type-specific observed_value validators)
- backend/app/domain/evidence_contracts.py (EvidenceContract)
- backend/app/domain/claim_contracts.py (ClaimContract, with evidence_ids enforced)
- backend/app/claims_engine/claim_repo.py (ClaimRepository Protocol + InMemoryClaimRepository)
- backend/app/claims_engine/service.py (ClaimService)
- backend/app/claims_engine/rule_engine.py (RuleEngine + constrained ruleset loader)
- backend/tests/evidence_ledger/test_evidence_contracts.py (3 passing)
- backend/tests/evidence_ledger/test_evidence_service.py (17 passing)
- backend/tests/evidence_ledger/test_payload_validation.py (17 passing)
- backend/tests/evidence_ledger/test_evidence_audit.py (4 passing)
- backend/tests/claims_engine/test_claim_contracts.py (4 passing)
- backend/tests/claims_engine/test_claim_service.py (12 passing)
- backend/tests/claims_engine/test_rule_engine.py (26 passing)
Next lowest-dependency task:
- Plan the next hard-gate domain slice (zoning, slope, or water) before editing, or shift to Lane D TD-050 if integration is prioritized
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
