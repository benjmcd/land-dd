$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $root

$validator = '.\scripts\provenance_check.py'
if (-not (Test-Path -Path $validator -PathType Leaf)) {
    throw "required dependency provenance artifact missing: scripts\provenance_check.py"
}

if ($env:PYTHON_BIN) {
    & $env:PYTHON_BIN $validator
} else {
    py -3.12 $validator
}

if ($LASTEXITCODE -ne 0) {
    throw "dependency provenance artifact validation failed with exit code $LASTEXITCODE"
}

Write-Host 'dependency provenance check: ok'
