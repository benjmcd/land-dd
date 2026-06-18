$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $root

$projectName = if ($env:DEPLOYMENT_SMOKE_PROJECT) {
    $env:DEPLOYMENT_SMOKE_PROJECT
} else {
    'land-diligence-smoke'
}
$backendPort = if ($env:DEPLOYMENT_SMOKE_BACKEND_PORT) {
    $env:DEPLOYMENT_SMOKE_BACKEND_PORT
} else {
    '18080'
}
$dbPort = if ($env:DEPLOYMENT_SMOKE_DB_PORT) {
    $env:DEPLOYMENT_SMOKE_DB_PORT
} else {
    '55432'
}
$baseUrl = "http://127.0.0.1:$backendPort"

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

function Invoke-Compose {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    Invoke-NativeCommand -Label "docker compose $($Arguments -join ' ')" -Command {
        & docker compose --project-name $projectName @Arguments
    }
}

function Invoke-ComposeSqlFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    Write-Host "Applying $Path"
    Invoke-NativeCommand -Label "docker compose cp $Path" -Command {
        & docker compose --project-name $projectName cp $Path "db:/tmp/deployment-smoke.sql"
    }
    Invoke-NativeCommand -Label "psql $Path" -Command {
        & docker compose --project-name $projectName exec -T db psql -U land -d land_diligence -v ON_ERROR_STOP=1 -f /tmp/deployment-smoke.sql
    }
}

