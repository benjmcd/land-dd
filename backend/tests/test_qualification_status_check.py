from __future__ import annotations

import importlib
import importlib.util
import sys
from copy import deepcopy
from pathlib import Path
from types import ModuleType
from typing import Any, cast

yaml = cast(Any, importlib.import_module("yaml"))

REPO_ROOT = Path(__file__).resolve().parents[2]
STATUS_PATH = REPO_ROOT / "state" / "EMPIRICAL_QUALIFICATION_STATUS.yaml"
TARGETS_PATH = REPO_ROOT / "config" / "qualification" / "qualification_targets.yaml"
CATALOG_PATH = REPO_ROOT / "config" / "qualification" / "criterion_catalog.yaml"
CROSSWALK_PATH = REPO_ROOT / "config" / "qualification" / "readiness_crosswalk.yaml"
RUBRICS_PATH = REPO_ROOT / "config" / "qualification" / "judgment_rubrics.yaml"
DOMAIN_PROFILES_DIR = REPO_ROOT / "config" / "qualification" / "domain_profiles"
SOURCE_PROFILES_DIR = REPO_ROOT / "config" / "qualification" / "source_profiles"


def _load_script() -> ModuleType:
    path = REPO_ROOT / "scripts" / "qualification_status_check.py"
    spec = importlib.util.spec_from_file_location("qualification_status_check_under_test", path)
    assert spec is not None
    loader = spec.loader
    assert loader is not None
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def _yaml(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], yaml.safe_load(path.read_text(encoding="utf-8")))


def _controls() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    return (
        _yaml(STATUS_PATH),
        _yaml(TARGETS_PATH),
        _yaml(CATALOG_PATH),
        _yaml(CROSSWALK_PATH),
    )


def _profile_map(directory: Path, key_field: str) -> dict[str, dict[str, Any]]:
    profiles: dict[str, dict[str, Any]] = {}
    for path in directory.glob("*.yaml"):
        payload = _yaml(path)
        profiles[payload[key_field]] = payload
    return profiles


def _fill_candidate_identity(status: dict[str, Any]) -> None:
    status["candidate"].update(
        {
            "commit": "0" * 40,
            "artifact_digest": "sha256:" + "1" * 64,
            "protocol_version": "qualification_protocol_v3",
            "targets_version": "0.1.0-test",
            "vocabulary_version": "qualification_vocabulary_v3",
            "criteria_catalog_digest": "sha256:" + "2" * 64,
        }
    )


def _successful_results(module: ModuleType, crosswalk: dict[str, Any]) -> dict[str, Any]:
    results = {
        path: module.CheckerResult(
            path=path,
            returncode=0,
            stdout="ok",
            stderr="",
            advertised_criterion_ids=module.advertised_criterion_ids_for_checker(
                crosswalk,
                path,
            ),
        )
        for path in module.unique_checker_paths(crosswalk)
    }
    results["scripts/package_manifest_check.py"] = module.CheckerResult(
        path="scripts/package_manifest_check.py",
        returncode=2,
        stdout="",
        stderr="usage: package_manifest_check.py [-h] manifest",
        advertised_criterion_ids=module.advertised_criterion_ids_for_checker(
            crosswalk,
            "scripts/package_manifest_check.py",
        ),
    )
    results["scripts/spatial_query_plan_runtime_check.py"] = module.CheckerResult(
        path="scripts/spatial_query_plan_runtime_check.py",
        returncode=1,
        stdout="missing required --db-url or DATABASE_URL_SYNC",
        stderr="",
        advertised_criterion_ids=module.advertised_criterion_ids_for_checker(
            crosswalk,
            "scripts/spatial_query_plan_runtime_check.py",
        ),
    )
    return results


def test_status_derivation_matches_committed_blocked_not_run_shape() -> None:
    module = _load_script()
    status, targets, catalog, crosswalk = _controls()

    derived = module.derive_statuses(
        root=REPO_ROOT,
        status=status,
        targets=targets,
        catalog=catalog,
        crosswalk=crosswalk,
        checker_results=_successful_results(module, crosswalk),
    )
    errors = module.compare_committed_statuses(status, derived)

    assert errors == []
    assert derived[("qualifications", "p0")] == "BLOCKED"
    assert sum(1 for value in derived.values() if value == "BLOCKED") == 1
    assert set(derived.values()) == {"BLOCKED", "NOT_RUN"}


def test_p0_drift_to_not_run_is_rejected() -> None:
    module = _load_script()
    status, targets, catalog, crosswalk = _controls()
    drifted = deepcopy(status)
    drifted["qualifications"]["p0"]["status"] = "NOT_RUN"

    derived = module.derive_statuses(
        root=REPO_ROOT,
        status=drifted,
        targets=targets,
        catalog=catalog,
        crosswalk=crosswalk,
        checker_results=_successful_results(module, crosswalk),
    )
    errors = module.compare_committed_statuses(drifted, derived)

    assert any("qualifications.p0 expected BLOCKED but found NOT_RUN" in error for error in errors)


