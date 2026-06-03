# Prompt for a Fresh Codex Session

You are working in this repository with authority to implement autonomously within the repo's governance.

Start by reading:
1. `AGENTS.md`
2. `README.md`
3. `MANIFEST.md`
4. `state/PROJECT_STATE.md`
5. the active plan referenced in `state/PROJECT_STATE.md`

Then run:

```bash
./scripts/verify.sh
```

Proceed bottom-up. Select the lowest-dependency unblocked task in `tasks/task_queue.yaml`. Do not start with UI, LLM summaries, live data vendors, or global expansion. Build on already-proven functionality. Update tests, docs, state, and validation logs as you work. Use `plans/` for any non-trivial change. Run `./scripts/verify.sh` before handoff.

Do not rely on any chat history. Treat repository files as the source of truth.
