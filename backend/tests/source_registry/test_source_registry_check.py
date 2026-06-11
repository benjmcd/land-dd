from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


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
