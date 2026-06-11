$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $root

$validator = '.\scripts\private_mvp_readiness_check.py'
if (-not (Test-Path -Path $validator -PathType Leaf)) {
    throw "required private MVP readiness artifact missing: scripts\private_mvp_readiness_check.py"
}

if ($env:PYTHON_BIN) {
    & $env:PYTHON_BIN $validator
} else {
    py -3.12 $validator
}

if ($LASTEXITCODE -ne 0) {
    throw "private MVP readiness validation failed with exit code $LASTEXITCODE"
}

Write-Host 'private MVP readiness check: ok'
