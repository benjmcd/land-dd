$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $root

$localArtifacts = Join-Path $root 'local_artifacts'
if (Test-Path -Path $localArtifacts -PathType Container) {
    $env:PATH = "$localArtifacts;$env:PATH"
}

$dbUrl = if ($env:DATABASE_URL_SYNC) { $env:DATABASE_URL_SYNC } else { 'postgresql://land:land@localhost:5432/land_diligence' }
$defaultDbUrl = 'postgresql://land:land@localhost:5432/land_diligence'
$psqlCommand = Get-Command psql -ErrorAction SilentlyContinue

function Invoke-SqlFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if ($psqlCommand) {
        & psql $dbUrl -v ON_ERROR_STOP=1 -f $Path
    } else {
        if ($dbUrl -ne $defaultDbUrl) {
            throw 'psql is required when DATABASE_URL_SYNC is not the default local Docker database.'
        }
        if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
            throw 'psql not found and Docker is not available for the local db fallback.'
        }

        Get-Content -Path $Path -Raw | docker compose exec -T db psql -U land -d land_diligence -v ON_ERROR_STOP=1
    }

    if ($LASTEXITCODE -ne 0) {
        throw "psql failed on $Path with exit code $LASTEXITCODE"
    }
}

Get-ChildItem -Path 'db/migrations' -Filter '*.sql' | Sort-Object Name | ForEach-Object {
    Write-Host "Applying $($_.FullName)"
    Invoke-SqlFile -Path $_.FullName
}

Get-ChildItem -Path 'db/seeds' -Filter '*.sql' | Sort-Object Name | ForEach-Object {
    Write-Host "Applying $($_.FullName)"
    Invoke-SqlFile -Path $_.FullName
}

Write-Host 'Migrations and seeds applied.'
