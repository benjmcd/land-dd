#!/usr/bin/env bash
# Live connector smoke wrapper (bash).
#
# When RUN_LIVE_CONNECTOR_TESTS != 1: prints a SKIP message and exits 0.
# When RUN_LIVE_CONNECTOR_TESTS = 1: starts the API on port 8103 (in-memory,
#   live connectors enabled), runs the four query-bbox smoke legs for a small
#   Buncombe NC bbox, writes a timestamped transcript to local_artifacts/, and
#   stops the API before exiting.
#
# Usage:
#   ./scripts/run_live_smoke.sh
#   RUN_LIVE_CONNECTOR_TESTS=1 ./scripts/run_live_smoke.sh
#
# Environment variables honoured:
#   RUN_LIVE_CONNECTOR_TESTS  Set to 1 to execute; any other value (or absent) skips.
#   SMOKE_API_PORT            Override the API port (default 8103).
#   SMOKE_OUTPUT_DIR          Override the transcript directory (default local_artifacts).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

PORT="${SMOKE_API_PORT:-8103}"
OUTPUT_DIR="${SMOKE_OUTPUT_DIR:-$ROOT_DIR/local_artifacts}"

# ---------------------------------------------------------------------------
# Gate: skip unless explicitly opted in
# ---------------------------------------------------------------------------
if [ "${RUN_LIVE_CONNECTOR_TESTS:-}" != "1" ]; then
    echo "SKIP: live connector smoke (set RUN_LIVE_CONNECTOR_TESTS=1 to run)"
    exit 0
fi

echo "=== live connector smoke: port=$PORT output=$OUTPUT_DIR ==="

# ---------------------------------------------------------------------------
# Locate Python 3.12+
# ---------------------------------------------------------------------------
PYTHON=""
if command -v py &>/dev/null; then
    candidate="$(py -3.12 -c 'import sys; print(sys.executable)' 2>/dev/null || true)"
    if [ -n "$candidate" ]; then PYTHON="$candidate"; fi
fi
if [ -z "$PYTHON" ] && command -v python3.12 &>/dev/null; then
    PYTHON="python3.12"
fi
if [ -z "$PYTHON" ] && command -v python3 &>/dev/null; then
    if python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,12) else 1)' 2>/dev/null; then
        PYTHON="python3"
    fi
fi
if [ -z "$PYTHON" ]; then
    echo "ERROR: Python 3.12+ required (py -3.12, python3.12, or python3 with 3.12+)"
    exit 1
fi
echo "Using Python: $PYTHON"

# ---------------------------------------------------------------------------
# Start API server in background
# ---------------------------------------------------------------------------
API_URL="http://127.0.0.1:$PORT"
BACKEND_DIR="$ROOT_DIR/backend"
API_PID=""

cleanup() {
    if [ -n "$API_PID" ] && kill -0 "$API_PID" 2>/dev/null; then
        echo "Stopping API (PID $API_PID)..."
        kill "$API_PID" 2>/dev/null || true
        wait "$API_PID" 2>/dev/null || true
    fi
    unset ENABLE_LIVE_CONNECTORS
    unset PYTHONPATH
    unset OBJECT_STORE_ROOT
}
trap cleanup EXIT

export ENABLE_LIVE_CONNECTORS=true
export PYTHONPATH=.
export OBJECT_STORE_ROOT="$ROOT_DIR/local_artifacts/object_store"

echo "Starting API on $API_URL (in-memory storage, ENABLE_LIVE_CONNECTORS=true)..."
(cd "$BACKEND_DIR" && "$PYTHON" -m uvicorn app.main:app \
    --host 127.0.0.1 --port "$PORT" --no-access-log) &
API_PID=$!

# ---------------------------------------------------------------------------
# Run smoke driver
# ---------------------------------------------------------------------------
SMOKE_EXIT=0
"$PYTHON" "$SCRIPT_DIR/run_live_smoke.py" \
    --api-url "$API_URL" \
    --output-dir "$OUTPUT_DIR" || SMOKE_EXIT=$?

if [ "$SMOKE_EXIT" -ne 0 ]; then
    echo "live connector smoke FAILED (exit $SMOKE_EXIT)"
    exit $SMOKE_EXIT
fi
echo "live connector smoke PASSED"
exit 0
