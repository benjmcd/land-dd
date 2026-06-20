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
CONFIG_PATH = REPO_ROOT / "config" / "bologna_source_candidates.yaml"


def _load_validator() -> ModuleType:
    script_path = REPO_ROOT / "scripts" / "bologna_source_candidates_check.py"
    spec = importlib.util.spec_from_file_location("bologna_source_candidates_check", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _catalog() -> dict[str, Any]:
    catalog = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    assert isinstance(catalog, dict)
    return cast(dict[str, Any], catalog)


def test_bologna_source_candidates_catalog_is_candidate_only() -> None:
    validator = cast(Any, _load_validator())
    catalog = _catalog()

    assert catalog["schema_version"] == "bologna_source_candidates_v1"
    assert catalog["operator_runbook"] == "docs/runbooks/bologna_source_candidates.md"
    assert catalog["source_review"] == "docs/source-reviews/bologna-source-candidates.md"
    assert catalog["status"] == "repo_local_candidate_inventory"
    assert catalog["validation"] == "scripts/run_bologna_source_candidates_check.ps1"
    assert catalog["approvals"] == validator.EXPECTED_APPROVALS
    assert catalog["limits"] == validator.EXPECTED_LIMITS
    assert all(value is False for value in catalog["approvals"].values())
    assert catalog["limits"]["candidate_only"] is True


def test_bologna_source_candidates_cover_required_domains_and_gaps() -> None:
    validator = cast(Any, _load_validator())
    catalog = _catalog()
    domains = {candidate["domain"] for candidate in catalog["candidate_sources"]}
    gaps = {gap["gap_id"] for gap in catalog["known_gaps"]}

    assert domains == validator.REQUIRED_DOMAINS
    assert gaps == validator.REQUIRED_GAPS
    assert set(catalog["required_before_any_use"]) == validator.REQUIRED_BEFORE_ANY_USE


def test_bologna_source_candidates_remain_unapproved() -> None:
    catalog = _catalog()

    for candidate in catalog["candidate_sources"]:
        assert candidate["source_version_status"] == "pending_review"
        assert candidate["rights_review_status"] == "pending_review"
        assert candidate["approval_status"] == "not_approved"
        assert candidate["source_registry_promoted"] is False
        assert candidate["allowed_for_runtime"] is False
        assert candidate["allowed_for_fixture_corpus"] is False
        assert candidate["required_before_use"]
        assert candidate["caveats"]


def test_bologna_source_candidates_validator_passes_current_artifacts() -> None:
    validator = cast(Any, _load_validator())

    assert validator.main() == 0


def test_bologna_source_candidates_validator_fails_if_candidate_promoted(
    monkeypatch: Any,
) -> None:
    validator = cast(Any, _load_validator())
    catalog = deepcopy(_catalog())
    catalog["candidate_sources"][0]["allowed_for_runtime"] = True

    def fake_read_text(path: str) -> str:
        if path == "config/bologna_source_candidates.yaml":
            return cast(str, yaml.safe_dump(catalog))
        return (REPO_ROOT / path).read_text(encoding="utf-8")

    monkeypatch.setattr(validator, "read_text", fake_read_text)

    with pytest.raises(SystemExit, match="runtime use allowed"):
        validator.validate_catalog()


def test_bologna_source_candidates_validator_fails_if_gap_removed(
    monkeypatch: Any,
) -> None:
    validator = cast(Any, _load_validator())
    catalog = deepcopy(_catalog())
    catalog["known_gaps"] = [
        gap for gap in catalog["known_gaps"] if gap["gap_id"] != "italian_cadastral_cartography"
    ]

    def fake_read_text(path: str) -> str:
        if path == "config/bologna_source_candidates.yaml":
            return cast(str, yaml.safe_dump(catalog))
        return (REPO_ROOT / path).read_text(encoding="utf-8")

    monkeypatch.setattr(validator, "read_text", fake_read_text)

    with pytest.raises(SystemExit, match="known gap set mismatch"):
        validator.validate_catalog()


def test_bologna_source_candidates_script_and_wrappers_are_validate_only() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/bologna_source_candidates_check.py"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == "Bologna source candidates check: ok"
    ps1 = (REPO_ROOT / "scripts" / "run_bologna_source_candidates_check.ps1").read_text(
        encoding="utf-8",
    )
    sh = (REPO_ROOT / "scripts" / "run_bologna_source_candidates_check.sh").read_text(
        encoding="utf-8",
    )
    for script in (ps1, sh):
        assert "bologna_source_candidates_check.py" in script
        assert "Bologna source candidates check: ok" in script
    assert "New-Item" not in ps1
    assert "Remove-Item" not in ps1
    assert "mkdir" not in sh
    assert "rm " not in sh


def test_bologna_source_candidates_runbook_and_review_preserve_boundary() -> None:
    runbook = (REPO_ROOT / "docs" / "runbooks" / "bologna_source_candidates.md").read_text(
        encoding="utf-8",
    )
    review = (REPO_ROOT / "docs" / "source-reviews" / "bologna-source-candidates.md").read_text(
        encoding="utf-8",
    )

    for phrase in (
        "candidate-only",
        "does not approve sources",
        "does not fetch official datasets",
        "Italian cadastral cartography remains a direct source-review gap",
    ):
        assert phrase in runbook
    for phrase in (
        "candidate inventory only",
        "Production use allowed: no",
        "Fixture corpus allowed: no",
        "Source registry promotion allowed: no",
        "Not approved",
    ):
        assert phrase in review
