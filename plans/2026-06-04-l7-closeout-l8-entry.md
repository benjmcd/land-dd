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
5. Status: COMPLETE. See "D-004 Level 8 Ownership and Fixture Acceptance Plan" below.

### L8P-001: First fixture-only connector preparation

1. Implement only after L7C-002 and L7C-003 are recorded.
2. Prefer a narrow contract/fixture test before connector runtime code.
3. Prohibit live requests by default and make any live check opt-in.
4. Fail closed on unknown source license/review status.

## D-004 Level 8 Ownership and Fixture Acceptance Plan

Status: complete on 2026-06-04 as a planning/ownership pass. No connector runtime code, schemas, migrations, or lane-owned implementation files were edited.

### L8 Gate Ownership Map

| Gate | Requirement | Primary owner for next implementation | Supporting owners | Acceptance signal before Level 8 PASS |
|---|---|---|---|---|
| L8-001 | Shared connector interface and source registry use | Coordinator assigns new connector module owner before code; Lane A owns source registry checks | Lane C for evidence output contract; Lane D for API/report surfacing | Connector cannot run without registered source/dataset/version references and a reviewed interface contract. |
| L8-002 | Connector run lifecycle persisted with timing, source version, and error metadata | Lane A | Lane D only if surfacing run status through API later | `SourceRetrievalRunContract` / provenance repository records status, timestamps, `dataset_version_id`, `log_uri`, counts, and metrics. |
| L8-003 | Idempotent ingestion | Lane A for dataset version/retrieval identity; Lane C for evidence duplicate/supersession behavior | Coordinator if a cross-lane idempotency key is needed | Re-running the same fixture does not duplicate evidence or creates a documented supersession path. |
| L8-004 | Failures become source-failure evidence or blocked retrieval records | Lane C for `EvidenceService.create_source_failure`; Lane A for blocked/failed retrieval runs | Lane D verifies report/API unknown surfacing | Fixture failure case records a failed/blocked retrieval run and/or stored SOURCE_FAILURE evidence that appears as an UNKNOWN report claim. |
| L8-005 | Rate limits, timeouts, retry policy explicit | Future connector owner assigned by coordinator | Lane A records retry/failure metadata; Lane D may document API behavior | Fixture connector has no live calls; live connector plans must define timeout/retry/rate-limit defaults before implementation. |
| L8-006 | Data-quality gates reject malformed or unsafe records | Lane C for evidence payload validation; Lane B for geometry validation | Lane A for source/license constraints | Malformed fixture payloads fail closed before evidence/claims; geometry fixtures use Lane B validators. |
| L8-007 | Connector output enters evidence ledger before claims | Lane C | Lane D validates downstream report behavior | Connector output is `EvidenceContract`/SOURCE_FAILURE only; it never emits claims directly. |
| L8-008 | Normal verification does not require live network | Coordinator/test owner; likely connector module owner | Lane D records validation; CI keeps live tests opt-in | Default `.\scripts\verify.ps1` passes with fixture-only connector tests and no network. |
| L8-009 | Production connector blocked if license/terms unresolved | Lane A | Lane C evidence service enforces production-use source checks | Unknown/blocked source rights prevent source-derived evidence creation and connector production use. |
| L8-010 | Logs/metrics diagnose connector failures | Lane A for retrieval metrics/log URI | Lane D for future operator/report surfacing | Fixture success/failure runs include row/error/warning counts and failure reason metadata. |

### First Fixture-Only Connector Acceptance Path

The first connector implementation should be a static local fixture connector for one already-modeled screening domain, preferably flood, because current rule/report tests already verify flood evidence and flood source-failure behavior.

Proposed fixture path:

1. Input is local fixture JSON only; no HTTP, browser, shell download, vendor credential, or live API call is allowed.
2. Fixture references an existing approved/restricted source registry row and a Lane A dataset/version record.
3. Success fixture produces one or more `EvidenceContract` records with `evidence_type=spatial_intersection`, `domain=flood`, source ID, method code/version, caveat, confidence, and validated observed value.
4. Failure fixture records a failed or blocked retrieval run and creates SOURCE_FAILURE evidence through Lane C service behavior.
5. Re-running the same fixture is idempotent: it either returns the same evidence identity, skips duplicates, or records a controlled supersession. The expected behavior must be selected before code.
6. Report verification proves connector-created evidence reaches the existing report/API path before claims and that failures surface as UNKNOWNs.
7. Default verification remains fixture-only; any live connector smoke requires an explicit opt-in environment variable and separate runbook.

