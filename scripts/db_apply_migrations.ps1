$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $root

$localArtifacts = Join-Path $root 'local_artifacts'
if (Test-Path -Path $localArtifacts -PathType Container) {
    $env:PATH = "$localArtifacts;$env:PATH"
}

$dbUrl = if ($env:DATABASE_URL_SYNC) { $env:DATABASE_URL_SYNC } else { 'postgresql://land:land@localhost:5432/land_diligence' }

if (-not (Get-Command psql -ErrorAction SilentlyContinue)) {
    Write-Error 'psql not found. Install PostgreSQL client or run migrations through your preferred DB tool.'
    exit 1
}

Get-ChildItem -Path 'db/migrations' -Filter '*.sql' | Sort-Object Name | ForEach-Object {
    Write-Host "Applying $($_.FullName)"
    & psql $dbUrl -v ON_ERROR_STOP=1 -f $_.FullName
    if ($LASTEXITCODE -ne 0) {
        throw "psql failed on $($_.FullName) with exit code $LASTEXITCODE"
    }
}

Get-ChildItem -Path 'db/seeds' -Filter '*.sql' | Sort-Object Name | ForEach-Object {
    Write-Host "Applying $($_.FullName)"
    & psql $dbUrl -v ON_ERROR_STOP=1 -f $_.FullName
    if ($LASTEXITCODE -ne 0) {
        throw "psql failed on $($_.FullName) with exit code $LASTEXITCODE"
    }
}

Write-Host 'Migrations and seeds applied.'
