# Level 7 Closeout and Level 8 Entry Plan

## Goal

Turn the current Level 7 fixture-backed report/API PASS into a durable handoff for the next stage, then define the first safe Level 8 connector-preparation slice without changing shared schemas, live connector behavior, or other lane-owned implementation files.

The intended outcome is a fresh-session-ready plan for:

- proving the current report contract against a committed fixture report artifact;
- deciding how report/evidence/source JSON schemas should align before any `schemas/*.json` edit;
- assigning Level 8 connector responsibilities across lanes before implementation begins;
- selecting a fixture-only connector path that cannot hit live services.

## Non-goals

- No live connectors, public APIs, paid vendors, or network-backed data ingestion.
- No `schemas/*.json` edits in this pass.
- No database migrations or source/area/evidence/claim/report contract changes.
- No UI, LLM summary, auth/security, production observability, or batch workflow work.
- No edits to Lane A/B/C implementation files.

## Current state

- `state/PROJECT_STATE.md` records Level 7 PASS for the fixture-backed report/API workflow.
- `backend/app/api/dependencies.py` and `backend/app/main.py` provide explicit DB-backed API mode through `create_app(use_db_services=True)`.
- `backend/tests/api/test_report_runs_db.py` proves DB-backed `POST /areas`, `POST /report-runs`, `GET /report-runs/{id}`, persisted `reports.report_runs.intent_id`, unsupported-category UNKNOWNs, and artifact path.
- `backend/app/reports/report_repo.py` writes machine-readable report artifacts under `OBJECT_STORE_ROOT`.
- `MILESTONE_MAP.md` Level 7 still names `report JSON schema`, `fixture report input/output`, and `sample generated report artifact` as required artifacts.
- `MILESTONE_MAP.md` Level 8 requires a shared connector interface, persisted connector runs, idempotency, failure handling, data-quality gates, source-version linkage, connector fixtures, and non-flaky local verification.
- `LANE_OWNERSHIP.md` assigns source registry, source provenance, seeds, and migrations to Lane A; area geometry to Lane B; evidence and claims to Lane C; reports/API to Lane D. Connector work will cross these boundaries unless planned before code changes.
- Session 1 is working isolated Lane B coordinate-validation hardening and must not be coupled to this pass.

## Proposed design

Use a closeout-first sequence before Level 8 implementation:

1. Add a Lane D report regression fixture that normalizes dynamic IDs/timestamps/paths and asserts the stable report artifact shape.
2. Produce a schema-contract alignment note before editing shared schemas. This note should map `ReportRunContract`, `EvidenceContract`, `ClaimContract`, and source metadata fields to existing `schemas/*.json` gaps and decide which lane owns each schema update.
3. Define Level 8 connector ownership before implementation. Lane A should own source registry/source-version/retrieval-run persistence. Lane C should own evidence-ledger ingestion contracts and source-failure evidence behavior. Lane D should own API/report surfacing of connector results. Lane B should own only geometry inputs/validation needed by connector fixtures.
4. Start Level 8 with a fixture-only connector contract test or static local file connector that uses seeded/approved sources and cannot make live network calls.

Rejected alternatives:

- Editing `schemas/*.json` immediately: shared interface zone; it needs cross-lane review and explicit ownership.
- Starting connector code in Lane D: connectors feed source/evidence layers and would conflict with Lane A/C ownership unless scoped first.
- Advancing UI/MVP workflow: blocked by Level 8 connector and failure/idempotency requirements.

## D-003 Schema-Contract Alignment Note

Status: complete on 2026-06-04 as a documentation/ownership pass. No shared schemas were edited.

### Contract Sources Of Truth

