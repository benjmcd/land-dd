#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
PYTHON_BIN="${PYTHON_BIN:-python}"
"$PYTHON_BIN" scripts/bol_scope_auth_check.py "$@"
if [[ "$#" -eq 0 ]]; then
  echo "Bologna scope authority readiness check: ok"
fi
