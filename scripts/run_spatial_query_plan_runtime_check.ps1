$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $root
$validator = Join-Path $root 'scripts\spatial_query_plan_runtime_check.py'

if (-not (Test-Path -Path $validator -PathType Leaf)) {
    throw "spatial query-plan runtime validator missing: $validator"
}

$python = if ($env:PYTHON_BIN) { $env:PYTHON_BIN } else { 'py' }

if ($python -eq 'py') {
    & $python -3.12 $validator @args
} else {
    & $python $validator @args
}

if ($LASTEXITCODE -ne 0) {
    throw "spatial query-plan runtime check failed with exit code $LASTEXITCODE"
}
