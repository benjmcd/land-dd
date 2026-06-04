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
- `schemas/evidence_schema.json` and `schemas/claim_schema.json` now mirror the serialized Lane C Pydantic domain contracts rather than DB rows or future report/export envelopes.
- `SourceExistsProtocol`, `AreaExistsProtocol` in `backend/app/domain/protocols.py`.
- `backend/app/evidence_ledger/` contains `EvidenceRepository`, `InMemoryEvidenceRepository`, `SqlAlchemyEvidenceRepository`, `EvidenceService`, `InMemoryEvidenceAuditLog`, and `SqlAlchemyEvidenceAuditLog`.
- `backend/app/claims_engine/` contains `ClaimRepository`, `InMemoryClaimRepository`, `ClaimService`, and `RuleEngine`.
- `backend/tests/evidence_ledger/` and `backend/tests/claims_engine/` test directories exist.
- 153 tests in `backend/tests/evidence_ledger/` and `backend/tests/claims_engine/`.

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
5. Status: COMPLETE for the access fixture hard-gate scope. At TC-080 completion, the rule engine covered flood and access hard-gate fixtures; zoning, wetlands, slope, and water were pending follow-on slices.

### TC-090: Wetlands fixture hard-gate coverage
1. Extend deterministic rule handling for `WETLAND_G001` using mapped wetland/deepwater screening fixture evidence.
2. Add fixture evidence patterns for mapped wetland intersection, no mapped wetland intersection, wetlands source failure, stale wetland evidence, and mixed/incomplete evidence.
3. Preserve evidence IDs, caveat propagation, severity/confidence separation, deterministic IDs/order, and verification tasks.
4. Keep output language strictly screening-only: do not assert jurisdictional wetlands, delineation results, permitting outcomes, or final buildability.
5. Tests: positive, negative/no-claim, source-failure/unknown, stale/review, deterministic ordering, and payload validation for wetland fixture keys.
6. Status: COMPLETE for the wetlands fixture hard-gate scope. At TC-090 completion, the rule engine covered flood, access, and wetlands hard-gate fixtures; zoning, slope, and water were pending follow-on slices.

### TC-100: Slope/buildability fixture hard-gate coverage
1. Extend deterministic rule handling for `SLOPE_G001` using fixture-derived low-slope buildable-area metrics.
2. Add fixture evidence patterns for explicit insufficient low-slope area, sufficient/no-claim, source failure, stale slope evidence, and mixed/incomplete evidence.
3. Preserve evidence IDs, caveat propagation, severity/confidence separation, deterministic IDs/order, and verification tasks.
4. Avoid hard-coding a jurisdictional or engineering threshold; fixture evidence must carry the explicit insufficiency signal.
5. Keep output language as a buildability screening proxy only: do not assert final buildability, site-plan approval, engineering feasibility, or permitted building envelope.
6. Tests: positive, negative/no-claim, source-failure/unknown, stale/review, deterministic ordering, and payload validation for slope fixture keys.
7. Status: COMPLETE for the slope/buildability fixture hard-gate scope. At TC-100 completion, the rule engine covered flood, access, wetlands, and slope hard-gate fixtures; zoning and water were pending follow-on slices.

### TC-110: Zoning/use fixture hard-gate coverage
1. Extend deterministic rule handling for `ZONING_G001` using fixture source-observation evidence for intended residential/homestead use screening.
2. Add fixture evidence patterns for explicit prohibited/unsupported intended residential use, allowed/no-claim, source failure, stale zoning evidence, and mixed/incomplete evidence.
3. Preserve evidence IDs, caveat propagation, severity/confidence separation, deterministic IDs/order, and verification tasks.
4. Avoid hard-coding a state, county, zoning district taxonomy, ordinance parser, or legal interpretation; fixture evidence must carry the explicit prohibited/unsupported signal.
5. Keep output language as zoning/use screening only: do not assert final legal use, zoning compliance, permit eligibility, vested rights, minimum lot-size compliance, or buildability.
6. Tests: positive, negative/no-claim, source-failure/unknown, stale/review, deterministic ordering, and payload validation for zoning fixture keys.
7. Status: COMPLETE for the zoning/use fixture hard-gate scope. At TC-110 completion, the rule engine covered flood, access, zoning, wetlands, and slope hard-gate fixtures; water was pending after this slice.

