# Plans

Active implementation plans live here. Keep them executable and narrow.

Latest completed plan: `2026-06-20-account-free-local-auth.md`.

Active plan: `2026-06-20-raw-data-inventory.md`.

The active slice is `G1b`, the next retained product/control slice after `G1a`
account-free local auth posture merged. It reconstructs a local read-only raw-data
inventory route from live `origin/main`, links it from `/ui/`, and keeps `GET
/ui/raw-data` free of hidden seeding, connector execution, report creation, source
approval, hosted deployment, or identity/RBAC claims.

Lane 1 routing artifacts remain `state/reconciliation-inventory.md`,
`state/reconciliation-slices.md`, `state/r023-review.md`, and
`state/reconciliation-dispositions.md`. The disposition matrix remains the source for
retain/rework/defer/archive/discard decisions and future focused PR sequencing.

Superseded plans should be moved to `plans/archive/` with a note at the top.
