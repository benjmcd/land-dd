$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    py -3.12 scripts\bologna_odp3_corpus_response_gate_check.py
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
    Write-Output "Bologna ODP-BOL-003 corpus response gate check: ok"
}
finally {
    Pop-Location
}
