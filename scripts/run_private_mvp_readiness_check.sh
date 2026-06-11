#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f "./scripts/private_mvp_readiness_check.py" ]]; then
  echo "required private MVP readiness artifact missing: scripts/private_mvp_readiness_check.py" >&2
  exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-python}"
"$PYTHON_BIN" ./scripts/private_mvp_readiness_check.py

echo "private MVP readiness check: ok"
