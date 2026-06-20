$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot

$validator = '.\scripts\bologna_preflight_check.py'

Push-Location $root
try {
    if (-not (Test-Path $validator)) {
        throw "required Bologna preflight artifact missing: scripts\bologna_preflight_check.py"
    }

    py -3.12 $validator
    if ($LASTEXITCODE -ne 0) {
        throw "Bologna preflight check failed with exit code $LASTEXITCODE"
    }

    Write-Host 'Bologna preflight check: ok'
} finally {
    Pop-Location
}
