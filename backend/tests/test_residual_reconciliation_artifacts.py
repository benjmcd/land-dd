from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RESIDUAL_PATH = REPO_ROOT / "state" / "residual-reconciliation.md"

CURRENT_MAIN_SHA = "74af6f5a26594e80efed0fb4cfa9015e7e9e135d"
DEFERRED_PATHS = (
    "backend/tests/api/test_ui_readiness_overview.py",
    "backend/app/expansion_readiness.py",
    "backend/app/selected_geography_coverage.py",
    "backend/tests/api/test_ui_expansion_readiness.py",
    "backend/tests/api/test_ui_selected_geography_coverage.py",
    "backend/app/production_authority.py",
    "backend/tests/api/test_ui_production_authority.py",
    "backend/tests/api/test_ui_release_readiness.py",
    "backend/tests/test_local_deployment_artifacts.py",
    "config/local_deployment.yaml",
    "scripts/local_deployment_check.py",
    "scripts/run_local_deployment_check.ps1",
    "scripts/run_local_deployment_check.sh",
    "backend/app/dossier_readiness.py",
    "backend/tests/api/test_ui_dossier_readiness.py",
    "backend/app/product_correctness.py",
    "backend/tests/api/test_ui_product_correctness.py",
)


def test_residual_reconciliation_records_eqr_closeout_without_product_promotion() -> None:
    residual = RESIDUAL_PATH.read_text(encoding="utf-8")
    normalized = " ".join(residual.split())

    assert CURRENT_MAIN_SHA in residual
    assert "| `STILL_DIVERGENT` | 0 |" in residual
    assert "| `DEFER_STILL_BLOCKED` | 17 |" in residual
    assert "## EQ-R Closeout - 2026-06-23" in residual
    assert "The 17 deferred paths below remain candidate evidence only" in residual
    assert "No deferred file is promoted to `PASS`, live product authority" in residual
    assert "no-divergent shorthand must not be read as no residual deferred work" in normalized

    for path in DEFERRED_PATHS:
        assert f"| `DEFER_STILL_BLOCKED` | `??` | no | `{path}` |" in residual

    assert "STILL_DIVERGENT: none" not in residual
