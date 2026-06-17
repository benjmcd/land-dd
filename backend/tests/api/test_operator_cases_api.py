from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

import yaml
from fastapi.testclient import TestClient

import app.api.operator_cases as operator_cases_api
from app.api.dependencies import ApiServices
from app.core.config import Settings
from app.domain.area_contracts import AreaContract
from app.domain.enums import IntentCode
from app.main import create_app

ROOT = Path(__file__).resolve().parents[3]
MANIFEST_PATH = ROOT / "tests" / "fixtures" / "golden_aois" / "manifest.yaml"
GEOMETRY_FIXTURE_PATH = ROOT / "tests" / "fixtures" / "geometries" / "valid_polygon.geojson"
_WORKSPACE_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
_USER_ID = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
_REVIEWER_ID = "fixture-reviewer"
_REVIEWER_TOKEN = "fixture-token-123"


def _auth_headers(
    *,
    workspace_id: UUID = _WORKSPACE_ID,
    user_id: UUID = _USER_ID,
    reviewer_id: str = _REVIEWER_ID,
    reviewer_token: str = _REVIEWER_TOKEN,
) -> dict[str, str]:
    return {
        "X-Workspace-Id": str(workspace_id),
        "X-User-Id": str(user_id),
        "X-Reviewer-Id": reviewer_id,
        "X-Reviewer-Token": reviewer_token,
    }


def _selected_county_cases() -> list[dict[str, Any]]:
    manifest = cast(
        dict[str, Any],
        yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8")),
    )
    return [
        {
            "case_id": case["case_id"],
            "county": case["county"],
            "state": case["state"],
            "intent": case["intent"],
            "description": case["description"],
            "connector_domains": list(case["expected_connector_workflow_domains"]),
            "fixture_only": True,
        }
        for case in manifest["cases"]
    ]


