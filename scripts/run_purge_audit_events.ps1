$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $root

$localArtifacts = Join-Path $root 'local_artifacts'
if (Test-Path -Path $localArtifacts -PathType Container) {
    $env:PATH = "$localArtifacts;$env:PATH"
}

function Get-PythonExecutable {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3.12 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)" 2>$null
        if ($LASTEXITCODE -eq 0) {
            return 'py -3.12'
        }
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        & python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)" 2>$null
        if ($LASTEXITCODE -eq 0) {
            return 'python'
        }
    }
    throw 'Python 3.12+ is required.'
}

$pythonExecutable = Get-PythonExecutable

Write-Host "purge_audit_events: running dry-run (validate only, no deletes)"

if ($pythonExecutable -eq 'py -3.12') {
    & py -3.12 scripts/purge_audit_events.py
} else {
    & python scripts/purge_audit_events.py
}

if ($LASTEXITCODE -ne 0) {
    throw "purge_audit_events dry-run failed with exit code $LASTEXITCODE"
}

Write-Host "purge_audit_events: dry-run complete (PASS)"
Write-Host ""
Write-Host "To apply deletions (manual operator action), run:"
Write-Host "  py -3.12 scripts/purge_audit_events.py --apply"
Write-Host "  py -3.12 scripts/purge_audit_events.py --apply --retention-days 90"
