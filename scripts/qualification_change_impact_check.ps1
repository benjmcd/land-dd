param(
    [string]$Root = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$ChangeMatrix = "",
    [string]$Crosswalk = "",
    [string]$Catalog = "",
    [string]$BaseRef = "origin/main",
    [string[]]$ChangedPath = @(),
    [string]$ChangedPathsFile = "",
    [string]$PythonCommand = $env:LAND_DD_PYTHON_EXECUTABLE
)

$ErrorActionPreference = 'Stop'

if (-not $PythonCommand) {
    $PythonCommand = 'python'
}

$arguments = @(
    "$PSScriptRoot\qualification_change_impact_check.py",
    "--root", $Root,
    "--base-ref", $BaseRef
)
if ($ChangeMatrix) { $arguments += @("--change-matrix", $ChangeMatrix) }
if ($Crosswalk) { $arguments += @("--crosswalk", $Crosswalk) }
if ($Catalog) { $arguments += @("--catalog", $Catalog) }
foreach ($Path in $ChangedPath) {
    $arguments += @("--changed-path", $Path)
}
if ($ChangedPathsFile) { $arguments += @("--changed-paths-file", $ChangedPathsFile) }
$arguments += $args

& $PythonCommand @arguments
exit $LASTEXITCODE
