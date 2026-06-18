$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = Resolve-Path (Join-Path $PSScriptRoot '..')
$validator = Join-Path $root 'scripts\performance_baseline_check.py'

if (-not (Test-Path -Path $validator -PathType Leaf)) {
    throw "performance baseline validator missing: $validator"
}

$python = if ($env:PYTHON_BIN) { $env:PYTHON_BIN } else { 'py' }

if ($python -eq 'py') {
    & $python -3.12 $validator
} else {
    & $python $validator
}

if ($LASTEXITCODE -ne 0) {
    throw "performance baseline check failed with exit code $LASTEXITCODE"
}

Write-Host 'performance baseline check: ok'
