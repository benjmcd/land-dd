$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$validator = '.\scripts\bologna_source_candidates_check.py'

Push-Location $root
try {
    if (-not (Test-Path $validator)) {
        throw "required Bologna source-candidates artifact missing: scripts\bologna_source_candidates_check.py"
    }
    py -3.12 $validator
    if ($LASTEXITCODE -ne 0) {
        throw "Bologna source candidates check failed with exit code $LASTEXITCODE"
    }
    Write-Host 'Bologna source candidates check: ok'
} finally {
    Pop-Location
}
