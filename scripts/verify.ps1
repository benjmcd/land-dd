$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $root

$localArtifacts = Join-Path $root 'local_artifacts'
if (Test-Path -Path $localArtifacts -PathType Container) {
    $env:PATH = "$localArtifacts;$env:PATH"
}

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

Select-Python

Write-Host '== workspace validation =='
& (Join-Path $PSScriptRoot 'validate_workspace.ps1')

if ($env:RUN_DB_SMOKE -eq '1') {
    Write-Host '== db migration + seed =='
    & (Join-Path $PSScriptRoot 'db_apply_migrations.ps1')
}

Write-Host '== backend tests =='
Push-Location backend
try {
    $env:PYTHONPATH = '.'
    Invoke-PythonCommand -Label 'backend tests' -Arguments @('-m', 'pytest', '-q')

    if (Get-Command ruff -ErrorAction SilentlyContinue) {
        Write-Host '== backend lint =='
        Invoke-NativeCommand -Label 'backend lint' -Command { ruff check . }
    } else {
        Write-Host 'ruff not installed; skipping lint'
    }

    if (Get-Command mypy -ErrorAction SilentlyContinue) {
        Write-Host '== backend typecheck =='
        Invoke-NativeCommand -Label 'backend typecheck' -Command { mypy app tests }
    } else {
        Write-Host 'mypy not installed; skipping typecheck'
    }
}
finally {
    Pop-Location
    Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
}

if ($env:RUN_DB_SMOKE -eq '1') {
    Write-Host '== db smoke =='
    Invoke-PythonCommand -Label 'db smoke' -Arguments @('scripts/db_smoke_check.py')
} else {
    Write-Host "db smoke skipped; set RUN_DB_SMOKE=1 after 'make db-up'"
}

Write-Host 'verify: ok'
