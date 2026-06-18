from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any, cast

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_CHECKER_PATH = REPO_ROOT / "scripts" / "spatial_query_plan_runtime_check.py"


def _load_runtime_checker() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "spatial_query_plan_runtime_check_under_test",
        RUNTIME_CHECKER_PATH,
    )
    assert spec is not None
    loader = spec.loader
    assert loader is not None
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def test_runtime_checker_imports_without_connecting_to_database(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DATABASE_URL_SYNC", raising=False)
    monkeypatch.delenv("SPATIAL_QUERY_PLAN_AREA_ID", raising=False)

    checker = cast(Any, _load_runtime_checker())

    assert checker.SUCCESS_MARKER == "spatial query plan runtime check: ok"


def test_runtime_checker_is_read_only_and_has_no_seed_path() -> None:
    script = RUNTIME_CHECKER_PATH.read_text(encoding="utf-8")

    assert "BEGIN READ ONLY" in script
    assert "ROLLBACK" in script
    assert "SET LOCAL statement_timeout" in script
    assert "INSERT INTO" not in script
    assert "UPDATE " not in script
    assert "DELETE FROM" not in script
    assert "CREATE TABLE" not in script


def test_runtime_checker_requires_db_url_before_area_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checker = cast(Any, _load_runtime_checker())
    monkeypatch.delenv("DATABASE_URL_SYNC", raising=False)
    monkeypatch.setenv("SPATIAL_QUERY_PLAN_AREA_ID", "area-1")

    with pytest.raises(SystemExit, match="DATABASE_URL_SYNC"):
        checker.parse_args([])


def test_runtime_checker_requires_area_id_before_connecting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checker = cast(Any, _load_runtime_checker())
    monkeypatch.setenv("DATABASE_URL_SYNC", "postgresql://example")
    monkeypatch.delenv("SPATIAL_QUERY_PLAN_AREA_ID", raising=False)

    with pytest.raises(SystemExit, match="SPATIAL_QUERY_PLAN_AREA_ID"):
        checker.parse_args([])


def test_runtime_checker_converts_config_sql_to_json_explain() -> None:
    checker = cast(Any, _load_runtime_checker())

    sql = checker.to_runtime_explain_sql(
        """
        EXPLAIN (ANALYZE, BUFFERS)
        SELECT p.parcel_id
        FROM geo.parcels p
        JOIN core.areas a ON ST_Intersects(p.geom, a.geom)
        WHERE a.area_id = :area_id;
        """,
    )

    assert sql.startswith("EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)")
    assert "EXPLAIN (ANALYZE, BUFFERS)\n" not in sql
    assert "WHERE a.area_id = %(area_id)s" in sql
    assert sql.endswith(";")


def test_runtime_checker_accepts_select_sql_for_conversion() -> None:
    checker = cast(Any, _load_runtime_checker())

    sql = checker.to_runtime_explain_sql(
        "SELECT p.parcel_id FROM geo.parcels p WHERE p.area_id = :area_id",
    )

    assert sql == (
        "EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) "
        "SELECT p.parcel_id FROM geo.parcels p WHERE p.area_id = %(area_id)s;"
    )


def test_runtime_checker_parses_nested_plan_indexes() -> None:
    checker = cast(Any, _load_runtime_checker())
    plan = [
        {
            "Plan": {
                "Node Type": "Nested Loop",
                "Plans": [
                    {
                        "Node Type": "Index Scan",
                        "Index Name": "areas_geom_gix",
                        "Relation Name": "areas",
                    },
                    {
                        "Node Type": "Bitmap Heap Scan",
                        "Plans": [
                            {
                                "Node Type": "Bitmap Index Scan",
                                "Index Name": "parcels_geom_gix",
                            },
                        ],
                    },
                ],
            },
        },
    ]

    evidence = checker.plan_evidence(plan)

    assert "areas_geom_gix" in evidence.index_names
    assert "parcels_geom_gix" in evidence.index_names
    assert "Index Scan" in evidence.node_types
    assert "Bitmap Index Scan" in evidence.node_types


def test_runtime_checker_parses_json_string_plan() -> None:
    checker = cast(Any, _load_runtime_checker())
    payload = json.dumps(
        [
            {
                "Plan": {
                    "Node Type": "Index Scan",
                    "Index Name": "reference_features_geom_gix",
                },
            },
        ],
    )

    evidence = checker.plan_evidence(payload)

    assert evidence.index_names == {"reference_features_geom_gix"}
    assert evidence.node_types == {"Index Scan"}


def test_runtime_checker_fails_closed_when_target_index_missing() -> None:
    checker = cast(Any, _load_runtime_checker())

    with pytest.raises(SystemExit, match="missing required target index"):
        checker.require_target_index(
            review_id="area_parcel_intersections",
            target_index="parcels_geom_gix",
            evidence=checker.PlanEvidence(index_names={"areas_geom_gix"}, node_types=set()),
        )


def test_runtime_checker_output_json_is_explicit_opt_in(tmp_path: Path) -> None:
    checker = cast(Any, _load_runtime_checker())
    result = {
        "schema_version": "spatial_query_plan_runtime_result_v1",
        "reviews": [],
    }
    output_path = tmp_path / "plan.json"

    checker.write_result_json(None, result)
    assert not output_path.exists()

    checker.write_result_json(output_path, result)
    assert json.loads(output_path.read_text(encoding="utf-8")) == result
