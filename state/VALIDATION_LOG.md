# Validation Log

Record commands, results, and residual risk.

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