### TC-120: Water-context fixture hard-gate coverage
1. Extend deterministic rule handling for `WATER_G001` using fixture source-observation evidence for water-context screening.
2. Add fixture evidence patterns for explicit no-plausible-water-context signals, plausible-context/no-claim signals, source failure, stale water evidence, and mixed/incomplete evidence.
3. Preserve evidence IDs, caveat propagation, severity/confidence separation, deterministic IDs/order, and verification tasks.
4. Avoid hard-coding a state, county, aquifer, well-log threshold, water-rights rule, hauling rule, or source-specific interpretation; fixture evidence must carry the explicit water-context signal.
5. Keep output language as water-context screening only: do not assert water rights, well yield or viability, lawful hauling, utility/service availability, potable water, or final water availability.
6. Tests: positive, negative/no-claim, source-failure/unknown, incomplete/review, stale/review, deterministic ordering, and payload validation for water fixture keys.
7. Status: COMPLETE for the water-context fixture hard-gate scope. The rule engine now covers the current ruleset's flood, access, zoning, water, wetlands, and slope hard-gate fixtures in memory.

### TC-130: DB-backed evidence repository and audit log
1. Add SQLAlchemy-backed repository behavior for `evidence.observations`.
2. Preserve contract fields that are not first-class columns (`source_id`, `evidence_code`, `superseded_by`, `observed_at`) in observation metadata.
3. Add SQLAlchemy-backed evidence audit events using `audit.events`.
4. Tests: source observation, source failure, spatial intersection, derived metric, document extract, human verification, invalid payload rejection, supersession, retrieval by area/source/type, rollback behavior, and durable audit events.
5. Status: COMPLETE for the DB-backed repository/audit scope. L5 remains PARTIAL until first-class evidence geometry/spatial-precision fields are exposed in the contract and mapped to `evidence.observations.geometry`.

### TC-140: Evidence geometry and spatial precision mapping
1. Add optional evidence geometry fields to `EvidenceContract` with fail-closed SRID 4326 validation.
2. Add optional `spatial_precision_meters` to the evidence contract.
3. Persist evidence geometry to `evidence.observations.geometry` through `SqlAlchemyEvidenceRepository`.
4. Preserve spatial precision in `evidence.observations.metadata.spatial_precision_meters` until a schema migration promotes it.
5. Add DB-gated tests for geometry/SRID/precision storage and readback.
6. Add an evidence-ledger persistence ADR covering immutability, supersession/amendment, audit events, geometry mapping, source failures, and metadata-preserved fields.
7. Status: COMPLETE. Level 5 now passes for the fixture-backed DB evidence-ledger path.

### TC-150: DB-backed claim persistence and evidence links
1. Add SQLAlchemy-backed repository behavior for `claims.claims`.
2. Persist claim/evidence links through `claims.claim_evidence`.
3. Preserve rule metadata (`rule_code`, `ruleset_id`, `ruleset_version`) and evidence ordering in claim metadata until a coordinated schema migration promotes those fields.
4. Persist verification tasks through `claims.verification_tasks` when a claim requires professional/local confirmation.
5. Tests: durable claim round-trip, evidence-link rows, verification-task rows, unknown/source-failure claim persistence, duplicate claim rejection, and rollback behavior.
6. Add a rules/claim persistence ADR covering deterministic rules, evidence links, rule version metadata, verification tasks, hard gates before scoring, and deferred suitability scoring.
7. Status: COMPLETE for durable claim persistence in the current fixture-backed DB scope. L6 remains PARTIAL until remaining minimum rule categories are implemented or explicitly marked not evaluated in report/API output.

