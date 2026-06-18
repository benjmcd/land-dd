from __future__ import annotations

import csv
import json
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any, cast

import yaml

ROOT = Path(__file__).resolve().parents[1]
STALE_SOURCE_REVIEW_AFTER_DAYS = 90

REQUIRED_FILES = (
    "config/ops_alert_rules.yaml",
    "docs/runbooks/alerting.md",
    "docs/runbooks/incident_response.md",
    "scripts/run_deployment_smoke.ps1",
    "scripts/run_backup_restore_check.ps1",
    "scripts/verify.ps1",
    "scripts/source_readiness.py",
    "scripts/alert_rules_check.py",
    "scripts/run_alert_rules_check.ps1",
    "scripts/run_alert_rules_check.sh",
    "registers/data_source_registry.csv",
)
ALLOWED_SEVERITIES = {"SEV0", "SEV1", "SEV2", "SEV3"}
REQUIRED_RULE_IDS = {
    "safety_contract_check_failed",
    "api_health_down",
    "deployment_smoke_failed",
    "db_smoke_failed",
    "backup_restore_failed",
    "metrics_endpoint_down",
    "report_queue_backlog_high",
    "report_running_stale",
    "report_failures_high",
    "live_connector_queue_backlog_high",
    "live_connector_running_stale",
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
SOURCE_REVIEW_REQUIRED_PHRASES = (
    "Source-specific upstream/update cadence:",
    "Terms/source-page review triggers:",
    "Last Checked At must remain within the 90-day repo-local freshness horizon "
    "enforced by source_readiness.py and alert_rules_check.py.",
)
SOURCE_REVIEW_FORBIDDEN_PATTERNS = (re.compile(r"\bnext\s+review\s+date\b", re.I),)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def read_text(path_text: str) -> str:
    return (ROOT / path_text).read_text(encoding="utf-8")


def require_existing(path_text: str) -> None:
    normalized = path_text.replace("\\", "/")
    require((ROOT / normalized).exists(), f"referenced alerting artifact missing: {normalized}")


def validate_required_files() -> None:
    for path_text in REQUIRED_FILES:
        require(
            (ROOT / path_text).is_file(),
            f"required alerting artifact missing: {path_text}",
        )


def load_rules() -> dict[str, Any]:
    payload = yaml.safe_load(read_text("config/ops_alert_rules.yaml"))
    require(isinstance(payload, dict), "alert rules catalog must be a mapping")
    payload = cast(dict[str, Any], payload)
    require(payload.get("schema_version") == "ops_alert_rules_v1", "unexpected alert schema")
    require(
        payload.get("incident_runbook") == "docs/runbooks/incident_response.md",
        "incident runbook mismatch",
    )
    rules = payload.get("rules")
    require(isinstance(rules, list) and bool(rules), "alert rules catalog has no rules")
    return payload


def validate_signal(rule_id: str, signal: object) -> None:
    require(isinstance(signal, dict), f"{rule_id} signal must be a mapping")
    signal = cast(dict[str, Any], signal)
    require(
        isinstance(signal.get("kind"), str) and bool(signal["kind"]),
        f"{rule_id} signal kind missing",
    )
    require(
        isinstance(signal.get("target"), str) and bool(signal["target"]),
        f"{rule_id} signal target missing",
    )


def validate_validation(rule_id: str, validation: object) -> None:
    require(isinstance(validation, dict), f"{rule_id} validation must be a mapping")
    validation = cast(dict[str, Any], validation)
    proof = validation.get("proof")
    if not isinstance(proof, str) or not proof:
        raise SystemExit(f"{rule_id} validation proof missing")

    if proof.startswith(("scripts/", "docs/", "registers/", "backend/")):
        require_existing(proof)


def validate_rules(payload: dict[str, Any]) -> None:
    rules = payload["rules"]
    require(isinstance(rules, list), "alert rules catalog has no rules")

    ids: set[str] = set()
    for rule in rules:
        require(isinstance(rule, dict), "each alert rule must be a mapping")
        rule = cast(dict[str, Any], rule)
        missing = REQUIRED_FIELDS.difference(rule)
        require(not missing, f"alert rule missing fields: {sorted(missing)}")

        rule_id = rule["id"]
        require(isinstance(rule_id, str) and bool(rule_id), "alert rule id must be a string")
        require(rule_id not in ids, f"duplicate alert rule id: {rule_id}")
        ids.add(rule_id)
        require(rule["severity"] in ALLOWED_SEVERITIES, f"{rule_id} has invalid severity")

        validate_signal(rule_id, rule["signal"])
        validate_validation(rule_id, rule["validation"])

        runbook = rule["runbook"]
        require(
            isinstance(runbook, str) and runbook.startswith("docs/runbooks/"),
            f"{rule_id} runbook invalid",
        )
        require_existing(runbook)

    missing_ids = sorted(REQUIRED_RULE_IDS - ids)
    require(not missing_ids, f"required alert rules missing: {missing_ids}")


def validate_source_readiness() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/source_readiness.py", "--priority", "Must", "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    require(
        payload.get("schema_version") == "source_readiness_v1",
        "source readiness schema mismatch",
    )
    require(int(payload.get("source_count", 0)) >= 1, "source readiness returned no Must sources")
    require(
        "ready_count" in payload and "blocked_count" in payload,
        "source readiness counts missing",
    )


def validate_source_freshness_inputs(
    *,
    registry_path: Path | None = None,
    as_of: date | None = None,
) -> None:
    registry = (
        registry_path
        if registry_path is not None
        else ROOT / "registers" / "data_source_registry.csv"
    )
    effective_as_of = as_of if as_of is not None else date.today()
    with registry.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    must_rows = [row for row in rows if row.get("MVP Priority") == "Must"]
    require(bool(must_rows), "source registry has no Must rows")
    for row in must_rows:
        source_id = row.get("Source ID", "<unknown>")
        freshness_class = row.get("Freshness Class", "")
        last_checked = row.get("Last Checked At", "")
        review_owner = row.get("Review Owner", "")
        require(bool(freshness_class.strip()), f"{source_id} missing Freshness Class")
        if freshness_class.strip().lower() != "current-effective":
            continue

        require(bool(last_checked.strip()), f"{source_id} missing Last Checked At")
        try:
            parsed_last_checked = date.fromisoformat(last_checked)
        except ValueError as exc:
            raise SystemExit(f"{source_id} invalid Last Checked At") from exc
        require(
            parsed_last_checked <= effective_as_of,
            f"{source_id} future Last Checked At",
        )
        age_days = (effective_as_of - parsed_last_checked).days
        require(
            age_days <= STALE_SOURCE_REVIEW_AFTER_DAYS,
            f"{source_id} stale Last Checked At",
        )
        require(
            _has_real_review_owner(review_owner),
            f"{source_id} missing Review Owner",
        )


def validate_must_current_effective_source_review_docs(
    *,
    registry_path: Path | None = None,
    docs_dir: Path | None = None,
) -> None:
    registry = (
        registry_path
        if registry_path is not None
        else ROOT / "registers" / "data_source_registry.csv"
    )
    source_review_docs_dir = (
        docs_dir if docs_dir is not None else ROOT / "docs" / "source-reviews"
    )
    with registry.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    must_current_effective_rows = [
        row
        for row in rows
        if row.get("MVP Priority") == "Must"
        and row.get("Freshness Class", "").strip().lower() == "current-effective"
    ]
    require(
        bool(must_current_effective_rows),
        "source registry has no Must current-effective rows",
    )

    for row in must_current_effective_rows:
        source_id = row.get("Source ID", "<unknown>")
        doc_path = source_review_docs_dir / f"{source_id.lower()}.md"
        require(
            doc_path.is_file(),
            f"{source_id} source review doc missing",
        )

        text = doc_path.read_text(encoding="utf-8")
        for pattern in SOURCE_REVIEW_FORBIDDEN_PATTERNS:
            require(
                pattern.search(text) is None,
                f"{source_id} has conflicting Next review date label",
            )
        missing_phrases = [
            phrase for phrase in SOURCE_REVIEW_REQUIRED_PHRASES if phrase not in text
        ]
        require(
            not missing_phrases,
            f"{source_id} source review missing cadence language: {missing_phrases}",
        )


def _has_real_review_owner(review_owner: str | None) -> bool:
    if review_owner is None:
        return False
    normalized = review_owner.strip().lower()
    return bool(normalized) and normalized != "unassigned"


def validate_compose_config_when_available() -> None:
    if shutil.which("docker") is None:
        print("alert rules check: docker unavailable; compose config skipped")
        return

    subprocess.run(["docker", "compose", "config", "--quiet"], check=True)


def main() -> int:
    validate_required_files()
    payload = load_rules()
    validate_rules(payload)
    validate_source_readiness()
    validate_source_freshness_inputs()
    validate_must_current_effective_source_review_docs()
    validate_compose_config_when_available()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
