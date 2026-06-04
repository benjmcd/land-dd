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
- 2026-06-04: CON-004 implemented as a connector-zone retrieval-run provenance adapter. It depends on an injected source retrieval provenance port, records deterministic `SourceRetrievalRunContract` values without Lane A repository imports, skips duplicate `ingest_run_id` values, and keeps evidence ingestion separate from retrieval provenance.
- 2026-06-04: CON-005 implemented as a fixture-only connector ingest workflow. It composes the static flood fixture connector, retrieval provenance adapter, and evidence ingestion adapter; records retrieval provenance before evidence ingestion; proves repeated fixture workflow idempotency; and keeps live I/O, Lane A/C repository imports, claims, reports, schemas, and DB sessions out of scope.
- 2026-06-04: CON-006 implemented the connector-owned public-service wiring path that is currently possible without Lane A/C repository imports. `build_fixture_workflow_with_public_services` wires the fixture workflow to public Lane C `EvidenceService` methods through the evidence adapter and requires an identity-preserving retrieval provenance port. The flood source-failure fixture now uses Lane C's controlled source-failure payload keys.

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

## CON-004 Retrieval-Run Provenance Adapter

Status: complete on 2026-06-04. No Lane A implementation, repository, shared schema, migration, live connector, report/API, evidence/claim, or DB-session code changed.

### Implemented Design

`ConnectorRetrievalProvenanceAdapter` lives in the connector integration zone and accepts an injected `SourceRetrievalProvenancePort`. The port intentionally preserves `SourceRetrievalRunContract` as the authority value so fixture connector `ingest_run_id` and `dataset_version_id` are not lost before evidence ingestion.

The adapter:

- records connector retrieval runs before evidence ingestion;
- skips duplicate deterministic `ingest_run_id` values;
- returns recorded/skipped run state explicitly;
- does not import Lane A source registry services or repositories;
- does not import evidence, claim, report, DB-session, or live I/O modules.

### Boundary Note

Current Lane A `SourceProvenanceService.record_retrieval_run(...)` is a public service, but its current signature creates a new `SourceRetrievalRunContract` and does not accept a connector-provided `ingest_run_id`. The connector adapter therefore defines the required injected port shape without modifying Lane A. Concrete production wiring needs either a Lane A public method that records a supplied `SourceRetrievalRunContract` or a Lane A-owned adapter that preserves the contract identity.

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

Result: connector tests pass (15 tests); connector ruff clean; connector mypy clean; full PowerShell verification passes with 278 collected backend tests, lint clean, mypy clean (100 source files), and DB smoke skipped by default; whitespace check clean.

### Next Slice

CON-005 should compose the fixture connector, retrieval provenance adapter, and evidence ingestion adapter into one fixture-only workflow. It must record retrieval provenance before evidence ingestion, preserve fixture-only/no-live-IO behavior, stay before claims/reports, and continue to use injected ports rather than Lane A/Lane C repositories.

## CON-005 Fixture Connector Ingest Workflow

Status: complete on 2026-06-04. No Lane A/C implementation, repository, shared schema, migration, live connector, report/API, claim, or DB-session code changed.

### Implemented Design

`FixtureConnectorIngestWorkflow` lives in the connector integration zone and composes:

- `StaticFloodFixtureConnector`
- `ConnectorRetrievalProvenanceAdapter`
- `ConnectorEvidenceIngestionAdapter`

The workflow loads a local fixture, records retrieval provenance, then ingests evidence. The result exposes the connector output, retrieval-provenance result, and evidence-ingestion result so callers can audit each stage independently.

### Verification

Tests prove:

- retrieval provenance is recorded before evidence ingestion for successful fixture evidence;
- blocked/source-failure fixture runs record retrieval provenance before routing source failure evidence;
- repeated fixture workflow runs skip duplicate retrieval runs and duplicate evidence;
- workflow code remains connector-owned and does not import live I/O, Lane A source registry, Lane C evidence/claims, reports, DB sessions, or schemas.

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

Result: connector tests pass (19 tests); connector ruff clean; connector mypy clean; full PowerShell verification passes with 282 collected backend tests, lint clean, mypy clean (102 source files), and DB smoke skipped by default; whitespace check clean.

### Remaining Gap

CON-005 proves the connector workflow boundary with injected ports only. Concrete production wiring still needs a Lane A-compatible public provenance port that preserves supplied `SourceRetrievalRunContract.ingest_run_id`, plus wiring to a public Lane C evidence-ingestion port. No connector workflow should claim durable DB-backed production ingestion until that wiring is implemented and DB-smoke verified.

## CON-006 Public-Service Workflow Wiring Handoff

