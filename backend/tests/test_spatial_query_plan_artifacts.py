from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any, TypedDict, cast

import pytest

yaml = cast(Any, importlib.import_module("yaml"))

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "config" / "spatial_query_plan.yaml"
CHECKER_PATH = REPO_ROOT / "scripts" / "spatial_query_plan_check.py"
DDL_PATH = REPO_ROOT / "db" / "migrations" / "0001_initial_spine.sql"
RUNBOOK_PATH = REPO_ROOT / "docs" / "runbooks" / "performance.md"
RUNTIME_CHECKER_PATH = REPO_ROOT / "scripts" / "spatial_query_plan_runtime_check.py"

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


class ExpectedStatement(TypedDict):
    alias: str
    table_ref: str
    primary_key: str
    spatial_column: str
    indexes: set[str]


EXPECTED_STATEMENTS: dict[str, ExpectedStatement] = {
    "area_parcel_intersections": {
        "alias": "p",
        "table_ref": "geo.parcels p",
        "primary_key": "parcel_id",
        "spatial_column": "geom",
        "indexes": {"areas_geom_gix", "parcels_geom_gix"},
    },
    "area_reference_feature_intersections": {
        "alias": "rf",
        "table_ref": "geo.reference_features rf",
        "primary_key": "feature_id",
        "spatial_column": "geom",
        "indexes": {"areas_geom_gix", "reference_features_geom_gix"},
    },
    "area_observation_intersections": {
        "alias": "o",
        "table_ref": "evidence.observations o",
        "primary_key": "evidence_id",
        "spatial_column": "geometry",
        "indexes": {"areas_geom_gix", "observations_geom_gix"},
    },
}


def _load_checker() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "spatial_query_plan_check_under_test",
        CHECKER_PATH,
    )
    assert spec is not None
    loader = spec.loader
    assert loader is not None
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def _config() -> dict[str, Any]:
    payload = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_spatial_query_plan_config_pins_validate_only_contract() -> None:
    config = _config()

    assert config["schema_version"] == "spatial_query_plan_v1"
    assert config["scope"] == "selected_county_private_mvp_spatial_queries"
    assert config["default_mode"] == "validate_only_static"
    assert config["ddl_authority"] == "db/migrations/0001_initial_spine.sql"
    assert config["wrappers"] == {
        "windows": "scripts/run_spatial_query_plan_check.ps1",
        "posix": "scripts/run_spatial_query_plan_check.sh",
    }
    assert config["runtime_review"] == {
        "checker": "scripts/spatial_query_plan_runtime_check.py",
        "wrappers": {
            "windows": "scripts/run_spatial_query_plan_runtime_check.ps1",
            "posix": "scripts/run_spatial_query_plan_runtime_check.sh",
        },
        "db_url_env": "DATABASE_URL_SYNC",
        "area_id_env": "SPATIAL_QUERY_PLAN_AREA_ID",
        "statement_timeout_ms": 30000,
        "output_schema_version": "spatial_query_plan_runtime_result_v1",
        "success_marker": "spatial query plan runtime check: ok",
    }

    limits = config["limits"]
    assert limits["opens_database_connection_by_default"] is False
    assert limits["seeds_runtime_state"] is False
    assert limits["generates_artifacts"] is False
    assert limits["network_access"] is False
    assert limits["hosted_performance_claim"] is False
    assert limits["level_10_completion_claim"] is False


def test_spatial_query_plan_config_pins_required_indexes_and_queries() -> None:
    config = _config()
    indexes = config["required_indexes"]
    assert isinstance(indexes, list)

    by_name = {index["name"]: index for index in indexes}
    assert set(by_name) == set(EXPECTED_INDEXES)
    for name, expected in EXPECTED_INDEXES.items():
        index = by_name[name]
        assert index["schema"] == expected["schema"]
        assert index["table"] == expected["table"]
        assert index["column"] == expected["column"]
        assert index["method"] == "gist"
        assert index["authority"] == "db/migrations/0001_initial_spine.sql"

    queries = config["query_plan_reviews"]
    assert isinstance(queries, list)
    by_id = {query["id"]: query for query in queries}
    assert set(by_id) == EXPECTED_QUERY_IDS
    for query in by_id.values():
        assert query["review_mode"] == "manual_read_only_explain"
        assert query["default_release_readiness"] is False
        assert query["expected_plan_node"] == "Index Scan"
        assert set(query["required_indexes"]).issubset(set(EXPECTED_INDEXES))
        assert query["runtime_requires_target_index"] in query["required_indexes"]
        assert query["runtime_requires_target_index"] != "areas_geom_gix"