def test_p0_stays_blocked_when_non_target_parameterization_is_unresolved() -> None:
    module = _load_script()
    status, targets, catalog, crosswalk = _controls()
    drifted_status = deepcopy(status)
    drifted_targets = deepcopy(targets)
    drifted_status["qualifications"]["p0"]["status"] = "NOT_RUN"
    _fill_candidate_identity(drifted_status)
    drifted_targets["status"] = "FROZEN"
    drifted_targets["frozen_at"] = "2026-06-22T00:00:00Z"
    drifted_targets["approved_by"] = ["test-owner"]

    derived = module.derive_statuses(
        root=REPO_ROOT,
        status=drifted_status,
        targets=drifted_targets,
        catalog=catalog,
        crosswalk=crosswalk,
        checker_results=_successful_results(module, crosswalk),
        rubrics=_yaml(RUBRICS_PATH),
        domain_profiles=_profile_map(DOMAIN_PROFILES_DIR, "domain_id"),
        source_profiles=_profile_map(SOURCE_PROFILES_DIR, "source_id"),
    )
    errors = module.compare_committed_statuses(drifted_status, derived)

    assert derived[("qualifications", "p0")] == "BLOCKED"
    assert any("qualifications.p0 expected BLOCKED but found NOT_RUN" in error for error in errors)


def test_unexpected_checker_failure_blocks_mapped_statuses() -> None:
    module = _load_script()
    status, targets, catalog, crosswalk = _controls()
    checker_results = _successful_results(module, crosswalk)
    checker_results["scripts/source_readiness.py"] = module.CheckerResult(
        path="scripts/source_readiness.py",
        returncode=1,
        stdout="unexpected source readiness failure",
        stderr="",
        advertised_criterion_ids=module.advertised_criterion_ids_for_checker(
            crosswalk,
            "scripts/source_readiness.py",
        ),
    )

    derived = module.derive_statuses(
        root=REPO_ROOT,
        status=status,
        targets=targets,
        catalog=catalog,
        crosswalk=crosswalk,
        checker_results=checker_results,
    )
    errors = module.compare_committed_statuses(status, derived)

    assert derived[("qualifications", "q1")] == "BLOCKED"
    assert derived[("overlays", "data_quality")] == "BLOCKED"
    assert derived[("overlays", "security_privacy_compliance")] == "BLOCKED"
    assert any("qualifications.q1 expected BLOCKED but found NOT_RUN" in error for error in errors)


def test_unexpected_missing_checker_result_fails_closed() -> None:
    module = _load_script()
    status, targets, catalog, crosswalk = _controls()
    checker_results = _successful_results(module, crosswalk)
    checker_results.pop("scripts/source_readiness.py")

    try:
        module.derive_statuses(
            root=REPO_ROOT,
            status=status,
            targets=targets,
            catalog=catalog,
            crosswalk=crosswalk,
            checker_results=checker_results,
        )
    except module.QualificationStatusError as exc:
        assert "missing checker result: scripts/source_readiness.py" in str(exc)
    else:
        raise AssertionError("missing checker result should fail closed")


def test_runtime_checker_env_is_suppressed_by_default(monkeypatch: Any) -> None:
    module = _load_script()
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://land:land@localhost:5432/land_diligence")
    monkeypatch.setenv("DATABASE_URL_SYNC", "postgresql://land:land@localhost:5432/land_diligence")

    result = module.run_checker(
        REPO_ROOT,
        "scripts/spatial_query_plan_runtime_check.py",
        sys.executable,
        60,
    )

    assert module.checker_is_known_not_run(result)


def test_timeout_output_is_normalized(monkeypatch: Any) -> None:
    module = _load_script()

    def raise_timeout(*args: Any, **kwargs: Any) -> None:
        raise module.subprocess.TimeoutExpired(
            cmd=["python", "scripts/source_readiness.py"],
            timeout=1,
            output=b"partial stdout",
            stderr=b"partial stderr",
        )

    monkeypatch.setattr(
        module,
        "run_checker_advertisement",
        lambda *args, **kwargs: ("Q1-012",),
    )
    monkeypatch.setattr(module.subprocess, "run", raise_timeout)

    result = module.run_checker(
        REPO_ROOT,
        "scripts/source_readiness.py",
        sys.executable,
        1,
    )

    assert result.returncode == 124
    assert result.stdout == "partial stdout"
    assert "partial stderr" in result.stderr
    assert "checker timed out after 1s" in result.stderr


def test_missing_checker_advertisement_fails_closed() -> None:
    module = _load_script()
    status, targets, catalog, crosswalk = _controls()
    checker_results = _successful_results(module, crosswalk)
    checker_results["scripts/source_readiness.py"] = module.CheckerResult(
        path="scripts/source_readiness.py",
        returncode=1,
        stdout="unexpected source readiness failure",
        stderr="",
        advertised_criterion_ids=(),
    )

    try:
        module.derive_statuses(
            root=REPO_ROOT,
            status=status,
            targets=targets,
            catalog=catalog,
            crosswalk=crosswalk,
            checker_results=checker_results,
        )
    except module.QualificationStatusError as exc:
        assert "missing checker criterion advertisement: scripts/source_readiness.py" in str(exc)
    else:
        raise AssertionError("missing checker advertisement should fail closed")
