# ADR 0003: Thin agent context layer

## Status
Accepted

## Context
The repository must work for Codex and Claude Code across sessions without chat history. Excessive startup context increases cost and can reduce adherence.

## Decision
Use `AGENTS.md` as the canonical thin contract, `CLAUDE.md` as an adapter importing it, and route long procedures into plans, skills, subagents, docs, scripts, and CI.

## Consequences
- Do not create giant generated context bibles.
- Use `MANIFEST.md` for routing, not as exhaustive prose.
- Use executable checks for enforcement.
