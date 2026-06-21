#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f "./scripts/validate_qualification.py" ]]; then
  echo "required qualification artifact missing: scripts/validate_qualification.py" >&2
  exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-python}"
"$PYTHON_BIN" ./scripts/validate_qualification.py --root . --layout repo "$@"

echo "qualification validation: ok"
