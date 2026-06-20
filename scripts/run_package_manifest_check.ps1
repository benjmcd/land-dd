param(
    [Parameter(Mandatory=$true)]
    [string]$Manifest
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $root

$validator = '.\scripts\package_manifest_check.py'
if (-not (Test-Path -Path $validator -PathType Leaf)) {
    throw "required package manifest checker missing: scripts\package_manifest_check.py"
}

if ($env:PYTHON_BIN) {
    & $env:PYTHON_BIN $validator $Manifest
} else {
    py -3.12 $validator $Manifest
}

if ($LASTEXITCODE -ne 0) {
    throw "package manifest validation failed with exit code $LASTEXITCODE"
}
