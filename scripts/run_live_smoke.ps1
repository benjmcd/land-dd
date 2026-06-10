# Live connector smoke wrapper (PowerShell).
#
# When RUN_LIVE_CONNECTOR_TESTS != 1: prints a SKIP message and exits 0.
# When RUN_LIVE_CONNECTOR_TESTS = 1: starts the API on port 8103 (in-memory,
#   live connectors enabled), runs the four query-bbox smoke legs for a small
#   Buncombe NC bbox, writes a timestamped transcript to local_artifacts/, and
#   stops the API before exiting.
#
# Usage:
#   .\scripts\run_live_smoke.ps1
#   $env:RUN_LIVE_CONNECTOR_TESTS=1; .\scripts\run_live_smoke.ps1
#
# Environment variables honoured:
#   RUN_LIVE_CONNECTOR_TESTS  Set to 1 to execute; any other value (or absent) skips.
#   SMOKE_API_PORT            Override the API port (default 8103).
#   SMOKE_OUTPUT_DIR          Override the transcript directory (default local_artifacts).

param()
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$Root = Resolve-Path (Join-Path $PSScriptRoot '..')
$Port = if ($env:SMOKE_API_PORT) { $env:SMOKE_API_PORT } else { '8103' }
$OutputDir = if ($env:SMOKE_OUTPUT_DIR) { $env:SMOKE_OUTPUT_DIR } else { Join-Path $Root 'local_artifacts' }

# ---------------------------------------------------------------------------
# Gate: skip unless explicitly opted in
# ---------------------------------------------------------------------------
if ($env:RUN_LIVE_CONNECTOR_TESTS -ne '1') {
    Write-Host "SKIP: live connector smoke (set RUN_LIVE_CONNECTOR_TESTS=1 to run)"
    exit 0
}

Write-Host "=== live connector smoke: port=$Port output=$OutputDir ==="

# ---------------------------------------------------------------------------
# Locate Python 3.12+
# ---------------------------------------------------------------------------
$Python = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    $candidate = py -3.12 -c "import sys; print(sys.executable)" 2>$null
    if ($LASTEXITCODE -eq 0 -and $candidate) { $Python = $candidate.Trim() }
}
if (-not $Python -and (Get-Command python -ErrorAction SilentlyContinue)) {
    $vcheck = python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,12) else 1)" 2>$null
    if ($LASTEXITCODE -eq 0) { $Python = 'python' }
}
if (-not $Python) {
    Write-Error "Python 3.12+ required (py -3.12 or python with 3.12+)"
    exit 1
}
Write-Host "Using Python: $Python"

# ---------------------------------------------------------------------------
# Start API server in background
# ---------------------------------------------------------------------------
$ApiUrl = "http://127.0.0.1:$Port"
$BackendDir = Join-Path $Root 'backend'

$env:ENABLE_LIVE_CONNECTORS = 'true'
$env:PYTHONPATH = '.'
$env:OBJECT_STORE_ROOT = Join-Path $Root 'local_artifacts\object_store'

Write-Host "Starting API on $ApiUrl (in-memory storage, ENABLE_LIVE_CONNECTORS=true)..."
$ApiProcess = Start-Process `
    -FilePath $Python `
    -ArgumentList @('-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', $Port, '--no-access-log') `
    -WorkingDirectory $BackendDir `
    -PassThru `
    -NoNewWindow

$StopApi = {
    if ($ApiProcess -and -not $ApiProcess.HasExited) {
        Write-Host "Stopping API (PID $($ApiProcess.Id))..."
        Stop-Process -Id $ApiProcess.Id -Force -ErrorAction SilentlyContinue
    }
}

try {
    # ---------------------------------------------------------------------------
    # Run smoke driver
    # ---------------------------------------------------------------------------
    $SmokeScript = Join-Path $PSScriptRoot 'run_live_smoke.py'
    & $Python $SmokeScript --api-url $ApiUrl --output-dir $OutputDir
    $SmokeExit = $LASTEXITCODE
} finally {
    & $StopApi
    # Clean up env vars set above
    Remove-Item Env:ENABLE_LIVE_CONNECTORS -ErrorAction SilentlyContinue
    Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
    Remove-Item Env:OBJECT_STORE_ROOT -ErrorAction SilentlyContinue
}

if ($SmokeExit -ne 0) {
    Write-Host "live connector smoke FAILED (exit $SmokeExit)"
    exit $SmokeExit
}
Write-Host "live connector smoke PASSED"
exit 0
