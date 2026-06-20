# Plans

Active implementation plans live here. Keep them executable and narrow.

Latest completed plan: `2026-06-20-selected-county-source-provenance-catalog.md`.

Active plan: `2026-06-20-runtime-browser-smoke-g2.md`.

The active slice is `G2`, the next retained product/control slice after `G3b`
selected-county source-provenance catalog merged. It rebuilds runtime/browser smoke
around the accepted G1 UI surface: account-free default local operation, read-only
`/ui/raw-data`, explicit default-disabled `/ui/auth*` checks, opt-in protected auth
checks, and DB-backed deployment smoke composition without adding later readiness,
provenance, guardrail, hosted, identity/RBAC, or Level 10 claims.

Lane 1 routing artifacts remain `state/reconciliation-inventory.md`,
`state/reconciliation-slices.md`, `state/r023-review.md`, and
`state/reconciliation-dispositions.md`. The disposition matrix remains the source for
retain/rework/defer/archive/discard decisions and future focused PR sequencing.

Superseded plans should be moved to `plans/archive/` with a note at the top.
