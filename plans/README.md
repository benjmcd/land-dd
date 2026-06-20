# Plans

Active implementation plans live here. Keep them executable and narrow.

Latest completed plan: `2026-06-20-deployment-readiness-ui-g3.md`.

Active plan: `2026-06-20-source-provenance-ui-g5.md`.

The active slice is the narrow `G5` source-provenance UI surface after `G3`
deployment-readiness merged. It adds a read-only `/ui/source-provenance` page over the
selected-county provenance catalog and Must-source readiness records without running
connectors, seeding runtime provenance, approving DS-017, expanding county/source
coverage, starting Bologna, proving hosted source authority, or claiming Level 10
production authority.

Lane 1 routing artifacts remain `state/reconciliation-inventory.md`,
`state/reconciliation-slices.md`, `state/r023-review.md`, and
`state/reconciliation-dispositions.md`. The disposition matrix remains the source for
retain/rework/defer/archive/discard decisions and future focused PR sequencing.

Superseded plans should be moved to `plans/archive/` with a note at the top.
