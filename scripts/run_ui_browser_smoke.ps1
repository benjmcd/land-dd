param(
    [string]$BaseUrl = $env:LAND_DD_UI_SMOKE_BASE_URL,
    [string]$ChromePath = $env:LAND_DD_CHROME_PATH,
    [ValidateSet('headless', 'headed', 'both')]
    [string]$Mode = $(if ($env:LAND_DD_UI_SMOKE_MODE) { $env:LAND_DD_UI_SMOKE_MODE } else { 'headless' }),
    [string]$ApiKey = $env:LAND_DD_UI_SMOKE_API_KEY,
    [string]$ReviewerId = $env:LAND_DD_UI_SMOKE_REVIEWER_ID,
    [string]$ReviewerToken = $env:LAND_DD_UI_SMOKE_REVIEWER_TOKEN,
    [string]$ScreenshotDir = $env:LAND_DD_UI_SMOKE_SCREENSHOT_DIR,
    [switch]$Json
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = Resolve-Path (Join-Path $PSScriptRoot '..')
$script = Join-Path $root 'scripts/ui_browser_smoke.mjs'
$argsList = @($script, '--mode', $Mode)

if ($BaseUrl) { $argsList += @('--base-url', $BaseUrl) }
if ($ChromePath) { $argsList += @('--chrome-path', $ChromePath) }
if ($ApiKey) { $argsList += @('--api-key', $ApiKey) }
if ($ReviewerId) { $argsList += @('--reviewer-id', $ReviewerId) }
if ($ReviewerToken) { $argsList += @('--reviewer-token', $ReviewerToken) }
if ($ScreenshotDir) { $argsList += @('--screenshot-dir', $ScreenshotDir) }
if ($Json) { $argsList += '--json' }

& node @argsList
if ($LASTEXITCODE -ne 0) {
    throw "UI browser smoke failed with exit code $LASTEXITCODE"
}
