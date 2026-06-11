param(
    [string]$Version = ''
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $root

$builder = '.\scripts\build_release_package.py'
if (-not (Test-Path -Path $builder -PathType Leaf)) {
    throw "required release package builder missing: scripts\build_release_package.py"
}

if ($env:PYTHON_BIN) {
    & $env:PYTHON_BIN $builder $Version
} else {
    py -3.12 $builder $Version
}

if ($LASTEXITCODE -ne 0) {
    throw "release package build failed with exit code $LASTEXITCODE"
}
