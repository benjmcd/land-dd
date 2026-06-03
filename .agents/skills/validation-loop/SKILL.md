---
name: validation-loop
description: Run and interpret repository verification gates. Use before handoff or after implementation slices.
---

# Validation Loop Skill

1. Run the narrowest relevant check for the changed area.
2. Run `./scripts/verify.sh` before handoff.
3. If Docker/PostGIS is available and DB work changed, run `docker compose up -d db`, `./scripts/db_apply_migrations.sh`, and `python scripts/db_smoke_check.py`.
4. Do not mark work done if checks were skipped without a reason.
5. Record results in `state/VALIDATION_LOG.md` and the active plan progress log.
