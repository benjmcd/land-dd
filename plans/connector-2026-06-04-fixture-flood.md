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
- 2026-06-04: CON-024 recorded the connector review action API implementation blocker. The current repo has no authenticated reviewer/operator principal dependency, so mutation-route implementation remains blocked even though repository-level request-fix, requeue, and cancel substrate exists.
- 2026-06-04: CON-025 added a local service-account reviewer principal dependency and focused API tests without registering a mutation route or changing OpenAPI.
- 2026-06-04: CON-026 accepted the connector review action route implementation subset and deferred route/OpenAPI changes to avoid conflict with Session 1's Lane C evidence-linkage/OpenAPI branch.

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

## CON-008 DB-Backed Fixture Workflow Smoke

CON-008 is complete. The connector public-service wiring now has a DB-enabled smoke test that composes:

- SQLAlchemy-backed Lane A `SourceProvenanceService` through `SourceProvenanceServiceRetrievalPort`;
- SQLAlchemy-backed Lane C `EvidenceService` through `ConnectorEvidenceIngestionAdapter`;
- the existing static local flood fixture connector and fixture-only ingest workflow.

The smoke seeds only the fixed local fixture prerequisites needed by `tests/fixtures/connectors/flood_success.json`: a fixture area, a fixture source, and the fixture dataset/version. It then runs the workflow twice. The first run records the connector-supplied `SourceRetrievalRunContract.ingest_run_id` in `source.ingest_runs` and persists the fixture evidence through public Lane C evidence methods. The second run proves idempotency by skipping the existing retrieval run and deterministic evidence ID. The test removes its fixture-owned DB rows before and after execution so interrupted prior local runs do not poison later DB verification.

### Boundary Preserved

This smoke does not introduce live I/O, claims, reports, schema changes, or production connector behavior. It also does not claim durable evidence-row linkage to `ingest_run_id`; that remains the previously recorded Lane C/schema coordination gap because the current SQLAlchemy evidence repository persists source identity in metadata and does not write `evidence.observations.ingest_run_id`.

### Validation

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/connectors/test_public_wiring.py
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/connectors/test_public_wiring.py
ruff check tests/connectors/test_public_wiring.py
mypy tests/connectors/test_public_wiring.py
Set-Location ..
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
git diff --check
```

Result: targeted connector public-wiring tests pass with DB smoke skipped by default (5 passed, 1 skipped); targeted DB-enabled connector public-wiring tests pass (6 passed); targeted ruff clean; targeted mypy clean; full DB-enabled PowerShell verification passes with 290 collected backend tests, lint clean, mypy clean (104 source files), migrations/seeds apply, and DB smoke passes; whitespace check clean.

### Next Slice

The fixture connector path is now proven through DB-backed public Lane A and Lane C services. The next Level 8 pass should choose between:

- source-failure DB-backed workflow smoke for blocked/unavailable fixture source behavior;
- a Lane C/schema coordination slice for durable `ingest_run_id` linkage on evidence rows;
- a connector run/status API or human-review handoff plan, if Level 9 workflow entry is preferred.

## CON-009 DB-Backed Source-Failure Fixture Workflow Smoke

CON-009 is complete. The connector public-service wiring now has a DB-enabled smoke for the blocked/unavailable fixture path in `tests/fixtures/connectors/flood_failure.json`. The smoke uses the same SQLAlchemy-backed public Lane A provenance service, public Lane C evidence service, and local fixture-only workflow as CON-008.

The first run records the connector-supplied blocked retrieval run in `source.ingest_runs` and persists a Lane C source-failure evidence record through `EvidenceService.create_source_failure(...)`. The second run proves idempotency by skipping the existing retrieval run and matching the persisted source-failure evidence by the connector adapter's source-failure fingerprint. The test removes fixture-owned DB rows before and after execution.

### Boundary Preserved

This smoke does not introduce live I/O, claims, reports, schema changes, or production connector behavior. It also preserves the existing exact-field boundary: public Lane C source-failure creation is persistence authority and generates the persisted source-failure evidence ID, so connector-provided source-failure IDs remain templates unless Lane C adds a public method for exact source-failure contract persistence.

### Validation

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/connectors/test_public_wiring.py
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/connectors/test_public_wiring.py
ruff check tests/connectors/test_public_wiring.py
mypy tests/connectors/test_public_wiring.py
Set-Location ..
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
git diff --check
```

Result: targeted connector public-wiring tests pass with DB smoke skipped by default (5 passed, 2 skipped); targeted DB-enabled connector public-wiring tests pass (7 passed); targeted ruff clean; targeted mypy clean; full DB-enabled PowerShell verification passes with 291 collected backend tests, lint clean, mypy clean (104 source files), migrations/seeds apply, and DB smoke passes; whitespace check clean.

### Next Slice

The connector fixture success and source-failure paths are now both proven through DB-backed public Lane A and Lane C services. The next Level 8 pass should choose between:

- a Lane C/schema coordination slice for durable `ingest_run_id` linkage on evidence rows;
- a connector run/status API or human-review handoff plan, if Level 9 workflow entry is preferred;
- broader fixture data-quality coverage if another connector fixture category is selected.

## CON-010 Connector Run/Status Review Packet

CON-010 is complete. The connector integration zone now exposes a pure review-packet projection over `FixtureConnectorIngestWorkflowResult` through `build_connector_run_review_packet(...)`. The packet summarizes:

- connector name, `ingest_run_id`, dataset version, retrieval status, timing, counts, log URI, and metrics;
- whether retrieval provenance was recorded or skipped;
- evidence input, created, skipped, and source-failure counts;
- created, skipped, and source-failure evidence IDs;
- review signals and deterministic human-review tasks.

### Boundary Preserved

This is a handoff/status surface only. It does not persist new data, add an API route, evaluate claims, build reports, perform live I/O, change schemas, or modify Lane A/B/C/D implementation files. The packet treats the existing workflow result as authority and keeps durable `ingest_run_id` evidence-row linkage and exact source-failure evidence ID preservation as separate Lane C/schema coordination gaps.

