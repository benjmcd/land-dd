$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $root

$validator = '.\scripts\access_control_check.py'
if (-not (Test-Path -Path $validator -PathType Leaf)) {
    throw "required access-control artifact missing: scripts\access_control_check.py"
}

if ($env:PYTHON_BIN) {
    & $env:PYTHON_BIN $validator
} else {
    py -3.12 $validator
}

if ($LASTEXITCODE -ne 0) {
    throw "access-control validation failed with exit code $LASTEXITCODE"
}

Write-Host 'access-control check: ok'
