from __future__ import annotations

import argparse
import json
from collections.abc import Callable, Mapping, Sequence
from datetime import date
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]

RowFormatter = Callable[[dict[str, Any]], str]
ExtraLineFormatter = Callable[[Mapping[str, Any]], str]


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


def require_non_empty_list(value: Any, message: str) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise SystemExit(message)
    return value


def require_text(value: Any, message: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SystemExit(message)
    return value.strip()


def require_iso_date(value: Any, message: str) -> str:
    text = require_text(value, message)
    try:
        date.fromisoformat(text)
    except ValueError as exc:
        raise SystemExit(message) from exc
    return text


def normalize_path(path_text: str) -> str:
    return path_text.replace("\\", "/")


def repo_path(path_text: str) -> Path:
    return ROOT / normalize_path(path_text)


def require_existing(path_text: str, message_prefix: str) -> None:
    normalized = normalize_path(path_text)
    require(repo_path(normalized).exists(), f"{message_prefix}: {normalized}")


def read_text(path_text: str) -> str:
    return repo_path(path_text).read_text(encoding="utf-8")


def load_yaml(path_text: str, *, reader: Callable[[str], str] | None = None) -> dict[str, Any]:
    read = reader or read_text
    return require_mapping(yaml.safe_load(read(path_text)), f"{path_text} must be a mapping")


def list_set(value: Any, message: str, *, allow_empty: bool = False) -> set[str]:
    items = require_list(value, message)
    if not allow_empty and not items:
        raise SystemExit(message)
    return {str(item) for item in items}


def build_summary(schema_version: str, fields: Mapping[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "schema_version": schema_version,
        "ok": True,
    }
    summary.update(fields)
    return summary


def format_summary(
    title: str,
    summary: Mapping[str, Any],
    fields: Sequence[tuple[str, str]],
    *,
    row_groups: Sequence[tuple[str, str, RowFormatter]] = (),
    fields_after_rows: Sequence[tuple[str, str]] = (),
    extra_lines_after_rows: Sequence[ExtraLineFormatter] = (),
    list_fields: Sequence[tuple[str, str]] = (),
    footer: str,
) -> str:
    lines = [title]
    for label, key in fields:
        lines.append(f"{label}: {summary.get(key)}")
    for key, prefix, row_formatter in row_groups:
        for raw_row in require_list(summary.get(key), f"{key} missing"):
            row = require_mapping(raw_row, f"{key} row must be a mapping")
            lines.append(f"{prefix} {row_formatter(row)}")
    for label, key in fields_after_rows:
        lines.append(f"{label}: {summary.get(key)}")
    for extra_line in extra_lines_after_rows:
        lines.append(extra_line(summary))
    for label, key in list_fields:
        lines.append(f"{label}: " + ", ".join(str(item) for item in summary.get(key, [])))
    lines.append(footer)
    return "\n".join(lines)


def row_summary(id_key: str, fields: Sequence[tuple[str, str]]) -> RowFormatter:
    def format_row(row: dict[str, Any]) -> str:
        return f"{row.get(id_key)}: " + " ".join(
            f"{label}={row.get(key)}" for label, key in fields
        )

    return format_row


def run_reporting_cli(
    *,
    description: str,
    ok_message: str,
    validate: Callable[[], Any],
    summary_builder: Callable[[Any], dict[str, Any]],
    summary_formatter: Callable[[dict[str, Any]], str],
    argv: list[str] | None = None,
) -> int:
    parser = argparse.ArgumentParser(description=description)
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument("--json", action="store_true", dest="json_output")
    output_group.add_argument("--summary", action="store_true", dest="summary_output")
    args = parser.parse_args([] if argv is None else argv)
    payload = validate()
    if args.json_output:
        print(json.dumps(summary_builder(payload), indent=2, sort_keys=True))
    elif args.summary_output:
        print(summary_formatter(summary_builder(payload)))
    else:
        print(ok_message)
    return 0
