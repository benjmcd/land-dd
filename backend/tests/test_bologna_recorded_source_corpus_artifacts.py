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
CONFIG_PATH = REPO_ROOT / "config" / "bologna_recorded_source_corpus.yaml"


def _load_validator() -> ModuleType:
    script_path = REPO_ROOT / "scripts" / "bologna_recorded_source_corpus_check.py"
    spec = importlib.util.spec_from_file_location(
        "bologna_recorded_source_corpus_check",
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


def test_bologna_recorded_source_corpus_is_validate_only_and_blocked() -> None:
    validator = cast(Any, _load_validator())
    catalog = _catalog()

    assert catalog["schema_version"] == "bologna_recorded_source_corpus_v1"
    assert catalog["operator_runbook"] == "docs/runbooks/bologna_recorded_source_corpus.md"
    assert catalog["preflight_catalog"] == "config/bologna_preflight.yaml"
    assert catalog["source_authority_intake"] == "config/bologna_source_authority_intake.yaml"
    assert catalog["source_rights_matrix"] == "config/bologna_source_rights.yaml"
    assert catalog["status"] == "blocked_no_authority"
    assert catalog["validation"] == "scripts/run_bologna_recorded_source_corpus_check.ps1"
    assert catalog["approvals"] == validator.EXPECTED_APPROVALS
    assert catalog["limits"] == validator.EXPECTED_LIMITS
    assert all(value is False for value in catalog["approvals"].values())


def test_bologna_recorded_source_corpus_matches_authority_and_rights_evidence() -> None:
    validator = cast(Any, _load_validator())
    catalog = _catalog()
    intake_reviews = validator.intake_reviews_by_candidate()
    rights_reviews = validator.rights_reviews_by_candidate()

    assert {review["candidate_id"] for review in catalog["candidate_corpus_reviews"]} == set(
        intake_reviews,
    )
    for review in catalog["candidate_corpus_reviews"]:
        candidate_id = review["candidate_id"]
        assert set(review["required_manifest_evidence"]) == set(
            intake_reviews[candidate_id]["evidence_slots"],
        )
        assert set(review["required_manifest_evidence"]) == set(
            rights_reviews[candidate_id]["required_evidence"],
        )
    assert set(catalog["promotion_blockers"]) == validator.rights_promotion_blockers()


def test_bologna_recorded_source_corpus_rows_remain_unpromoted() -> None:
    catalog = _catalog()

    for review in catalog["candidate_corpus_reviews"]:
        assert review["corpus_state"] == "blocked_no_authority"
        assert review["fixture_manifest_entry_allowed"] is False
        assert review["source_failure_fixture_allowed"] is False

    cadastral = catalog["cadastral_corpus_review"]
    assert cadastral["corpus_state"] == "blocked_direct_source_review_required"
    assert cadastral["fixture_manifest_entry_allowed"] is False
    assert cadastral["source_failure_fixture_allowed"] is False


def test_bologna_recorded_source_corpus_validator_passes_current_artifacts() -> None:
    validator = cast(Any, _load_validator())

    assert validator.main() == 0


def test_bologna_recorded_source_corpus_validator_fails_if_fixture_allowed(
    monkeypatch: Any,
) -> None:
    validator = cast(Any, _load_validator())
    catalog = deepcopy(_catalog())
    catalog["candidate_corpus_reviews"][0]["fixture_manifest_entry_allowed"] = True

    def fake_read_text(path: str) -> str:
        if path == "config/bologna_recorded_source_corpus.yaml":
            return cast(str, yaml.safe_dump(catalog))
        return (REPO_ROOT / path).read_text(encoding="utf-8")

    monkeypatch.setattr(validator, "read_text", fake_read_text)

    with pytest.raises(SystemExit, match="fixture manifest unexpectedly allowed"):
        validator.validate_catalog()


def test_bologna_recorded_source_corpus_script_and_wrappers_are_validate_only() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/bologna_recorded_source_corpus_check.py"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == "Bologna recorded-source corpus check: ok"
    ps1 = (
        REPO_ROOT / "scripts" / "run_bologna_recorded_source_corpus_check.ps1"
    ).read_text(encoding="utf-8")
    sh = (
        REPO_ROOT / "scripts" / "run_bologna_recorded_source_corpus_check.sh"
    ).read_text(encoding="utf-8")
    for script in (ps1, sh):
        assert "bologna_recorded_source_corpus_check.py" in script
        assert "Bologna recorded-source corpus check: ok" in script
    assert "New-Item" not in ps1
    assert "Remove-Item" not in ps1
    assert "mkdir" not in sh
    assert "rm " not in sh


def test_bologna_recorded_source_corpus_runbook_preserves_boundary() -> None:
    runbook = (
        REPO_ROOT / "docs" / "runbooks" / "bologna_recorded_source_corpus.md"
    ).read_text(encoding="utf-8")

    for phrase in (
        "bologna_recorded_source_corpus_v1",
        "validate-only",
        "does not select a Bologna AOI",
        "source-failure fixture",
        "corpus_state",
        "fixture manifest entry remains disallowed",
    ):
        assert phrase in runbook
