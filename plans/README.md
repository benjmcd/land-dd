# Plans

Active implementation plans live here. Keep them executable and narrow.

Latest completed plan: `2026-06-20-security-guardrails-ui-g6a.md`.

Active plan: `2026-06-20-operations-guardrails-ui-g6b.md`.

The active slice is the narrow `G6b` operations guardrails surface after `G6a`
security/access-control merged. It should expose existing local alerting, incident,
backup/restore, retention, queue/recovery, and cost-monitoring authority without
executing operational actions, approving DS-017, adding hosted alerting/pager/scheduler
or billing authority, proving hosted observability, or claiming Level 10 production
operations.

Lane 1 routing artifacts remain `state/reconciliation-inventory.md`,
`state/reconciliation-slices.md`, `state/r023-review.md`, and
`state/reconciliation-dispositions.md`. The disposition matrix remains the source for
retain/rework/defer/archive/discard decisions and future focused PR sequencing.

Superseded plans should be moved to `plans/archive/` with a note at the top.
