from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
REGISTRY_PATH = REPO_ROOT / "registers" / "data_source_registry.csv"


def _registry_row(source_id: str) -> dict[str, str]:
    with REGISTRY_PATH.open(newline="", encoding="utf-8") as csv_file:
        for row in csv.DictReader(csv_file):
            if row["Source ID"] == source_id:
                return dict(row)
    raise AssertionError(f"{source_id} missing from source registry")


def test_source_registry_check_passes_against_current_registry_and_sql_seed() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/check_source_registry.py"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "source registry check: ok (25 rows)" in result.stdout


def test_workspace_validation_runs_source_registry_check() -> None:
    for script_name in ("validate_workspace.ps1", "validate_workspace.sh"):
        script = (REPO_ROOT / "scripts" / script_name).read_text(encoding="utf-8")

        assert "scripts/check_source_registry.py" in script


def test_workspace_validation_runs_private_mvp_readiness_check() -> None:
    for script_name in ("validate_workspace.ps1", "validate_workspace.sh"):
        script = (REPO_ROOT / "scripts" / script_name).read_text(encoding="utf-8")

        assert "scripts/private_mvp_readiness_check.py" in script


def test_ds012_review_records_blocked_registry_decision() -> None:
    review = (REPO_ROOT / "docs" / "source-reviews" / "ds-012.md").read_text(
        encoding="utf-8",
    )

    assert "License/terms status recorded in source registry | complete" in review
    assert "Decision recorded in source registry? yes" in review
    assert "Decision recorded in source registry? pending" not in review


def test_ds010_registry_and_review_track_selected_county_connector_status() -> None:
    row = _registry_row("DS-010")
    caveats = row["Caveats"]
    review = (REPO_ROOT / "docs" / "source-reviews" / "ds-010.md").read_text(
        encoding="utf-8",
    )

    assert row["Last Checked At"] == "2026-06-12"
    assert (
        "Buncombe/Chatham/Brunswick NC selected-county connectors complete"
        in caveats
    )
    assert "durable live-job support not claimed" in caveats
    assert "Buncombe and Brunswick connector implementation pending" not in caveats
    assert (
        "Buncombe, Chatham, and Brunswick selected-county parcel connectors complete"
        in review
    )
    assert "connectors not yet implemented" not in review


def test_ds023_registry_and_review_track_recorded_fixture_scope() -> None:
    row = _registry_row("DS-023")
    caveats = row["Caveats"]
    review = (REPO_ROOT / "docs" / "source-reviews" / "ds-023.md").read_text(
        encoding="utf-8",
    )

    assert row["Last Checked At"] == "2026-06-12"
    assert "Chatham/Brunswick recorded-fixture zoning only" in caveats
    assert "Buncombe zoning NOT_EVALUATED" in caveats
    assert "private-MVP scope: Chatham County NC" not in caveats
    assert "DS-023 is now connector-ready for Chatham and Brunswick" in review
    assert "sources=8 ready=7 blocked=1" in review
    assert "sources=8 ready=6 blocked=2" not in review
    assert "DS-011 and DS-017 remain blocked" not in review
