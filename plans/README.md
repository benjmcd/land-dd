# Plans

Active implementation plans live here. Keep them executable and narrow.

Latest completed plan: `2026-06-20-production-authority-intake-guard.md`.

Current routing plan: `2026-06-20-post-bsr-roadmap.md`.

`BSR-001` completed the validate-only Bologna source-rights matrix through PR #109.
Post-BSR routing landed through PR #110, and `BSG-001` completed the validate-only
Bologna source-authority intake guard through PR #111. `PAI-001` adds a
production-wide validate-only authority intake guard across DS-017, hosted platform,
secrets, identity/RBAC, image publication, billing, hosted observability, and Bologna
recorded-source blockers. There is still no unblocked Bologna implementation lane until
product/AOI/source-review authority exists. `BSA-001` remains blocked. Do not proceed
to fixture capture, runtime integration, source registry promotion, rulepack
implementation, hosted authority, DS-017 approval, or a multi-geography framework from
repo-local inference alone.

Lane 1 routing artifacts remain `state/reconciliation-inventory.md`,
`state/reconciliation-slices.md`, `state/r023-review.md`, and
`state/reconciliation-dispositions.md`. The disposition matrix remains the historical
source for initial retain/rework/defer/archive/discard decisions; current residual
classification is in `state/residual-reconciliation.md`.

Superseded plans should be moved to `plans/archive/` with a note at the top.