### TC-160: Not-evaluated minimum rule categories
1. Add Lane C-owned unsupported-domain definitions for `soil_septic`, `env_hazard`, `resource_context`, and `market_context`.
2. Add four explicit hard-gate rules to `config/ruleset_homestead_mvp.yaml`.
3. Make `RuleEngine.evaluate()` emit deterministic `SeverityBand.UNKNOWN` claims when provided source-failure evidence for those unsupported domains.
4. Preserve the evidence-before-claim invariant by requiring stored source-failure evidence input; the rule engine does not create free-standing not-evaluated claims.
5. Tests: ruleset declarations, source-failure evidence helper, four unknown not-evaluated claims, deterministic output, non-failure records ignored, evidence-ID ordering, and market-context safe language.
6. Status: COMPLETE for Lane C-owned Level 6 claim/rule scope. Report-run auto-creation of unsupported-domain source-failure evidence is a Lane D integration handoff because `backend/app/reports/service.py` is Lane D-owned.

### TC-170: Lane C schema-contract alignment
1. Treat `schemas/evidence_schema.json` and `schemas/claim_schema.json` as serialized Pydantic domain-contract schemas for `EvidenceContract` and `ClaimContract`.
2. Align evidence schema fields with `EvidenceContract.model_fields`, including `source_id`, `evidence_code`, `observed_at`, `superseded_by`, `geometry_geojson`, `geometry_srid`, and `spatial_precision_meters`.
3. Remove stale evidence schema fields that belong to DB rows or older docs (`retrieved_at`, `geometry_wkt`, `metadata`, `authority_level`).
4. Align claim schema fields with `ClaimContract.model_fields`, including rule metadata (`rule_code`, `ruleset_id`, `ruleset_version`).
5. Remove stale claim schema fields not carried by the current contract (`intent`, `contradiction_group_ids`, `metadata`).
6. Add schema-contract parity tests without adding a JSON-schema validation dependency.
7. Record the shared-schema decision in `docs/adr/lane-c-schemas.md`.
8. Status: COMPLETE for canonical Lane C schema/contract scope. Planning-pack evidence/claim schema copies are reconciled as documentation-packaging copies, not runtime schema truth.

### TC-180: Source-failure evidence identity preservation
1. Extend `EvidenceService.create_source_failure(...)` with an optional caller-supplied `evidence_id`.
2. Preserve the supplied ID through the existing source-failure validation, duplicate-rejection, repository persistence, and audit-event path.
3. Add in-memory tests proving ID preservation and duplicate rejection for source-failure evidence.
4. Add a DB-gated persistence assertion proving the supplied source-failure ID round-trips through `SqlAlchemyEvidenceRepository`.
5. Keep connector adapter usage out of this Lane C slice; connector-owned code can adopt the public parameter in a separately coordinated pass.
6. Status: COMPLETE for the Lane C public evidence-service contract. CON-019 completes connector-zone adoption in the Session 2 integration branch by passing `evidence.evidence_id` to the public Lane C method.

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
| `schemas/evidence_schema.json` | TC-170 canonical evidence contract schema alignment |
| `schemas/claim_schema.json` | TC-170 canonical claim contract schema alignment |
| `docs/adr/lane-c-schemas.md` | TC-170 shared-schema decision record |
| `state/lane-c-state.md` | Update after each task |

## Tests / verification

```bash
pytest backend/tests/evidence_ledger/ backend/tests/claims_engine/ -v
mypy backend/app/evidence_ledger backend/app/claims_engine \
     backend/app/domain/evidence_contracts.py backend/app/domain/claim_contracts.py
# Verify cross-lane import isolation:
grep -r "from app.source_registry" backend/app/evidence_ledger/ backend/app/claims_engine/
grep -r "from app.area_geometry" backend/app/evidence_ledger/ backend/app/claims_engine/
.\scripts\verify.ps1
```

## Risks and blockers

