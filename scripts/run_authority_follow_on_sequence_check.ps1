$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    $python = if ($env:LAND_DD_PYTHON_EXECUTABLE) { $env:LAND_DD_PYTHON_EXECUTABLE } else { "py" }
    if ($python -eq "py") {
        & $python -3.12 .\scripts\authority_follow_on_sequence_check.py
    } else {
        & $python .\scripts\authority_follow_on_sequence_check.py
    }
    if ($LASTEXITCODE -ne 0) {
        throw "Authority follow-on sequence check failed"
    }
    Write-Output "authority follow-on sequence: ok"
}
finally {
    Pop-Location
}
