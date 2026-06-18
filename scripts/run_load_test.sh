#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

VALIDATE_ONLY=0
SCENARIO=""
BASE_URL_ARG=""
RESULT_DIR=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --validate-only) VALIDATE_ONLY=1 ;;
    --scenario)      SCENARIO="$2"; shift ;;
    --base-url)      BASE_URL_ARG="$2"; shift ;;
    --result-dir)    RESULT_DIR="$2"; shift ;;
    *) echo "unknown argument: $1" >&2; exit 1 ;;
  esac
  shift
done

required_files=(
  "scripts/run_load_test.ps1"
  "scripts/run_load_test.sh"
  "scripts/load_test_runner.py"
  "config/performance_baseline.yaml"
  "docs/runbooks/load_testing.md"
)

for file in "${required_files[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "load test artifact missing: $file" >&2
    exit 1
  fi
  if [[ ! -s "$file" ]]; then
    echo "load test artifact is empty: $file" >&2
    exit 1
  fi
done

echo "load test: artifact validation ok"

if [[ "$VALIDATE_ONLY" -eq 1 ]]; then
  echo "load test: --validate-only requested; skipping live HTTP requests"
  exit 0
fi

# Resolve base URL: --base-url arg > LOAD_TEST_BASE_URL env > default
if [[ -n "$BASE_URL_ARG" ]]; then
  export LOAD_TEST_BASE_URL="$BASE_URL_ARG"
elif [[ -z "${LOAD_TEST_BASE_URL:-}" ]]; then
  export LOAD_TEST_BASE_URL="http://127.0.0.1:8000"
fi

RUNNER="scripts/load_test_runner.py"
FAILED=0

if [[ -n "$SCENARIO" ]]; then
  SCENARIOS=("$SCENARIO")
else
  SCENARIOS=("sequential" "concurrent")
fi

for s in "${SCENARIOS[@]}"; do
  echo "load test: running scenario=$s base_url=$LOAD_TEST_BASE_URL"
  runner_args=(--scenario "$s" --base-url "$LOAD_TEST_BASE_URL")
  if [[ -n "$RESULT_DIR" ]]; then
    mkdir -p "$RESULT_DIR"
    runner_args+=(--json-output "$RESULT_DIR/load-test-$s.json")
  fi
  python3 "$RUNNER" "${runner_args[@]}" || FAILED=1
done

if [[ "$FAILED" -ne 0 ]]; then
  echo "load test: one or more scenarios failed" >&2
  exit 1
fi
