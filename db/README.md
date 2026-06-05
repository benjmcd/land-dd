# Database

This directory contains the Postgres/PostGIS database spine.

## Files

- `migrations/0001_initial_spine.sql`: initial schema from the planning pack.
- `seeds/001_seed_intents.sql`: seed intents.
- `seeds/002_seed_source_registry.sql`: seed source registry.
- `seeds/003_seed_demo_identity.sql`: seed the deterministic fixture workspace
  and user used by the local authenticated API demo.
- `fixtures/`: small deterministic fixtures to be added by implementation tasks.

## Local usage

```bash
make db-up
scripts/db_apply_migrations.sh
python scripts/db_smoke_check.py
```

The migration is intentionally SQL-first. Future Alembic adoption should preserve the Postgres-first storage policy and migration auditability.
