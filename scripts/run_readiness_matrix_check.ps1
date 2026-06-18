$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $root

$validator = '.\scripts\readiness_matrix_check.py'
if (-not (Test-Path -Path $validator -PathType Leaf)) {
    throw "required readiness-matrix artifact missing: scripts\readiness_matrix_check.py"
}

if ($env:PYTHON_BIN) {
    & $env:PYTHON_BIN $validator
} else {
    py -3.12 $validator
}

if ($LASTEXITCODE -ne 0) {
    throw "readiness matrix validation failed with exit code $LASTEXITCODE"
}

Write-Host 'readiness matrix check: ok'
