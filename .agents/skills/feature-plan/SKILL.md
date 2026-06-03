---
name: feature-plan
description: Create or update an executable plan for non-trivial implementation work. Use when work is ambiguous, cross-cutting, schema-changing, or touches more than three files.
---

# Feature Plan Skill

1. Restate the implementation goal and non-goals.
2. Explore relevant files before proposing edits.
3. Check `docs/ARCHITECTURE.md`, relevant ADRs, `state/PROJECT_STATE.md`, and existing plans.
4. Write or update `plans/YYYY-MM-DD-<slug>.md` using `.agent/PLANS.md`.
5. Include bottom-up sequence, files likely to change, tests, risks, and first safe slice.
6. Do not implement until the plan is coherent enough for a fresh session to resume.
