#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f "./scripts/release_readiness_check.py" ]]; then
  echo "required release-readiness artifact missing: scripts/release_readiness_check.py" >&2
  exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-python}"
"$PYTHON_BIN" ./scripts/release_readiness_check.py

echo "release readiness check: ok"
