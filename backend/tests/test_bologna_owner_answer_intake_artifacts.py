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
CONFIG_PATH = REPO_ROOT / "config" / "bologna_owner_answer_intake.yaml"
ODP1_OWNER_ANSWER_ID = "odp-bol-001-scope-pursuit-2026-06-26"


def _load_validator() -> ModuleType:
    script_path = REPO_ROOT / "scripts" / "bologna_owner_answer_intake_check.py"
    spec = importlib.util.spec_from_file_location(
        "bologna_owner_answer_intake_check",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _yaml(path: Path) -> dict[str, Any]:
    catalog = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(catalog, dict)
    return cast(dict[str, Any], catalog)


def _complete_owner_answer_record() -> dict[str, Any]:
    return {
        "owner_answer_id": ODP1_OWNER_ANSWER_ID,
        "odp_id": "ODP-BOL-001",
        "answer_type": "approve_review_only",
        "decision_owner": "benjmcd",
        "decision_date": "2026-06-26",
        "authority_reference": "owner directive 2026-06-26: pursue Bologna scope",
        "answer_summary": "Owner directed review-only Bologna scope pursuit.",
        "cited_artifacts": [
            "Codex thread owner directive 2026-06-26: pursue Bologna scope",
        ],
        "caveats": [
            "Review-only record; not complete pilot-scope authority.",
        ],
        "downstream_unlocks_requested": [],
        "supersedes_owner_answer_ids": [],
    }


def test_bologna_owner_answer_intake_is_validate_only_and_blocked() -> None:
    validator = cast(Any, _load_validator())
    catalog = _yaml(CONFIG_PATH)

    assert catalog["schema_version"] == "bologna_owner_answer_intake_v1"
    assert catalog["operator_runbook"] == "docs/runbooks/bologna_owner_answer_intake.md"
    assert catalog["status"] == "blocked_review_only_scope_pursuit"
    assert catalog["validation"] == "scripts/run_bologna_owner_answer_intake_check.ps1"
    assert catalog["approvals"] == validator.EXPECTED_APPROVALS
    assert catalog["limits"] == validator.EXPECTED_LIMITS
    assert catalog["approvals"]["product_aoi_scope_answered"] is True
    assert all(
        value is False
        for key, value in catalog["approvals"].items()
        if key != "product_aoi_scope_answered"
    )


def test_bologna_owner_answer_threads_align_to_existing_bologna_contracts() -> None:
    validator = cast(Any, _load_validator())
    catalog = _yaml(CONFIG_PATH)
    threads = {thread["odp_id"]: thread for thread in catalog["bologna_decision_threads"]}

    assert set(threads) == validator.EXPECTED_ODP_IDS
    assert threads["ODP-BOL-001"]["required_decisions"] == sorted(
        validator.pilot_scope_decisions(),
    )
    assert threads["ODP-BOL-002"]["required_rights_decisions"] == sorted(
        validator.source_rights_decisions(),
    )
    assert set(threads["ODP-BOL-002"]["candidate_review_ids"]) == (
        validator.source_candidate_ids() | {"cadastral_gap"}
    )
    assert threads["ODP-BOL-003"]["required_corpus_decisions"] == sorted(
        validator.corpus_decisions(),
    )
    assert threads["ODP-BOL-003"]["required_manifest_fields"] == sorted(
        validator.corpus_manifest_fields(),
    )
    assert set(threads["ODP-BOL-004"]["required_report_proof_fields"]) == (
        validator.EXPECTED_REPORT_PROOF_FIELDS
    )

    for odp_id, thread in threads.items():
        if odp_id == "ODP-BOL-001":
            assert thread["status"] == "review_only_scope_pursuit_answered"
            assert thread["owner_answer_references"] == [ODP1_OWNER_ANSWER_ID]
        else:
            assert thread["status"] == "missing_owner_answer"
            assert thread["owner_answer_references"] == []
        assert thread["downstream_updates_allowed"] is False
        assert thread["sequence"] == validator.EXPECTED_ODP_SEQUENCE[odp_id]


def test_bologna_owner_answer_contract_accepts_complete_future_shape() -> None:
    validator = cast(Any, _load_validator())
    catalog = deepcopy(_yaml(CONFIG_PATH))
    catalog["owner_answer_contract"]["current_owner_answers"] = [
        _complete_owner_answer_record(),
    ]

    validator.validate_owner_answer_contract(catalog)


def test_bologna_owner_answer_contract_rejects_downstream_unlocks() -> None:
    validator = cast(Any, _load_validator())
    catalog = deepcopy(_yaml(CONFIG_PATH))
    record = _complete_owner_answer_record()
    record["downstream_unlocks_requested"] = ["config/bologna_source_authority_intake.yaml"]
    catalog["owner_answer_contract"]["current_owner_answers"] = [record]

    with pytest.raises(SystemExit, match="must not request downstream unlocks"):
        validator.validate_owner_answer_contract(catalog)


def test_bologna_owner_answer_intake_current_artifacts_validate() -> None:
    validator = cast(Any, _load_validator())

    assert validator.main() == 0


def test_bologna_owner_answer_intake_script_and_wrappers_are_validate_only() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/bologna_owner_answer_intake_check.py"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == "Bologna owner answer intake check: ok"
    ps1 = (REPO_ROOT / "scripts" / "run_bologna_owner_answer_intake_check.ps1").read_text(
        encoding="utf-8",
    )
    sh = (REPO_ROOT / "scripts" / "run_bologna_owner_answer_intake_check.sh").read_text(
        encoding="utf-8",
    )
    for script in (ps1, sh):
        assert "bologna_owner_answer_intake_check.py" in script
        assert "Bologna owner answer intake check: ok" in script
    assert "$LASTEXITCODE" in ps1
    assert "New-Item" not in ps1
    assert "Remove-Item" not in ps1
    assert "mkdir" not in sh
    assert "rm " not in sh


def test_bologna_owner_answer_intake_runbook_preserves_boundary() -> None:
    runbook = (REPO_ROOT / "docs" / "runbooks" / "bologna_owner_answer_intake.md").read_text(
        encoding="utf-8",
    )

    for phrase in (
        "bologna_owner_answer_intake_v1",
        "validate-only",
        "records one review-only owner answer",
        ODP1_OWNER_ANSWER_ID,
        "ODP-BOL-001",
        "ODP-BOL-004",
        "downstream_updates_allowed",
        "current_owner_answers",
    ):
        assert phrase in runbook
