---
name: code-review
description: Review the current diff or a completed implementation slice for correctness, architecture, tests, security, data lineage, and product-scope violations.
---

# Code Review Skill

Review only. Do not edit files unless explicitly asked.

## Inputs to inspect

- `git diff --stat`
- `git diff`
- active plan in `state/PROJECT_STATE.md`
- changed tests
- relevant docs/ADRs if touched

## Review checklist

- Does the diff preserve evidence-before-claim semantics?
- Are source failures explicit rather than silent?
- Are suitability and confidence separate?
- Does it avoid legal/title/survey/wetland/appraisal/insurance/lending/investment advice claims?
- Are tests meaningful and not merely snapshot/implementation-detail noise?
- Does it respect Postgres/PostGIS as system of record?
- Are dependencies, schema changes, and external services justified?
- Is the change bottom-up and reversible?

## Output

Return findings ranked by severity: blocker, high, medium, low. Include file paths and exact remediation where possible. Include "no blocking findings" only if true.
