from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, cast

yaml = cast(Any, __import__("yaml"))

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "config" / "bologna_odp4_db_report_proof_response_gate.yaml"


def _load_validator() -> ModuleType:
    script_path = (
        REPO_ROOT / "scripts" / "bologna_odp4_db_report_proof_response_gate_check.py"
    )
    spec = importlib.util.spec_from_file_location(
        "bologna_odp4_db_report_proof_response_gate_check",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return cast(dict[str, Any], payload)


def test_odp4_db_report_proof_response_gate_is_validate_only_and_blocked() -> None:
    validator = cast(Any, _load_validator())
    catalog = _yaml(CONFIG_PATH)

    assert catalog["schema_version"] == (
        "bologna_odp4_db_report_proof_response_gate_v1"
    )
    assert catalog["operator_runbook"] == (
        "docs/runbooks/bologna_odp4_db_report_proof_response_gate.md"
    )
    assert catalog["status"] == (
        "blocked_until_odp_bol_001_odp_bol_002_odp_bol_003_and_missing_odp_bol_004_owner_answer"
    )
    assert catalog["validation"] == (
        "scripts/run_bologna_odp4_db_report_proof_response_gate_check.ps1"
    )
    assert catalog["approvals"] == validator.EXPECTED_APPROVALS
    assert catalog["limits"] == validator.EXPECTED_LIMITS
    assert all(value is False for value in catalog["approvals"].values())


def test_odp4_db_report_proof_response_gate_aligns_with_contracts() -> None:
    validator = cast(Any, _load_validator())
    catalog = _yaml(CONFIG_PATH)
    gate = catalog["odp_bol_004_gate"]

    assert gate["odp_id"] == validator.ODP_ID
    assert gate["status"] == "blocked_until_odp_bol_001_odp_bol_002_and_odp_bol_003"
    assert gate["prerequisite_odp_ids"] == validator.PREREQUISITE_ODP_IDS
    assert gate["prerequisite_status"] == "missing_owner_answers"
    assert gate["current_owner_answer_references"] == []
    assert gate["current_report_proof_authority_references"] == []
    assert gate["current_db_report_run_references"] == []
    assert gate["current_report_artifact_references"] == []
    assert set(gate["required_owner_answer_fields"]) == validator.owner_answer_fields()
    assert set(gate["required_report_proof_fields"]) == validator.report_proof_fields()
    assert set(gate["required_report_run_contract_fields"]) == (
        validator.report_run_required_fields()
    )
    assert set(gate["required_evidence_contract_fields"]) == (
        validator.evidence_required_fields()
    )
    assert set(gate["required_claim_contract_fields"]) == validator.claim_required_fields()


def test_odp4_report_proof_requirements_match_owner_intake() -> None:
    validator = cast(Any, _load_validator())
    catalog = _yaml(CONFIG_PATH)

    assert {item["field_id"] for item in catalog["report_proof_requirements"]} == (
        validator.report_proof_fields()
    )
    for requirement in catalog["report_proof_requirements"]:
        assert requirement["owner_question"]
        assert requirement["must_cite"]
        assert requirement["consequence_if_missing"]


def test_odp4_schema_contract_requirements_match_json_schemas() -> None:
    validator = cast(Any, _load_validator())
    catalog = _yaml(CONFIG_PATH)
    contracts = catalog["schema_contract_requirements"]

    assert set(contracts["report_run_contract"]["required_fields"]) == (
        validator.report_run_required_fields()
    )
    assert set(contracts["evidence_contract"]["required_fields"]) == (
        validator.evidence_required_fields()
    )
    assert set(contracts["claim_contract"]["required_fields"]) == (
        validator.claim_required_fields()
    )


def test_odp4_outcomes_do_not_unlock_work() -> None:
    validator = cast(Any, _load_validator())
    catalog = _yaml(CONFIG_PATH)

    assert {item["answer_type"] for item in catalog["outcome_matrix"]} == (
        validator.EXPECTED_ANSWER_TYPES
    )
    assert {item["answer_type"] for item in catalog["outcome_matrix"]} == (
        validator.allowed_owner_answer_types()
    )
    for outcome in catalog["outcome_matrix"]:
        assert outcome["downstream_updates_allowed"] is False
        assert outcome["still_disallowed"]
    assert all(catalog["no_overclaim_controls"].values())


def test_odp4_db_report_proof_response_gate_current_artifacts_validate() -> None:
    validator = cast(Any, _load_validator())

    assert validator.main() == 0


def test_odp4_db_report_proof_response_gate_script_and_wrappers_validate_only() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/bologna_odp4_db_report_proof_response_gate_check.py",
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == (
        "Bologna ODP-BOL-004 DB report proof response gate check: ok"
    )
    ps1 = (
        REPO_ROOT
        / "scripts"
        / "run_bologna_odp4_db_report_proof_response_gate_check.ps1"
    ).read_text(encoding="utf-8")
    sh = (
        REPO_ROOT / "scripts" / "run_bologna_odp4_db_report_proof_response_gate_check.sh"
    ).read_text(encoding="utf-8")
    for script in (ps1, sh):
        assert "bologna_odp4_db_report_proof_response_gate_check.py" in script
        assert "Bologna ODP-BOL-004 DB report proof response gate check: ok" in script
    assert "$LASTEXITCODE" in ps1
    assert "New-Item" not in ps1
    assert "Remove-Item" not in ps1
    assert "mkdir" not in sh
    assert "rm " not in sh


def test_odp4_db_report_proof_response_gate_runbook_preserves_boundary() -> None:
    runbook = (
        REPO_ROOT / "docs" / "runbooks" / (
            "bologna_odp4_db_report_proof_response_gate.md"
        )
    ).read_text(encoding="utf-8")

    for phrase in (
        "bologna_odp4_db_report_proof_response_gate_v1",
        "validate-only",
        "does not record report-proof authority",
        "ODP-BOL-004",
        "ODP-BOL-001",
        "ODP-BOL-002",
        "ODP-BOL-003",
        "current_report_proof_authority_references",
        "current_db_report_run_references",
        "downstream_updates_allowed",
    ):
        assert phrase in runbook