function Get-DbStartTime {
    $output = & docker compose --project-name $projectName exec -T db `
        psql -U land -d land_diligence -At -v ON_ERROR_STOP=1 -c "SELECT pg_postmaster_start_time();" 2>$null
    if ($LASTEXITCODE -ne 0) {
        return ''
    }
    return ([string]$output).Trim()
}

function Wait-ForDb {
    $deadline = (Get-Date).AddSeconds(90)
    do {
        & docker compose --project-name $projectName exec -T db `
            pg_isready -U land -d land_diligence *> $null
        if ($LASTEXITCODE -eq 0) {
            $firstStartTime = Get-DbStartTime
            if ($firstStartTime) {
                Start-Sleep -Seconds 5
                & docker compose --project-name $projectName exec -T db `
                    pg_isready -U land -d land_diligence *> $null
                if ($LASTEXITCODE -eq 0) {
                    $secondStartTime = Get-DbStartTime
                    if ($secondStartTime -and $firstStartTime -eq $secondStartTime) {
                        return
                    }
                    Write-Host 'db start time changed while waiting for deployment smoke; waiting for final startup'
                }
            }
        }
        Start-Sleep -Seconds 2
    } while ((Get-Date) -lt $deadline)

    throw 'db did not become ready for deployment smoke'
}

function Wait-ForBackend {
    $deadline = (Get-Date).AddSeconds(90)
    do {
        try {
            $health = Invoke-RestMethod -Uri "$baseUrl/health" -TimeoutSec 3
            if ($health.status -eq 'ok') {
                return
            }
        } catch {
            Start-Sleep -Seconds 2
        }
    } while ((Get-Date) -lt $deadline)

    throw "backend did not become healthy at $baseUrl/health"
}

function Invoke-JsonPost {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Uri,

        [Parameter(Mandatory = $true)]
        [object]$Body
    )

    $jsonBody = if ($Body -is [string]) {
        $Body
    } else {
        $Body | ConvertTo-Json -Depth 20
    }

    Invoke-RestMethod `
        -Method Post `
        -Uri $Uri `
        -ContentType 'application/json' `
        -Body $jsonBody `
        -TimeoutSec 10
}

function Wait-ForReport {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ReportRunId
    )

    $deadline = (Get-Date).AddSeconds(90)
    do {
        $report = Invoke-RestMethod -Uri "$baseUrl/report-runs/$ReportRunId" -TimeoutSec 10
        if ($report.status -eq 'succeeded') {
            return $report
        }
        if ($report.status -eq 'failed') {
            throw "report run failed during deployment smoke: $ReportRunId"
        }
        Start-Sleep -Seconds 2
    } while ((Get-Date) -lt $deadline)

    throw "report run did not finish during deployment smoke: $ReportRunId"
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw 'Docker is required for deployment smoke.'
}

$savedEnv = @{
    DB_PORT = $env:DB_PORT
    BACKEND_PORT = $env:BACKEND_PORT
    COMPOSE_USE_DB_SERVICES = $env:COMPOSE_USE_DB_SERVICES
    ENABLE_LIVE_CONNECTORS = $env:ENABLE_LIVE_CONNECTORS
    ENABLE_METRICS = $env:ENABLE_METRICS
    REQUIRE_API_KEY = $env:REQUIRE_API_KEY
    ENABLE_RATE_LIMIT = $env:ENABLE_RATE_LIMIT
}

$env:DB_PORT = $dbPort
$env:BACKEND_PORT = $backendPort
$env:COMPOSE_USE_DB_SERVICES = 'true'
$env:ENABLE_LIVE_CONNECTORS = 'false'
$env:ENABLE_METRICS = 'true'
$env:REQUIRE_API_KEY = 'false'
$env:ENABLE_RATE_LIMIT = 'false'

try {
    Write-Host "deployment smoke: project=$projectName backend=$baseUrl db-port=$dbPort"
    Invoke-Compose -Arguments @('build', 'backend')
    Invoke-Compose -Arguments @('up', '-d', 'db')
    Wait-ForDb

    Get-ChildItem -Path '.\db\migrations' -Filter '*.sql' |
        Sort-Object Name |
        ForEach-Object { Invoke-ComposeSqlFile -Path $_.FullName }
    Get-ChildItem -Path '.\db\seeds' -Filter '*.sql' |
        Sort-Object Name |
        ForEach-Object { Invoke-ComposeSqlFile -Path $_.FullName }

    Invoke-Compose -Arguments @('up', '-d', 'backend')
    Wait-ForBackend

    $version = Invoke-RestMethod -Uri "$baseUrl/version" -TimeoutSec 10
    if (-not $version.version) {
        throw 'version endpoint did not return version'
    }
    $metrics = Invoke-RestMethod -Uri "$baseUrl/metrics" -TimeoutSec 10
    if ($metrics.schema_version -ne 'runtime_metrics_v1') {
        throw 'metrics endpoint did not return runtime_metrics_v1'
    }

    $headers = @{
        'X-Reviewer-Id' = 'fixture-reviewer'
        'X-Reviewer-Token' = 'fixture-token-123'
    }
    $queueHealth = Invoke-RestMethod -Uri "$baseUrl/operations/queue-health" -Headers $headers -TimeoutSec 10
    if ($queueHealth.schema_version -ne 'operations_queue_health_v1') {
        throw 'queue health endpoint did not return operations_queue_health_v1'
    }
    foreach ($queueName in @('report_jobs', 'live_connector_jobs')) {
        $queue = $queueHealth.$queueName
        foreach ($fieldName in @(
            'oldest_running_age_seconds',
            'oldest_running_job_id',
            'stale_running',
            'stale_running_threshold_seconds'
        )) {
            if ($queue.PSObject.Properties.Name -notcontains $fieldName) {
                throw "queue health $queueName missing $fieldName"
            }
        }
        if ($queue.stale_running_threshold_seconds -ne 900) {
            throw "queue health $queueName stale threshold mismatch"
        }
    }
    $recoveryPreview = Invoke-RestMethod -Uri "$baseUrl/operations/recovery-preview" -Headers $headers -TimeoutSec 10
    if ($recoveryPreview.schema_version -ne 'operations_recovery_preview_v1') {
        throw 'recovery preview endpoint did not return operations_recovery_preview_v1'
    }
    if ($recoveryPreview.stale_running_threshold_seconds -ne 900) {
        throw 'recovery preview stale threshold mismatch'
    }
    foreach ($queueName in @('report_jobs', 'live_connector_jobs')) {
        $queue = $recoveryPreview.$queueName
        foreach ($fieldName in @(
            'failed_count',
            'stale_running_count',
            'queued_count',
            'failed_candidates_truncated',
            'stale_running_candidates_truncated',
            'candidates'
        )) {
            if ($queue.PSObject.Properties.Name -notcontains $fieldName) {
                throw "recovery preview $queueName missing $fieldName"
            }
        }
    }

    $areaBody = @'
{
  "label": "deployment smoke polygon",
  "geom_source": "deployment-smoke",
  "geom_geojson": {
    "type": "Polygon",
    "coordinates": [[
      [-77.10, 38.80],
      [-77.00, 38.80],
      [-77.00, 38.90],
      [-77.10, 38.90],
      [-77.10, 38.80]
    ]]
  }
}
'@
    $area = Invoke-JsonPost -Uri "$baseUrl/areas" -Body $areaBody
    $reportJob = Invoke-JsonPost -Uri "$baseUrl/report-runs" -Body @{
        area_id = $area.area_id
        intent_code = 'rural_land_purchase'
    }
    $report = Wait-ForReport -ReportRunId $reportJob.report_run_id
    if (-not $report.claims -or -not $report.evidence) {
        throw 'report response did not include claims and evidence'
    }

    Write-Host 'deployment smoke: ok'
} finally {
    if ($env:DEPLOYMENT_SMOKE_KEEP_SERVICES -ne '1') {
        try {
            Invoke-Compose -Arguments @('down')
        } catch {
            Write-Warning $_
        }
    } else {
        Write-Host "deployment smoke: preserved Compose project $projectName"
    }

    foreach ($key in $savedEnv.Keys) {
        if ($null -eq $savedEnv[$key]) {
            Remove-Item "Env:$key" -ErrorAction SilentlyContinue
        } else {
            Set-Item "Env:$key" $savedEnv[$key]
        }
    }
}
