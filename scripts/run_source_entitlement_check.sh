#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python}"

if [[ ! -f "./scripts/source_entitlement_check.py" ]]; then
  echo "required source-entitlement artifact missing: scripts/source_entitlement_check.py" >&2
  exit 1
fi

"$PYTHON_BIN" ./scripts/source_entitlement_check.py
echo "source entitlement check: ok"
