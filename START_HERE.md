# Start Here

This file is for a fresh agent or human entering the repo without chat history.

## Immediate sequence

1. Read `AGENTS.md`.
2. If using Claude Code, read `CLAUDE.md`; it imports `AGENTS.md` and adds only Claude-specific notes.
3. Read `MANIFEST.md` for file routing.
4. Read `state/PROJECT_STATE.md`.
5. Read the active plan listed there.
6. Run `./scripts/verify.sh` and record the result in `state/VALIDATION_LOG.md`.
7. Continue with the lowest-dependency unblocked task in `tasks/task_queue.yaml`.

## Do not do this

- Do not read every file before starting.
- Do not rewrite the planning pack into a giant context document.
- Do not start with frontend, LLM summarization, global data ingestion, or paid/live vendor connectors.
- Do not make final legal or valuation claims.

## Current product build direction

Implement a narrow, verifiable vertical slice:

```text
source registry -> area geometry -> evidence -> claim -> report run -> API response
```

Everything else is downstream.
