# Plans

Active implementation plans live here. Keep them executable and narrow.

Latest completed plan: `2026-06-20-operations-guardrails-ui-g6b.md`.

Active plan: `2026-06-20-performance-guardrails-ui-g6c.md`.

The active slice is the narrow `G6c` performance guardrails surface after `G6b`
operations guardrails merged. It should expose existing local performance-baseline,
spatial query-plan, and queue-backpressure authority without running live load tests,
opening runtime DB `EXPLAIN`, writing performance artifacts, approving DS-017, proving
hosted SLO/capacity/observability, or claiming Level 10 production performance.

Lane 1 routing artifacts remain `state/reconciliation-inventory.md`,
`state/reconciliation-slices.md`, `state/r023-review.md`, and
`state/reconciliation-dispositions.md`. The disposition matrix remains the source for
retain/rework/defer/archive/discard decisions and future focused PR sequencing.

Superseded plans should be moved to `plans/archive/` with a note at the top.
