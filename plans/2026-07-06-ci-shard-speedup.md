# Plan: CI shard speedup (land-dd `.github/workflows/ci.yml`)

Date: 2026-07-06
Status: PROPOSED (investigation + adversarially-vetted plan; not yet executed)
Lane: Claude backend/app lane (CI + `scripts/verify.sh` / `scripts/verify.ps1`), per AGENTS.md fence — NOT the Codex qualification/bologna lane.
Method: opus investigation (ci.yml structure, db-verify deep-dive, redundancy audit) → opus recommendation → 2 fable adversarial reviews (coverage/safety + operational fragility) → opus reconciliation.

## Problem (confirmed, evidence-cited)

CI is `.github/workflows/ci.yml`: 12 jobs, all `runs-on: ubuntu-latest`, all triggered on **both** `push` and `pull_request`, no `needs:` graph, no `concurrency:`, no `timeout-minutes`, no caching of any kind.

Observed durations (real PR runs): `db-verify` ~13min, `verify` ~12min, `qualification-selftest` ~4.5min; rest are seconds.

**Redundancies**
- `verify` (ci.yml:20) and `db-verify` (ci.yml:55) run the **identical** `./scripts/verify.sh`. `db-verify` is a strict superset (adds `RUN_DB_SMOKE=1` + DB env). The entire non-DB body (lint, mypy, ~11 gate scripts) runs **twice**. BUT `RUN_DB_SMOKE=1` un-skips **70 DB-gated test files** in the same pytest run — that full-suite-against-real-Postgres is **intentional integration coverage**, not waste. Only lint + mypy + the qualification/authority validators are true duplication.
- The qualification suite runs **three times** (verify, db-verify, qualification-selftest) — the selftest job (ci.yml:57-81) re-invokes the same Python entrypoints `verify.sh` already runs.
- `run_provenance_check.sh` runs in both `supply-chain` (:95) and `dependency-attestations` (:121).
- `push` + `pull_request` both fire → all 12 jobs run **twice** per same-repo PR-branch push. No `concurrency` cancel, so stacked pushes pile up full suites.

**Inefficiencies**: zero pip cache (`cache: pip` absent on all setup-python), zero mypy `.mypy_cache`, uncached `apt-get install postgresql-client` on the long-pole db-verify (:46), uncached `docker build` in container-image-scan (:167), no concurrency-cancel.

**Inconsistencies**: `verify` (:8) + `db-verify` (:22) omit a `permissions` block (broad default token) while the other 10 pin `contents: read`; inconsistent `fetch-depth` (0 on verify/db-verify/qualification-selftest, shallow elsewhere); `python-version '3.12'` hardcoded in 12 places; no reusable composite action.

## Vetted plan (ordered; adversarial adjustments folded in)

Expected total: **~35–45% per-PR-push compute reduction**, dominated by trigger de-dup (kills the 2× double-fire) + concurrency-cancel. Wall-clock on the green path is **unchanged-to-slightly-better** — the two ~12–13min long poles stay parallel (NO `needs:` serialization is adopted). Main-push runs kept intact (attestation/evidence completeness).

