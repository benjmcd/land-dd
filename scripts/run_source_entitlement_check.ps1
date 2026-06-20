$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$validator = '.\scripts\source_entitlement_check.py'

Push-Location $root
try {
    if (-not (Test-Path $validator)) {
        throw "required source-entitlement artifact missing: scripts\source_entitlement_check.py"
    }
    py -3.12 $validator
    if ($LASTEXITCODE -ne 0) {
        throw "source entitlement check failed with exit code $LASTEXITCODE"
    }
    Write-Host 'source entitlement check: ok'
} finally {
    Pop-Location
}
