from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_windows_run_api_preserves_configured_object_store_root() -> None:
    script = (REPO_ROOT / "scripts" / "run_api.ps1").read_text(encoding="utf-8")

    assert "if ([string]::IsNullOrWhiteSpace($env:OBJECT_STORE_ROOT))" in script
    assert "$env:OBJECT_STORE_ROOT = Join-Path $root 'local_artifacts\\object_store'" in script


def test_run_api_scripts_map_storage_backend_to_runtime_services() -> None:
    powershell = (REPO_ROOT / "scripts" / "run_api.ps1").read_text(encoding="utf-8")
    posix = (REPO_ROOT / "scripts" / "run_api.sh").read_text(encoding="utf-8")

    assert "$useDbServices = if ($StorageBackend -eq 'postgres')" in powershell
    assert "$env:USE_DB_SERVICES = $useDbServices" in powershell
    assert "$previousUseDbServices = $env:USE_DB_SERVICES" in powershell
    assert "Remove-Item Env:USE_DB_SERVICES" in powershell

    assert 'if [[ "$STORAGE_BACKEND" == "postgres" ]]' in posix
    assert 'USE_DB_SERVICES="true"' in posix
    assert 'USE_DB_SERVICES="false"' in posix
    assert 'USE_DB_SERVICES="$USE_DB_SERVICES"' in posix
