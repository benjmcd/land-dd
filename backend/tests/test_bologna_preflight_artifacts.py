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
CONFIG_PATH = REPO_ROOT / "config" / "bologna_preflight.yaml"


def _load_validator() -> ModuleType:
    script_path = REPO_ROOT / "scripts" / "bologna_preflight_check.py"
    spec = importlib.util.spec_from_file_location("bologna_preflight_check", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _catalog() -> dict[str, Any]:
    catalog = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    assert isinstance(catalog, dict)
    return cast(dict[str, Any], catalog)


def test_bologna_preflight_catalog_keeps_pilot_not_started() -> None:
    validator = cast(Any, _load_validator())
    catalog = _catalog()

    assert catalog["schema_version"] == "bologna_preflight_v1"
    assert catalog["operator_runbook"] == "docs/runbooks/bologna_preflight.md"
    assert catalog["status"] == "repo_local_validate_only"
    assert catalog["validation"] == "scripts/run_bologna_preflight_check.ps1"
    assert catalog["limits"] == validator.EXPECTED_LIMITS
    assert catalog["candidate"]["status"] == "not_started_external_authority_required"
    assert catalog["candidate"]["approvals"] == validator.EXPECTED_APPROVALS
    assert all(value is False for value in catalog["candidate"]["approvals"].values())


def test_bologna_preflight_gate_set_and_statuses_are_pinned() -> None:
    validator = cast(Any, _load_validator())
    catalog = _catalog()
    gates = {gate["id"]: gate for gate in catalog["preflight_gates"]}

    assert set(gates) == set(validator.EXPECTED_GATE_STATUSES)
    for gate_id, expected_status in validator.EXPECTED_GATE_STATUSES.items():
        assert gates[gate_id]["status"] == expected_status
        assert gates[gate_id]["evidence"]
        if expected_status == "repo_confirmed":
            assert gates[gate_id]["evidence_assertions"]
        else:
            assert gates[gate_id]["next_action"]
            assert gates[gate_id]["blocker_authority"]
    assert "config/bologna_source_candidates.yaml" in gates["italy_source_inventory"]["evidence"]
    assert gates["italy_source_inventory"]["status"] == "missing_candidate_decision"
    assert "config/bologna_source_rights.yaml" in gates["italy_source_rights_review"]["evidence"]
    assert (
        "config/bologna_source_authority_intake.yaml"
        in gates["italy_source_rights_review"]["evidence"]
    )
    assert gates["italy_source_rights_review"]["status"] == "blocked_external_authority"
    assert (
        "config/bologna_recorded_source_corpus.yaml"
        in gates["recorded_source_fixture_corpus"]["evidence"]
    )
    assert (
        "config/bologna_recorded_source_corpus.yaml"
        in gates["recorded_source_fixture_corpus"]["blocker_authority"]
    )


def test_bologna_preflight_validator_passes_current_artifacts() -> None:
    validator = cast(Any, _load_validator())

    assert validator.main() == 0


def test_bologna_preflight_composes_source_candidate_inventory() -> None:
    validator = cast(Any, _load_validator())

    validator.validate_source_candidates()


def test_bologna_preflight_composes_source_rights_matrix() -> None:
    validator = cast(Any, _load_validator())

    validator.validate_source_rights()


def test_bologna_preflight_composes_source_authority_intake() -> None:
    validator = cast(Any, _load_validator())

    validator.validate_source_authority_intake()


def test_bologna_preflight_composes_recorded_source_corpus_contract() -> None:
    validator = cast(Any, _load_validator())

    validator.validate_recorded_source_corpus()


def test_bologna_preflight_validator_fails_if_approval_flips(
    monkeypatch: Any,
) -> None:
    validator = cast(Any, _load_validator())
    catalog = deepcopy(_catalog())
    catalog["candidate"]["approvals"]["bologna_selected"] = True

    def fake_read_text(path: str) -> str:
        if path == "config/bologna_preflight.yaml":
            return cast(str, yaml.safe_dump(catalog))
        return (REPO_ROOT / path).read_text(encoding="utf-8")

    monkeypatch.setattr(validator, "read_text", fake_read_text)

    with pytest.raises(SystemExit, match="approval flags changed"):
        validator.validate_catalog()


def test_bologna_preflight_validator_fails_if_limit_flips(
    monkeypatch: Any,
) -> None:
    validator = cast(Any, _load_validator())
    catalog = deepcopy(_catalog())
    catalog["limits"]["selects_bologna"] = True

    def fake_read_text(path: str) -> str:
        if path == "config/bologna_preflight.yaml":
            return cast(str, yaml.safe_dump(catalog))
        return (REPO_ROOT / path).read_text(encoding="utf-8")

    monkeypatch.setattr(validator, "read_text", fake_read_text)

    with pytest.raises(SystemExit, match="limits changed"):
        validator.validate_catalog()


def test_bologna_preflight_validator_requires_gate_next_action(
    monkeypatch: Any,
) -> None:
    validator = cast(Any, _load_validator())
    catalog = deepcopy(_catalog())
    catalog["preflight_gates"][1].pop("next_action")

    def fake_read_text(path: str) -> str:
        if path == "config/bologna_preflight.yaml":
            return cast(str, yaml.safe_dump(catalog))
        return (REPO_ROOT / path).read_text(encoding="utf-8")

    monkeypatch.setattr(validator, "read_text", fake_read_text)

    with pytest.raises(SystemExit, match="next action missing"):
        validator.validate_catalog()


def test_bologna_preflight_script_and_wrappers_are_validate_only() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/bologna_preflight_check.py"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == "Bologna preflight check: ok"
    ps1 = (REPO_ROOT / "scripts" / "run_bologna_preflight_check.ps1").read_text(
        encoding="utf-8",
    )
    sh = (REPO_ROOT / "scripts" / "run_bologna_preflight_check.sh").read_text(
        encoding="utf-8",
    )
    for script in (ps1, sh):
        assert "bologna_preflight_check.py" in script
        assert "Bologna preflight check: ok" in script
    assert "New-Item" not in ps1
    assert "Remove-Item" not in ps1
    assert "mkdir" not in sh
    assert "rm " not in sh


def test_bologna_preflight_runbook_and_authority_packet_preserve_boundary() -> None:
    runbook = (REPO_ROOT / "docs" / "runbooks" / "bologna_preflight.md").read_text(
        encoding="utf-8",
    )
    packet = (REPO_ROOT / "state" / "PRODUCTION_AUTHORITY_PACKET.md").read_text(
        encoding="utf-8",
    )

    for phrase in (
        "does not select Bologna",
        "does not approve Italy sources",
        "does not approve an EU/Italy rulepack",
        "does not unblock DS-017",
        "does not claim hosted production readiness",
        "bologna_recorded_source_corpus_v1",
    ):
        assert phrase in runbook
    for phrase in (
        "Bologna Recorded-Source Pilot Authority",
        "does not approve or start Bologna",
        "Do not reuse the US homestead rulepack",
        "Do not generalize into a multi-geography framework",
    ):
        assert phrase in packet