def _valid_geojson() -> dict[str, object]:
    data = json.loads(GEOMETRY_FIXTURE_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


class _FakeOperatorCasesContract:
    def __init__(self) -> None:
        self._cases = {case["case_id"]: case for case in _selected_county_cases()}

    def list_selected_county_cases(self) -> list[dict[str, Any]]:
        return list(self._cases.values())

    def get_selected_county_case(self, case_id: str) -> dict[str, Any] | None:
        return self._cases.get(case_id)

    def create_selected_county_report(
        self,
        services: ApiServices,
        case_id: str,
        reviewer_id: str = "fixture-reviewer",
        reason: str = "private_mvp_fixture_only",
        workspace_id: UUID | None = None,
        requested_by: UUID | None = None,
    ) -> dict[str, Any]:
        case = self._cases[case_id]
        area_seed = (
            f"selected-county:{workspace_id}:{case_id}"
            if workspace_id
            else f"selected-county:{case_id}"
        )
        area_id = uuid5(NAMESPACE_URL, area_seed)
        if services.area_service.get(area_id) is None:
            services.area_service.create(
                AreaContract(
                    area_id=area_id,
                    workspace_id=workspace_id,
                    created_by=requested_by,
                    label=f"selected-county-{case_id.lower()}",
                    geom_geojson=_valid_geojson(),
                    geom_source="selected-county-fixture",
                )
            )
        report = services.report_service.create_report_run(
            area_id=area_id,
            intent_code=IntentCode(case["intent"]),
            workspace_id=workspace_id,
            requested_by=requested_by,
        )
        approved = services.report_service.approve_report_run(
            report.report_run_id,
            reviewer_id=reviewer_id,
            reason=reason,
        )
        assert approved is not None
        return {
            "case_id": case_id,
            "report_run_id": approved.report_run_id,
            "review_status": approved.review_status,
            "status": approved.status,
            "fixture_only": True,
            "connector_count": len(case["connector_domains"]),
            "evidence_count": len(approved.evidence),
            "links": {
                "ui": f"/ui/report-runs/{approved.report_run_id}",
                "dossier_download": f"/report-runs/{approved.report_run_id}/dossier?download=1",
                "artifact": f"/report-runs/{approved.report_run_id}/artifact",
            },
        }


class _CapturingOperatorCasesContract(_FakeOperatorCasesContract):
    def __init__(self) -> None:
        super().__init__()
        self.reviewer_id: str | None = None
        self.reason: str | None = None
        self.workspace_id: UUID | None = None
        self.requested_by: UUID | None = None

    def create_selected_county_report(
        self,
        services: ApiServices,
        case_id: str,
        reviewer_id: str = "fixture-reviewer",
        reason: str = "private_mvp_fixture_only",
        workspace_id: UUID | None = None,
        requested_by: UUID | None = None,
    ) -> dict[str, Any]:
        self.reviewer_id = reviewer_id
        self.reason = reason
        self.workspace_id = workspace_id
        self.requested_by = requested_by
        return super().create_selected_county_report(
            services,
            case_id,
            reviewer_id=reviewer_id,
            reason=reason,
            workspace_id=workspace_id,
            requested_by=requested_by,
        )


def test_operator_cases_list_returns_all_nine_fixture_cases(
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr(
        operator_cases_api,
        "resolve_operator_cases_contract",
        lambda: _FakeOperatorCasesContract(),
    )
    client = TestClient(create_app())

    response = client.get("/operator-cases")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 9
    assert {item["case_id"] for item in body} == {
        case["case_id"] for case in _selected_county_cases()
    }
    assert all(item["fixture_only"] is True for item in body)
    assert all(item["connector_domains"] for item in body)
    assert all(item["fixture_scope"] == "private_mvp_fixture" for item in body)
    assert all("fixture_language" in item for item in body)
    assert all("not_evaluated_domains" in item for item in body)
    assert all("expected_unknowns" in item for item in body)


def test_operator_case_report_create_returns_approved_report_and_artifact(
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr(
        operator_cases_api,
        "resolve_operator_cases_contract",
        lambda: _FakeOperatorCasesContract(),
    )
    client = TestClient(create_app())

    response = client.post("/operator-cases/BUN-slope/report", headers=_auth_headers())

    assert response.status_code == 201
    body = response.json()
    assert body["case_id"] == "BUN-slope"
    assert body["review_status"] == "approved"
    assert body["status"] == "succeeded"
    assert body["fixture_only"] is True
    assert body["connector_count"] == 5
    report_run_id = body["report_run_id"]
    assert body["links"]["ui"] == f"/ui/report-runs/{report_run_id}"
    assert body["links"]["dossier_download"] == (
        f"/report-runs/{report_run_id}/dossier?download=1"
    )
    assert body["links"]["artifact"] == f"/report-runs/{report_run_id}/artifact"

    artifact_response = client.get(body["links"]["artifact"])

    assert artifact_response.status_code == 200
    artifact = artifact_response.json()
    assert artifact["report_run_id"] == report_run_id
    assert artifact["workspace_id"] == str(_WORKSPACE_ID)
    assert artifact["requested_by"] == str(_USER_ID)
    assert artifact["reviewed_by"] == _REVIEWER_ID


def test_operator_case_report_create_rejects_missing_workspace_identity() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/operator-cases/BUN-slope/report",
        headers={
            "X-Reviewer-Id": _REVIEWER_ID,
            "X-Reviewer-Token": _REVIEWER_TOKEN,
        },
    )

    assert response.status_code == 401
    assert "X-Workspace-Id" in response.text


def test_operator_case_report_create_rejects_missing_reviewer_auth() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/operator-cases/BUN-slope/report",
        headers={
            "X-Workspace-Id": str(_WORKSPACE_ID),
            "X-User-Id": str(_USER_ID),
        },
    )

    assert response.status_code == 401
    assert "reviewer credentials" in response.text


def test_operator_case_report_create_rejects_reviewer_without_report_run_scope() -> None:
    settings = Settings(
        REVIEWER_ACCOUNTS="limited:limited-token",
        REVIEWER_ACCOUNT_SCOPES="limited:operations:read",
    )
    client = TestClient(create_app(settings=settings))

    response = client.post(
        "/operator-cases/BUN-slope/report",
        headers=_auth_headers(
            reviewer_id="limited",
            reviewer_token="limited-token",
        ),
    )

    assert response.status_code == 403
    assert "report:run" in response.text


def test_operator_case_report_create_rejects_body_reviewer_mismatch() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/operator-cases/BUN-slope/report",
        headers=_auth_headers(),
        json={"reviewer_id": "other-reviewer"},
    )

    assert response.status_code == 403
    assert "reviewer_id" in response.text


