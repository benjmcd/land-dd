param(
    [string]$PythonCommand = "python"
)

$ErrorActionPreference = "Stop"
& $PythonCommand "$PSScriptRoot\selftest_qualification_validator.py"
exit $LASTEXITCODE