### Validation

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/connectors/test_review_packet.py tests/connectors/test_fixture_workflow.py
ruff check app/connectors tests/connectors/test_review_packet.py
mypy app/connectors tests/connectors/test_review_packet.py
py -3.12 -m pytest -q tests/connectors
ruff check app/connectors tests/connectors
mypy app/connectors tests/connectors
Set-Location ..
.\scripts\verify.ps1
git diff --check
```

Result: focused review-packet/fixture-workflow tests pass (8 tests); full connector tests pass with DB smoke skipped by default (28 passed, 2 skipped); connector ruff clean; connector mypy clean over 13 source/test files. Full workspace verification result is recorded in `state/VALIDATION_LOG.md`.

### Next Slice

The next Level 8 pass should choose one of:

- a Lane C/schema coordination slice for durable `ingest_run_id` linkage on evidence rows;
- exact source-failure evidence ID preservation if Lane C accepts a public exact-contract persistence method;
- a connector API/status endpoint or human-review queue surface that consumes the review packet without changing connector persistence semantics;
- broader fixture data-quality coverage if another connector fixture category is selected.

## CON-011 Connector Review Handoff Consumer

CON-011 is complete. The connector integration zone now exposes `build_connector_review_handoff(...)`, a pure consumer for CON-010 review packets. It classifies fixture workflow review packets into deterministic handoff dispositions:

- `needs_human_review` for packets with review-required signals;
- `ready_for_connector_qa` for successful fixture workflow packets that created evidence and need normal QA review;
- `idempotent_noop` for repeated fixture workflow packets that skipped existing retrieval/evidence records without requiring human review.

The handoff includes a queue name, priority, title, summary, tasks, signal codes, and `to_review_record()` for a JSON-safe record that future API or workflow code can consume without reinterpreting connector packet semantics.

### Boundary Preserved

This is a connector-local consumer surface only. It does not create a database queue, add API routes, evaluate claims, generate reports, perform live I/O, change schemas, or modify Lane A/B/C/D implementation files. Future API/status or durable human-review queue work can consume this surface, but must still be separately planned if it crosses Lane D/API or persistence ownership.

### Validation

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/connectors/test_review_handoff.py tests/connectors/test_review_packet.py
ruff check app/connectors tests/connectors/test_review_handoff.py tests/connectors/test_review_packet.py
mypy app/connectors tests/connectors/test_review_handoff.py tests/connectors/test_review_packet.py
py -3.12 -m pytest -q tests/connectors
ruff check app/connectors tests/connectors
mypy app/connectors tests/connectors
Set-Location ..
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
git diff --check
```

Result: focused review-handoff/review-packet tests pass (8 tests); full connector tests pass with DB smoke skipped by default (32 passed, 2 skipped); connector ruff clean; connector mypy clean over 15 source/test files; full DB-enabled PowerShell verification passes with 300 backend tests, lint clean, mypy clean over 109 source files, migrations/seeds apply, and DB smoke passes.

### Next Slice

The next Level 8 pass should choose one of:

- a coordinated Lane C/schema slice for durable `ingest_run_id` linkage on evidence rows;
- exact source-failure evidence ID preservation if Lane C accepts a public exact-contract persistence method;
- a Lane D/API status endpoint or durable human-review queue that consumes the connector review handoff;
- broader fixture data-quality coverage if another connector fixture category is selected.

## CON-012 Connector Fixture Quality Profile

CON-012 is complete. The connector integration zone now exposes `evaluate_flood_fixture_quality(...)`, a deterministic fixture quality profile over `FloodFixtureConnectorResult`.

The profile checks:

- retrieval timing, dataset-version presence, fixture-local log URI, and `fixture_only` metrics;
- retrieval status consistency with emitted non-failure/source-failure evidence;
- row-count consistency for successful fixture retrievals;
- evidence dataset-version alignment with the retrieval run;
- required geometry and spatial precision for non-failure spatial-intersection evidence;
- controlled source-failure payload keys and UNKNOWN confidence for source-failure evidence.

### Boundary Preserved

This is a connector-local fixture-quality evaluator only. It does not create API routes, durable queues, report output, claims, schema changes, live I/O, DB sessions, persistence behavior, Lane A/B/C/D implementation changes, durable `ingest_run_id` evidence-row linkage, or exact source-failure evidence ID preservation.

### Validation

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/connectors/test_fixture_quality.py
ruff check app/connectors tests/connectors/test_fixture_quality.py
mypy app/connectors tests/connectors/test_fixture_quality.py
py -3.12 -m pytest -q tests/connectors
ruff check app/connectors tests/connectors
mypy app/connectors tests/connectors
Set-Location ..
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
git diff --check
```

Result: focused fixture-quality tests pass (7 tests); full connector tests pass with DB smoke skipped by default (39 passed, 2 skipped); connector ruff clean; connector mypy clean over 17 source/test files; full DB-enabled PowerShell verification passes with 307 backend tests, lint clean, mypy clean over 111 source files, migrations/seeds apply, and DB smoke passes.

### Next Slice

The next Level 8 pass should choose one of:

- a coordinated Lane C/schema slice for durable `ingest_run_id` linkage on evidence rows;
- exact source-failure evidence ID preservation if Lane C accepts a public exact-contract persistence method;
- a Lane D/API status endpoint or durable human-review queue that consumes the connector review handoff and/or fixture quality profile;
- broader fixture data-quality coverage for another fixture category after that fixture is selected.

## CON-013 Connector Review Status API Surface

CON-013 is complete. The connector integration zone now exposes `build_connector_run_review_status(...)`, which composes a connector review handoff with a fixture quality profile into one JSON-safe status record. Lane D API now registers `GET /connector-runs/{ingest_run_id}/review-status`, backed by the existing `ApiServices` in-memory status store.

The status surface reports:

- review handoff queue, disposition, priority, tasks, and signal codes;
- connector name, `ingest_run_id`, dataset version, retrieval status, and evidence/source-failure counts;
- fixture quality pass/fail state, blocking issue count, and issue code/message records;
- `review_required` as true when either the handoff requires human review or fixture quality has blocking issues.

### Boundary Preserved

This is an API status surface and in-memory handoff store only. It does not create a durable queue, connector status table, schema/migration, live connector, DB-backed connector status repository, claims, reports, durable `ingest_run_id` evidence-row linkage, or exact source-failure evidence ID preservation. Unknown connector runs return 404 rather than manufacturing status.

### Validation

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/connectors/test_review_status.py tests/api/test_connector_review_status.py
ruff check app/connectors/review_status.py app/api/connectors.py app/api/dependencies.py app/main.py tests/connectors/test_review_status.py tests/api/test_connector_review_status.py
mypy app/connectors/review_status.py app/api/connectors.py app/api/dependencies.py app/main.py tests/connectors/test_review_status.py tests/api/test_connector_review_status.py
py -3.12 -m pytest -q tests/connectors tests/api -rA
ruff check app/connectors app/api app/main.py tests/connectors tests/api
mypy app/connectors app/api app/main.py tests/connectors tests/api
Set-Location ..
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
git diff --check
```

Result: focused review-status/API tests pass (8 tests); connector/API tests pass with DB smoke skipped by default (55 passed, 3 skipped); connector/API ruff clean; connector/API mypy clean over 33 source/test files; full DB-enabled PowerShell verification passes with 315 backend tests, lint clean, mypy clean over 115 source files, migrations/seeds apply, and DB smoke passes.

### Next Slice

The next Level 8 pass should choose one of:

- a coordinated Lane C/schema slice for durable `ingest_run_id` linkage on evidence rows;
- exact source-failure evidence ID preservation if Lane C accepts a public exact-contract persistence method;
- durable human-review queue persistence for connector review status after schema/queue ownership is planned;
- broader fixture data-quality coverage for another fixture category after that fixture is selected.

## CON-014 Durable Connector Review Queue

CON-014 is complete. The connector integration zone now exposes a durable queue adapter for connector review status records:

- `InMemoryConnectorReviewQueueRepository` for cheap fixture tests;
- `SqlAlchemyConnectorReviewQueueRepository` for DB-backed persistence into `jobs.job_queue`;
- `ConnectorReviewQueueItem` as the queue item projection over a connector review status.

