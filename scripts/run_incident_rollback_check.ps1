$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $root

$runbookPath = Join-Path $root 'docs\runbooks\incident_response.md'
$requiredFiles = @(
    'docs\runbooks\incident_response.md',
    'scripts\run_deployment_smoke.ps1',
    'scripts\run_deployment_smoke.sh',
    'scripts\run_backup_restore_check.ps1',
    'scripts\run_backup_restore_check.sh',
    'scripts\verify.ps1',
    'scripts\source_readiness.py'
)
$requiredPhrases = @(
    '## Severity Levels',
    '## Ownership',
    '## Escalation',
    '## Rollback and Mitigation',
    '## Recovery Criteria',
    'SEV0',
    'SEV1',
    'Incident commander',
    'Deployment Rollback',
    'Database Rollback or Migration Mitigation',
    'Connector or Source Outage',
    'Queue or Report Failure',
    'run_deployment_smoke.ps1',
    'run_backup_restore_check.ps1',
    'source_readiness.py',
    'ENABLE_LIVE_CONNECTORS=false'
)

function Invoke-NativeCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Label,

        [Parameter(Mandatory = $true)]
        [scriptblock]$Command
    )

    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE"
    }
}

foreach ($file in $requiredFiles) {
    if (-not (Test-Path -Path (Join-Path $root $file) -PathType Leaf)) {
        throw "required incident/rollback artifact missing: $file"
    }
}

$runbook = Get-Content -Raw -Path $runbookPath
foreach ($phrase in $requiredPhrases) {
    if (-not $runbook.Contains($phrase)) {
        throw "incident response runbook missing required phrase: $phrase"
    }
}

if (Get-Command docker -ErrorAction SilentlyContinue) {
    Invoke-NativeCommand -Label 'docker compose config' -Command {
        & docker compose config --quiet
    }
} else {
    Write-Host 'incident/rollback check: docker unavailable; compose config skipped'
}

$sourceReadinessJson = & py -3.12 .\scripts\source_readiness.py --priority Must --json
if ($LASTEXITCODE -ne 0) {
    throw "source readiness check failed with exit code $LASTEXITCODE"
}
$sourceReadiness = $sourceReadinessJson | ConvertFrom-Json
if ($sourceReadiness.schema_version -ne 'source_readiness_v1') {
    throw 'source readiness JSON did not return source_readiness_v1'
}
if ($sourceReadiness.source_count -lt 1) {
    throw 'source readiness JSON returned no sources'
}

Write-Host 'incident/rollback check: ok'
