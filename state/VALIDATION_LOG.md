# Validation Log

Record commands, results, and residual risk.

## 2026-06-04 Lane C TC-150 DB-backed claim persistence

**Commands run:**

```powershell
Set-Location backend
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/claims_engine/test_sqlalchemy_claim_repo.py
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/evidence_ledger tests/claims_engine
ruff check app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
mypy app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
rg -n "from app\.source_registry|from app\.area_geometry|import app\.source_registry|import app\.area_geometry" app/evidence_ledger app/claims_engine
py -3.12 -m pytest --collect-only -q
Set-Location ..
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

**Results:**

- New claim DB tests pass: 4 tests with DB smoke enabled.
- Lane C evidence/claims tests pass: 130 tests with DB smoke enabled.
- `SqlAlchemyClaimRepository` persists claims to `claims.claims`.
- Claim/evidence links persist to `claims.claim_evidence`.
- Verification tasks persist to `claims.verification_tasks`.
- Rule metadata and evidence ordering are preserved in `claims.claims.metadata`.
- DB-backed service tests cover durable claim round-trip, unknown/source-failure claim persistence, duplicate claim rejection, and rollback behavior.
- Added `docs/adr/lane-c-rules.md` for deterministic rules, evidence links, rule metadata, verification tasks, hard gates, and deferred suitability scoring.
- Targeted Lane C ruff passes.
- Targeted Lane C mypy passes: no issues in 23 source/test files.
- Lane C cross-lane import scan returns 0 matches.
- Full collection reports 235 tests.
- Full PowerShell verification passes with DB smoke enabled: 235 tests; lint clean; mypy clean (81 source files); DB smoke passes.

**Residual risk:**

- Level 6 remains partial: durable claim persistence is in place, but the remaining minimum rule categories still need fixture-backed implementation or explicit not-evaluated labeling in report/API output.
- Rule metadata remains metadata-preserved until a coordinated schema migration promotes it to first-class columns.

## 2026-06-04 Lane C TC-140 evidence geometry/spatial precision and automation guardrails

**Commands run:**

```powershell
rg -n --hidden --glob '!.git/**' --glob '!node_modules/**' --glob '!archive/**' -i "P[o]stToolUse|h[o]oks\.json|\.codex[\\/]h[o]oks|\.claude[\\/]settings|h[o]ok" .
Test-Path (Join-Path .\.claude 'settings.json'); Test-Path (Join-Path .\.codex ('h' + 'ooks.json')); Test-Path .\local_artifacts\psql.cmd
.\scripts\agent-context-check.ps1
Set-Location backend
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/evidence_ledger
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/evidence_ledger tests/claims_engine
ruff check app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
mypy app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
rg -n "from app\.source_registry|from app\.area_geometry|import app\.source_registry|import app\.area_geometry" app/evidence_ledger app/claims_engine
py -3.12 -m pytest --collect-only -q
Set-Location ..
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

**Results:**

- Automation sweep returns 0 active matches; the Claude/Codex automatic config paths are absent; `local_artifacts/psql.cmd` remains present.
- Updated `CLAUDE.md`, `AGENTS.md`, and repo-local Claude skills so Windows verification uses PowerShell wrappers instead of automatic or `.sh` execution.
- Initial evidence DB test run failed on `psycopg.errors.AmbiguousParameter` for the nullable geometry bind inside a SQL `CASE`; fixed by casting the GeoJSON bind to text in the PostGIS insert expression.
- Cleaned 22 committed `core.areas` rows with test-only label `evidence fixture area` left by the failed DB run; no linked evidence or audit rows were present.
- Lane C evidence tests pass: 62 tests with DB smoke enabled.
- Lane C evidence/claims tests pass: 126 tests with DB smoke enabled.
- Targeted Lane C ruff passes.
- Targeted Lane C mypy passes: no issues in 22 source/test files.
- Lane C cross-lane import scan returns 0 matches.
- Full collection reports 231 tests.
- Full PowerShell verification passes with DB smoke enabled: 231 tests; lint clean; mypy clean (80 source files); DB smoke passes.

**Residual risk:**

- Level 5 evidence ledger now passes for the fixture-backed DB path.
- Level 6 remains partial because claims and claim/evidence links are still in-memory, not durably persisted.
- Contract-only evidence metadata fields remain metadata-preserved until a coordinated schema migration promotes them.

## 2026-06-04 Lane C TC-130 DB-backed evidence repository and audit log

**Commands run:**

```powershell
Set-Location backend
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/evidence_ledger
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/evidence_ledger tests/claims_engine
ruff check app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
mypy app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
rg -n "from app\.source_registry|from app\.area_geometry|import app\.source_registry|import app\.area_geometry" app/evidence_ledger app/claims_engine
py -3.12 -m pytest --collect-only -q
Set-Location ..
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

**Results:**

- Lane C evidence/claims tests pass: 122 tests with DB smoke enabled.
- `SqlAlchemyEvidenceRepository` persists to `evidence.observations` and round-trips source observations, source failures, spatial intersections, derived metrics, document extracts, and human verification notes.
- Contract-only fields are preserved in `evidence.observations.metadata`: `source_id`, `evidence_code`, `observed_at`, and `superseded_by`.
- DB-backed service tests cover invalid payload rejection before storage, supersession without overwrite, deterministic retrieval by area/source/type, rollback behavior, and durable audit events.
- `SqlAlchemyEvidenceAuditLog` persists create/supersede events in `audit.events`.
- Targeted Lane C ruff passes.
- Targeted Lane C mypy passes: no issues in 22 source/test files.
- Lane C cross-lane import scan returns 0 matches.
- Full PowerShell verification passes with DB smoke enabled: 227 collected tests; lint clean; mypy clean (80 source files); DB smoke passes.

**Residual risk:**

- Level 5 remains partial: `EvidenceContract` does not yet expose geometry/SRID/spatial-precision fields, so `evidence.observations.geometry` is not mapped by the repository.
- `source_id`, `evidence_code`, `observed_at`, and `superseded_by` are metadata-preserved rather than first-class columns until a coordinated schema migration promotes them.

## 2026-06-04 Lane B TB-090 supported domain area-type mapping

**Commands run:**

```powershell
Set-Location backend
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/area_geometry
ruff check app/area_geometry app/domain/area_contracts.py tests/area_geometry
mypy app/area_geometry app/domain/area_contracts.py tests/area_geometry
py -3.12 -m pytest --collect-only -q
Set-Location ..
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

**Results:**

- Lane B area tests pass: 46 tests with DB smoke enabled.
- `SqlAlchemyAreaRepository` supports all six Level 4 domain area types: `parcel_like`, `drawn_polygon`, `multi_polygon`, `locality`, `buffer`, and `generated_candidate`.
- Exact domain area type is stored in `core.areas.metadata.domain_area_type`; `multi_polygon` uses DB bucket `polygon`, and `buffer` uses DB bucket `generated_candidate`.
- Reads fail closed when `metadata.domain_area_type` conflicts with stored `core.areas.area_type`.
- Targeted Lane B ruff passes.
- Targeted Lane B mypy passes: no issues in 10 source/test files.
- Full PowerShell verification passes with DB smoke enabled: 216 collected tests; lint clean; mypy clean (78 source files); DB smoke passes.

**Residual risk:**

- Broader spatial query/source-feature geometry support remains deferred; current relation helpers intentionally support fixture polygon/multipolygon comparison geometry only.
- Area version rows still preserve prior geometry and change reason only because that is the current schema shape; preserving prior source/confidence metadata would require a coordinated schema/ADR pass.

