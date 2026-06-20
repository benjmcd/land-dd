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
