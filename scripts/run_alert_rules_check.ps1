$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $root

$validator = '.\scripts\alert_rules_check.py'
if (-not (Test-Path -Path $validator -PathType Leaf)) {
    throw "required alerting artifact missing: scripts\alert_rules_check.py"
}

if ($env:PYTHON_BIN) {
    & $env:PYTHON_BIN $validator
} else {
    py -3.12 $validator
}

if ($LASTEXITCODE -ne 0) {
    throw "alert rules catalog validation failed with exit code $LASTEXITCODE"
}

Write-Host 'alert rules check: ok'
