$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    py -3.12 scripts\bologna_odp1_owner_answer_packet_check.py
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
    Write-Output "Bologna ODP-BOL-001 owner answer packet check: ok"
}
finally {
    Pop-Location
}
