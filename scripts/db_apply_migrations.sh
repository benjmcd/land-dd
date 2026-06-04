#!/usr/bin/env bash
set -euo pipefail

DB_URL="${DATABASE_URL_SYNC:-postgresql://land:land@localhost:5432/land_diligence}"

if ! command -v psql >/dev/null 2>&1; then
  echo "psql not found. Install PostgreSQL client or run migrations through your preferred DB tool." >&2
  exit 1
fi

for file in db/migrations/*.sql; do
  echo "Applying $file"
  psql "$DB_URL" -v ON_ERROR_STOP=1 -f "$file"
done

for file in db/seeds/*.sql; do
  echo "Applying $file"
  psql "$DB_URL" -v ON_ERROR_STOP=1 -f "$file"
done

echo "Migrations and seeds applied."