## 2026-06-04 Lane B TB-080 DB-backed area versioning

**Commands run:**

```powershell
Set-Location backend
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/area_geometry
ruff check app/area_geometry app/domain/area_contracts.py tests/area_geometry
mypy app/area_geometry app/domain/area_contracts.py tests/area_geometry
py -3.12 -m pytest --collect-only -q
Set-Location ..
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

**Results:**

- Lane B area tests pass: 41 tests with DB smoke enabled.
- `AreaVersionContract` captures immutable prior-geometry version rows from `core.area_versions`.
- `AreaVersionModel` maps `core.area_versions`, including the `(area_id, version_num)` uniqueness constraint and SRID 4326 MultiPolygon geometry type.
- `SqlAlchemyAreaRepository.replace_geometry` stores the prior canonical geometry in `core.area_versions` before updating `core.areas`.
- `SqlAlchemyAreaRepository.list_versions` returns ordered prior-geometry versions as typed contracts.
- DB tests cover immutable prior-geometry storage, version sequencing, missing-area no-op, invalid replacement rejection, and rollback behavior.
- Targeted Lane B ruff passes.
- Targeted Lane B mypy passes: no issues in 10 source/test files.
- Full PowerShell verification passes with DB smoke enabled: 211 collected tests; lint clean; mypy clean (78 source files); DB smoke passes.

**Residual risk:**

- Superseded by TB-090: the `multi_polygon`/`buffer` domain-to-DB area-type mismatch was resolved for the current repository path with explicit `metadata.domain_area_type` preservation.
- Version rows preserve prior geometry and change reason only because that is the current schema shape; if source/confidence history must be immutable too, a coordinated schema/ADR pass is required.

## 2026-06-04 Lane B TB-070 PostGIS spatial relation helper

**Commands run:**

```powershell
Set-Location backend
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/area_geometry
ruff check app/area_geometry app/domain/area_contracts.py tests/area_geometry
mypy app/area_geometry app/domain/area_contracts.py tests/area_geometry
py -3.12 -m pytest --collect-only -q
Set-Location ..
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

**Results:**

- Lane B area tests pass: 35 tests with DB smoke enabled.
- `AreaSpatialRelationContract` captures fixture-backed intersects, contains, distance, intersection area, intersection ratio, method, and screening caveat.
- `SqlAlchemyAreaRepository.get_spatial_relation` validates comparison GeoJSON/SRID before SQL and queries PostGIS `ST_Intersects`, `ST_Contains`, `ST_Distance`, and `ST_Intersection`.
- DB tests cover contained, disjoint, missing-area, wrong-SRID, empty-geometry, and unsupported-geometry-type behavior.
- Targeted Lane B ruff passes.
- Targeted Lane B mypy passes: no issues in 10 source/test files.
- Full PowerShell verification passes with DB smoke enabled: 205 collected tests; lint clean; mypy clean (78 source files); DB smoke passes.

**Residual risk:**

- Area versioning is still pending for Level 4.
- The spatial helper intentionally supports fixture polygon/multipolygon comparison geometry only; broader source-feature geometry types require a scoped plan.

## 2026-06-04 Lane B TB-060 PostGIS area metrics read model

**Commands run:**

```powershell
Set-Location backend
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/area_geometry
ruff check app/area_geometry app/domain/area_contracts.py tests/area_geometry
mypy app/area_geometry app/domain/area_contracts.py tests/area_geometry
py -3.12 -m pytest --collect-only -q
Set-Location ..
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

**Results:**

- Lane B area tests pass: 27 tests with DB smoke enabled.
- `AreaMetricsContract` captures SRID, centroid GeoJSON, bbox GeoJSON, geodesic area in square meters, measurement method, and screening caveat.
- `SqlAlchemyAreaRepository.get_metrics` reads PostGIS generated `centroid` and `bbox` columns and `ST_Area(geom::geography)` without modifying canonical geometry.
- Polygon and MultiPolygon fixture rows return deterministic SRID, Point centroid, Polygon bbox, positive area, and a non-survey caveat.
- Targeted Lane B ruff passes.
- Targeted Lane B mypy passes: no issues in 10 source/test files.
- Full PowerShell verification passes with DB smoke enabled: 197 collected tests; lint clean; mypy clean (78 source files); DB smoke passes.

**Residual risk:**

- Spatial query helpers and area versioning are still pending for Level 4.
- Metrics are screening values from stored geometry, not legal/survey acreage.

## 2026-06-04 Lane B TB-050 PostGIS area repository

**Commands run:**

```powershell
Set-Location backend
py -3.12 -m pytest -q tests/area_geometry
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/area_geometry/test_sqlalchemy_area_repo.py
$env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/area_geometry
ruff check app/area_geometry tests/area_geometry
mypy app/area_geometry tests/area_geometry
py -3.12 -m pytest --collect-only -q
Set-Location ..
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

**Results:**

- Lane B area tests pass: 22 tests with DB smoke enabled.
- `SqlAlchemyAreaRepository` round-trips Polygon and MultiPolygon fixtures through `core.areas` as SRID 4326 PostGIS MultiPolygon geometry.
- Geometry source, confidence, and validated flags round-trip through the DB-backed repository.
- Domain area types without a safe `core.area_type` mapping (`multi_polygon`, `buffer`) fail closed rather than being silently mapped to parcel/corridor semantics.
- Targeted Lane B ruff passes.
- Targeted Lane B mypy passes: no issues in 9 source/test files.
- Full PowerShell verification passes with DB smoke enabled: 192 collected tests; lint clean; mypy clean (78 source files); DB smoke passes.

**Residual risk:**

- Area metrics/read model, spatial query helpers, and area versioning are still pending for Level 4.
- The repository intentionally does not support every `core.area_type` enum value until domain/schema alignment is planned.

## 2026-06-04 source-governance and DB verification hardening

**Commands run:**

```powershell
$env:PYTHONPATH='.'; py -3.12 -m pytest -q tests/source_registry/test_source_service.py
py -3.12 scripts/db_smoke_check.py
$env:PYTHONPATH='.'; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/reports/test_report_service.py tests/reports/test_report_repository.py
$env:PYTHONPATH='.'; $env:RUN_DB_SMOKE='1'; py -3.12 -m pytest -q tests/source_registry/test_source_provenance.py tests/source_registry/test_source_service.py
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
cd backend; $env:PYTHONPATH='.'; py -3.12 -m pytest --collect-only -q
```

**Results:**

- Source service tests pass: 19 tests.
- Report DB/repository and source provenance targeted tests pass with `RUN_DB_SMOKE=1`.
- PowerShell verification now selects Python 3.12.10 even when `python` on PATH points at Python 3.11.
- Full verification passes with DB smoke enabled: 186 tests pass; ruff clean; mypy clean (76 source files).
- DB smoke now validates required schemas, 18 tables, 11 column groups, 2 enums, 8 foreign keys, seeded sources, and seeded intents.

**Residual risk:**

- The new GitHub Actions PostGIS job is defined but not yet proven by a remote CI run in this local-only workspace.
- Lane D remains a partial report-run persistence harness until Lane B area persistence and Lane C durable evidence/claim/rule-execution persistence are wired underneath it.

## 2026-06-03 Windows PowerShell verification wrapper

**Commands run:**

```powershell
$env:RUN_DB_SMOKE='1'; .\scripts\verify.ps1
```

**Results:**

