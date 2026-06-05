param(
    [string]$StorageBackend = $env:APP_STORAGE_BACKEND,
    [string]$BindAddress = '127.0.0.1',
    [int]$Port = 8000,
    [switch]$NoReload
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = Resolve-Path (Join-Path $PSScriptRoot '..')
$allowedBackends = @('memory', 'postgres')
if ([string]::IsNullOrWhiteSpace($StorageBackend)) {
    $StorageBackend = 'memory'
}
$StorageBackend = $StorageBackend.Trim().ToLowerInvariant()
if ($StorageBackend -notin $allowedBackends) {
    throw "StorageBackend must be one of: $($allowedBackends -join ', ')"
}

$python = ''
if (Get-Command py -ErrorAction SilentlyContinue) {
    $candidate = & py -3.12 -c "import sys; raise SystemExit(1 if sys.version_info < (3, 12) else print(sys.executable))"
    if ($LASTEXITCODE -eq 0) {
        $python = $candidate
    }
}
if (-not $python -and (Get-Command python -ErrorAction SilentlyContinue)) {
    $candidate = & python -c "import sys; raise SystemExit(1 if sys.version_info < (3, 12) else print(sys.executable))"
    if ($LASTEXITCODE -eq 0) {
        $python = $candidate
    }
}
if (-not $python) {
    throw 'Python 3.12+ is required. Install Python 3.12+ or make it available through py -3.12 or python.'
}

$previousStorageBackend = $env:APP_STORAGE_BACKEND
$previousPythonPath = $env:PYTHONPATH
$previousObjectStoreRoot = $env:OBJECT_STORE_ROOT
$env:APP_STORAGE_BACKEND = $StorageBackend
$env:PYTHONPATH = '.'
$env:OBJECT_STORE_ROOT = Join-Path $root 'local_artifacts\object_store'
$uvicornArgs = @('-m', 'uvicorn', 'app.main:app', '--host', $BindAddress, '--port', [string]$Port)
if (-not $NoReload) {
    $uvicornArgs += '--reload'
}

Write-Host "Starting land-diligence API on http://$BindAddress`:$Port using $StorageBackend storage"
Push-Location (Join-Path $root 'backend')
try {
    & $python @uvicornArgs
}
finally {
    Pop-Location
    if ($null -eq $previousStorageBackend) {
        Remove-Item Env:APP_STORAGE_BACKEND -ErrorAction SilentlyContinue
    } else {
        $env:APP_STORAGE_BACKEND = $previousStorageBackend
    }
    if ($null -eq $previousPythonPath) {
        Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
    } else {
        $env:PYTHONPATH = $previousPythonPath
    }
    if ($null -eq $previousObjectStoreRoot) {
        Remove-Item Env:OBJECT_STORE_ROOT -ErrorAction SilentlyContinue
    } else {
        $env:OBJECT_STORE_ROOT = $previousObjectStoreRoot
    }
}
