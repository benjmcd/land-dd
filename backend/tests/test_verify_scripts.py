from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _powershell() -> str | None:
    return shutil.which("pwsh") or shutil.which("powershell")


def _ps_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _extract_between(text: str, start: str, end: str) -> str:
    start_index = text.index(start)
    end_index = text.index(end, start_index)
    return text[start_index:end_index]


def _read_log(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-16"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def test_verify_scripts_buffer_backend_pytest_output_to_log() -> None:
    powershell = (REPO_ROOT / "scripts" / "verify.ps1").read_text(encoding="utf-8")
    posix = (REPO_ROOT / "scripts" / "verify.sh").read_text(encoding="utf-8")

    assert "New-VerifyLogPath" in powershell
    assert "Invoke-PythonCommandWithLog" in powershell
    assert "backend-pytest.log" in powershell
    assert "*> $logPath" in powershell
    assert "Remove-Item -Path $logPath" not in powershell
    assert "exit $backendTestsExitCode" in powershell
    assert "$previousPythonPath" in powershell
    assert "make_log_path" in posix
    assert "run_python_with_log" in posix
    assert "backend-pytest.log" in posix
    assert '> "$log_path" 2>&1' in posix
    assert 'rm -f "$log_path"' not in posix


@pytest.mark.skipif(_powershell() is None, reason="PowerShell is not available")
def test_powershell_logged_python_command_preserves_failure_evidence(
    tmp_path: Path,
) -> None:
    powershell = (REPO_ROOT / "scripts" / "verify.ps1").read_text(encoding="utf-8")
    helpers = _extract_between(powershell, "function New-VerifyLogPath", "\nSelect-Python")

    artifacts = tmp_path / "local_artifacts"
    artifacts.mkdir()
    existing_log = artifacts / "backend-pytest.log"
    existing_log.write_text("previous", encoding="utf-8")

    python_code = (
        "import sys; print('probe-out'); "
        "print('probe-err', file=sys.stderr); raise SystemExit(7)"
    )
    probe_script = tmp_path / "probe.ps1"
    probe_script.write_text(
        "\n".join(
            [
                "$ErrorActionPreference = 'Stop'",
                "Set-StrictMode -Version Latest",
                f"$root = {_ps_quote(str(tmp_path))}",
                f"$script:PythonExecutable = {_ps_quote(sys.executable)}",
                helpers,
                "$exitCode = Invoke-PythonCommandWithLog "
                "-Label 'probe' "
                f"-Arguments @('-c', {_ps_quote(python_code)}) "
                "-LogName 'backend-pytest.log'",
                'Write-Host "returned: $exitCode"',
                "exit $exitCode",
            ],
        ),
        encoding="utf-8",
    )

    command = [_powershell() or "", "-NoProfile"]
    if os.name == "nt":
        command.extend(["-ExecutionPolicy", "Bypass"])
    command.extend(["-File", str(probe_script)])
    result = subprocess.run(command, capture_output=True, text=True, check=False)

    assert result.returncode == 7
    assert "probe-out" in result.stdout
    assert "probe-err" in result.stdout
    assert "returned: 7" in result.stdout
    assert existing_log.read_text(encoding="utf-8") == "previous"
    rotated_logs = list(artifacts.glob("backend-pytest-*.log"))
    assert len(rotated_logs) == 1
    rotated_content = _read_log(rotated_logs[0])
    assert "probe-out" in rotated_content
    assert "probe-err" in rotated_content


@pytest.mark.skipif(
    os.name == "nt" or shutil.which("bash") is None,
    reason="POSIX shell behavior is covered on non-Windows runners",
)
def test_posix_logged_python_command_preserves_failure_evidence(tmp_path: Path) -> None:
    posix = (REPO_ROOT / "scripts" / "verify.sh").read_text(encoding="utf-8")
    helpers = _extract_between(posix, "make_log_path() {", '\necho "== agent context =="')

    artifacts = tmp_path / "local_artifacts"
    artifacts.mkdir()
    existing_log = artifacts / "backend-pytest.log"
    existing_log.write_text("previous", encoding="utf-8")

    python_code = (
        "import sys; print('probe-out'); "
        "print('probe-err', file=sys.stderr); raise SystemExit(9)"
    )
    probe_script = tmp_path / "probe.sh"
    probe_script.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                f"ROOT_DIR={shlex.quote(str(tmp_path))}",
                f"PYTHON_BIN={shlex.quote(sys.executable)}",
                helpers,
                "run_python_with_log "
                '"probe" "backend-pytest.log" '
                f"-c {shlex.quote(python_code)}",
                "status=$?",
                'echo "returned: $status"',
                'exit "$status"',
            ],
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        ["bash", str(probe_script)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 9
    assert "probe-out" in result.stdout
    assert "probe-err" in result.stdout
    assert "returned: 9" in result.stdout
    assert existing_log.read_text(encoding="utf-8") == "previous"
    rotated_logs = list(artifacts.glob("backend-pytest-*.log"))
    assert len(rotated_logs) == 1
    rotated_content = rotated_logs[0].read_text(encoding="utf-8")
    assert "probe-out" in rotated_content
    assert "probe-err" in rotated_content
