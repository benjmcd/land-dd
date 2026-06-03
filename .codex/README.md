# Codex configuration

This repo keeps project-local Codex configuration focused:

- `model = "gpt-5.5"` for complex coding by default;
- workspace writes are allowed;
- network is off by default;
- approval is required for boundary-crossing operations;
- specialized read-only review agents live in `.codex/agents/`;
- reusable workflows live in `.agents/skills/`.

For a new session, paste `PROMPT_FOR_FRESH_CODEX_SESSION.md`.