- PowerShell-native verification wrapper passes end to end without launching Git Bash.
- Workspace validation passes, including agent context checks and JSON file checks.
- Backend tests pass: 179 tests.
- Backend lint passes.
- Backend typecheck passes: no issues in 76 source files.
- DB migration + smoke passes using the local `psql` shim in `local_artifacts`.

**Residual risk:**

- The Bash entrypoints still exist for Linux/CI compatibility; Windows users should use `.\scripts\verify.ps1` to avoid the separate Git Bash launcher.
- The wrapper now owns the local `psql` PATH shim, so future DB-smoke changes should keep that prepend in sync.

## 2026-06-03 Lane D TD-040 persisted report runs

**Commands run:**

```bash
Set-Location .\backend; $env:PYTHONPATH='.'; python -m pytest tests/reports tests/api -q
Set-Location .\backend; $env:PYTHONPATH='.'; $env:RUN_DB_SMOKE='1'; python -m pytest tests/reports tests/api -q
Set-Location .\backend; ruff check app/reports app/api app/main.py app/domain/report_contracts.py tests/reports tests/api
Set-Location .\backend; mypy app/reports app/api app/main.py app/domain/report_contracts.py tests/reports tests/api
& 'C:\Program Files\Git\bin\bash.exe' -lc 'cd /c/Users/benny/OneDrive/Desktop/land_diligence_dual_agent_workspace && PATH="$PWD/local_artifacts:$PATH" RUN_DB_SMOKE=1 ./scripts/verify.sh'
Set-Location .\backend; $env:PYTHONPATH='.'; $env:RUN_DB_SMOKE='1'; python -m pytest --collect-only -q
```

**Results:**

- Lane D report/API tests pass: 16 tests.
- SQLAlchemy-backed report persistence round-trips through `reports.report_runs` and a machine-readable JSON artifact under `OBJECT_STORE_ROOT`.
- Lane D targeted ruff passes.
- Lane D targeted mypy passes: no issues in 21 source/test files.
- Full verification through explicit Git Bash passes: agent context check ok, workspace validation ok, JSON check ok (14 files), backend tests pass, ruff clean, mypy clean (72 source files), DB smoke passes.
- Test collection reports 173 tests.
- Docker Desktop Linux engine is running; DB smoke is available.

**Residual risk:**

- The default in-memory API scaffold still exists for fixture tests; the persisted report path is exercised through repository injection and round-trip tests.
- Shared-schema alignment remains the next coordinated pass before editing `schemas/*.json`.

## 2026-06-03 Lane D TD-050 protocol adapter wiring

**Commands run:**

```bash
cd backend && PYTHONPATH=. python -m pytest -q tests/reports/test_adapters.py tests/reports/test_report_service.py tests/api/test_api_scaffold.py
cd backend && PYTHONPATH=. python -m pytest -q tests/reports tests/api
cd backend && PYTHONPATH=. python -m pytest --collect-only -q tests/reports tests/api
cd backend && PYTHONPATH=. python -m pytest --collect-only -q
cd backend && ruff check app/reports app/api tests/reports tests/api
cd backend && mypy app/reports app/api tests/reports tests/api
C:/Program Files/Git/bin/bash.exe ./scripts/verify.sh
```

**Results:**

- Lane D report/API tests pass: 15 tests.
- Cross-lane adapter wiring preserves the existing report-service behavior and guardrails while making the `EvidenceService` protocol seam explicit.
- Lane D targeted ruff passes.
- Lane D targeted mypy passes: no issues in 16 source/test files.
- Full verification through explicit Git Bash passes: agent context check ok, workspace validation ok, JSON check ok (14 files), backend tests pass, ruff clean, mypy clean (69 source files).
- Test collection reports 172 tests.
- Docker client is installed, but Docker Desktop Linux engine is not running; DB smoke remains blocked.

**Residual risk:**

- TD-050 is intentionally in-memory only. Persisted report runs still wait on DB smoke / Lane A TA-060.
- The adapter layer is thin by design; its value is architectural clarity and protocol isolation, not new behavior.

## 2026-06-03 Lane C TC-120 water-context hard-gate fixture coverage

**Commands run:**

```bash
cd backend && PYTHONPATH=. python -m pytest -q tests/claims_engine/test_rule_engine.py tests/evidence_ledger/test_payload_validation.py
cd backend && PYTHONPATH=. python -m pytest -q tests/evidence_ledger tests/claims_engine
rg -n "from app\.source_registry|from app\.area_geometry|import app\.source_registry|import app\.area_geometry" backend/app/evidence_ledger backend/app/claims_engine
cd backend && ruff check app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
cd backend && mypy app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
C:/Program\ Files/Git/bin/bash.exe ./scripts/verify.sh
cd backend && PYTHONPATH=. python -m pytest --collect-only -q tests/claims_engine/test_rule_engine.py tests/evidence_ledger/test_payload_validation.py
cd backend && PYTHONPATH=. python -m pytest --collect-only -q tests/evidence_ledger tests/claims_engine
cd backend && PYTHONPATH=. python -m pytest --collect-only -q
docker info --format '{{.ServerVersion}}'
```

**Results:**

- Focused water/rule/payload tests pass: 71 tests.
- Lane C evidence/claims/rules tests pass: 111 tests.
- Cross-lane import scan returns no matches; Lane C still does not import Lane A/B modules.
- Lane C targeted ruff passes.
- Lane C targeted mypy passes: no issues in 20 source/test files.
- Full verification through explicit Git Bash passes: agent context check ok, workspace validation ok, JSON check ok (14 files), backend tests pass, ruff clean, mypy clean (67 source files).
- Test collection reports 168 tests.
- Docker client is installed, but Docker Desktop Linux engine is not running; DB smoke remains blocked.

**Residual risk:**

- TC-120 covers the water-context fixture hard gate only. It does not implement water-rights law, well-yield modeling, hauling legality, service availability, potable-water evaluation, or final water availability.
- A reviewer-found regression is covered: one internally contradictory water fixture record with both no-context and plausible-context true now emits review-only `WATER_EVIDENCE_NEEDS_REVIEW`, not `WATER_001`.
- The in-memory current-ruleset hard gates now cover flood, access, zoning, water, wetlands, and slope. Durable claim/rule persistence remains blocked by DB smoke and later repository work.
- `schemas/evidence_schema.json` remains broad and does not yet encode water fixture fields; shared-schema alignment remains a coordinated future pass.

## 2026-06-03 Lane C TC-110 zoning/use hard-gate fixture coverage

**Commands run:**

```bash
cd backend && PYTHONPATH=. python -m pytest -q tests/claims_engine/test_rule_engine.py tests/evidence_ledger/test_payload_validation.py
cd backend && PYTHONPATH=. python -m pytest -q tests/evidence_ledger tests/claims_engine
rg -n "from app\.source_registry|from app\.area_geometry|import app\.source_registry|import app\.area_geometry" backend/app/evidence_ledger backend/app/claims_engine
cd backend && ruff check app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
cd backend && mypy app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
C:/Program\ Files/Git/bin/bash.exe ./scripts/verify.sh
cd backend && PYTHONPATH=. python -m pytest --collect-only -q tests/claims_engine/test_rule_engine.py tests/evidence_ledger/test_payload_validation.py
cd backend && PYTHONPATH=. python -m pytest --collect-only -q tests/evidence_ledger tests/claims_engine
cd backend && PYTHONPATH=. python -m pytest --collect-only -q
docker info --format '{{.ServerVersion}}'
```

