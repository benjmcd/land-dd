---
name: feature-plan
description: Draft or update an executable implementation plan for non-trivial work, migrations, schema/API changes, or ambiguous features.
---

# Feature Plan Skill

Use this skill before implementation when the task crosses the planning threshold in `AGENTS.md`.

## Procedure

1. Read `AGENTS.md`, `MANIFEST.md`, `state/PROJECT_STATE.md`, and `.agent/PLANS.md`.
2. Explore only the files relevant to the requested change.
3. Create or update `plans/YYYY-MM-DD-<slug>.md`.
4. Include goal, non-goals, current state, design, alternatives rejected, likely changed files, milestones, tests, risks, and progress log.
5. Keep the plan executable: a fresh agent should be able to resume from it without chat history.
6. Do not implement while still resolving major ambiguity; record blockers and ask only if a decision is truly required.
