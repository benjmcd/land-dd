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
    spec.loader.exec_module(module)
    return module


def _yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return cast(dict[str, Any], payload)


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
