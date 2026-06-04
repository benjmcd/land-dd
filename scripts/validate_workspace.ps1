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
    if ($env:LAND_DD_PYTHON_EXECUTABLE) {
        $script:PythonExecutable = $env:LAND_DD_PYTHON_EXECUTABLE
        return
    }

    $py312Path = Get-PythonCandidatePath -Executable 'py' -Prefix @('-3.12')
    $pythonPath = Get-PythonCandidatePath -Executable 'python'
    if ($py312Path) {
        $script:PythonExecutable = $py312Path
    } elseif ($pythonPath) {
        $script:PythonExecutable = $pythonPath
    } else {
        throw 'Python 3.12+ is required. Install Python 3.12+ or make it available through py -3.12 or python.'
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

Write-Host '== workspace structure =='

$required = @(
    'README.md'
    'docs/ARCHITECTURE.md'
    'docs/PRODUCT_SPEC.md'
    'docs/POSTGRES_FIRST_STORAGE.md'
    'docs/DATA_SOURCE_STRATEGY.md'
    'docs/TESTING.md'
    'backend/pyproject.toml'
    'db/migrations/0001_initial_spine.sql'
)

foreach ($path in $required) {
    if (-not (Test-Path -Path $path -PathType Leaf)) {
        throw "missing $path"
    }
}

Invoke-PythonCommand -Label 'json file check' -Arguments @('scripts/check_json_files.py')

# Structural invariant checks. These must hold or a prior fix has been regressed.
Write-Host '== structural invariants =='

$backendApp = Join-Path (Join-Path $root 'backend') 'app'

# Exactly one DeclarativeBase subclass -- all ORM models must use AppBase from db/base.py
$declarativeBases = (Get-ChildItem -Path $backendApp -Recurse -Filter '*.py' |
    Select-String -Pattern 'class\s+\w+\s*\(\s*DeclarativeBase\s*\)' |
    Measure-Object).Count
if ($declarativeBases -ne 1) {
    throw "structural invariant: expected 1 DeclarativeBase subclass in backend/app/, found $declarativeBases"
}

# Zero legacy .query() API calls -- all repos must use SQLAlchemy 2.x select() style
$legacyQuery = (Get-ChildItem -Path $backendApp -Recurse -Filter '*.py' |
    Select-String -Pattern '\.query\(' |
    Measure-Object).Count
if ($legacyQuery -ne 0) {
    throw "structural invariant: found $legacyQuery legacy .query() calls in backend/app/ -- use select() style"
}

# No agent attribution strings in tracked source files
$agentAttrib = (git -C $root grep -l 'noreply@anthropic' -- '*.py' '*.sql' 2>$null |
    Measure-Object).Count
if ($agentAttrib -ne 0) {
    throw "structural invariant: found agent attribution in $agentAttrib tracked source files"
}

Write-Host 'structural invariants: ok'
Write-Host 'workspace validation: ok'
