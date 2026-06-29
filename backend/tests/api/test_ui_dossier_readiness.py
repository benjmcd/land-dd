from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

from app.api import ui as ui_module
from app.dossier_readiness import (
    DossierReadinessError,
    load_dossier_readiness,
    parse_dossier_readiness,
)
from app.main import create_app

REPO_ROOT = Path(__file__).resolve().parents[3]


def _schema(path: str) -> dict[str, Any]:
    import json

    payload = json.loads((REPO_ROOT / path).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return cast(dict[str, Any], payload)


def _artifact_texts() -> dict[str, str]:
    paths = (
        "backend/tests/reports/test_report_service.py",
        "backend/tests/reports/test_report_overclaim.py",
        "backend/tests/api/test_ui_routes.py",
        "backend/tests/reports/test_report_regression.py",
    )
    return {path: (REPO_ROOT / path).read_text(encoding="utf-8") for path in paths}


def test_dossier_readiness_loader_summarizes_report_contract_artifacts() -> None:
    readiness = load_dossier_readiness(REPO_ROOT)

    assert readiness.report_schema_path == "schemas/report_run_schema.json"
    assert readiness.evidence_schema_path == "schemas/evidence_schema.json"
    assert readiness.claim_schema_path == "schemas/claim_schema.json"
    assert {
        "evidence",
        "claims",
        "unknowns",
        "caveats",
        "source_manifest",
        "artifact_metadata",
    }.issubset(set(readiness.report_required_fields))
    assert {
        "evidence_id",
        "source_id",
        "source_ingest_run_id",
        "confidence",
        "caveat",
    }.issubset(set(readiness.evidence_required_fields))
    assert {
        "claim_id",
        "evidence_ids",
        "confidence",
        "user_safe_language",
        "verification_task",
    }.issubset(set(readiness.claim_required_fields))
    assert {anchor.anchor_id for anchor in readiness.anchors} == {
        "approved_dossier_gate",
        "lineage_gate",
        "source_failure_unknowns_gate",
        "safe_language_overclaim_gate",
        "regression_artifact_contract",
    }


def test_dossier_readiness_parser_fails_closed_on_missing_report_required_field() -> None:
    report_schema = _schema("schemas/report_run_schema.json")
    evidence_schema = _schema("schemas/evidence_schema.json")
    claim_schema = _schema("schemas/claim_schema.json")
    report_schema = deepcopy(report_schema)
    report_schema["required"] = [
        field for field in report_schema["required"] if field != "source_manifest"
    ]

    with pytest.raises(DossierReadinessError, match="source_manifest"):
        parse_dossier_readiness(
            report_schema=report_schema,
            evidence_schema=evidence_schema,
            claim_schema=claim_schema,
            artifact_texts=_artifact_texts(),
        )


def test_dossier_readiness_parser_fails_closed_on_missing_anchor_text() -> None:
    report_schema = _schema("schemas/report_run_schema.json")
    evidence_schema = _schema("schemas/evidence_schema.json")
    claim_schema = _schema("schemas/claim_schema.json")
    artifact_texts = _artifact_texts()
    artifact_texts["backend/tests/reports/test_report_overclaim.py"] = artifact_texts[
        "backend/tests/reports/test_report_overclaim.py"
    ].replace("_assert_no_forbidden_phrases", "_anchor_removed")

    with pytest.raises(DossierReadinessError, match="safe_language_overclaim_gate"):
        parse_dossier_readiness(
            report_schema=report_schema,
            evidence_schema=evidence_schema,
            claim_schema=claim_schema,
            artifact_texts=artifact_texts,
        )


def test_ui_dossier_readiness_route_renders_contract_artifacts_and_boundaries() -> None:
    client = TestClient(create_app())

    response = client.get("/ui/dossier-readiness")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert 'name="viewport"' in response.text
    assert "Local Dossier Readiness" in response.text
    assert "Report Schema Contract" in response.text
    assert "schemas/report_run_schema.json" in response.text
    for field in (
        "evidence",
        "claims",
        "unknowns",
        "caveats",
        "source_manifest",
        "artifact_metadata",
    ):
        assert field in response.text
    for field in (
        "evidence_id",
        "source_id",
        "source_ingest_run_id",
        "confidence",
        "caveat",
        "claim_id",
        "evidence_ids",
        "user_safe_language",
    ):
        assert field in response.text
    for anchor in (
        "approved_dossier_gate",
        "lineage_gate",
        "source_failure_unknowns_gate",
        "safe_language_overclaim_gate",
    ):
        assert anchor in response.text
    assert "backend/tests/reports/test_report_overclaim.py" in response.text
    assert "read-only contract summary" in response.text
    assert "does not change report schema" in response.text
    assert "does not change dossier generation" in response.text
    assert "does not approve DS-017" in response.text
    assert "full identity/RBAC" in response.text


def test_ui_dossier_readiness_route_returns_503_when_loader_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _raise_loader() -> None:
        raise DossierReadinessError("test dossier readiness failure")

    monkeypatch.setattr(ui_module, "load_dossier_readiness", _raise_loader)
    client = TestClient(create_app())

    response = client.get("/ui/dossier-readiness")

    assert response.status_code == 503
    assert "Dossier readiness unavailable from repo-owned contract artifacts" in response.text
    assert "test dossier readiness failure" in response.text
    assert "Traceback" not in response.text


def test_ui_navigation_links_to_dossier_readiness() -> None:
    client = TestClient(create_app())

    # The /ui/readiness hub page is not part of this harvest; navigation is
    # asserted against the readiness pages that exist on this branch.
    home = client.get("/ui/")
    expansion = client.get("/ui/expansion")
    raw_data = client.get("/ui/raw-data")

    assert home.status_code == 200
    assert expansion.status_code == 200
    assert raw_data.status_code == 200
    assert 'href="/ui/dossier-readiness"' in home.text
    assert 'href="/ui/dossier-readiness"' in expansion.text
    assert 'href="/ui/dossier-readiness"' in raw_data.text
