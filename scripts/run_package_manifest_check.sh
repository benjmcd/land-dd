#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ $# -ne 1 ]]; then
  echo "usage: scripts/run_package_manifest_check.sh <manifest-path>" >&2
  exit 2
fi

if [[ ! -f "./scripts/package_manifest_check.py" ]]; then
  echo "required package manifest checker missing: scripts/package_manifest_check.py" >&2
  exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-python}"
"$PYTHON_BIN" ./scripts/package_manifest_check.py "$1"
