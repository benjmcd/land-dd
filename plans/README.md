# Plans

Active implementation plans live here. Keep them executable and narrow.

Latest completed plan: `2026-06-20-package-manifest-ci.md`.

Active plan: `2026-06-20-source-readiness-module.md`.

The active slice is `G3a`, the next retained product/control slice after the
package-manifest CI gate. It extracts source-readiness record construction into
`backend/app/source_registry/readiness.py` and keeps `scripts/source_readiness.py` as a
CLI wrapper without changing source policy, readiness counts, or DS-017 blocker status.

Lane 1 routing artifacts remain `state/reconciliation-inventory.md`,
`state/reconciliation-slices.md`, `state/r023-review.md`, and
`state/reconciliation-dispositions.md`. The disposition matrix remains the source for
retain/rework/defer/archive/discard decisions and future focused PR sequencing.

Superseded plans should be moved to `plans/archive/` with a note at the top.
