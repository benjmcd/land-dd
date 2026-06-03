---
name: validation-loop
description: Run the repository verification gates, interpret failures, fix narrow issues, and prepare a clean handoff.
---

# Validation Loop Skill

1. Run `./scripts/agent-context-check.sh`.
2. Run `./scripts/verify.sh`.
3. If Docker/Postgres is available and the task touched DB logic, run:
   ```bash
   docker compose up -d db
   ./scripts/db_apply_migrations.sh
   python scripts/db_smoke_check.py
   ```
4. Record results in `state/VALIDATION_LOG.md`.
5. Update `state/PROJECT_STATE.md` and `state/WORKLOG.md`.
6. Final handoff must list changed files, checks run, failures/blockers, and next task.