def test_spatial_query_plan_statements_pin_canonical_identifiers() -> None:
    config = _config()
    queries = config["query_plan_reviews"]
    assert isinstance(queries, list)
    by_id = {query["id"]: query for query in queries}

    for query_id, expected in EXPECTED_STATEMENTS.items():
        statement = by_id[query_id]["statement"]
        assert isinstance(statement, str)
        alias = expected["alias"]
        primary_key = expected["primary_key"]
        spatial_column = expected["spatial_column"]

        assert f"SELECT {alias}.{primary_key}" in statement
        assert expected["table_ref"] in statement
        assert f"ST_Intersects({alias}.{spatial_column}, a.geom)" in statement
        assert "JOIN core.areas a" in statement
        assert "WHERE a.area_id = :area_id" in statement
        assert set(by_id[query_id]["required_indexes"]) == expected["indexes"]

    assert "observation_id" not in by_id["area_observation_intersections"]["statement"]


def test_spatial_query_plan_checker_rejects_noncanonical_statement_column(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checker = cast(Any, _load_checker())
    config = _config()

    for query in config["query_plan_reviews"]:
        if query["id"] == "area_observation_intersections":
            query["statement"] = query["statement"].replace(
                "o.evidence_id",
                "o.observation_id",
            )

    monkeypatch.setattr(checker, "load_config", lambda: config)

    with pytest.raises(SystemExit, match="observation_id"):
        checker.validate_config()


def test_spatial_query_plan_checker_reads_observation_primary_key_from_ddl() -> None:
    checker = cast(Any, _load_checker())

    primary_keys = checker.load_canonical_primary_keys()

    assert primary_keys["evidence.observations"] == "evidence_id"
    assert "observation_id" not in checker.load_canonical_columns()["evidence.observations"]


def test_spatial_query_plan_checker_imports_and_passes() -> None:
    checker = cast(Any, _load_checker())

    checker.validate_config()
    checker.validate_index_ddl()
    checker.validate_wrappers()
    checker.validate_runbook()
    assert checker.main() == 0


def test_spatial_query_plan_checker_is_static_by_default() -> None:
    script = CHECKER_PATH.read_text(encoding="utf-8")

    assert "db/migrations/0001_initial_spine.sql" in script
    assert "psycopg" not in script
    assert "create_engine" not in script
    assert "requests" not in script
    assert "subprocess" not in script
    assert "write_text" not in script


def test_spatial_query_plan_wrappers_delegate_to_shared_validator() -> None:
    for script_path in (
        REPO_ROOT / "scripts" / "run_spatial_query_plan_check.ps1",
        REPO_ROOT / "scripts" / "run_spatial_query_plan_check.sh",
    ):
        script = script_path.read_text(encoding="utf-8")

        assert "spatial_query_plan_check.py" in script
        assert "spatial query plan check: ok" in script


def test_spatial_query_plan_runtime_wrappers_are_manual_opt_in() -> None:
    config = _config()
    runtime_review = config["runtime_review"]

    for script_path in (
        REPO_ROOT / runtime_review["wrappers"]["windows"],
        REPO_ROOT / runtime_review["wrappers"]["posix"],
    ):
        script = script_path.read_text(encoding="utf-8")

        assert "spatial_query_plan_runtime_check.py" in script
        assert "--area-id" not in script
        assert "SPATIAL_QUERY_PLAN_AREA_ID" not in script
        assert "DATABASE_URL_SYNC" not in script

    runtime_checker = RUNTIME_CHECKER_PATH.read_text(encoding="utf-8")
    assert "spatial query plan runtime check: ok" in runtime_checker


def test_spatial_indexes_declared_in_canonical_ddl() -> None:
    ddl = DDL_PATH.read_text(encoding="utf-8").lower()

    for name, expected in EXPECTED_INDEXES.items():
        phrase = (
            f"create index if not exists {name} on "
            f"{expected['schema']}.{expected['table']} using gist "
            f"({expected['column']})"
        )
        assert phrase in ddl


def test_performance_runbook_records_spatial_plan_review_boundary() -> None:
    runbook = RUNBOOK_PATH.read_text(encoding="utf-8")

    for phrase in (
        "Spatial query plan review",
        "config/spatial_query_plan.yaml",
        "run_spatial_query_plan_check.ps1",
        "spatial_query_plan_v1",
        "EXPLAIN ANALYZE",
        "GIST index",
        "Index Scan using <idx>",
        "opens no database connection by default",
        "run_spatial_query_plan_runtime_check.ps1",
        "SPATIAL_QUERY_PLAN_AREA_ID",
        "DATABASE_URL_SYNC",
        "Runtime `EXPLAIN ANALYZE` evidence remains manual/read-only",
        "writes JSON only when `--output-json` is supplied",
        "No automated live spatial query-plan gate in CI",
    ):
        assert phrase in runbook
