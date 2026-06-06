#Requires -Version 5.1
<#
.SYNOPSIS
    Run the Private MVP regression suite (DB-smoke-gated).

.DESCRIPTION
    Exercises the end-to-end fixture connector path (Path B) for the three
    NC private-MVP counties (Buncombe, Chatham, Brunswick).  All tests use
    in-memory services and the golden-AOI fixture blobs; no live DB or
    vendor connection is required.

    Set $env:RUN_DB_SMOKE = '1' before running, or use the -Force flag.

.PARAMETER Force
    Automatically sets RUN_DB_SMOKE=1 for this invocation.

.PARAMETER PytestArgs
    Extra arguments forwarded verbatim to pytest (e.g. -v, -s, -k buncombe).

.EXAMPLE
    .\scripts\run_mvp_regression.ps1 -Force
    .\scripts\run_mvp_regression.ps1 -Force -PytestArgs '-v'
    $env:RUN_DB_SMOKE='1'; .\scripts\run_mvp_regression.ps1
#>
[CmdletBinding()]
param(
    [switch]$Force,
    [string[]]$PytestArgs = @()
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot

if ($Force) {
    $env:RUN_DB_SMOKE = '1'
}

if ($env:RUN_DB_SMOKE -ne '1') {
    Write-Error "RUN_DB_SMOKE is not set to '1'. Use -Force or set the variable before running."
    exit 1
}

Write-Host "== Private MVP regression suite ==" -ForegroundColor Cyan
Write-Host "RUN_DB_SMOKE=$env:RUN_DB_SMOKE"

Set-Location (Join-Path $Root 'backend')

$pytestCmd = @(
    'python', '-m', 'pytest',
    'tests/private_mvp/test_mvp_regression.py'
) + $PytestArgs

$env:PYTHONPATH = '.'
& $pytestCmd[0] $pytestCmd[1..($pytestCmd.Length - 1)]

if ($LASTEXITCODE -ne 0) {
    Write-Error "MVP regression suite FAILED (exit $LASTEXITCODE)"
    exit $LASTEXITCODE
}

Write-Host "== MVP regression suite PASSED ==" -ForegroundColor Green
