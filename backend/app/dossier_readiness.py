from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPORT_SCHEMA_PATH = "schemas/report_run_schema.json"
EVIDENCE_SCHEMA_PATH = "schemas/evidence_schema.json"
CLAIM_SCHEMA_PATH = "schemas/claim_schema.json"

REQUIRED_REPORT_FIELDS = {
    "evidence",
    "claims",
    "unknowns",
    "caveats",
    "source_manifest",
    "artifact_metadata",
}
REQUIRED_EVIDENCE_FIELDS = {
    "evidence_id",
    "source_id",
    "source_ingest_run_id",
    "confidence",
    "caveat",
}
REQUIRED_CLAIM_FIELDS = {
    "claim_id",
    "evidence_ids",
    "confidence",
    "user_safe_language",
    "verification_task",
}


class DossierReadinessError(RuntimeError):
    """Raised when dossier contract artifacts cannot be trusted for UI rendering."""


@dataclass(frozen=True)
class DossierAnchor:
    anchor_id: str
    artifact_path: str
    purpose: str
    anchors: tuple[str, ...]


@dataclass(frozen=True)
class DossierReadiness:
    report_schema_path: str
    evidence_schema_path: str
    claim_schema_path: str
    report_required_fields: tuple[str, ...]
    evidence_required_fields: tuple[str, ...]
    claim_required_fields: tuple[str, ...]
    anchors: tuple[DossierAnchor, ...]
    boundary: str


@dataclass(frozen=True)
class _AnchorSpec:
    anchor_id: str
    artifact_path: str
    purpose: str
    required_text: tuple[str, ...]


ANCHOR_SPECS = (
    _AnchorSpec(
        anchor_id="approved_dossier_gate",
        artifact_path="backend/tests/api/test_ui_routes.py",
        purpose="Approved UI reports expose dossier delivery only after review approval.",
        required_text=(
            "test_ui_report_run_shows_dossier_after_approval",
            "test_ui_report_run_list_approved_action_links_to_delivery_surfaces",
            "Download dossier",
            "View dossier",
        ),
    ),
    _AnchorSpec(
        anchor_id="lineage_gate",
        artifact_path="backend/tests/api/test_ui_routes.py",
        purpose="Approved report lineage exposes evidence-to-claim links.",
        required_text=(
            "test_ui_lineage_page_renders_claim_evidence_mapping",
            "test_ui_lineage_page_requires_approved_report",
            "View evidence lineage",
            "No evidence records",
        ),
    ),
    _AnchorSpec(
        anchor_id="source_failure_unknowns_gate",
        artifact_path="backend/tests/reports/test_report_service.py",
        purpose="Source failures and not-evaluated records flow into unknowns and caveats.",
        required_text=(
            "test_create_report_run_collects_evidence_claims_unknowns_and_caveats",
            "test_create_report_run_without_source_evidence_surfaces_not_evaluated_unknowns",
            "FLOOD_SOURCE_FAILURE",
            "source_manifest",
            "artifact_metadata",
        ),
    ),
    _AnchorSpec(
        anchor_id="safe_language_overclaim_gate",
        artifact_path="backend/tests/reports/test_report_overclaim.py",
        purpose="Dossier copy is bounded by screening-only and overclaim-denial tests.",
        required_text=(
            "_assert_no_forbidden_phrases",
            "Screening output only",
            "not legal",
            "investment advice",
        ),
    ),
    _AnchorSpec(
        anchor_id="regression_artifact_contract",
        artifact_path="backend/tests/reports/test_report_regression.py",
        purpose="Regression artifacts preserve source manifests, unknowns, caveats, and metadata.",
        required_text=(
            "source_manifest",
            "unknown_codes",
            "caveats",
            "artifact_metadata",
        ),
    ),
)


def repo_root_from_app() -> Path:
    return Path(__file__).resolve().parents[2]


def load_dossier_readiness(repo_root: Path | None = None) -> DossierReadiness:
    root = repo_root or repo_root_from_app()
    report_schema = _read_json(root / REPORT_SCHEMA_PATH)
    evidence_schema = _read_json(root / EVIDENCE_SCHEMA_PATH)
    claim_schema = _read_json(root / CLAIM_SCHEMA_PATH)
    artifact_texts = {
        spec.artifact_path: _read_text(root / spec.artifact_path) for spec in ANCHOR_SPECS
    }
    return parse_dossier_readiness(
        report_schema=report_schema,
        evidence_schema=evidence_schema,
        claim_schema=claim_schema,
        artifact_texts=artifact_texts,
    )


