# Handoff from Claude Code -> Codex

_No active handoff._

- File-drop:  `./scripts/handoff_to_codex.sh "task for Codex"` then paste the printed pickup line.
- GUI inject: `./scripts/handoff_to_codex.sh --ipc <conversationId> "task"` (thread must be open in the Desktop app).

Every real handoff also embeds a pointer to Claude's full session transcript so Codex can
investigate the originating context if needed (see the "Claude session context" block in a
generated handoff).
