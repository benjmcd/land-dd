# Plans

Active implementation plans live here. Keep them executable and narrow.

Latest completed plan: `2026-06-21-bologna-recorded-source-corpus.md`.

Current routing plan: `2026-06-21-pr116-sync.md`.

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

`SRP-001` reworks the retained dirty-root runtime-provenance regression into a
current-main selected-county fixture review-bundle/idempotency test. It is test-only
and does not change source/report behavior, source readiness, hosted authority, Bologna
authority, or Level 10 status.

`RSR-001` merged through PR #114 and records the post-SRP residual routing closeout.
After `RSR-001`, the only remaining `STILL_DIVERGENT` residual candidate paths are
`backend/app/project_readiness.py` and `backend/app/release_readiness.py`; both remain
deferred until a real control-plane consolidation slice is explicitly selected.

`BRC-001` adds a validate-only Bologna recorded-source corpus contract. It is allowed
because it defines future fixture-manifest requirements while preserving every external
authority blocker; it does not capture fixtures, promote sources, start Bologna, or
claim hosted/Level 10 authority. `BRC-001` merged through PR #116 at
`4b29bcf646e0cf61bbf3eedee00417a4eed9f115`.

`PR116-SYNC` is the current routing-only follow-up after PR #116. It updates live-state
surfaces to stop treating the completed corpus contract as active work while preserving
the same DS-017, hosted, Bologna implementation, and Level 10 blockers.

Lane 1 routing artifacts remain `state/reconciliation-inventory.md`,
`state/reconciliation-slices.md`, `state/r023-review.md`, and
`state/reconciliation-dispositions.md`. The disposition matrix remains the historical
source for initial retain/rework/defer/archive/discard decisions; current residual
classification is in `state/residual-reconciliation.md`.

Superseded plans should be moved to `plans/archive/` with a note at the top.