def test_operator_case_report_create_rejects_unknown_case_id(
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr(
        operator_cases_api,
        "resolve_operator_cases_contract",
        lambda: _FakeOperatorCasesContract(),
    )
    client = TestClient(create_app())

    response = client.post("/operator-cases/NOT-A-CASE/report", headers=_auth_headers())

    assert response.status_code == 404
    assert "fixture case" in response.json()["detail"]


def test_operator_case_report_create_uses_packaged_case_service() -> None:
    client = TestClient(create_app())

    first = client.post("/operator-cases/BUN-slope/report", headers=_auth_headers())
    second = client.post(
        "/operator-cases/CHA-zoning-edge/report",
        headers=_auth_headers(user_id=uuid4()),
    )

    assert first.status_code == 201
    assert second.status_code == 201
    first_body = first.json()
    second_body = second.json()
    assert first_body["case_id"] == "BUN-slope"
    assert second_body["case_id"] == "CHA-zoning-edge"
    assert first_body["report_run_id"] != second_body["report_run_id"]
    assert first_body["review_status"] == "approved"
    assert second_body["review_status"] == "approved"
    assert first_body["evidence_count"] > 0
    assert second_body["evidence_count"] > 0

    first_artifact = client.get(first_body["links"]["artifact"])
    second_artifact = client.get(second_body["links"]["artifact"])

    assert first_artifact.status_code == 200
    assert second_artifact.status_code == 200
    assert first_artifact.json()["report_run_id"] == first_body["report_run_id"]
    assert second_artifact.json()["report_run_id"] == second_body["report_run_id"]
    assert first_artifact.json()["workspace_id"] == str(_WORKSPACE_ID)
    assert first_artifact.json()["requested_by"] == str(_USER_ID)
    assert first_artifact.json()["reviewed_by"] == _REVIEWER_ID


def test_operator_case_report_rejects_blank_reviewer_id() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/operator-cases/BUN-slope/report",
        headers=_auth_headers(),
        json={"reviewer_id": "   "},
    )

    assert response.status_code == 422
    assert "reviewer_id" in response.text


def test_operator_case_report_rejects_blank_reason() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/operator-cases/BUN-slope/report",
        headers=_auth_headers(),
        json={"reason": "   "},
    )

    assert response.status_code == 422
    assert "reason" in response.text


def test_operator_case_report_rejects_unrecognized_body_fields() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/operator-cases/BUN-slope/report",
        headers=_auth_headers(),
        json={"reviewer_id": "operator", "unexpected": "ignored?"},
    )

    assert response.status_code == 422
    assert "unexpected" in response.text


def test_operator_case_report_strips_reviewer_id_and_reason(
    monkeypatch: Any,
) -> None:
    contract = _CapturingOperatorCasesContract()
    monkeypatch.setattr(
        operator_cases_api,
        "resolve_operator_cases_contract",
        lambda: contract,
    )
    client = TestClient(create_app())

    response = client.post(
        "/operator-cases/BUN-slope/report",
        headers=_auth_headers(),
        json={"reviewer_id": "  fixture-reviewer  ", "reason": "  reviewed  "},
    )

    assert response.status_code == 201
    assert contract.reviewer_id == _REVIEWER_ID
    assert contract.reason == "reviewed"
    assert contract.workspace_id == _WORKSPACE_ID
    assert contract.requested_by == _USER_ID