**Results:**

- Focused zoning/rule/payload tests pass: 60 tests.
- Lane C evidence/claims/rules tests pass: 100 tests.
- Cross-lane import scan returns no matches; Lane C still does not import Lane A/B modules.
- Lane C targeted ruff passes.
- Lane C targeted mypy passes: no issues in 20 source/test files.
- Full verification through explicit Git Bash passes: agent context check ok, workspace validation ok, JSON check ok (14 files), backend tests pass, ruff clean, mypy clean (67 source files).
- Test collection reports 157 tests.
- Docker client is installed, but Docker Desktop Linux engine is not running; DB smoke remains blocked.

**Residual risk:**

- TC-110 covers the zoning/use fixture hard gate only, including explicit prohibited/unsupported signals, allowed/no-claim evidence, incomplete/no-signal evidence, source failure, stale review, and mixed evidence. Water remains pending.
- Zoning/use outputs are screening-only and deliberately do not assert final legal use, zoning compliance, permit eligibility, vested rights, minimum lot-size compliance, or buildability.
- Durable claim/rule persistence remains blocked by DB smoke and later repository work.
- `schemas/evidence_schema.json` remains broad and does not yet encode zoning fixture fields; shared-schema alignment remains a coordinated future pass.

## 2026-06-03 Lane C TC-100 slope hard-gate fixture coverage

**Commands run:**

```bash
cd backend && PYTHONPATH=. python -m pytest -q tests/claims_engine/test_rule_engine.py tests/evidence_ledger/test_payload_validation.py
cd backend && PYTHONPATH=. python -m pytest -q tests/evidence_ledger tests/claims_engine
rg -n "from app\.source_registry|from app\.area_geometry|import app\.source_registry|import app\.area_geometry" backend/app/evidence_ledger backend/app/claims_engine
cd backend && ruff check app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
cd backend && mypy app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
C:/Program\ Files/Git/bin/bash.exe ./scripts/verify.sh
cd backend && PYTHONPATH=. python -m pytest --collect-only -q
docker info --format '{{.ServerVersion}}'
```

**Results:**

- Focused slope/rule/payload tests pass: 50 tests.
- Lane C evidence/claims/rules tests pass: 90 tests.
- Cross-lane import scan returns no matches; Lane C still does not import Lane A/B modules.
- Lane C targeted ruff passes.
- Lane C targeted mypy passes: no issues in 20 source/test files.
- Full verification through explicit Git Bash passes: agent context check ok, workspace validation ok, JSON check ok (14 files), backend tests pass, ruff clean, mypy clean (67 source files).
- Test collection reports 145 tests.
- Docker client is installed, but Docker Desktop Linux engine is not running; DB smoke remains blocked.

**Residual risk:**

- TC-100 covers the slope/buildability fixture hard gate only. Zoning and water hard-gate domains remain pending.
- Slope outputs are screening proxies and deliberately do not assert final buildability, site-plan approval, engineering feasibility, or a permitted building envelope.
- Durable claim/rule persistence remains blocked by DB smoke and later repository work.
- `schemas/evidence_schema.json` remains broad and does not yet encode slope fixture fields; shared-schema alignment remains a coordinated future pass.

## 2026-06-03 Lane C TC-090 wetlands hard-gate fixture coverage

**Commands run:**

```bash
cd backend && PYTHONPATH=. python -m pytest -q tests/claims_engine/test_rule_engine.py tests/evidence_ledger/test_payload_validation.py
cd backend && PYTHONPATH=. python -m pytest -q tests/evidence_ledger tests/claims_engine
rg -n "from app\.source_registry|from app\.area_geometry|import app\.source_registry|import app\.area_geometry" backend/app/evidence_ledger backend/app/claims_engine
cd backend && ruff check app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
cd backend && mypy app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
C:/Program\ Files/Git/bin/bash.exe ./scripts/verify.sh
cd backend && PYTHONPATH=. python -m pytest --collect-only -q
docker info --format '{{.ServerVersion}}'
```

**Results:**

- Focused wetlands/rule/payload tests pass: 43 tests.
- Lane C evidence/claims/rules tests pass: 83 tests.
- Cross-lane import scan returns no matches; Lane C still does not import Lane A/B modules.
- Lane C targeted ruff passes.
- Lane C targeted mypy passes: no issues in 20 source/test files.
- Full verification through explicit Git Bash passes: agent context check ok, workspace validation ok, JSON check ok (14 files), backend tests pass, ruff clean, mypy clean (67 source files).
- Test collection reports 138 tests.
- Docker client is installed, but Docker Desktop Linux engine is not running; DB smoke remains blocked.

**Residual risk:**

- TC-090 covers the wetlands fixture hard gate only. Zoning, slope, and water hard-gate domains remain pending.
- Wetland outputs are screening-only and deliberately do not assert jurisdictional wetlands, delineation results, permitting outcomes, or final buildability.
- Durable claim/rule persistence remains blocked by DB smoke and later repository work.
- `schemas/evidence_schema.json` remains broad and does not yet encode wetland fixture fields; shared-schema alignment remains a coordinated future pass.

## 2026-06-03 Lane C TC-080 access hard-gate fixture coverage

**Commands run:**

```bash
cd backend && PYTHONPATH=. python -m pytest -q tests/claims_engine/test_rule_engine.py tests/evidence_ledger/test_payload_validation.py
cd backend && PYTHONPATH=. python -m pytest -q tests/evidence_ledger tests/claims_engine
rg -n "from app\.source_registry|from app\.area_geometry|import app\.source_registry|import app\.area_geometry" backend/app/evidence_ledger backend/app/claims_engine
cd backend && ruff check app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
cd backend && mypy app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
C:/Program\ Files/Git/bin/bash.exe ./scripts/verify.sh
cd backend && PYTHONPATH=. python -m pytest --collect-only -q
docker info --format '{{.ServerVersion}}'
```

**Results:**

- Focused access/rule/payload tests pass: 36 tests.
- Lane C evidence/claims/rules tests pass: 76 tests.
- Cross-lane import scan returns no matches; Lane C still does not import Lane A/B modules.
- Lane C targeted ruff passes.
- Lane C targeted mypy passes: no issues in 20 source/test files.
- Full verification through explicit Git Bash passes: agent context check ok, workspace validation ok, JSON check ok (14 files), backend tests pass, ruff clean, mypy clean (67 source files).
- Test collection reports 131 tests.
- Docker client is installed, but Docker Desktop Linux engine is not running; DB smoke remains blocked.

**Residual risk:**

- TC-080 covers the access fixture hard gate only. Zoning, wetlands, slope, and water hard-gate domains remain pending.
- Road adjacency remains a physical proxy only; the rule output deliberately avoids asserting recorded legal access or easements.
- Durable claim/rule persistence remains blocked by DB smoke and later repository work.
- `schemas/evidence_schema.json` remains broad and does not yet encode access adjacency fixture fields; shared-schema alignment remains a coordinated future pass.

## 2026-06-03 Lane D TD-030 in-memory ReportRunService

**Commands run:**

```bash
cd backend && PYTHONPATH=. python -m pytest -q tests/reports tests/api
bash ./scripts/verify.sh
cd backend && PYTHONPATH=. python -m pytest -q
cd backend && ruff check .
cd backend && mypy app tests
docker info --format '{{.ServerVersion}}'
C:/Program\ Files/Git/bin/bash.exe ./scripts/verify.sh
cd backend && PYTHONPATH=. python -m pytest --collect-only -q
```

