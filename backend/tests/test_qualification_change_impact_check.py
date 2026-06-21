from __future__ import annotations

import contextlib
import importlib
import importlib.util
import io
from pathlib import Path
from types import ModuleType
from typing import Any, cast

yaml = cast(Any, importlib.import_module("yaml"))

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = REPO_ROOT / "config" / "qualification" / "criterion_catalog.yaml"
CHANGE_MATRIX_PATH = REPO_ROOT / "config" / "qualification" / "change_impact_matrix.yaml"
CROSSWALK_PATH = REPO_ROOT / "config" / "qualification" / "readiness_crosswalk.yaml"


def _load_script() -> ModuleType:
    path = REPO_ROOT / "scripts" / "qualification_change_impact_check.py"
    spec = importlib.util.spec_from_file_location(
        "qualification_change_impact_check_under_test",
        path,
    )
    assert spec is not None
    loader = spec.loader
    assert loader is not None
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def _yaml(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], yaml.safe_load(path.read_text(encoding="utf-8")))


def test_changed_readiness_paths_report_matrix_and_crosswalk_impacts() -> None:
    module = _load_script()
    report = module.analyze_changed_paths(
        root=REPO_ROOT,
        changed_paths=[
            "config/release_readiness.yaml",
            "scripts/source_readiness.py",
        ],
        change_matrix=_yaml(CHANGE_MATRIX_PATH),
        crosswalk=_yaml(CROSSWALK_PATH),
        catalog=_yaml(CATALOG_PATH),
    )

    assert "DEPLOYMENT_INFRASTRUCTURE" in report.change_classes
    assert "SOURCE_SCHEMA_OR_CONNECTOR" in report.change_classes
    assert "O-001" in report.invalidate_criterion_ids
    assert "Q1-027" in report.invalidate_criterion_ids
    assert "release_readiness" in report.surface_ids
    assert "source_readiness" in report.surface_ids
    assert "G-016" in report.surface_criterion_ids
    assert "DQ-018" in report.surface_criterion_ids
    assert report.unmatched_paths == []


def test_current_core_backend_paths_map_to_change_classes() -> None:
    module = _load_script()
    report = module.analyze_changed_paths(
        root=REPO_ROOT,
        changed_paths=[
            "backend/app/connectors/fema_nfhl.py",
            "backend/tests/connectors/test_fema_nfhl_connector.py",
            "backend/app/claims_engine/rule_engine.py",
            "backend/tests/claims_engine/test_rule_engine.py",
            "backend/app/area_geometry/geometry_validator.py",
            "backend/tests/area_geometry/test_area_service.py",
            "backend/app/evidence_ledger/service.py",
            "backend/tests/evidence_ledger/test_evidence_service.py",
            "scripts/verify.sh",
            "scripts/verify.ps1",
        ],
        change_matrix=_yaml(CHANGE_MATRIX_PATH),
        crosswalk=_yaml(CROSSWALK_PATH),
        catalog=_yaml(CATALOG_PATH),
    )

    assert (
        report.path_impacts["backend/app/connectors/fema_nfhl.py"]["change_classes"]
        == ["SOURCE_SCHEMA_OR_CONNECTOR"]
    )
    assert (
        report.path_impacts["backend/tests/connectors/test_fema_nfhl_connector.py"][
            "change_classes"
        ]
        == ["SOURCE_SCHEMA_OR_CONNECTOR"]
    )
    assert (
        report.path_impacts["backend/app/claims_engine/rule_engine.py"]["change_classes"]
        == ["RULE_OR_CONFIDENCE_SEMANTICS"]
    )
    assert (
        report.path_impacts["backend/tests/claims_engine/test_rule_engine.py"][
            "change_classes"
        ]
        == ["RULE_OR_CONFIDENCE_SEMANTICS"]
    )
    assert (
        report.path_impacts["backend/app/area_geometry/geometry_validator.py"][
            "change_classes"
        ]
        == ["AOI_IDENTITY_OR_GEOMETRY"]
    )
    assert (
        report.path_impacts["backend/tests/area_geometry/test_area_service.py"][
            "change_classes"
        ]
        == ["AOI_IDENTITY_OR_GEOMETRY"]
    )
    assert (
        report.path_impacts["backend/app/evidence_ledger/service.py"]["change_classes"]
        == ["REPORT_OR_CAVEAT_SEMANTICS"]
    )
    assert (
        report.path_impacts["backend/tests/evidence_ledger/test_evidence_service.py"][
            "change_classes"
        ]
        == ["REPORT_OR_CAVEAT_SEMANTICS"]
    )
    assert "DEPLOYMENT_INFRASTRUCTURE" in report.path_impacts["scripts/verify.sh"][
        "change_classes"
    ]
    assert "DEPLOYMENT_INFRASTRUCTURE" in report.path_impacts["scripts/verify.ps1"][
        "change_classes"
    ]
    assert "WINDOWS_TOOLING_OR_LOCAL_RUNTIME" in report.path_impacts["scripts/verify.ps1"][
        "change_classes"
    ]
    assert report.unmatched_paths == []


def test_unmatched_docs_path_reports_no_false_invalidation() -> None:
    module = _load_script()
    report = module.analyze_changed_paths(
        root=REPO_ROOT,
        changed_paths=["docs/misc/typo.md"],
        change_matrix=_yaml(CHANGE_MATRIX_PATH),
        crosswalk=_yaml(CROSSWALK_PATH),
        catalog=_yaml(CATALOG_PATH),
    )

    assert report.change_classes == []
    assert report.invalidate_criterion_ids == []
    assert report.surface_criterion_ids == []
    assert report.unmatched_paths == ["docs/misc/typo.md"]


def test_unsafe_changed_path_fails_closed() -> None:
    module = _load_script()

    try:
        module.analyze_changed_paths(
            root=REPO_ROOT,
            changed_paths=["../outside.yaml"],
            change_matrix=_yaml(CHANGE_MATRIX_PATH),
            crosswalk=_yaml(CROSSWALK_PATH),
            catalog=_yaml(CATALOG_PATH),
        )
    except module.QualificationChangeImpactError as exc:
        assert "changed path escapes repo" in str(exc)
    else:
        raise AssertionError("unsafe changed path should fail closed")


def test_cli_prints_advisory_report_and_exits_zero() -> None:
    module = _load_script()
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        exit_code = module.main(
            [
                "--root",
                str(REPO_ROOT),
                "--changed-path",
                "config/release_readiness.yaml",
                "--changed-path",
                "scripts/source_readiness.py",
            ],
        )
    output = stdout.getvalue()

    assert exit_code == 0
    assert "qualification change impact: advisory" in output
    assert "DEPLOYMENT_INFRASTRUCTURE" in output
    assert "SOURCE_SCHEMA_OR_CONNECTOR" in output
    assert "release_readiness" in output
    assert "source_readiness" in output
