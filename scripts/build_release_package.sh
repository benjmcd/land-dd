#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f "./scripts/build_release_package.py" ]]; then
  echo "required release package builder missing: scripts/build_release_package.py" >&2
  exit 1
fi

VERSION="${1:-}"
PYTHON_BIN="${PYTHON_BIN:-python}"
"$PYTHON_BIN" ./scripts/build_release_package.py "$VERSION"