| Blocker | Status | Impact |
|---|---|---|
| SourceExistsProtocol needs real implementation | Available for in-memory wiring | Lane A SourceService exposes source existence and fail-closed production-use checks; integration wiring remains Lane D's job |
| AreaExistsProtocol needs real implementation | Available for in-memory wiring | Lane B AreaService exposes `area_is_registered`; integration wiring remains Lane D's job |
| New EvidenceType value | Requires shared enums.py change | Stop and record blocker |
| YAML rules engine needs jurisdiction | Undecided | Use fixture rules only; do not hard-code state |
| YAML parser scope | Accepted for TC-040 | Current loader supports the checked-in ruleset shape only; broaden with an approved parser/dependency decision before complex YAML features |
| Evidence geometry/spatial precision | Closed for Level 5 | `EvidenceContract` exposes optional GeoJSON/SRID/spatial precision; `SqlAlchemyEvidenceRepository` maps geometry to `evidence.observations.geometry` and precision to metadata |
| Minimum rule categories | Closed for Lane C | Soil/septic, environmental hazards, market context, and resource context now emit evidence-backed not-evaluated UNKNOWN claims when source-failure evidence is supplied; report-run auto-injection is a Lane D handoff |
| Planning-pack evidence/claim schema copies | Closed | `docs/planning_pack/schemas/evidence_schema.json` and `docs/planning_pack/schemas/claim_schema.json` mirror the canonical root Lane C schemas; broader planning-pack API/source/job/report surfaces remain separate follow-ups |
| Connector source-failure evidence ID preservation | Lane C public service side closed; CON-019 connector adoption complete in Session 2 integration branch | `EvidenceService.create_source_failure(...)` can preserve a supplied evidence ID; durable `ingest_run_id` evidence-row linkage remains a future coordinated connector/Lane C/schema pass |

## Decision log

