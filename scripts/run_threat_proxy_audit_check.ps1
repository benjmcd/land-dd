$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $root

$validator = '.\scripts\threat_proxy_audit_check.py'
if (-not (Test-Path -Path $validator -PathType Leaf)) {
    throw "required threat/proxy artifact missing: scripts\threat_proxy_audit_check.py"
}

if ($env:PYTHON_BIN) {
    & $env:PYTHON_BIN $validator
} else {
    py -3.12 $validator
}

if ($LASTEXITCODE -ne 0) {
    throw "threat/proxy audit validation failed with exit code $LASTEXITCODE"
}

Write-Host 'threat/proxy audit check: ok'
