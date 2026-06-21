param(
    [string]$Root = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$Status = "",
    [string]$Targets = "",
    [string]$Catalog = "",
    [string]$Crosswalk = "",
    [string]$PythonCommand = "python",
    [int]$TimeoutSeconds = 60
)

$ErrorActionPreference = "Stop"

$arguments = @(
    "$PSScriptRoot\qualification_status_check.py",
    "--root", $Root,
    "--python-command", $PythonCommand,
    "--timeout-seconds", "$TimeoutSeconds"
)
if ($Status) { $arguments += @("--status", $Status) }
if ($Targets) { $arguments += @("--targets", $Targets) }
if ($Catalog) { $arguments += @("--catalog", $Catalog) }
if ($Crosswalk) { $arguments += @("--crosswalk", $Crosswalk) }

& $PythonCommand @arguments
exit $LASTEXITCODE