### Required Pre-Code Decisions

| Decision | Why it matters | Owner / resolver |
|---|---|---|
| Who owns future `backend/app/connectors/` if created | `LANE_OWNERSHIP.md` does not currently assign connector module ownership | Coordinator before implementation |
| Whether connector run status uses source retrieval runs, jobs, or both | D-003 identified job/source retrieval status schema divergence | Coordinator with Lane A and Lane D |
| Idempotency identity | Prevents duplicate evidence and unclear retry semantics | Lane A + Lane C before connector code |
| Success fixture evidence shape | Must align with Lane C payload validation and current rule domains | Lane C, with Lane D downstream test |
| Failure taxonomy | Determines failed retrieval vs SOURCE_FAILURE evidence behavior | Lane A + Lane C |
| Geometry fixture needs | Must use Lane B hardened EPSG:4326 coordinate validation | Lane B only if new geometry fixtures are needed |

### Stop Conditions Before L8P-001 Code

- Stop if connector implementation requires a new shared connector directory without ownership update.
- Stop if source license/review status is unknown or incompatible.
- Stop if fixture evidence payload shape is not accepted by Lane C validators.
- Stop if idempotency behavior is unspecified.
- Stop if implementation requires live network, credentials, paid/vendor data, or selecting the MVP jurisdiction.
- Stop if schema edits are needed before D-003 owner-specific follow-up happens.

## D-005 Connector Module Ownership Decision Packet

Status: prepared on 2026-06-04; coordinator action still required before D-005 can be considered complete. The proposed ADR is `docs/adr/lane-d-0002-connector-entry-ownership.md`.

### Proposed Decision

Create a coordinator-owned connector integration zone before any runtime connector code:

- `backend/app/connectors/`
- `backend/tests/connectors/`
- `tests/fixtures/connectors/`
- `plans/connector-*.md` and `state/connector-state.md` if connector work becomes a sustained lane

This zone should be writable only by an explicitly assigned connector implementation pass. It may read public lane APIs and domain contracts, but any required Lane A/B/C/D implementation change remains owned by that lane.

Use source retrieval runs as the connector attempt lifecycle authority. `SourceRetrievalRunContract` and `source.ingest_runs` already carry connector name, dataset version, status, timing, row/error/warning counts, log URI, metrics, and durable linkage into `evidence.observations.ingest_run_id`. `jobs.job_queue` should remain future async orchestration, not provenance authority, unless a later jobs ADR explicitly references retrieval runs instead of replacing them.

### Prepared Coordinator Action

To resolve D-005, update `LANE_OWNERSHIP.md` with the connector integration zone above, then assign the first fixture connector implementation pass to that zone. Do not assign it to Lane D by default; report/API should validate downstream surfacing, not own ingestion.

### Remaining Stop Condition

No `backend/app/connectors/` runtime code should be created until `LANE_OWNERSHIP.md` makes this ownership explicit.

## Files likely to change

| File | Expected change |
|---|---|
| `backend/tests/reports/test_report_regression.py` | Add normalized report artifact regression test |
| `backend/tests/reports/fixtures/*.json` | Optional committed expected fixture output |
| `docs/adr/lane-d-0002-connector-entry-ownership.md` | Proposed connector ownership/run-lifecycle decision packet |
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
- 2026-06-04: D-004 Level 8 ownership and fixture-only connector acceptance plan completed after Lane B TB-100 landed on root `main` (`cf9897e`). No connector runtime, schema, migration, or lane-owned implementation files were changed.
- 2026-06-04: D-005 decision packet prepared. Proposed ADR recommends a coordinator-owned connector integration zone and source retrieval runs as connector lifecycle authority; `LANE_OWNERSHIP.md` still needs coordinator update before runtime code.
