$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $root

$validator = '.\scripts\release_readiness_check.py'
if (-not (Test-Path -Path $validator -PathType Leaf)) {
    throw "required release-readiness artifact missing: scripts\release_readiness_check.py"
}

if ($env:PYTHON_BIN) {
    & $env:PYTHON_BIN $validator
} else {
    py -3.12 $validator
}

if ($LASTEXITCODE -ne 0) {
    throw "release readiness validation failed with exit code $LASTEXITCODE"
}

Write-Host 'release readiness check: ok'
