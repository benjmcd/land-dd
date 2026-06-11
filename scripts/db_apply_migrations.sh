#!/usr/bin/env bash
set -euo pipefail

DB_URL="${DATABASE_URL_SYNC:-postgresql://land:land@localhost:5432/land_diligence}"
ROOT_DIR="$(pwd)"
USE_DOCKER_PSQL=0

convert_localhost_for_docker() {
  "${PYTHON_BIN:-python}" - "$1" <<'PY'
import sys
from urllib.parse import urlsplit, urlunsplit

url = sys.argv[1]
parts = urlsplit(url)
if parts.hostname not in {"localhost", "127.0.0.1", "::1"}:
    print(url)
    raise SystemExit(0)

host = "host.docker.internal"
netloc = host
if parts.port is not None:
    netloc = f"{host}:{parts.port}"
if parts.username is not None:
    userinfo = parts.username
    if parts.password is not None:
        userinfo = f"{userinfo}:{parts.password}"
    netloc = f"{userinfo}@{netloc}"
print(urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment)))
PY
}

PSQL_PATH="$(command -v psql || true)"
LOCAL_ARTIFACTS_PSQL="$ROOT_DIR/local_artifacts/"

if [[ -z "$PSQL_PATH" || "$PSQL_PATH" == "$LOCAL_ARTIFACTS_PSQL"* ]]; then
  if ! command -v docker >/dev/null 2>&1; then
    echo "psql not found and Docker is unavailable. Install PostgreSQL client or run migrations through your preferred DB tool." >&2
    exit 1
  fi
  USE_DOCKER_PSQL=1
fi

CLIENT_DB_URL="$DB_URL"
if [[ "$USE_DOCKER_PSQL" == "1" ]]; then
  CLIENT_DB_URL="$(convert_localhost_for_docker "$DB_URL")"
fi

apply_sql_file() {
  local file="$1"
  if [[ "$USE_DOCKER_PSQL" == "1" ]]; then
    docker run --rm -i --add-host=host.docker.internal:host-gateway postgis/postgis:16-3.4 \
      psql "$CLIENT_DB_URL" -v ON_ERROR_STOP=1 -f - < "$file"
  else
    "$PSQL_PATH" "$CLIENT_DB_URL" -v ON_ERROR_STOP=1 -f "$file"
  fi
}

for file in db/migrations/*.sql; do
  echo "Applying $file"
  apply_sql_file "$file"
done

for file in db/seeds/*.sql; do
  echo "Applying $file"
  apply_sql_file "$file"
done

echo "Migrations and seeds applied."
