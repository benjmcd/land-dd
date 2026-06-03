@../../AGENTS.md
@AGENTS.md

## Lane C — Claude Code specific

- You are the Lane C agent. Your scope is evidence ledger + claims engine (MILESTONE Levels 5-6).
- Read `../../LANE_OWNERSHIP.md` and `../../state/lane-c-state.md` before doing anything.
- Use plan mode for any evidence/claim contract, rules engine, or audit change.
- Never import from `app.source_registry` or `app.area_geometry` — use `app.domain.protocols` for cross-lane checks.
- Run `pytest backend/tests/evidence_ledger/ backend/tests/claims_engine/ -v` after every change.
- Run `./scripts/verify.sh` before handoff.
- Do NOT modify any file owned by Lane A, B, or D.
