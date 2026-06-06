$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $root

$localArtifacts = Join-Path $root 'local_artifacts'
if (Test-Path -Path $localArtifacts -PathType Container) {
    $env:PATH = "$localArtifacts;$env:PATH"
}

$sourceDbUrl = if ($env:DATABASE_URL_SYNC) {
    $env:DATABASE_URL_SYNC
} else {
    'postgresql://land:land@localhost:5432/land_diligence'
}

$restoreDbName = if ($env:RESTORE_CHECK_DB_NAME) {
    $env:RESTORE_CHECK_DB_NAME
} else {
    'land_diligence_restore_check'
}

if ($restoreDbName -notmatch '^land_diligence_restore_check[a-zA-Z0-9_]*$') {
    throw 'RESTORE_CHECK_DB_NAME must start with land_diligence_restore_check and contain only letters, digits, or underscores.'
}

function Convert-DatabaseUrl {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Url,

        [Parameter(Mandatory = $true)]
        [string]$DatabaseName
    )

    $builder = [System.UriBuilder]::new($Url)
    $builder.Path = $DatabaseName
    return $builder.Uri.AbsoluteUri
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

function Quote-PgIdentifier {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Identifier
    )

    return '"' + $Identifier.Replace('"', '""') + '"'
}

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

function Get-PythonExecutable {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3.12 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)" 2>$null
        if ($LASTEXITCODE -eq 0) {
            return 'py -3.12'
        }
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        & python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)" 2>$null
        if ($LASTEXITCODE -eq 0) {
            return 'python'
        }
    }
    throw 'Python 3.12+ is required.'
}

if (-not (Get-Command psql -ErrorAction SilentlyContinue)) {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw 'psql not found and Docker is unavailable. Install PostgreSQL client or use the local_artifacts wrapper.'
    }
}
$useDockerPgDump = $false
if (-not (Get-Command pg_dump -ErrorAction SilentlyContinue)) {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw 'pg_dump not found and Docker is unavailable. Install PostgreSQL client or use the local_artifacts wrapper.'
    }
    $useDockerPgDump = $true
}
$useDockerPsql = $useDockerPgDump

$adminDbUrl = if ($env:DATABASE_ADMIN_URL_SYNC) {
    $env:DATABASE_ADMIN_URL_SYNC
} else {
    Convert-DatabaseUrl -Url $sourceDbUrl -DatabaseName 'postgres'
}
$restoreDbUrl = if ($env:RESTORE_DATABASE_URL_SYNC) {
    $env:RESTORE_DATABASE_URL_SYNC
} else {
    Convert-DatabaseUrl -Url $sourceDbUrl -DatabaseName $restoreDbName
}

$dumpDir = Join-Path $root 'local_artifacts\backup_restore'
New-Item -ItemType Directory -Force -Path $dumpDir | Out-Null
$dumpPath = if ($env:RESTORE_CHECK_DUMP_PATH) {
    $env:RESTORE_CHECK_DUMP_PATH
} else {
    Join-Path $dumpDir 'restore-check.sql'
}

$quotedRestoreDb = Quote-PgIdentifier -Identifier $restoreDbName
$pythonExecutable = Get-PythonExecutable
$adminClientDbUrl = if ($useDockerPsql) {
    Convert-LocalhostForDocker -Url $adminDbUrl
} else {
    $adminDbUrl
}
$restoreClientDbUrl = if ($useDockerPsql) {
    Convert-LocalhostForDocker -Url $restoreDbUrl
} else {
    $restoreDbUrl
}

function Invoke-PsqlCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Label,

        [Parameter(Mandatory = $true)]
        [string]$Url,

        [Parameter(Mandatory = $true)]
        [string]$Sql
    )

    if ($useDockerPsql) {
        Invoke-NativeCommand -Label $Label -Command {
            & docker run --rm postgis/postgis:16-3.4 psql $Url -v ON_ERROR_STOP=1 -c $Sql
        }
    } else {
        Invoke-NativeCommand -Label $Label -Command {
            & psql $Url -v ON_ERROR_STOP=1 -c $Sql
        }
    }
}

function Invoke-PsqlFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Label,

        [Parameter(Mandatory = $true)]
        [string]$Url,

        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if ($useDockerPsql) {
        Invoke-NativeCommand -Label $Label -Command {
            Get-Content -Raw -Path $Path | & docker run -i --rm postgis/postgis:16-3.4 psql $Url -v ON_ERROR_STOP=1
        }
    } else {
        Invoke-NativeCommand -Label $Label -Command {
            & psql $Url -v ON_ERROR_STOP=1 -f $Path
        }
    }
}

Write-Host "backup/restore check: source=$sourceDbUrl"
Write-Host "backup/restore check: restore database=$restoreDbName"
Write-Host "backup/restore check: dump path=$dumpPath"

Invoke-PsqlCommand `
    -Label 'drop pre-existing restore database' `
    -Url $adminClientDbUrl `
    -Sql "DROP DATABASE IF EXISTS $quotedRestoreDb WITH (FORCE)"
Invoke-PsqlCommand `
    -Label 'create restore database' `
    -Url $adminClientDbUrl `
    -Sql "CREATE DATABASE $quotedRestoreDb"

try {
    if ($useDockerPgDump) {
        $dockerSourceDbUrl = Convert-LocalhostForDocker -Url $sourceDbUrl
        Invoke-NativeCommand -Label 'docker pg_dump' -Command {
            & docker run --rm postgis/postgis:16-3.4 pg_dump $dockerSourceDbUrl --format=plain --no-owner --no-privileges > $dumpPath
        }
    } else {
        Invoke-NativeCommand -Label 'pg_dump' -Command {
            & pg_dump $sourceDbUrl --format=plain --no-owner --no-privileges --file $dumpPath
        }
    }
    Invoke-PsqlFile -Label 'restore dump' -Url $restoreClientDbUrl -Path $dumpPath

    $previousDatabaseUrl = $env:DATABASE_URL_SYNC
    $env:DATABASE_URL_SYNC = $restoreDbUrl
    try {
        if ($pythonExecutable -eq 'py -3.12') {
            Invoke-NativeCommand -Label 'restore DB smoke' -Command {
                & py -3.12 scripts/db_smoke_check.py
            }
        } else {
            Invoke-NativeCommand -Label 'restore DB smoke' -Command {
                & python scripts/db_smoke_check.py
            }
        }
    } finally {
        if ($null -eq $previousDatabaseUrl) {
            Remove-Item Env:DATABASE_URL_SYNC -ErrorAction SilentlyContinue
        } else {
            $env:DATABASE_URL_SYNC = $previousDatabaseUrl
        }
    }

    Write-Host 'backup/restore check: ok'
} finally {
    if ($env:RESTORE_CHECK_KEEP_DB -ne '1') {
        Invoke-PsqlCommand `
            -Label 'drop restore database' `
            -Url $adminClientDbUrl `
            -Sql "DROP DATABASE IF EXISTS $quotedRestoreDb WITH (FORCE)"
    } else {
        Write-Host "backup/restore check: preserved restore database $restoreDbName"
    }
}
