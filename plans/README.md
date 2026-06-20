# Plans

Active implementation plans live here. Keep them executable and narrow.

Latest completed plan: `2026-06-20-performance-guardrails-ui-g6c.md`.

Active plan: `2026-06-20-observability-readiness-ui-g8.md`.

The active slice is the narrow `G8` observability readiness surface after `G6c`
performance guardrails merged. It should expose existing local metrics, queue health,
recovery preview, connector observability, source-failure evidence, alert-rule,
deployment-smoke reference, and hosted-blocker authority without creating hosted
dashboards, dispatching alerts, provisioning pager/on-call or hosted log retention,
running deployment smoke from the UI helper, approving DS-017, proving production
traffic observability, or claiming Level 10 production observability.

Lane 1 routing artifacts remain `state/reconciliation-inventory.md`,
`state/reconciliation-slices.md`, `state/r023-review.md`, and
`state/reconciliation-dispositions.md`. The disposition matrix remains the source for
retain/rework/defer/archive/discard decisions and future focused PR sequencing.

Superseded plans should be moved to `plans/archive/` with a note at the top.
