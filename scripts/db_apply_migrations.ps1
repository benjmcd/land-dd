$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $root

$localArtifacts = Join-Path $root 'local_artifacts'
if (Test-Path -Path $localArtifacts -PathType Container) {
    $env:PATH = "$localArtifacts;$env:PATH"
}

$dbUrl = if ($env:DATABASE_URL_SYNC) { $env:DATABASE_URL_SYNC } else { 'postgresql://land:land@localhost:5432/land_diligence' }

$useDockerPsql = $false
$psqlCommand = Get-Command psql -ErrorAction SilentlyContinue
$localPsqlShim = $false
if ($psqlCommand) {
    $psqlSource = [string]$psqlCommand.Source
    $localPsqlShim = $psqlSource.StartsWith(
        [string]$localArtifacts,
        [System.StringComparison]::OrdinalIgnoreCase
    )
}

function Convert-LocalhostForDocker {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Url
    )

    $builder = [System.UriBuilder]::new($Url)
    if ($builder.Host -in @('localhost', '127.0.0.1', '::1')) {
        $builder.Host = 'host.docker.internal'
    }
    return $builder.Uri.AbsoluteUri
}

if (-not $psqlCommand -or $localPsqlShim) {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Error 'psql not found and Docker is unavailable. Install PostgreSQL client or run migrations through your preferred DB tool.'
        exit 1
    }
    $useDockerPsql = $true
}

$clientDbUrl = if ($useDockerPsql) { Convert-LocalhostForDocker -Url $dbUrl } else { $dbUrl }

function Invoke-PsqlFile {
    param(
        [Parameter(Mandatory = $true)]
        [System.IO.FileInfo]$File
    )

    if ($useDockerPsql) {
        Get-Content -Path $File.FullName -Raw | & docker run --rm -i --add-host=host.docker.internal:host-gateway postgis/postgis:16-3.4 psql $clientDbUrl -v ON_ERROR_STOP=1 -f -
    } else {
        & $psqlCommand.Source $clientDbUrl -v ON_ERROR_STOP=1 -f $File.FullName
    }
    if ($LASTEXITCODE -ne 0) {
        throw "psql failed on $($File.FullName) with exit code $LASTEXITCODE"
    }
}

Get-ChildItem -Path 'db/migrations' -Filter '*.sql' | Sort-Object Name | ForEach-Object {
    Write-Host "Applying $($_.FullName)"
    Invoke-PsqlFile -File $_
}

Get-ChildItem -Path 'db/seeds' -Filter '*.sql' | Sort-Object Name | ForEach-Object {
    Write-Host "Applying $($_.FullName)"
    Invoke-PsqlFile -File $_
}

Write-Host 'Migrations and seeds applied.'
