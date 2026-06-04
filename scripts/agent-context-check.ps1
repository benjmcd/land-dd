$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $root

$fail = $false

function Write-Failure {
    param([string]$Message)

    Write-Error $Message
    $script:fail = $true
}

function Test-RequiredFile {
    param([string]$Path)

    if (-not (Test-Path -Path $Path -PathType Leaf)) {
        Write-Failure "missing required file: $Path"
    }
}

function Test-MaxLines {
    param(
        [string]$Path,
        [int]$MaxLines
    )

    if (Test-Path -Path $Path -PathType Leaf) {
        $lines = ([System.IO.File]::ReadAllLines((Resolve-Path $Path))).Length
        if ($lines -gt $MaxLines) {
            Write-Failure "$Path has $lines lines; limit is $MaxLines"
        }
    }
}

Test-RequiredFile 'AGENTS.md'
Test-RequiredFile 'CLAUDE.md'
Test-RequiredFile 'MANIFEST.md'
Test-RequiredFile 'state/PROJECT_STATE.md'
Test-RequiredFile 'plans/2026-06-03-foundation-vertical-slice.md'
Test-RequiredFile 'scripts/verify.sh'

Test-MaxLines 'AGENTS.md' 140
Test-MaxLines 'CLAUDE.md' 80
Test-MaxLines 'MANIFEST.md' 160

if (Test-Path -Path 'CLAUDE.md' -PathType Leaf) {
    $claude = Get-Content -Path 'CLAUDE.md' -Raw
    if ($claude -notmatch '(?m)^@AGENTS\.md') {
        Write-Failure 'CLAUDE.md must import AGENTS.md with @AGENTS.md'
    }
}

foreach ($bad in @('CONTEXT.md', 'RULES.md', 'DEVELOPMENT.md', 'CODING_STANDARDS.md', 'AI_NOTES.md', 'SYSTEM_OVERVIEW.md')) {
    if (Test-Path -Path $bad -PathType Leaf) {
        Write-Failure "avoid root context-bloat file: $bad"
    }
}

if ($fail) {
    throw 'agent context check failed'
}

Write-Host 'agent context check: ok'
