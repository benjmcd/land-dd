# Plans

Active implementation plans live here. Keep them executable and narrow.

Latest completed plan: `2026-06-20-source-readiness-module.md`.

Active plan: `2026-06-20-account-free-local-auth.md`.

The active slice is `G1a`, the next retained product/control slice after the
package-manifest CI gate and source-readiness module extraction. It makes default local
browser operation account-free by omitting `/ui/auth*` login/session routes from local
no-auth runtime and default OpenAPI output while preserving explicit protected-mode
auth behavior.

Lane 1 routing artifacts remain `state/reconciliation-inventory.md`,
`state/reconciliation-slices.md`, `state/r023-review.md`, and
`state/reconciliation-dispositions.md`. The disposition matrix remains the source for
retain/rework/defer/archive/discard decisions and future focused PR sequencing.

Superseded plans should be moved to `plans/archive/` with a note at the top.
