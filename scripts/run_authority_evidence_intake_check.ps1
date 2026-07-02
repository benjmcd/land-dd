param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$CheckerArgs
)

$ErrorActionPreference = "Stop"

$script = Join-Path $PSScriptRoot "authority_evidence_intake_check.py"
$python = if ($env:LAND_DD_PYTHON_EXECUTABLE) { $env:LAND_DD_PYTHON_EXECUTABLE } else { "py" }

if ($python -eq "py") {
    & $python -3.12 $script @CheckerArgs
} else {
    & $python $script @CheckerArgs
}

if ($LASTEXITCODE -ne 0) {
    throw "Authority evidence intake check failed"
}

if ($CheckerArgs.Count -eq 0) {
    Write-Output "authority evidence intake: ok"
}
