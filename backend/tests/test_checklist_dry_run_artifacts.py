from __future__ import annotations

import importlib
import importlib.util
import subprocess
from copy import deepcopy
from pathlib import Path
from types import ModuleType
from typing import Any, cast

import pytest

yaml = cast(Any, importlib.import_module("yaml"))

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = REPO_ROOT / "config" / "checklist_dry_run.yaml"


def _load_validator() -> ModuleType:
    script_path = REPO_ROOT / "scripts" / "checklist_dry_run_check.py"
    spec = importlib.util.spec_from_file_location("checklist_dry_run_check", script_path)
    assert spec is not None
    loader = spec.loader
    assert loader is not None
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def _load_release_validator() -> ModuleType:
    script_path = REPO_ROOT / "scripts" / "release_readiness_check.py"
    spec = importlib.util.spec_from_file_location("release_readiness_check", script_path)
    assert spec is not None
    loader = spec.loader
    assert loader is not None
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def _catalog() -> dict[str, Any]:
    catalog = yaml.safe_load(CATALOG_PATH.read_text(encoding="utf-8"))
    assert isinstance(catalog, dict)
    return cast(dict[str, Any], catalog)


def test_checklist_dry_run_catalog_covers_source_checklists() -> None:
    validator = cast(Any, _load_validator())
    catalog = _catalog()

    assert catalog["schema_version"] == "checklist_dry_run_v1"
    assert catalog["operator_runbook"] == "docs/runbooks/checklist_dry_run.md"
    assert catalog["status"] == "repo_local_validate_only"
    assert catalog["validation"] == "scripts/run_checklist_dry_run_check.ps1"
    assert catalog["limits"] == validator.EXPECTED_LIMITS
    assert catalog["candidate_shape"]["status"] == "hypothetical_not_selected"
    assert all(value is False for value in catalog["candidate_shape"]["approvals"].values())

    checklists = {checklist["id"]: checklist for checklist in catalog["checklists"]}
    assert checklists.keys() == validator.REQUIRED_CHECKLISTS.keys()
    for checklist_id, checklist in checklists.items():
        source = validator.REQUIRED_CHECKLISTS[checklist_id]
        source_item_ids = validator.checklist_item_ids(source)
        catalog_item_ids = {item["item_id"] for item in checklist["dry_run"]}

        assert checklist["source"] == source
        assert checklist["scope"] == "intentionally_scoped_pre_expansion_gate"
        assert catalog_item_ids == source_item_ids
        for item in checklist["dry_run"]:
            if item["status"] == "repo_confirmed":
                assert item["evidence_assertions"]


def test_checklist_parser_covers_checked_and_unchecked_items(
    monkeypatch: Any,
) -> None:
    validator = cast(Any, _load_validator())

    monkeypatch.setattr(
        validator,
        "read_text",
        lambda _path: "\n".join(
            (
                "- [ ] First candidate item",
                "- [x] Completed-looking item",
                "- [X] Uppercase completed-looking item",
            ),
        ),
    )

    assert validator.checklist_item_ids("sample.md") == {
        "first_candidate_item",
        "completed_looking_item",
        "uppercase_completed_looking_item",
    }


def test_checklist_parser_covers_unordered_and_ordered_checkbox_markers(
    monkeypatch: Any,
) -> None:
    validator = cast(Any, _load_validator())

    monkeypatch.setattr(
        validator,
        "read_text",
        lambda _path: "\n".join(
            (
                "* [ ] Star marker item",
                "+ [x] Plus marker item",
                "1. [ ] Ordered marker item",
                "2. [X] Ordered complete item",
            ),
        ),
    )

    assert validator.checklist_item_ids("sample.md") == {
        "star_marker_item",
        "plus_marker_item",
        "ordered_marker_item",
        "ordered_complete_item",
    }


def test_checklist_parser_fails_closed_on_unsupported_checkbox_marker(
    monkeypatch: Any,
) -> None:
    validator = cast(Any, _load_validator())

    monkeypatch.setattr(
        validator,
        "read_text",
        lambda _path: "- [-] Unsupported checkbox marker",
    )

    with pytest.raises(SystemExit, match="unsupported checkbox marker"):
        validator.checklist_item_ids("sample.md")


