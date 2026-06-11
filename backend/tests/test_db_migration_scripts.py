from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_db_migration_scripts_can_fallback_to_docker_psql() -> None:
    for script_name in ("db_apply_migrations.ps1", "db_apply_migrations.sh"):
        script = (REPO_ROOT / "scripts" / script_name).read_text(encoding="utf-8")
        assert "postgis/postgis:16-3.4" in script
        assert "host.docker.internal" in script
        assert "psql not found and Docker is unavailable" in script
        assert "ON_ERROR_STOP=1" in script
        assert "local_artifacts" in script
    posix_script = (REPO_ROOT / "scripts" / "db_apply_migrations.sh").read_text(
        encoding="utf-8"
    )
    assert "${PYTHON_BIN:-python}" in posix_script