**Results:**

- Lane D report/API tests pass: 11 tests.
- Plain `bash ./scripts/verify.sh` fails on this machine because `bash` resolves to the Windows WSL launcher and `/bin/bash` is unavailable.
- Workspace/agent-context equivalent checks pass in PowerShell; JSON check passes: 14 files.
- Full backend test suite passes: 126 tests.
- Ruff passes.
- Mypy passes: no issues in 67 source files.
- Full verification through explicit Git Bash passes: agent context check ok, workspace validation ok, JSON check ok (14 files), backend tests pass, ruff clean, mypy clean (67 source files).
- Test collection reports 126 tests.
- Docker client is installed, but Docker Desktop Linux engine is not running; DB smoke remains blocked.

**Residual risk:**

- TD-030 is in-memory only. Report runs are stored inside the per-app ReportRunService and are not durable.
- Report output now contains evidence-linked claims, unknowns, caveats, red flags, verification tasks, source manifest, and artifact metadata, but no persisted report sections or exported artifacts exist yet.
- Report source manifest is a fixture-scope snapshot, not a durable source-version/retrieval-run snapshot.
- DB-backed report persistence remains blocked until Docker/PostGIS smoke is available.

## 2026-06-03 Lane D TD-020 in-memory API scaffold

**Commands run:**

```bash
cd backend && PYTHONPATH=. python -m pytest tests/reports/ tests/api/ -v
cd backend && ruff check app/reports app/api app/main.py app/domain/report_contracts.py tests/reports tests/api
cd backend && mypy app/reports app/api app/main.py app/domain/report_contracts.py tests/reports tests/api
C:/Program\ Files/Git/bin/bash.exe ./scripts/verify.sh
cd backend && PYTHONPATH=. python -m pytest --collect-only -q
docker info --format '{{.ServerVersion}}'
```

**Results:**

- Lane D report/API tests pass: 7 tests.
- Lane D targeted ruff passes.
- Lane D targeted mypy passes: no issues in 14 source/test files.
- Full verification through Git Bash passes: agent context check ok, workspace validation ok, JSON check ok (14 files), backend tests pass, ruff clean, mypy clean (65 source files).
- Test collection reports 122 tests.
- Docker client is installed, but Docker Desktop Linux engine is not running; DB smoke remains blocked.

**Residual risk:**

- TD-020 is an in-memory API scaffold only. ReportRunService, evidence-linked report output, unknown/source-failure report content, artifact metadata, and reproducibility snapshots remain pending.
- Report runs created through `/report-runs` are per-app in-memory records, not persisted durable report runs.
- The evidence router exposes read-only area-filtered evidence; evidence creation remains service-level and future workflow/integration work.
- DB-backed report persistence remains blocked until Docker/PostGIS smoke is available.

## 2026-06-03 Lane C TC-070 contradiction/stale rule handling

**Commands run:**

```bash
cd backend && PYTHONPATH=. python -m pytest tests/claims_engine/test_rule_engine.py tests/evidence_ledger/test_payload_validation.py -v
cd backend && PYTHONPATH=. python -m pytest tests/evidence_ledger/ tests/claims_engine/ -v
cd backend && ruff check app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
cd backend && mypy app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
rg -n "from app\.source_registry|from app\.area_geometry|import app\.source_registry|import app\.area_geometry" backend/app/evidence_ledger backend/app/claims_engine
C:/Program\ Files/Git/bin/bash.exe ./scripts/verify.sh
cd backend && PYTHONPATH=. python -m pytest --collect-only -q
docker info --format '{{.ServerVersion}}'
```

**Results:**

- Focused rule/payload tests pass: 28 tests.
- Lane C evidence/claims/rules tests pass: 69 tests.
- Lane C targeted ruff passes.
- Lane C targeted mypy passes: no issues in 20 source/test files.
- Cross-lane import scan returns no matches; Lane C still does not import Lane A/B modules.
- Full verification through Git Bash passes: agent context check ok, workspace validation ok, JSON check ok (14 files), backend tests pass, ruff clean, mypy clean (60 source files).
- Test collection reports 117 tests.
- Docker client is installed, but Docker Desktop Linux engine is not running; DB smoke remains blocked.

**Residual risk:**

- TC-070 is limited to the in-memory flood-rule slice. Broader hard-gate domains in `config/ruleset_homestead_mvp.yaml` remain pending.
- Stale evidence uses an explicit fixture `source_stale` flag. It does not implement live source freshness calculations, source-version aging, or production freshness monitoring.
- Durable claim/rule persistence and DB-backed evidence freshness remain blocked by DB smoke and later repository work.
- `schemas/evidence_schema.json` remains broad and does not yet encode the `source_stale` fixture field or other type-specific observed_value constraints; shared-schema alignment remains a coordinated future pass.

## 2026-06-03 Lane C TC-060 evidence audit events

**Commands run:**

```bash
cd backend && PYTHONPATH=. python -m pytest tests/evidence_ledger/ tests/claims_engine/ -v
cd backend && ruff check app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
cd backend && mypy app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
rg -n "from app\.source_registry|from app\.area_geometry|import app\.source_registry|import app\.area_geometry" backend/app/evidence_ledger backend/app/claims_engine
C:/Program\ Files/Git/bin/bash.exe ./scripts/verify.sh
cd backend && PYTHONPATH=. python -m pytest --collect-only -q
docker info --format '{{.ServerVersion}}'
```

**Results:**

- Lane C evidence/claims/rules tests pass: 63 tests.
- Lane C targeted ruff passes.
- Lane C targeted mypy passes: no issues in 20 source/test files.
- Cross-lane import scan returns no matches; Lane C still does not import Lane A/B modules.
- Full verification through Git Bash passes: agent context check ok, workspace validation ok, JSON check ok (14 files), backend tests pass, ruff clean, mypy clean (60 source files).
- Test collection reports 111 tests.
- Docker client is installed, but Docker Desktop Linux engine is not running; DB smoke remains blocked.

**Residual risk:**

- Audit events are implemented only for the in-memory EvidenceService path. Durable audit persistence remains blocked by DB smoke and later repository work.
- `schemas/evidence_schema.json` remains broad and does not yet encode the same type-specific observed_value constraints; update requires a coordinated shared-schema pass.
- Contradiction, needs-review, stale-evidence, and broader ruleset categories remain pending.
- DB smoke remains unavailable until Docker Desktop starts.

## 2026-06-03 Lane C TC-050 evidence payload validation

**Commands run:**

```bash
cd backend && PYTHONPATH=. python -m pytest tests/evidence_ledger/ tests/claims_engine/ -v
cd backend && ruff check app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
cd backend && mypy app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
rg -n "from app\.source_registry|from app\.area_geometry|import app\.source_registry|import app\.area_geometry" backend/app/evidence_ledger backend/app/claims_engine
C:/Program\ Files/Git/bin/bash.exe ./scripts/verify.sh
cd backend && PYTHONPATH=. python -m pytest --collect-only -q
docker info --format '{{.ServerVersion}}'
```

**Results:**

- Lane C evidence/claims/rules tests pass: 59 tests.
- Lane C targeted ruff passes.
- Lane C targeted mypy passes: no issues in 18 source/test files.
- Cross-lane import scan returns no matches; Lane C still does not import Lane A/B modules.
- Payload tests cover allowed `flood_zone_code` spatial results and reject `intersection_ratio` above 1.
- Full verification through Git Bash passes: agent context check ok, workspace validation ok, JSON check ok (14 files), backend tests pass, ruff clean, mypy clean (59 source files).
- Test collection reports 107 tests.
- Docker client is installed, but Docker Desktop Linux engine is not running; DB smoke remains blocked.

