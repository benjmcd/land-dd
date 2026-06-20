# Plans

Active implementation plans live here. Keep them executable and narrow.

Latest completed plan: `2026-06-20-supported-aoi-ui-runtime.md`.

Active plan: `2026-06-20-source-entitlement-decision-packet.md`.

The active slice is `SE-001` source-entitlement decision packet. `G9c` proved the
supported-AOI `area_id` workflow through the no-JavaScript operator UI and runtime
smoke. The next unblocked engineering path is to make the remaining DS-017 Must-source
blocker decision-ready with a validate-only, machine-readable packet and checker while
keeping DS-017 blocked. It must not select a vendor, approve DS-017, add a connector,
start Bologna, create hosted deployment/identity/observability authority, or claim
Level 10 production proof.

Lane 1 routing artifacts remain `state/reconciliation-inventory.md`,
`state/reconciliation-slices.md`, `state/r023-review.md`, and
`state/reconciliation-dispositions.md`. The disposition matrix remains the historical
source for initial retain/rework/defer/archive/discard decisions; current residual
classification is in `state/residual-reconciliation.md`.

Superseded plans should be moved to `plans/archive/` with a note at the top.
