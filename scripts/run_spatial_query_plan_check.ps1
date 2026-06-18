$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = Resolve-Path (Join-Path $PSScriptRoot '..')
$validator = Join-Path $root 'scripts\spatial_query_plan_check.py'

if (-not (Test-Path -Path $validator -PathType Leaf)) {
    throw "spatial query-plan validator missing: $validator"
}

$python = if ($env:PYTHON_BIN) { $env:PYTHON_BIN } else { 'py' }

if ($python -eq 'py') {
    & $python -3.12 $validator
} else {
    & $python $validator
}

if ($LASTEXITCODE -ne 0) {
    throw "spatial query-plan check failed with exit code $LASTEXITCODE"
}

Write-Host 'spatial query plan check: ok'