**Residual risk:**

- Payload validation is implemented in the in-memory EvidenceService path only. Durable DB enforcement remains blocked by DB smoke and later repository work.
- `schemas/evidence_schema.json` remains broad and does not yet encode the same type-specific observed_value constraints; update requires a coordinated shared-schema pass.
- L5-010 audit events remain unimplemented.

## 2026-06-03 Lane C TC-040 deterministic rule slice

**Commands run:**

```bash
cd backend && PYTHONPATH=. python -m pytest tests/claims_engine/test_rule_engine.py -v
cd backend && PYTHONPATH=. python -m pytest tests/evidence_ledger/ tests/claims_engine/ -v
cd backend && ruff check app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
cd backend && mypy app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
rg -n "from app\.source_registry|from app\.area_geometry|import app\.source_registry|import app\.area_geometry" backend/app/evidence_ledger backend/app/claims_engine
cd backend && PYTHONPATH=. python -m pytest --collect-only -q
C:/Program\ Files/Git/bin/bash.exe ./scripts/verify.sh
```

**Results:**

- Rule-engine focused tests pass: 9 tests.
- Lane C evidence/claims tests pass: 45 tests.
- Lane C targeted ruff passes.
- Lane C targeted mypy passes: no issues in 16 source/test files.
- Cross-lane import scan returns no matches; Lane C still does not import Lane A/B modules.
- Test collection reports 93 tests.
- Full verification through Git Bash passes: agent context check ok, workspace validation ok, JSON check ok (14 files), backend tests pass, ruff clean, mypy clean (56 source files).
- DB smoke skipped because `RUN_DB_SMOKE=1` was not set and Docker Desktop is not running.

**Residual risk:**

- TC-040 covers one deterministic flood hard-gate only. Full Level 6 still needs broader rules, stale evidence handling, contradiction handling, and report-run integration.
- Rules are not durably persisted; DB-backed claim/report storage remains blocked by Docker/PostGIS smoke.
- L5-002 payload schema validation and L5-010 audit events remain unimplemented.
- `schemas/claim_schema.json` and `schemas/evidence_schema.json` remain shared-contract drift risks and need a schema alignment pass.

## 2026-06-03 Lane C TC-030 claim service

**Commands run:**

```bash
cd backend && PYTHONPATH=. python -m pytest tests/evidence_ledger/ tests/claims_engine/ -v
cd backend && ruff check app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
cd backend && mypy app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
rg -n "from app\.source_registry|from app\.area_geometry|import app\.source_registry|import app\.area_geometry" backend/app/evidence_ledger backend/app/claims_engine
C:/Program\ Files/Git/bin/bash.exe ./scripts/verify.sh
cd backend && PYTHONPATH=. python -m pytest --collect-only -q
```

**Results:**

- Lane C evidence/claims tests pass: 35 tests.
- Lane C targeted ruff passes.
- Lane C targeted mypy passes: no issues in 14 source/test files.
- Cross-lane import scan returns no matches; Lane C still does not import Lane A/B modules.
- Full verification through Git Bash passes: agent context check ok, workspace validation ok, JSON check ok (14 files), backend tests pass, ruff clean, mypy clean (54 source files).
- Test collection reports 83 tests.
- DB smoke skipped because `RUN_DB_SMOKE=1` was not set and Docker Desktop is not running.

**Residual risk:**

- ClaimService is verified only against the in-memory claim and evidence repositories. Durable Postgres claim/evidence links remain blocked by DB smoke and later repository work.
- Versioned deterministic rules, contradiction handling, stale evidence handling, and broader positive/negative rule fixture coverage remain pending.
- L5-002 payload schema validation and L5-010 audit events remain unimplemented.

## 2026-06-03 Lane C TC-020 evidence supersession

**Commands run:**

```bash
cd backend && PYTHONPATH=. python -m pytest tests/evidence_ledger/ tests/claims_engine/ -v
cd backend && mypy app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
cd backend && ruff check app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
rg -n "from app\.source_registry|from app\.area_geometry|import app\.source_registry|import app\.area_geometry" backend/app/evidence_ledger backend/app/claims_engine
C:/Program\ Files/Git/bin/bash.exe ./scripts/verify.sh
cd backend && PYTHONPATH=. python -m pytest --collect-only -q
```

**Results:**

- Lane C evidence/claims tests pass: 23 tests.
- Lane C targeted mypy passes: no issues in 11 source/test files.
- Lane C targeted ruff passes.
- Cross-lane import scan returns no matches; Lane C still does not import Lane A/B modules.
- Full verification through Git Bash passes: agent context check ok, workspace validation ok, JSON check ok (14 files), backend tests pass, ruff clean, mypy clean (51 source files).
- Test collection reports 71 tests.
- DB smoke skipped because `RUN_DB_SMOKE=1` was not set and Docker Desktop is not running.

**Residual risk:**

- Supersession is verified only in the in-memory repository. Durable Postgres evidence supersession/audit behavior remains blocked by DB smoke and later repository work.
- L5-002 payload schema validation and L5-010 audit events remain unimplemented.
- ClaimService/rules engine work is still not started.

## 2026-06-03 Lane A TA-050 source provenance and license gates

**Commands run:**

```bash
cd backend && PYTHONPATH=. python -m pytest tests/source_registry/ -v
python scripts/seed_sources.py
python scripts/seed_sources.py --json
cd backend && mypy app/source_registry app/evidence_ledger app/domain/source_contracts.py app/domain/evidence_contracts.py tests/source_registry/test_source_seeds.py tests/source_registry/test_sqlalchemy_source_repo.py tests/evidence_ledger/test_evidence_service.py
python scripts/check_json_files.py
python -c "import csv; rows=list(csv.DictReader(open('./registers/data_source_registry.csv', newline='', encoding='utf-8'))); print(len(rows)); print(rows[0]['License Status'], rows[16]['License Status'], rows[16]['Cache Allowed'])"
C:/Program\ Files/Git/bin/bash.exe ./scripts/verify.sh
cd backend && PYTHONPATH=. python -m pytest --collect-only -q
```

**Results:**

- Lane A source-registry tests pass: 28 tests.
- Source seed dry-run validates 8 `Must` registry rows and JSON output returns the same 8 row summaries.
- Targeted mypy passes: no issues in 12 source/test files.
- JSON check passes: 14 files.
- Source register parses 25 rows; DS-001 has unknown license status, and DS-017 is blocked for license/cache usage.
- Full verification through Git Bash passes: agent context check ok, workspace validation ok, JSON check ok (14 files), backend tests pass, ruff clean, mypy clean (51 source files).
- Test collection reports 64 tests.
- DB smoke skipped because `RUN_DB_SMOKE=1` was not set and Docker Desktop is not running.

**Residual risk:**

- Source governance is still non-DB and non-production: DB seed apply, source-version behavior, retrieval-run behavior, and live connector enforcement are not verified.
- The license review template exists, but no source has completed human license review; unknown statuses remain fail-closed.
- Durable Level 2 and durable Level 3 claims remain blocked until Docker/PostGIS smoke runs.

## 2026-06-03 Lane C TC-010 evidence service slice

**Commands run:**