| Surface | Current live authority | Notes |
|---|---|---|
| Source API/domain contract | `backend/app/domain/source_contracts.py` | Lane A owns source contract and source schema edits. |
| Evidence API/domain contract | `backend/app/domain/evidence_contracts.py` | Lane C owns evidence contract and evidence schema edits. |
| Claim API/domain contract | `backend/app/domain/claim_contracts.py` | Lane C owns claim contract and claim schema edits. |
| Report API/domain contract | `backend/app/domain/report_contracts.py` | Lane D owns report contract and future report schema proposal. |
| Active API behavior | `backend/app/api/*.py` with Pydantic response models | Planning-pack OpenAPI is reference-only until refreshed explicitly. |
| Persisted report artifact | `backend/app/reports/report_repo.py` and `backend/tests/reports/test_report_regression.py` | Report artifact schema currently lives as Pydantic contract plus regression projection, not as `schemas/report_run_schema.json`. |

### Shared-Schema Gaps

| Existing schema | Gap vs current contracts/artifacts | Future owner | Required decision before edit |
|---|---|---|---|
| `schemas/source_schema.json` | Requires `source_type`, while `SourceContract.source_type` is optional; does not model `SourceDatasetContract`, `SourceDatasetVersionContract`, or `SourceRetrievalRunContract`; does not constrain source governance status vocabularies beyond string type. | Lane A | Decide whether source schema covers only `SourceContract` or the full source/dataset/version/retrieval family. |
| `schemas/evidence_schema.json` | Does not include required domain fields `source_id`, `evidence_code`, `observed_at`, `superseded_by`, `geometry_geojson`, `geometry_srid`, or `spatial_precision_meters`; still exposes `geometry_wkt`, which current `EvidenceContract` does not use; `retrieved_at` differs from contract `observed_at`; `observed_value` is broad while runtime validators enforce type-specific payloads. | Lane C | Decide whether schema should mirror the API contract exactly or define persistence/ingestion payloads separately. |
| `schemas/claim_schema.json` | Requires `intent`, which current `ClaimContract` does not carry; omits `rule_code`, `ruleset_id`, and `ruleset_version`; includes `contradiction_group_ids`, which current claim contract does not carry. | Lane C | Decide whether claim schema represents current API/domain claims or a future enriched report/export claim. |
| `schemas/job_schema.json` | Matches the broad `JobStatus` values but there is no current `JobContract`; Level 8 connector/retrieval run statuses also use `SourceRetrievalStatus` values (`pending`, `running`, `succeeded`, `failed`, `blocked`, `skipped`) that do not fully match job status. | Coordinator with Lane A/Lane D | Decide whether connector runs reuse job schema, source retrieval run schema, or both. |
| report schema missing | Level 7 requires a report JSON schema, but no active `schemas/report_run_schema.json` exists. Current report output is governed by `ReportRunContract`, `SqlAlchemyReportRunRepository`, and the normalized report regression test. | Lane D proposes; coordinator reviews because nested evidence/claim/source shapes cross lanes | Decide whether to add a new report-run schema that references lane-owned source/evidence/claim schemas after those schemas are aligned. |
| planning-pack OpenAPI | `docs/planning_pack/api/openapi_stub.yaml` is not active API truth and predates the current FastAPI routers. | Lane D/docs follow-up | Decide whether to generate/update active OpenAPI docs from FastAPI instead of manually editing the planning-pack stub. |

### Recommended Edit Order

1. Lane C aligns evidence and claim schemas with current `EvidenceContract` and `ClaimContract`, or records an ADR explaining a separate persistence/export schema.
2. Lane A aligns source schema scope with `SourceContract` vs source provenance family contracts.
3. Lane D proposes `schemas/report_run_schema.json` only after nested source/evidence/claim schema scope is settled.
4. Lane D refreshes API/OpenAPI documentation from the FastAPI app after schema scope is settled.
5. Level 8 connector work begins with fixture-only connector contracts that reference the aligned source/evidence schemas.

### Stop Conditions

- Do not edit `schemas/*.json` from a single lane without owner assignment and review scope.
- Do not start connector runtime code until source version/retrieval-run ownership and evidence output shape are explicit.
- Do not use live network data for schema validation; fixture-only payloads are the first Level 8 path.

## Bottom-up sequence

