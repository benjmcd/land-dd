# Validation Log

Record commands, results, and residual risk.

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
