from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "registers" / "data_source_registry.csv"
REVIEW_DIR = ROOT / "registers" / "license-reviews"
SQL_SEED_PATH = ROOT / "db" / "seeds" / "002_seed_source_registry.sql"

RIGHTS_COLUMNS = (
    "License Status",
    "Commercial Use Status",
    "Redistribution Status",
    "Cache Allowed",
    "Export Allowed",
    "AI Use Status",
    "Raw Data Allowed",
)
RIGHTS_VALUES = {
    "unknown",
    "approved",
    "approved-with-restrictions",
    "restricted",
    "blocked",
}
ATTRIBUTION_VALUES = {"unknown", "yes", "no", "restricted"}
REVIEW_STATUSES = {
    "pending",
    "approved",
    "approved-with-restrictions",
    "blocked",
    "superseded",
}


def main() -> None:
    rows = _load_rows()
    errors: list[str] = []
    seen_ids: set[str] = set()

    for line_number, row in enumerate(rows, start=2):
        source_id = row["Source ID"].strip()
        if source_id in seen_ids:
            errors.append(f"{_location(line_number)} duplicate Source ID {source_id}")
        seen_ids.add(source_id)

        for column in RIGHTS_COLUMNS:
            value = row[column].strip()
            if value not in RIGHTS_VALUES:
                errors.append(
                    f"{_location(line_number)} {column}={value!r} is not an allowed value"
                )

        attribution = row["Attribution Required"].strip()
        if attribution not in ATTRIBUTION_VALUES:
            errors.append(
                f"{_location(line_number)} Attribution Required={attribution!r} "
                "is not an allowed value"
            )

        review_status = row["Review Status"].strip()
        if review_status not in REVIEW_STATUSES:
            errors.append(
                f"{_location(line_number)} Review Status={review_status!r} "
                "is not an allowed value"
            )

        if review_status.startswith("approved"):
            _check_approved_row(row, line_number, errors)

    _check_sql_seed_rows(rows, errors)

    if errors:
        raise SystemExit("source registry check failed:\n" + "\n".join(errors))

    print(f"source registry check: ok ({len(rows)} rows)")


def _load_rows() -> list[dict[str, str]]:
    with REGISTRY_PATH.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _check_approved_row(row: dict[str, str], line_number: int, errors: list[str]) -> None:
    source_id = row["Source ID"].strip()
    source_type = row["Source Type"].strip()

    for column in RIGHTS_COLUMNS:
        if row[column].strip() in {"unknown", "blocked"}:
            errors.append(
                f"{_location(line_number)} approved source {source_id} has "
                f"{column}={row[column]!r}"
            )

    if row["Attribution Required"].strip() == "unknown":
        errors.append(
            f"{_location(line_number)} approved source {source_id} has unknown attribution"
        )
    if not row["Last Checked At"].strip():
        errors.append(
            f"{_location(line_number)} approved source {source_id} has no Last Checked At"
        )
    if row["Review Owner"].strip() in {"", "unassigned"}:
        errors.append(f"{_location(line_number)} approved source {source_id} has no Review Owner")

    if source_type != "Internal fixture" and not _has_review_file(source_id):
        errors.append(
            f"{_location(line_number)} approved source {source_id} has no "
            f"{REVIEW_DIR.relative_to(ROOT)}/{source_id.lower()}-*.md review file"
        )


def _check_sql_seed_rows(rows: list[dict[str, str]], errors: list[str]) -> None:
    sql_rows = _load_sql_seed_rows()
    for row in rows:
        source_id = row["Source ID"].strip()
        if not row["Review Status"].strip().startswith("approved"):
            continue
        if row["Source Type"].strip() == "Internal fixture":
            continue
        if source_id not in sql_rows:
            errors.append(
                f"{SQL_SEED_PATH.relative_to(ROOT)} missing approved source {source_id}"
            )
            continue

        sql_row = sql_rows[source_id]
        metadata = sql_row["metadata"]
        _compare_sql_value(source_id, "Commercial Use Status", row, sql_row, errors)
        _compare_sql_value(source_id, "Cache Allowed", row, sql_row, errors)
        _compare_sql_value(source_id, "Export Allowed", row, sql_row, errors)
        _compare_sql_value(source_id, "AI Use Status", row, sql_row, errors)
        _compare_sql_value(source_id, "Raw Data Allowed", row, sql_row, errors)

        for column, metadata_key in (
            ("License Status", "license_status"),
            ("Redistribution Status", "redistribution_status"),
            ("Attribution Required", "attribution_required_status"),
            ("Freshness Class", "freshness_class"),
            ("Last Checked At", "last_checked_at"),
            ("Review Owner", "review_owner"),
            ("Review Status", "review_status"),
        ):
            expected = row[column].strip()
            actual = str(metadata.get(metadata_key, "")).strip()
            if expected != actual:
                errors.append(
                    f"{SQL_SEED_PATH.relative_to(ROOT)} {source_id} metadata "
                    f"{metadata_key}={actual!r}; expected {expected!r}"
                )


def _compare_sql_value(
    source_id: str,
    column: str,
    row: dict[str, str],
    sql_row: dict[str, object],
    errors: list[str],
) -> None:
    key = _sql_key_for(column)
    expected = row[column].strip()
    actual = str(sql_row[key]).strip()
    if expected != actual:
        errors.append(
            f"{SQL_SEED_PATH.relative_to(ROOT)} {source_id} {key}={actual!r}; "
            f"expected {expected!r}"
        )


def _sql_key_for(column: str) -> str:
    return {
        "Commercial Use Status": "commercial_use_status",
        "Cache Allowed": "cache_allowed",
        "Export Allowed": "export_allowed",
        "AI Use Status": "ai_use_allowed",
        "Raw Data Allowed": "raw_data_allowed",
    }[column]


def _load_sql_seed_rows() -> dict[str, dict[str, object]]:
    rows: dict[str, dict[str, object]] = {}
    for line in SQL_SEED_PATH.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("('"):
            continue
        parsed = _parse_sql_seed_values(stripped)
        metadata = json.loads(str(parsed[12]).removesuffix("::jsonb"))
        source_id = str(metadata.get("source_registry_id", ""))
        if source_id:
            rows[source_id] = {
                "commercial_use_status": parsed[6],
                "ai_use_allowed": parsed[8],
                "cache_allowed": parsed[9],
                "export_allowed": parsed[10],
                "raw_data_allowed": parsed[11],
                "metadata": metadata,
            }
    return rows


def _parse_sql_seed_values(line: str) -> list[str]:
    values = line.removeprefix("(").removesuffix(",").removesuffix(")")
    return next(csv.reader([values], quotechar="'", skipinitialspace=True))


def _has_review_file(source_id: str) -> bool:
    return REVIEW_DIR.exists() and any(REVIEW_DIR.glob(f"{source_id.lower()}-*.md"))


def _location(line_number: int) -> str:
    return f"{REGISTRY_PATH.relative_to(ROOT)}:{line_number}"


if __name__ == "__main__":
    main()
