param(
    [string]$Root = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$Artifact = "",
    [string]$Status = "",
    [string]$Catalog = "",
    [string]$Backlog = "",
    [string]$PythonCommand = $env:LAND_DD_PYTHON_EXECUTABLE
)

$ErrorActionPreference = 'Stop'

if (-not $PythonCommand) {
    $PythonCommand = 'python'
}

$arguments = @(
    "$PSScriptRoot\qualification_p0_evidence_check.py",
    "--root", $Root
)
if ($Artifact) { $arguments += @("--artifact", $Artifact) }
if ($Status) { $arguments += @("--status", $Status) }
if ($Catalog) { $arguments += @("--catalog", $Catalog) }
if ($Backlog) { $arguments += @("--backlog", $Backlog) }
$arguments += $args

& $PythonCommand @arguments
exit $LASTEXITCODE
