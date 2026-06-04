# Fixture Flood Connector Contract Slice

## Goal

Implement the first Level 8 connector contract slice in the connector integration zone. The connector reads local flood fixture JSON, records source retrieval provenance, and emits evidence/source-failure inputs before claims or reports.

## Non-goals

- No live network, browser/download step, vendor credential, paid API, or public API access.
- No DB persistence, migrations, shared schema edits, report/API wiring, claims generation, or UI work.
- No Lane A/B/C/D implementation file changes.

## Current state

- `LANE_OWNERSHIP.md` assigns `backend/app/connectors/`, `backend/tests/connectors/`, and `tests/fixtures/connectors/` to the connector integration zone.
- `SourceRetrievalRunContract` is the connector lifecycle/provenance contract.
- `EvidenceContract` is the connector output contract before evidence storage, claims, or reports.
- D-005 records `source.ingest_runs` as provenance authority and `jobs.job_queue` as future async orchestration.

## Proposed design

Add `StaticFloodFixtureConnector` under `backend/app/connectors/`. It accepts a local fixture file path, rejects URI-like inputs, parses one retrieval run plus evidence inputs, and validates that:

- the retrieval run uses the configured connector name;
- every emitted evidence input is in the `flood` domain;
- successful runs emit at least one non-failure evidence record;
- failed or blocked runs emit SOURCE_FAILURE evidence;
- connector code does not import claim or report modules.

## Bottom-up sequence

1. Add local success and failure fixture JSON under `tests/fixtures/connectors/`.
2. Add the fixture connector implementation under `backend/app/connectors/`.
3. Add connector-zone tests under `backend/tests/connectors/`.
4. Run targeted connector tests and full Windows-native verification.

## Files likely to change

| File | Expected change |
|---|---|
| `backend/app/connectors/__init__.py` | Export connector contract symbols |
| `backend/app/connectors/flood_fixture.py` | Static fixture connector implementation |
| `backend/tests/connectors/test_flood_fixture_connector.py` | Connector contract tests |
| `tests/fixtures/connectors/flood_success.json` | Success fixture |
| `tests/fixtures/connectors/flood_failure.json` | Failure fixture |
| `plans/connector-2026-06-04-fixture-flood.md` | Connector-zone plan |
| `state/connector-state.md` | Connector-zone state |

