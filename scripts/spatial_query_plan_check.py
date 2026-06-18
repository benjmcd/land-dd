from __future__ import annotations

import re
from pathlib import Path
from typing import Any, TypedDict

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = "config/spatial_query_plan.yaml"
DDL_AUTHORITY = "db/migrations/0001_initial_spine.sql"
WINDOWS_WRAPPER = "scripts/run_spatial_query_plan_check.ps1"
POSIX_WRAPPER = "scripts/run_spatial_query_plan_check.sh"
PERFORMANCE_RUNBOOK = "docs/runbooks/performance.md"

EXPECTED_INDEXES = {
    "areas_geom_gix": {"schema": "core", "table": "areas", "column": "geom"},
    "area_versions_geom_gix": {
        "schema": "core",
        "table": "area_versions",
        "column": "geom",
    },
    "parcels_geom_gix": {"schema": "geo", "table": "parcels", "column": "geom"},
    "reference_features_geom_gix": {
        "schema": "geo",
        "table": "reference_features",
        "column": "geom",
    },
    "observations_geom_gix": {
        "schema": "evidence",
        "table": "observations",
        "column": "geometry",
    },
}
EXPECTED_QUERY_IDS = {
    "area_parcel_intersections",
    "area_reference_feature_intersections",
    "area_observation_intersections",
}


class QueryContract(TypedDict):
    target_schema: str
    target_table: str
    target_alias: str
    target_primary_key: str
    target_spatial_column: str
    required_indexes: set[str]


