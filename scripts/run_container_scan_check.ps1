$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $root

$validator = '.\scripts\container_scan_check.py'
if (-not (Test-Path -Path $validator -PathType Leaf)) {
    throw "required container-scan artifact missing: scripts\container_scan_check.py"
}

if ($env:PYTHON_BIN) {
    & $env:PYTHON_BIN $validator
} else {
    py -3.12 $validator
}

if ($LASTEXITCODE -ne 0) {
    throw "container image scan configuration validation failed with exit code $LASTEXITCODE"
}

Write-Host 'container image scan check: ok'
