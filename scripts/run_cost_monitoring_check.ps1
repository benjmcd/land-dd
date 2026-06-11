$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $root

$validator = '.\scripts\cost_monitoring_check.py'
if (-not (Test-Path -Path $validator -PathType Leaf)) {
    throw "required cost-monitoring artifact missing: scripts\cost_monitoring_check.py"
}

if ($env:PYTHON_BIN) {
    & $env:PYTHON_BIN $validator
} else {
    py -3.12 $validator
}

if ($LASTEXITCODE -ne 0) {
    throw "cost monitoring validation failed with exit code $LASTEXITCODE"
}

Write-Host 'cost monitoring check: ok'
