$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $root

$validator = '.\scripts\image_publication_check.py'
if (-not (Test-Path -Path $validator -PathType Leaf)) {
    throw "required image-publication artifact missing: scripts\image_publication_check.py"
}

if ($env:PYTHON_BIN) {
    & $env:PYTHON_BIN $validator
} else {
    py -3.12 $validator
}

if ($LASTEXITCODE -ne 0) {
    throw "image publication validation failed with exit code $LASTEXITCODE"
}

Write-Host 'image publication check: ok'
