$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $root

$validator = '.\scripts\data_retention_check.py'
if (-not (Test-Path -Path $validator -PathType Leaf)) {
    throw "required data-retention artifact missing: scripts\data_retention_check.py"
}

if ($env:PYTHON_BIN) {
    & $env:PYTHON_BIN $validator
} else {
    py -3.12 $validator
}

if ($LASTEXITCODE -ne 0) {
    throw "data retention catalog validation failed with exit code $LASTEXITCODE"
}
