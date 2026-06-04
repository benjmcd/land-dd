@../../AGENTS.md
@AGENTS.md

## Lane A — Claude Code specific

- You are the Lane A agent. Your scope is source registry + DB infrastructure.
- Read `../../LANE_OWNERSHIP.md` and `../../state/lane-a-state.md` before doing anything.
- Use plan mode for any schema, API, or architecture change.
- Keep API handlers thin; put business logic in `source_registry/service.py`.
- Run `pytest backend/tests/source_registry/ -v` after every change.
- Run `.\scripts\verify.ps1` before handoff on Windows.
- Do NOT modify any file owned by Lane B, C, or D.
