#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PROJECT_NAME="${DEPLOYMENT_SMOKE_PROJECT:-land-diligence-smoke}"
BACKEND_PORT="${DEPLOYMENT_SMOKE_BACKEND_PORT:-18080}"
DB_PORT_VALUE="${DEPLOYMENT_SMOKE_DB_PORT:-55432}"
BASE_URL="http://127.0.0.1:${BACKEND_PORT}"

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "$1 is required for deployment smoke." >&2
    exit 1
  fi
}

compose() {
  docker compose --project-name "$PROJECT_NAME" "$@"
}

apply_sql_file() {
  local file="$1"
  echo "Applying $file"
  compose exec -T db psql -U land -d land_diligence -v ON_ERROR_STOP=1 -f - < "$file"
}

db_start_time() {
  compose exec -T db psql -U land -d land_diligence -At -v ON_ERROR_STOP=1 \
    -c "SELECT pg_postmaster_start_time();" 2>/dev/null || true
}

wait_for_db() {
  local deadline=$((SECONDS + 90))
  local first_start_time second_start_time
  while true; do
    if compose exec -T db pg_isready -U land -d land_diligence >/dev/null 2>&1; then
      first_start_time="$(db_start_time)"
      if [[ -n "$first_start_time" ]]; then
        sleep 5
        if compose exec -T db pg_isready -U land -d land_diligence >/dev/null 2>&1; then
          second_start_time="$(db_start_time)"
          if [[ -n "$second_start_time" && "$first_start_time" == "$second_start_time" ]]; then
            return 0
          fi
          echo "db start time changed while waiting for deployment smoke; waiting for final startup" >&2
        fi
      fi
    fi
    if (( SECONDS >= deadline )); then
      echo "db did not become ready for deployment smoke" >&2
      return 1
    fi
    sleep 2
  done
}

wait_for_backend() {
  local deadline=$((SECONDS + 90))
  until python - "$BASE_URL/health" <<'PY'
import json
import sys
import urllib.request

try:
    with urllib.request.urlopen(sys.argv[1], timeout=3) as response:
        body = json.load(response)
except Exception:
    raise SystemExit(1)
raise SystemExit(0 if body.get("status") == "ok" else 1)
PY
  do
    if (( SECONDS >= deadline )); then
      echo "backend did not become healthy at ${BASE_URL}/health" >&2
      return 1
    fi
    sleep 2
  done
}

json_get() {
  python - "$1" <<'PY'
import json
import sys
import urllib.request

with urllib.request.urlopen(sys.argv[1], timeout=10) as response:
    print(json.dumps(json.load(response)))
PY
}

reviewer_json_get() {
  python - "$1" <<'PY'
import json
import sys
import urllib.request

request = urllib.request.Request(
    sys.argv[1],
    headers={
        "X-Reviewer-Id": "fixture-reviewer",
        "X-Reviewer-Token": "fixture-token-123",
    },
)
with urllib.request.urlopen(request, timeout=10) as response:
    print(json.dumps(json.load(response)))
PY
}

