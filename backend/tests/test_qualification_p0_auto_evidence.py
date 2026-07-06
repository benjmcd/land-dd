from __future__ import annotations

import contextlib
import importlib
import importlib.util
import io
from copy import deepcopy
from pathlib import Path
from types import ModuleType
from typing import Any, cast

yaml = cast(Any, importlib.import_module("yaml"))

REPO_ROOT = Path(__file__).resolve().parents[2]
AUTO_EVIDENCE_PATH = REPO_ROOT / "docs" / "qualification" / "P0_AUTO_EVIDENCE.yaml"
STATUS_PATH = REPO_ROOT / "state" / "EMPIRICAL_QUALIFICATION_STATUS.yaml"
BACKLOG_PATH = REPO_ROOT / "state" / "QUALIFICATION_PARAMETERIZATION_BACKLOG.md"
CATALOG_PATH = REPO_ROOT / "config" / "qualification" / "criterion_catalog.yaml"
AUTO_EVIDENCE_IDS = ("P0-004", "P0-005", "P0-021", "P0-023")


def _load_script(path: Path, module_name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None
    loader = spec.loader
    assert loader is not None
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def _yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return cast(dict[str, Any], payload)


def _catalog_by_id() -> dict[str, dict[str, Any]]:
    catalog = _yaml(CATALOG_PATH)
    return {
        str(item["criterion_id"]): item
        for item in catalog["criteria"]
        if isinstance(item, dict) and item.get("criterion_id")
    }


def test_p0_auto_evidence_artifact_records_live_catalog_rows() -> None:
    artifact = _yaml(AUTO_EVIDENCE_PATH)
    catalog = _catalog_by_id()

    assert artifact["schema_version"] == "qualification_p0_auto_evidence_v1"
    assert artifact["effective_gate_status"] == "NOT_RUN"
    assert artifact["result_claimed"] is False
    assert artifact["status_reference"] == "state/EMPIRICAL_QUALIFICATION_STATUS.yaml"

    rows = artifact["criteria"]
    assert [row["criterion_id"] for row in rows] == list(AUTO_EVIDENCE_IDS)

    for row in rows:
        criterion = catalog[row["criterion_id"]]
        assert row["catalog_gate_id"] == "P0"
        assert row["catalog_requirement_class"] == "INVARIANT"
        assert row["catalog_statement"] == criterion["statement"]
        assert row["evidence_status"] == "auto_evidenced_p0_not_run"
        assert row["effective_status"] == "NOT_RUN"
        assert row["pass_claimed"] is False
        assert "P0 remains NOT_RUN" in " ".join(row["caveats"])

        evidence = row["evidence"]
        assert evidence
        for record in evidence:
            path_text = record["path"]
            assert not Path(path_text).is_absolute()
            assert (REPO_ROOT / path_text).exists()
            assert record["signal"].strip()


def test_p0_status_and_backlog_link_auto_evidence_without_result_pass() -> None:
    status = _yaml(STATUS_PATH)
    p0 = status["qualifications"]["p0"]

    assert p0["status"] == "NOT_RUN"
    assert p0["result_path"] is None
    assert p0["blocker_references"] == []

    backlog = BACKLOG_PATH.read_text(encoding="utf-8")
    for criterion_id in AUTO_EVIDENCE_IDS:
        assert f"`{criterion_id}`" in backlog
        assert f"`{criterion_id}` | auto-evidenced; P0 not run" in backlog


def test_p0_auto_evidence_checker_passes() -> None:
    checker = _load_script(
        REPO_ROOT / "scripts" / "qualification_p0_evidence_check.py",
        "qualification_p0_evidence_check_under_test",
    )
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        exit_code = checker.main(["--root", str(REPO_ROOT)])
    output = stdout.getvalue()

    assert exit_code == 0, output
    assert "qualification P0 auto evidence check: ok" in output
    assert "effective P0 status: NOT_RUN" in output


def test_p0_auto_evidence_checker_rejects_stale_status_blocker_link() -> None:
    checker = _load_script(
        REPO_ROOT / "scripts" / "qualification_p0_evidence_check.py",
        "qualification_p0_evidence_check_mutation_under_test",
    )
    status = deepcopy(_yaml(STATUS_PATH))
    status["qualifications"]["p0"]["blocker_references"] = [
        "docs/qualification/P0_AUTO_EVIDENCE.yaml",
    ]

    errors: list[str] = []
    checker.validate_status_link(REPO_ROOT, status, errors)

    assert any("blocker_references must remain empty" in error for error in errors)
