# Repo Bootstrap and Local Index

## Goal

Prepare the local workspace for future work that can later be committed to `benjmcd/land-dd`, while keeping this pass local-only.

## Non-goals

- No commit or push to GitHub.
- No product behavior changes.
- No schema, API, security, report, or data-source semantic changes.
- No file deletion or cleanup of generated runtime files.

## Current state

- The workspace was not initialized as a Git repository.
- Codesight indexing completed locally with `npx codesight --index`.
- The canonical state file says the overall foundation plan has been split into four lane plans.
- `tasks/task_queue.yaml` still marked T020 as ready even though `state/PROJECT_STATE.md` and the overall plan progress log mark it complete.
- Public metadata still used the temporary workspace name rather than the target repo name.

## Proposed design

Keep the product implementation plan intact. Make only bootstrap metadata edits: record the local index, align repo-facing metadata with `land-dd`, correct the stale task queue, and initialize local Git with an `origin` pointer to the empty GitHub repo without committing or pushing.

## Bottom-up sequence

1. Read canonical startup files and active plan.
2. Run Codesight index without watch mode.
3. Align metadata and task routing files.
4. Initialize local Git and add the GitHub remote pointer.
5. Run the workspace verification gate and record results.

## Files likely to change

| File | Expected change |
|---|---|
| `.codesight/**` | Local Codesight index output |
| `README.md` | Target repo name alignment |
| `manifest.json` | Target repo metadata alignment |
| `tasks/task_queue.yaml` | Correct stale statuses and lane routing note |
| `state/WORKLOG.md` | Record local bootstrap/index work |
| `state/VALIDATION_LOG.md` | Record verification result |

## Tests / verification

```bash
npx codesight --index
./scripts/verify.sh
git status --short --branch
git remote -v
```

Expected signals:

- Codesight writes `.codesight/`.
- Verification passes except DB smoke remains skipped unless `RUN_DB_SMOKE=1`.
- Git is initialized locally on `main`, with `origin` pointing at `https://github.com/benjmcd/land-dd.git`.

## Risks and blockers

- DB smoke remains dependent on Docker Desktop and is not part of this local bootstrap.
- `.codesight/` is generated and should be regenerated after significant code changes.
- No remote write is allowed until the user explicitly permits commit/push.

## Decision log

- 2026-06-03: Keep GitHub interaction local-only: initialize local Git and set `origin`, but do not commit or push.
- 2026-06-03: Preserve existing lane architecture and product active plan; this bootstrap plan does not replace the foundation or lane plans.

## Progress log

- 2026-06-03: Codesight index generated with `npx codesight --index`.
- 2026-06-03: README and `manifest.json` aligned to target repo `benjmcd/land-dd`.
- 2026-06-03: `tasks/task_queue.yaml` corrected against canonical project/lane state.
- 2026-06-03: Local Git initialized on `main`; `origin` set to `https://github.com/benjmcd/land-dd.git`; no commit or push performed.
- 2026-06-03: `verify.sh` passed via Git Bash; DB smoke skipped.