EXPECTED_QUERY_CONTRACTS: dict[str, QueryContract] = {
    "area_parcel_intersections": {
        "target_schema": "geo",
        "target_table": "parcels",
        "target_alias": "p",
        "target_primary_key": "parcel_id",
        "target_spatial_column": "geom",
        "required_indexes": {"areas_geom_gix", "parcels_geom_gix"},
    },
    "area_reference_feature_intersections": {
        "target_schema": "geo",
        "target_table": "reference_features",
        "target_alias": "rf",
        "target_primary_key": "feature_id",
        "target_spatial_column": "geom",
        "required_indexes": {"areas_geom_gix", "reference_features_geom_gix"},
    },
    "area_observation_intersections": {
        "target_schema": "evidence",
        "target_table": "observations",
        "target_alias": "o",
        "target_primary_key": "evidence_id",
        "target_spatial_column": "geometry",
        "required_indexes": {"areas_geom_gix", "observations_geom_gix"},
    },
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def require_mapping(value: Any, message: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SystemExit(message)
    return value


def require_list(value: Any, message: str) -> list[Any]:
    if not isinstance(value, list):
        raise SystemExit(message)
    return value


def read_text(path_text: str) -> str:
    return (ROOT / path_text).read_text(encoding="utf-8")


def require_existing_file(path_text: str) -> None:
    require((ROOT / path_text).is_file(), f"missing spatial query-plan artifact: {path_text}")


def load_config() -> dict[str, Any]:
    require_existing_file(CONFIG_PATH)
    return require_mapping(
        yaml.safe_load(read_text(CONFIG_PATH)),
        "spatial query-plan config must be a mapping",
    )


def normalized_sql(statement: str) -> str:
    return " ".join(statement.lower().split())


def load_canonical_columns() -> dict[str, set[str]]:
    ddl = read_text(DDL_AUTHORITY)
    tables: dict[str, set[str]] = {}
    table_pattern = re.compile(
        r"create table if not exists\s+([a-z_]+\.[a-z_]+)\s*\((.*?)\n\);",
        re.IGNORECASE | re.DOTALL,
    )
    for match in table_pattern.finditer(ddl):
        table_ref = match.group(1).lower()
        columns: set[str] = set()
        for raw_line in match.group(2).splitlines():
            line = raw_line.strip().rstrip(",")
            if not line or line.upper().startswith(
                ("CONSTRAINT", "PRIMARY", "UNIQUE", "FOREIGN"),
            ):
                continue
            column_match = re.match(r"([a-z_][a-z0-9_]*)\s+", line, re.IGNORECASE)
            if column_match is not None:
                columns.add(column_match.group(1).lower())
        require(bool(columns), f"canonical DDL columns missing for {table_ref}")
        tables[table_ref] = columns
    return tables


def load_canonical_primary_keys() -> dict[str, str]:
    ddl = read_text(DDL_AUTHORITY)
    primary_keys: dict[str, str] = {}
    table_pattern = re.compile(
        r"create table if not exists\s+([a-z_]+\.[a-z_]+)\s*\((.*?)\n\);",
        re.IGNORECASE | re.DOTALL,
    )
    for match in table_pattern.finditer(ddl):
        table_ref = match.group(1).lower()
        for raw_line in match.group(2).splitlines():
            line = raw_line.strip().rstrip(",")
            if "primary key" not in line.lower():
                continue
            column_match = re.match(r"([a-z_][a-z0-9_]*)\s+", line, re.IGNORECASE)
            if column_match is not None:
                primary_keys[table_ref] = column_match.group(1).lower()
                break
    return primary_keys


def require_phrase(statement: str, phrase: str, review_id: str) -> None:
    require(
        phrase.lower() in normalized_sql(statement),
        f"{review_id} SQL missing phrase: {phrase}",
    )


def validate_statement_columns(
    review_id: str,
    statement: str,
    alias_tables: dict[str, str],
    canonical_columns: dict[str, set[str]],
) -> None:
    aliases = set(alias_tables)
    canonical_table_refs = set(canonical_columns)
    column_refs = re.findall(r"\b([a-z][a-z0-9_]*)\.([a-z][a-z0-9_]*)\b", statement.lower())
    for alias, column in column_refs:
        if f"{alias}.{column}" in canonical_table_refs:
            continue
        require(alias in aliases, f"{review_id} SQL references unexpected alias: {alias}")
        table_ref = alias_tables[alias]
        require(
            table_ref in canonical_columns,
            f"{review_id} canonical table missing: {table_ref}",
        )
        require(
            column in canonical_columns[table_ref],
            f"{review_id} SQL references non-canonical column {alias}.{column}",
        )


def validate_statement_contract(
    review_id: str,
    review: dict[str, Any],
    canonical_columns: dict[str, set[str]],
    canonical_primary_keys: dict[str, str],
) -> None:
    contract = EXPECTED_QUERY_CONTRACTS[review_id]
    target_table_ref = f"{contract['target_schema']}.{contract['target_table']}"
    target_alias = contract["target_alias"]
    target_primary_key = contract["target_primary_key"]
    target_spatial_column = contract["target_spatial_column"]
    statement = review.get("statement")
    if not isinstance(statement, str) or "EXPLAIN" not in statement:
        raise SystemExit(f"{review_id} SQL missing")

    required_indexes: set[str] = set()
    for index_name in require_list(review.get("required_indexes"), f"{review_id} indexes missing"):
        if not isinstance(index_name, str):
            raise SystemExit(f"{review_id} required index names must be strings")
        required_indexes.add(index_name)
    require(
        required_indexes == contract["required_indexes"],
        f"{review_id} required indexes do not match expected table relationship",
    )
    for index_name in required_indexes:
        index = EXPECTED_INDEXES[index_name]
        if index_name == "areas_geom_gix":
            expected_index = {"schema": "core", "table": "areas", "column": "geom"}
        else:
            expected_index = {
                "schema": contract["target_schema"],
                "table": contract["target_table"],
                "column": target_spatial_column,
            }
        require(
            index == expected_index,
            f"{review_id} {index_name} table relationship mismatch",
        )

    require(
        canonical_primary_keys.get(target_table_ref) == target_primary_key,
        f"{review_id} selected key is not canonical primary key for {target_table_ref}",
    )

    validate_statement_columns(
        review_id,
        statement,
        {target_alias: target_table_ref, "a": "core.areas"},
        canonical_columns,
    )

    require_phrase(statement, "EXPLAIN (ANALYZE, BUFFERS)", review_id)
    require_phrase(statement, f"SELECT {target_alias}.{target_primary_key}", review_id)
    require_phrase(statement, f"FROM {target_table_ref} {target_alias}", review_id)
    require_phrase(statement, "JOIN core.areas a", review_id)
    require_phrase(
        statement,
        f"ST_Intersects({target_alias}.{target_spatial_column}, a.geom)",
        review_id,
    )
    require_phrase(statement, "WHERE a.area_id = :area_id", review_id)


def validate_config() -> None:
    config = load_config()
    require(
        config.get("schema_version") == "spatial_query_plan_v1",
        "unexpected spatial query-plan schema",
    )
    require(
        config.get("scope") == "selected_county_private_mvp_spatial_queries",
        "spatial query-plan scope mismatch",
    )
    require(
        config.get("default_mode") == "validate_only_static",
        "spatial query-plan default mode must remain validate-only static",
    )
    require(config.get("ddl_authority") == DDL_AUTHORITY, "spatial DDL authority mismatch")

    wrappers = require_mapping(config.get("wrappers"), "spatial wrappers missing")
    require(wrappers.get("windows") == WINDOWS_WRAPPER, "Windows wrapper mismatch")
    require(wrappers.get("posix") == POSIX_WRAPPER, "POSIX wrapper mismatch")

    indexes = require_list(config.get("required_indexes"), "spatial indexes missing")
    by_name = {
        require_mapping(index, "each spatial index must be a mapping").get("name"): index
        for index in indexes
    }
    require(set(by_name) == set(EXPECTED_INDEXES), "unexpected spatial index set")
    for name, expected in EXPECTED_INDEXES.items():
        index = require_mapping(by_name[name], f"{name} index declaration missing")
        for key, value in expected.items():
            require(index.get(key) == value, f"{name} {key} mismatch")
        require(index.get("method") == "gist", f"{name} must remain a GIST index")
        require(index.get("authority") == DDL_AUTHORITY, f"{name} authority mismatch")

    reviews = require_list(config.get("query_plan_reviews"), "query-plan reviews missing")
    canonical_columns = load_canonical_columns()
    canonical_primary_keys = load_canonical_primary_keys()
    by_id = {
        require_mapping(review, "each query-plan review must be a mapping").get("id"): review
        for review in reviews
    }
    require(set(by_id) == EXPECTED_QUERY_IDS, "unexpected query-plan review set")
    for review_id in sorted(EXPECTED_QUERY_IDS):
        review = require_mapping(by_id[review_id], f"{review_id} declaration missing")
        require(
            review.get("review_mode") == "manual_read_only_explain",
            f"{review_id} must stay manual/read-only",
        )
        require(
            review.get("default_release_readiness") is False,
            f"{review_id} must not run by default in release readiness",
        )
        require(
            review.get("expected_plan_node") == "Index Scan",
            f"{review_id} expected plan node mismatch",
        )
        required_indexes = set(
            require_list(review.get("required_indexes"), f"{review_id} indexes missing"),
        )
        require(bool(required_indexes), f"{review_id} must name required indexes")
        require(
            required_indexes.issubset(set(EXPECTED_INDEXES)),
            f"{review_id} references an unknown spatial index",
        )
        validate_statement_contract(
            review_id,
            review,
            canonical_columns,
            canonical_primary_keys,
        )

    limits = require_mapping(config.get("limits"), "spatial query-plan limits missing")
    for key in (
        "opens_database_connection_by_default",
        "seeds_runtime_state",
        "generates_artifacts",
        "network_access",
        "hosted_performance_claim",
        "level_10_completion_claim",
    ):
        require(limits.get(key) is False, f"{key} must remain false")


def validate_index_ddl() -> None:
    require_existing_file(DDL_AUTHORITY)
    ddl = " ".join(read_text(DDL_AUTHORITY).lower().split())
    for name, expected in EXPECTED_INDEXES.items():
        phrase = (
            f"create index if not exists {name} on "
            f"{expected['schema']}.{expected['table']} using gist "
            f"({expected['column']})"
        )
        require(phrase in ddl, f"canonical DDL missing expected GIST index: {name}")


def validate_wrappers() -> None:
    for path_text in (WINDOWS_WRAPPER, POSIX_WRAPPER):
        require_existing_file(path_text)
        text = read_text(path_text)
        require(
            "spatial_query_plan_check.py" in text,
            f"{path_text} must delegate to shared validator",
        )
        require(
            "spatial query plan check: ok" in text,
            f"{path_text} must print success marker",
        )


def validate_runbook() -> None:
    require_existing_file(PERFORMANCE_RUNBOOK)
    runbook = read_text(PERFORMANCE_RUNBOOK)
    for phrase in (
        "Spatial query plan review",
        "config/spatial_query_plan.yaml",
        "run_spatial_query_plan_check.ps1",
        "spatial_query_plan_v1",
        "EXPLAIN ANALYZE",
        "GIST index",
        "Index Scan using <idx>",
        "opens no database connection by default",
        "Runtime `EXPLAIN ANALYZE` evidence remains manual/read-only",
        "No automated live spatial query-plan gate in CI",
    ):
        require(phrase in runbook, f"performance runbook missing phrase: {phrase}")


def main() -> int:
    validate_config()
    validate_index_ddl()
    validate_wrappers()
    validate_runbook()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
