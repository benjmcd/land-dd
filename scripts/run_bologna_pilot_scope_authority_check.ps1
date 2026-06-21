$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    py -3.12 .\scripts\bologna_pilot_scope_authority_check.py
    Write-Host "Bologna pilot scope authority check: ok"
}
finally {
    Pop-Location
}