## Tests / verification

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/connectors
ruff check app/connectors tests/connectors
mypy app/connectors tests/connectors
Set-Location ..
.\scripts\verify.ps1
git diff --check
```

## Risks and blockers

| Risk / blocker | Handling |
|---|---|
| Connector accidentally becomes report or claim code | Tests assert no claim/report imports in connector module |
| Fixture path accidentally behaves like a live URL | Connector rejects URI-like inputs |
| Runtime evidence shape drifts from Lane C contract | Connector builds `EvidenceContract` instances |
| Retrieval provenance is bypassed | Connector requires `SourceRetrievalRunContract` |

## Decision log

- 2026-06-04: Keep CON-001 as a contract slice only. It produces typed retrieval/evidence inputs and does not persist or evaluate claims.

## Progress log

- 2026-06-04: Plan created from root `main` after D-005 (`dc3c38e`).
- 2026-06-04: CON-001 implemented as a fixture-only contract slice. `StaticFloodFixtureConnector` reads local JSON, rejects URI-like paths, emits `SourceRetrievalRunContract` plus `EvidenceContract` inputs, covers success/failure fixtures, and avoids claim/report imports.
- 2026-06-04: CON-003 implemented as a connector-zone evidence-ingestion adapter. It depends on an injected public evidence-ingestion port, routes normal evidence to `create_observation`, routes source-failure templates to `create_source_failure`, skips duplicate deterministic evidence IDs, fingerprints source failures for repeated fixture idempotency, and avoids claim/report imports.

## CON-002 Evidence-Ingestion Handoff

Status: complete on 2026-06-04 as a handoff/boundary decision. No Lane C implementation, shared schema, migration, live connector, report/API, or claim code changed.

### Current Service Authority

| Surface | Current authority | Handoff implication |
|---|---|---|
| Connector output | `FloodFixtureConnectorResult` with `SourceRetrievalRunContract` plus `EvidenceContract` inputs | Connector zone owns local fixture parsing, connector validation, and typed handoff values. |
| Normal evidence persistence | `EvidenceService.create_observation(evidence)` | Connector ingestion adapter can call the public Lane C service with non-failure source-derived `EvidenceContract` inputs. |
| Source-failure persistence | `EvidenceService.create_source_failure(...)` | Connector ingestion adapter must use the public Lane C source-failure API and treat the returned evidence as persistence authority. It must not call private Lane C helpers. |
| Idempotency | `EvidenceService.evidence_exists(...)`, `list_by_area(...)`, and repository duplicate rejection | Adapter should skip already-stored deterministic evidence IDs and use an explicit source-failure fingerprint for public API-created failure records. |
| Retrieval provenance | `SourceRetrievalRunContract` / `source.ingest_runs` | Connector zone owns retrieval-run handoff to Lane A provenance. Evidence ingestion must not replace source retrieval provenance. |

### Boundary Decision

The next ingestion adapter belongs in the connector integration zone, not Lane C. It should depend on an injected evidence-ingestion port that mirrors only the Lane C public service methods needed by connectors:

- `create_observation(evidence: EvidenceContract) -> EvidenceContract`
- `create_source_failure(...) -> EvidenceContract`
- `evidence_exists(evidence_id) -> bool`
- `list_by_area(area_id) -> list[EvidenceContract]`

The adapter must not import Lane C repositories, DB sessions, rule/claim modules, report modules, or private Lane C service helpers. Lane C remains the owner of validation, audit behavior, repository semantics, and any new public method if stronger source-failure preservation is required.

### Persistence Mapping

1. Persist or record the connector retrieval run through Lane A provenance before evidence ingestion.
2. For connector evidence where `is_source_failure` is false, call `create_observation(evidence)`.
3. For connector evidence where `is_source_failure` is true, call `create_source_failure` using the connector input's area, source, method, caveat, evidence code, domain, observation, and observed value.
4. Treat the returned `EvidenceContract` as the persisted failure authority because the current public source-failure API constructs the stored evidence record.
5. Do not feed connector outputs into claims or reports until persisted evidence has passed Lane C validation.

### Known Contract Gaps

- Current `EvidenceContract` does not carry `ingest_run_id`, even though `evidence.observations` has an `ingest_run_id` column in the DB spine.
- Current SQLAlchemy evidence persistence does not round-trip `dataset_version_id` from `EvidenceContract`.
- Current public source-failure creation does not preserve a connector-provided source-failure `evidence_id`, `dataset_version_id`, or `observed_at`.

These are not CON-002 code changes. If future connector work requires durable retrieval-run/evidence linkage or exact source-failure ID preservation, coordinate a Lane C/schema follow-up before implementation.

### Boundary Debate

| Option | Argument for | Argument against | Decision |
|---|---|---|---|
| Connector adapter writes directly to `EvidenceRepository` | Simple persistence path | Bypasses Lane C service validation, production-use checks, payload validation, and audit hooks | Rejected |
| Connector adapter calls public `EvidenceService` methods | Preserves Lane C validation boundary and avoids Lane C file edits | Source-failure API does not preserve every connector-provided field | Accepted for next adapter slice |
| Modify Lane C now to accept source-failure `EvidenceContract` directly | Stronger field preservation | Violates CON-002 no-Lane-C-change scope and overlaps Session 1 Lane C work | Deferred |

### Next Slice

CON-003 should implement a connector-zone ingestion adapter against the public evidence-ingestion port above, with tests proving:

- normal flood evidence calls `create_observation`;
- source-failure evidence calls `create_source_failure`;
- duplicate deterministic evidence IDs are skipped;
- source-failure fingerprints prevent duplicate failures on repeated fixture runs;
- no claim/report shortcuts are introduced.

## CON-003 Evidence-Ingestion Adapter

Status: complete on 2026-06-04. No Lane C implementation, shared schema, migration, live connector, report/API, or claim code changed.

### Implemented Design

`ConnectorEvidenceIngestionAdapter` lives in the connector integration zone and accepts an injected `EvidenceIngestionPort` with only the public methods recorded in CON-002. The adapter:

- skips evidence whose deterministic `evidence_id` already exists;
- sends non-failure connector evidence to `create_observation`;
- sends source-failure connector inputs to `create_source_failure`;
- fingerprints source failures by area, source, method, evidence code, domain, observation, caveat, and normalized observed value so repeated fixture ingestion does not create duplicate public-API-generated failure records;
- rejects inconsistent source-failure flags before persistence;
- does not import claim, report, DB-session, repository, or live I/O modules.

### Verification

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/connectors
ruff check app/connectors tests/connectors
mypy app/connectors tests/connectors
py -3.12 -m pytest --collect-only -q
Set-Location ..
.\scripts\verify.ps1
git diff --check
```

Result: connector tests pass (11 tests); connector ruff clean; connector mypy clean; full PowerShell verification passes with 274 collected backend tests, lint clean, mypy clean (98 source files), and DB smoke skipped by default; whitespace check clean.

### Remaining Gap

CON-003 does not persist `SourceRetrievalRunContract`. The next connector slice should define or implement a connector-zone retrieval-run provenance adapter against an injected public Lane A/source provenance port before claiming a complete connector ingest workflow.