def parse_dossier_readiness(
    *,
    report_schema: dict[str, Any],
    evidence_schema: dict[str, Any],
    claim_schema: dict[str, Any],
    artifact_texts: dict[str, str],
) -> DossierReadiness:
    report_fields = _required_fields(
        report_schema,
        REQUIRED_REPORT_FIELDS,
        label="report schema",
    )
    evidence_fields = _required_fields(
        evidence_schema,
        REQUIRED_EVIDENCE_FIELDS,
        label="evidence schema",
    )
    claim_fields = _required_fields(
        claim_schema,
        REQUIRED_CLAIM_FIELDS,
        label="claim schema",
    )
    _require_report_schema_links(report_schema)
    anchors = tuple(_anchor_from_spec(spec, artifact_texts) for spec in ANCHOR_SPECS)
    return DossierReadiness(
        report_schema_path=REPORT_SCHEMA_PATH,
        evidence_schema_path=EVIDENCE_SCHEMA_PATH,
        claim_schema_path=CLAIM_SCHEMA_PATH,
        report_required_fields=report_fields,
        evidence_required_fields=evidence_fields,
        claim_required_fields=claim_fields,
        anchors=anchors,
        boundary=(
            "Local dossier-readiness view only: read-only contract summary from schemas "
            "and tests. It does not change report schema, does not change dossier "
            "generation, does not change claim semantics, does not mutate runtime state, "
            "does not approve DS-017, and does not add hosted identity or full identity/RBAC."
        ),
    )


def _required_fields(
    schema: dict[str, Any],
    required: set[str],
    *,
    label: str,
) -> tuple[str, ...]:
    fields = schema.get("required")
    if not isinstance(fields, list) or not fields:
        raise DossierReadinessError(f"{label} required fields missing")
    field_set = {field for field in fields if isinstance(field, str)}
    missing = sorted(required - field_set)
    if missing:
        raise DossierReadinessError(f"{label} missing required fields: {', '.join(missing)}")
    return tuple(sorted(field_set))


def _require_report_schema_links(report_schema: dict[str, Any]) -> None:
    properties = report_schema.get("properties")
    if not isinstance(properties, dict):
        raise DossierReadinessError("report schema properties missing")
    _require_ref(properties, "evidence", "evidence.schema.json")
    for field in ("claims", "unknowns", "advisory_claims"):
        _require_ref(properties, field, "claim.schema.json")


def _require_ref(properties: dict[Any, Any], field: str, expected_ref: str) -> None:
    raw_field = properties.get(field)
    if not isinstance(raw_field, dict):
        raise DossierReadinessError(f"report schema {field} property missing")
    raw_items = raw_field.get("items")
    if not isinstance(raw_items, dict):
        raise DossierReadinessError(f"report schema {field} items missing")
    ref = raw_items.get("$ref")
    if not isinstance(ref, str) or expected_ref not in ref:
        raise DossierReadinessError(f"report schema {field} must reference {expected_ref}")


def _anchor_from_spec(
    spec: _AnchorSpec,
    artifact_texts: dict[str, str],
) -> DossierAnchor:
    text = artifact_texts.get(spec.artifact_path)
    if text is None:
        raise DossierReadinessError(f"{spec.anchor_id} artifact missing: {spec.artifact_path}")
    if not text.strip():
        raise DossierReadinessError(f"{spec.anchor_id} artifact is empty: {spec.artifact_path}")
    missing = [anchor for anchor in spec.required_text if anchor not in text]
    if missing:
        raise DossierReadinessError(
            f"{spec.anchor_id} missing anchor text: {', '.join(missing)}"
        )
    return DossierAnchor(
        anchor_id=spec.anchor_id,
        artifact_path=spec.artifact_path,
        purpose=spec.purpose,
        anchors=spec.required_text,
    )


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(_read_text(path))
    except json.JSONDecodeError as exc:
        raise DossierReadinessError(f"cannot parse {path}") from exc
    if not isinstance(payload, dict):
        raise DossierReadinessError(f"{path} must contain a JSON object")
    return payload


def _read_text(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise DossierReadinessError(f"cannot read {path}") from exc
    if not text.strip():
        raise DossierReadinessError(f"{path} is empty")
    return text
