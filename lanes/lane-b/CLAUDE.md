@../../AGENTS.md
@AGENTS.md

## Lane B — Claude Code specific

- You are the Lane B agent. Your scope is area + geometry domain (MILESTONE Level 4).
- Read `../../LANE_OWNERSHIP.md` and `../../state/lane-b-state.md` before doing anything.
- Use plan mode for any schema, geometry contract, or PostGIS query change.
- Run `pytest backend/tests/area_geometry/ -v` after every change.
- Run `./scripts/verify.sh` before handoff.
- Do NOT modify any file owned by Lane A, C, or D.
