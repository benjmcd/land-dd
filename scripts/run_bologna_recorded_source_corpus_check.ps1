$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$validator = '.\scripts\bologna_recorded_source_corpus_check.py'

Push-Location $root
try {
    if (-not (Test-Path $validator)) {
        throw "required Bologna recorded-source corpus artifact missing: scripts\bologna_recorded_source_corpus_check.py"
    }
    py -3.12 $validator
    if ($LASTEXITCODE -ne 0) {
        throw "Bologna recorded-source corpus check failed with exit code $LASTEXITCODE"
    }
    Write-Host 'Bologna recorded-source corpus check: ok'
} finally {
    Pop-Location
}