The durable adapter writes `job_type = "connector_review_status"` rows with idempotency key `connector_review_status:<ingest_run_id>`. The JSON payload includes the connector name, `ingest_run_id`, dataset version, retrieval status, review disposition, review-required flag, signal codes, and fixture quality result. Human-review-required statuses are queued with `status = "needs_review"` and priority `10`; non-blocking connector QA statuses use `status = "queued"` and priority `100`.

### Boundary Preserved

This is durable queue persistence only. It does not create a worker, scheduler, queue dashboard, new schema/migration, live connector, claim/report shortcut, DB-backed connector status API read path, durable `ingest_run_id` evidence-row linkage, or exact source-failure evidence ID preservation. `source.ingest_runs` remains connector attempt provenance and lifecycle authority; `jobs.job_queue` references it through the payload and idempotency key.

### Validation

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/connectors/test_review_queue.py
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/connectors/test_review_queue.py
ruff check app/connectors/review_queue.py tests/connectors/test_review_queue.py app/connectors/__init__.py
mypy app/connectors/review_queue.py tests/connectors/test_review_queue.py app/connectors/__init__.py
py -3.12 -m pytest -q tests/connectors
ruff check app/connectors tests/connectors
mypy app/connectors tests/connectors
Set-Location ..
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
git diff --check
```

Result: focused queue tests pass with DB smoke skipped by default (2 passed, 1 skipped); DB-enabled queue tests pass (3 tests); connector tests pass with DB smoke skipped by default (45 passed, 3 skipped); connector ruff clean; connector mypy clean over 21 source/test files; full DB-enabled PowerShell verification passes with 318 backend tests, lint clean, mypy clean over 117 source files, migrations/seeds apply, and DB smoke passes.

### Next Slice

The next Level 8 pass should choose one of:

- a coordinated Lane C/schema slice for durable `ingest_run_id` linkage on evidence rows;
- exact source-failure evidence ID preservation if Lane C accepts a public exact-contract persistence method;
- worker/API retrieval behavior for queued connector review items after queue execution semantics are planned;
- broader fixture data-quality coverage for another fixture category after that fixture is selected.

## CON-015 Connector Review Queue API Retrieval

CON-015 is complete. Lane D API now exposes read-only queue-item retrieval for connector review queue records through `GET /connector-runs/{ingest_run_id}/review-queue`.

The endpoint uses the connector-owned queue repository already wired through `ApiServices`:

- in-memory API services use `InMemoryConnectorReviewQueueRepository`;
- DB-backed API services use `SqlAlchemyConnectorReviewQueueRepository`;
- unknown queue items return 404;
- successful responses expose job ID, `ingest_run_id`, job type, job status, priority, idempotency key, payload, and creation time.

### Boundary Preserved

This is read-only API retrieval for queued connector review items. It does not create, mutate, lock, retry, cancel, complete, or lease jobs; does not add a worker, scheduler, queue dashboard, live connector, schema/migration, claim/report shortcut, durable `ingest_run_id` evidence-row linkage, or exact source-failure evidence ID preservation. Queue state remains orchestration state; `source.ingest_runs` remains connector provenance and lifecycle authority.

### Validation

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/api/test_connector_review_status.py tests/api/test_connector_review_queue_db.py
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/api/test_connector_review_queue_db.py
ruff check app/api/connectors.py app/api/dependencies.py tests/api/test_connector_review_status.py tests/api/test_connector_review_queue_db.py
mypy app/api/connectors.py app/api/dependencies.py tests/api/test_connector_review_status.py tests/api/test_connector_review_queue_db.py
py -3.12 -m pytest -q tests/connectors tests/api -rA
ruff check app/connectors app/api app/main.py tests/connectors tests/api
mypy app/connectors app/api app/main.py tests/connectors tests/api
Set-Location ..
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
git diff --check
```

Result: focused queue-retrieval API tests pass with DB smoke skipped by default (6 passed, 1 skipped); DB-enabled queue-retrieval API test passes (1 test); connector/API tests pass with DB smoke skipped by default (59 passed, 5 skipped); connector/API ruff clean; connector/API mypy clean over 36 source/test files; full DB-enabled PowerShell verification passes with 321 backend tests, lint clean, mypy clean over 118 source files, migrations/seeds apply, and DB smoke passes.

### Next Slice

The next Level 8 pass should choose one of:

- a coordinated Lane C/schema slice for durable `ingest_run_id` linkage on evidence rows;
- exact source-failure evidence ID preservation if Lane C accepts a public exact-contract persistence method;
- worker execution/lease semantics for connector review queue items after a worker ADR is accepted;
- broader fixture data-quality coverage for another fixture category after that fixture is selected.

## CON-016 Connector Review Queue Worker Lease Semantics

CON-016 is complete. The connector review queue repository now exposes worker lease and finish semantics for queued connector review items:

- `lease_next(worker_id=...)` leases the next eligible `connector_review_status` item by priority and creation time;
- eligible items are limited to `queued` or `needs_review` rows with remaining attempts;
- leased items transition to `running`, increment `attempts`, and record lock/start metadata;
- `mark_succeeded(job_id)` completes only running connector review queue jobs;
- `mark_failed(job_id, error=...)` fails only running connector review queue jobs and records the failure error.

The DB-backed implementation uses existing `jobs.job_queue` columns and does not require a schema migration. The in-memory implementation mirrors the same fail-closed transition rules for cheap connector tests.

### Boundary Preserved

This is repository-level worker lease and finish behavior only. It does not add a long-running worker process, scheduler, background loop, API mutation route, retry/requeue policy, cancellation path, queue dashboard, live connector execution, evidence persistence, claims, reports, schema/migration changes, durable `ingest_run_id` evidence-row linkage, or exact source-failure evidence ID preservation. `source.ingest_runs` remains connector attempt provenance and lifecycle authority; `jobs.job_queue` remains orchestration state.

### Validation

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/connectors/test_review_queue.py
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/connectors/test_review_queue.py
ruff check app/connectors/review_queue.py tests/connectors/test_review_queue.py app/connectors/__init__.py
mypy app/connectors/review_queue.py tests/connectors/test_review_queue.py app/connectors/__init__.py
py -3.12 -m pytest -q tests/connectors
ruff check app/connectors tests/connectors
mypy app/connectors tests/connectors
Set-Location ..
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
git diff --check
```

Result: focused queue tests pass with DB smoke skipped by default (4 passed, 2 skipped); DB-enabled queue tests pass (6 tests); focused queue ruff clean; focused queue mypy clean over 3 source/test files. Full connector and workspace verification results are recorded in `state/VALIDATION_LOG.md`.

### Next Slice

The next Level 8 pass should choose one of:

- coordinate the Lane C/schema result for durable `ingest_run_id` evidence linkage after Session 1's source-failure identity-preservation slice lands;
- expose worker result/status behavior through a planned API or review workflow after queue mutation semantics are stable;
- add retry/requeue/cancel semantics with a separate ADR if worker execution needs them;
- broaden fixture data-quality coverage for another selected fixture category.

## CON-017 Connector Queue Worker Read Model

CON-017 is complete. The existing read-only connector review queue endpoint now surfaces worker-state metadata already carried by `ConnectorReviewQueueItem` and `jobs.job_queue`:

- attempts and max attempts;
- lock owner and lock timestamp;
- start and finish timestamps;
- last error.

This lets API consumers inspect queued, running, succeeded, or failed connector review queue state after CON-016 without adding job mutation routes.

### Boundary Preserved

This is read-only API surfacing for worker state. It does not lease, complete, fail, retry, requeue, cancel, create, or execute jobs; does not add a scheduler, background loop, queue dashboard, live connector execution, evidence persistence, claims, reports, schema/migration changes, durable `ingest_run_id` evidence-row linkage, or exact source-failure evidence ID preservation. `source.ingest_runs` remains connector attempt provenance and lifecycle authority; `jobs.job_queue` remains orchestration state.

### Validation

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/api/test_connector_review_status.py tests/api/test_connector_review_queue_db.py
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/api/test_connector_review_queue_db.py
ruff check app/api/connectors.py tests/api/test_connector_review_status.py tests/api/test_connector_review_queue_db.py
mypy app/api/connectors.py tests/api/test_connector_review_status.py tests/api/test_connector_review_queue_db.py
```

