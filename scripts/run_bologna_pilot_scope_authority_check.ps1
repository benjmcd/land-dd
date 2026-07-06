param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $CheckerArgs
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    py -3.12 .\scripts\bologna_pilot_scope_authority_check.py @CheckerArgs
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
    if ($CheckerArgs.Count -eq 0) {
        Write-Host "Bologna pilot scope authority check: ok"
    }
}
finally {
    Pop-Location
}
