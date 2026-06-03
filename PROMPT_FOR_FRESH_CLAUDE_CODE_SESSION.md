# Prompt for a Fresh Claude Code Session

## General (no assigned lane)

You are working in this repository with authority to implement autonomously within the repo's governance.

Read in this order:
1. `CLAUDE.md` (imports `AGENTS.md`)
2. `README.md`
3. `MILESTONE_MAP.md` (authoritative maturity gates)
4. `MANIFEST.md`
5. `state/PROJECT_STATE.md`
6. The active plan referenced in `state/PROJECT_STATE.md`

Run:

```bash
./scripts/verify.sh
```

Use plan mode for ambiguous, cross-cutting, schema/API/security/architecture changes. Use subagents for large review or exploration passes. Do not rely on chat history.

---

## Lane-specific prompts

See the per-lane prompt files for agents assigned to a specific lane:

- `PROMPT_LANE_A.md` — Source Registry + DB Infrastructure (MILESTONE Levels 2-3)
- `PROMPT_LANE_B.md` — Area + Geometry Domain (MILESTONE Level 4)
- `PROMPT_LANE_C.md` — Evidence Ledger + Claims Engine (MILESTONE Levels 5-6)
- `PROMPT_LANE_D.md` — Reports + API + Platform (MILESTONE Level 7+)