```bash
cd backend && PYTHONPATH=. python -m pytest tests/evidence_ledger/ tests/claims_engine/ -v
cd backend && ruff check app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
cd backend && mypy app/evidence_ledger app/claims_engine app/domain/evidence_contracts.py app/domain/claim_contracts.py tests/evidence_ledger tests/claims_engine
rg -n "from app\.source_registry|from app\.area_geometry|import app\.source_registry|import app\.area_geometry" backend/app/evidence_ledger backend/app/claims_engine
C:/Program\ Files/Git/bin/bash.exe ./scripts/verify.sh
```

**Results:**

- Lane C evidence/claims tests pass: 16 tests.
- Lane C targeted ruff passes.
- Lane C targeted mypy passes: no issues in 11 source/test files.
- Cross-lane import scan returns no matches; Lane C does not import Lane A/B modules.
- Full verification through Git Bash passes: agent context check ok, workspace validation ok, JSON check ok (14 files), 59 backend tests pass, ruff clean, mypy clean (51 source files).
- DB smoke skipped because `RUN_DB_SMOKE=1` was not set and Docker Desktop is not running.

**Residual risk:**

- TC-010 is an in-memory evidence-service slice only; durable Postgres evidence persistence remains blocked by DB smoke/migration work.
- L5-002 payload schema validation, L5-006 supersession/amendment, and L5-010 audit events remain unimplemented.
- ClaimService/rules engine work is still not started.

## 2026-06-03 Lane A TA-040 source seeds + Lane B in-memory geometry slice

**Commands run:**

```bash
cd backend && PYTHONPATH=. python -m pytest tests/source_registry/ -v
python scripts/seed_sources.py
python scripts/seed_sources.py --json
cd backend && mypy app/source_registry app/domain/source_contracts.py tests/source_registry/test_source_seeds.py tests/source_registry/test_sqlalchemy_source_repo.py
cd backend && PYTHONPATH=. python -m pytest tests/area_geometry/ -v
cd backend && mypy app/area_geometry app/domain/area_contracts.py tests/area_geometry/test_area_service.py
bash ./scripts/verify.sh
C:/Program\ Files/Git/bin/bash.exe ./scripts/verify.sh
```

**Results:**

- Lane A source-registry tests pass: 23 tests.
- Source seed dry-run validates 8 `Must` registry rows: DS-001, DS-002, DS-003, DS-004, DS-010, DS-011, DS-017, DS-023.
- Source seed JSON output returns the same 8 rows with source names, organizations, and registry IDs.
- Targeted Lane A typecheck passes: no issues in 7 source/test files.
- Lane B area-geometry tests pass: 16 tests.
- Initial targeted Lane B typecheck found one `json.loads` `Any` return in `test_area_service.py`; fixed with a fixture-shape assertion and cast.
- Full verification initially failed on Lane B ruff issues in the untracked geometry slice; fixed with targeted `ruff check app/area_geometry/geometry_validator.py tests/area_geometry/test_area_service.py --fix --unsafe-fixes`.
- Plain `bash ./scripts/verify.sh` failed because `bash` resolved to the Windows WSL launcher and `/bin/bash` is unavailable.
- Canonical verification through Git Bash passes: agent context check ok, workspace validation ok, JSON check ok (14 files), 49 backend tests pass, ruff clean, mypy clean (48 source files).
- DB smoke skipped because `RUN_DB_SMOKE=1` was not set and Docker Desktop is not running.

**Residual risk:**

- DB apply path for `scripts/seed_sources.py --apply` is not live-verified until Docker/PostGIS is available.
- Level 2 remains blocked by Docker/PostGIS smoke; source and geometry work are verified non-DB slices only.
- Lane A still needs TA-050 license review/provenance ADR before source governance can be considered adequate for connector work.
- Lane B TB-050 PostGIS-backed area repository and spatial query behavior remain blocked on Lane A TA-060.

## 2026-06-03 scaffold validation alignment

**Commands run:**

```bash
git status --short --branch
cd backend && PYTHONPATH=. python -m pytest tests/area_geometry/ -v
cd backend && PYTHONPATH=. python -m pytest tests/reports/ tests/api/ -v
cd backend && mypy app/area_geometry app/domain/area_contracts.py app/reports app/api
C:/Program\ Files/Git/bin/bash.exe ./scripts/verify.sh
```

**Results:**

- Root status no longer lists the nested `001-audit/` worktree after adding it to `.gitignore`.
- Lane B scaffold command now passes: 1 test.
- Lane D scaffold command now passes: 2 tests.
- Targeted Lane B/D type check passes: no issues in 5 source files.
- Full verification passes: agent context check ok, workspace validation ok, JSON check ok (14 files), 22 tests pass, ruff clean, mypy clean (44 source files).
- DB smoke skipped because `RUN_DB_SMOKE=1` was not set and Docker Desktop is still unavailable.

**Residual risk:**

- Local baseline commit `ffb73e1` now exists on `main`, parented to `origin/main`.
- No GitHub push has been performed; `origin/main` remains at `13b75a9`, so fresh worktrees from remote `main` do not yet contain the project scaffold.
- DB smoke remains unverified until Docker Desktop is running.

## 2026-06-03 local baseline authority commit

**Commands run:**

```bash
git reset --mixed origin/main
git add -A --dry-run
rg -n "password|secret|token|api[_-]?key|private|credential|BEGIN .*KEY|sk-|ghp_|pat_" --glob '!docs/planning_pack/planning_registers.xlsx' --glob '!*.pyc' --glob '!*.db' .
git add -A
git commit -m "Establish governed scaffold baseline"
git log --oneline --decorate --max-count=5
```

**Results:**

- Local `main` was anchored to `origin/main` before committing, so the scaffold commit is not an unrelated root history.
- Secret scan found no committed secrets or paid-vendor dumps; matches were policy/planning references and `.env.example` local defaults.
- Local baseline commit created: `ffb73e1` (`Establish governed scaffold baseline`).

**Residual risk:**

- Commit is local only; no push has been performed.
- `001-audit` still points at `origin/main` (`13b75a9`) and does not contain the scaffold until a new worktree is created from local `main` or the baseline is pushed.
- DB smoke remains unverified until Docker Desktop is running.

## 2026-06-03 Lane A TA-010 shim archival

**Commands run:**

```bash
rg -n --fixed-strings "from app.repositories" ./backend/app ./backend/tests ./scripts
rg -n --fixed-strings "from app.services" ./backend/app ./backend/tests ./scripts
Move-Item backend/app/repositories archive/2026-06-03_source-registry-lane-migration/backend/app/
Move-Item backend/app/services archive/2026-06-03_source-registry-lane-migration/backend/app/
```

**Results:**

- Active-tree import checks found zero uses of `app.repositories` or `app.services`.
- Shim directories were moved to `archive/2026-06-03_source-registry-lane-migration/backend/app/`; no files were deleted.
- Lane A unit tests pass: 11 tests.
- Lane A typecheck passes: no issues in 4 source files.
- Full verification passes: 22 tests, ruff clean, mypy clean (40 active source files).

**Residual risk:**

- DB smoke remains unverified until Docker Desktop is running.

## 2026-06-03 Lane A TA-020 source ORM model

**Commands run:**

```bash
cd backend && PYTHONPATH=. python -m pytest tests/source_registry/ -v
cd backend && mypy app/source_registry app/domain/source_contracts.py tests/source_registry/test_source_models.py
C:/Program\ Files/Git/bin/bash.exe ./scripts/verify.sh
```

**Results:**

