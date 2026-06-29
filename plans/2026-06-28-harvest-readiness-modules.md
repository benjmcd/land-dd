# Plan: Harvest net-new readiness modules from r026 onto main

Date: 2026-06-28
Branch: `claude/harvest-readiness` (off origin/main @ 8b24cffc)
Owner-authorized autonomous lane (Claude). Parallel Codex lane (ODGAV) is isolated; see fence.

## Objective
Land the net-new, owner-independent operator-UI readiness modules that were stranded in the
abandoned `codex/r026-raw-readiness-ui` working tree (preserved as tag
`archive/r026-raw-readiness-20260628`). Reconcile each against current main; add nothing
speculative.

## Context / why
`r026` was a parallel Codex experiment, 155 commits behind main; its shared-module rewrites
conflict with main's evolved contracts and were discarded. But it produced five standalone
modules absent from main. An evaluation (2026-06-28) cleared three as real, non-duplicative,
deps-intact; deferred one; dropped one.

## Scope — modules to harvest (verified earns-place, deps intact, no main duplication)
1. `production_authority.py` (275L) — parses `state/PRODUCTION_AUTHORITY_PACKET.md` +
   `state/POST_RC_AUTHORITY_SPLIT.md` into a fail-closed operator view of external authority
   blockers + repo-local candidates. Route `/ui/production-authority`.
2. `dossier_readiness.py` (265L) — read-only structural audit that the report/evidence/claim
   schemas carry required fields, inter-schema `$ref` links are intact, and dossier-gate test
   anchors exist. Route `/ui/dossier-readiness`.
3. `expansion_readiness.py` (435L) — fail-closed surface of `config/checklist_dry_run.yaml`
   expansion-governance state (limits, dry-run coverage, fail-closed status classes). Route
   `/ui/expansion`.

Harvest order: production_authority -> dossier_readiness -> expansion_readiness (simplest deps first).

## Out of scope (deliberate)
- `product_correctness.py` (750L) — DEFERRED. Partial overlap with security_guardrails/
  deployment_readiness/source_provenance + one broken test anchor
  (`test_ui_operations_recovery_preview_get_uses_local_operator_without_credentials` no longer
  exists on main). Needs an owner decision on overlap vs a narrowed slice. Recorded as a future
  owner-decision item; not landed here.
- `selected_geography_coverage.py` (561L) — DROPPED. Substantially duplicates main's
  `source_provenance.py` (same config, same county/source iteration). Its only unique bits
  (source_scope fields, case-count, fragment cross-check) belong as a small extension to
  `source_provenance.py` IF ever justified — not a second parallel route. YAGNI.

## Wiring (backend/app/** only)
For each harvested module, in `backend/app/api/ui.py`, following the existing
`ui_source_provenance` pattern:
- import the loader + error class,
- add `@router.get('/<route>', response_class=HTMLResponse)` with the 503 fail-closed error page,
- add a minimal `_<name>_page()` renderer,
- add the route href to the existing readiness-panel nav block.
No `main.py`, schema, report-semantics, auth, or openapi public-API change. Read-only pages.

## Isolation fence (parallel Codex ODGAV lane in flight)
CLAUDE (this lane) touches ONLY: `backend/app/dossier_readiness.py`,
`backend/app/expansion_readiness.py`, `backend/app/production_authority.py`,
`backend/app/api/ui.py`, `backend/tests/api/test_ui_{dossier_readiness,expansion_readiness,
production_authority}.py`, this plan, and `state/lanes/2026-06-28-claude-harvest-readiness.md`.
Claude does NOT touch any `scripts/`, `config/`, `schemas/`, or canonical state file
(`PROJECT_STATE.md`/`WORKLOG.md`/`VALIDATION_LOG.md`/`task_queue.yaml`) — those are Codex's.
Disjoint from Codex by construction (Codex = scripts/config/schemas-qualification+bologna+state).

## Acceptance criteria (pass/fail)
- The 3 modules + their tests copied from the archive tag, route-wired in `ui.py`, nav updated.
- `product_correctness`/`selected_geography_coverage` NOT added.
- Each harvested test passes: `cd backend && py -3.12 -m pytest tests/api/test_ui_dossier_readiness.py
  tests/api/test_ui_expansion_readiness.py tests/api/test_ui_production_authority.py -q`.
- `ruff` clean + `mypy` clean on the 3 modules + ui.py changes.
- `.\scripts\verify.ps1` green.
- Independent reviewer (code-reviewer subagent) pass clean — no self-approval.
- No change to report semantics, schema, auth, or the openapi public API. Read-only operator pages.
- `gh pr checks` green before any merge.

## Verification commands
```
cd backend && py -3.12 -m pytest tests/api/test_ui_dossier_readiness.py tests/api/test_ui_expansion_readiness.py tests/api/test_ui_production_authority.py -q
# ruff (Python311 ruff.exe), mypy on changed files
.\scripts\verify.ps1
```
