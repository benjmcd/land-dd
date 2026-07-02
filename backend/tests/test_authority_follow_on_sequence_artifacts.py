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
CONFIG_PATH = REPO_ROOT / "config" / "authority_follow_on_sequence.yaml"


def _load_validator() -> ModuleType:
    script_path = REPO_ROOT / "scripts" / "authority_follow_on_sequence_check.py"
    spec = importlib.util.spec_from_file_location(
        "authority_follow_on_sequence_check",
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


def test_authority_follow_on_sequence_current_artifacts_validate() -> None:
    validator = cast(Any, _load_validator())

    assert validator.main() == 0


def test_authority_follow_on_sequence_is_validate_only_and_blocked() -> None:
    validator = cast(Any, _load_validator())
    catalog = _catalog()

    assert catalog["schema_version"] == "authority_follow_on_sequence_v1"
    assert catalog["status"] == "blocked_waiting_for_external_authority"
    assert catalog["source_packet"] == "state/PRODUCTION_AUTHORITY_PACKET.md"
    assert catalog["source_intake"] == "config/production_authority_intake.yaml"
    assert catalog["validation"] == "scripts/run_authority_follow_on_sequence_check.ps1"
    assert catalog["limits"] == validator.EXPECTED_LIMITS
    assert catalog["sequence_policy"]["blocked_boundaries"] == [
        "ds017_approval",
        "bologna_owner_decisions",
        "bologna_source_rights",
        "bologna_recorded_corpus",
        "bologna_db_report_proof",
        "hosted_readiness",
        "level_10_authority",
        "qualification_pass",
        "owner_decision_unfreeze",
        "p0_unblock",
    ]


def test_authority_follow_on_sequence_covers_packet_map_and_authority_streams() -> None:
    validator = cast(Any, _load_validator())
    catalog = _catalog()
    packet_rows = validator.parse_follow_on_map(
        (REPO_ROOT / "state" / "PRODUCTION_AUTHORITY_PACKET.md").read_text(
            encoding="utf-8",
        ),
    )
    streams = set(validator.production_streams())
    lanes = {lane["id"]: lane for lane in catalog["follow_on_lanes"]}

    assert set(lanes) == validator.EXPECTED_LANES
    assert {
        lane["authority_received"] for lane in catalog["follow_on_lanes"]
    } == set(packet_rows)
    assert set().union(*(set(lane["authority_streams"]) for lane in lanes.values())) == streams
    assert lanes["production_workload_retention_follow_on"]["authority_streams"] == []
    assert lanes["production_workload_retention_follow_on"]["packet_only_authority_area"] is True
    assert lanes["bologna_recorded_source_pilot_follow_on"]["authority_streams"] == [
        "bologna_pilot_scope",
        "bologna_recorded_source",
    ]


def test_authority_follow_on_sequence_fails_closed_if_lane_unblocked() -> None:
    validator = cast(Any, _load_validator())
    catalog = deepcopy(_catalog())
    catalog["follow_on_lanes"][0]["status"] = "ready"

    with pytest.raises(SystemExit, match="must remain blocked waiting for authority"):
        validator.validate_catalog(catalog)


def test_authority_follow_on_sequence_fails_closed_if_stream_not_covered() -> None:
    validator = cast(Any, _load_validator())
    catalog = deepcopy(_catalog())
    catalog["follow_on_lanes"][0]["authority_streams"] = []

    with pytest.raises(SystemExit, match="must reference a production authority stream"):
        validator.validate_catalog(catalog)


def test_authority_follow_on_sequence_fails_closed_if_packet_map_drifts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    validator = cast(Any, _load_validator())
    original_read_text = validator.read_text

    def fake_read_text(path_text: str) -> str:
        text = cast(str, original_read_text(path_text))
        if path_text == "state/PRODUCTION_AUTHORITY_PACKET.md":
            return text.replace(
                "Source review, registry/seed updates, entitlement tests",
                "Source review, registry updates, entitlement tests",
            )
        return text

    monkeypatch.setattr(validator, "read_text", fake_read_text)

    with pytest.raises(SystemExit, match="follow-on text drifted from packet"):
        validator.validate_catalog(_catalog())


def test_authority_follow_on_sequence_script_and_wrappers_are_validate_only() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/authority_follow_on_sequence_check.py"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == "authority follow-on sequence check: ok"
    ps1 = (
        REPO_ROOT / "scripts" / "run_authority_follow_on_sequence_check.ps1"
    ).read_text(encoding="utf-8")
    sh = (
        REPO_ROOT / "scripts" / "run_authority_follow_on_sequence_check.sh"
    ).read_text(encoding="utf-8")
    for script in (ps1, sh):
        assert "authority_follow_on_sequence_check.py" in script
        assert "authority follow-on sequence" in script
    assert "New-Item" not in ps1
    assert "Remove-Item" not in ps1
    assert "mkdir" not in sh
    assert "rm " not in sh
