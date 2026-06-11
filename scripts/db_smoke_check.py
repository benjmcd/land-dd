from __future__ import annotations

import csv
import os
import sys
from pathlib import Path
from typing import Any, cast

try:
    import psycopg
except ImportError:  # pragma: no cover
    print(
        "psycopg is not installed. Run: cd backend && python -m pip install -e "
        "'.[dev]'",
        file=sys.stderr,
    )
    raise SystemExit(1) from None

ROOT_DIR = Path(__file__).resolve().parents[1]
DB_URL = os.environ.get("DATABASE_URL_SYNC", "postgresql://land:land@localhost:5432/land_diligence")
SOURCE_REGISTRY_PATH = ROOT_DIR / "registers" / "data_source_registry.csv"
REQUIRED_SCHEMAS = [
    "core",
    "source",
    "geo",
    "evidence",
    "rules",
    "claims",
    "reports",
    "jobs",
    "audit",
]
REQUIRED_TABLES = {
    "core": ["areas", "area_versions", "intents", "intent_versions"],
    "source": ["sources", "datasets", "dataset_versions", "ingest_runs"],
    "evidence": ["observations"],
    "rules": ["rule_sets", "rule_versions", "rule_execution_runs"],
    "claims": ["claims", "claim_evidence"],
    "reports": ["report_runs", "report_sections", "report_assets"],
    "audit": ["events"],
}
REQUIRED_COLUMNS = {
    ("source", "sources"): [
        "source_id",
        "name",
        "authority_level",
        "commercial_use_status",
        "metadata",
    ],
    ("source", "datasets"): ["dataset_id", "source_id", "dataset_name", "domain"],
    ("source", "dataset_versions"): [
        "dataset_version_id",
        "dataset_id",
        "version_label",
        "retrieved_at",
        "is_current",
    ],
    ("source", "ingest_runs"): ["ingest_run_id", "dataset_version_id", "status", "metrics"],
    ("core", "areas"): ["area_id", "area_type", "geom", "centroid", "bbox"],
    ("evidence", "observations"): [
        "evidence_id",
        "area_id",
        "dataset_version_id",
        "ingest_run_id",
        "observed_value",
        "is_source_failure",
    ],
    ("claims", "claims"): [
        "claim_id",
        "area_id",
        "rule_execution_run_id",
        "intent_id",
        "severity",
        "confidence",
    ],
    ("claims", "claim_evidence"): ["claim_id", "evidence_id", "support_role"],
    ("rules", "rule_versions"): ["rule_version_id", "rule_set_id", "version_label", "ruleset_body"],
    ("rules", "rule_execution_runs"): [
        "rule_execution_run_id",
        "area_id",
        "rule_version_id",
        "report_run_id",
        "status",
    ],
    ("reports", "report_runs"): [
        "report_run_id",
        "area_id",
        "intent_id",
        "intent_version_id",
        "rule_version_id",
        "status",
        "output_uri",
        "machine_json_uri",
        "source_manifest",
        "cost_metrics",
    ],
}
REQUIRED_ENUM_LABELS = {
    ("core", "intent_code"): [
        "rural_land_purchase",
        "homestead_feasibility",
    ],
    ("jobs", "job_status"): [
        "queued",
        "running",
        "succeeded",
        "failed",
        "cancelled",
        "needs_review",
    ],
}
REQUIRED_FOREIGN_KEYS = [
    ("source", "datasets", "source_id"),
    ("source", "dataset_versions", "dataset_id"),
    ("source", "ingest_runs", "dataset_version_id"),
    ("evidence", "observations", "area_id"),
    ("claims", "claim_evidence", "claim_id"),
    ("claims", "claim_evidence", "evidence_id"),
    ("rules", "rule_execution_runs", "rule_version_id"),
    ("reports", "report_runs", "area_id"),
]


def _load_expected_source_registry_ids(
    registry_path: Path = SOURCE_REGISTRY_PATH,
) -> set[str]:
    with registry_path.open(newline="", encoding="utf-8") as csv_file:
        return {
            row["Source ID"]
            for row in csv.DictReader(csv_file)
            if row.get("Source ID")
        }


def _validate_seeded_source_registry_ids(
    registry_counts: dict[str, int],
    expected_registry_ids: set[str],
) -> None:
    actual_registry_ids = set(registry_counts)
    missing = sorted(expected_registry_ids - actual_registry_ids)
    unexpected = sorted(actual_registry_ids - expected_registry_ids)
    duplicates = sorted(
        registry_id
        for registry_id, count in registry_counts.items()
        if count != 1
    )
    if missing:
        raise SystemExit(f"Missing seeded source registry IDs: {missing}")
    if unexpected:
        raise SystemExit(f"Unexpected seeded source registry IDs: {unexpected}")
    if duplicates:
        raise SystemExit(f"Duplicated seeded source registry IDs: {duplicates}")


