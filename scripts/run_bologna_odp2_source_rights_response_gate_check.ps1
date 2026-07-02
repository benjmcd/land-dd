$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    py -3.12 scripts\bologna_odp2_source_rights_response_gate_check.py
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
    Write-Output "Bologna ODP-BOL-002 source-rights response gate check: ok"
}
finally {
    Pop-Location
}
