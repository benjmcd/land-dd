#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python}"

if [[ ! -f "./scripts/bologna_preflight_check.py" ]]; then
  echo "required Bologna preflight artifact missing: scripts/bologna_preflight_check.py" >&2
  exit 1
fi

"$PYTHON_BIN" ./scripts/bologna_preflight_check.py
echo "Bologna preflight check: ok"
