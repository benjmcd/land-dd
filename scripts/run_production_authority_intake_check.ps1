$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    py -3.12 .\scripts\production_authority_intake_check.py
    Write-Host "production authority intake check: ok"
}
finally {
    Pop-Location
}
