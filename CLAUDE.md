@AGENTS.md

## Claude Code specific
- Use plan mode for ambiguous, cross-cutting, multi-file, schema, API, security, or architecture changes.
- Use `.claude/skills/feature-plan` for new plans, `.claude/skills/code-review` for diff review, `.claude/skills/debug` for failing checks, and `.claude/skills/validation-loop` before handoff.
- Use read-only subagents for architecture, security, data-governance, and test review when a task produces broad output.
- Treat this file as context, not enforcement. Hooks, tests, scripts, and CI are the enforcement layer.
- Do not duplicate `AGENTS.md` content here. Keep Claude-only notes short.