def _fetchone_required(cursor: Any) -> tuple[Any, ...]:
    row = cursor.fetchone()
    if row is None:
        raise SystemExit("Expected database query to return one row")
    return cast(tuple[Any, ...], row)


def main() -> None:
    expected_registry_ids = _load_expected_source_registry_ids()
    with psycopg.connect(DB_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT postgis_version()")
            postgis_version = _fetchone_required(cur)[0]
            print(f"PostGIS version: {postgis_version}")

            cur.execute("SELECT schema_name FROM information_schema.schemata")
            schemas = {row[0] for row in cur.fetchall()}
            missing = [schema for schema in REQUIRED_SCHEMAS if schema not in schemas]
            if missing:
                raise SystemExit(f"Missing schemas: {missing}")
            print(f"Required schemas: {len(REQUIRED_SCHEMAS)}")

            missing_tables: list[str] = []
            for schema, tables in REQUIRED_TABLES.items():
                for table in tables:
                    cur.execute("SELECT to_regclass(%s)", (f"{schema}.{table}",))
                    if _fetchone_required(cur)[0] is None:
                        missing_tables.append(f"{schema}.{table}")
            if missing_tables:
                raise SystemExit(f"Missing tables: {missing_tables}")
            print(f"Required tables: {sum(len(tables) for tables in REQUIRED_TABLES.values())}")

            for table_ref, required_columns in REQUIRED_COLUMNS.items():
                schema, table = table_ref
                cur.execute(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = %s AND table_name = %s
                    """,
                    (schema, table),
                )
                columns = {row[0] for row in cur.fetchall()}
                missing_columns = [
                    column for column in required_columns if column not in columns
                ]
                if missing_columns:
                    raise SystemExit(
                        f"Missing columns on {schema}.{table}: {missing_columns}"
                    )
            print(f"Required column groups: {len(REQUIRED_COLUMNS)}")

            for enum_ref, required_labels in REQUIRED_ENUM_LABELS.items():
                schema, enum_name = enum_ref
                cur.execute(
                    """
                    SELECT enumlabel
                    FROM pg_enum
                    JOIN pg_type ON pg_type.oid = pg_enum.enumtypid
                    JOIN pg_namespace ON pg_namespace.oid = pg_type.typnamespace
                    WHERE pg_namespace.nspname = %s AND pg_type.typname = %s
                    """,
                    (schema, enum_name),
                )
                labels = {row[0] for row in cur.fetchall()}
                missing_labels = [
                    label for label in required_labels if label not in labels
                ]
                if missing_labels:
                    raise SystemExit(
                        f"Missing enum labels on {schema}.{enum_name}: {missing_labels}"
                    )
            print(f"Required enums: {len(REQUIRED_ENUM_LABELS)}")

            missing_fks: list[str] = []
            for schema, table, column in REQUIRED_FOREIGN_KEYS:
                cur.execute(
                    """
                    SELECT 1
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                      ON tc.constraint_schema = kcu.constraint_schema
                     AND tc.constraint_name = kcu.constraint_name
                     AND tc.table_schema = kcu.table_schema
                     AND tc.table_name = kcu.table_name
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                      AND tc.table_schema = %s
                      AND tc.table_name = %s
                      AND kcu.column_name = %s
                    LIMIT 1
                    """,
                    (schema, table, column),
                )
                if cur.fetchone() is None:
                    missing_fks.append(f"{schema}.{table}.{column}")
            if missing_fks:
                raise SystemExit(f"Missing foreign keys: {missing_fks}")
            print(f"Required foreign keys: {len(REQUIRED_FOREIGN_KEYS)}")

            cur.execute(
                """
                SELECT metadata->>'source_registry_id', count(*)
                FROM source.sources
                WHERE metadata ? 'source_registry_id'
                GROUP BY 1
                """
            )
            registry_counts = {
                row[0]: row[1]
                for row in cur.fetchall()
            }
            _validate_seeded_source_registry_ids(
                registry_counts,
                expected_registry_ids,
            )
            print(f"Seeded source registry rows: {len(expected_registry_ids)}")

            cur.execute("SELECT count(*) FROM source.sources")
            source_count = _fetchone_required(cur)[0]
            print(f"Total sources: {source_count}")

            cur.execute("SELECT intent_code::text FROM core.intents")
            intent_codes = {row[0] for row in cur.fetchall()}
            missing_intents = {
                "rural_land_purchase",
                "homestead_feasibility",
            } - intent_codes
            if missing_intents:
                raise SystemExit(f"Missing seeded intents: {sorted(missing_intents)}")
            print(f"Seeded intents: {len(intent_codes)}")

    print("DB smoke check passed.")


if __name__ == "__main__":
    main()
