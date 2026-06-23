$ErrorActionPreference = "Stop"

$script = Join-Path $PSScriptRoot "bologna_owner_answer_intake_check.py"
$python = if ($env:LAND_DD_PYTHON_EXECUTABLE) { $env:LAND_DD_PYTHON_EXECUTABLE } else { "py" }

if ($python -eq "py") {
    & $python -3.12 $script
} else {
    & $python $script
}

if ($LASTEXITCODE -ne 0) {
    throw "Bologna owner answer intake check failed"
}

Write-Output "Bologna owner answer intake check: ok"
