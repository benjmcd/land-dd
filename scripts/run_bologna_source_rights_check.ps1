$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$validator = '.\scripts\bologna_source_rights_check.py'

Push-Location $root
try {
    if (-not (Test-Path $validator)) {
        throw "required Bologna source-rights artifact missing: scripts\bologna_source_rights_check.py"
    }
    py -3.12 $validator
    if ($LASTEXITCODE -ne 0) {
        throw "Bologna source rights check failed with exit code $LASTEXITCODE"
    }
    Write-Host 'Bologna source rights check: ok'
} finally {
    Pop-Location
}
