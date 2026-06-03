# Agent Operating Model

## Design goal

Enable Codex and Claude Code to work across many sessions without chat-history dependence while avoiding context bloat.

## Instruction hierarchy

```text
AGENTS.md      canonical always-on contract
CLAUDE.md      Claude adapter importing AGENTS.md
README.md      human overview
MANIFEST.md    routing map
plans/*.md     executable active work specs
.agent/*.md    reusable agent procedures
.claude/skills reusable Claude workflows loaded only when invoked/relevant
.claude/agents isolated reviewer/research roles
scripts/*      enforceable checks
CI             external verification gate
```

## Session loop

1. Read minimal startup files.
2. Identify active plan and next task.
3. Explore relevant files only.
4. Plan if threshold met.
5. Implement lowest-dependency slice.
6. Run narrow tests.
7. Review with other model/subagent where material.
8. Run full verification.
9. Update state and handoff.

## State files

| File | Use |
|---|---|
| `state/PROJECT_STATE.md` | current active plan, next task, blockers |
| `state/WORKLOG.md` | append-only session/work-package notes |
| `state/VALIDATION_LOG.md` | commands run and results |
| `state/DECISION_LEDGER.md` | lightweight decision notes not large enough for ADR |

State files are not canonical architecture. Move durable decisions to ADRs/docs.

## Cross-model review

Prefer same-family self-review only for minor changes. For material changes:

- Codex implements -> Claude subagent or Claude Code reviews.
- Claude implements -> Codex review or independent test pass.

## Coherence checks

Run a coherence/reconceptualization pass after:

- every third completed work package;
- any architecture/schema/report-semantics change;
- any discovered conflict between docs/tests/code;
- any data-source/legal/compliance blocker.

Use `docs/planning_pack/` and the prior-art skill only when the current task needs deeper reconceptualization.
