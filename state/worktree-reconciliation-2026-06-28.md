# Worktree Reconciliation - 2026-06-28

Live reconciliation run from `worktrees/odgav` after `git fetch origin --prune`.

## Authority

- Live `origin/main`: `8b24cffc1f253c9237bce78c85cd05b99631e7cf`.
- Current Codex worktree: `worktrees/odgav` on `codex/odgav`.
- Open PRs checked with `gh pr list --state open`: PR #166
  `claude/harvest-readiness` and PR #95 `dependabot/github_actions/actions/checkout-7`.
- Safe-retirement rule for this pass: remove no worktree unless it is clean, branch
  head is merged into `origin/main`, current evidence proves it is superseded, it is
  not root/current/detached/Claude-owned, and an archive tag is created before
  `git worktree remove`.

## Summary

- Total live worktrees after creating `worktrees/odgav`: 50.
- Unmerged branch worktrees classified below: 47.
- Dirty unmerged branch worktrees: 3.
- Clean unmerged branch worktrees: 44.
- Retired in this pass: 0.

No worktree met the full safe-retirement rule. In particular, `worktrees/harvest-readiness`
is tied to open PR #166 and is Claude-owned, and `worktrees/post-merge-proof` is a
detached proof worktree rather than an unmerged branch-retirement target.

## Non-Retirement Scope

| Worktree | Branch | Head | Clean | Classification | Reason |
|---|---|---:|---|---|---|
| root checkout | `main` | `8b24cffc` | no | keep-root | Canonical main workspace; root has the coordination inbox modification. |
| `worktrees/odgav` | `codex/odgav` | `8b24cffc` | no | keep-active-codex | Current active implementation worktree. |
| `worktrees/post-merge-proof` | detached | `8dadfbff` | yes | keep-detached-proof | Detached historical/proof worktree; no branch-retirement proof. |

## Unmerged Branch Worktrees

