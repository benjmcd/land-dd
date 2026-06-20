# Plans

Active implementation plans live here. Keep them executable and narrow.

Latest completed plan: `2026-06-20-runtime-browser-smoke-g2.md`.

Active plan: `2026-06-20-deployment-readiness-ui-g3.md`.

The active slice is the narrow `G3` deployment-readiness UI surface after `G2`
runtime/browser smoke merged. It adds a read-only `/ui/deployment-readiness` page over
the existing release-package, image-publication, and hosted-deployment catalogs without
building packages, pushing images, creating hosted infrastructure, writing secrets,
opening public endpoints, approving DS-017, adding identity/RBAC, or claiming Level 10
production authority.

Lane 1 routing artifacts remain `state/reconciliation-inventory.md`,
`state/reconciliation-slices.md`, `state/r023-review.md`, and
`state/reconciliation-dispositions.md`. The disposition matrix remains the source for
retain/rework/defer/archive/discard decisions and future focused PR sequencing.

Superseded plans should be moved to `plans/archive/` with a note at the top.
