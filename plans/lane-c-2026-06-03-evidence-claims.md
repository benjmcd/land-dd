# Lane C — Evidence Ledger + Claims Engine

## Goal

Complete MILESTONE_MAP.md Levels 5-6: a durable, auditable evidence ledger and a deterministic, evidence-linked claims engine.

## Non-goals

- No source registry or area geometry work (Lane A/B).
- No live connectors.
- No LLM-generated claims.
- No report assembly or API (Lane D).

## Current state

- `EvidenceContract` in `backend/app/domain/evidence_contracts.py` (evidence_type, evidence_code, domain, observation, observed_value, source_id, method_code, confidence, caveat, is_source_failure, etc.).
- `ClaimContract` in `backend/app/domain/claim_contracts.py` (evidence_ids enforced, severity + confidence separate).
- `EvidenceType` enum in `backend/app/domain/enums.py`.
- `SourceExistsProtocol`, `AreaExistsProtocol` in `backend/app/domain/protocols.py`.
- `backend/app/evidence_ledger/` contains `EvidenceRepository`, `InMemoryEvidenceRepository`, and `EvidenceService`.
- `backend/app/claims_engine/` module directory exists (empty except package marker).
- `backend/tests/evidence_ledger/` and `backend/tests/claims_engine/` test directories exist.
- 16 tests in `backend/tests/evidence_ledger/` and `backend/tests/claims_engine/`.

## Non-negotiables from AGENTS.md

- Source failure MUST create evidence record — never silent.
- Evidence cannot be created without source_id + method_code.
- Claims cannot be created without at least one evidence_id.
- Confidence and severity are always separate.
- Evidence can be superseded but never silently overwritten.

## Proposed design

Cross-lane isolation via constructor-injected protocols: `EvidenceService(source_checker: SourceExistsProtocol, area_checker: AreaExistsProtocol)`. Tests use in-memory stubs. Production wiring is Lane D's job.

## Bottom-up sequence

### TC-010: Evidence repository and service
1. Create `backend/app/evidence_ledger/evidence_repo.py` with `EvidenceRepository` Protocol + `InMemoryEvidenceRepository`.
2. Create `backend/app/evidence_ledger/service.py` with `EvidenceService`.
3. `EvidenceService.__init__` takes `repo`, `source_checker: SourceExistsProtocol`, `area_checker: AreaExistsProtocol`.
4. `create_observation(evidence: EvidenceContract) -> EvidenceContract`: validates source registered + production-allowed + area registered, stores.
5. `create_source_failure(area_id, source_id, method_code, caveat) -> EvidenceContract`: creates `is_source_failure=True` record.
6. `create_human_note(evidence: EvidenceContract) -> EvidenceContract`: stores typed manual/human verification notes separately from source observations.
7. `get(evidence_id)`, `list_by_area(area_id)`, `list_by_source(source_id)`, `list_by_type(evidence_type)`.
8. Tests: happy path, source failure, human note, source-not-registered rejection, disallowed-source rejection, area-not-registered rejection, duplicate rejection.

### TC-020: Evidence supersession
1. Add `supersede(evidence_id, replacement: EvidenceContract) -> EvidenceContract` to service.
2. Original evidence is marked superseded (add `superseded_by: UUID | None` field to `EvidenceContract`).
3. Tests: supersession creates new record; original is not deleted; both are retrievable.

### TC-030: Claim repository and service
1. Create `backend/app/claims_engine/claim_repo.py` with `ClaimRepository` Protocol + `InMemoryClaimRepository`.
2. Create `backend/app/claims_engine/service.py` with `ClaimService`.
3. `ClaimService.create_claim(claim: ClaimContract, evidence_ids: list[UUID]) -> ClaimContract`: validates all evidence_ids exist in the evidence repo.
4. `ClaimService.create_unknown(area_id, claim_code, reason, evidence_ids)`: creates unknown/blocker claim from source-failure evidence.
5. Tests: evidence-linked claim, empty-evidence rejection, unknown claim from source failure.

### TC-040: YAML rules engine slice
1. Create `backend/app/claims_engine/rule_engine.py` that loads `config/ruleset_homestead_mvp.yaml`.
2. Implement `evaluate(evidence_list: list[EvidenceContract]) -> list[ClaimContract]` for ONE rule (e.g., flood_screen).
3. Rule must be deterministic for fixed inputs (L6-003).
4. Tests: positive evidence → positive claim; failure evidence → unknown claim.

## Files likely to change

| File | Expected change |
|---|---|
| `backend/app/evidence_ledger/evidence_repo.py` | New: EvidenceRepository + InMemoryEvidenceRepository |
| `backend/app/evidence_ledger/service.py` | New: EvidenceService |
| `backend/app/claims_engine/claim_repo.py` | New: ClaimRepository + InMemoryClaimRepository |
| `backend/app/claims_engine/service.py` | New: ClaimService |
| `backend/app/claims_engine/rule_engine.py` | New: YAML rules engine |
| `backend/app/domain/evidence_contracts.py` | Possible: add superseded_by field |
| `config/ruleset_homestead_mvp.yaml` | Add/extend rule definitions |
| `state/lane-c-state.md` | Update after each task |

## Tests / verification

```bash
pytest backend/tests/evidence_ledger/ backend/tests/claims_engine/ -v
mypy backend/app/evidence_ledger backend/app/claims_engine \
     backend/app/domain/evidence_contracts.py backend/app/domain/claim_contracts.py
# Verify cross-lane import isolation:
grep -r "from app.source_registry" backend/app/evidence_ledger/ backend/app/claims_engine/
grep -r "from app.area_geometry" backend/app/evidence_ledger/ backend/app/claims_engine/
./scripts/verify.sh
```

## Risks and blockers

| Blocker | Status | Impact |
|---|---|---|
| SourceExistsProtocol needs real implementation | Available for in-memory wiring | Lane A SourceService exposes source existence and fail-closed production-use checks; integration wiring remains Lane D's job |
| AreaExistsProtocol needs real implementation | Available for in-memory wiring | Lane B AreaService exposes `area_is_registered`; integration wiring remains Lane D's job |
| New EvidenceType value | Requires shared enums.py change | Stop and record blocker |
| YAML rules engine needs jurisdiction | Undecided | Use fixture rules only; do not hard-code state |

## Decision log

- 2026-06-03: Lane C owns evidence ledger + claims engine (MILESTONE Levels 5-6).
- 2026-06-03: Cross-lane validation via Protocol injection — never import from source_registry or area_geometry.
- 2026-06-03: Evidence supersession adds superseded_by field (not silent overwrite).

## Progress log

- 2026-06-03: Lane scaffold created. EvidenceContract + ClaimContract in per-lane files. 6 contract tests passing.
- 2026-06-03: TC-010 complete for the in-memory evidence slice. Added `EvidenceRepository`, `InMemoryEvidenceRepository`, and `EvidenceService` with source/area protocol validation, production-use rejection for observations, source-failure evidence creation, typed human notes, retrieval by area/source/type, and duplicate evidence protection. Lane C tests: 16 passing. Full verification: 64 tests, ruff clean, mypy clean (51 source files); DB smoke skipped.