- Lane A source-registry tests pass: 15 tests.
- Targeted Lane A typecheck passes: no issues in 6 source/test files.
- Full verification passes: 26 tests, ruff clean, mypy clean (42 source files).
- `SourceModel` maps `source.sources` without DB access at import time.

**Residual risk:**

- DB smoke remains unverified until Docker Desktop is running.
- SQLAlchemy-backed repository is next (TA-030); live DB execution remains deferred.

## 2026-06-03 Lane A TA-030 SQLAlchemy repository

**Commands run:**

```bash
cd backend && PYTHONPATH=. python -m pytest tests/source_registry/ -v
cd backend && mypy app/source_registry app/domain/source_contracts.py tests/source_registry/test_sqlalchemy_source_repo.py
C:/Program\ Files/Git/bin/bash.exe ./scripts/verify.sh
```

**Results:**

- Lane A source-registry tests pass: 19 tests.
- Targeted Lane A typecheck passes: no issues in 6 source/test files.
- Full verification passes: 30 tests, ruff clean, mypy clean (43 source files).
- `SqlAlchemySourceRepository` implements `add`, `get`, `list_all`, and `exists_by_name_org` against a SQLAlchemy `Session`.

**Residual risk:**

- Repository tests do not execute against live Postgres; DB execution remains blocked until Docker Desktop is running.
- Source seed implementation is next (TA-040).

## 2026-06-03 repo bootstrap + local index

**Commands run:**

```bash
npx codesight --index
bash ./scripts/verify.sh
git status --short --branch
git remote -v
```

**Results:**

- Codesight v1.14.0 scanned 125 files and wrote `.codesight/`.
- `bash ./scripts/verify.sh` failed in PowerShell because `bash` resolved to the Windows WSL launcher and `/bin/bash` was unavailable.
- Re-ran the canonical gate via Git Bash: `C:/Program Files/Git/bin/bash.exe ./scripts/verify.sh`.
- Full verification passed: agent context check ok, workspace validation ok, JSON check ok (14 files), 19 tests pass, ruff clean, mypy clean (40 source files).
- DB smoke skipped because `RUN_DB_SMOKE=1` was not set.
- Local Git initialized on `main`; `origin` points to `https://github.com/benjmcd/land-dd.git`.

**Residual risk:**

- No commit or push has been performed.
- DB smoke remains unverified until Docker Desktop is running.
- Use Git Bash explicitly on this machine unless PATH is changed; plain `bash` currently invokes the WSL launcher.

## 2026-06-03 isolated lane prompt + generated artifact policy

**Commands run:**

```bash
git check-ignore -v ./.codesight/CODESIGHT.md
C:/Program Files/Git/bin/bash.exe ./scripts/verify.sh
git status --short --branch
```

**Results:**

- `.codesight/` is ignored by `.gitignore`.
- Full verification passed: agent context check ok, workspace validation ok, JSON check ok (14 files), 19 tests pass, ruff clean, mypy clean (40 source files).
- DB smoke skipped because `RUN_DB_SMOKE=1` was not set.
- Git status no longer lists `.codesight/`; all repo files remain untracked because no commit has been made.

**Residual risk:**

- No commit or push has been performed.
- Parallel agents must use isolated worktrees/copies; concurrent writes to the same checkout remain unsafe.

## 2026-06-03 isolated lane prompt hardening

**Commands run:**

```bash
C:/Program Files/Git/bin/bash.exe ./scripts/verify.sh
git check-ignore -v ./.codesight/CODESIGHT.md
git status --short --branch
```

**Results:**

- Full verification passed: agent context check ok, workspace validation ok, JSON check ok (14 files), 19 tests pass, ruff clean, mypy clean (40 source files).
- `.codesight/` remains ignored by `.gitignore`.
- Prompt now includes no-baseline-commit isolation guidance, Windows/Git Bash command notes, test-first protocol, tech-debt controls, shared-log conflict handling, stricter definition of done, and cross-lane stop conditions.
- DB smoke skipped because `RUN_DB_SMOKE=1` was not set.

**Residual risk:**

- No commit or push has been performed.
- DB smoke remains unverified until Docker Desktop is running.

## 2026-06-03 initial workspace generation

Commands expected:

```bash
./scripts/agent-context-check.sh
./scripts/validate_workspace.sh
cd backend && PYTHONPATH=. python -m pytest -q
./scripts/verify.sh
```

DB smoke not run by default because it requires Docker/PostGIS.

## 2026-06-03 local validation in generation environment

```bash
./scripts/verify.sh
```

Result:

```text
agent context check: ok
workspace validation: ok
json check: ok (13 files)
backend tests: 6 passed
verify: ok
```

DB smoke was not run here because it requires Docker/PostGIS. Run it locally after `docker compose up -d db`.

## 2026-06-03 (session 3) — 4-lane scaffold + dependency baseline

**Commands run:**

```bash
pip install psycopg[binary] pytest-cov types-PyYAML
./scripts/verify.sh
```

**Results:**

- Dependencies installed: psycopg[binary], pytest-cov, types-PyYAML.
- engine.py fixed: deferred/lazy initialization (no module-level DB connection).
- contracts.py split into 5 per-lane files; enums.py extended with EvidenceType, AreaType, JobStatus.
- Source registry code migrated to source_registry/ module; shims left in repositories/ + services/.
- Tests split: test_domain_contracts.py → 3 per-lane files; test_source_service.py → source_registry/.
- Full verify.sh: 19 tests passing; lint clean; mypy clean (40 source files).

**Lane scaffold created:**

| Lane | Module dir | Test dir | Plan | State |
|---|---|---|---|---|
| A | app/source_registry/ | tests/source_registry/ | plans/lane-a-*.md | state/lane-a-state.md |
| B | app/area_geometry/ | tests/area_geometry/ | plans/lane-b-*.md | state/lane-b-state.md |
| C | app/evidence_ledger/ + claims_engine/ | tests/evidence_ledger/ + claims_engine/ | plans/lane-c-*.md | state/lane-c-state.md |
| D | app/reports/ | tests/reports/ + api/ | plans/lane-d-*.md | state/lane-d-state.md |

**Residual risk:**

- Docker Desktop not running — all DB-dependent gates remain blocked.
- Backward-compat shims in repositories/ + services/ must be archived by Lane A (TA-010) once no code imports from them.
- `app/domain/contracts.py` re-export shim should be cleaned up by Lane D when all lanes have migrated.

## 2026-06-03 T020 — source registry service layer

**Blocker recorded:** Docker Desktop was not running; T010 (DB migration smoke) skipped.

**Commands run:**

```bash
./scripts/verify.sh
cd backend && PYTHONPATH=. python -m pytest tests/test_source_service.py -v
mypy app tests
./scripts/verify.sh
```

**Results:**

- Baseline lint fixed: 3 ruff errors in `config.py` (E501) and `contracts.py` (UP017, UP037).
- mypy installed in Python 3.11 env (`mypy>=1.11`); `verify.sh` typecheck step now runs.
- Source registry repository/service layer added (T020).
- 8 new tests in `tests/test_source_service.py` — all pass.
- Full `verify.sh`: 14 tests passed, lint clean, mypy clean (18 source files).

**Residual risk:**

- DB smoke unverified until Docker is running.
- `InMemorySourceRepository.exists_by_name_org` treats `None == None` as duplicate (stricter than Postgres `UNIQUE(name, organization)` which allows multiple NULL-org rows). Resolve when SQLAlchemy repo is added.