| Worktree | Branch | Head | Clean | Classification | Reason |
|---|---|---:|---|---|---|
| `worktrees/actions-upgrade` | `codex/actions-node24` | `4112604f` | yes | keep-unmerged | Branch head is not an ancestor of `origin/main`; no supersession proof. |
| `worktrees/bootstrap-pr` | `bootstrap/vertical-slice` | `06f31fea` | yes | keep-unmerged | Branch head is not an ancestor of `origin/main`; no supersession proof. |
| `worktrees/ci-fix` | `codex/ci-clean` | `5fe9dc84` | yes | keep-unmerged | Branch head is not an ancestor of `origin/main`; no supersession proof. |
| `worktrees/harvest-readiness` | `claude/harvest-readiness` | `22a390bc` | yes | keep-open-pr | Open PR #166 owns this branch; Codex must not retire it. |
| `worktrees/land_dd_advance_20260611` | `advance/full-tool-20260611` | `33c947e5` | yes | keep-unmerged | Branch head is not an ancestor of `origin/main`; no supersession proof. |
| `worktrees/land_dd_lane_fixa` | `lane/fix-queue` | `33c947e5` | no | keep-dirty | Six uncommitted changes; never retire without branch-specific review. |
| `worktrees/land_dd_lane_fixb` | `lane/fix-governance` | `33c947e5` | no | keep-dirty | Seven uncommitted changes; never retire without branch-specific review. |
| `worktrees/land_dd_lane_w1l1` | `lane/w1l1-intents` | `e3d2c3a3` | yes | keep-unmerged | Branch head is not an ancestor of `origin/main`; no supersession proof. |
| `worktrees/land_dd_lane_w1l2` | `lane/w1l2-coverage` | `36e02982` | yes | keep-unmerged | Branch head is not an ancestor of `origin/main`; no supersession proof. |
| `worktrees/land_dd_lane_w1l3` | `lane/w1l3-readapi` | `5d157641` | yes | keep-unmerged | Branch head is not an ancestor of `origin/main`; no supersession proof. |
| `worktrees/land_dd_lane_w2l1` | `lane/w2l1-durability` | `873e17dd` | yes | keep-unmerged | Branch head is not an ancestor of `origin/main`; no supersession proof. |
| `worktrees/land_dd_lane_w2l2` | `lane/w2l2-packaging` | `ec336174` | yes | keep-unmerged | Branch head is not an ancestor of `origin/main`; no supersession proof. |
| `worktrees/land_dd_lane_w2l3` | `lane/w2l3-honesty` | `8995506f` | yes | keep-unmerged | Branch head is not an ancestor of `origin/main`; no supersession proof. |
| `worktrees/land_dd_lane_w2l4` | `lane/w2l4-map` | `5890a6a1` | yes | keep-unmerged | Branch head is not an ancestor of `origin/main`; no supersession proof. |
| `worktrees/land_dd_lane_w2l5` | `lane/w2l5-dossier` | `18042541` | yes | keep-unmerged | Branch head is not an ancestor of `origin/main`; no supersession proof. |
| `worktrees/land_dd_lane_w3l1` | `lane/w3l1-revux` | `7f108dd1` | yes | keep-unmerged | Branch head is not an ancestor of `origin/main`; no supersession proof. |
| `worktrees/land_dd_lane_w3l2` | `lane/w3l2-integration` | `21c222ce` | yes | keep-unmerged | Branch head is not an ancestor of `origin/main`; no supersession proof. |
| `worktrees/lane-c-ingest-link` | `codex/lane-c-ingest-link` | `b464fe4b` | yes | keep-unmerged | Branch head is not an ancestor of `origin/main`; no supersession proof. |
| `worktrees/lane-c-ingest-link-refresh` | `codex/lane-c-ingest-link-refresh` | `b5a6a8b7` | yes | keep-unmerged | Branch head is not an ancestor of `origin/main`; no supersession proof. |
| `worktrees/local-only-readiness` | `codex/local-only-readiness` | `50f84275` | yes | keep-unmerged | Branch head is not an ancestor of `origin/main`; no supersession proof. |
| `worktrees/pr20-fix` | `codex/pr20-fix` | `47d1ef77` | yes | keep-unmerged | Branch head is not an ancestor of `origin/main`; no supersession proof. |
| `worktrees/prod-advance-20260610` | `batch/state-closeout` | `978e7cf0` | yes | keep-unmerged | Branch head is not an ancestor of `origin/main`; no supersession proof. |
| `worktrees/pub-fixture-quality` | `connector/fixture-quality` | `3d3bdd83` | yes | keep-unmerged | Branch head is not an ancestor of `origin/main`; no supersession proof. |
| `worktrees/pub-fixture-workflow` | `connector/fixture-workflow` | `f55849b8` | yes | keep-unmerged | Branch head is not an ancestor of `origin/main`; no supersession proof. |
| `worktrees/pub-retrieval-provenance` | `connector/retrieval-provenance` | `e18f542c` | yes | keep-unmerged | Branch head is not an ancestor of `origin/main`; no supersession proof. |
| `worktrees/pub-review-queue` | `connector/review-queue` | `78fa82cf` | no | keep-dirty | One untracked `archive/` change; never retire without branch-specific review. |
| `worktrees/pub-review-status` | `connector/review-status` | `958e5864` | yes | keep-unmerged | Branch head is not an ancestor of `origin/main`; no supersession proof. |
| `worktrees/pub-source-contract` | `schema/source-contract-parity` | `8d6b7e87` | yes | keep-unmerged | Branch head is not an ancestor of `origin/main`; no supersession proof. |
| `worktrees/pub-source-provenance` | `schema/source-provenance-contracts` | `b51794ee` | yes | keep-unmerged | Branch head is not an ancestor of `origin/main`; no supersession proof. |
| `worktrees/pub-source-provenance-service` | `source/provenance-contract-service` | `1f25ac26` | yes | keep-unmerged | Branch head is not an ancestor of `origin/main`; no supersession proof. |
| `worktrees/review-debt` | `codex/review-debt` | `d5d44815` | yes | keep-unmerged | Branch head is not an ancestor of `origin/main`; no supersession proof. |
| `worktrees/session1-lane-a` | `lane-a/session1-source-hardening` | `4037d294` | yes | keep-unmerged | Branch head is not an ancestor of `origin/main`; no supersession proof. |
| `worktrees/session1-lane-b` | `lane-b/session1-geometry-hardening` | `498a4157` | yes | keep-unmerged | Branch head is not an ancestor of `origin/main`; no supersession proof. |
| `worktrees/session1-lane-c` | `codex/session1-lane-c` | `90db5344` | yes | keep-unmerged | Branch head is not an ancestor of `origin/main`; no supersession proof. |
| `worktrees/session2-lineage` | `codex/session2-source-failure-lineage` | `8c229945` | yes | keep-unmerged | Branch head is not an ancestor of `origin/main`; no supersession proof. |
| `worktrees/session2-review-actions` | `codex/session2-review-actions` | `23753a5f` | yes | keep-unmerged | Branch head is not an ancestor of `origin/main`; no supersession proof. |
| `worktrees/tc190-90348d0` | `codex/tc190-90348d0` | `10f538a6` | yes | keep-unmerged | Branch head is not an ancestor of `origin/main`; no supersession proof. |
| `worktrees/tc190-af550ee` | `codex/tc190-af550ee` | `d7c557ac` | yes | keep-unmerged | Branch head is not an ancestor of `origin/main`; no supersession proof. |
| `worktrees/tc190-current` | `codex/tc190-current` | `7cb42ad0` | yes | keep-unmerged | Branch head is not an ancestor of `origin/main`; no supersession proof. |
| `worktrees/tc190-guard` | `codex/tc190-guard` | `4caa378c` | yes | keep-unmerged | Branch head is not an ancestor of `origin/main`; no supersession proof. |
| `worktrees/tc190-int` | `codex/tc190-int-proof` | `a6f583e7` | yes | keep-unmerged | Branch head is not an ancestor of `origin/main`; no supersession proof. |
| `worktrees/tc190-main` | `codex/tc190-main` | `d720b7b8` | yes | keep-unmerged | Branch head is not an ancestor of `origin/main`; no supersession proof. |
| `worktrees/tc190-service-proof` | `codex/tc190-service-proof` | `c6c7f65c` | yes | keep-unmerged | Branch head is not an ancestor of `origin/main`; no supersession proof. |
| `worktrees/tc191-int` | `codex/tc191-int` | `d351e35b` | yes | keep-unmerged | Branch head is not an ancestor of `origin/main`; no supersession proof. |
| `worktrees/tc192-failure-version` | `codex/tc192-failure-version` | `0f3ce094` | yes | keep-unmerged | Branch head is not an ancestor of `origin/main`; no supersession proof. |
| `worktrees/tc192-int` | `codex/tc192-int` | `d73589d3` | yes | keep-unmerged | Branch head is not an ancestor of `origin/main`; no supersession proof. |
| `worktrees/td085-prov-summary` | `s1/td085-prov-summary` | `40ff6bdd` | yes | keep-unmerged | Branch head is not an ancestor of `origin/main`; no supersession proof. |

## Retirement Result

No archive tags were created and no `git worktree remove` command was run in this pass,
because no worktree satisfied the full safe-retirement rule.
