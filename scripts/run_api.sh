#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
STORAGE_BACKEND="${APP_STORAGE_BACKEND:-memory}"
BIND_ADDRESS="${BIND_ADDRESS:-127.0.0.1}"
PORT="${PORT:-8000}"
OBJECT_STORE_ROOT="${OBJECT_STORE_ROOT:-$ROOT_DIR/local_artifacts/object_store}"
RELOAD=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --memory)
      STORAGE_BACKEND="memory"
      shift
      ;;
    --postgres)
      STORAGE_BACKEND="postgres"
      shift
      ;;
    --host)
      BIND_ADDRESS="$2"
      shift 2
      ;;
    --port)
      PORT="$2"
      shift 2
      ;;
    --no-reload)
      RELOAD=0
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if [[ "$STORAGE_BACKEND" != "memory" && "$STORAGE_BACKEND" != "postgres" ]]; then
  echo "APP_STORAGE_BACKEND must be memory or postgres" >&2
  exit 2
fi
if [[ "$STORAGE_BACKEND" == "postgres" ]]; then
  USE_DB_SERVICES="true"
else
  USE_DB_SERVICES="false"
fi

reload_args=()
if [[ "$RELOAD" == "1" ]]; then
  reload_args=(--reload)
fi

echo "Starting land-diligence API on http://$BIND_ADDRESS:$PORT using $STORAGE_BACKEND storage"
cd "$ROOT_DIR/backend"
APP_STORAGE_BACKEND="$STORAGE_BACKEND" USE_DB_SERVICES="$USE_DB_SERVICES" \
  OBJECT_STORE_ROOT="$OBJECT_STORE_ROOT" PYTHONPATH=. "$PYTHON_BIN" \
  -m uvicorn app.main:app --host "$BIND_ADDRESS" --port "$PORT" "${reload_args[@]}"
