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
CONFIG_PATH = REPO_ROOT / "config" / "bologna_source_rights.yaml"


def _load_validator() -> ModuleType:
    script_path = REPO_ROOT / "scripts" / "bologna_source_rights_check.py"
    spec = importlib.util.spec_from_file_location("bologna_source_rights_check", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _catalog() -> dict[str, Any]:
    catalog = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    assert isinstance(catalog, dict)
    return cast(dict[str, Any], catalog)


def test_bologna_source_rights_catalog_is_validate_only() -> None:
    validator = cast(Any, _load_validator())
    catalog = _catalog()

    assert catalog["schema_version"] == "bologna_source_rights_v1"
    assert catalog["operator_runbook"] == "docs/runbooks/bologna_source_rights.md"
    assert catalog["source_review"] == "docs/source-reviews/bologna-source-rights.md"
    assert catalog["candidate_catalog"] == "config/bologna_source_candidates.yaml"
    assert catalog["status"] == "repo_local_validate_only"
    assert catalog["validation"] == "scripts/run_bologna_source_rights_check.ps1"
    assert catalog["approvals"] == validator.EXPECTED_APPROVALS
    assert catalog["limits"] == validator.EXPECTED_LIMITS
    assert all(value is False for value in catalog["approvals"].values())


def test_bologna_source_rights_cover_candidates_and_source_schema() -> None:
    validator = cast(Any, _load_validator())
    catalog = _catalog()
    reviewed_ids = {review["candidate_id"] for review in catalog["candidate_rights_reviews"]}

    assert reviewed_ids == validator.candidate_ids()
    assert (
        set(catalog["source_contract_required_fields"])
        == validator.source_schema_required_fields()
    )
    assert set(catalog["required_rights_decisions"]) == validator.EXPECTED_RIGHTS_DECISIONS


def test_bologna_source_rights_reviews_remain_pending_and_unpromoted() -> None:
    validator = cast(Any, _load_validator())
    catalog = _catalog()

    for review in catalog["candidate_rights_reviews"]:
        assert review["decision_state"] == "pending_external_review"
        assert set(review["rights_decisions"]) == validator.EXPECTED_RIGHTS_DECISIONS
        assert all(value == "pending_review" for value in review["rights_decisions"].values())
        assert review["promotion"] == validator.EXPECTED_PROMOTION
        assert review["required_evidence"]


def test_bologna_source_rights_cadastral_gap_stays_blocked() -> None:
    catalog = _catalog()
    gap = catalog["cadastral_gap"]

    assert gap["status"] == "direct_source_review_required"
    assert all(value is False for value in gap["approval"].values())
    assert gap["required_evidence"]


def test_bologna_source_rights_validator_passes_current_artifacts() -> None:
    validator = cast(Any, _load_validator())

    assert validator.main() == 0


def test_bologna_source_rights_validator_fails_if_candidate_promoted(monkeypatch: Any) -> None:
    validator = cast(Any, _load_validator())
    catalog = deepcopy(_catalog())
    catalog["candidate_rights_reviews"][0]["promotion"]["runtime_use_allowed"] = True

    def fake_read_text(path: str) -> str:
        if path == "config/bologna_source_rights.yaml":
            return cast(str, yaml.safe_dump(catalog))
        return (REPO_ROOT / path).read_text(encoding="utf-8")

    monkeypatch.setattr(validator, "read_text", fake_read_text)

    with pytest.raises(SystemExit, match="promotion changed"):
        validator.validate_catalog()


def test_bologna_source_rights_validator_fails_if_candidate_missing(monkeypatch: Any) -> None:
    validator = cast(Any, _load_validator())
    catalog = deepcopy(_catalog())
    catalog["candidate_rights_reviews"] = catalog["candidate_rights_reviews"][1:]

    def fake_read_text(path: str) -> str:
        if path == "config/bologna_source_rights.yaml":
            return cast(str, yaml.safe_dump(catalog))
        return (REPO_ROOT / path).read_text(encoding="utf-8")

    monkeypatch.setattr(validator, "read_text", fake_read_text)

    with pytest.raises(SystemExit, match="rights review candidate mismatch"):
        validator.validate_catalog()


def test_bologna_source_rights_script_and_wrappers_are_validate_only() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/bologna_source_rights_check.py"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == "Bologna source rights check: ok"
    ps1 = (REPO_ROOT / "scripts" / "run_bologna_source_rights_check.ps1").read_text(
        encoding="utf-8",
    )
    sh = (REPO_ROOT / "scripts" / "run_bologna_source_rights_check.sh").read_text(
        encoding="utf-8",
    )
    for script in (ps1, sh):
        assert "bologna_source_rights_check.py" in script
        assert "Bologna source rights check: ok" in script
    assert "New-Item" not in ps1
    assert "Remove-Item" not in ps1
    assert "mkdir" not in sh
    assert "rm " not in sh


def test_bologna_source_rights_runbook_and_review_preserve_boundary() -> None:
    runbook = (REPO_ROOT / "docs" / "runbooks" / "bologna_source_rights.md").read_text(
        encoding="utf-8",
    )
    review = (REPO_ROOT / "docs" / "source-reviews" / "bologna-source-rights.md").read_text(
        encoding="utf-8",
    )

    for phrase in (
        "validate-only",
        "does not approve sources",
        "schemas/source_schema.json",
        "Cadastral cartography remains a direct official-source review gap",
    ):
        assert phrase in runbook
    for phrase in (
        "source-rights matrix only",
        "Source approval allowed: no",
        "Source registry promotion allowed: no",
        "Fixture corpus allowed: no",
        "Runtime/report use allowed: no",
        "Not approved",
    ):
        assert phrase in review
