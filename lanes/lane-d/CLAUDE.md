@../../AGENTS.md
@AGENTS.md

## Lane D — Claude Code specific

- You are the Lane D agent. Your scope is reports, API, and platform integration (MILESTONE Level 7+).
- Read `../../LANE_OWNERSHIP.md` and `../../state/lane-d-state.md` before doing anything.
- You are the integration lane. You wire A/B/C services together — never modify their files.
- Use plan mode for any API contract, report schema, or infrastructure change.
- Run `pytest backend/tests/reports/ backend/tests/api/ -v` after every change.
- Run `./scripts/verify.sh` before handoff.
- Do NOT modify any file owned by Lane A, B, or C.
