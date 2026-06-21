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

CONFIG_FILES = {
    "config/qualification/change_impact_matrix.yaml",
    "config/qualification/criterion_catalog.yaml",
    "config/qualification/judgment_rubrics.yaml",
    "config/qualification/qualification_profiles.yaml",
    "config/qualification/qualification_targets.yaml",
    "config/qualification/qualification_vocabulary.yaml",
}
SCHEMA_FILES = {
    "schemas/qualification/change_impact_matrix.schema.json",
    "schemas/qualification/criterion_catalog.schema.json",
    "schemas/qualification/criterion_contract.schema.json",
    "schemas/qualification/domain_qualification_profile.schema.json",
    "schemas/qualification/empirical_qualification_status.schema.json",
    "schemas/qualification/judgment_rubrics.schema.json",
    "schemas/qualification/qualification_profiles.schema.json",
    "schemas/qualification/qualification_result.schema.json",
    "schemas/qualification/qualification_targets.schema.json",
    "schemas/qualification/qualification_vocabulary.schema.json",
    "schemas/qualification/source_quality_profile.schema.json",
}
SCRIPT_FILES = {
    "scripts/validate_qualification.py",
    "scripts/validate_qualification.ps1",
    "scripts/validate_qualification.cmd",
    "scripts/selftest_qualification_validator.py",
    "scripts/selftest_qualification_validator.ps1",
    "scripts/selftest_qualification_validator.cmd",
    "scripts/run_qualification_validate.sh",
    "scripts/run_qualification_selftest.sh",
}


def _load_script(path: Path, module_name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None
    loader = spec.loader
    assert loader is not None
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def _steps_text(job: dict[str, Any]) -> str:
    return "\n".join(
        str(step.get("uses", ""))
        + "\n"
        + str(step.get("run", ""))
        + "\n"
        + str(step.get("with", ""))
        for step in job["steps"]
    )


def test_qualification_spine_artifacts_are_repo_owned() -> None:
    expected = {
        "docs/qualification/EMPIRICAL_QUALIFICATION_FRAMEWORK.md",
        "docs/qualification/README.md",
        "state/EMPIRICAL_QUALIFICATION_STATUS.yaml",
        *CONFIG_FILES,
        *SCHEMA_FILES,
        *SCRIPT_FILES,
    }

    missing = sorted(path for path in expected if not (REPO_ROOT / path).exists())
    assert missing == []

    domain_profiles = sorted(
        (REPO_ROOT / "config" / "qualification" / "domain_profiles").glob("*.yaml"),
    )
    source_profiles = sorted(
        (REPO_ROOT / "config" / "qualification" / "source_profiles").glob("*.yaml"),
    )
    assert domain_profiles
    assert source_profiles


def test_qualification_status_is_non_passing_and_targets_remain_draft() -> None:
    status = yaml.safe_load(
        (REPO_ROOT / "state" / "EMPIRICAL_QUALIFICATION_STATUS.yaml").read_text(
            encoding="utf-8",
        ),
    )
    targets = yaml.safe_load(
        (REPO_ROOT / "config" / "qualification" / "qualification_targets.yaml").read_text(
            encoding="utf-8",
        ),
    )

    assert targets["status"] == "DRAFT"
    assert targets["approved_by"] == []
    assert status["highest_valid_classification"] == "L9-R"
    assert status["qualifications"]["p0"]["status"] in {"NOT_RUN", "BLOCKED"}
    assert status["qualifications"]["p0"]["status"] != "PASS"
    assert status["blocked_decisions"]


def test_qualification_validator_passes_and_pins_catalog_to_framework() -> None:
    validator = _load_script(
        REPO_ROOT / "scripts" / "validate_qualification.py",
        "validate_qualification_under_test",
    )
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        exit_code = validator.main(["--root", str(REPO_ROOT), "--layout", "repo"])
    output = stdout.getvalue()

    assert exit_code == 0, output
    assert "qualification structural validation: PASS" in output
    assert "target status: DRAFT" in output
    assert "highest valid classification: L9-R" in output
    assert "BLOCKED-READINESS:" in output

    framework_ids = validator.framework_ids(
        REPO_ROOT / "docs" / "qualification" / "EMPIRICAL_QUALIFICATION_FRAMEWORK.md",
    )
    catalog = yaml.safe_load(
        (REPO_ROOT / "config" / "qualification" / "criterion_catalog.yaml").read_text(
            encoding="utf-8",
        ),
    )
    catalog_ids = {item["criterion_id"] for item in catalog["criteria"]}
    assert framework_ids == catalog_ids
    assert catalog["criterion_count"] == len(catalog_ids)


def test_qualification_selftest_passes() -> None:
    selftest = _load_script(
        REPO_ROOT / "scripts" / "selftest_qualification_validator.py",
        "selftest_qualification_validator_under_test",
    )
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        exit_code = selftest.main()
    output = stdout.getvalue()

    assert exit_code == 0, output
    assert "qualification validator self-test: PASS" in output


def test_qualification_ci_verify_and_dev_dependency_are_wired() -> None:
    pyproject_text = (REPO_ROOT / "backend" / "pyproject.toml").read_text(encoding="utf-8")
    verify_sh = (REPO_ROOT / "scripts" / "verify.sh").read_text(encoding="utf-8")
    verify_ps1 = (REPO_ROOT / "scripts" / "verify.ps1").read_text(encoding="utf-8")
    ci_text = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    ci = yaml.safe_load(ci_text)

    assert "jsonschema" in pyproject_text
    assert "scripts/selftest_qualification_validator.py" in verify_sh
    assert "scripts/validate_qualification.py" in verify_sh
    assert "selftest_qualification_validator.py" in verify_ps1
    assert "validate_qualification.py" in verify_ps1

    job = ci["jobs"]["qualification-selftest"]
    job_steps = _steps_text(job)
    assert job["permissions"]["contents"] == "read"
    assert "actions/checkout@v6" in job_steps
    assert "actions/setup-python@v6" in job_steps
    assert "python-version: '3.12'" in ci_text
    assert 'python -m pip install -e "backend[dev]"' in job_steps
    assert "./scripts/run_qualification_selftest.sh" in job_steps
    assert "./scripts/run_qualification_validate.sh" in job_steps
