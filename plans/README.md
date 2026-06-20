# Plans

Active implementation plans live here. Keep them executable and narrow.

Latest completed plan: `2026-06-20-custom-aoi-ui-runtime-smoke.md`.

Active plan: `2026-06-20-post-g9a-roadmap-reconciliation.md`.

The active slice is the metadata-only `REC-002` post-G9a roadmap and residual
reconciliation routing pass. `G9a` custom AOI UI runtime smoke merged through PR #101 at
`b525439e6bcddefba81c7d6bf12290b3f8551b55`; live routing now needs to move from the
completed G9a plan to a residual Lane 1 pass that compares the preserved dirty-root
candidate stack against current live `origin/main`, identifies what has already landed,
and selects the next unblocked retained slice. It must not select a new jurisdiction, add
sources/connectors/rulepacks, approve DS-017, start Bologna, create hosted
deployment/identity/observability authority, or claim Level 10 production proof.

Lane 1 routing artifacts remain `state/reconciliation-inventory.md`,
`state/reconciliation-slices.md`, `state/r023-review.md`, and
`state/reconciliation-dispositions.md`. The disposition matrix remains the historical
source for initial retain/rework/defer/archive/discard decisions; `REC-002` should
refresh residual sequencing against current live `origin/main`.

Superseded plans should be moved to `plans/archive/` with a note at the top.
