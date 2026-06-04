---
name: validation-loop
description: Run the repository verification gates, interpret failures, fix narrow issues, and prepare a clean handoff.
---

# Validation Loop Skill

1. Run the agent context check: on Windows use `.\scripts\agent-context-check.ps1`; on POSIX use `./scripts/agent-context-check.sh`.
2. Run the repository verify gate: on Windows use `.\scripts\verify.ps1`; on POSIX use `./scripts/verify.sh`.
3. If Docker/Postgres is available and the task touched DB logic, run:
   ```powershell
   docker compose up -d db
   .\scripts\db_apply_migrations.ps1
   python scripts\db_smoke_check.py
   ```
4. Record results in `state/VALIDATION_LOG.md`.
5. Update `state/PROJECT_STATE.md` and `state/WORKLOG.md`.
6. Final handoff must list changed files, checks run, failures/blockers, and next task.
