# Execution Plans

An execution plan is a self-contained implementation spec. A new agent must be able to resume from the plan without chat history.

Create or update a plan when the planning threshold in `AGENTS.md` is met.

## Required structure

```md
# <Title>

## Goal
What user-visible or system-visible outcome this delivers.

## Non-goals
What is intentionally out of scope.

## Current state
Files, flows, tests, and behavior discovered during exploration.

## Proposed design
Chosen approach and why alternatives were rejected.

## Bottom-up sequence
Small implementation slices in dependency order.

## Files likely to change
| File | Expected change |
|---|---|

## Tests / verification
Exact commands and expected signals.

## Risks and blockers
Known migration, security, data, performance, legal, or compatibility risks.

## Decision log
Append dated decisions.

## Progress log
Append progress after each meaningful step.
```

## Plan hygiene

- Keep active plans specific and executable.
- Do not duplicate entire docs or source files.
- Link to canonical docs instead of pasting them.
- Mark stale plans as superseded.
- Update `state/PROJECT_STATE.md` when changing the active plan.
