from __future__ import annotations

import csv
import importlib
import importlib.util
import sys
from datetime import date
from pathlib import Path
from types import ModuleType
from typing import Any, cast

import pytest

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


def _load_alert_rules_check_module() -> ModuleType:
    module_path = REPO_ROOT / "scripts" / "alert_rules_check.py"
    spec = importlib.util.spec_from_file_location("alert_rules_check", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_source_readiness_module() -> ModuleType:
    module_path = REPO_ROOT / "scripts" / "source_readiness.py"
    spec = importlib.util.spec_from_file_location("source_readiness", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_registry_with_must_row(
    tmp_path: Path,
    *,
    overrides: dict[str, str],
) -> Path:
    registry_path = REPO_ROOT / "registers" / "data_source_registry.csv"
    with registry_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    row = next(row for row in rows if row["Source ID"] == "DS-001")
    updated_row = {**row, **overrides}
    output_path = tmp_path / "registry.csv"
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(updated_row))
        writer.writeheader()
        writer.writerow(updated_row)
    return output_path


def _write_registry_with_rows(
    tmp_path: Path,
    rows: list[dict[str, str]],
) -> Path:
    registry_path = REPO_ROOT / "registers" / "data_source_registry.csv"
    with registry_path.open(newline="", encoding="utf-8") as handle:
        fieldnames = list(cast(Any, csv.DictReader(handle)).fieldnames or [])

    output_path = tmp_path / "registry.csv"
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
    return output_path


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


def test_stale_source_review_horizon_matches_readiness_guard() -> None:
    catalog = yaml.safe_load(
        (REPO_ROOT / "config" / "ops_alert_rules.yaml").read_text(encoding="utf-8"),
    )
    rule = next(
        rule
        for rule in catalog["rules"]
        if rule["id"] == "source_registry_last_checked_stale"
    )
    alert_rules_check = _load_alert_rules_check_module()
    source_readiness = _load_source_readiness_module()

    assert "older than 90 days" in rule["condition"]
    assert alert_rules_check.STALE_SOURCE_REVIEW_AFTER_DAYS == 90
    assert source_readiness.STALE_AFTER_DAYS == 90
    assert (
        alert_rules_check.STALE_SOURCE_REVIEW_AFTER_DAYS
        == source_readiness.STALE_AFTER_DAYS
    )


def test_alert_rule_source_freshness_validator_accepts_current_reviews(
    tmp_path: Path,
) -> None:
    alert_rules_check = _load_alert_rules_check_module()
    registry_path = _write_registry_with_must_row(
        tmp_path,
        overrides={
            "Freshness Class": "current-effective",
            "Last Checked At": "2026-06-05",
            "Review Owner": "operator",
            "Review Status": "approved-with-restrictions",
        },
    )

    alert_rules_check.validate_source_freshness_inputs(
        registry_path=registry_path,
        as_of=date(2026, 6, 18),
    )


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"Last Checked At": "2026-03-19"}, "stale Last Checked At"),
        ({"Last Checked At": ""}, "missing Last Checked At"),
        ({"Last Checked At": "not-a-date"}, "invalid Last Checked At"),
        ({"Last Checked At": "2026-06-19"}, "future Last Checked At"),
        ({"Review Owner": "unassigned"}, "missing Review Owner"),
        ({"Review Owner": " "}, "missing Review Owner"),
    ],
)
def test_alert_rule_source_freshness_validator_fails_closed_for_review_drift(
    tmp_path: Path,
    overrides: dict[str, str],
    expected: str,
) -> None:
    alert_rules_check = _load_alert_rules_check_module()
    registry_path = _write_registry_with_must_row(
        tmp_path,
        overrides={
            "Freshness Class": "current-effective",
            "Last Checked At": "2026-06-05",
            "Review Owner": "operator",
            "Review Status": "approved-with-restrictions",
            **overrides,
        },
    )

    with pytest.raises(SystemExit, match=expected):
        alert_rules_check.validate_source_freshness_inputs(
            registry_path=registry_path,
            as_of=date(2026, 6, 18),
        )


