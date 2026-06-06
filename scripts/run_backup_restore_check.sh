#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -d "$ROOT/local_artifacts" ]]; then
  export PATH="$ROOT/local_artifacts:$PATH"
fi

SOURCE_DB_URL="${DATABASE_URL_SYNC:-postgresql://land:land@localhost:5432/land_diligence}"
RESTORE_DB_NAME="${RESTORE_CHECK_DB_NAME:-land_diligence_restore_check}"

if [[ ! "$RESTORE_DB_NAME" =~ ^land_diligence_restore_check[a-zA-Z0-9_]*$ ]]; then
  echo "RESTORE_CHECK_DB_NAME must start with land_diligence_restore_check and contain only letters, digits, or underscores." >&2
  exit 1
fi

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "$1 not found. Install PostgreSQL client or use the local_artifacts wrapper." >&2
    exit 1
  fi
}

replace_database_name() {
  python - "$1" "$2" <<'PY'
from urllib.parse import urlsplit, urlunsplit
import sys

url, database_name = sys.argv[1], sys.argv[2]
parts = urlsplit(url)
print(urlunsplit((parts.scheme, parts.netloc, f"/{database_name}", parts.query, parts.fragment)))
PY
}

localhost_for_docker() {
  python - "$1" <<'PY'
from urllib.parse import urlsplit, urlunsplit
import sys

url = sys.argv[1]
parts = urlsplit(url)
host = parts.hostname
netloc = parts.netloc
if host in {"localhost", "127.0.0.1", "::1"}:
    userinfo = ""
    if parts.username:
        userinfo = parts.username
        if parts.password:
            userinfo += f":{parts.password}"
        userinfo += "@"
    port = f":{parts.port}" if parts.port else ""
    netloc = f"{userinfo}host.docker.internal{port}"
print(urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment)))
PY
}

quote_pg_identifier() {
  local escaped="${1//\"/\"\"}"
  printf '"%s"' "$escaped"
}

USE_DOCKER_PG_DUMP=0
if ! command -v pg_dump >/dev/null 2>&1; then
  require_command docker
  USE_DOCKER_PG_DUMP=1
fi
USE_DOCKER_PSQL="$USE_DOCKER_PG_DUMP"
if [[ "$USE_DOCKER_PSQL" == "0" ]] && ! command -v psql >/dev/null 2>&1; then
  require_command docker
  USE_DOCKER_PSQL=1
fi

ADMIN_DB_URL="${DATABASE_ADMIN_URL_SYNC:-$(replace_database_name "$SOURCE_DB_URL" postgres)}"
RESTORE_DB_URL="${RESTORE_DATABASE_URL_SYNC:-$(replace_database_name "$SOURCE_DB_URL" "$RESTORE_DB_NAME")}"
DUMP_DIR="$ROOT/local_artifacts/backup_restore"
DUMP_PATH="${RESTORE_CHECK_DUMP_PATH:-$DUMP_DIR/restore-check.sql}"
QUOTED_RESTORE_DB="$(quote_pg_identifier "$RESTORE_DB_NAME")"
ADMIN_CLIENT_DB_URL="$ADMIN_DB_URL"
RESTORE_CLIENT_DB_URL="$RESTORE_DB_URL"
if [[ "$USE_DOCKER_PSQL" == "1" ]]; then
  ADMIN_CLIENT_DB_URL="$(localhost_for_docker "$ADMIN_DB_URL")"
  RESTORE_CLIENT_DB_URL="$(localhost_for_docker "$RESTORE_DB_URL")"
fi

psql_command() {
  local url="$1"
  local sql="$2"
  if [[ "$USE_DOCKER_PSQL" == "1" ]]; then
    docker run --rm postgis/postgis:16-3.4 \
      psql "$url" -v ON_ERROR_STOP=1 -c "$sql"
  else
    psql "$url" -v ON_ERROR_STOP=1 -c "$sql"
  fi
}

psql_file() {
  local url="$1"
  local file="$2"
  if [[ "$USE_DOCKER_PSQL" == "1" ]]; then
    docker run -i --rm postgis/postgis:16-3.4 \
      psql "$url" -v ON_ERROR_STOP=1 < "$file"
  else
    psql "$url" -v ON_ERROR_STOP=1 -f "$file"
  fi
}

mkdir -p "$DUMP_DIR"

cleanup() {
  if [[ "${RESTORE_CHECK_KEEP_DB:-}" != "1" ]]; then
    psql_command "$ADMIN_CLIENT_DB_URL" \
      "DROP DATABASE IF EXISTS $QUOTED_RESTORE_DB WITH (FORCE)" >/dev/null
  else
    echo "backup/restore check: preserved restore database $RESTORE_DB_NAME"
  fi
}
trap cleanup EXIT

echo "backup/restore check: source=$SOURCE_DB_URL"
echo "backup/restore check: restore database=$RESTORE_DB_NAME"
echo "backup/restore check: dump path=$DUMP_PATH"

psql_command "$ADMIN_CLIENT_DB_URL" \
  "DROP DATABASE IF EXISTS $QUOTED_RESTORE_DB WITH (FORCE)"
psql_command "$ADMIN_CLIENT_DB_URL" \
  "CREATE DATABASE $QUOTED_RESTORE_DB"
if [[ "$USE_DOCKER_PG_DUMP" == "1" ]]; then
  DOCKER_SOURCE_DB_URL="$(localhost_for_docker "$SOURCE_DB_URL")"
  docker run --rm postgis/postgis:16-3.4 \
    pg_dump "$DOCKER_SOURCE_DB_URL" --format=plain --no-owner --no-privileges \
    > "$DUMP_PATH"
else
  pg_dump "$SOURCE_DB_URL" --format=plain --no-owner --no-privileges --file "$DUMP_PATH"
fi
psql_file "$RESTORE_CLIENT_DB_URL" "$DUMP_PATH"

DATABASE_URL_SYNC="$RESTORE_DB_URL" python scripts/db_smoke_check.py

echo "backup/restore check: ok"
