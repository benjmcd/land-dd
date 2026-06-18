from __future__ import annotations

from pathlib import Path
from typing import Any

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
    by_id = {
        require_mapping(review, "each query-plan review must be a mapping").get("id"): review
        for review in reviews
    }
    require(set(by_id) == EXPECTED_QUERY_IDS, "unexpected query-plan review set")
    for review_id, review in by_id.items():
        review = require_mapping(review, f"{review_id} declaration missing")
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
        statement = review.get("statement")
        require(isinstance(statement, str) and "EXPLAIN" in statement, f"{review_id} SQL missing")

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
