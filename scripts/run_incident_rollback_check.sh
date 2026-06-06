#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

RUNBOOK="docs/runbooks/incident_response.md"
required_files=(
  "docs/runbooks/incident_response.md"
  "scripts/run_deployment_smoke.ps1"
  "scripts/run_deployment_smoke.sh"
  "scripts/run_backup_restore_check.ps1"
  "scripts/run_backup_restore_check.sh"
  "scripts/verify.sh"
  "scripts/source_readiness.py"
)
required_phrases=(
  "## Severity Levels"
  "## Ownership"
  "## Escalation"
  "## Rollback and Mitigation"
  "## Recovery Criteria"
  "SEV0"
  "SEV1"
  "Incident commander"
  "Deployment Rollback"
  "Database Rollback or Migration Mitigation"
  "Connector or Source Outage"
  "Queue or Report Failure"
  "run_deployment_smoke.ps1"
  "run_backup_restore_check.ps1"
  "source_readiness.py"
  "ENABLE_LIVE_CONNECTORS=false"
)

for file in "${required_files[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "required incident/rollback artifact missing: $file" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq "$phrase" "$RUNBOOK"; then
    echo "incident response runbook missing required phrase: $phrase" >&2
    exit 1
  fi
done

if command -v docker >/dev/null 2>&1; then
  docker compose config --quiet
else
  echo "incident/rollback check: docker unavailable; compose config skipped"
fi

python - <<'PY'
import json
import subprocess
import sys

result = subprocess.run(
    [sys.executable, "scripts/source_readiness.py", "--priority", "Must", "--json"],
    check=True,
    capture_output=True,
    text=True,
)
payload = json.loads(result.stdout)
if payload.get("schema_version") != "source_readiness_v1":
    raise SystemExit("source readiness JSON did not return source_readiness_v1")
if int(payload.get("source_count", 0)) < 1:
    raise SystemExit("source readiness JSON returned no sources")
PY

echo "incident/rollback check: ok"
