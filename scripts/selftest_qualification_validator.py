#!/usr/bin/env python3
"""Adversarial in-process smoke tests for the qualification validator."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml


def load_validator(source_root: Path):
    path = source_root / "scripts" / "validate_qualification.py"
    spec = importlib.util.spec_from_file_location("qualification_validator_under_test", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load validator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_status_checker(source_root: Path):
    path = source_root / "scripts" / "qualification_status_check.py"
    spec = importlib.util.spec_from_file_location("qualification_status_check_under_test", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load status checker: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_change_impact_checker(source_root: Path):
    path = source_root / "scripts" / "qualification_change_impact_check.py"
    spec = importlib.util.spec_from_file_location("qualification_change_impact_check_under_test", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load change-impact checker: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_validator(module, root: Path) -> tuple[int, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        return_code = module.main(["--root", str(root)])
    return return_code, stdout.getvalue() + "\n" + stderr.getvalue()


def run_status_checker(module, root: Path) -> tuple[int, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        return_code = module.main(
            ["--root", str(root), "--python-command", sys.executable]
        )
    return return_code, stdout.getvalue() + "\n" + stderr.getvalue()


def run_change_impact_checker(module, root: Path, changed_paths: list[str]) -> tuple[int, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    args = ["--root", str(root)]
    for path in changed_paths:
        args.extend(["--changed-path", path])
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        return_code = module.main(args)
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


def catalog_map(root: Path) -> dict[str, dict]:
    return {
        item["criterion_id"]: item
        for item in yaml.safe_load(
            control_paths(root)["catalog"].read_text(encoding="utf-8")
        )["criteria"]
    }


def catalog_digest(root: Path) -> str:
    return __import__("hashlib").sha256(
        control_paths(root)["catalog"].read_bytes()
    ).hexdigest()


def complete_gate_result(
    validator,
    root: Path,
    gate: str,
    *,
    status: str = "PASS",
    evidence_ref: str | None = None,
    include_reviewers: bool = True,
    include_reproducer: bool = True,
    overrides: dict | None = None,
) -> dict:
    targets = yaml.safe_load(control_paths(root)["targets"].read_text(encoding="utf-8"))
    catalog = catalog_map(root)
    evidence_ref = evidence_ref or str(
        control_paths(root)["evidence"].relative_to(root)
    )
    expected = sorted(validator.expected_criteria_for_gate(gate, catalog, targets))
    if status == "PASS":
        rows = [
            {
                "criterion_id": cid,
                "result": "PASS",
                "requirement_class": catalog[cid]["requirement_class"],
                "evidence": [evidence_ref],
                "rationale": None,
                "approver": None,
                "expires_at": None,
                "metric_value": None,
                "threshold_value": None,
                "stratum": None,
            }
            for cid in expected
        ]
    else:
        cid = expected[0]
        rows = [
            {
                "criterion_id": cid,
                "result": status,
                "requirement_class": catalog[cid]["requirement_class"],
                "evidence": [evidence_ref],
                "rationale": f"Intentional {status.lower()} row.",
                "approver": None,
                "expires_at": None,
                "metric_value": None,
                "threshold_value": None,
                "stratum": None,
            }
        ]
    result: dict[str, Any] = {
        "schema_version": "qualification_result_v3",
        "gate_id": gate,
        "status": status,
        "selected_product_scope_profile": "BOUNDED_USER_VALIDATED",
        "selected_deployment_profile": "LOCAL_SINGLE_USER",
        "candidate_commit": "1" * 40,
        "candidate_tag": None,
        "artifact_digest": "sha256:" + "1" * 64,
        "protocol_version": "selftest-protocol",
        "targets_version": "selftest-targets",
        "vocabulary_version": "qualification_vocabulary_v3",
        "criteria_catalog_digest": "sha256:" + catalog_digest(root),
        "started_at": "2026-06-21T00:00:00Z",
        "completed_at": "2026-06-21T00:01:00Z",
        "expires_at": "2099-01-01T00:00:00Z",
        "evidence_path": evidence_ref,
        "criterion_results": rows,
        "summary_metrics": {},
        "accepted_residual_risks": [],
        "invalidation_reason": None,
    }
    if include_reviewers:
        result["reviewers"] = [
            {
                "id": "independent-reviewer",
                "role": "qualification reviewer",
                "competency_record": "docs/qualification/README.md",
                "conflict_disclosed": False,
                "independent": True,
            }
        ]
    if include_reproducer:
        result["independent_reproducer"] = {
            "id": "independent-reproducer",
            "reproduction_report": "docs/qualification/README.md",
            "completed_at": "2026-06-21T00:02:00Z",
            "independent": True,
        }
    if overrides:
        result.update(overrides)
    return result


def write_result(root: Path, relative_path: str, result: dict) -> None:
    (root / relative_path).write_text(
        json.dumps(result, indent=2),
        encoding="utf-8",
    )


def assert_direct_validation_error(name: str, errors: list[str], expected_text: str) -> None:
    output = "\n".join(errors)
    if expected_text not in output:
        print(f"FAIL: {name}")
        print(f"missing expected text: {expected_text!r}")
        print(output)
        raise SystemExit(1)
    print(f"PASS: {name}")


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
    status_checker = load_status_checker(source)
    change_impact_checker = load_change_impact_checker(source)

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
        assert_result(
            "baseline derived status matches committed status",
            run_status_checker(status_checker, baseline),
            True,
            "qualification status check: ok",
        )
        assert_result(
            "known mapped path surfaces change-impact criteria",
            run_change_impact_checker(
                change_impact_checker,
                baseline,
                [
                    "config/release_readiness.yaml",
                    "scripts/source_readiness.py",
                ],
            ),
            True,
            "SOURCE_SCHEMA_OR_CONNECTOR",
        )

        status_drift = temp_root / "status-drift"
        copy_fixture(source, status_drift)

        def drift_p0_to_not_run(value):
            value["qualifications"]["p0"]["status"] = "NOT_RUN"

        mutate_yaml(
            control_paths(status_drift)["status"],
            drift_p0_to_not_run,
        )
        assert_result(
            "derived status drift is rejected",
            run_status_checker(status_checker, status_drift),
            False,
            "qualifications.p0 expected BLOCKED but found NOT_RUN",
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

        crosswalk_missing_gate = temp_root / "crosswalk-missing-gate"
        copy_fixture(source, crosswalk_missing_gate)

        def remove_required_crosswalk_gate(value):
            for entry in value["entries"]:
                gate_paths = entry.get("gate_paths") or []
                if "scripts/run_security_scan.sh" in gate_paths:
                    gate_paths.remove("scripts/run_security_scan.sh")
                    entry["gate_paths"] = gate_paths
                    return

        mutate_yaml(
            control_paths(crosswalk_missing_gate)["readiness_crosswalk"],
            remove_required_crosswalk_gate,
        )
        assert_result(
            "readiness crosswalk CI gate inventory must cover workflow gates",
            run_validator(validator, crosswalk_missing_gate),
            False,
            "readiness_crosswalk: missing gate inventory paths",
        )

        crosswalk_missing_release_gate = temp_root / "crosswalk-missing-release-gate"
        copy_fixture(source, crosswalk_missing_release_gate)

        def remove_required_crosswalk_release_gate(value):
            for entry in value["entries"]:
                gate_paths = entry.get("gate_paths") or []
                if "scripts/run_incident_rollback_check.ps1" in gate_paths:
                    gate_paths.remove("scripts/run_incident_rollback_check.ps1")
                    entry["gate_paths"] = gate_paths
                    return

        mutate_yaml(
            control_paths(crosswalk_missing_release_gate)["readiness_crosswalk"],
            remove_required_crosswalk_release_gate,
        )
        assert_result(
            "readiness crosswalk release gate inventory must cover release proofs",
            run_validator(validator, crosswalk_missing_release_gate),
            False,
            "readiness_crosswalk: missing gate inventory paths",
        )

        checker_advertisement_drift = temp_root / "checker-advertisement-drift"
        copy_fixture(source, checker_advertisement_drift)
        checker_path = checker_advertisement_drift / "scripts" / "source_readiness.py"
        checker_path.write_text(
            checker_path.read_text(encoding="utf-8").replace(
                "maybe_emit_qualification_criteria(__file__)",
                "False",
            ),
            encoding="utf-8",
        )
        assert_result(
            "checker advertisement drift is rejected",
            run_validator(validator, checker_advertisement_drift),
            False,
            "checker advertisement failed: scripts/source_readiness.py",
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

        expired_pass = temp_root / "expired-pass"
        copy_fixture(source, expired_pass)
        write_result(
            expired_pass,
            "dq-pass.json",
            complete_gate_result(
                validator,
                expired_pass,
                "DQ",
                overrides={"expires_at": "2000-01-01T00:00:00Z"},
            ),
        )

        def reference_expired_pass(value):
            value["overlays"]["data_quality"]["status"] = "PASS"
            value["overlays"]["data_quality"]["result_path"] = "dq-pass.json"
            value["overlays"]["data_quality"]["expires_at"] = "2000-01-01T00:00:00Z"

        mutate_yaml(control_paths(expired_pass)["status"], reference_expired_pass)
        assert_result(
            "expired PASS gate is rejected",
            run_validator(validator, expired_pass),
            False,
            "expired PASS",
        )

        mismatched_gate = temp_root / "mismatched-gate"
        copy_fixture(source, mismatched_gate)
        write_result(
            mismatched_gate,
            "wrong-gate-pass.json",
            complete_gate_result(validator, mismatched_gate, "IR"),
        )

        def reference_wrong_gate(value):
            value["overlays"]["data_quality"]["status"] = "PASS"
            value["overlays"]["data_quality"]["result_path"] = "wrong-gate-pass.json"
            value["overlays"]["data_quality"]["expires_at"] = "2099-01-01T00:00:00Z"

        mutate_yaml(control_paths(mismatched_gate)["status"], reference_wrong_gate)
        assert_result(
            "result gate_id must match status gate",
            run_validator(validator, mismatched_gate),
            False,
            "gate_id IR does not match status gate DQ",
        )

        mismatched_identity = temp_root / "mismatched-identity"
        copy_fixture(source, mismatched_identity)
        write_result(
            mismatched_identity,
            "identity-mismatch.json",
            complete_gate_result(
                validator,
                mismatched_identity,
                "DQ",
                overrides={
                    "selected_product_scope_profile": "OTHER_PROFILE",
                    "protocol_version": "wrong-protocol",
                    "targets_version": "wrong-targets",
                },
            ),
        )

        def reference_identity_mismatch(value):
            value["candidate"]["protocol_version"] = "selftest-protocol"
            value["candidate"]["targets_version"] = "selftest-targets"
            value["overlays"]["data_quality"]["status"] = "PASS"
            value["overlays"]["data_quality"]["result_path"] = "identity-mismatch.json"
            value["overlays"]["data_quality"]["expires_at"] = "2099-01-01T00:00:00Z"

        mutate_yaml(control_paths(mismatched_identity)["status"], reference_identity_mismatch)
        assert_result(
            "result identity must match active scope and candidate versions",
            run_validator(validator, mismatched_identity),
            False,
            "selected product-scope profile differs from status",
        )

        broken_criterion_evidence = temp_root / "broken-criterion-evidence"
        copy_fixture(source, broken_criterion_evidence)
        write_result(
            broken_criterion_evidence,
            "broken-evidence-pass.json",
            complete_gate_result(
                validator,
                broken_criterion_evidence,
                "DQ",
                evidence_ref="missing-evidence.md",
                overrides={
                    "evidence_path": str(
                        control_paths(broken_criterion_evidence)["evidence"].relative_to(
                            broken_criterion_evidence
                        )
                    )
                },
            ),
        )

        def reference_broken_criterion_evidence(value):
            value["overlays"]["data_quality"]["status"] = "PASS"
            value["overlays"]["data_quality"]["result_path"] = "broken-evidence-pass.json"
            value["overlays"]["data_quality"]["expires_at"] = "2099-01-01T00:00:00Z"

        mutate_yaml(
            control_paths(broken_criterion_evidence)["status"],
            reference_broken_criterion_evidence,
        )
        assert_result(
            "PASS criterion evidence references must resolve",
            run_validator(validator, broken_criterion_evidence),
            False,
            "criterion evidence does not exist",
        )

        remote_criterion_evidence = temp_root / "remote-criterion-evidence"
        copy_fixture(source, remote_criterion_evidence)
        write_result(
            remote_criterion_evidence,
            "remote-evidence-pass.json",
            complete_gate_result(
                validator,
                remote_criterion_evidence,
                "DQ",
                evidence_ref="https://example.invalid/evidence.md",
            ),
        )

        def reference_remote_criterion_evidence(value):
            value["overlays"]["data_quality"]["status"] = "PASS"
            value["overlays"]["data_quality"]["result_path"] = "remote-evidence-pass.json"
            value["overlays"]["data_quality"]["expires_at"] = "2099-01-01T00:00:00Z"

        mutate_yaml(
            control_paths(remote_criterion_evidence)["status"],
            reference_remote_criterion_evidence,
        )
        assert_result(
            "PASS criterion evidence must be repo-local",
            run_validator(validator, remote_criterion_evidence),
            False,
            "criterion evidence must be repo-local",
        )

        malformed_expiry = temp_root / "malformed-expiry"
        copy_fixture(source, malformed_expiry)
        write_result(
            malformed_expiry,
            "malformed-expiry-pass.json",
            complete_gate_result(
                validator,
                malformed_expiry,
                "DQ",
                overrides={"expires_at": 123},
            ),
        )

        def reference_malformed_expiry(value):
            value["overlays"]["data_quality"]["status"] = "PASS"
            value["overlays"]["data_quality"]["result_path"] = "malformed-expiry-pass.json"
            value["overlays"]["data_quality"]["expires_at"] = "2099-01-01T00:00:00Z"

        mutate_yaml(control_paths(malformed_expiry)["status"], reference_malformed_expiry)
        assert_result(
            "malformed PASS expiry fails closed without crashing",
            run_validator(validator, malformed_expiry),
            False,
            "expires_at must be a date-time string",
        )

        blocked_with_result = temp_root / "blocked-with-result"
        copy_fixture(source, blocked_with_result)
        write_result(
            blocked_with_result,
            "p0-blocked-result.json",
            complete_gate_result(validator, blocked_with_result, "P0", status="BLOCKED"),
        )

        def reference_blocked_with_bad_reference(value):
            value["qualifications"]["p0"]["status"] = "BLOCKED"
            value["qualifications"]["p0"]["result_path"] = "p0-blocked-result.json"
            value["qualifications"]["p0"]["blocker_references"] = [
                str(blocked_with_result.parent / "outside-repo.md")
            ]

        mutate_yaml(
            control_paths(blocked_with_result)["status"],
            reference_blocked_with_bad_reference,
        )
        assert_result(
            "P0 blocked record is validated even with result_path",
            run_validator(validator, blocked_with_result),
            False,
            "blocker reference must be repo-local",
        )

        pass_without_reviewers = temp_root / "pass-without-reviewers"
        copy_fixture(source, pass_without_reviewers)
        write_result(
            pass_without_reviewers,
            "unreviewed-pass.json",
            complete_gate_result(
                validator,
                pass_without_reviewers,
                "DQ",
                include_reviewers=False,
            ),
        )

        def reference_unreviewed_pass(value):
            value["overlays"]["data_quality"]["status"] = "PASS"
            value["overlays"]["data_quality"]["result_path"] = "unreviewed-pass.json"
            value["overlays"]["data_quality"]["expires_at"] = "2099-01-01T00:00:00Z"

        mutate_yaml(control_paths(pass_without_reviewers)["status"], reference_unreviewed_pass)
        assert_result(
            "PASS result requires reviewer metadata",
            run_validator(validator, pass_without_reviewers),
            False,
            "'reviewers' is a required property",
        )

        pass_without_reproducer = temp_root / "pass-without-reproducer"
        copy_fixture(source, pass_without_reproducer)
        write_result(
            pass_without_reproducer,
            "unreproduced-pass.json",
            complete_gate_result(
                validator,
                pass_without_reproducer,
                "DQ",
                include_reproducer=False,
            ),
        )

        def reference_unreproduced_pass(value):
            value["overlays"]["data_quality"]["status"] = "PASS"
            value["overlays"]["data_quality"]["result_path"] = "unreproduced-pass.json"
            value["overlays"]["data_quality"]["expires_at"] = "2099-01-01T00:00:00Z"

        mutate_yaml(control_paths(pass_without_reproducer)["status"], reference_unreproduced_pass)
        assert_result(
            "PASS result requires independent reproduction metadata",
            run_validator(validator, pass_without_reproducer),
            False,
            "'independent_reproducer' is a required property",
        )

        profile_targets: dict[str, Any] = {
            "scope": {
                "qualified_domains": ["zoning"],
                "source_profile_ids": ["DS-X"],
                "geographies": ["NC"],
                "intents": ["homestead"],
                "input_modalities": ["single_parcel_aoi", "multi_parcel_aoi"],
                "output_channels": ["api_json", "exported_report"],
                "product_scope_profile": "BOUNDED_USER_VALIDATED",
                "commercial_profile_enabled": False,
                "ai_llm_enabled_for_decision_relevant_output": False,
            }
        }
        profile_status = {"qualifications": {"p0": {"status": "PASS"}}}
        valid_source_profile: dict[str, Any] = {
            "status": "APPROVED",
            "approved_use_profiles": ["BOUNDED_USER_VALIDATED"],
            "coverage": {"geographies": ["NC"], "domains": ["zoning"]},
            "rights": {
                "commercial_use": "ALLOWED",
                "cache": "ALLOWED",
                "retain": "ALLOWED",
                "redistribute": "ALLOWED",
                "export": "ALLOWED",
                "raw_data": "ALLOWED",
                "ai_use": "ALLOWED",
            },
            "rights_conditions": {},
            "enabled_operations": ["INGEST"],
            "conditions_enforced_by": ["not-required"],
        }

        def frozen_domain_profile(domain_id: str) -> dict:
            return {
                "status": "FROZEN",
                "scope": profile_targets["scope"],
                "reference_hierarchy": [{"rank": 1, "type": "official"}],
                "issue_taxonomy": [{"id": domain_id}],
                "severity_rubric": [{"level": "high"}],
                "confidence_rubric": [{"band": "supported"}],
                "source_requirements": [{"source_id": "DS-X"}],
                "spatial_temporal_tolerances": [{"id": "default"}],
                "unknown_states": ["UNKNOWN"],
                "metrics": [{"id": "domain_recall"}],
                "owner": "product",
                "reviewers": ["reviewer"],
                "expires_at": "2099-01-01T00:00:00Z",
                "frozen_at": "2026-06-21T00:00:00Z",
                "approved_by": ["approver"],
                "invalidation_triggers": ["source change"],
                "field_surveillance_plan": "docs/qualification/README.md",
            }

        errors: list[str] = []
        validator.validate_domain_and_source_profiles(
            profile_targets,
            profile_status,
            {
                "zoning": {
                    "status": "FROZEN",
                    "scope": {
                        "geographies": ["NC"],
                        "intents": ["homestead"],
                        "input_modalities": ["single_parcel_aoi"],
                        "output_channels": ["api_json"],
                    },
                    "issue_taxonomy": [{"id": "zoning"}],
                    "severity_rubric": [{"level": "high"}],
                    "confidence_rubric": [{"band": "supported"}],
                    "source_requirements": [{"source_id": "DS-X"}],
                    "owner": "product",
                    "reviewers": ["reviewer"],
                }
            },
            {"DS-X": valid_source_profile},
            errors,
            [],
        )
        assert_direct_validation_error(
            "domain profiles must match modalities and channels",
            errors,
            "input_modalities do not exactly match frozen target scope",
        )

        errors = []
        validator.validate_domain_and_source_profiles(
            profile_targets,
            profile_status,
            {
                "zoning": {
                    "status": "FROZEN",
                    "scope": {
                        "geographies": ["NC"],
                        "intents": ["homestead"],
                        "input_modalities": ["single_parcel_aoi", "multi_parcel_aoi"],
                        "output_channels": ["api_json", "exported_report"],
                    },
                    "issue_taxonomy": [{"id": "TBD"}],
                    "severity_rubric": [{"level": "high"}],
                    "confidence_rubric": [{"band": "supported"}],
                    "source_requirements": [{"source_id": "DS-X"}],
                    "owner": "product",
                    "reviewers": ["reviewer"],
                }
            },
            {"DS-X": valid_source_profile},
            errors,
            [],
        )
        assert_direct_validation_error(
            "frozen domain profiles cannot retain unresolved fields",
            errors,
            "unresolved frozen profile fields",
        )

        errors = []
        tolerance_unresolved = frozen_domain_profile("zoning")
        tolerance_unresolved["spatial_temporal_tolerances"] = {}
        validator.validate_domain_and_source_profiles(
            profile_targets,
            profile_status,
            {"zoning": tolerance_unresolved},
            {"DS-X": valid_source_profile},
            errors,
            [],
        )
        assert_direct_validation_error(
            "frozen domain profiles must freeze spatial temporal tolerances",
            errors,
            "spatial_temporal_tolerances",
        )

        errors = []
        outside_coverage = {
            **valid_source_profile,
            "coverage": {"geographies": ["WA"], "domains": ["flood"]},
        }
        validator.validate_domain_and_source_profiles(
            profile_targets,
            profile_status,
            {"zoning": {
                "status": "FROZEN",
                "scope": profile_targets["scope"],
                "issue_taxonomy": [{"id": "zoning"}],
                "severity_rubric": [{"level": "high"}],
                "confidence_rubric": [{"band": "supported"}],
                "source_requirements": [{"source_id": "DS-X"}],
                "owner": "product",
                "reviewers": ["reviewer"],
            }},
            {"DS-X": outside_coverage},
            errors,
            [],
        )
        assert_direct_validation_error(
            "source profile coverage must cover target scope",
            errors,
            "coverage.geographies does not cover target scope",
        )

        errors = []
        multi_domain_targets = {
            "scope": {
                **profile_targets["scope"],
                "qualified_domains": ["zoning", "flood"],
            }
        }
        validator.validate_domain_and_source_profiles(
            multi_domain_targets,
            profile_status,
            {
                "zoning": frozen_domain_profile("zoning"),
                "flood": frozen_domain_profile("flood"),
            },
            {"DS-X": valid_source_profile},
            errors,
            [],
        )
        assert_direct_validation_error(
            "selected sources must cover every target domain",
            errors,
            "selected source profiles do not cover target domains",
        )

        errors = []
        conditional_source = {
            **valid_source_profile,
            "rights": {**valid_source_profile["rights"], "cache": "CONDITIONAL"},
            "enabled_operations": ["CACHE"],
            "rights_conditions": {},
            "conditions_enforced_by": [],
        }
        validator.validate_domain_and_source_profiles(
            profile_targets,
            profile_status,
            {"zoning": {
                "status": "FROZEN",
                "scope": profile_targets["scope"],
                "issue_taxonomy": [{"id": "zoning"}],
                "severity_rubric": [{"level": "high"}],
                "confidence_rubric": [{"band": "supported"}],
                "source_requirements": [{"source_id": "DS-X"}],
                "owner": "product",
                "reviewers": ["reviewer"],
            }},
            {"DS-X": conditional_source},
            errors,
            [],
        )
        assert_direct_validation_error(
            "conditional source rights require enforcement controls",
            errors,
            "conditional cache right lacks enforcement controls",
        )

        errors = []
        conditional_commercial_source = {
            **valid_source_profile,
            "rights": {
                **valid_source_profile["rights"],
                "commercial_use": "CONDITIONAL",
            },
            "enabled_operations": ["INGEST"],
            "rights_conditions": {},
            "conditions_enforced_by": [],
        }
        commercial_targets = {
            "scope": {
                **profile_targets["scope"],
                "commercial_profile_enabled": True,
            }
        }
        validator.validate_domain_and_source_profiles(
            commercial_targets,
            profile_status,
            {"zoning": frozen_domain_profile("zoning")},
            {"DS-X": conditional_commercial_source},
            errors,
            [],
        )
        assert_direct_validation_error(
            "conditional commercial use requires enforcement controls",
            errors,
            "conditional commercial_use right lacks enforcement controls",
        )

        errors = []
        raw_without_export = {
            **valid_source_profile,
            "rights": {**valid_source_profile["rights"], "export": "PROHIBITED"},
            "enabled_operations": ["RAW_EXPORT"],
        }
        validator.validate_domain_and_source_profiles(
            profile_targets,
            profile_status,
            {"zoning": {
                "status": "FROZEN",
                "scope": profile_targets["scope"],
                "issue_taxonomy": [{"id": "zoning"}],
                "severity_rubric": [{"level": "high"}],
                "confidence_rubric": [{"band": "supported"}],
                "source_requirements": [{"source_id": "DS-X"}],
                "owner": "product",
                "reviewers": ["reviewer"],
            }},
            {"DS-X": raw_without_export},
            errors,
            [],
        )
        assert_direct_validation_error(
            "RAW_EXPORT also requires export right",
            errors,
            "operation RAW_EXPORT conflicts with export right",
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