Result: focused queue API tests pass with DB smoke skipped by default (7 passed, 2 skipped); DB-enabled queue API tests pass (2 tests); focused queue API ruff clean; focused queue API mypy clean over 3 source/test files. Full connector/API and workspace verification results are recorded in `state/VALIDATION_LOG.md`.

### Next Slice

The next Level 8 pass should choose one of:

- integrate or preserve Session 1's Lane C source-failure identity-preservation branch after it rebases onto CON-017;
- add retry/requeue/cancel semantics with a separate ADR if worker execution needs them;
- add an explicit human-review workflow action surface after mutation semantics are planned;
- broaden fixture data-quality coverage for another selected fixture category.

## CON-018 Connector Queue Retry And Cancel Semantics

CON-018 is complete. The connector review queue repository now exposes explicit retry/requeue and cancellation semantics:

- `requeue_failed(job_id, reason=..., not_before=...)` requeues only failed connector review queue jobs with remaining attempts;
- requeue keeps the current attempt count, clears lock/finish metadata, schedules the next lease through `not_before`, and records a requeue reason;
- `cancel(job_id, reason=...)` cancels queued, needs-review, running, or failed connector review queue jobs and records a cancellation reason;
- succeeded and already-cancelled jobs cannot be cancelled.

Default connector review queue jobs still use `max_attempts = 1`, so retry remains fail-closed unless a future planned producer/operator explicitly permits additional attempts.

### Boundary Preserved

This is repository-level retry/requeue/cancel behavior only. It does not add API-side mutation, automatic retry policy, timeout handling, a scheduler, background loop, queue dashboard, live connector execution, evidence persistence, claims, reports, schema/migration changes, durable `ingest_run_id` evidence-row linkage, or exact source-failure evidence ID preservation. `source.ingest_runs` remains connector attempt provenance and lifecycle authority; `jobs.job_queue` remains orchestration state.

### Validation

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/connectors/test_review_queue.py
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/connectors/test_review_queue.py
ruff check app/connectors/review_queue.py tests/connectors/test_review_queue.py app/connectors/__init__.py
mypy app/connectors/review_queue.py tests/connectors/test_review_queue.py app/connectors/__init__.py
```

Result: focused queue tests pass with DB smoke skipped by default (6 passed, 3 skipped); DB-enabled queue tests pass (9 tests); focused queue ruff clean; focused queue mypy clean over 3 source/test files. Full connector/API and workspace verification results are recorded in `state/VALIDATION_LOG.md`.

### Next Slice

The next Level 8 pass should choose one of:

- integrate or preserve Session 1's Lane C source-failure identity-preservation branch after it rebases onto CON-018;
- add an explicit human-review action workflow after API mutation semantics are planned;
- expose retry/cancel state through API after deciding whether mutation routes are in scope;
- broaden fixture data-quality coverage for another selected fixture category.

## CON-019 Connector Source-Failure Evidence ID Adoption

CON-019 is complete. The connector evidence-ingestion adapter now adopts Lane C TC-180's public source-failure ID preservation boundary:

- `EvidenceIngestionPort.create_source_failure(...)` accepts an optional `evidence_id`;
- connector source-failure evidence passes its deterministic `EvidenceContract.evidence_id` into the public Lane C source-failure creation method;
- repeated source-failure fixture runs check existing stored source-failure fingerprints before deterministic-ID duplicate fallback, so idempotent repeats return stored authority;
- connector/API test fake evidence ports preserve supplied source-failure IDs, matching the public service boundary;
- DB-backed public wiring proves the fixture source-failure evidence ID is persisted and returned unchanged.

### Boundary Preserved

This is connector-side adoption of an already-landed Lane C public service capability. It does not edit Lane C evidence service or schemas, add a migration, add live connector behavior, add claim/report shortcuts, mutate queue APIs, change worker semantics, or add durable `ingest_run_id` evidence-row linkage. Source retrieval runs remain connector provenance and lifecycle authority; evidence rows now preserve connector-supplied source-failure IDs but still do not carry retrieval-run lineage.

### Validation

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/connectors/test_evidence_ingestion_adapter.py tests/connectors/test_fixture_workflow.py tests/connectors/test_public_wiring.py
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/connectors/test_public_wiring.py::test_db_backed_public_lane_service_fixture_source_failure_is_idempotent
ruff check app/connectors/evidence_ingestion.py tests/connectors/test_evidence_ingestion_adapter.py tests/connectors/test_fixture_workflow.py tests/connectors/test_public_wiring.py tests/connectors/test_review_packet.py tests/connectors/test_review_handoff.py tests/connectors/test_review_queue.py tests/connectors/test_review_status.py tests/api/test_connector_review_status.py tests/api/test_connector_review_queue_db.py
mypy app/connectors/evidence_ingestion.py tests/connectors/test_evidence_ingestion_adapter.py tests/connectors/test_fixture_workflow.py tests/connectors/test_public_wiring.py tests/connectors/test_review_packet.py tests/connectors/test_review_handoff.py tests/connectors/test_review_queue.py tests/connectors/test_review_status.py tests/api/test_connector_review_status.py tests/api/test_connector_review_queue_db.py
py -3.12 -m pytest -q tests/connectors tests/api -rA
ruff check app/connectors app/api app/main.py tests/connectors tests/api
mypy app/connectors app/api app/main.py tests/connectors tests/api
```

Result: focused connector adoption tests pass with DB smoke skipped by default (15 passed, 2 skipped); DB-backed public wiring source-failure ID test passes (1 test); targeted ruff clean; targeted mypy clean over 10 source/test files; broader connector/API tests pass with DB smoke skipped by default (64 passed, 8 skipped); broader connector/API ruff clean; broader connector/API mypy clean over 36 source/test files. Full workspace verification results are recorded in `state/VALIDATION_LOG.md`.

### Next Slice

The next Level 8 pass should choose one of:

- add an explicit human-review action workflow after API mutation semantics are planned;
- expose retry/cancel state or mutation routes through API only after route semantics are accepted;
- coordinate durable `ingest_run_id` evidence-row linkage with Lane C/schema ownership;
- broaden fixture data-quality coverage for another selected fixture category.