json_post() {
  python - "$1" "$2" <<'PY'
import json
import sys
import urllib.request

request = urllib.request.Request(
    sys.argv[1],
    data=sys.argv[2].encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(request, timeout=10) as response:
    print(json.dumps(json.load(response)))
PY
}

json_field() {
  python - "$1" "$2" <<'PY'
import json
import sys

data = json.loads(sys.argv[1])
value = data
for part in sys.argv[2].split("."):
    value = value[part]
print(value)
PY
}

wait_for_report() {
  local report_run_id="$1"
  local deadline=$((SECONDS + 90))
  local report status
  while true; do
    report="$(json_get "${BASE_URL}/report-runs/${report_run_id}")"
    status="$(json_field "$report" status)"
    if [[ "$status" == "succeeded" ]]; then
      echo "$report"
      return 0
    fi
    if [[ "$status" == "failed" ]]; then
      echo "report run failed during deployment smoke: $report_run_id" >&2
      return 1
    fi
    if (( SECONDS >= deadline )); then
      echo "report run did not finish during deployment smoke: $report_run_id" >&2
      return 1
    fi
    sleep 2
  done
}

cleanup() {
  if [[ "${DEPLOYMENT_SMOKE_KEEP_SERVICES:-}" != "1" ]]; then
    compose down || true
  else
    echo "deployment smoke: preserved Compose project $PROJECT_NAME"
  fi
}

require_command docker
require_command python
trap cleanup EXIT

export DB_PORT="$DB_PORT_VALUE"
export BACKEND_PORT
export COMPOSE_USE_DB_SERVICES=true
export ENABLE_LIVE_CONNECTORS=false
export ENABLE_METRICS=true
export REQUIRE_API_KEY=false
export ENABLE_RATE_LIMIT=false
export APP_ENV=local

echo "deployment smoke: project=$PROJECT_NAME backend=$BASE_URL db-port=$DB_PORT_VALUE"
compose build backend
compose up -d db
wait_for_db

for file in db/migrations/*.sql; do
  apply_sql_file "$file"
done
for file in db/seeds/*.sql; do
  apply_sql_file "$file"
done

compose up -d backend
wait_for_backend

version="$(json_get "${BASE_URL}/version")"
[[ -n "$(json_field "$version" version)" ]]
metrics="$(json_get "${BASE_URL}/metrics")"
[[ "$(json_field "$metrics" schema_version)" == "runtime_metrics_v1" ]]
queue_health="$(reviewer_json_get "${BASE_URL}/operations/queue-health")"
[[ "$(json_field "$queue_health" schema_version)" == "operations_queue_health_v1" ]]
for queue_name in report_jobs live_connector_jobs; do
  json_field "$queue_health" "${queue_name}.oldest_running_age_seconds" >/dev/null
  json_field "$queue_health" "${queue_name}.oldest_running_job_id" >/dev/null
  json_field "$queue_health" "${queue_name}.stale_running" >/dev/null
  [[ "$(json_field "$queue_health" "${queue_name}.stale_running_threshold_seconds")" == "900" ]]
done
recovery_preview="$(reviewer_json_get "${BASE_URL}/operations/recovery-preview")"
[[ "$(json_field "$recovery_preview" schema_version)" == "operations_recovery_preview_v1" ]]
[[ "$(json_field "$recovery_preview" stale_running_threshold_seconds)" == "900" ]]
for queue_name in report_jobs live_connector_jobs; do
  json_field "$recovery_preview" "${queue_name}.failed_count" >/dev/null
  json_field "$recovery_preview" "${queue_name}.stale_running_count" >/dev/null
  json_field "$recovery_preview" "${queue_name}.queued_count" >/dev/null
  json_field "$recovery_preview" "${queue_name}.failed_candidates_truncated" >/dev/null
  json_field "$recovery_preview" "${queue_name}.stale_running_candidates_truncated" >/dev/null
  json_field "$recovery_preview" "${queue_name}.candidates" >/dev/null
done

area_body='{"label":"deployment smoke polygon","geom_source":"deployment-smoke","geom_geojson":{"type":"Polygon","coordinates":[[[-77.10,38.80],[-77.00,38.80],[-77.00,38.90],[-77.10,38.90],[-77.10,38.80]]]}}'
area="$(json_post "${BASE_URL}/areas" "$area_body")"
area_id="$(json_field "$area" area_id)"
report_job="$(json_post "${BASE_URL}/report-runs" "{\"area_id\":\"${area_id}\",\"intent_code\":\"rural_land_purchase\"}")"
report_run_id="$(json_field "$report_job" report_run_id)"
report="$(wait_for_report "$report_run_id")"
[[ -n "$(json_field "$report" status)" ]]
[[ "$(json_field "$report" status)" == "succeeded" ]]

python ./scripts/ui_runtime_smoke.py \
  --base-url "$BASE_URL" \
  --reviewer-id fixture-reviewer \
  --reviewer-token fixture-token-123 \
  --operator-case-id BUN-slope \
  --compare-same-area \
  --expect-artifact-persistence postgres+object_store

echo "deployment smoke: ok"