def test_source_review_cadence_validator_accepts_canonical_current_effective_docs(
    tmp_path: Path,
) -> None:
    alert_rules_check = _load_alert_rules_check_module()
    registry_path = _write_registry_with_rows(
        tmp_path,
        rows=[
            {
                "Source ID": "DS-001",
                "MVP Priority": "Must",
                "Freshness Class": "current-effective",
                "Review Status": "approved-with-restrictions",
            },
            {
                "Source ID": "DS-017",
                "MVP Priority": "Must",
                "Freshness Class": "unreviewed",
                "Review Status": "pending",
            },
        ],
    )
    docs_dir = tmp_path / "source-reviews"
    docs_dir.mkdir()
    (docs_dir / "ds-001.md").write_text(
        "\n".join(
            [
                "# DS-001",
                "- Source-specific upstream/update cadence: dynamic.",
                "- Terms/source-page review triggers: review earlier if source pages change.",
                "- Local readiness freshness: Last Checked At must remain within the "
                "90-day repo-local freshness horizon enforced by source_readiness.py "
                "and alert_rules_check.py.",
            ],
        ),
        encoding="utf-8",
    )
    (docs_dir / "ds-017.md").write_text(
        "\n".join(
            [
                "# DS-017",
                "- Next review date: blocked until vendor authority changes.",
            ],
        ),
        encoding="utf-8",
    )

    alert_rules_check.validate_must_current_effective_source_review_docs(
        registry_path=registry_path,
        docs_dir=docs_dir,
    )


def test_source_review_cadence_validator_rejects_next_review_date_label(
    tmp_path: Path,
) -> None:
    alert_rules_check = _load_alert_rules_check_module()
    registry_path = _write_registry_with_rows(
        tmp_path,
        rows=[
            {
                "Source ID": "DS-001",
                "MVP Priority": "Must",
                "Freshness Class": "current-effective",
                "Review Status": "approved-with-restrictions",
            },
        ],
    )
    docs_dir = tmp_path / "source-reviews"
    docs_dir.mkdir()
    (docs_dir / "ds-001.md").write_text(
        "\n".join(
            [
                "# DS-001",
                "- Source-specific upstream/update cadence: dynamic.",
                "- Terms/source-page review triggers: review earlier if source pages change.",
                "- Local readiness freshness: Last Checked At must remain within the "
                "90-day repo-local freshness horizon enforced by source_readiness.py "
                "and alert_rules_check.py.",
                "**Next review date:** 2027-06-05.",
            ],
        ),
        encoding="utf-8",
    )

    with pytest.raises(SystemExit, match="DS-001 has conflicting Next review date"):
        alert_rules_check.validate_must_current_effective_source_review_docs(
            registry_path=registry_path,
            docs_dir=docs_dir,
        )


def test_source_review_cadence_validator_rejects_missing_current_effective_doc(
    tmp_path: Path,
) -> None:
    alert_rules_check = _load_alert_rules_check_module()
    registry_path = _write_registry_with_rows(
        tmp_path,
        rows=[
            {
                "Source ID": "DS-001",
                "MVP Priority": "Must",
                "Freshness Class": "current-effective",
                "Review Status": "approved-with-restrictions",
            },
        ],
    )
    docs_dir = tmp_path / "source-reviews"
    docs_dir.mkdir()

    with pytest.raises(SystemExit, match="DS-001 source review doc missing"):
        alert_rules_check.validate_must_current_effective_source_review_docs(
            registry_path=registry_path,
            docs_dir=docs_dir,
        )


def test_current_must_source_reviews_name_repo_local_freshness_boundary() -> None:
    alert_rules_check = _load_alert_rules_check_module()

    alert_rules_check.validate_must_current_effective_source_review_docs()


def test_alerting_wrappers_delegate_to_shared_validator() -> None:
    for script_name in ("run_alert_rules_check.ps1", "run_alert_rules_check.sh"):
        script = (REPO_ROOT / "scripts" / script_name).read_text(encoding="utf-8")

        assert "alert_rules_check.py" in script
