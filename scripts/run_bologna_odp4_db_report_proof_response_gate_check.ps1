$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    py -3.12 scripts\bologna_odp4_db_report_proof_response_gate_check.py
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
    Write-Output "Bologna ODP-BOL-004 DB report proof response gate check: ok"
}
finally {
    Pop-Location
}
