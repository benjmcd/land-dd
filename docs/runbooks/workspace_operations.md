# Workspace Operations Runbook

This runbook records local workspace hazards observed during the July 2026
documentation and qualification-control closeout. It is operational guidance only; it
does not change source authority, qualification status, or release readiness.

## OneDrive Sync Hazards

- The workspace is inside OneDrive. File visibility can lag briefly after another tool
  or agent writes a handoff or state file.
- `git worktree remove` can fail with permission-denied errors when OneDrive, an
  editor, or another process holds a file lock.
- Mitigation: re-read the file or rerun the worktree command after the lock releases.
  Do not manually delete a repo worktree; if cleanup is needed, archive or use the
  normal git worktree command after verifying ownership.

## Worktree Debt

- Observed local debt during the July 2026 closeout was about 1.1 GB across roughly 40
  registered worktrees.
- Mitigation: before creating a new branch, run `git worktree list`, confirm no active
  session owns the target branch/worktree, and place any new worktree under
  `worktrees/<short-name>`.
- Retire only completed, merged, unowned worktrees. Preserve branch refs and commits
  unless deletion is explicitly authorized.

## Main Branch Drift

- Local `main` can be behind `origin/main` even when the root checkout appears stable.
- Mitigation: run `git fetch origin main --prune` and confirm both the intended base
  commit and dirty-state boundary before creating a new worktree. Do not reset a dirty
  checkout unless its owner and scope are clear.

## CI Timing

Recent land-dd PR checks with the heavy shards have taken approximately:

| Check | Observed timing |
|---|---:|
| `verify` | about 12 minutes |
| `db-verify` | about 13 minutes |
| `qualification-selftest` | about 4.5 minutes |

When `db-verify` is present in a PR check set, use
`gh pr checks <pr> --watch --interval 335` or another interval greater than 180
seconds. Prefer a longer watch interval over polling the same long-running checks
frequently.