## CON-020 Connector Fixture Identity And Timing Quality

CON-020 is complete. The connector fixture quality profile now checks two additional fixture-local data-quality categories:

- duplicate evidence IDs within one fixture connector run;
- evidence `observed_at` timestamps that precede retrieval start or follow retrieval finish.

These checks strengthen fixture review before ingestion without adding schema changes or cross-lane service dependencies.

### Boundary Preserved

This is a connector-local fixture-quality extension only. It does not add live I/O, API mutation routes, queue behavior, persistence, claims, reports, shared schema edits, Lane A/B/C implementation changes, or durable `ingest_run_id` evidence-row linkage. The source-retrieval run remains connector provenance/lifecycle authority; this pass only validates fixture evidence identity uniqueness and observation timing against that run.

### Validation

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/connectors/test_fixture_quality.py
ruff check app/connectors/fixture_quality.py tests/connectors/test_fixture_quality.py
mypy app/connectors/fixture_quality.py tests/connectors/test_fixture_quality.py
```

Result: focused fixture-quality tests pass (9 tests); targeted ruff clean; targeted mypy clean over 2 source/test files. Full workspace verification results are recorded in `state/VALIDATION_LOG.md`.

### Next Slice

The next Level 8 pass should choose one of:

- add an explicit human-review action workflow after API mutation semantics are planned;
- expose retry/cancel state or mutation routes through API only after route semantics are accepted;
- coordinate durable `ingest_run_id` evidence-row linkage with Lane C/schema ownership;
- propose report-run schema only after nested schema scope is settled;
- broaden fixture data-quality coverage for another selected fixture category.

## CON-021 Connector Human Review Action Semantics Plan

CON-021 is complete as a planning-only action semantics slice. ADR `docs/adr/lane-d-0011-connector-human-review-actions.md` defines the future human-review action vocabulary for connector review queue rows:

- `acknowledge`;
- `approve_for_connector_qa`;
- `request_fixture_fix`;
- `requeue_after_fix`;
- `cancel_review`.

These are future workflow/API semantics only. No route, repository method, worker, scheduler, dashboard, migration, evidence mutation, claim/report behavior, live connector execution, schema edit, hook config, or POSIX script was added.

### Boundary Preserved

Human review actions operate over `connector_review_status` queue rows only. `source.ingest_runs` remains connector provenance and lifecycle authority. `jobs.job_queue` remains review orchestration state. Evidence, claims, reports, source schemas, job schemas, connector runtime, and API mutation routes remain unchanged.

Any future API mutation slice must explicitly plan route names, request/response models, reviewer identity, reason requirements, idempotency, auth/security expectations, and fail-closed transition behavior before code.

### Validation

```powershell
.\scripts\verify.ps1
```

Result: full DB-enabled PowerShell verification passes with 344 backend tests, lint clean, mypy clean over 120 source files, migrations/seeds apply, and DB smoke passes.

### Next Slice

The next Level 8 pass should choose one of:

- implement a narrow human-review action API only after route semantics, reviewer identity, and auth expectations are accepted;
- expose retry/cancel mutation routes only after route semantics are accepted;
- coordinate durable `ingest_run_id` evidence-row linkage with Lane C/schema ownership;
- define future report metadata extensions;
- broaden fixture data-quality coverage for another selected fixture category.

## CON-022 Connector Human Review API Semantics Plan

CON-022 is complete as a planning-only route/reviewer/auth semantics slice. ADR `docs/adr/lane-d-0012-connector-human-review-api-semantics.md` accepts a future narrow route:

- `POST /connector-runs/{ingest_run_id}/review-actions`

Accepted future request fields:

- `action`;
- `reviewer_id`;
- `reason`;
- `idempotency_key`;
- `expected_status`.

Accepted future response fields:

- `ingest_run_id`;
- `job_id`;
- `action`;
- `status`;
- `reviewer_id`;
- `reason`;
- `idempotency_key`;
- `created_at`;
- `queue_item`.

### Boundary Preserved

This is route semantics only. It does not add a route, repository method, queue code, auth code, OpenAPI change, connector runtime, evidence mutation, claim/report behavior, schema, migration, live I/O, hook config, or POSIX script.

Future implementation must require an authenticated reviewer/operator boundary, reject empty or mismatched reviewer identity, fail closed for missing queue rows and invalid transitions, preserve `source.ingest_runs` as provenance authority, and preserve `jobs.job_queue` as review orchestration state.

### Validation

```powershell
.\scripts\verify.ps1
```

Result: pass on 2026-06-04. Full Windows PowerShell verification passed with 344 backend tests collected/passing, lint clean, mypy clean over 120 source files, migrations/seeds applied, and DB smoke passed.

### Next Slice

The next Level 8 pass should choose one of:

- add a narrow reviewer/operator principal dependency or documented service-account delegation rule before any review-action mutation route;
- implement the narrow human-review action API only after auth/reviewer identity enforcement and required queue transition substrate are accepted;
- expose retry/cancel mutation behavior through the accepted action route or a separate accepted route after auth is satisfied;
- coordinate durable `ingest_run_id` evidence-row linkage with Lane C/schema ownership;
- define future report metadata extensions;
- broaden fixture data-quality coverage for another selected fixture category.

## CON-023 Connector Fixture Evidence Provenance Quality

CON-023 extends the connector-local flood fixture quality evaluator to fail closed when evidence omits reviewer-critical provenance text.

New blocking issue codes:

- `evidence_provenance_text_missing`;
- `evidence_caveat_missing`;
- `source_observation_source_date_missing`.

The evaluator now requires fixture evidence to include non-empty evidence code, observation, method code, method version, and caveat. Non-failure source observations must also include `source_date`. Source-failure evidence may continue to omit `source_date` because the retrieval failure itself is the evidence.

### Boundary Preserved

This is connector-local fixture-quality validation only. It does not add API routes, OpenAPI changes, durable queue behavior, repository methods, source/evidence/claim/report behavior, schemas, migrations, live I/O, hook config, or POSIX scripts.

### Validation

```powershell
cd backend
py -3.12 -m pytest -q tests/connectors/test_fixture_quality.py
ruff check app/connectors/fixture_quality.py tests/connectors/test_fixture_quality.py
mypy app/connectors/fixture_quality.py tests/connectors/test_fixture_quality.py
cd ..
.\scripts\verify.ps1
```

Result: pass on 2026-06-04. Fixture-quality tests cover 10 cases; focused ruff clean; focused mypy clean over 2 source files. Full Windows PowerShell verification passed with 351 backend tests collected/passing, lint clean, mypy clean over 121 source files, migrations/seeds applied, and DB smoke passed.

### Next Slice

The next Level 8 pass should choose one of:

- add a narrow reviewer/operator principal dependency or documented service-account delegation rule before any review-action mutation route;
- implement the narrow human-review action API only after auth/reviewer identity enforcement and required queue transition substrate are accepted;
- expose retry/cancel mutation behavior through the accepted action route or a separate accepted route after auth is satisfied;
- coordinate durable `ingest_run_id` evidence-row linkage with Lane C/schema ownership;
- define future report metadata extensions;
- broaden fixture data-quality coverage for another selected fixture category.

## CON-024 Connector Review Action API Auth Blocker

CON-024 is complete as an implementation-blocker decision. ADR `docs/adr/lane-d-0014-connector-review-api-auth-blocker.md` records that the current repo has no authenticated reviewer/operator principal dependency, so the future `POST /connector-runs/{ingest_run_id}/review-actions` mutation route must not be implemented by trusting caller-supplied identity alone.

### Current Authority

- `backend/app/api/connectors.py` exposes read-only connector review status and queue retrieval.
- `backend/app/connectors/review_queue.py` has repository-level queue mutation methods for failure, requeue, and cancellation.
- `docs/adr/lane-d-0012-connector-human-review-api-semantics.md` requires an authenticated reviewer/operator boundary before mutation-route implementation.

### Decision

The following actions remain blocked at API level:

- `acknowledge`, because reviewer ownership storage is not accepted;
- `approve_for_connector_qa`, because no accepted queue transition maps it to current persistence;
- `request_fixture_fix`, `requeue_after_fix`, and `cancel_review`, because API surfacing still needs authenticated reviewer identity matching before mutating `jobs.job_queue`.

Header-only reviewer identity is not sufficient unless a future ADR explicitly accepts a local service-account delegation rule and its limits.

### Boundary Preserved

This is an auth/blocker decision only. It does not add API routes, OpenAPI changes, queue code, repository methods, schemas, migrations, connector runtime behavior, live I/O, hook config, POSIX scripts, evidence behavior, claim behavior, or report behavior.

### Validation

```powershell
git diff --check
.\scripts\verify.ps1
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

