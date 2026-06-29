from __future__ import annotations

import importlib.util
from copy import deepcopy
from pathlib import Path
from types import ModuleType
from typing import Any, cast

yaml = cast(Any, __import__("yaml"))

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load(script_name: str) -> ModuleType:
    script_path = REPO_ROOT / "scripts" / script_name
    spec = importlib.util.spec_from_file_location(script_name.removesuffix(".py"), script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _yaml(path: str) -> dict[str, Any]:
    payload = yaml.safe_load((REPO_ROOT / path).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return cast(dict[str, Any], payload)


def _owner_answer(odp_id: str) -> dict[str, Any]:
    slug = odp_id.lower().replace("-", "_")
    return {
        "owner_answer_id": f"synthetic-{slug}",
        "odp_id": odp_id,
        "answer_type": "approve_with_cited_authority",
        "decision_owner": "benjmcd",
        "decision_date": "2026-06-28",
        "authority_reference": f"external owner authority for {odp_id}",
        "answer_summary": f"Synthetic complete cited-authority answer for {odp_id}.",
        "cited_artifacts": [f"external cited artifact for {odp_id}"],
        "caveats": [f"synthetic caveat for {odp_id}"],
        "downstream_unlocks_requested": [],
        "supersedes_owner_answer_ids": [],
    }


def _record(required_fields: list[str], **overrides: Any) -> dict[str, Any]:
    record: dict[str, Any] = {}
    for field in required_fields:
        if field.endswith("_ids"):
            record[field] = [f"synthetic-{field}"]
        elif field in {
            "cited_artifacts",
            "caveats",
            "stop_conditions",
            "source_versions",
            "retrieval_metadata",
            "fixture_file_manifest",
            "source_failure_fixture_manifest",
            "field_allowlist",
            "field_denylist",
            "evidence_ledger_rows",
            "claim_evidence_links",
            "unknowns_list",
            "caveats_list",
            "artifact_manifest",
            "source_lineage",
        }:
            record[field] = [f"synthetic-{field}"]
        elif field in {"evidence_slot_values", "storage_export_boundaries"}:
            record[field] = {"synthetic": f"synthetic-{field}"}
        elif field == "downstream_unlocks_requested":
            record[field] = []
        else:
            record[field] = f"synthetic-{field}"
    record.update(overrides)
    return record


def test_bologna_gate_evaluators_accept_complete_synthetic_answers() -> None:
    intake = cast(Any, _load("bologna_owner_answer_intake_check.py"))
    intake_payload = _yaml("config/bologna_owner_answer_intake.yaml")
    intake_threads = {
        thread["odp_id"]: thread for thread in intake_payload["bologna_decision_threads"]
    }
    intake_result = intake.evaluate_synthetic_owner_answer(
        intake_payload,
        _owner_answer("ODP-BOL-001"),
        decision_coverage=intake_threads["ODP-BOL-001"]["required_decisions"],
    )
    assert intake_result.accepted, intake_result.errors

    scope = cast(Any, _load("bol_scope_auth_check.py"))
    scope_payload = _yaml("config/bol_scope_auth.yaml")
    scope_readiness = scope_payload["promotion_readiness"]
    scope_authority = _record(
        scope_readiness["required_authority_record_fields"],
        scope_decision_ids=scope_readiness["required_scope_decisions"],
        downstream_unlocks_requested=[],
        supersedes_authority_record_ids=[],
    )
    scope_result = scope.evaluate_synthetic_owner_answer(
        scope_payload,
        _owner_answer("ODP-BOL-001"),
        scope_authority,
    )
    assert scope_result.accepted, scope_result.errors

    odp1 = cast(Any, _load("bologna_odp1_owner_response_gate_check.py"))
    odp1_payload = _yaml("config/bologna_odp1_owner_response_gate.yaml")
    odp1_gate = odp1_payload["odp_bol_001_gate"]
    odp1_authority = _record(
        odp1_gate["required_authority_record_fields"],
        scope_decision_ids=odp1_gate["required_scope_decisions"],
        downstream_unlocks_requested=[],
        supersedes_authority_record_ids=[],
    )
    odp1_result = odp1.evaluate_synthetic_owner_answer(
        odp1_payload,
        _owner_answer("ODP-BOL-001"),
        odp1_authority,
    )
    assert odp1_result.accepted, odp1_result.errors

    odp2 = cast(Any, _load("bologna_odp2_source_rights_response_gate_check.py"))
    odp2_payload = _yaml("config/bologna_odp2_source_rights_response_gate.yaml")
    odp2_gate = odp2_payload["odp_bol_002_gate"]
    source_records = [
        _record(
            odp2_gate["required_source_authority_record_fields"],
            candidate_id=candidate_id,
            rights_decision_ids=odp2_gate["required_rights_decisions"],
            scope_authority_record_ids=["synthetic-odp1-authority"],
            downstream_unlocks_requested=[],
            supersedes_source_authority_record_ids=[],
        )
        for candidate_id in odp2_gate["candidate_review_ids"]
    ]
    odp2_result = odp2.evaluate_synthetic_owner_answer(
        odp2_payload,
        _owner_answer("ODP-BOL-002"),
        source_records,
        satisfied_prerequisites=["ODP-BOL-001"],
    )
    assert odp2_result.accepted, odp2_result.errors

    odp3 = cast(Any, _load("bologna_odp3_corpus_response_gate_check.py"))
    odp3_payload = _yaml("config/bologna_odp3_corpus_response_gate.yaml")
    odp3_gate = odp3_payload["odp_bol_003_gate"]
    corpus_manifest = _record(
        odp3_gate["required_manifest_fields"],
        corpus_decision_ids=odp3_gate["required_corpus_decisions"],
    )
    odp3_result = odp3.evaluate_synthetic_owner_answer(
        odp3_payload,
        _owner_answer("ODP-BOL-003"),
        corpus_manifest,
        satisfied_prerequisites=["ODP-BOL-001", "ODP-BOL-002"],
    )
    assert odp3_result.accepted, odp3_result.errors

    odp4 = cast(Any, _load("bologna_odp4_db_report_proof_response_gate_check.py"))
    odp4_payload = _yaml("config/bologna_odp4_db_report_proof_response_gate.yaml")
    odp4_gate = odp4_payload["odp_bol_004_gate"]
    report_proof = _record(odp4_gate["required_report_proof_fields"])
    odp4_result = odp4.evaluate_synthetic_owner_answer(
        odp4_payload,
        _owner_answer("ODP-BOL-004"),
        report_proof,
        satisfied_prerequisites=["ODP-BOL-001", "ODP-BOL-002", "ODP-BOL-003"],
    )
    assert odp4_result.accepted, odp4_result.errors


def test_bologna_gate_evaluator_does_not_mutate_inputs() -> None:
    odp2 = cast(Any, _load("bologna_odp2_source_rights_response_gate_check.py"))
    odp2_payload = _yaml("config/bologna_odp2_source_rights_response_gate.yaml")
    odp2_gate = odp2_payload["odp_bol_002_gate"]
    owner_answer = _owner_answer("ODP-BOL-002")
    source_records = [
        _record(
            odp2_gate["required_source_authority_record_fields"],
            candidate_id=candidate_id,
            rights_decision_ids=odp2_gate["required_rights_decisions"],
            scope_authority_record_ids=["synthetic-odp1-authority"],
            downstream_unlocks_requested=[],
            supersedes_source_authority_record_ids=[],
        )
        for candidate_id in odp2_gate["candidate_review_ids"]
    ]
    payload_before = deepcopy(odp2_payload)
    owner_before = deepcopy(owner_answer)
    records_before = deepcopy(source_records)

    result = odp2.evaluate_synthetic_owner_answer(
        odp2_payload,
        owner_answer,
        source_records,
        satisfied_prerequisites=["ODP-BOL-001"],
    )

    assert result.accepted, result.errors
    assert odp2_payload == payload_before
    assert owner_answer == owner_before
    assert source_records == records_before


def test_bologna_gate_evaluators_reject_bad_synthetic_answers() -> None:
    intake = cast(Any, _load("bologna_owner_answer_intake_check.py"))
    intake_payload = _yaml("config/bologna_owner_answer_intake.yaml")
    malformed = _owner_answer("ODP-BOL-001")
    malformed.pop("authority_reference")
    intake_result = intake.evaluate_synthetic_owner_answer(intake_payload, malformed)
    assert not intake_result.accepted
    assert any("missing required fields" in error for error in intake_result.errors)

    scope = cast(Any, _load("bol_scope_auth_check.py"))
    scope_payload = _yaml("config/bol_scope_auth.yaml")
    scope_readiness = scope_payload["promotion_readiness"]
    scope_authority = _record(
        scope_readiness["required_authority_record_fields"],
        scope_decision_ids=scope_readiness["required_scope_decisions"][:-1],
        downstream_unlocks_requested=[],
        supersedes_authority_record_ids=[],
    )
    review_only = _owner_answer("ODP-BOL-001")
    review_only["answer_type"] = "approve_review_only"
    scope_result = scope.evaluate_synthetic_owner_answer(
        scope_payload,
        review_only,
        scope_authority,
    )
    assert not scope_result.accepted
    assert any(
        "answer_type must be approve_with_cited_authority" in error
        for error in scope_result.errors
    )
    assert any("missing required decisions" in error for error in scope_result.errors)

    odp2 = cast(Any, _load("bologna_odp2_source_rights_response_gate_check.py"))
    odp2_payload = _yaml("config/bologna_odp2_source_rights_response_gate.yaml")
    odp2_gate = odp2_payload["odp_bol_002_gate"]
    source_record = _record(
        odp2_gate["required_source_authority_record_fields"],
        candidate_id=odp2_gate["candidate_review_ids"][0],
        rights_decision_ids=odp2_gate["required_rights_decisions"],
        scope_authority_record_ids=["synthetic-odp1-authority"],
        downstream_unlocks_requested=["config/bologna_recorded_source_corpus.yaml"],
        supersedes_source_authority_record_ids=[],
    )
    odp2_result = odp2.evaluate_synthetic_owner_answer(
        odp2_payload,
        _owner_answer("ODP-BOL-002"),
        [source_record],
    )
    assert not odp2_result.accepted
    assert any("missing satisfied prerequisites" in error for error in odp2_result.errors)
    assert any("must not request downstream unlocks" in error for error in odp2_result.errors)
    assert any(
        "missing required source_authority_record ids" in error
        for error in odp2_result.errors
    )

    odp3 = cast(Any, _load("bologna_odp3_corpus_response_gate_check.py"))
    odp3_payload = _yaml("config/bologna_odp3_corpus_response_gate.yaml")
    odp3_gate = odp3_payload["odp_bol_003_gate"]
    partial_manifest = _record(
        odp3_gate["required_manifest_fields"][:-1],
        corpus_decision_ids=odp3_gate["required_corpus_decisions"],
    )
    odp3_result = odp3.evaluate_synthetic_owner_answer(
        odp3_payload,
        _owner_answer("ODP-BOL-003"),
        partial_manifest,
        satisfied_prerequisites=["ODP-BOL-001", "ODP-BOL-002"],
    )
    assert not odp3_result.accepted
    assert any("missing required fields" in error for error in odp3_result.errors)

    odp4 = cast(Any, _load("bologna_odp4_db_report_proof_response_gate_check.py"))
    odp4_payload = _yaml("config/bologna_odp4_db_report_proof_response_gate.yaml")
    odp4_gate = odp4_payload["odp_bol_004_gate"]
    unlock_answer = _owner_answer("ODP-BOL-004")
    unlock_answer["downstream_unlocks_requested"] = ["backend/app/api"]
    odp4_result = odp4.evaluate_synthetic_owner_answer(
        odp4_payload,
        unlock_answer,
        _record(odp4_gate["required_report_proof_fields"]),
        satisfied_prerequisites=["ODP-BOL-001", "ODP-BOL-002", "ODP-BOL-003"],
    )
    assert not odp4_result.accepted
    assert any("must not request downstream unlocks" in error for error in odp4_result.errors)
