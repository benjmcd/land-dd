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
    'AGENTS.md'
    'CLAUDE.md'
    'README.md'
    'MANIFEST.md'
    'docs/ARCHITECTURE.md'
    'docs/PRODUCT_SPEC.md'
    'docs/POSTGRES_FIRST_STORAGE.md'
    '.agent/PLANS.md'
    '.codex/config.toml'
    'plans/2026-06-03-foundation-vertical-slice.md'
    'tasks/task_queue.yaml'
    'state/PROJECT_STATE.md'
    'backend/pyproject.toml'
    'db/migrations/0001_initial_spine.sql'
)

foreach ($path in $required) {
    if (-not (Test-Path -Path $path -PathType Leaf)) {
        throw "missing $path"
    }
}

& (Join-Path $PSScriptRoot 'agent-context-check.ps1')

Invoke-PythonCommand -Label 'json file check' -Arguments @('scripts/check_json_files.py')

Write-Host 'workspace validation: ok'