Result: pass on 2026-06-04. Whitespace check clean; default Windows PowerShell verification passed with 351 backend tests collected/passing, lint clean, mypy clean over 121 source files, and DB smoke skipped by default; DB-enabled Windows PowerShell verification passed with 351 backend tests collected/passing, lint clean, mypy clean over 121 source files, migrations/seeds applied, and DB smoke passed.

### Next Slice

The next API-enabling slice should add a narrow reviewer/operator principal dependency and tests, or document a service-account delegation rule, before any connector review mutation route is added. Other low-conflict work can continue in report metadata extensions or fixture-quality coverage while Session 1 owns Lane C evidence linkage.

## CON-025 Connector Reviewer Principal Boundary

CON-025 is complete as a narrow API-auth substrate slice. ADR `docs/adr/lane-d-0015-connector-reviewer-principal.md` accepts a local service-account reviewer principal dependency for future connector review mutation routes.

### Implemented Surface

- `backend/app/api/reviewer_auth.py` defines `ReviewerPrincipal` and `LocalServiceAccountReviewerAuth`.
- `backend/tests/api/test_reviewer_auth.py` covers accepted credentials, missing credentials, invalid credentials, unconfigured fail-closed behavior, and blank configuration rejection.

The dependency accepts `X-Reviewer-Id` and `X-Reviewer-Token`, validates the reviewer against a caller-supplied allow-list, and returns a `ReviewerPrincipal` only after token validation.

### Boundary Preserved

This is a dependency/test substrate only. It does not register an API route, change OpenAPI, mutate queue rows, add settings or secrets, add production auth, add reviewer ownership persistence, add reviewer action history, change connector runtime behavior, change evidence/claim/report behavior, add schemas, add migrations, use live I/O, alter hook config, or invoke POSIX scripts.

### Validation

```powershell
cd backend
py -3.12 -m pytest -q tests/api/test_reviewer_auth.py
ruff check app/api/reviewer_auth.py tests/api/test_reviewer_auth.py
mypy app/api/reviewer_auth.py tests/api/test_reviewer_auth.py
py -3.12 -m pytest --collect-only -q
cd ..
git diff --check
.\scripts\verify.ps1
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

Result: pass on 2026-06-04. Focused API auth tests: 11 passed. Focused ruff and mypy clean. Backend collection: 362 tests. Default and DB-enabled Windows PowerShell verification passed with 362 backend tests collected/passing, lint clean, mypy clean over 123 source files, migrations/seeds applied, and DB smoke passed.

### Next Slice

The next connector review API slice can plan or implement only the subset of mutation actions that already have repository substrate and principal matching: `request_fixture_fix`, `requeue_after_fix`, and `cancel_review`. `acknowledge`, `approve_for_connector_qa`, durable idempotency, reviewer ownership persistence, reviewer action history, production auth, and dashboard workflow remain separate future slices.

## CON-026 Connector Review Action Route Subset

CON-026 is complete as a route-subset decision. ADR `docs/adr/lane-d-0016-connector-review-action-route-subset.md` accepts the exact mutation actions that may be implemented next without inventing new queue semantics.

### Accepted Implementation Subset

- `request_fixture_fix`: use `ConnectorReviewQueueRepository.mark_failed(...)` for running connector review jobs only.
- `requeue_after_fix`: use `ConnectorReviewQueueRepository.requeue_failed(...)` for failed connector review jobs only when attempts remain.
- `cancel_review`: use `ConnectorReviewQueueRepository.cancel(...)` for nonfinal cancellable connector review jobs.

Each accepted action must require a non-empty reason and an authenticated reviewer principal. If a future request carries `reviewer_id`, that value must match `ReviewerPrincipal.reviewer_id`.

### Still Out Of Scope

- `acknowledge`, because reviewer ownership storage is not accepted.
- `approve_for_connector_qa`, because no accepted queue transition maps it to current persistence.
- Durable idempotency and reviewer action history, because no persistence decision exists.
- Route registration, OpenAPI refresh, queue code changes, repository method changes, production auth, reviewer ownership persistence, worker execution, live connector behavior, evidence/claim/report mutation, schemas, migrations, hook config, and POSIX scripts.

### Validation

```powershell
.\scripts\verify.ps1
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
git diff --check
```

Result: recorded in `state/VALIDATION_LOG.md` for CON-026.

### Next Slice

After Session 1's Lane C evidence-linkage/OpenAPI branch lands or a clean merge point is coordinated, implement `POST /connector-runs/{ingest_run_id}/review-actions` for the accepted subset above and refresh OpenAPI parity in the same route implementation slice.

## CON-027 Connector Fixture Retrieval Metric Quality

CON-027 tightens connector-local fixture quality around retrieval-run metric consistency.

### Implemented Checks

- Succeeded fixture retrievals must report `row_count` equal to non-failure evidence count.
- Succeeded fixture retrievals must report `error_count == 0`.
- Blocked or failed fixture retrievals must report explicit `row_count == 0`.
- Blocked or failed fixture retrievals must report `error_count > 0`.

### Boundary Preserved

This is connector-local fixture-quality validation only. It does not add API routes, OpenAPI changes, DB schema changes, queue behavior, connector runtime behavior, live I/O, hook config, POSIX scripts, durable evidence-row `ingest_run_id` linkage, or Lane A/B/C/D module changes outside the connector quality evaluator.

### Validation

```powershell
cd backend
py -3.12 -m pytest -q tests/connectors/test_fixture_quality.py
ruff check app/connectors/fixture_quality.py tests/connectors/test_fixture_quality.py
mypy app/connectors/fixture_quality.py tests/connectors/test_fixture_quality.py
cd ..
git diff --check
.\scripts\verify.ps1
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

