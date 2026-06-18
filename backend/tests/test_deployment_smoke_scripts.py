from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_deployment_smoke_scripts_exist_for_windows_and_posix() -> None:
    assert (REPO_ROOT / "scripts" / "run_deployment_smoke.ps1").is_file()
    assert (REPO_ROOT / "scripts" / "run_deployment_smoke.sh").is_file()


def test_deployment_smoke_scripts_cover_runtime_contract() -> None:
    powershell = (REPO_ROOT / "scripts" / "run_deployment_smoke.ps1").read_text(
        encoding="utf-8",
    )
    posix = (REPO_ROOT / "scripts" / "run_deployment_smoke.sh").read_text(
        encoding="utf-8",
    )

    for script in (powershell, posix):
        assert "land-diligence-smoke" in script
        assert "COMPOSE_USE_DB_SERVICES" in script
        assert "/health" in script
        assert "/version" in script
        assert "/metrics" in script
        assert "/operations/queue-health" in script
        assert "oldest_running_age_seconds" in script
        assert "oldest_running_job_id" in script
        assert "stale_running" in script
        assert "stale_running_threshold_seconds" in script
        assert "/operations/recovery-preview" in script
        assert "operations_recovery_preview_v1" in script
        assert "failed_count" in script
        assert "stale_running_count" in script
        assert "queued_count" in script
        assert "failed_candidates_truncated" in script
        assert "stale_running_candidates_truncated" in script
        assert "candidates" in script
        assert "/areas" in script
        assert "/report-runs" in script
        assert "deployment smoke: ok" in script

    assert "recoveryPreview.stale_running_threshold_seconds" in powershell
    assert 'json_field "$recovery_preview" stale_running_threshold_seconds' in posix


def test_deployment_smoke_scripts_feed_sql_through_stable_psql_file_modes() -> None:
    powershell = (REPO_ROOT / "scripts" / "run_deployment_smoke.ps1").read_text(
        encoding="utf-8",
    )
    posix = (REPO_ROOT / "scripts" / "run_deployment_smoke.sh").read_text(
        encoding="utf-8",
    )

    assert "docker compose --project-name $projectName cp" in powershell
    assert "db:/tmp/deployment-smoke.sql" in powershell
    assert (
        "psql -U land -d land_diligence -v ON_ERROR_STOP=1 "
        "-f /tmp/deployment-smoke.sql"
    ) in powershell
    assert "Get-Content -Raw -Path $Path |" not in powershell
    assert "psql -U land -d land_diligence -v ON_ERROR_STOP=1 -f -" in posix
    assert 'ON_ERROR_STOP=1 < "$file"' not in posix


def test_deployment_smoke_scripts_wait_for_stable_postgres_startup() -> None:
    powershell = (REPO_ROOT / "scripts" / "run_deployment_smoke.ps1").read_text(
        encoding="utf-8",
    )
    posix = (REPO_ROOT / "scripts" / "run_deployment_smoke.sh").read_text(
        encoding="utf-8",
    )

    for script in (powershell, posix):
        assert "pg_postmaster_start_time()" in script
        assert "db start time changed while waiting for deployment smoke" in script
