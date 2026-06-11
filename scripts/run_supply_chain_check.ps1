$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $root

$validator = '.\scripts\supply_chain_check.py'
if (-not (Test-Path -Path $validator -PathType Leaf)) {
    throw "required supply-chain artifact missing: scripts\supply_chain_check.py"
}

if ($env:PYTHON_BIN) {
    & $env:PYTHON_BIN $validator
} else {
    py -3.12 $validator
}

if ($LASTEXITCODE -ne 0) {
    throw "supply-chain configuration validation failed with exit code $LASTEXITCODE"
}

Write-Host 'supply-chain check: ok'