- 2026-06-03: Lane C owns evidence ledger + claims engine (MILESTONE Levels 5-6).
- 2026-06-03: Cross-lane validation via Protocol injection — never import from source_registry or area_geometry.
- 2026-06-03: Evidence supersession adds superseded_by field (not silent overwrite).
- 2026-06-03: TC-040 uses a narrow no-new-dependency ruleset loader for the current YAML shape; broader YAML support requires an explicit dependency/design decision.
- 2026-06-04: `SqlAlchemyEvidenceRepository` stores contract-only provenance/amendment fields in `evidence.observations.metadata` until a coordinated schema change promotes them to first-class columns.
- 2026-06-04: `SqlAlchemyEvidenceAuditLog` records evidence create/supersede events in `audit.events` with `target_table='evidence.observations'`.
- 2026-06-04: Evidence geometry remains optional and SRID 4326; spatial precision remains metadata-preserved until a coordinated schema migration promotes it.
- 2026-06-04: `SqlAlchemyClaimRepository` stores rule metadata and evidence ordering in `claims.claims.metadata`, claim/evidence links in `claims.claim_evidence`, and verification tasks in `claims.verification_tasks`.
- 2026-06-04: Canonical Lane C schemas represent serialized `EvidenceContract` and `ClaimContract` field sets, not DB rows, planning-pack snapshots, or future report/export envelopes.
- 2026-06-04: `docs/adr/lane-c-schemas.md` records the shared-schema decision after D-003 assigned evidence/claim schema follow-up to Lane C.

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
- 2026-06-03: TC-090 complete for the wetlands fixture hard-gate slice. Added deterministic mapped-wetland/deepwater claims, wetland source-unavailable unknowns, wetland needs-review, stale wetland review claims, screening-only/no-delineation language, and wetland fixture payload validation. Lane C tests: 83 passing. Full verification: 138 tests, ruff clean, mypy clean (67 source files); DB smoke skipped because Docker Desktop Linux engine is unavailable.
- 2026-06-03: TC-100 complete for the slope/buildability fixture hard-gate slice. Added deterministic insufficient low-slope buildable-area claims, slope source-unavailable unknowns, slope needs-review, stale slope review claims, screening-only/no-final-buildability language, and slope derived-metric payload validation. Lane C tests: 90 passing. Full verification: 145 tests, ruff clean, mypy clean (67 source files); DB smoke skipped because Docker Desktop Linux engine is unavailable.
- 2026-06-03: TC-110 complete for the zoning/use fixture hard-gate slice. Added deterministic intended residential/homestead use prohibited-or-unsupported claims, zoning source-unavailable unknowns, zoning needs-review for incomplete/mixed evidence, stale zoning review claims, screening-only/no-final-legal-use language, and zoning source-observation payload validation. Lane C tests: 100 passing. Full verification: 157 tests, ruff clean, mypy clean (67 source files); DB smoke skipped because Docker Desktop Linux engine is unavailable.
- 2026-06-03: TC-120 complete for the water-context fixture hard-gate slice. Added deterministic no-plausible-water-context claims, water source-unavailable unknowns, water needs-review for incomplete/mixed evidence including internally contradictory fixture records, stale water review claims, screening-only/no-water-rights/no-well-viability language, and water source-observation payload validation. Lane C tests: 111 passing. Full verification: 168 tests, ruff clean, mypy clean (67 source files); DB smoke skipped because Docker Desktop Linux engine is unavailable.
- 2026-06-04: TC-130 complete for the DB-backed evidence repository/audit slice. Added `SqlAlchemyEvidenceRepository`, `SqlAlchemyEvidenceAuditLog`, and DB-gated tests for source observation, source failure, spatial intersection, derived metric, document extract, human verification, invalid payload rejection, supersession, retrieval by area/source/type, rollback, and durable audit events. Lane C tests: 122 passing with DB smoke enabled. Full PowerShell verification: 227 tests, ruff clean, mypy clean (80 source files), DB smoke passes.
- 2026-06-04: TC-140 complete for evidence geometry/spatial precision mapping. Added optional GeoJSON/SRID/spatial precision fields to `EvidenceContract`, mapped geometry to `evidence.observations.geometry`, preserved precision in metadata, added DB-gated round-trip tests, and recorded the evidence persistence ADR. Lane C tests: 126 passing with DB smoke enabled. Full PowerShell verification: 231 tests, ruff clean, mypy clean (80 source files), DB smoke passes.
- 2026-06-04: TC-150 complete for DB-backed claim persistence. Added `SqlAlchemyClaimRepository`, DB-backed claim/evidence links, verification-task persistence, durable unknown/source-failure claim tests, duplicate/rollback tests, and the rules/claim persistence ADR. Lane C tests: 130 passing with DB smoke enabled. Full PowerShell verification: 235 tests, ruff clean, mypy clean (81 source files), DB smoke passes.
- 2026-06-04: TC-160 complete for Lane C-owned not-evaluated rule categories. Added unsupported-domain constants/helper, four YAML hard gates, deterministic UNKNOWN rule-engine claims from source-failure evidence, and tests for ruleset declarations, helper output, evidence-linked claims, deterministic ordering, non-failure ignore behavior, and market-context safe language. Lane C tests: 143 collected with DB smoke enabled. Full backend collection: 248 tests; full DB-gated backend pytest, direct DB smoke, targeted ruff/mypy, and default PowerShell verification pass.
- 2026-06-04: TC-170 complete for canonical Lane C schema-contract alignment. `schemas/evidence_schema.json` and `schemas/claim_schema.json` now mirror serialized `EvidenceContract`/`ClaimContract` fields and enums; stale DB/doc fields are removed; `docs/adr/lane-c-schemas.md` records the shared-schema decision; schema parity tests were added without a new validation dependency. Lane C evidence/claims collection: 151 tests. Full backend collection after rebasing onto CON-002: 268 tests. Full PowerShell verification with DB smoke: 268 tests, ruff clean, mypy clean (96 source files), DB smoke passes.
- 2026-06-04: Planning-pack evidence/claim schema-copy follow-up complete. `docs/planning_pack/schemas/evidence_schema.json` and `docs/planning_pack/schemas/claim_schema.json` now mirror the canonical root Lane C schemas, and `backend/tests/test_planning_pack_schema_copies.py` prevents those copies from silently drifting.
- 2026-06-04: TC-180 complete for Lane C public source-failure identity preservation. `EvidenceService.create_source_failure(...)` now accepts an optional `evidence_id`, preserves it through in-memory and SQLAlchemy-backed evidence storage, and still rejects duplicate IDs without overwrite. CON-019 completes connector-zone adapter adoption in the Session 2 integration branch.
