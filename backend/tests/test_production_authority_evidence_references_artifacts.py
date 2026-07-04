from __future__ import annotations

import importlib.util
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from types import ModuleType
from typing import Any, cast

import pytest

yaml = cast(Any, __import__("yaml"))

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "config" / "production_authority_evidence_references.yaml"
INTAKE_PATH = REPO_ROOT / "config" / "production_authority_intake.yaml"


def _load_validator() -> ModuleType:
    script_path = REPO_ROOT / "scripts" / "production_authority_evidence_references_check.py"
    spec = importlib.util.spec_from_file_location(
        "production_authority_evidence_references_check",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return cast(dict[str, Any], payload)


def _evidence_reference(
    *,
    stream_id: str = "ds017_source_entitlement",
    evidence_item_id: str = "reviewed_terms_or_redacted_contract_reference",
) -> dict[str, Any]:
    return {
        "reference_id": "synthetic-production-authority-reference",
        "authority_stream_id": stream_id,
        "evidence_item_id": evidence_item_id,
        "authority_reference": "external cited authority reference",
        "artifact_type": "terms_url",
        "artifact_location_or_citation": "https://example.invalid/authority",
        "decision_owner": "benjmcd",
        "review_owner": "benjmcd",
        "decision_date": "2026-07-04",
        "effective_date": "2026-07-04",
        "scope_summary": "Synthetic submitted reference shape for validator coverage only.",
        "evidence_summary": "Synthetic cited evidence summary for validator coverage only.",
        "caveats": ["synthetic caveat"],
        "downstream_unlocks_requested": [],
        "supersedes_reference_ids": [],
    }


def test_production_authority_evidence_references_current_artifacts_validate() -> None:
    validator = cast(Any, _load_validator())

    assert validator.main() == 0


def test_production_authority_evidence_references_are_validate_only_and_blocked() -> None:
    catalog = _yaml(CONFIG_PATH)

    assert catalog["schema_version"] == "production_authority_evidence_references_v1"
    assert catalog["status"] == "blocked_no_submitted_references"
    assert catalog["source_intake"] == "config/production_authority_intake.yaml"
    assert catalog["follow_on_sequence"] == "config/authority_follow_on_sequence.yaml"
    assert catalog["validation"] == (
        "scripts/run_production_authority_evidence_references_check.ps1"
    )
    assert catalog["limits"] == {
        "validate_only_reference_contract": True,
        "records_authority": False,
        "records_owner_answer": False,
        "supplies_authority_evidence": False,
        "approves_sources": False,
        "changes_source_rights": False,
        "changes_source_readiness": False,
        "triggers_follow_on_sequence": False,
        "captures_fixtures": False,
        "seeds_database": False,
        "proves_report": False,
        "provisions_hosted_runtime": False,
        "changes_schema_api_auth_ui_runtime": False,
        "unfreezes_qualification": False,
        "unblocks_p0": False,
        "claims_level_10": False,
    }
    contract = catalog["reference_contract"]
    assert contract["current_evidence_references"] == []
    assert contract["downstream_unlocks_requested"] == []
    assert "authority_stream_id" in contract["required_reference_fields"]
    assert "evidence_item_id" in contract["required_reference_fields"]
    assert "downstream_unlocks_requested" in contract["required_reference_fields"]
    assert "p0_unblock" in contract["forbidden_reference_effects"]


def test_production_authority_evidence_references_cover_every_stream() -> None:
    validator = cast(Any, _load_validator())
    catalog = _yaml(CONFIG_PATH)
    production = _yaml(INTAKE_PATH)

    templates = {
        template["authority_stream_id"]: template
        for template in catalog["stream_reference_templates"]
    }
    streams = {stream["id"]: stream for stream in production["authority_streams"]}

    assert set(templates) == set(streams) == set(validator.production_streams())
    for stream_id, stream in streams.items():
        template = templates[stream_id]
        assert template["source_catalog"] == stream["source_catalog"]
        assert template["required_evidence"] == stream["required_evidence"]
        assert template["current_authority_references"] == []
        assert template["decision_updates_allowed"] is False
        assert template["downstream_unlocks_requested"] == []


def test_production_authority_evidence_references_reject_current_reference() -> None:
    validator = cast(Any, _load_validator())
    catalog = deepcopy(_yaml(CONFIG_PATH))
    catalog["reference_contract"]["current_evidence_references"] = [
        {"reference_id": "REF-001"},
    ]

    with pytest.raises(SystemExit, match="current evidence references must remain empty"):
        validator.validate_catalog(catalog)


def test_production_authority_evidence_references_reject_stream_unlock() -> None:
    validator = cast(Any, _load_validator())
    catalog = deepcopy(_yaml(CONFIG_PATH))
    catalog["stream_reference_templates"][0]["downstream_unlocks_requested"] = [
        "p0_unblock",
    ]

    with pytest.raises(SystemExit, match="requested downstream unlocks"):
        validator.validate_catalog(catalog)


def test_production_authority_evidence_references_reject_required_evidence_drift() -> None:
    validator = cast(Any, _load_validator())
    catalog = deepcopy(_yaml(CONFIG_PATH))
    catalog["stream_reference_templates"][0]["required_evidence"] = [
        item
        for item in catalog["stream_reference_templates"][0]["required_evidence"]
        if item != "reviewed_terms_or_redacted_contract_reference"
    ]

    with pytest.raises(SystemExit, match="required evidence drifted"):
        validator.validate_catalog(catalog)


def test_production_authority_evidence_references_accept_synthetic_reference_shape() -> None:
    validator = cast(Any, _load_validator())
    catalog = _yaml(CONFIG_PATH)
    evidence_reference = _evidence_reference()
    catalog_before = deepcopy(catalog)
    reference_before = deepcopy(evidence_reference)

    result = validator.evaluate_submitted_evidence_reference(catalog, evidence_reference)

    assert result.accepted, result.errors
    assert "source_approval" in result.still_blocked
    assert "p0_unblock" in result.still_blocked
    assert catalog == catalog_before
    assert evidence_reference == reference_before


def test_production_authority_evidence_references_reject_bad_synthetic_references() -> None:
    validator = cast(Any, _load_validator())
    catalog = _yaml(CONFIG_PATH)

    missing_authority = _evidence_reference()
    missing_authority.pop("authority_reference")
    unknown_stream = _evidence_reference(stream_id="unknown_stream")
    unknown_evidence = _evidence_reference(evidence_item_id="not_a_required_evidence_item")
    unlock_request = _evidence_reference()
    unlock_request["downstream_unlocks_requested"] = ["p0_unblock"]
    bad_artifact_type = _evidence_reference()
    bad_artifact_type["artifact_type"] = "fixture_capture"
    bad_effective_date = _evidence_reference()
    bad_effective_date["effective_date"] = "July 4, 2026"

    cases = [
        (missing_authority, "missing required fields"),
        (unknown_stream, "unknown authority_stream_id"),
        (unknown_evidence, "evidence_item_id is not required"),
        (unlock_request, "must not request downstream unlocks"),
        (bad_artifact_type, "artifact_type is not allowed"),
        (bad_effective_date, "effective_date must be an ISO date"),
    ]
    for evidence_reference, expected_error in cases:
        result = validator.evaluate_submitted_evidence_reference(catalog, evidence_reference)
        assert not result.accepted
        assert any(expected_error in error for error in result.errors), result.errors


def test_production_authority_evidence_references_still_reject_current_reference() -> None:
    validator = cast(Any, _load_validator())
    catalog = deepcopy(_yaml(CONFIG_PATH))
    catalog["reference_contract"]["current_evidence_references"] = [
        _evidence_reference(),
    ]

    with pytest.raises(SystemExit, match="current evidence references must remain empty"):
        validator.validate_catalog(catalog)


def test_production_authority_evidence_references_script_and_wrappers_are_validate_only() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/production_authority_evidence_references_check.py"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "production authority evidence references check: ok" in result.stdout
    ps1 = (
        REPO_ROOT / "scripts" / "run_production_authority_evidence_references_check.ps1"
    ).read_text(encoding="utf-8")
    sh = (
        REPO_ROOT / "scripts" / "run_production_authority_evidence_references_check.sh"
    ).read_text(encoding="utf-8")
    for script in (ps1, sh):
        assert "production_authority_evidence_references_check.py" in script
    assert "New-Item" not in ps1
    assert "Remove-Item" not in ps1
    assert "mkdir" not in sh
    assert "rm " not in sh
    assert "CheckerArgs.Count -eq 0" in ps1
    assert 'if [[ "$#" -eq 0 ]]' in sh


def test_production_authority_evidence_references_json_reports_empty_contract() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/production_authority_evidence_references_check.py",
            "--json",
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    summary = yaml.safe_load(result.stdout)
    assert summary["schema_version"] == "production_authority_evidence_references_summary_v1"
    assert summary["ok"] is True
    assert summary["contract_status"] == "blocked_no_submitted_references"
    assert summary["source_intake"] == "config/production_authority_intake.yaml"
    assert summary["follow_on_sequence"] == "config/authority_follow_on_sequence.yaml"
    assert summary["current_evidence_reference_count"] == 0
    assert summary["downstream_unlock_request_count"] == 0
    assert summary["required_reference_field_count"] == 15
    assert "authority_stream_id" in summary["required_reference_fields"]
    assert "p0_unblock" in summary["forbidden_reference_effects"]

    templates = {
        template["authority_stream_id"]: template
        for template in summary["stream_reference_templates"]
    }
    assert summary["stream_reference_template_count"] == 9
    assert templates["ds017_source_entitlement"]["required_evidence_count"] == 14
    assert templates["bologna_pilot_scope"]["required_evidence_count"] == 12
    assert all(
        template["current_authority_reference_count"] == 0
        for template in templates.values()
    )
    assert all(
        template["downstream_unlock_request_count"] == 0
        for template in templates.values()
    )
    assert all(template["decision_updates_allowed"] is False for template in templates.values())


def test_production_authority_evidence_references_summary_keeps_blocked_boundaries() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/production_authority_evidence_references_check.py",
            "--summary",
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "production authority evidence references summary: blocked" in result.stdout
    assert "schema_version: production_authority_evidence_references_summary_v1" in result.stdout
    assert "contract_status: blocked_no_submitted_references" in result.stdout
    assert "current_evidence_references: 0" in result.stdout
    assert "downstream_unlock_requests: 0" in result.stdout
    assert "stream_reference_templates: 9" in result.stdout
    assert (
        "stream_reference_template ds017_source_entitlement: "
        "status=missing_authority_reference"
    ) in result.stdout
    assert "forbidden_reference_effects:" in result.stdout
    assert "p0_unblock" in result.stdout
    assert "production authority evidence references check: ok" in result.stdout


def test_production_authority_evidence_references_wrapper_forwards_summary_and_json() -> None:
    wrapper_command = [
        "powershell",
        "-NoProfile",
        "-File",
        "scripts/run_production_authority_evidence_references_check.ps1",
    ]
    ps_summary = subprocess.run(
        [*wrapper_command, "--summary"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "production authority evidence references summary: blocked" in ps_summary.stdout
    assert "production authority evidence references: ok" not in ps_summary.stdout

    ps_json = subprocess.run(
        [*wrapper_command, "--json"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    parsed = yaml.safe_load(ps_json.stdout)
    assert parsed["schema_version"] == "production_authority_evidence_references_summary_v1"
    assert parsed["contract_status"] == "blocked_no_submitted_references"
    assert "production authority evidence references: ok" not in ps_json.stdout
