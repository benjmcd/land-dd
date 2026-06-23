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

function New-VerifyLogPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$LogName
    )

    $logDir = Join-Path $root 'local_artifacts'
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
    $logPath = Join-Path $logDir $LogName
    if (-not (Test-Path -Path $logPath -PathType Leaf)) {
        return $logPath
    }

    $stamp = Get-Date -Format 'yyyyMMddTHHmmssfffZ'
    $name = [System.IO.Path]::GetFileNameWithoutExtension($LogName)
    $extension = [System.IO.Path]::GetExtension($LogName)
    return (Join-Path $logDir "$name-$stamp$extension")
}

function Invoke-PythonCommandWithLog {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Label,

        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,

        [Parameter(Mandatory = $true)]
        [string]$LogName
    )

    $logPath = New-VerifyLogPath -LogName $LogName

    $previousErrorActionPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        & $script:PythonExecutable @Arguments *> $logPath
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
    if (Test-Path -Path $logPath -PathType Leaf) {
        Get-Content -Path $logPath | ForEach-Object { Write-Host $_ }
    }
    Write-Host "$Label log: $logPath"
    if ($exitCode -ne 0) {
        Write-Host "$Label failed with exit code $exitCode"
    }
    return [int]$exitCode
}

Select-Python

Write-Host '== workspace validation =='
& (Join-Path $PSScriptRoot 'validate_workspace.ps1')

Write-Host '== qualification selftest =='
Invoke-PythonCommand `
    -Label 'qualification selftest' `
    -Arguments @('scripts/selftest_qualification_validator.py')

Write-Host '== qualification validation =='
Invoke-PythonCommand `
    -Label 'qualification validation' `
    -Arguments @('scripts/validate_qualification.py', '--root', '.', '--layout', 'repo')

Write-Host '== qualification status =='
Invoke-PythonCommand `
    -Label 'qualification status' `
    -Arguments @('scripts/qualification_status_check.py', '--root', '.', '--python-command', $script:PythonExecutable)

Write-Host '== qualification change impact =='
Invoke-PythonCommand `
    -Label 'qualification change impact' `
    -Arguments @('scripts/qualification_change_impact_check.py', '--root', '.')

Write-Host '== qualification P0 auto evidence =='
Invoke-PythonCommand `
    -Label 'qualification P0 auto evidence' `
    -Arguments @('scripts/qualification_p0_evidence_check.py', '--root', '.')

Write-Host '== qualification parameterization backlog =='
Invoke-PythonCommand `
    -Label 'qualification parameterization backlog' `
    -Arguments @('scripts/qualification_parameterization_backlog_check.py', '--root', '.')

if ($env:RUN_DB_SMOKE -eq '1') {
    Write-Host '== db migration =='
    & (Join-Path $PSScriptRoot 'db_apply_migrations.ps1')
}

Write-Host '== backend tests =='
$backendTestsExitCode = 0
$hadPythonPath = Test-Path Env:PYTHONPATH
$previousPythonPath = if ($hadPythonPath) { $env:PYTHONPATH } else { '' }
Push-Location backend
try {
    $env:PYTHONPATH = '.'
    $backendTestsExitCode = Invoke-PythonCommandWithLog `
        -Label 'backend tests' `
        -Arguments @('-m', 'pytest', '-q') `
        -LogName 'backend-pytest.log'

    if ($backendTestsExitCode -ne 0) {
        Write-Host "backend tests failed; skipping lint and typecheck"
    } elseif (Get-Command ruff -ErrorAction SilentlyContinue) {
        Write-Host '== backend lint =='
        Invoke-NativeCommand -Label 'backend lint' -Command { ruff check . }
    } else {
        Write-Host 'ruff not installed; skipping lint'
    }

    if ($backendTestsExitCode -eq 0) {
        & $script:PythonExecutable -m mypy --version *> $null
        if ($LASTEXITCODE -eq 0) {
            Write-Host '== backend typecheck =='
            Invoke-PythonCommand -Label 'backend typecheck' -Arguments @('-m', 'mypy', 'app', 'tests')
        } else {
            Write-Host 'mypy not installed for the selected Python; skipping typecheck'
        }
    }
}
finally {
    Pop-Location
    if ($hadPythonPath) {
        $env:PYTHONPATH = $previousPythonPath
    } else {
        Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
    }
}

if ($backendTestsExitCode -ne 0) {
    exit $backendTestsExitCode
}

if ($env:RUN_DB_SMOKE -eq '1') {
    Write-Host '== db smoke =='
    Invoke-PythonCommand -Label 'db smoke' -Arguments @('scripts/db_smoke_check.py')
} else {
    Write-Host "db smoke skipped; set RUN_DB_SMOKE=1 after 'make db-up'"
}

Write-Host 'verify: ok'
