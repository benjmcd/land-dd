# Lane record: Claude harvest-readiness (2026-06-28)

Isolated Claude lane. Canonical state owner (Codex) may roll this into
`state/PROJECT_STATE.md` / `WORKLOG.md` / `VALIDATION_LOG.md` at next checkpoint.

## Branch
`claude/harvest-readiness` off origin/main @ 8b24cffc. PR: (see `gh pr` for this branch).

## What landed
Harvested 3 net-new, owner-independent, read-only operator-UI readiness modules stranded in the
abandoned `codex/r026-raw-readiness-ui` experiment (preserved as tag
`archive/r026-raw-readiness-20260628`):
- `backend/app/production_authority.py` -> `/ui/production-authority`
- `backend/app/dossier_readiness.py` -> `/ui/dossier-readiness`
- `backend/app/expansion_readiness.py` -> `/ui/expansion`
+ route wiring in `backend/app/api/ui.py` (mirrors existing source_provenance readiness-route
pattern; 503 fail-closed error page via `safe_error_message`) + nav cross-links.
+ tests `backend/tests/api/test_ui_{production_authority,dossier_readiness,expansion_readiness}.py`.
+ regenerated OpenAPI contract stubs `api/openapi_stub.yaml` + `docs/planning_pack/api/openapi_stub.yaml`
  (via `scripts/export_openapi_stub.py`) so the runtime/stub parity tests pass — +78 lines total,
  exactly the 3 new GET route blocks, no other drift. Additive read-only routes, consistent with the
  existing `/ui/*` readiness routes already in the contract.

## Deliberately NOT landed
- `product_correctness.py` (750L) — DEFERRED to an owner decision: partial overlap with
  security_guardrails/deployment_readiness/source_provenance + one stale test anchor
  (`test_ui_operations_recovery_preview_get_uses_local_operator_without_credentials` renamed on
  main). Needs owner call on overlap vs a narrowed slice.
- `selected_geography_coverage.py` (561L) — DROPPED: duplicates main's `source_provenance.py`.

## Verification evidence
- `cd backend && py -3.12 -m pytest tests/api/test_ui_{production_authority,dossier_readiness,expansion_readiness}.py -q` -> 20 passed.
- `tests/api/test_ui_routes.py` regression -> 102 passed (122 combined). No regression.
- ruff clean (7 files); mypy clean (3 modules) — confirmed by independent code-reviewer.
- `.\scripts\verify.ps1` -> (recorded in PR).
- Independent code-reviewer (separate lane): SHIP, 0 Critical/High/Medium, 3 Low (optional DRY).
- Read-only operator pages only: no report-semantics, DB-schema, auth, or openapi public-API change;
  no prohibited claim; no raw value/secret/path/traceback exposure (paths+tracebacks redacted,
  values html-escaped).

## Isolation (no overlap with parallel Codex ODGAV lane)
Touched ONLY: the 3 modules, `backend/app/api/ui.py`, the 3 test files, the 2 regenerated
OpenAPI contract stubs (`api/openapi_stub.yaml`, `docs/planning_pack/api/openapi_stub.yaml`),
this lane file, and `plans/2026-06-28-harvest-readiness-modules.md`. No `scripts/`, `config/`,
`schemas/qualification`, `config/bologna`, or canonical state file touched. Disjoint from Codex's
qualification/bologna/state set by construction.

## Related lanes / repo state
- Codex delegated milestone: ODGAV (owner-decision gate acceptance verification) — see
  `state/agent-inbox/for-codex.md` (2026-06-28 handoff). Disjoint file set.
- r026 dirty tree preserved as commit + tag `archive/r026-raw-readiness-20260628`; root checkout
  moved to clean main.
- Worktree pruning DEFERRED: 47 worktree branches are unmerged into main; per-branch triage is a
  separate future effort (do not mass-prune).

## Outstanding owner decisions (unchanged; not unblocked by this lane)
ODP-BOL-001 pilot-scope authority remains the gate blocking all Bologna downstream work; this lane
is pure owner-independent product hardening and changes none of it. P0 stays BLOCKED.