Result: pass on 2026-06-04. Focused fixture-quality tests cover 11 cases; focused ruff clean; focused mypy clean over 2 source files. Full final verification is recorded in `state/VALIDATION_LOG.md`.

### Next Slice

After Session 1's Lane C evidence-linkage/OpenAPI branch lands or a clean merge point is coordinated, implement `POST /connector-runs/{ingest_run_id}/review-actions` for the accepted subset above and refresh OpenAPI parity in the same route implementation slice. If that branch remains parked, continue with non-OpenAPI connector fixture-quality or job-schema planning work.

## CON-028 Connector Source-Failure Payload Type Quality

CON-028 tightens connector-local fixture quality around source-failure payload value types.

### Implemented Checks

Source-failure fixture evidence must still include `failure_reason`, `error_message`, and `retryable`. When those keys exist:

- `failure_reason` must be non-empty text;
- `error_message` must be non-empty text;
- `retryable` must be a boolean.

### Boundary Preserved

This is connector-local fixture-quality validation only. It does not add API routes, OpenAPI changes, DB schema changes, queue behavior, connector runtime behavior, live I/O, hook config, POSIX scripts, durable evidence-row `ingest_run_id` linkage, or Lane A/B/C/D module changes outside the connector quality evaluator.

### Validation

```powershell
cd backend
py -3.12 -m pytest -q tests/connectors/test_fixture_quality.py
ruff check app/connectors/fixture_quality.py tests/connectors/test_fixture_quality.py
mypy app/connectors/fixture_quality.py tests/connectors/test_fixture_quality.py
cd ..
git diff --check
.\scripts\verify.ps1
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

Result: pass on 2026-06-04. Focused fixture-quality tests cover 12 cases; focused ruff clean; focused mypy clean over 2 source files. Full final verification is recorded in `state/VALIDATION_LOG.md`.

### Next Slice

After Session 1's Lane C evidence-linkage/OpenAPI branch lands or a clean merge point is coordinated, implement `POST /connector-runs/{ingest_run_id}/review-actions` for the accepted subset above and refresh OpenAPI parity in the same route implementation slice. If that branch remains parked, continue with non-OpenAPI connector fixture-quality, report metadata, or schema-boundary work.

## CON-031 Connector Succeeded-Retrieval Failure-Metric Quality

CON-031 tightens connector-local fixture quality around success/failure metric separation.

### Implemented Checks

Succeeded fixture retrievals must not record a non-empty `metrics.failure_reason` value. Failure reasons are reserved for blocked or failed retrievals and source-failure evidence.

### Boundary Preserved

This is connector-local fixture-quality validation only. It does not add API routes, OpenAPI changes, DB schema changes, queue behavior, connector runtime behavior, live I/O, hook config, POSIX scripts, durable evidence-row `ingest_run_id` linkage, or Lane A/B/C/D module changes outside the connector quality evaluator.

### Validation

```powershell
cd backend
py -3.12 -m pytest -q tests/connectors/test_fixture_quality.py
ruff check app/connectors/fixture_quality.py tests/connectors/test_fixture_quality.py
mypy app/connectors/fixture_quality.py tests/connectors/test_fixture_quality.py
cd ..
git diff --check
.\scripts\verify.ps1
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

Result: pass on 2026-06-04. Focused fixture-quality tests cover 13 cases; focused ruff clean; focused mypy clean over 2 source files. Full final verification is recorded in `state/VALIDATION_LOG.md`.

### Next Slice

After Session 1's Lane C evidence-linkage/OpenAPI branch lands or a clean merge point is coordinated, implement `POST /connector-runs/{ingest_run_id}/review-actions` for the accepted subset above and refresh OpenAPI parity in the same route implementation slice. If that branch remains parked, continue with non-OpenAPI connector fixture-quality, report metadata, or schema-boundary work.

## CON-035 Connector Fixture Evidence Area Consistency

CON-035 tightens connector-local fixture quality around subject-area identity inside a single flood fixture retrieval.

### Implemented Checks

All evidence emitted by one flood fixture run must share the same `area_id`. Mixed subject areas in one run are rejected before the fixture output can be accepted as one coherent area-specific retrieval result.

### Boundary Preserved

This is connector-local fixture-quality validation only. It does not add API routes, OpenAPI changes, DB schema changes, queue behavior, connector runtime behavior, live I/O, hook config, POSIX scripts, durable evidence-row `ingest_run_id` linkage, or Lane A/B/C/D module changes outside the connector quality evaluator.

### Validation

```powershell
cd backend
python -m pytest -q tests/connectors/test_fixture_quality.py
ruff check app/connectors/fixture_quality.py tests/connectors/test_fixture_quality.py
mypy app/connectors/fixture_quality.py tests/connectors/test_fixture_quality.py
cd ..
git diff --check
.\scripts\verify.ps1
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend
python -m pytest --collect-only
```

Result: pass on 2026-06-04. Focused fixture-quality tests cover 17 cases; focused ruff clean; focused mypy clean over 2 source files. Full DB-enabled Windows PowerShell verification passes with 369 backend tests collected/passing, lint clean, mypy clean over 123 source files, migrations/seeds applied, and DB smoke passed.

### Next Slice

After Session 1's Lane C evidence-linkage/OpenAPI branch lands or a clean merge point is coordinated, implement `POST /connector-runs/{ingest_run_id}/review-actions` for the accepted subset above and refresh OpenAPI parity in the same route implementation slice. If that branch remains parked, continue with non-OpenAPI connector fixture-quality, report metadata, or schema-boundary work.

## CON-034 Connector Fixture Evidence Source Consistency

CON-034 tightens connector-local fixture quality around evidence source identity inside a single flood fixture retrieval.

### Implemented Checks

All evidence emitted by one flood fixture run must share the same `source_id`. Mixed source identities in one run are rejected before the fixture output can be accepted as one coherent source-derived retrieval result.

### Boundary Preserved

This is connector-local fixture-quality validation only. It does not add API routes, OpenAPI changes, DB schema changes, queue behavior, connector runtime behavior, live I/O, hook config, POSIX scripts, durable evidence-row `ingest_run_id` linkage, or Lane A/B/C/D module changes outside the connector quality evaluator.

### Validation

```powershell
cd backend
python -m pytest -q tests/connectors/test_fixture_quality.py
ruff check app/connectors/fixture_quality.py tests/connectors/test_fixture_quality.py
mypy app/connectors/fixture_quality.py tests/connectors/test_fixture_quality.py
cd ..
git diff --check
.\scripts\verify.ps1
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend
python -m pytest --collect-only
```

Result: pass on 2026-06-04. Focused fixture-quality tests cover 16 cases; focused ruff clean; focused mypy clean over 2 source files. Full DB-enabled Windows PowerShell verification passes with 368 backend tests collected/passing, lint clean, mypy clean over 123 source files, migrations/seeds applied, and DB smoke passed.

### Next Slice

