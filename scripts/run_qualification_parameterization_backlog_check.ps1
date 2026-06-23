$ErrorActionPreference = "Stop"

$script = Join-Path $PSScriptRoot "qualification_parameterization_backlog_check.py"
$python = if ($env:LAND_DD_PYTHON_EXECUTABLE) { $env:LAND_DD_PYTHON_EXECUTABLE } else { "py" }

if ($python -eq "py") {
    & $python -3.12 $script --root .
} else {
    & $python $script --root .
}

if ($LASTEXITCODE -ne 0) {
    throw "Qualification parameterization backlog check failed"
}

Write-Output "qualification parameterization backlog: ok"