### L7C-001: Report artifact regression fixture

1. Add a Lane D test that generates a fixture report using current in-memory services.
2. Normalize dynamic fields: UUIDs, timestamps, output paths, and any repository-managed URIs.
3. Assert stable sections: source manifest, evidence domains, claim codes, unknowns, red flags, verification tasks, caveats, artifact metadata, and no live-source markers.
4. If a committed expected JSON fixture is added, keep it under a Lane D-owned test path such as `backend/tests/reports/fixtures/`.

### L7C-002: Schema-contract alignment note

1. Read `schemas/evidence_schema.json`, `schemas/claim_schema.json`, `schemas/source_schema.json`, and any future report schema location.
2. Compare them to `backend/app/domain/*_contracts.py` and persisted metadata behavior.
3. Record gaps without changing shared schemas.
4. Identify the lane owner for each future schema edit and whether an ADR is required.
5. Status: COMPLETE. See "D-003 Schema-Contract Alignment Note" above.

### L7C-003: Level 8 ownership plan

1. Map Level 8 gates L8-001 through L8-010 to lane-owned modules.
2. Define the first fixture-only connector slice that does not need live network, new vendors, or new jurisdiction decisions.
3. Define failure/idempotency acceptance tests before connector implementation.
4. Add any new queue entries only after lane ownership is clear.

### L8P-001: First fixture-only connector preparation

1. Implement only after L7C-002 and L7C-003 are recorded.
2. Prefer a narrow contract/fixture test before connector runtime code.
3. Prohibit live requests by default and make any live check opt-in.
4. Fail closed on unknown source license/review status.

## Files likely to change

| File | Expected change |
|---|---|
| `backend/tests/reports/test_report_regression.py` | Add normalized report artifact regression test |
| `backend/tests/reports/fixtures/*.json` | Optional committed expected fixture output |
| `plans/2026-06-04-l7-closeout-l8-entry.md` | Track closeout and entry sequencing |
| `plans/lane-d-2026-06-03-reports-api-infra.md` | Record Lane D closeout progress if report regression is implemented |
| `state/PROJECT_STATE.md` | Update only when the next executable task changes materially |
| `state/VALIDATION_LOG.md` | Record validation for closeout slices |
| `state/WORKLOG.md` | Record material closeout progress |

## Tests / verification

For L7C-001:

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/reports/test_report_regression.py
ruff check tests/reports/test_report_regression.py
mypy tests/reports/test_report_regression.py
Set-Location ..
.\scripts\verify.ps1
```

For schema-contract notes without code changes:

```powershell
.\scripts\verify.ps1
```

If DB-backed behavior changes in a later slice:

```powershell
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

## Risks and blockers

| Risk / blocker | Handling |
|---|---|
| Shared-schema edits cross lane boundaries | Do not edit `schemas/*.json` until a schema-contract note assigns ownership and review scope |
| Connector work crosses Lane A/C ownership | Plan connector responsibilities before code; stop if implementation requires Lane A/C files |
| Session 1 Lane B branch is active | Avoid geometry validator, geometry fixtures, Lane B plan/state, and area tests |
| Report regression fixture may overfit UUID/time/path fields | Normalize dynamic fields and assert stable semantic structure only |
| Level 8 could accidentally use live network | Fixture-only first; live tests must be opt-in and disabled by default |

## Decision log

- 2026-06-04: After D-001, advance through closeout/schema-contract planning before Level 8 connector code because connector implementation crosses source/evidence/report ownership.
- 2026-06-04: Keep this pass away from Session 1's Lane B coordinate-validation files and away from Lane A/C implementation files.

## Progress log

- 2026-06-04: Plan created from root `main` after D-001 (`c3453ce`). No schema or implementation files changed in this planning slice.
- 2026-06-04: D-002 completed from root `main` (`16c5d7f`) with a normalized report artifact regression.
- 2026-06-04: D-003 schema-contract alignment note completed. Shared schemas were audited but not edited; future schema ownership and edit order are recorded above.
