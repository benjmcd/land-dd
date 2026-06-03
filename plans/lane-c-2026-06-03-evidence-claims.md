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
- `ClaimContract` in `backend/app/domain/claim_contracts.py` (evidence_ids enforced, severity + confidence separate, rule metadata fields).
- `EvidenceType` enum in `backend/app/domain/enums.py`.
- `SourceExistsProtocol`, `AreaExistsProtocol` in `backend/app/domain/protocols.py`.
- `backend/app/evidence_ledger/` contains `EvidenceRepository`, `InMemoryEvidenceRepository`, and `EvidenceService`.
- `backend/app/claims_engine/` contains `ClaimRepository`, `InMemoryClaimRepository`, `ClaimService`, and `RuleEngine`.
- `backend/tests/evidence_ledger/` and `backend/tests/claims_engine/` test directories exist.
- 76 tests in `backend/tests/evidence_ledger/` and `backend/tests/claims_engine/`.

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
6. Status: COMPLETE for the in-memory service slice. Service also rejects duplicate evidence IDs, mismatched supplied IDs, cross-area evidence links, missing user-safe language, missing verification tasks when required, unknown claims without source-failure evidence, and duplicate claim IDs.

### TC-040: YAML rules engine slice
1. Create `backend/app/claims_engine/rule_engine.py` that loads `config/ruleset_homestead_mvp.yaml`.
2. Implement `evaluate(evidence_list: list[EvidenceContract]) -> list[ClaimContract]` for one flood hard-gate rule.
3. Rule output is deterministic for fixed inputs and input order changes (L6-003).
4. Tests: positive evidence -> positive claim; failure evidence -> unknown claim.
5. Status: COMPLETE for one in-memory deterministic flood hard-gate slice. The loader supports the current ruleset YAML shape, not arbitrary YAML. Tests cover ruleset version loading, deterministic high-risk flood claims, source-failure unknowns, low-risk no-claim output, input-order determinism, empty input, multi-area grouping, invalid severity rejection, explicit positive-plus-failure output, and superseded evidence exclusion.

### TC-050: Evidence payload schema validation
1. Define evidence-type-specific observed_value validators for at least `source_observation`, `spatial_intersection`, `derived_metric`, and `source_failure`.
2. Keep validation in Lane C, before claim/rule use.
3. Reject arbitrary observed_value payloads with clear errors.
4. Tests: valid/invalid payloads for each covered evidence type.
5. Status: COMPLETE for the in-memory service slice. Validators cover source observations, spatial intersections, derived metrics, document extracts, source failures, and human-note observed_value guardrails. Spatial validation accepts `flood_zone_code` results and bounds `intersection_ratio` to `0..1`. The shared `schemas/evidence_schema.json` still needs a coordinated schema-alignment pass.

### TC-060: Evidence audit events
1. Add in-memory audit-event emission for evidence create/supersede paths.
2. Keep durable audit persistence blocked until DB smoke is available.
3. Tests: create/source-failure/human-note/supersede emit auditable events without overwriting evidence.
4. Status: COMPLETE for the in-memory service slice. `EvidenceService` now emits optional audit events for successful observation, source-failure, human-note, and supersede paths through `EvidenceAuditLog`. Durable audit persistence remains blocked until DB smoke and repository work are available.

### TC-070: Contradiction/needs-review and stale-evidence rule handling
1. Define the fixture-only stale-evidence signal without hard-coding a jurisdiction or live source policy.
2. Add deterministic rule handling for contradictory active evidence and source-failure-plus-positive evidence where a human review claim is required.
3. Add stale-evidence output that separates confidence from severity and cites the triggering evidence IDs.
4. Tests: contradiction, stale evidence, no stale false positive, superseded evidence ignored, and deterministic output ordering.
5. Status: COMPLETE for the in-memory flood-rule slice. The rule engine emits needs-review claims for conflicting flood evidence and positive-plus-source-failure evidence, emits stale-evidence review claims from an explicit `source_stale` fixture signal, ignores superseded evidence, and keeps deterministic ordering.

