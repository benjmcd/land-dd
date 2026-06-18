param(
    [switch]$ValidateOnly,
    [string]$Scenario = "",
    [string]$BaseUrl = "",
    [string]$ResultDir = ""
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $root

$requiredFiles = @(
    'scripts\run_load_test.ps1',
    'scripts\run_load_test.sh',
    'scripts\load_test_runner.py',
    'config\performance_baseline.yaml',
    'docs\runbooks\load_testing.md'
)

foreach ($file in $requiredFiles) {
    $fullPath = Join-Path $root $file
    if (-not (Test-Path -Path $fullPath -PathType Leaf)) {
        Write-Error "load test artifact missing: $file"
        exit 1
    }
    $content = Get-Content -Path $fullPath -Raw
    if (-not $content -or $content.Trim().Length -eq 0) {
        Write-Error "load test artifact is empty: $file"
        exit 1
    }
}

Write-Host 'load test: artifact validation ok'

if ($ValidateOnly) {
    Write-Host 'load test: --validate-only requested; skipping live HTTP requests'
    exit 0
}

# Resolve base URL: -BaseUrl param > LOAD_TEST_BASE_URL env > default
if ($BaseUrl -ne "") {
    $env:LOAD_TEST_BASE_URL = $BaseUrl
} elseif (-not $env:LOAD_TEST_BASE_URL) {
    $env:LOAD_TEST_BASE_URL = "http://127.0.0.1:8000"
}

$runnerScript = Join-Path $root 'scripts\load_test_runner.py'

$scenarios = if ($Scenario -ne "") {
    @($Scenario)
} else {
    @("sequential", "concurrent")
}

$failed = $false
foreach ($s in $scenarios) {
    Write-Host "load test: running scenario=$s base_url=$env:LOAD_TEST_BASE_URL"
    $runnerArgs = @($runnerScript, '--scenario', $s, '--base-url', $env:LOAD_TEST_BASE_URL)
    if ($ResultDir -ne "") {
        New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null
        $outputPath = Join-Path $ResultDir "load-test-$s.json"
        $runnerArgs += @('--json-output', $outputPath)
    }
    py -3.12 @runnerArgs
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "load test scenario '$s' failed with exit code $LASTEXITCODE"
        $failed = $true
    }
}

if ($failed) {
    exit 1
}
