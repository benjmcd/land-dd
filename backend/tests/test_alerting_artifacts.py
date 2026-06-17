from __future__ import annotations

import csv
import importlib
from pathlib import Path
from typing import Any, cast

yaml = cast(Any, importlib.import_module("yaml"))

REPO_ROOT = Path(__file__).resolve().parents[2]
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


def test_alert_rule_catalog_covers_l10_failure_and_stale_data_signals() -> None:
    catalog = yaml.safe_load(
        (REPO_ROOT / "config" / "ops_alert_rules.yaml").read_text(encoding="utf-8"),
    )

    assert catalog["schema_version"] == "ops_alert_rules_v1"
    assert catalog["incident_runbook"] == "docs/runbooks/incident_response.md"

    rules = catalog["rules"]
    rule_ids = {rule["id"] for rule in rules}
    assert REQUIRED_RULE_IDS.issubset(rule_ids)

    for rule in rules:
        assert rule["severity"] in {"SEV0", "SEV1", "SEV2", "SEV3"}
        assert rule["condition"]
        assert rule["window"]
        assert rule["owner"]
        assert rule["escalation"]
        assert rule["runbook"].startswith("docs/runbooks/")
        assert "kind" in rule["signal"]
        assert "target" in rule["signal"]
        assert "proof" in rule["validation"]


def test_alerting_artifacts_reference_existing_runbooks_and_proofs() -> None:
    catalog = yaml.safe_load(
        (REPO_ROOT / "config" / "ops_alert_rules.yaml").read_text(encoding="utf-8"),
    )

    for rule in catalog["rules"]:
        runbook_path = REPO_ROOT / rule["runbook"]
        assert runbook_path.is_file()
        proof = rule["validation"]["proof"]
        if proof.startswith(("backend/", "docs/", "registers/", "scripts/")):
            assert (REPO_ROOT / proof).exists()

    assert (REPO_ROOT / "scripts" / "alert_rules_check.py").is_file()
    assert (REPO_ROOT / "scripts" / "run_alert_rules_check.ps1").is_file()
    assert (REPO_ROOT / "scripts" / "run_alert_rules_check.sh").is_file()


def test_alerting_runbook_names_validation_and_incident_response() -> None:
    runbook = (REPO_ROOT / "docs" / "runbooks" / "alerting.md").read_text(
        encoding="utf-8",
    )

    for phrase in (
        "config/ops_alert_rules.yaml",
        "run_alert_rules_check.ps1",
        "scripts/alert_rules_check.py",
        "docs/runbooks/incident_response.md",
        "/operations/queue-health",
        "source_readiness.py --priority Must --json",
        "stale_running",
        "Last Checked At",
        "Known Limits",
    ):
        assert phrase in runbook


def test_must_source_rows_have_freshness_metadata_for_alerting() -> None:
    with (REPO_ROOT / "registers" / "data_source_registry.csv").open(
        newline="",
        encoding="utf-8",
    ) as handle:
        rows = list(csv.DictReader(handle))

    must_rows = [row for row in rows if row["MVP Priority"] == "Must"]
    assert must_rows
    for row in must_rows:
        assert row["Freshness Class"]
        if row["Review Status"] != "pending":
            assert row["Last Checked At"]


def test_alerting_wrappers_delegate_to_shared_validator() -> None:
    for script_name in ("run_alert_rules_check.ps1", "run_alert_rules_check.sh"):
        script = (REPO_ROOT / "scripts" / script_name).read_text(encoding="utf-8")

        assert "alert_rules_check.py" in script
