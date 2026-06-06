#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

required_files=(
  "config/ops_alert_rules.yaml"
  "docs/runbooks/alerting.md"
  "docs/runbooks/incident_response.md"
  "scripts/run_deployment_smoke.ps1"
  "scripts/run_backup_restore_check.ps1"
  "scripts/verify.ps1"
  "scripts/source_readiness.py"
  "registers/data_source_registry.csv"
)

for file in "${required_files[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "required alerting artifact missing: $file" >&2
    exit 1
  fi
done

python - <<'PY'
from __future__ import annotations

import csv
import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

import yaml

ROOT = Path.cwd()
ALLOWED_SEVERITIES = {"SEV0", "SEV1", "SEV2", "SEV3"}
REQUIRED_RULE_IDS = {
    "safety_contract_check_failed",
    "api_health_down",
    "deployment_smoke_failed",
    "db_smoke_failed",
    "backup_restore_failed",
    "metrics_endpoint_down",
    "report_queue_backlog_high",
    "report_failures_high",
    "live_connector_queue_backlog_high",
    "live_connector_failures_high",
    "source_readiness_ready_drop",
    "source_registry_last_checked_stale",
}
REQUIRED_FIELDS = {
    "id",
    "severity",
    "signal",
    "condition",
    "window",
    "owner",
    "escalation",
    "runbook",
    "validation",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def require_existing(path_text: str) -> None:
    normalized = path_text.replace("\\", "/")
    require((ROOT / normalized).exists(), f"referenced alerting artifact missing: {normalized}")


payload = yaml.safe_load((ROOT / "config" / "ops_alert_rules.yaml").read_text(encoding="utf-8"))
require(isinstance(payload, dict), "alert rules catalog must be a mapping")
require(payload.get("schema_version") == "ops_alert_rules_v1", "unexpected alert schema")
require(payload.get("incident_runbook") == "docs/runbooks/incident_response.md", "incident runbook mismatch")
rules = payload.get("rules")
require(isinstance(rules, list) and rules, "alert rules catalog has no rules")

ids: set[str] = set()
for rule in rules:
    require(isinstance(rule, dict), "each alert rule must be a mapping")
    missing = REQUIRED_FIELDS.difference(rule)
    require(not missing, f"alert rule missing fields: {sorted(missing)}")
    rule_id = rule["id"]
    require(isinstance(rule_id, str) and rule_id, "alert rule id must be a string")
    require(rule_id not in ids, f"duplicate alert rule id: {rule_id}")
    ids.add(rule_id)
    require(rule["severity"] in ALLOWED_SEVERITIES, f"{rule_id} has invalid severity")
    signal = rule["signal"]
    require(isinstance(signal, dict), f"{rule_id} signal must be a mapping")
    require(isinstance(signal.get("kind"), str) and signal["kind"], f"{rule_id} signal kind missing")
    require(isinstance(signal.get("target"), str) and signal["target"], f"{rule_id} signal target missing")
    validation = rule["validation"]
    require(isinstance(validation, dict), f"{rule_id} validation must be a mapping")
    proof = validation.get("proof")
    require(isinstance(proof, str) and proof, f"{rule_id} validation proof missing")
    if proof.startswith(("scripts/", "docs/", "registers/", "backend/")):
        require_existing(proof)
    runbook = rule["runbook"]
    require(isinstance(runbook, str) and runbook.startswith("docs/runbooks/"), f"{rule_id} runbook invalid")
    require_existing(runbook)

missing_ids = REQUIRED_RULE_IDS.difference(ids)
require(not missing_ids, f"required alert rules missing: {sorted(missing_ids)}")

result = subprocess.run(
    [sys.executable, "scripts/source_readiness.py", "--priority", "Must", "--json"],
    check=True,
    capture_output=True,
    text=True,
)
source_readiness = json.loads(result.stdout)
require(source_readiness.get("schema_version") == "source_readiness_v1", "source readiness schema mismatch")
require(int(source_readiness.get("source_count", 0)) >= 1, "source readiness returned no Must sources")
require("ready_count" in source_readiness and "blocked_count" in source_readiness, "source readiness counts missing")

with (ROOT / "registers" / "data_source_registry.csv").open(newline="", encoding="utf-8") as handle:
    rows = list(csv.DictReader(handle))
must_rows = [row for row in rows if row.get("MVP Priority") == "Must"]
require(must_rows, "source registry has no Must rows")
for row in must_rows:
    source_id = row.get("Source ID", "<unknown>")
    freshness_class = row.get("Freshness Class", "")
    last_checked = row.get("Last Checked At", "")
    require(freshness_class.strip(), f"{source_id} missing Freshness Class")
    if row.get("Review Status") != "pending":
        require(last_checked.strip(), f"{source_id} missing Last Checked At")
        date.fromisoformat(last_checked)
PY

if command -v docker >/dev/null 2>&1; then
  docker compose config --quiet
else
  echo "alert rules check: docker unavailable; compose config skipped"
fi

echo "alert rules check: ok"