After Session 1's Lane C evidence-linkage/OpenAPI branch lands or a clean merge point is coordinated, implement `POST /connector-runs/{ingest_run_id}/review-actions` for the accepted subset above and refresh OpenAPI parity in the same route implementation slice. If that branch remains parked, continue with non-OpenAPI connector fixture-quality, report metadata, or schema-boundary work.

## CON-033 Connector Fixture Retrieval Name Quality

CON-033 tightens connector-local fixture quality around flood fixture retrieval identity.

### Implemented Checks

Flood fixture retrievals must use `connector_name == "fixture_flood_static"`. Retrievals from any other connector name are rejected by the fixture-quality evaluator before they can be treated as acceptable flood fixture runs.

### Boundary Preserved

This is connector-local fixture-quality validation only. It does not add API routes, OpenAPI changes, DB schema changes, queue behavior, connector runtime behavior, live I/O, hook config, POSIX scripts, durable evidence-row `ingest_run_id` linkage, or Lane A/B/C/D module changes outside the connector quality evaluator.

### Validation

```powershell
cd backend
python -m pytest -q tests/connectors/test_fixture_quality.py
ruff check app/connectors/fixture_quality.py tests/connectors/test_fixture_quality.py
mypy app/connectors/fixture_quality.py tests/connectors/test_fixture_quality.py
cd ..
git diff --check
.\scripts\verify.ps1
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend
python -m pytest --collect-only
```

Result: pass on 2026-06-04. Focused fixture-quality tests cover 15 cases; focused ruff clean; focused mypy clean over 2 source files. Full DB-enabled Windows PowerShell verification passes with 367 backend tests collected/passing, lint clean, mypy clean over 123 source files, migrations/seeds applied, and DB smoke passed.

### Next Slice

After Session 1's Lane C evidence-linkage/OpenAPI branch lands or a clean merge point is coordinated, implement `POST /connector-runs/{ingest_run_id}/review-actions` for the accepted subset above and refresh OpenAPI parity in the same route implementation slice. If that branch remains parked, continue with non-OpenAPI connector fixture-quality, report metadata, or schema-boundary work.

## CON-032 Connector Fixture Evidence Domain Quality

CON-032 tightens connector-local fixture quality around flood fixture evidence domain consistency.

### Implemented Checks

Flood fixture evidence must use `domain == "flood"`. Evidence from any other domain is rejected by the fixture-quality evaluator before it can be treated as fixture-acceptable flood evidence.

### Boundary Preserved

This is connector-local fixture-quality validation only. It does not add API routes, OpenAPI changes, DB schema changes, queue behavior, connector runtime behavior, live I/O, hook config, POSIX scripts, durable evidence-row `ingest_run_id` linkage, or Lane A/B/C/D module changes outside the connector quality evaluator.

### Validation

```powershell
cd backend
python -m pytest -q tests/connectors/test_fixture_quality.py
ruff check app/connectors/fixture_quality.py tests/connectors/test_fixture_quality.py
mypy app/connectors/fixture_quality.py tests/connectors/test_fixture_quality.py
cd ..
git diff --check
.\scripts\verify.ps1
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend
python -m pytest --collect-only
```

Result: pass on 2026-06-04. Focused fixture-quality tests cover 14 cases; focused ruff clean; focused mypy clean over 2 source files. Full DB-enabled Windows PowerShell verification passes with 366 backend tests collected/passing, lint clean, mypy clean over 123 source files, migrations/seeds applied, and DB smoke passed.

### Next Slice

After Session 1's Lane C evidence-linkage/OpenAPI branch lands or a clean merge point is coordinated, implement `POST /connector-runs/{ingest_run_id}/review-actions` for the accepted subset above and refresh OpenAPI parity in the same route implementation slice. If that branch remains parked, continue with non-OpenAPI connector fixture-quality, report metadata, or schema-boundary work.

## CON-029 Connector Source-Failure Reason Consistency

CON-029 tightens connector-local fixture quality around source-failure reason consistency.

### Implemented Checks

When a source-failure fixture retrieval records `metrics.failure_reason`, the source-failure evidence payload `observed_value.failure_reason` must match it exactly after whitespace trimming.

This follows the existing source-failure payload checks from CON-028. Missing or invalid payload values are still reported by the existing incomplete/invalid payload issue codes before reason-consistency comparison runs.

### Boundary Preserved

This is connector-local fixture-quality validation only. It does not add API routes, OpenAPI changes, DB schema changes, queue behavior, connector runtime behavior, live I/O, hook config, POSIX scripts, durable evidence-row `ingest_run_id` linkage, or Lane A/B/C/D module changes outside the connector quality evaluator.

### Validation

```powershell
cd backend
py -3.12 -m pytest -q tests/connectors/test_fixture_quality.py
ruff check app/connectors/fixture_quality.py tests/connectors/test_fixture_quality.py
mypy app/connectors/fixture_quality.py tests/connectors/test_fixture_quality.py
cd ..
git diff --check
.\scripts\verify.ps1
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

Result: pass on 2026-06-04. Focused fixture-quality tests cover 13 cases; focused ruff clean; focused mypy clean over 2 source files. Full final verification is recorded in `state/VALIDATION_LOG.md`.

### Next Slice

After Session 1's Lane C evidence-linkage/OpenAPI branch lands or a clean merge point is coordinated, implement `POST /connector-runs/{ingest_run_id}/review-actions` for the accepted subset above and refresh OpenAPI parity in the same route implementation slice. If that branch remains parked, continue with non-OpenAPI connector fixture-quality, report metadata, or schema-boundary work.

## CON-030 Connector Retrieval Failure-Reason Metric Quality

CON-030 tightens connector-local fixture quality around retrieval-level failure reasons.

### Implemented Checks

Blocked or failed fixture retrievals must record a non-empty `metrics.failure_reason` value. This retrieval-level metric is the run-level failure reason authority for the connector attempt and is compared against source-failure evidence payloads by CON-029.

### Boundary Preserved

This is connector-local fixture-quality validation only. It does not add API routes, OpenAPI changes, DB schema changes, queue behavior, connector runtime behavior, live I/O, hook config, POSIX scripts, durable evidence-row `ingest_run_id` linkage, or Lane A/B/C/D module changes outside the connector quality evaluator.

### Validation

```powershell
cd backend
py -3.12 -m pytest -q tests/connectors/test_fixture_quality.py
ruff check app/connectors/fixture_quality.py tests/connectors/test_fixture_quality.py
mypy app/connectors/fixture_quality.py tests/connectors/test_fixture_quality.py
cd ..
git diff --check
.\scripts\verify.ps1
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

Result: pass on 2026-06-04. Focused fixture-quality tests cover 13 cases; focused ruff clean; focused mypy clean over 2 source files. Full final verification is recorded in `state/VALIDATION_LOG.md`.

### Next Slice

After Session 1's Lane C evidence-linkage/OpenAPI branch lands or a clean merge point is coordinated, implement `POST /connector-runs/{ingest_run_id}/review-actions` for the accepted subset above and refresh OpenAPI parity in the same route implementation slice. If that branch remains parked, continue with non-OpenAPI connector fixture-quality, report metadata, or schema-boundary work.
