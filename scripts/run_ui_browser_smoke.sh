#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT="$ROOT_DIR/scripts/ui_browser_smoke.mjs"

args=("$SCRIPT" "--mode" "${LAND_DD_UI_SMOKE_MODE:-headless}")

if [[ -n "${LAND_DD_UI_SMOKE_BASE_URL:-}" ]]; then
  args+=("--base-url" "$LAND_DD_UI_SMOKE_BASE_URL")
fi
if [[ -n "${LAND_DD_CHROME_PATH:-}" ]]; then
  args+=("--chrome-path" "$LAND_DD_CHROME_PATH")
fi
if [[ -n "${LAND_DD_UI_SMOKE_API_KEY:-}" ]]; then
  args+=("--api-key" "$LAND_DD_UI_SMOKE_API_KEY")
fi
if [[ -n "${LAND_DD_UI_SMOKE_REVIEWER_ID:-}" ]]; then
  args+=("--reviewer-id" "$LAND_DD_UI_SMOKE_REVIEWER_ID")
fi
if [[ -n "${LAND_DD_UI_SMOKE_REVIEWER_TOKEN:-}" ]]; then
  args+=("--reviewer-token" "$LAND_DD_UI_SMOKE_REVIEWER_TOKEN")
fi
if [[ -n "${LAND_DD_UI_SMOKE_SCREENSHOT_DIR:-}" ]]; then
  args+=("--screenshot-dir" "$LAND_DD_UI_SMOKE_SCREENSHOT_DIR")
fi

exec node "${args[@]}" "$@"
