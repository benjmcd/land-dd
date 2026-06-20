# Plans

Active implementation plans live here. Keep them executable and narrow.

Latest completed plan: `2026-06-20-observability-readiness-ui-g8.md`.

Active plan: `2026-06-20-custom-aoi-ui-runtime-smoke.md`.

The active slice is the narrow `G9a` custom AOI UI runtime smoke proof after `G8`
observability readiness merged. It should prove the existing custom GeoJSON intake UI
path through runtime smoke by creating a fixture AOI report, waiting for async report
completion, approving through the existing reviewer UI path when needed, and checking
approved delivery, artifact persistence, and lineage. It must not select a new
jurisdiction, add sources/connectors/rulepacks, approve DS-017, start Bologna, create
hosted deployment/identity/observability authority, or claim Level 10 production proof.

Lane 1 routing artifacts remain `state/reconciliation-inventory.md`,
`state/reconciliation-slices.md`, `state/r023-review.md`, and
`state/reconciliation-dispositions.md`. The disposition matrix remains the source for
retain/rework/defer/archive/discard decisions and future focused PR sequencing.

Superseded plans should be moved to `plans/archive/` with a note at the top.
