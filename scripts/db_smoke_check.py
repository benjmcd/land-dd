from __future__ import annotations

import os
import sys

try:
    import psycopg
except ImportError:  # pragma: no cover
    print("psycopg is not installed. Run: cd backend && python -m pip install -e '.[dev]'", file=sys.stderr)
    raise SystemExit(1)

DB_URL = os.environ.get("DATABASE_URL_SYNC", "postgresql://land:land@localhost:5432/land_diligence")
REQUIRED_SCHEMAS = ["core", "source", "geo", "evidence", "rules", "claims", "reports", "jobs", "audit"]

with psycopg.connect(DB_URL) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT postgis_version()")
        postgis_version = cur.fetchone()[0]
        print(f"PostGIS version: {postgis_version}")

        cur.execute("SELECT schema_name FROM information_schema.schemata")
        schemas = {row[0] for row in cur.fetchall()}
        missing = [schema for schema in REQUIRED_SCHEMAS if schema not in schemas]
        if missing:
            raise SystemExit(f"Missing schemas: {missing}")

        cur.execute("SELECT count(*) FROM source.sources")
        source_count = cur.fetchone()[0]
        if source_count == 0:
            raise SystemExit("Expected seeded source registry rows")
        print(f"Seeded sources: {source_count}")

print("DB smoke check passed.")