Status: complete on 2026-06-04 as the connector-owned wiring path plus explicit Lane A handoff. No Lane A/C implementation, repository, shared schema, migration, live connector, report/API, claim, or DB-session code changed.

### Implemented Design

`build_fixture_workflow_with_public_services` composes a fixture workflow from:

- an identity-preserving `SourceRetrievalProvenancePort`;
- the public Lane C `EvidenceService`;
- an optional `StaticFloodFixtureConnector`.

This is the concrete public-service wiring path available today without crossing ownership boundaries. Lane C evidence ingestion is real public-service wiring: normal evidence calls `EvidenceService.create_observation`, source failures call `EvidenceService.create_source_failure`, duplicate checks call `EvidenceService.evidence_exists`, and source-failure fingerprinting uses `EvidenceService.list_by_area`.

The connector still does not wire directly to Lane A's current `SourceProvenanceService.record_retrieval_run(...)`, because that public method creates a fresh `SourceRetrievalRunContract` and cannot preserve connector-supplied `ingest_run_id`. CON-006 therefore keeps retrieval provenance behind the identity-preserving port and records the Lane A public-service follow-up explicitly.

### Fixture Alignment

`tests/fixtures/connectors/flood_failure.json` now uses Lane C's controlled source-failure payload keys:

- `failure_reason`
- `error_message`
- `retryable`

This lets the fixture workflow pass through the public `EvidenceService` validator without relaxing Lane C validation or adding schema changes.

### Verification

Tests prove:

- fixture workflow public wiring uses the public Lane C `EvidenceService` for normal evidence;
- fixture workflow public wiring uses the public Lane C `EvidenceService` for source failures;
- repeated public-service fixture workflow runs are idempotent across retrieval and evidence stages;
- the public wiring surface requires an identity-preserving retrieval provenance port;
- connector public wiring imports the public Lane C evidence service but does not import Lane C repositories, Lane A source registry modules, claims, reports, live I/O, schemas, or DB sessions.

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

Result: connector tests pass (23 tests); connector ruff clean; connector mypy clean; full PowerShell verification passes with 286 collected backend tests, lint clean, mypy clean (104 source files), and DB smoke skipped by default; whitespace check clean.

### Remaining Gap

The next connector task must coordinate or implement the Lane A public provenance method/adapter that can record a supplied `SourceRetrievalRunContract` while preserving `ingest_run_id`. Only after that is wired and DB-smoke verified should the project claim durable DB-backed connector workflow ingestion.

## CON-007 Lane A Public Provenance Identity Preservation

Status: complete on 2026-06-04 as a coordinated Lane A public-service change plus connector public wiring. No schema, migration, live connector, claim, report/API, or Lane A repository import in connector code was added.

### Implemented Design

Lane A `SourceProvenanceService` now exposes:

- `record_retrieval_run_contract(retrieval_run)` to validate and persist a supplied `SourceRetrievalRunContract` while preserving `ingest_run_id`;
- `retrieval_run_exists(ingest_run_id)` as the public duplicate-check method needed by connector retrieval provenance wiring.

Connector public wiring now includes `SourceProvenanceServiceRetrievalPort`, which adapts the public Lane A service to the connector `SourceRetrievalProvenancePort` without importing Lane A repositories. `build_fixture_workflow_with_public_lane_services(...)` composes that public Lane A provenance service with the public Lane C `EvidenceService`.

### Verification

Tests prove:

- public Lane A service recording preserves a supplied retrieval-run identity;
- duplicate supplied retrieval-run identities fail closed;
- SQLAlchemy-backed source provenance round-trips supplied `ingest_run_id` with DB smoke enabled;
- connector public wiring can use Lane A/Lane C public services without connector imports from Lane A repositories;
- full DB-enabled workspace verification passes.

```powershell
Set-Location backend
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/source_registry/test_source_provenance.py tests/connectors
ruff check app/source_registry/provenance_service.py app/connectors tests/source_registry/test_source_provenance.py tests/connectors
mypy app/source_registry/provenance_service.py app/connectors tests/source_registry/test_source_provenance.py tests/connectors
py -3.12 -m pytest --collect-only -q
Set-Location ..
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
git diff --check
```

Result: targeted DB-enabled source-provenance/connector tests pass (29 tests); targeted ruff clean; targeted mypy clean; full DB-enabled PowerShell verification passes with 289 collected backend tests, lint clean, mypy clean (104 source files), migrations/seeds apply, and DB smoke passes; whitespace check clean.

### Next Slice

CON-008 should prove a DB-backed fixture workflow smoke using public Lane A provenance wiring and public Lane C evidence wiring together. It must still remain fixture-only, avoid live I/O and claim/report shortcuts, and avoid schema changes unless separately planned.
