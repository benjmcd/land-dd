#!/usr/bin/env python3
"""Adversarial in-process smoke tests for the qualification validator."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import shutil
import tempfile
from pathlib import Path

import yaml


def load_validator(source_root: Path):
    path = source_root / "scripts" / "validate_qualification.py"
    spec = importlib.util.spec_from_file_location("qualification_validator_under_test", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load validator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_validator(module, root: Path) -> tuple[int, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        return_code = module.main(["--root", str(root)])
    return return_code, stdout.getvalue() + "\n" + stderr.getvalue()


def mutate_yaml(path: Path, mutate) -> None:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    mutate(data)
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def copy_fixture(source: Path, destination: Path) -> None:
    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns(
            ".git",
            ".mypy_cache",
            ".pytest_cache",
            ".ruff_cache",
            "__pycache__",
            "*.pyc",
            "_selftest",
            "local_artifacts",
            "worktrees",
        ),
    )



def control_paths(root: Path) -> dict[str, Path]:
    if (root / "docs" / "qualification" / "EMPIRICAL_QUALIFICATION_FRAMEWORK.md").exists():
        return {
            "status": root / "state" / "EMPIRICAL_QUALIFICATION_STATUS.yaml",
            "targets": root / "config" / "qualification" / "qualification_targets.yaml",
            "catalog": root / "config" / "qualification" / "criterion_catalog.yaml",
            "change_matrix": root / "config" / "qualification" / "change_impact_matrix.yaml",
            "readiness_crosswalk": root / "config" / "qualification" / "readiness_crosswalk.yaml",
            "evidence": root / "docs" / "qualification" / "README.md",
        }
    return {
        "status": root / "empirical_qualification_status.example.yaml",
        "targets": root / "qualification_targets.example.yaml",
        "catalog": root / "criterion_catalog.yaml",
        "change_matrix": root / "change_impact_matrix.yaml",
        "readiness_crosswalk": root / "readiness_crosswalk.yaml",
        "evidence": root / "README.md",
    }


def assert_result(
    name: str,
    result: tuple[int, str],
    should_pass: bool,
    expected_text: str | None = None,
) -> None:
    return_code, output = result
    passed = return_code == 0
    if passed != should_pass or (expected_text and expected_text not in output):
        print(f"FAIL: {name}")
        print(f"expected pass={should_pass}, returncode={return_code}")
        if expected_text:
            print(f"missing expected text: {expected_text!r}")
        print(output)
        raise SystemExit(1)
    print(f"PASS: {name}")


def main() -> int:
    source = Path(__file__).resolve().parent.parent
    validator = load_validator(source)

    with tempfile.TemporaryDirectory(prefix="qualification-validator-") as temp:
        temp_root = Path(temp)

        baseline = temp_root / "baseline"
        copy_fixture(source, baseline)
        assert_result(
            "baseline blocked status validates structurally",
            run_validator(validator, baseline),
            True,
            "qualification structural validation: PASS",
        )

        blocked_without_refs = temp_root / "blocked-without-refs"
        copy_fixture(source, blocked_without_refs)

        def remove_blocker_references(value):
            value["qualifications"]["p0"]["status"] = "BLOCKED"
            value["qualifications"]["p0"]["result_path"] = None
            value["qualifications"]["p0"].pop("blocked_reason", None)
            value["qualifications"]["p0"].pop("blocker_references", None)

        mutate_yaml(
            control_paths(blocked_without_refs)["status"],
            remove_blocker_references,
        )
        assert_result(
            "blocked status requires concrete blocker references",
            run_validator(validator, blocked_without_refs),
            False,
            "BLOCKED but has no blocker_references",
        )

        classification = temp_root / "classification"
        copy_fixture(source, classification)
        mutate_yaml(
            control_paths(classification)["status"],
            lambda value: value.update({"highest_valid_classification": "L9-E1"}),
        )
        assert_result(
            "classification cannot outrun gate status",
            run_validator(validator, classification),
            False,
            "classification L9-E1 requires",
        )

        conditional = temp_root / "conditional"
        copy_fixture(source, conditional)

        def mismatch(value):
            value["scope"]["candidate_generation_enabled"] = True
            value["candidate_generation"]["enabled"] = True

        mutate_yaml(control_paths(conditional)["targets"], mismatch)
        assert_result(
            "conditional applicability/status mismatch is rejected",
            run_validator(validator, conditional),
            False,
            "conditional overlay candidate_generation.applicable",
        )

        catalog_drift = temp_root / "catalog-drift"
        copy_fixture(source, catalog_drift)

        def remove_criterion(value):
            value["criteria"].pop()
            value["criterion_count"] -= 1

        mutate_yaml(control_paths(catalog_drift)["catalog"], remove_criterion)
        assert_result(
            "framework/catalog criterion drift is rejected",
            run_validator(validator, catalog_drift),
            False,
            "criterion_catalog: missing framework IDs",
        )

        invalid_change_impact = temp_root / "invalid-change-impact"
        copy_fixture(source, invalid_change_impact)

        def inject_bad_change_criterion(value):
            value["change_classes"]["SOURCE_DATA_REFRESH"][
                "invalidate_by_default"
            ].append("NOPE-001")

        mutate_yaml(
            control_paths(invalid_change_impact)["change_matrix"],
            inject_bad_change_criterion,
        )
        assert_result(
            "change-impact invalidation targets must be catalog criteria",
            run_validator(validator, invalid_change_impact),
            False,
            (
                "change_impact_matrix.SOURCE_DATA_REFRESH.invalidate_by_default: "
                "unknown criterion IDs"
            ),
        )

        invalid_crosswalk = temp_root / "invalid-crosswalk"
        copy_fixture(source, invalid_crosswalk)

        def inject_bad_crosswalk_criterion(value):
            value["entries"][0]["criterion_ids"].append("NOPE-001")

        mutate_yaml(
            control_paths(invalid_crosswalk)["readiness_crosswalk"],
            inject_bad_crosswalk_criterion,
        )
        assert_result(
            "readiness crosswalk targets must be catalog criteria",
            run_validator(validator, invalid_crosswalk),
            False,
            "readiness_crosswalk.level_9_10_matrix: unknown criterion IDs",
        )

        crosswalk_missing_glob = temp_root / "crosswalk-missing-glob"
        copy_fixture(source, crosswalk_missing_glob)

        def remove_required_crosswalk_glob(value):
            value["inventory"]["checker_globs"].remove("scripts/bologna_*_check.py")

        mutate_yaml(
            control_paths(crosswalk_missing_glob)["readiness_crosswalk"],
            remove_required_crosswalk_glob,
        )
        assert_result(
            "readiness crosswalk inventory policy must retain required globs",
            run_validator(validator, crosswalk_missing_glob),
            False,
            "readiness_crosswalk: missing required checker globs",
        )

        frozen_draft = temp_root / "frozen-draft"
        copy_fixture(source, frozen_draft)

        def falsely_freeze(value):
            value["status"] = "FROZEN"
            value["frozen_at"] = "2026-06-21T00:00:00Z"
            value["approved_by"] = ["selftest"]

        mutate_yaml(
            control_paths(frozen_draft)["targets"],
            falsely_freeze,
        )
        assert_result(
            "frozen target registry cannot retain unresolved active bindings",
            run_validator(validator, frozen_draft),
            False,
            "frozen/P0 scope requires target binding",
        )


        invariant_na = temp_root / "invariant-na"
        copy_fixture(source, invariant_na)
        catalog_value = yaml.safe_load(
            (control_paths(invariant_na)["catalog"]).read_text(encoding="utf-8")
        )
        catalog_digest = __import__("hashlib").sha256(
            (control_paths(invariant_na)["catalog"]).read_bytes()
        ).hexdigest()
        p0_004_class = next(
            item["requirement_class"]
            for item in catalog_value["criteria"]
            if item["criterion_id"] == "P0-004"
        )
        p0_001_class = next(
            item["requirement_class"]
            for item in catalog_value["criteria"]
            if item["criterion_id"] == "P0-001"
        )
        invalid_result = {
            "schema_version": "qualification_result_v3",
            "gate_id": "P0",
            "status": "FAIL",
            "selected_product_scope_profile": "BOUNDED_USER_VALIDATED",
            "selected_deployment_profile": "LOCAL_SINGLE_USER",
            "candidate_commit": "1" * 40,
            "candidate_tag": None,
            "artifact_digest": "sha256:" + "1" * 64,
            "protocol_version": "selftest",
            "targets_version": "selftest",
            "vocabulary_version": "qualification_vocabulary_v3",
            "criteria_catalog_digest": "sha256:" + catalog_digest,
            "started_at": "2026-06-21T00:00:00Z",
            "completed_at": "2026-06-21T00:01:00Z",
            "expires_at": None,
            "evidence_path": None,
            "reviewers": [],
            "criterion_results": [
                {
                    "criterion_id": "P0-001",
                    "result": "FAIL",
                    "requirement_class": p0_001_class,
                    "evidence": ["selftest"],
                    "rationale": "Intentional failure row.",
                    "approver": None,
                    "expires_at": None,
                    "metric_value": None,
                    "threshold_value": None,
                    "stratum": None,
                },
                {
                    "criterion_id": "P0-004",
                    "result": "N/A",
                    "requirement_class": p0_004_class,
                    "evidence": ["selftest"],
                    "rationale": "Intentional illegal N/A.",
                    "approver": "selftest",
                    "expires_at": "2099-01-01T00:00:00Z",
                    "metric_value": None,
                    "threshold_value": None,
                    "stratum": None,
                },
            ],
            "summary_metrics": {},
            "accepted_residual_risks": [],
            "invalidation_reason": None,
        }
        (invariant_na / "invalid-result.json").write_text(
            __import__("json").dumps(invalid_result, indent=2),
            encoding="utf-8",
        )

        def reference_invalid_result(value):
            value["qualifications"]["p0"]["status"] = "FAIL"
            value["qualifications"]["p0"]["result_path"] = "invalid-result.json"

        mutate_yaml(
            control_paths(invariant_na)["status"],
            reference_invalid_result,
        )
        assert_result(
            "applicable invariant cannot be marked N/A",
            run_validator(validator, invariant_na),
            False,
            "applicable criterion P0-004 cannot be N/A",
        )

        incomplete_pass = temp_root / "incomplete-pass"
        copy_fixture(source, incomplete_pass)
        pass_catalog_digest = __import__("hashlib").sha256(
            (control_paths(incomplete_pass)["catalog"]).read_bytes()
        ).hexdigest()
        pass_catalog = yaml.safe_load(
            (control_paths(incomplete_pass)["catalog"]).read_text(encoding="utf-8")
        )
        pass_class = next(
            item["requirement_class"]
            for item in pass_catalog["criteria"]
            if item["criterion_id"] == "P0-001"
        )
        partial_pass = {
            **invalid_result,
            "status": "PASS",
            "criteria_catalog_digest": "sha256:" + pass_catalog_digest,
            "completed_at": "2026-06-21T00:01:00Z",
            "expires_at": "2099-01-01T00:00:00Z",
            "evidence_path": str(control_paths(incomplete_pass)["evidence"].relative_to(incomplete_pass)),
            "criterion_results": [
                {
                    "criterion_id": "P0-001",
                    "result": "PASS",
                    "requirement_class": pass_class,
                    "evidence": [str(control_paths(incomplete_pass)["evidence"].relative_to(incomplete_pass))],
                    "rationale": None,
                    "approver": None,
                    "expires_at": None,
                    "metric_value": None,
                    "threshold_value": None,
                    "stratum": None,
                }
            ],
        }
        (incomplete_pass / "partial-pass.json").write_text(
            __import__("json").dumps(partial_pass, indent=2),
            encoding="utf-8",
        )

        def reference_partial_pass(value):
            value["qualifications"]["p0"]["status"] = "FAIL"
            value["qualifications"]["p0"]["result_path"] = "partial-pass.json"

        mutate_yaml(
            control_paths(incomplete_pass)["status"],
            reference_partial_pass,
        )
        assert_result(
            "incomplete gate result cannot be labeled PASS",
            run_validator(validator, incomplete_pass),
            False,
            "PASS omits applicable criteria",
        )

        false_p0 = temp_root / "false-p0"
        copy_fixture(source, false_p0)

        def claim_p0(value):
            value["highest_valid_classification"] = "L9-P"
            value["qualifications"]["p0"]["status"] = "PASS"
            value["qualifications"]["p0"]["result_path"] = "missing-result.yaml"
            value["qualifications"]["p0"]["expires_at"] = "2099-01-01T00:00:00Z"

        mutate_yaml(
            control_paths(false_p0)["status"],
            claim_p0,
        )
        assert_result(
            "P0 cannot pass with draft targets/contracts/missing evidence",
            run_validator(validator, false_p0),
            False,
            "P0 cannot PASS while qualification targets are not FROZEN",
        )

    print("qualification validator self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
