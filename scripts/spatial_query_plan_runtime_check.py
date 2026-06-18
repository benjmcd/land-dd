from __future__ import annotations

import argparse
import contextlib
import importlib.util
import json
import os
import re
from pathlib import Path
from types import ModuleType
from typing import Any, NamedTuple

ROOT = Path(__file__).resolve().parents[1]
STATIC_CHECKER_PATH = ROOT / "scripts" / "spatial_query_plan_check.py"
DB_URL_ENV = "DATABASE_URL_SYNC"
AREA_ID_ENV = "SPATIAL_QUERY_PLAN_AREA_ID"
SUCCESS_MARKER = "spatial query plan runtime check: ok"


class RuntimeOptions(NamedTuple):
    db_url: str
    area_id: str
    output_json: Path | None
    statement_timeout_ms: int | None


class PlanEvidence(NamedTuple):
    index_names: set[str]
    node_types: set[str]


def load_static_checker() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "spatial_query_plan_check_for_runtime",
        STATIC_CHECKER_PATH,
    )
    if spec is None or spec.loader is None:
        raise SystemExit("unable to load static spatial query-plan checker")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_args(argv: list[str] | None = None) -> RuntimeOptions:
    parser = argparse.ArgumentParser(
        description="Run opt-in read-only spatial query-plan EXPLAIN checks.",
    )
    parser.add_argument("--db-url", default=os.environ.get(DB_URL_ENV))
    parser.add_argument("--area-id", default=os.environ.get(AREA_ID_ENV))
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--statement-timeout-ms", type=int)
    args = parser.parse_args(argv)

    db_url = args.db_url
    if not isinstance(db_url, str) or not db_url.strip():
        raise SystemExit(f"missing required --db-url or {DB_URL_ENV}")

    area_id = args.area_id
    if not isinstance(area_id, str) or not area_id.strip():
        raise SystemExit(f"missing required --area-id or {AREA_ID_ENV}")

    statement_timeout_ms = args.statement_timeout_ms
    if statement_timeout_ms is not None and statement_timeout_ms <= 0:
        raise SystemExit("--statement-timeout-ms must be greater than zero")

    return RuntimeOptions(
        db_url=db_url.strip(),
        area_id=area_id.strip(),
        output_json=args.output_json,
        statement_timeout_ms=statement_timeout_ms,
    )


def to_runtime_explain_sql(statement: str) -> str:
    sql = statement.strip().rstrip(";")
    explain_match = re.match(
        r"^EXPLAIN\s*\([^)]*\)\s*(?P<body>.*)$",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if explain_match is not None:
        sql = explain_match.group("body").strip()
    converted = sql.replace(":area_id", "%(area_id)s")
    return f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {converted};"


def _json_payload(value: Any) -> Any:
    if isinstance(value, bytes):
        return json.loads(value.decode("utf-8"))
    if isinstance(value, str):
        return json.loads(value)
    return value


def plan_evidence(plan_payload: Any) -> PlanEvidence:
    payload = _json_payload(plan_payload)
    index_names: set[str] = set()
    node_types: set[str] = set()

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            index_name = value.get("Index Name")
            if isinstance(index_name, str):
                index_names.add(index_name)
            node_type = value.get("Node Type")
            if isinstance(node_type, str):
                node_types.add(node_type)
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(payload)
    return PlanEvidence(index_names=index_names, node_types=node_types)


def require_target_index(
    *,
    review_id: str,
    target_index: str,
    evidence: PlanEvidence,
) -> None:
    if target_index not in evidence.index_names:
        found = ", ".join(sorted(evidence.index_names)) or "<none>"
        raise SystemExit(
            f"{review_id} missing required target index {target_index}; found {found}",
        )


def write_result_json(output_path: Path | None, result: dict[str, Any]) -> None:
    if output_path is None:
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _runtime_config(config: dict[str, Any]) -> tuple[dict[str, Any], int]:
    runtime_review = config.get("runtime_review")
    if not isinstance(runtime_review, dict):
        raise SystemExit("spatial query-plan runtime metadata missing")
    timeout_ms = runtime_review.get("statement_timeout_ms")
    if not isinstance(timeout_ms, int) or timeout_ms <= 0:
        raise SystemExit("runtime statement_timeout_ms must be a positive integer")
    return runtime_review, timeout_ms


def _query_reviews(config: dict[str, Any]) -> list[dict[str, Any]]:
    reviews = config.get("query_plan_reviews")
    if not isinstance(reviews, list):
        raise SystemExit("query-plan reviews missing")
    result: list[dict[str, Any]] = []
    for review in reviews:
        if not isinstance(review, dict):
            raise SystemExit("each query-plan review must be a mapping")
        result.append(review)
    return result


def _run_database_checks(
    *,
    db_url: str,
    area_id: str,
    timeout_ms: int,
    reviews: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    try:
        import psycopg
    except ImportError as exc:
        raise SystemExit("psycopg is required for runtime spatial query-plan checks") from exc

    results: list[dict[str, Any]] = []
    try:
        with psycopg.connect(db_url, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("BEGIN READ ONLY")
                try:
                    cur.execute(f"SET LOCAL statement_timeout = {timeout_ms}")
                    cur.execute(
                        "SELECT 1 FROM core.areas WHERE area_id = %(area_id)s LIMIT 1",
                        {"area_id": area_id},
                    )
                    if cur.fetchone() is None:
                        raise SystemExit(f"area_id not found in core.areas: {area_id}")

                    for review in reviews:
                        review_id = review.get("id")
                        target_index = review.get("runtime_requires_target_index")
                        statement = review.get("statement")
                        if not isinstance(review_id, str):
                            raise SystemExit("query-plan review id missing")
                        if not isinstance(target_index, str):
                            raise SystemExit(f"{review_id} target index metadata missing")
                        if not isinstance(statement, str):
                            raise SystemExit(f"{review_id} SQL missing")

                        cur.execute(
                            to_runtime_explain_sql(statement),
                            {"area_id": area_id},
                        )
                        row = cur.fetchone()
                        if row is None:
                            raise SystemExit(f"{review_id} produced no plan rows")
                        plan = _json_payload(row[0])
                        evidence = plan_evidence(plan)
                        require_target_index(
                            review_id=review_id,
                            target_index=target_index,
                            evidence=evidence,
                        )
                        results.append(
                            {
                                "id": review_id,
                                "required_target_index": target_index,
                                "observed_indexes": sorted(evidence.index_names),
                                "observed_node_types": sorted(evidence.node_types),
                                "plan": plan,
                            },
                        )
                finally:
                    with contextlib.suppress(Exception):
                        cur.execute("ROLLBACK")
    except SystemExit:
        raise
    except Exception as exc:
        raise SystemExit(f"spatial query-plan runtime check failed: {exc}") from exc
    return results


def run_runtime_check(options: RuntimeOptions) -> dict[str, Any]:
    static_checker = load_static_checker()
    static_checker.validate_config()
    config = static_checker.load_config()
    runtime_review, configured_timeout_ms = _runtime_config(config)
    timeout_ms = options.statement_timeout_ms or configured_timeout_ms

    reviews = _query_reviews(config)
    results = _run_database_checks(
        db_url=options.db_url,
        area_id=options.area_id,
        timeout_ms=timeout_ms,
        reviews=reviews,
    )
    return {
        "schema_version": runtime_review["output_schema_version"],
        "area_id": options.area_id,
        "statement_timeout_ms": timeout_ms,
        "reviews": results,
    }


def main(argv: list[str] | None = None) -> int:
    options = parse_args(argv)
    result = run_runtime_check(options)
    write_result_json(options.output_json, result)
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
