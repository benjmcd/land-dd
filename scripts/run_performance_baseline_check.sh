#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

VALIDATOR="scripts/performance_baseline_check.py"

if [[ ! -f "$VALIDATOR" ]]; then
  echo "performance baseline validator missing: $VALIDATOR" >&2
  exit 1
fi

"${PYTHON_BIN:-python3}" "$VALIDATOR"
echo "performance baseline check: ok"
