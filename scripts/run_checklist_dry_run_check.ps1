$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $root

$validator = '.\scripts\checklist_dry_run_check.py'
if (-not (Test-Path -Path $validator -PathType Leaf)) {
    throw "required checklist dry-run artifact missing: scripts\checklist_dry_run_check.py"
}

if ($env:PYTHON_BIN) {
    & $env:PYTHON_BIN $validator
} else {
    py -3.12 $validator
}

if ($LASTEXITCODE -ne 0) {
    throw "checklist dry-run validation failed with exit code $LASTEXITCODE"
}

Write-Host 'checklist dry-run check: ok'
