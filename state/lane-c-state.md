# Lane C State — Evidence Ledger + Claims Engine

```text
Current milestone: Level 6 - Claims Engine
Target milestone: Level 5 (Evidence Ledger) → Level 6 (Claims Engine)
Milestone status: PASS for Lane C claim/rule scope
Last verified: 2026-06-04
Verification command(s):
- $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/evidence_ledger
- $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/evidence_ledger tests/claims_engine
- $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/claims_engine
- py -3.12 -m pytest -q tests/reports tests/api
- ruff check app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
- ruff check app/claims_engine tests/claims_engine
- mypy app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
- mypy app/claims_engine tests/claims_engine
- rg -n "from app\.source_registry|from app\.area_geometry|import app\.source_registry|import app\.area_geometry" app/evidence_ledger app/claims_engine
- py -3.12 -m pytest --collect-only -q
- python scripts/db_smoke_check.py
- $env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
Verification result:
- 153 Lane C evidence/claims tests pass with DB smoke enabled
- Lane C targeted ruff and mypy pass
- Cross-lane import scans return 0 matches (isolation clean)
- Full PowerShell verification passes with DB smoke enabled: 326 tests; lint clean; mypy clean (118 source files); migrations/seeds apply; DB smoke passes
- C-001 claims ORM persistence is stable on the current main base after removing cross-schema ORM FK metadata assumptions and flushing the parent claim before child link/task rows
- TC-180 source-failure evidence identity preservation is stable for the Lane C public service path: `EvidenceService.create_source_failure(...)` preserves a supplied evidence ID through in-memory and SQLAlchemy-backed storage while still rejecting duplicates
Failed or blocked gates:
- L5-001 through L5-010: PASS for DB-backed repository/service scope (`SqlAlchemyEvidenceRepository` persists source observations, source failures, spatial intersections, derived metrics, document extracts, human verification notes, optional geometry/SRID/spatial precision, invalid payload rejection, supersession, deterministic retrieval, rollback behavior, and `SqlAlchemyEvidenceAuditLog` durable audit events; `docs/adr/lane-c-evidence.md` documents immutability/amendment policy)
- L6-001: PASS for current DB-backed service/repository scope (ClaimService refuses missing, empty, duplicate, mismatched, superseded, and cross-area evidence links; `SqlAlchemyClaimRepository` persists claims plus `claims.claim_evidence` links via ORM models `ClaimModel`/`ClaimEvidenceLinkModel`/`VerificationTaskModel`; rule-generated claims cite evidence IDs)
- L6-004: PASS for current DB-backed service/repository scope (create_unknown requires source-failure evidence; not-evaluated categories emit UNKNOWN claims only from source-failure evidence; unknown claims persist with evidence links)
- L6-005: PASS for current rule scope (positive, unknown, needs-review, stale-review, and not-evaluated claims propagate evidence caveats)
- L6-006: PASS for current contract/service scope (severity and confidence remain separate)
- L6-007: PASS for current DB-backed service/repository scope (ClaimService requires verification_task when verification_required is true; rule-generated not-evaluated claims include verification tasks; `SqlAlchemyClaimRepository` persists verification tasks to `claims.verification_tasks`)
- L6-002: PASS for current rule-engine scope (ruleset ID/version load from `config/ruleset_homestead_mvp.yaml` and are copied into generated flood/access/zoning/water/wetlands/slope/not-evaluated claims)
- L6-003: PASS for flood, access, zoning, water, wetlands, slope, and not-evaluated hard-gate rules (deterministic claim IDs and deterministic output when input order changes)
- L6-008: PASS for current rule scope (conflicting active evidence, incomplete active evidence, positive-plus-source-failure evidence, and unsupported-domain source failures produce review or unknown claims where appropriate)
- L6-009: PASS for current rule scope (claim-service and rule-engine tests cover positive evidence-linked storage, negative/no-claim, unknown/source-failure, explicit stale fixture signal, contradiction/needs-review, incomplete evidence, superseded evidence, deterministic order, invalid rule config, duplicate claim rejection, and not-evaluated unsupported-domain cases)
- L6-010: PASS for current rule-engine scope (business logic lives in `backend/app/claims_engine/rule_engine.py` and `config/ruleset_homestead_mvp.yaml`, not an LLM prompt or UI copy)
Completion evidence:
- plans/lane-c-2026-06-03-evidence-claims.md
- backend/app/evidence_ledger/evidence_repo.py (EvidenceRepository Protocol + InMemoryEvidenceRepository + SqlAlchemyEvidenceRepository)
- backend/app/evidence_ledger/audit_log.py (EvidenceAuditEvent + InMemoryEvidenceAuditLog + SqlAlchemyEvidenceAuditLog)
- backend/app/evidence_ledger/service.py (EvidenceService)
- backend/app/evidence_ledger/payload_validation.py (type-specific observed_value validators)
- backend/app/domain/evidence_contracts.py (EvidenceContract)
- backend/app/domain/claim_contracts.py (ClaimContract, with evidence_ids enforced)
- schemas/evidence_schema.json (canonical serialized EvidenceContract schema)
- schemas/claim_schema.json (canonical serialized ClaimContract schema)
- docs/adr/lane-c-schemas.md (schema-contract ADR)
- backend/app/claims_engine/models.py (ClaimModel, ClaimEvidenceLinkModel, VerificationTaskModel — ORM models; C-001 DONE)
- backend/app/claims_engine/claim_repo.py (ClaimRepository Protocol + InMemoryClaimRepository + SqlAlchemyClaimRepository using ORM models)
- backend/app/claims_engine/not_evaluated.py (unsupported-domain constants and source-failure evidence helper)
- backend/app/claims_engine/service.py (ClaimService)
- backend/app/claims_engine/rule_engine.py (RuleEngine + constrained ruleset loader)
- backend/tests/evidence_ledger/test_evidence_contracts.py (6 passing)
- backend/tests/evidence_ledger/test_evidence_schema_contract.py (schema-contract parity tests)
- backend/tests/evidence_ledger/test_evidence_service.py (19 passing)
- backend/tests/evidence_ledger/test_payload_validation.py (23 passing)
- backend/tests/evidence_ledger/test_evidence_audit.py (4 passing)
- backend/tests/evidence_ledger/test_sqlalchemy_evidence_repo.py (12 passing)
- docs/adr/lane-c-evidence.md (evidence persistence/immutability/amendment ADR)
- backend/tests/claims_engine/test_claim_contracts.py (4 passing)
- backend/tests/claims_engine/test_claim_schema_contract.py (schema-contract parity tests)
- backend/tests/claims_engine/test_claim_service.py (12 passing)
- backend/tests/claims_engine/test_rule_engine.py (48 passing)
- backend/tests/claims_engine/test_not_evaluated_claims.py (6 passing)
- backend/tests/claims_engine/test_sqlalchemy_claim_repo.py (4 passing)
- docs/adr/lane-c-rules.md (rules and claim persistence ADR)
Next lowest-dependency task:
- **C-001: DONE and DB-gated stable on current main** - `backend/app/claims_engine/models.py` created; `SqlAlchemyClaimRepository` refactored to ORM; ORM metadata/flush ordering repaired and verified with DB-gated claim tests.
- **C-002: DONE for Lane C-owned rule/claim scope** - `RuleEngine.evaluate()` emits deterministic UNKNOWN claims for soil/septic, environmental hazards, resource context, and market context when provided stored source-failure evidence.
- **TC-170: DONE for canonical Lane C schema/contract scope** - `schemas/evidence_schema.json` and `schemas/claim_schema.json` mirror serialized `EvidenceContract` and `ClaimContract` fields and enums; `docs/adr/lane-c-schemas.md` records the shared-schema decision.
- **TC-180: DONE for Lane C public source-failure identity preservation** - `EvidenceService.create_source_failure(...)` accepts an optional `evidence_id`, preserves it through in-memory and DB-backed storage, and rejects duplicates without overwrite.
- **Next repo-wide dependency**: durable `ingest_run_id` evidence-row linkage remains a future coordinated connector/Lane C/schema pass after CON-019 connector-zone source-failure ID adoption.
Do not work on yet:
- D-001 cross-lane wiring (Lane D owns `api/dependencies.py`, `main.py`, and `db/session.py`)
- Live connectors, jurisdiction-specific rules, or UI/LLM summarization
- Any Lane A/B/D files
```

