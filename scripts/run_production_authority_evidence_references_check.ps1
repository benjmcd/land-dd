param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $CheckerArgs
)

$ErrorActionPreference = "Stop"

$python = Get-Command py -ErrorAction SilentlyContinue
if ($python) {
    & $python -3.12 .\scripts\production_authority_evidence_references_check.py @CheckerArgs
} else {
    python .\scripts\production_authority_evidence_references_check.py @CheckerArgs
}

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

if ($CheckerArgs.Count -eq 0) {
    Write-Host 'production authority evidence references: ok'
}
