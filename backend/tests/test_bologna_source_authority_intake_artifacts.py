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
CONFIG_PATH = REPO_ROOT / "config" / "bologna_source_authority_intake.yaml"


def _load_validator() -> ModuleType:
    script_path = REPO_ROOT / "scripts" / "bologna_source_authority_intake_check.py"
    spec = importlib.util.spec_from_file_location(
        "bologna_source_authority_intake_check",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _catalog() -> dict[str, Any]:
    catalog = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    assert isinstance(catalog, dict)
    return cast(dict[str, Any], catalog)


def _complete_source_authority_record(
    validator: Any,
    candidate_id: str = "comune_bologna_pug_webgis",
) -> dict[str, Any]:
    rights_review = validator.rights_reviews_by_candidate()[candidate_id]
    return {
        "source_authority_record_id": "hypothetical-source-authority-record",
        "authority_type": "candidate_source_terms_review",
        "candidate_id": candidate_id,
        "scope_authority_record_ids": ["hypothetical-bologna-scope-record"],
        "authority_reference": "external-authority://bologna-source-authority-record",
        "decision_owner": "source-review-owner-or-forum",
        "decision_date": "2026-06-21",
        "effective_date": "2026-06-21",
        "rights_decision_ids": sorted(rights_review["rights_decisions"]),
        "evidence_slot_values": {
            slot: f"hypothetical cited evidence for {slot}"
            for slot in rights_review["required_evidence"]
        },
        "source_terms_summary": "Hypothetical cited source terms summary.",
        "source_version_or_publication_date": "2026-06-21",
        "retrieval_metadata_policy": "Record URL, retrieval timestamp, method, and checksum.",
        "cache_export_ai_raw_data_decisions": {
            "cache_allowed": "decision must come from cited authority",
            "export_allowed": "decision must come from cited authority",
            "raw_data_allowed": "decision must come from cited authority",
            "ai_use_allowed": "decision must come from cited authority",
        },
        "crs_precision_policy": "Record CRS, transformation policy, and precision caveat.",
        "attribution_text": "Hypothetical attribution from cited authority.",
        "caveats": ["Test-only record shape; not committed source approval."],
        "storage_export_boundaries": {
            "cache_boundary": "No cache boundary without cited authority.",
            "export_boundary": "No export boundary without cited authority.",
            "raw_data_boundary": "No raw data boundary without cited authority.",
            "report_boundary": "No report use without later corpus/report authority.",
        },
        "source_failure_policy": "Record source failures as evidence.",
        "downstream_unlocks_requested": [],
        "supersedes_source_authority_record_ids": [],
    }


def test_bologna_source_authority_intake_is_validate_only_and_blocked() -> None:
    validator = cast(Any, _load_validator())
    catalog = _catalog()

    assert catalog["schema_version"] == "bologna_source_authority_intake_v1"
    assert catalog["operator_runbook"] == "docs/runbooks/bologna_source_authority_intake.md"
    assert catalog["source_rights_matrix"] == "config/bologna_source_rights.yaml"
    assert catalog["preflight_catalog"] == "config/bologna_preflight.yaml"
    assert catalog["status"] == "blocked_no_authority"
    assert catalog["validation"] == "scripts/run_bologna_source_authority_intake_check.ps1"
    assert catalog["approvals"] == validator.EXPECTED_APPROVALS
    assert catalog["limits"] == validator.EXPECTED_LIMITS
    assert all(value is False for value in catalog["approvals"].values())


def test_bologna_source_authority_record_contract_is_present_and_blocked() -> None:
    validator = cast(Any, _load_validator())
    catalog = _catalog()

    assert "source_authority_record_contract" in catalog
    contract = catalog["source_authority_record_contract"]
    assert contract["contract_state"] == "ready_for_external_source_authority_evidence"
    assert contract["current_source_authority_records"] == []
    assert set(contract["required_record_fields"]) == (
        validator.EXPECTED_SOURCE_AUTHORITY_RECORD_FIELDS
    )
    assert set(contract["allowed_authority_types"]) == validator.EXPECTED_AUTHORITY_TYPES
    assert set(contract["required_rights_decision_coverage"]) == (
        validator.rights_required_decisions()
    )
    assert contract["coverage_policy"] == "per_record_all_required_rights_decisions"
    assert contract["evidence_slot_policy"] == "per_candidate_required_evidence"
    assert contract["decision_update_policy"] == (
        "disabled_until_complete_cited_source_authority"
    )
    assert all(value is True for value in contract["no_overclaim_controls"].values())


def test_bologna_source_authority_record_validator_accepts_complete_candidate_record() -> None:
    validator = cast(Any, _load_validator())
    catalog = deepcopy(_catalog())
    validate_contract = getattr(validator, "validate_source_authority_record_contract", None)

    assert validate_contract is not None
    catalog["source_authority_record_contract"]["current_source_authority_records"] = [
        _complete_source_authority_record(validator),
    ]

    validate_contract(catalog)


def test_bologna_source_authority_record_validator_fails_on_missing_evidence_slot() -> None:
    validator = cast(Any, _load_validator())
    catalog = deepcopy(_catalog())
    validate_contract = getattr(validator, "validate_source_authority_record_contract", None)
    record = _complete_source_authority_record(validator)
    record["evidence_slot_values"].pop("effective_pug_document_or_webgis_version")
    catalog["source_authority_record_contract"]["current_source_authority_records"] = [record]

    assert validate_contract is not None
    with pytest.raises(SystemExit, match="evidence slot values drifted"):
        validate_contract(catalog)


def test_bologna_source_authority_record_validator_fails_on_downstream_unlock() -> None:
    validator = cast(Any, _load_validator())
    catalog = deepcopy(_catalog())
    validate_contract = getattr(validator, "validate_source_authority_record_contract", None)
    record = _complete_source_authority_record(validator)
    record["downstream_unlocks_requested"] = ["bologna_source_rights_matrix"]
    catalog["source_authority_record_contract"]["current_source_authority_records"] = [record]

    assert validate_contract is not None
    with pytest.raises(SystemExit, match="must not request downstream unlocks"):
        validate_contract(catalog)


def test_bologna_source_authority_intake_matches_source_rights_matrix() -> None:
    validator = cast(Any, _load_validator())
    catalog = _catalog()
    source_rights_reviews = validator.rights_reviews_by_candidate()

    assert {
        review["candidate_id"] for review in catalog["candidate_authority_reviews"]
    } == set(source_rights_reviews)
    for review in catalog["candidate_authority_reviews"]:
        candidate_id = review["candidate_id"]
        assert set(review["evidence_slots"]) == set(
            source_rights_reviews[candidate_id]["required_evidence"],
        )
    assert set(catalog["promotion_blockers"]) == validator.rights_promotion_blockers()


def test_bologna_source_authority_intake_cadastral_gap_matches_rights_matrix() -> None:
    validator = cast(Any, _load_validator())
    catalog = _catalog()
    cadastral_review = catalog["cadastral_authority_review"]
    rights_gap = validator.rights_cadastral_gap()

    assert cadastral_review["authority_state"] == "missing_authority"
    assert cadastral_review["rights_matrix_state"] == "direct_source_review_required"
    assert cadastral_review["authority_references"] == []
    assert cadastral_review["decision_updates_allowed"] is False
    assert set(cadastral_review["evidence_slots"]) == set(rights_gap["required_evidence"])


def test_bologna_source_authority_intake_reviews_remain_uncited_and_unpromoted() -> None:
    catalog = _catalog()

    for review in catalog["candidate_authority_reviews"]:
        assert review["authority_state"] == "missing_authority"
        assert review["rights_matrix_state"] == "pending_external_review"
        assert review["evidence_status"] == "missing"
        assert review["authority_references"] == []
        assert review["decision_updates_allowed"] is False


def test_bologna_source_authority_intake_validator_passes_current_artifacts() -> None:
    validator = cast(Any, _load_validator())

    assert validator.main() == 0


def test_bologna_source_authority_intake_validator_fails_if_authority_promoted(
    monkeypatch: Any,
) -> None:
    validator = cast(Any, _load_validator())
    catalog = deepcopy(_catalog())
    catalog["candidate_authority_reviews"][0]["decision_updates_allowed"] = True

    def fake_read_text(path: str) -> str:
        if path == "config/bologna_source_authority_intake.yaml":
            return cast(str, yaml.safe_dump(catalog))
        return (REPO_ROOT / path).read_text(encoding="utf-8")

    monkeypatch.setattr(validator, "read_text", fake_read_text)

    with pytest.raises(SystemExit, match="updates unexpectedly allowed"):
        validator.validate_catalog()


def test_bologna_source_authority_intake_validator_fails_if_slots_drift(
    monkeypatch: Any,
) -> None:
    validator = cast(Any, _load_validator())
    catalog = deepcopy(_catalog())
    catalog["candidate_authority_reviews"][0]["evidence_slots"].append("uncited_extra_slot")

    def fake_read_text(path: str) -> str:
        if path == "config/bologna_source_authority_intake.yaml":
            return cast(str, yaml.safe_dump(catalog))
        return (REPO_ROOT / path).read_text(encoding="utf-8")

    monkeypatch.setattr(validator, "read_text", fake_read_text)

    with pytest.raises(SystemExit, match="evidence slots drifted"):
        validator.validate_catalog()


def test_bologna_source_authority_intake_script_and_wrappers_are_validate_only() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/bologna_source_authority_intake_check.py"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == "Bologna source authority intake check: ok"
    ps1 = (
        REPO_ROOT / "scripts" / "run_bologna_source_authority_intake_check.ps1"
    ).read_text(encoding="utf-8")
    sh = (
        REPO_ROOT / "scripts" / "run_bologna_source_authority_intake_check.sh"
    ).read_text(encoding="utf-8")
    for script in (ps1, sh):
        assert "bologna_source_authority_intake_check.py" in script
        assert "Bologna source authority intake check: ok" in script
    assert "New-Item" not in ps1
    assert "Remove-Item" not in ps1
    assert "mkdir" not in sh
    assert "rm " not in sh


def test_bologna_source_authority_intake_runbook_preserves_boundary() -> None:
    runbook = (
        REPO_ROOT / "docs" / "runbooks" / "bologna_source_authority_intake.md"
    ).read_text(encoding="utf-8")

    for phrase in (
        "bologna_source_authority_intake_v1",
        "validate-only",
        "does not approve sources",
        "source-rights matrix",
        "authority_state",
        "decision_updates_allowed",
    ):
        assert phrase in runbook