## Known blockers

| Item | Status | Impact |
|---|---|---|
| SourceExistsProtocol real impl | Available for in-memory wiring | Lane A SourceService exposes source existence and fail-closed production-use checks; full integration remains Lane D's job |
| AreaExistsProtocol real impl | Available for in-memory wiring | Lane B AreaService exposes `area_is_registered`; full integration remains Lane D's job |
| Jurisdiction for rules | Undecided | Use fixture rules only |
| Evidence geometry/spatial precision | Closed for Level 5 | `EvidenceContract` exposes optional GeoJSON/SRID/spatial-precision fields; `SqlAlchemyEvidenceRepository` maps geometry to `evidence.observations.geometry` and precision to metadata |
| Minimum rule categories | Closed for Lane C | Soil/septic, environmental hazards, resource context, and market context emit evidence-backed not-evaluated UNKNOWN claims when source-failure evidence is supplied; report-run source-failure injection remains Lane D integration |
| Planning-pack evidence/claim schema copies | Closed | `docs/planning_pack/schemas/evidence_schema.json` and `docs/planning_pack/schemas/claim_schema.json` mirror the canonical root Lane C schemas; `backend/tests/test_planning_pack_schema_copies.py` guards against silent drift |
| Connector source-failure evidence ID preservation | Lane C public service side closed; CON-019 connector adoption complete in Session 2 integration branch | Durable `ingest_run_id` evidence-row linkage remains a future coordinated connector/Lane C/schema pass |

## Active plan

`plans/lane-c-2026-06-03-evidence-claims.md`

## Lane-specific verification commands

```powershell
Set-Location backend
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/evidence_ledger tests/claims_engine
ruff check app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
mypy app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
rg -n "from app\\.source_registry|from app\\.area_geometry|import app\\.source_registry|import app\\.area_geometry" app/evidence_ledger app/claims_engine
Set-Location ..
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```