1. **Concurrency cancel, main-exempted** (near-zero risk). Add top-level `concurrency: {group: ${{ github.workflow }}-${{ github.ref }}, cancel-in-progress: ${{ github.ref != 'refs/heads/main' }}}`. Main exemption is mandatory: repo is **public** (attestations at :137-151 actually run) and main is **unprotected** (a cancelled main run is never re-required → would orphan that commit's CI+attestation evidence). Feature/PR refs cancel freely.
2. **Trigger de-dup + `workflow_dispatch`** (largest, cleanest win). Change `on:` to `push: {branches: [main]}` + `pull_request:` + `workflow_dispatch:`. Kills the 2× full-suite double-fire per same-repo PR push. `workflow_dispatch` is the mandatory escape hatch so the dual-agent PR-less worktree branches retain pre-PR signal on demand. If branch protection is ever added, it must reference the post-change job set.
3. **pip caching, explicit path, heavy jobs only** (as-written breaks all jobs — MODIFY). On the 6 `pip install -e backend[dev]` steps, add setup-python `cache: 'pip'` **with `cache-dependency-path: backend/pyproject.toml`** (only `backend/requirements-prod.lock` exists; `cache: pip` without the explicit path hard-errors). **Pilot on ONE job first.** Skip the 8 PyYAML-only jobs. Realistic ~3–6min aggregate (caches wheels, not the editable env; dev deps are unpinned `>=`).
4. **mypy `.mypy_cache` via actions/cache** (~1–2min, intermittent). Key on source hash + mypy/python version, with restore-keys prefix fallback. Must save on main pushes so PR branches restore. Sequence AFTER rec 5 (dedup makes mypy run once/trigger).
5. **verify vs db-verify dedup — guard lint/type/validators, parallel, NO `needs:`** (MODIFY strongly). Introduce a NEW CI-only var `CI_DB_SLICE_ONLY=1` set on `db-verify`; wrap ONLY the ruff block (verify.sh:108-110), mypy block (:115-117), and qualification/authority validators (:70-95) behind it. Leave pytest (:105) + DB-smoke UNGUARDED (the 70 DB-gated tests must still run). **Mirror the guard in `verify.ps1`** (spine test asserts script parity). Do NOT key on `RUN_DB_SMOKE` (AGENTS.md documents devs running `RUN_DB_SMOKE=1 verify` locally — would silently drop their lint/typecheck). Reject a `db` pytest-marker slice (no markers registered → silent-deselect hole). Reject `needs:[verify]` (serializes 12+13≈25min vs 13min parallel). Realistic ~4–6min; full pytest still runs twice by design. **Lands LAST among behavior changes** (biggest blast radius).
6. **Repurpose qualification-selftest as a genuine cheap gate** (Opus "delete" DROPPED). `test_qualification_spine.py:181-204` hard-pins the job's 5 wrapper steps + checkout + `contents: read` + the 5 scripts' presence in BOTH verify.sh + verify.ps1 — deletion fails the suite. Instead: drop the heavyweight `pip install -e backend[dev]` (ci.yml:69) from THIS job — the 5 wrappers shell to stdlib/PyYAML/jsonschema-grade scripts → collapses ~4.5min to <1min while keeping every pinned assertion green. **Do NOT edit the spine test.**
7. **`timeout-minutes` on all jobs, wide margins** (near-zero risk). 30 for verify/db-verify (NOT 20 — db-verify also pays apt-get + postgis health-retries + cold pip; a tight cap turns variance into flaky hard-fails), 15 elsewhere. Revisit down after caching lands.
8. **`permissions: {contents: read}` on verify + db-verify** (least-privilege; zero time saved). The two heaviest jobs are the only two lacking a permissions block. Spine test does not constrain these two jobs' permissions — safe.
9. **container-image-scan: keep the docker build unconditional, add buildx gha layer cache only** (Opus's gating half DROPPED). The `docker build` (:167) is the only per-commit check that `backend/Dockerfile` + `requirements-prod.lock` still build — gating it behind Scout/DOCKERHUB entitlement would let Dockerfile breakage merge silently. Take only the layer-cache half. CAVEAT: gha layer cache shares the repo's 10GB actions-cache budget with pip/mypy caches (LRU eviction) — monitor hit rates.

## Dropped by adversarial review (do NOT do)

- **Delete/repurpose-away qualification-selftest** — fails `test_qualification_spine.py:181-204`.
- **De-dup provenance across supply-chain + dependency-attestations** — false economy (check is seconds; both jobs need checkout+setup for other steps; validate-before-attest in the same job is the correct pattern).
- **Fail-fast `needs:` graph splitting ruff/mypy out of verify.sh** — breaks the AGENTS.md canonical-gate contract (verify.sh IS the local+CI gate), reintroduces local-vs-CI drift, serializes the common all-green path.
- **pytest-xdist on db-verify** — shared single DB + destructive `test_purge_audit_events.py` + zero conftest.py fixture isolation → races/flakiness. DB-suite parallelism is a separate isolation PROJECT, not a CI flag. (Optional `-n auto --dist loadscope` on the non-DB path only would need a new dev dep + AGENTS.md approval + verify.ps1 mirror; ~1.5–2× at best on 2-core runners — deferred.)

## Implementation notes

- Land in ISOLATED slices in the vetted order (1→2→3→4→7→8→6→9→5), each its own commit, bisectable. Rec 5 lands last against a green baseline.
- **No-coverage-loss gate (load-bearing):** after EVERY slice, run the full suite BOTH ways and diff pytest collected/passed/skipped counts — `RUN_DB_SMOKE=0` (verify path) and `RUN_DB_SMOKE=1 AUDIT_PURGE_TEST_DB_ISOLATED=1` (db-verify path, needs the postgis service). The 70 DB-gated files MUST still collect+run under `RUN_DB_SMOKE=1`; assert deltas are zero.
- Rec 6 spine safety: run `pytest backend/tests/test_qualification_spine.py -q` after stripping the install; confirm green (it asserts steps/permissions/checkout but NOT the install step). Confirm each of the 5 `run_qualification_*.sh` wrappers needs no `backend[dev]` install.
- Rec 3 pilot: enable `cache: pip` + `cache-dependency-path` on `verify` ONLY first; confirm no no-requirements-file error + a cache save; then replicate.
- Rec 1/2: main is unprotected today (no required-check contexts break); record in the PR body that IF protection is added later it must list the post-change job names.
- Cache-budget monitoring: after buildx + pip + mypy caches land, `gh api /repos/:owner/:repo/actions/cache/usage` — 10GB LRU means docker layers can evict the small caches.

### Explicit DO-NOTs
Do not edit `backend/tests/test_qualification_spine.py`; do not add a `db` pytest marker; do not add `needs:` between verify and db-verify; do not enable pytest-xdist in db-verify; do not add pytest-xdist as a dev dep without a plan + AGENTS.md approval; do not gate the docker build behind entitlement; do not shallow-clone verify/db-verify/qualification-selftest (spine-pinned to `fetch-depth: 0`, and `qualification_change_impact_check.py` degrades to a vacuous warning without full history).
