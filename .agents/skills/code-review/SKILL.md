---
name: code-review
description: Review a diff or working tree against architecture, tests, data governance, and maintainability. Use after non-trivial changes or before final handoff.
---

# Code Review Skill

Review in this order:

1. Active plan alignment.
2. Architecture and module boundaries.
3. Postgres/PostGIS system-of-record integrity.
4. Evidence-before-claims invariant.
5. Source failure and no-silent-fallback behavior.
6. Tests and verification reliability.
7. Security, data licensing, and legal-output guardrails.
8. Docs, ADR, state, and plan updates.

Output: summary, findings by severity, checks run/recommended, and residual risk.
