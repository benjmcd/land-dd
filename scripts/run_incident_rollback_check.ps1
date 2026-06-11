$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $root

$validator = '.\scripts\incident_rollback_check.py'
if (-not (Test-Path -Path $validator -PathType Leaf)) {
    throw "required incident/rollback artifact missing: scripts\incident_rollback_check.py"
}

if ($env:PYTHON_BIN) {
    & $env:PYTHON_BIN $validator
} else {
    py -3.12 $validator
}

if ($LASTEXITCODE -ne 0) {
    throw "incident/rollback validation failed with exit code $LASTEXITCODE"
}
