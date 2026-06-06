<#
.SYNOPSIS
    Run bandit static security analysis on backend/app.

.PARAMETER ValidateOnly
    Check that bandit is importable without running a scan.
#>
param(
    [switch]$ValidateOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ($ValidateOnly) {
    py -3.12 -c "import bandit" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "bandit is not importable. Install with: pip install bandit"
        exit 1
    }
    Write-Host "bandit importable: OK"
    exit 0
}

$backendRoot = Join-Path (Join-Path $PSScriptRoot "..") "backend"
Push-Location $backendRoot
try {
    Write-Host "Running bandit on backend/app (severity threshold: medium+) ..."
    $banditOutput = $null
    py -3.12 -m bandit -r app -ll -q 2>&1 | Tee-Object -Variable banditOutput

    $outputText = $banditOutput -join "`n"

    $hasHigh     = $outputText -match "Severity:\s+High"
    $hasCritical = $outputText -match "Severity:\s+Critical"

    if ($hasHigh -or $hasCritical) {
        Write-Host ""
        Write-Error "Security scan FAILED: HIGH or CRITICAL severity issues found. Review the output above and either fix the code or add '# nosec <BXXX> # justification' comments for confirmed false positives."
        exit 1
    }

    Write-Host ""
    Write-Host "Security scan PASSED: no HIGH or CRITICAL issues found."
    exit 0
} finally {
    Pop-Location
}