### TC-080: Broader fixture hard-gate coverage
1. Extend deterministic rule handling beyond the first flood hard gate using existing ruleset domains, without adding live vendors or jurisdiction-specific policy.
2. Add fixture evidence patterns for at least one next hard-gate domain.
3. Preserve evidence IDs, caveat propagation, severity/confidence separation, and verification tasks.
4. Tests: positive, negative/no-claim, source-failure/unknown, stale/review, and deterministic ordering for the added domain.
5. Status: COMPLETE for the access fixture hard-gate scope. The rule engine now covers flood and access hard-gate fixtures. Zoning, wetlands, slope, and water remain pending follow-on slices.

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
| YAML parser scope | Accepted for TC-040 | Current loader supports the checked-in ruleset shape only; broaden with an approved parser/dependency decision before complex YAML features |

## Decision log

- 2026-06-03: Lane C owns evidence ledger + claims engine (MILESTONE Levels 5-6).
- 2026-06-03: Cross-lane validation via Protocol injection — never import from source_registry or area_geometry.
- 2026-06-03: Evidence supersession adds superseded_by field (not silent overwrite).
- 2026-06-03: TC-040 uses a narrow no-new-dependency ruleset loader for the current YAML shape; broader YAML support requires an explicit dependency/design decision.

## Progress log

- 2026-06-03: Lane scaffold created. EvidenceContract + ClaimContract in per-lane files. 6 contract tests passing.
- 2026-06-03: TC-010 complete for the in-memory evidence slice. Added `EvidenceRepository`, `InMemoryEvidenceRepository`, and `EvidenceService` with source/area protocol validation, production-use rejection for observations, source-failure evidence creation, typed human notes, retrieval by area/source/type, and duplicate evidence protection. Lane C tests: 16 passing. Full verification: 64 tests, ruff clean, mypy clean (51 source files); DB smoke skipped.
- 2026-06-03: TC-020 complete for the in-memory evidence slice. Added `superseded_by` to `EvidenceContract`, repository marking support, and `EvidenceService.supersede` with same-area/new-ID/already-superseded/pre-superseded safeguards. Lane C tests: 23 passing. Full verification: 71 tests, ruff clean, mypy clean (51 source files); DB smoke skipped.
- 2026-06-03: TC-030 complete for the in-memory claim-service slice. Added `ClaimRepository`, `InMemoryClaimRepository`, and `ClaimService` with evidence existence validation, claim/evidence ID consistency checks, same-area enforcement, unknown claim generation from source-failure evidence, user-safe-language enforcement, and verification-task enforcement. Lane C tests: 35 passing. Full verification: 83 tests, ruff clean, mypy clean (54 source files); DB smoke skipped.
- 2026-06-03: TC-040 complete for one deterministic in-memory rules slice. Added `RuleEngine`, rule metadata on `ClaimContract`, ruleset loading for `config/ruleset_homestead_mvp.yaml`, deterministic claim IDs, high-risk flood positive claims, flood source-failure unknown claims, caveat propagation, superseded-evidence filtering, and rule-engine tests for determinism, empty input, multi-area grouping, invalid severity, and explicit positive-plus-failure output. Lane C tests: 45 passing. Full verification: 93 tests, ruff clean, mypy clean (56 source files); DB smoke skipped.
- 2026-06-03: TC-050 complete for the in-memory evidence payload-validation slice. Added type-specific `observed_value` validators for source observations, spatial intersections, derived metrics, document extracts, source failures, and human-note guardrails, plus payload tests. Lane C tests: 59 passing. Full verification: 107 tests, ruff clean, mypy clean (59 source files); DB smoke skipped.
- 2026-06-03: TC-060 complete for the in-memory audit-event slice. Added `EvidenceAuditEvent`, `InMemoryEvidenceAuditLog`, optional `EvidenceService` audit-log injection, and create/source-failure/human-note/supersede audit tests. Lane C tests: 63 passing. Full verification: 111 tests, ruff clean, mypy clean (60 source files); DB smoke skipped.
- 2026-06-03: TC-070 complete for the in-memory flood contradiction/stale rule slice. Added deterministic needs-review claims for conflicting active evidence and positive-plus-source-failure evidence, explicit fixture `source_stale` handling, superseded-evidence exclusion, and deterministic review-output tests. Lane C tests: 69 passing. Full verification: 117 tests, ruff clean, mypy clean (60 source files); DB smoke skipped.
- 2026-06-03: TC-080 complete for the access fixture hard-gate slice. Added deterministic access no-public-road-adjacency claims, access source-unavailable unknowns, access needs-review, stale access review claims, safe road-adjacency/legal-access language, and access adjacency payload validation. Lane C tests: 76 passing. Full verification: 131 tests, ruff clean, mypy clean (67 source files); DB smoke skipped because Docker Desktop Linux engine is unavailable.
