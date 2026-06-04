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
