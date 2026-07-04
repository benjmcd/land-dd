param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $CheckerArgs
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    py -3.12 scripts\bol_scope_auth_check.py @CheckerArgs
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
    if ($CheckerArgs.Count -eq 0) {
        Write-Output "Bologna scope authority readiness check: ok"
    }
}
finally {
    Pop-Location
}
