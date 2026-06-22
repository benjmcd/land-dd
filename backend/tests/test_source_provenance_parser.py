"""Tests for source_provenance.py parser hardening (SP-1).

SP-1: KeyError / ValidationError from bad CSV rows must surface as
SourceProvenanceError (fail-closed 503) rather than an unhandled 500.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
import yaml

from app.source_provenance import SourceProvenanceError, parse_source_provenance

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = REPO_ROOT / "config" / "private_mvp_beta_readiness.yaml"
REGISTRY_PATH = REPO_ROOT / "registers" / "data_source_registry.csv"


def _load_catalog() -> dict[str, Any]:
    return yaml.safe_load(CATALOG_PATH.read_text(encoding="utf-8"))


def _load_registry_rows() -> list[dict[str, str]]:
    import csv
    with REGISTRY_PATH.open(newline="", encoding="utf-8") as fh:
        return [dict(row) for row in csv.DictReader(fh)]


# ---------------------------------------------------------------------------
# Happy-path: real catalog + registry parse without error
# ---------------------------------------------------------------------------


def test_source_provenance_parse_happy_path() -> None:
    catalog = _load_catalog()
    rows = _load_registry_rows()
    result = parse_source_provenance(catalog, rows, root=REPO_ROOT)
    assert result.schema_version == "private_mvp_beta_readiness_v1"


# ---------------------------------------------------------------------------
# SP-1: row conversion errors wrap as SourceProvenanceError
# ---------------------------------------------------------------------------


def test_sp1_keyerror_in_row_raises_source_provenance_error() -> None:
    """A KeyError from a dropped CSV column in _row_to_source must become SourceProvenanceError."""
    catalog = _load_catalog()
    rows = _load_registry_rows()
    # Inject a Must-priority row that is missing the required 'Domain' key
    broken_row: dict[str, str] = {
        "Source ID": "DS-TEST-BROKEN",
        "MVP Priority": "Must",
        "Name": "Broken Source",
        # 'Domain' intentionally omitted — _row_to_source does row["Domain"]
        "License Status": "open",
        "Commercial Use Status": "allowed",
        "Redistribution Status": "allowed",
        "Cache Allowed": "yes",
        "Export Allowed": "yes",
        "AI Use Status": "allowed",
        "Raw Data Allowed": "yes",
        "Freshness Class": "static",
        "Review Status": "reviewed",
    }
    rows_with_broken = [broken_row] + rows
    with pytest.raises(SourceProvenanceError, match="registry"):
        parse_source_provenance(catalog, rows_with_broken, root=REPO_ROOT)


def test_sp1_build_readiness_records_error_raises_source_provenance_error() -> None:
    """Errors raised inside build_readiness_records must become SourceProvenanceError."""
    catalog = _load_catalog()
    rows = _load_registry_rows()

    def _exploding_build(*args: Any, **kwargs: Any) -> Any:
        raise ValueError("simulated build_readiness_records failure")

    with patch(
        "app.source_provenance.build_readiness_records",
        side_effect=_exploding_build,
    ):
        with pytest.raises(SourceProvenanceError, match="registry"):
            parse_source_provenance(catalog, rows, root=REPO_ROOT)


def test_sp1_type_error_in_build_raises_source_provenance_error() -> None:
    """A TypeError raised during readiness-record build must become SourceProvenanceError.

    Covers the TypeError branch of SP-1's except tuple deterministically (a real
    malformed-row value is coerced/validated unpredictably by Pydantic, so mock the
    build to raise the exact exception type under test).
    """
    catalog = _load_catalog()
    rows = _load_registry_rows()

    def _exploding_build(*args: Any, **kwargs: Any) -> Any:
        raise TypeError("simulated row-conversion type error")

    with patch(
        "app.source_provenance.build_readiness_records",
        side_effect=_exploding_build,
    ):
        with pytest.raises(SourceProvenanceError, match="registry"):
            parse_source_provenance(catalog, rows, root=REPO_ROOT)
