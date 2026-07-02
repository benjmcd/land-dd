from __future__ import annotations

import importlib
import re
from pathlib import Path
from typing import Any, cast

yaml = cast(Any, importlib.import_module("yaml"))

REPO_ROOT = Path(__file__).resolve().parents[2]
CROSSWALK_PATH = REPO_ROOT / "config" / "qualification" / "readiness_crosswalk.yaml"
CROSSWALK_DOC_PATH = REPO_ROOT / "docs" / "qualification" / "readiness-crosswalk.md"
CATALOG_PATH = REPO_ROOT / "config" / "qualification" / "criterion_catalog.yaml"
CHANGE_MATRIX_PATH = (
    REPO_ROOT / "config" / "qualification" / "change_impact_matrix.yaml"
)
CI_WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "ci.yml"
REQUIRED_CONFIG_GLOBS = {
    "config/*readiness*.yaml",
    "config/*authority*.yaml",
    "config/*entitlement*.yaml",
    "config/bologna_*.yaml",
}
REQUIRED_CHECKER_GLOBS = {
    "scripts/*readiness*_check.py",
    "scripts/*authority*_check.py",
    "scripts/*entitlement*_check.py",
    "scripts/bologna_*_check.py",
}
QUALIFICATION_CONTROL_GATES = {
    "scripts/run_qualification_selftest.sh",
    "scripts/run_qualification_validate.sh",
    "scripts/run_qualification_status_check.sh",
    "scripts/run_qualification_change_impact_check.sh",
    "scripts/run_qualification_p0_evidence_check.sh",
}
RELEASE_GATE_PROOF_RE = re.compile(r"^scripts/run_[A-Za-z0-9_]+\.(?:ps1|sh)$")


def _yaml(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], yaml.safe_load(path.read_text(encoding="utf-8")))


def _catalog_ids() -> set[str]:
    catalog = _yaml(CATALOG_PATH)
    return {item["criterion_id"] for item in catalog["criteria"]}


def _glob_paths(patterns: list[str]) -> set[str]:
    paths: set[str] = set()
    for pattern in patterns:
        paths.update(
            path.relative_to(REPO_ROOT).as_posix()
            for path in REPO_ROOT.glob(pattern)
            if path.is_file()
        )
    return paths


def _ci_gate_paths() -> set[str]:
    workflow = CI_WORKFLOW_PATH.read_text(encoding="utf-8")
    paths = {
        match.group(1)
        for match in re.finditer(r"\./(scripts/run_[A-Za-z0-9_]+\.sh)", workflow)
    }
    return paths - QUALIFICATION_CONTROL_GATES


def _release_gate_paths() -> set[str]:
    release = _yaml(REPO_ROOT / "config" / "release_readiness.yaml")
    return {
        check["proof"]
        for check in release["required_checks"]
        if RELEASE_GATE_PROOF_RE.match(check["proof"])
    }


def test_readiness_crosswalk_covers_live_inventory_and_catalog_ids() -> None:
    crosswalk = _yaml(CROSSWALK_PATH)
    catalog_ids = _catalog_ids()

    assert crosswalk["schema_version"] == "qualification_readiness_crosswalk_v1"
    assert REQUIRED_CONFIG_GLOBS <= set(crosswalk["inventory"]["config_globs"])
    assert REQUIRED_CHECKER_GLOBS <= set(crosswalk["inventory"]["checker_globs"])
    entry_ids = [entry["surface_id"] for entry in crosswalk["entries"]]
    assert len(entry_ids) == len(set(entry_ids))
    assert crosswalk["orphaned_surfaces"] == []

    mapped_configs = {
        path
        for entry in crosswalk["entries"]
        for path in entry.get("config_paths", [])
    }
    mapped_checkers = {
        path
        for entry in crosswalk["entries"]
        for path in entry.get("checker_paths", [])
    }
    excluded = set(crosswalk["inventory"]["intentional_exclusions"])

    expected_configs = _glob_paths(crosswalk["inventory"]["config_globs"])
    expected_checkers = _glob_paths(crosswalk["inventory"]["checker_globs"])

    assert expected_configs - mapped_configs - excluded == set()
    assert expected_checkers - mapped_checkers - excluded == set()

    for entry in crosswalk["entries"]:
        assert set(entry["criterion_ids"]) <= catalog_ids
        assert entry["evidence_role"] in {
            "feeds_status",
            "deployment_gate",
            "authority_blocker",
            "static_guardrail",
        }


def test_readiness_crosswalk_maps_ci_and_release_gate_paths() -> None:
    crosswalk = _yaml(CROSSWALK_PATH)
    expected_gate_paths = _ci_gate_paths() | _release_gate_paths()
    mapped_gate_paths = {
        path
        for entry in crosswalk["entries"]
        for path in entry.get("gate_paths", [])
    }

    assert {
        "scripts/run_provenance_check.sh",
        "scripts/run_security_scan.sh",
        "scripts/run_backup_restore_check.ps1",
    } <= mapped_gate_paths
    assert expected_gate_paths - mapped_gate_paths == set()
    for gate_path in mapped_gate_paths:
        assert (REPO_ROOT / gate_path).is_file(), gate_path


def test_readiness_crosswalk_doc_lists_surfaces_gaps_and_orphans() -> None:
    crosswalk = _yaml(CROSSWALK_PATH)
    doc = CROSSWALK_DOC_PATH.read_text(encoding="utf-8")

    assert "## Mapped Surfaces" in doc
    assert "## Gaps" in doc
    assert "## Orphans" in doc
    assert "does not satisfy or pass the mapped criteria" in doc
    for entry in crosswalk["entries"]:
        assert entry["surface_id"] in doc
        for criterion_id in entry["criterion_ids"]:
            assert criterion_id in doc


def test_change_impact_matrix_invalidation_targets_are_catalog_criteria() -> None:
    catalog_ids = _catalog_ids()
    matrix = _yaml(CHANGE_MATRIX_PATH)

    assert matrix["schema_version"] == "qualification_change_impact_v3"
    for change_class, entry in matrix["change_classes"].items():
        invalidates = entry["invalidate_by_default"]
        path_globs = entry.get("path_globs", [])
        if change_class == "DOCS_NONSEMANTIC":
            assert path_globs == []
            assert invalidates == []
            continue
        assert path_globs, change_class
        assert all(isinstance(pattern, str) and pattern for pattern in path_globs)
        assert invalidates, change_class
        assert set(invalidates) <= catalog_ids, change_class
