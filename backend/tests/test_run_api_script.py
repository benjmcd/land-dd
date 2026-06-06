from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_windows_run_api_preserves_configured_object_store_root() -> None:
    script = (REPO_ROOT / "scripts" / "run_api.ps1").read_text(encoding="utf-8")

    assert "if ([string]::IsNullOrWhiteSpace($env:OBJECT_STORE_ROOT))" in script
    assert "$env:OBJECT_STORE_ROOT = Join-Path $root 'local_artifacts\\object_store'" in script
