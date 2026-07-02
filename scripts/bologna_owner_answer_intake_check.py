from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from bologna_owner_answer_evaluator import (  # noqa: E402
    OwnerAnswerEvaluation,
    evaluate_owner_answer,
)

CONFIG_PATH = "config/bologna_owner_answer_intake.yaml"
RUNBOOK_PATH = "docs/runbooks/bologna_owner_answer_intake.md"
OWNER_PACKET_PATH = "state/owner-decision-packet.md"
PILOT_SCOPE_PATH = "config/bologna_pilot_scope_authority.yaml"
SOURCE_AUTHORITY_PATH = "config/bologna_source_authority_intake.yaml"
SOURCE_RIGHTS_PATH = "config/bologna_source_rights.yaml"
CORPUS_PATH = "config/bologna_recorded_source_corpus.yaml"

EXPECTED_APPROVALS = {
    "owner_answers_complete": False,
    "product_aoi_scope_answered": True,
    "source_authority_rights_answered": False,
    "recorded_corpus_answered": False,
    "db_report_proof_answered": False,
    "downstream_authority_updates_allowed": False,
}
EXPECTED_LIMITS = {
    "validate_only_intake": True,
    "records_owner_authority": False,
    "selects_bologna_aoi": False,
    "approves_sources": False,
    "changes_source_rights": False,
    "creates_recorded_fixtures": False,
    "creates_source_failure_fixtures": False,
    "runs_live_connectors": False,
    "mutates_database": False,
    "creates_runtime_artifacts": False,
    "creates_report_artifacts": False,
    "changes_report_semantics": False,
    "changes_source_readiness": False,
    "approves_ds017": False,
    "claims_legal_review": False,
    "claims_hosted_production_ready": False,
    "claims_level_10": False,
}
EXPECTED_ODP_SEQUENCE = {
    "ODP-BOL-001": 1,
    "ODP-BOL-002": 2,
    "ODP-BOL-003": 3,
    "ODP-BOL-004": 4,
}
EXPECTED_ODP_IDS = set(EXPECTED_ODP_SEQUENCE)
ODP1_OWNER_ANSWER_ID = "odp-bol-001-scope-pursuit-2026-06-26"
EXPECTED_ODP_STATUS = {
    "ODP-BOL-001": "review_only_scope_pursuit_answered",
    "ODP-BOL-002": "missing_owner_answer",
    "ODP-BOL-003": "missing_owner_answer",
    "ODP-BOL-004": "missing_owner_answer",
}
EXPECTED_OWNER_ANSWER_REFERENCES = {
    "ODP-BOL-001": [ODP1_OWNER_ANSWER_ID],
    "ODP-BOL-002": [],
    "ODP-BOL-003": [],
    "ODP-BOL-004": [],
}
EXPECTED_REPORT_PROOF_FIELDS = {
    "one_local_db_report_run_id",
    "approved_corpus_reference",
    "evidence_ledger_rows",
    "claim_evidence_links",
    "unknowns_list",
    "caveats_list",
    "artifact_manifest",
    "source_lineage",
    "report_use_policy",
    "no_overclaim_review",
    "storage_export_boundaries",
}
EXPECTED_OWNER_ANSWER_FIELDS = {
    "owner_answer_id",
    "odp_id",
    "answer_type",
    "decision_owner",
    "decision_date",
    "authority_reference",
    "answer_summary",
    "cited_artifacts",
    "caveats",
    "downstream_unlocks_requested",
    "supersedes_owner_answer_ids",
}
EXPECTED_ANSWER_TYPES = {
    "approve_with_cited_authority",
    "keep_blocked",
    "approve_review_only",
    "exclude_or_defer",
}
EXPECTED_NO_OVERCLAIM_CONTROLS = {
    "no_authority_by_answer_intake",
    "no_source_approval_by_answer_intake",
    "no_aoi_selection_by_answer_intake",
    "no_source_rights_change_by_answer_intake",
    "no_fixture_capture_by_answer_intake",
    "no_report_runtime_use_by_answer_intake",
    "no_db_seed_by_answer_intake",
    "no_legal_buildability_title_or_value_claim",
    "no_level_10_or_hosted_claim",
}
REQUIRED_FILES = (
    CONFIG_PATH,
    RUNBOOK_PATH,
    OWNER_PACKET_PATH,
    PILOT_SCOPE_PATH,
    SOURCE_AUTHORITY_PATH,
    SOURCE_RIGHTS_PATH,
    CORPUS_PATH,
    "schemas/report_run_schema.json",
    "schemas/evidence_schema.json",
    "state/LEVEL_9_10_GATE_MATRIX.md",
    "state/PRODUCTION_AUTHORITY_PACKET.md",
    "scripts/run_bologna_owner_answer_intake_check.ps1",
    "scripts/run_bologna_owner_answer_intake_check.sh",
)
RUNBOOK_PHRASES = (
    "bologna_owner_answer_intake_v1",
    "validate-only",
    "records one review-only owner answer",
    "ODP-BOL-001",
    ODP1_OWNER_ANSWER_ID,
    "ODP-BOL-004",
    "downstream_updates_allowed",
    "current_owner_answers",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def require_mapping(value: Any, message: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SystemExit(message)
    return value


def require_list(value: Any, message: str) -> list[Any]:
    if not isinstance(value, list):
        raise SystemExit(message)
    return value


def require_non_empty_list(value: Any, message: str) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise SystemExit(message)
    return value


def require_text(value: Any, message: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SystemExit(message)
    return value.strip()


def require_iso_date(value: Any, message: str) -> str:
    text = require_text(value, message)
    try:
        date.fromisoformat(text)
    except ValueError as exc:
        raise SystemExit(message) from exc
    return text


def require_text_list(value: Any, message: str, *, allow_empty: bool = False) -> list[str]:
    items = require_list(value, message)
    if not allow_empty and not items:
        raise SystemExit(message)
    return [require_text(item, message) for item in items]


def normalize_path(path_text: str) -> str:
    return path_text.replace("\\", "/")


def require_existing(path_text: str) -> None:
    normalized = normalize_path(path_text)
    require((ROOT / normalized).exists(), f"owner-answer artifact missing: {normalized}")


def read_text(path_text: str) -> str:
    return (ROOT / normalize_path(path_text)).read_text(encoding="utf-8")


def load_yaml(path_text: str) -> dict[str, Any]:
    return require_mapping(yaml.safe_load(read_text(path_text)), f"{path_text} must be a mapping")


def list_set(value: Any, message: str) -> set[str]:
    return {str(item) for item in require_non_empty_list(value, message)}


def pilot_scope_decisions() -> set[str]:
    return list_set(
        load_yaml(PILOT_SCOPE_PATH).get("required_scope_decisions"),
        "pilot-scope decisions missing",
    )


def source_rights_decisions() -> set[str]:
    return list_set(
        load_yaml(SOURCE_RIGHTS_PATH).get("required_rights_decisions"),
        "source-rights decisions missing",
    )


def source_candidate_ids() -> set[str]:
    rights = load_yaml(SOURCE_RIGHTS_PATH)
    ids: set[str] = set()
    for raw_review in require_non_empty_list(
        rights.get("candidate_rights_reviews"),
        "candidate rights reviews missing",
    ):
        review = require_mapping(raw_review, "each candidate rights review must be a mapping")
        ids.add(require_text(review.get("candidate_id"), "candidate id missing"))
    return ids


def corpus_decisions() -> set[str]:
    return list_set(
        load_yaml(CORPUS_PATH).get("required_corpus_decisions"),
        "corpus decisions missing",
    )


def corpus_manifest_fields() -> set[str]:
    return list_set(
        load_yaml(CORPUS_PATH).get("required_manifest_fields"),
        "corpus manifest fields missing",
    )


def validate_required_files() -> None:
    for path_text in REQUIRED_FILES:
        require_existing(path_text)


def validate_authority_paths(payload: dict[str, Any]) -> None:
    for path_text in require_non_empty_list(payload.get("authority"), "authority paths missing"):
        require(isinstance(path_text, str), "authority paths must be strings")
        require_existing(path_text)


def validate_owner_packet_references() -> None:
    packet = read_text(OWNER_PACKET_PATH)
    for odp_id in EXPECTED_ODP_IDS:
        require(odp_id in packet, f"owner decision packet missing {odp_id}")


def validate_owner_answer_record(record: dict[str, Any]) -> str:
    require(set(record) == EXPECTED_OWNER_ANSWER_FIELDS, "owner answer fields drifted")
    answer_id = require_text(record.get("owner_answer_id"), "owner answer id missing")
    odp_id = require_text(record.get("odp_id"), f"{answer_id} ODP id missing")
    require(odp_id in EXPECTED_ODP_IDS, f"{answer_id} references unknown ODP id")
    answer_type = require_text(record.get("answer_type"), f"{answer_id} answer type missing")
    require(answer_type in EXPECTED_ANSWER_TYPES, f"{answer_id} answer type is not allowed")
    require_text(record.get("decision_owner"), f"{answer_id} decision owner missing")
    require_iso_date(record.get("decision_date"), f"{answer_id} decision date must be ISO")
    require_text(record.get("authority_reference"), f"{answer_id} authority reference missing")
    require_text(record.get("answer_summary"), f"{answer_id} answer summary missing")
    require_text_list(record.get("cited_artifacts"), f"{answer_id} cited artifacts missing")
    require_text_list(record.get("caveats"), f"{answer_id} caveats missing")
    require(
        require_list(
            record.get("downstream_unlocks_requested"),
            f"{answer_id} downstream unlocks missing",
        )
        == [],
        f"{answer_id} must not request downstream unlocks",
    )
    require_text_list(
        record.get("supersedes_owner_answer_ids"),
        f"{answer_id} superseded owner answers must be text",
        allow_empty=True,
    )
    return answer_id


def validate_owner_answer_contract(payload: dict[str, Any]) -> None:
    contract = require_mapping(
        payload.get("owner_answer_contract"),
        "owner answer contract missing",
    )
    require(
        contract.get("contract_state") == "ready_for_external_owner_answers",
        "owner answer contract state changed",
    )
    require(
        list_set(contract.get("required_record_fields"), "owner answer fields missing")
        == EXPECTED_OWNER_ANSWER_FIELDS,
        "owner answer fields drifted",
    )
    require(
        list_set(contract.get("allowed_answer_types"), "owner answer types missing")
        == EXPECTED_ANSWER_TYPES,
        "owner answer types drifted",
    )
    require(
        contract.get("response_update_policy") == "disabled_until_complete_cited_authority",
        "owner answer update policy changed",
    )
    controls = require_mapping(
        contract.get("no_overclaim_controls"),
        "owner answer no-overclaim controls missing",
    )
    require(set(controls) == EXPECTED_NO_OVERCLAIM_CONTROLS, "no-overclaim controls drifted")
    for control_id, enabled in controls.items():
        require(enabled is True, f"{control_id} no-overclaim control disabled")

    answers_by_id: dict[str, dict[str, Any]] = {}
    for raw_answer in require_list(
        contract.get("current_owner_answers"),
        "current owner answers must be a list",
    ):
        answer = require_mapping(raw_answer, "each owner answer must be a mapping")
        answer_id = validate_owner_answer_record(answer)
        require(answer_id not in answers_by_id, f"duplicate owner answer id: {answer_id}")
        answers_by_id[answer_id] = answer

    require(
        set(answers_by_id) == {ODP1_OWNER_ANSWER_ID},
        "current_owner_answers must contain only the recorded ODP-BOL-001 review-only answer",
    )
    odp1_answer = answers_by_id[ODP1_OWNER_ANSWER_ID]
    require(odp1_answer.get("odp_id") == "ODP-BOL-001", "ODP1 owner answer id mismatch")
    require(
        odp1_answer.get("answer_type") == "approve_review_only",
        "ODP1 owner answer must remain review-only",
    )


def validate_thread_common(thread: dict[str, Any]) -> str:
    odp_id = require_text(thread.get("odp_id"), "ODP id missing")
    require(odp_id in EXPECTED_ODP_IDS, f"unexpected ODP id {odp_id}")
    require(thread.get("sequence") == EXPECTED_ODP_SEQUENCE[odp_id], f"{odp_id} sequence drifted")
    require(thread.get("status") == EXPECTED_ODP_STATUS[odp_id], f"{odp_id} status changed")
    require_text(thread.get("title"), f"{odp_id} title missing")
    for path_text in require_non_empty_list(thread.get("source_packets"), f"{odp_id} packets missing"):
        require(isinstance(path_text, str), f"{odp_id} source packet paths must be strings")
        require_existing(path_text)
    require(
        thread.get("owner_answer_references") == EXPECTED_OWNER_ANSWER_REFERENCES[odp_id],
        f"{odp_id} owner answer references changed",
    )
    require(
        thread.get("downstream_updates_allowed") is False,
        f"{odp_id} downstream updates unexpectedly allowed",
    )
    for path_text in require_non_empty_list(
        thread.get("downstream_blocked_targets"),
        f"{odp_id} downstream blocked targets missing",
    ):
        require(isinstance(path_text, str), f"{odp_id} blocked targets must be strings")
    return odp_id


def _thread_decision_requirements(thread: Mapping[str, Any]) -> list[Any]:
    for key in (
        "required_decisions",
        "required_rights_decisions",
        "required_corpus_decisions",
        "required_report_proof_fields",
    ):
        values = thread.get(key)
        if isinstance(values, list):
            return values
    return []


def evaluate_synthetic_owner_answer(
    payload: dict[str, Any],
    owner_answer: Mapping[str, Any],
    *,
    satisfied_prerequisites: Iterable[str] = (),
    decision_coverage: Iterable[str] = (),
) -> OwnerAnswerEvaluation:
    if not isinstance(owner_answer, Mapping):
        return OwnerAnswerEvaluation(
            accepted=False,
            errors=("owner_answer must be a mapping",),
            still_blocked=(),
        )
    odp_id = str(owner_answer.get("odp_id", ""))
    raw_threads = payload.get("bologna_decision_threads")
    if not isinstance(raw_threads, list):
        return OwnerAnswerEvaluation(
            accepted=False,
            errors=("Bologna decision threads missing",),
            still_blocked=(),
        )
    threads = {
        thread.get("odp_id"): thread
        for thread in raw_threads
        if isinstance(thread, dict)
    }
    thread = threads.get(odp_id)
    if not isinstance(thread, dict):
        return OwnerAnswerEvaluation(
            accepted=False,
            errors=(f"unknown ODP thread: {odp_id}",),
            still_blocked=(),
        )
    return evaluate_owner_answer(
        owner_answer,
        odp_id=odp_id,
        required_fields=EXPECTED_OWNER_ANSWER_FIELDS,
        allowed_answer_types=EXPECTED_ANSWER_TYPES,
        required_prerequisites=thread.get("prerequisite_odp_ids", []),
        satisfied_prerequisites=satisfied_prerequisites,
        required_decisions=_thread_decision_requirements(thread),
        decision_coverage=decision_coverage,
        still_blocked_after_acceptance=thread.get("downstream_blocked_targets", []),
    )


def validate_threads(payload: dict[str, Any]) -> None:
    raw_threads = require_non_empty_list(
        payload.get("bologna_decision_threads"),
        "Bologna decision threads missing",
    )
    threads: dict[str, dict[str, Any]] = {}
    for raw_thread in raw_threads:
        thread = require_mapping(raw_thread, "each Bologna decision thread must be a mapping")
        odp_id = validate_thread_common(thread)
        require(odp_id not in threads, f"duplicate ODP thread: {odp_id}")
        threads[odp_id] = thread

    require(set(threads) == EXPECTED_ODP_IDS, "ODP thread set changed")
    require(
        list_set(threads["ODP-BOL-001"].get("required_decisions"), "scope decisions missing")
        == pilot_scope_decisions(),
        "ODP-BOL-001 decisions drifted from pilot-scope authority packet",
    )
    require(
        list_set(
            threads["ODP-BOL-002"].get("required_rights_decisions"),
            "rights decisions missing",
        )
        == source_rights_decisions(),
        "ODP-BOL-002 rights decisions drifted from source-rights matrix",
    )
    require(
        list_set(threads["ODP-BOL-002"].get("candidate_review_ids"), "candidates missing")
        == source_candidate_ids() | {"cadastral_gap"},
        "ODP-BOL-002 candidate set drifted from source-rights matrix",
    )
    require(
        list_set(
            threads["ODP-BOL-003"].get("required_corpus_decisions"),
            "corpus decisions missing",
        )
        == corpus_decisions(),
        "ODP-BOL-003 decisions drifted from corpus contract",
    )
    require(
        list_set(
            threads["ODP-BOL-003"].get("required_manifest_fields"),
            "manifest fields missing",
        )
        == corpus_manifest_fields(),
        "ODP-BOL-003 manifest fields drifted from corpus contract",
    )
    require(
        list_set(
            threads["ODP-BOL-004"].get("required_report_proof_fields"),
            "report proof fields missing",
        )
        == EXPECTED_REPORT_PROOF_FIELDS,
        "ODP-BOL-004 report proof fields drifted",
    )


def validate_catalog() -> dict[str, Any]:
    payload = load_yaml(CONFIG_PATH)
    require(payload.get("schema_version") == "bologna_owner_answer_intake_v1", "schema")
    require(payload.get("operator_runbook") == RUNBOOK_PATH, "runbook mismatch")
    require(payload.get("status") == "blocked_review_only_scope_pursuit", "status changed")
    require(
        payload.get("validation") == "scripts/run_bologna_owner_answer_intake_check.ps1",
        "validation wrapper mismatch",
    )
    require(
        require_mapping(payload.get("approvals"), "approvals missing") == EXPECTED_APPROVALS,
        "approvals changed",
    )
    require(
        require_mapping(payload.get("limits"), "limits missing") == EXPECTED_LIMITS,
        "limits changed",
    )
    validate_authority_paths(payload)
    validate_owner_answer_contract(payload)
    validate_threads(payload)
    require_non_empty_list(payload.get("unlock_policy"), "unlock policy missing")
    return payload


def validate_runbook() -> None:
    runbook = read_text(RUNBOOK_PATH)
    for phrase in RUNBOOK_PHRASES:
        require(phrase in runbook, f"owner-answer runbook missing phrase: {phrase}")
    for odp_id in EXPECTED_ODP_IDS:
        require(odp_id in runbook, f"owner-answer runbook missing {odp_id}")


def main() -> int:
    validate_required_files()
    validate_owner_packet_references()
    validate_catalog()
    validate_runbook()
    print("Bologna owner answer intake check: ok")
    return 0


if __name__ == "__main__":
    from pathlib import Path as _QualificationPath
    import sys as _qualification_sys

    _qualification_sys.path.insert(0, str(_QualificationPath(__file__).resolve().parent))
    from qualification_checker_advertisement import maybe_emit_qualification_criteria

    maybe_emit_qualification_criteria(__file__)
    raise SystemExit(main())
