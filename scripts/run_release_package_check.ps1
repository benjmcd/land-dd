$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $root

$validator = '.\scripts\release_package_check.py'
if (-not (Test-Path -Path $validator -PathType Leaf)) {
    throw "required release-package artifact missing: scripts\release_package_check.py"
}

if ($env:PYTHON_BIN) {
    & $env:PYTHON_BIN $validator
} else {
    py -3.12 $validator
}

if ($LASTEXITCODE -ne 0) {
    throw "release package validation failed with exit code $LASTEXITCODE"
}

Write-Host 'release package check: ok'
