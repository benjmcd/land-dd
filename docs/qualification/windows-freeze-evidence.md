# Windows Freeze Evidence

Status: target-freeze evidence only. This note does not claim W gate `PASS`, P0 `PASS`,
hosted readiness, production deployment readiness, or report/runtime proof.

Owner disposition:
- owner=benjmcd
- authority=owner directive 2026-06-22
- authority_file=state/owner-decisions.md
- rationale=conservative defaults matching operational reality
- reversal=requires a new owner decision + full requalification

## W-003 Long Path Boundary

Frozen target values:
- `windows_native.path_with_spaces_required: true`
- `windows_native.unicode_path_required: true`
- `windows_native.long_path_policy: ENABLED`

Observed local smoke on 2026-06-22 in `worktrees/qfreeze1`:
- Probe path:
  `local_artifacts/w003 path with spaces/<folder containing U+00E9>/probe file.txt`
- Probe write/read result: `ok`
- Probe existence check: `True`
- `git config --get core.longpaths`: `true`
- Windows `LongPathsEnabled`: `1`

The probe directory is under gitignored `local_artifacts/` and is not a source fixture,
seed, corpus, report artifact, or qualification result.

## W-011 Version Matrix And Upgrade Policy

Frozen target values:
- `supported_windows_versions: ["Windows 11 (>=22H2)"]`
- `supported_powershell_versions: ["5.1", "7.x"]`
- `supported_python_versions: ["3.12"]`
- `supported_docker_desktop_versions: ["4.x"]`

Observed local environment on 2026-06-22:
- Windows: `Microsoft Windows 11 Home`, version `10.0.26200`, build `26200`
- PowerShell: `5.1.26100.8655`
- Python: `Python 3.12.10`
- Docker Desktop: `4.61.0` from Windows uninstall metadata and
  `C:\Program Files\Docker\Docker\Docker Desktop.exe` product version `4.61.0.219004`
- Docker CLI/Engine: `Docker version 29.2.1, build a5c7197`

Upgrade policy: changes to supported Windows, PowerShell, Python, Docker Desktop, or
long-path behavior require a new owner decision plus full requalification before the
qualification target may change. Future version evidence can support a new freeze, but
it cannot silently expand the current target matrix.
