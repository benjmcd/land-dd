$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    py -3.12 .\scripts\bologna_source_authority_intake_check.py
    Write-Host "Bologna source authority intake check: ok"
}
finally {
    Pop-Location
}
