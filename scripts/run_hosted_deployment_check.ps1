$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $root

$validator = '.\scripts\hosted_deployment_check.py'
if (-not (Test-Path -Path $validator -PathType Leaf)) {
    throw "required hosted-deployment artifact missing: scripts\hosted_deployment_check.py"
}

if ($env:PYTHON_BIN) {
    & $env:PYTHON_BIN $validator
} else {
    py -3.12 $validator
}

if ($LASTEXITCODE -ne 0) {
    throw "hosted deployment validation failed with exit code $LASTEXITCODE"
}

Write-Host 'hosted deployment check: ok'