def test_checklist_dry_run_validator_rejects_repo_root_escape(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    validator = cast(Any, _load_validator())
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (tmp_path / "outside.md").write_text("not repo evidence\n", encoding="utf-8")
    monkeypatch.setattr(validator, "ROOT", repo_root)

    with pytest.raises(SystemExit, match="outside repository root"):
        validator.require_existing("../outside.md")


def test_checklist_dry_run_validator_rejects_empty_evidence_path(
    monkeypatch: Any,
) -> None:
    validator = cast(Any, _load_validator())
    catalog = deepcopy(_catalog())
    jurisdiction = next(
        checklist
        for checklist in catalog["checklists"]
        if checklist["id"] == "jurisdiction_readiness"
    )
    jurisdiction["dry_run"][0]["evidence"][0] = ""

    def fake_read_text(path: str) -> str:
        if path == "config/checklist_dry_run.yaml":
            return cast(str, yaml.safe_dump(catalog))
        return (REPO_ROOT / path).read_text(encoding="utf-8")

    monkeypatch.setattr(validator, "read_text", fake_read_text)

    with pytest.raises(SystemExit, match="artifact path missing"):
        validator.validate_catalog()


def test_checklist_dry_run_validator_rejects_directory_blocker_authority(
    monkeypatch: Any,
) -> None:
    validator = cast(Any, _load_validator())
    catalog = deepcopy(_catalog())
    jurisdiction = next(
        checklist
        for checklist in catalog["checklists"]
        if checklist["id"] == "jurisdiction_readiness"
    )
    blocked = next(
        item
        for item in jurisdiction["dry_run"]
        if item["status"] == "blocked_external_authority"
    )
    blocked["blocker_authority"][0] = "docs"

    def fake_read_text(path: str) -> str:
        if path == "config/checklist_dry_run.yaml":
            return cast(str, yaml.safe_dump(catalog))
        return (REPO_ROOT / path).read_text(encoding="utf-8")

    monkeypatch.setattr(validator, "read_text", fake_read_text)

    with pytest.raises(SystemExit, match="must be a file"):
        validator.validate_catalog()


def test_checklist_dry_run_validator_requires_wrappers() -> None:
    validator = cast(Any, _load_validator())

    assert "scripts/run_checklist_dry_run_check.ps1" in validator.REQUIRED_FILES
    assert "scripts/run_checklist_dry_run_check.sh" in validator.REQUIRED_FILES


def test_checklist_dry_run_validator_fails_when_required_wrapper_missing(
    monkeypatch: Any,
) -> None:
    validator = cast(Any, _load_validator())

    monkeypatch.setattr(
        validator,
        "REQUIRED_FILES",
        ("scripts/run_checklist_dry_run_check.ps1",),
    )

    def fake_require_existing(path: str) -> None:
        raise SystemExit(f"missing wrapper: {path}")

    monkeypatch.setattr(validator, "require_existing", fake_require_existing)

    with pytest.raises(SystemExit, match="missing wrapper"):
        validator.validate_required_files()


def test_checklist_dry_run_validator_fails_closed_for_missing_item(
    monkeypatch: Any,
) -> None:
    validator = cast(Any, _load_validator())
    catalog = deepcopy(_catalog())
    jurisdiction = next(
        checklist
        for checklist in catalog["checklists"]
        if checklist["id"] == "jurisdiction_readiness"
    )
    jurisdiction["dry_run"] = jurisdiction["dry_run"][1:]

    def fake_read_text(path: str) -> str:
        if path == "config/checklist_dry_run.yaml":
            return cast(str, yaml.safe_dump(catalog))
        return (REPO_ROOT / path).read_text(encoding="utf-8")

    monkeypatch.setattr(validator, "read_text", fake_read_text)

    with pytest.raises(SystemExit, match="dry-run coverage mismatch"):
        validator.validate_catalog()


def test_checklist_dry_run_validator_fails_closed_for_flipped_limit(
    monkeypatch: Any,
) -> None:
    validator = cast(Any, _load_validator())
    catalog = deepcopy(_catalog())
    catalog["limits"]["selects_new_geography"] = True

    def fake_read_text(path: str) -> str:
        if path == "config/checklist_dry_run.yaml":
            return cast(str, yaml.safe_dump(catalog))
        return (REPO_ROOT / path).read_text(encoding="utf-8")

    monkeypatch.setattr(validator, "read_text", fake_read_text)

    with pytest.raises(SystemExit, match="limits changed"):
        validator.validate_catalog()


def test_checklist_dry_run_validator_requires_blocker_next_action(
    monkeypatch: Any,
) -> None:
    validator = cast(Any, _load_validator())
    catalog = deepcopy(_catalog())
    jurisdiction = next(
        checklist
        for checklist in catalog["checklists"]
        if checklist["id"] == "jurisdiction_readiness"
    )
    jurisdiction["dry_run"][0].pop("next_action")

    def fake_read_text(path: str) -> str:
        if path == "config/checklist_dry_run.yaml":
            return cast(str, yaml.safe_dump(catalog))
        return (REPO_ROOT / path).read_text(encoding="utf-8")

    monkeypatch.setattr(validator, "read_text", fake_read_text)

    with pytest.raises(SystemExit, match="next action missing"):
        validator.validate_catalog()


def test_checklist_dry_run_validator_requires_repo_confirmed_assertions(
    monkeypatch: Any,
) -> None:
    validator = cast(Any, _load_validator())
    catalog = deepcopy(_catalog())
    rulepack = next(
        checklist
        for checklist in catalog["checklists"]
        if checklist["id"] == "rulepack_readiness"
    )
    confirmed = next(item for item in rulepack["dry_run"] if item["status"] == "repo_confirmed")
    confirmed.pop("evidence_assertions")

    def fake_read_text(path: str) -> str:
        if path == "config/checklist_dry_run.yaml":
            return cast(str, yaml.safe_dump(catalog))
        return (REPO_ROOT / path).read_text(encoding="utf-8")

    monkeypatch.setattr(validator, "read_text", fake_read_text)

    with pytest.raises(SystemExit, match="evidence assertions missing"):
        validator.validate_catalog()


def test_checklist_dry_run_validator_fails_closed_for_stale_assertion(
    monkeypatch: Any,
) -> None:
    validator = cast(Any, _load_validator())
    catalog = deepcopy(_catalog())
    rulepack = next(
        checklist
        for checklist in catalog["checklists"]
        if checklist["id"] == "rulepack_readiness"
    )
    confirmed = next(item for item in rulepack["dry_run"] if item["status"] == "repo_confirmed")
    confirmed["evidence_assertions"][0]["contains"] = "not present in cited evidence"

    def fake_read_text(path: str) -> str:
        if path == "config/checklist_dry_run.yaml":
            return cast(str, yaml.safe_dump(catalog))
        return (REPO_ROOT / path).read_text(encoding="utf-8")

    monkeypatch.setattr(validator, "read_text", fake_read_text)

    with pytest.raises(SystemExit, match="assertion missing text"):
        validator.validate_catalog()


def test_checklist_dry_run_validator_rejects_empty_contains_assertion(
    monkeypatch: Any,
) -> None:
    validator = cast(Any, _load_validator())
    catalog = deepcopy(_catalog())
    rulepack = next(
        checklist
        for checklist in catalog["checklists"]
        if checklist["id"] == "rulepack_readiness"
    )
    confirmed = next(item for item in rulepack["dry_run"] if item["status"] == "repo_confirmed")
    confirmed["evidence_assertions"][0]["contains"] = ""

    def fake_read_text(path: str) -> str:
        if path == "config/checklist_dry_run.yaml":
            return cast(str, yaml.safe_dump(catalog))
        return (REPO_ROOT / path).read_text(encoding="utf-8")

    monkeypatch.setattr(validator, "read_text", fake_read_text)

    with pytest.raises(SystemExit, match="contains must be non-empty"):
        validator.validate_catalog()


def test_checklist_dry_run_validator_rejects_empty_regex_assertion(
    monkeypatch: Any,
) -> None:
    validator = cast(Any, _load_validator())
    catalog = deepcopy(_catalog())
    rulepack = next(
        checklist
        for checklist in catalog["checklists"]
        if checklist["id"] == "rulepack_readiness"
    )
    confirmed = next(item for item in rulepack["dry_run"] if item["status"] == "repo_confirmed")
    assertion = confirmed["evidence_assertions"][0]
    assertion.pop("contains")
    assertion["regex"] = " "

    def fake_read_text(path: str) -> str:
        if path == "config/checklist_dry_run.yaml":
            return cast(str, yaml.safe_dump(catalog))
        return (REPO_ROOT / path).read_text(encoding="utf-8")

    monkeypatch.setattr(validator, "read_text", fake_read_text)

    with pytest.raises(SystemExit, match="regex must be non-empty"):
        validator.validate_catalog()


def test_checklist_dry_run_validator_rejects_self_referential_blocker_authority(
    monkeypatch: Any,
) -> None:
    validator = cast(Any, _load_validator())
    catalog = deepcopy(_catalog())
    jurisdiction = next(
        checklist
        for checklist in catalog["checklists"]
        if checklist["id"] == "jurisdiction_readiness"
    )
    blocked = next(
        item
        for item in jurisdiction["dry_run"]
        if item["status"] == "blocked_external_authority"
    )
    blocked["blocker_authority"] = [jurisdiction["source"]]

    def fake_read_text(path: str) -> str:
        if path == "config/checklist_dry_run.yaml":
            return cast(str, yaml.safe_dump(catalog))
        return (REPO_ROOT / path).read_text(encoding="utf-8")

    monkeypatch.setattr(validator, "read_text", fake_read_text)

    with pytest.raises(SystemExit, match="cannot point only at checklist"):
        validator.validate_catalog()


def test_checklist_dry_run_runbook_records_validate_only_limits() -> None:
    runbook = (REPO_ROOT / "docs" / "runbooks" / "checklist_dry_run.md").read_text(
        encoding="utf-8",
    )

    for phrase in (
        "run_checklist_dry_run_check.ps1",
        "checklist_dry_run_v1",
        "validate-only",
        "hypothetical_not_selected",
        "missing_candidate_decision",
        "missing_repo_evidence",
        "blocked_external_authority",
        "not_applicable_existing_scope",
        "does not approve a new geography",
        "does not approve a new rulepack",
        "does not unblock DS-017",
        "does not claim hosted production readiness",
    ):
        assert phrase in runbook


def test_checklist_dry_run_scripts_exist_and_delegate_to_shared_validator() -> None:
    for script_name in (
        "run_checklist_dry_run_check.ps1",
        "run_checklist_dry_run_check.sh",
    ):
        script = (REPO_ROOT / "scripts" / script_name).read_text(encoding="utf-8")
        assert "checklist_dry_run_check.py" in script
        assert "checklist dry-run check: ok" in script


def test_release_readiness_composes_checklist_dry_run() -> None:
    release_catalog = yaml.safe_load(
        (REPO_ROOT / "config" / "release_readiness.yaml").read_text(
            encoding="utf-8",
        ),
    )
    check_ids = {check["id"] for check in release_catalog["required_checks"]}

    assert "checklist_dry_run" in check_ids
    assert (
        REPO_ROOT / "scripts" / "run_checklist_dry_run_check.ps1"
    ).exists()

    validator = (REPO_ROOT / "scripts" / "release_readiness_check.py").read_text(
        encoding="utf-8",
    )
    runbook = (REPO_ROOT / "docs" / "runbooks" / "release_readiness.md").read_text(
        encoding="utf-8",
    )
    assert "scripts/checklist_dry_run_check.py" in validator
    assert "run_checklist_dry_run_check.ps1" in runbook


def test_release_readiness_fails_if_checklist_dry_run_validator_fails(
    monkeypatch: Any,
) -> None:
    validator = cast(Any, _load_release_validator())

    def fake_run(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[Any]:
        if args[1] == "scripts/checklist_dry_run_check.py":
            raise subprocess.CalledProcessError(returncode=1, cmd=args)
        return subprocess.CompletedProcess(args=args, returncode=0)

    monkeypatch.setattr(validator.subprocess, "run", fake_run)

    with pytest.raises(subprocess.CalledProcessError):
        validator.validate_composed_contracts()
