$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $root

$script:PythonExecutable = ''

function Get-PythonCandidatePath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Executable,

        [string[]]$Prefix = @()
    )

    if (-not (Get-Command $Executable -ErrorAction SilentlyContinue)) {
        return ''
    }

    $candidatePath = & $Executable @Prefix -c "import sys; raise SystemExit(1 if sys.version_info < (3, 12) else print(sys.executable))"
    if ($LASTEXITCODE -ne 0) {
        return ''
    }
    return $candidatePath
}

function Select-Python {
    $py312Path = Get-PythonCandidatePath -Executable 'py' -Prefix @('-3.12')
    $pythonPath = Get-PythonCandidatePath -Executable 'python'
    if ($py312Path) {
        $script:PythonExecutable = $py312Path
    } elseif ($pythonPath) {
        $script:PythonExecutable = $pythonPath
    } else {
        throw 'Python 3.12+ is required. Install Python 3.12+ or make it available through py -3.12 or python.'
    }

    $version = & $script:PythonExecutable -c "import sys; print(sys.version.split()[0])"
    Write-Host "python: $version"
    $env:LAND_DD_PYTHON_EXECUTABLE = $script:PythonExecutable
}

function Invoke-PythonCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Label,

        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    & $script:PythonExecutable @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE"
    }
}

Write-Host '== bootstrap =='
Select-Python

Write-Host '== install backend dev dependencies =='
Invoke-PythonCommand -Label 'pip install backend dev dependencies' -Arguments @(
    '-m',
    'pip',
    'install',
    '-e',
    'backend[dev]'
)

New-Item -ItemType Directory -Force -Path '.\local_artifacts\object_store' | Out-Null

Write-Host 'bootstrap: ok'
Write-Host 'Next: .\scripts\verify.ps1'
Write-Host 'Run in-memory API: .\scripts\run_api.ps1 -StorageBackend memory'
Write-Host 'Run Postgres API after db-up/migrate: .\scripts\run_api.ps1 -StorageBackend postgres'
