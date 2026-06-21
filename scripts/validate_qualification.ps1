param(
    [string]$Root = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$Targets = "",
    [string]$Status = "",
    [string]$Rubrics = "",
    [string]$DomainProfilesDir = "",
    [string]$SourceProfilesDir = "",
    [string]$PythonCommand = "python"
)

$ErrorActionPreference = "Stop"

$arguments = @(
    "$PSScriptRoot\validate_qualification.py",
    "--root", $Root
)
if ($Targets) { $arguments += @("--targets", $Targets) }
if ($Status) { $arguments += @("--status", $Status) }
if ($Rubrics) { $arguments += @("--rubrics", $Rubrics) }
if ($DomainProfilesDir) { $arguments += @("--domain-profiles-dir", $DomainProfilesDir) }
if ($SourceProfilesDir) { $arguments += @("--source-profiles-dir", $SourceProfilesDir) }

& $PythonCommand @arguments
exit $LASTEXITCODE
