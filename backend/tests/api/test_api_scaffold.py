from __future__ import annotations

import json
from pathlib import Path
from typing import cast
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.api.dependencies import ApiServices, get_db_services, get_services
from app.claims_engine.not_evaluated import (
    NOT_EVALUATED_CLAIM_CODES,
    NOT_EVALUATED_DOMAINS,
    NOT_EVALUATED_SOURCE_NAME,
)
from app.core.config import Settings
from app.main import create_app

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "geometries"


def load_geometry(name: str) -> dict[str, object]:
    data = json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return cast(dict[str, object], data)


def not_evaluated_claim_codes() -> list[str]:
    return [NOT_EVALUATED_CLAIM_CODES[domain] for domain in NOT_EVALUATED_DOMAINS]


def auth_headers(
    workspace_id: str | None = None,
    user_id: str | None = None,
) -> dict[str, str]:
    return {
        "X-Workspace-Id": workspace_id or str(uuid4()),
        "X-User-Id": user_id or str(uuid4()),
    }


def create_fixture_area(
    client: TestClient,
    headers: dict[str, str],
    *,
    label: str = "fixture polygon",
) -> dict[str, object]:
    response = client.post(
        "/areas",
        json={
            "label": label,
            "geom_geojson": load_geometry("valid_polygon.geojson"),
            "geom_source": "api fixture",
        },
        headers=headers,
    )
    assert response.status_code == 201
    return cast(dict[str, object], response.json())


def test_api_scaffold_exposes_health_endpoint() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200


def test_api_scaffold_lists_empty_in_memory_resources() -> None:
    client = TestClient(create_app())
    headers = auth_headers()
    area_id = uuid4()

    assert client.get("/sources").json() == []
    assert client.get("/areas").status_code == 401
    assert client.get("/areas", headers=headers).json() == []
    assert client.get(f"/evidence?area_id={area_id}").status_code == 401
    assert client.get(f"/evidence?area_id={area_id}", headers=headers).json() == []


def test_api_runtime_uses_memory_backend_by_default_for_isolated_tests() -> None:
    app = create_app(settings=Settings(APP_STORAGE_BACKEND="postgres"))

    assert app.state.storage_backend == "memory"
    assert get_services not in app.dependency_overrides
    assert hasattr(app.state, "services")


def test_api_runtime_can_use_configured_postgres_backend() -> None:
    app = create_app(
        settings=Settings(APP_STORAGE_BACKEND="postgres"),
        use_db_services=None,
    )

    assert app.state.storage_backend == "postgres"
    assert app.dependency_overrides[get_services] is get_db_services


def test_api_scaffold_creates_and_lists_sources() -> None:
    client = TestClient(create_app())

    create_response = client.post(
        "/sources",
        json={
            "name": "Fixture FEMA",
            "organization": "FEMA",
            "domain": "flood",
            "license_status": "approved",
            "commercial_use_status": "approved",
            "review_status": "approved",
        },
    )

    assert create_response.status_code == 201
    source_id = create_response.json()["source_id"]
    list_response = client.get("/sources")
    assert list_response.status_code == 200
    assert [source["source_id"] for source in list_response.json()] == [source_id]


def test_api_scaffold_creates_and_lists_areas() -> None:
    client = TestClient(create_app())
    workspace_id = str(uuid4())
    user_id = str(uuid4())
    headers = auth_headers(workspace_id, user_id)
    other_headers = auth_headers(str(uuid4()), user_id)

    create_response = client.post(
        "/areas",
        json={
            "label": "fixture polygon",
            "geom_geojson": load_geometry("valid_polygon.geojson"),
            "geom_source": "api fixture",
        },
        headers=headers,
    )

    assert create_response.status_code == 201
    area = create_response.json()
    area_id = area["area_id"]
    assert area["workspace_id"] == workspace_id
    assert area["created_by"] == user_id
    list_response = client.get("/areas", headers=headers)
    assert list_response.status_code == 200
    assert [area["area_id"] for area in list_response.json()] == [area_id]
    assert client.get("/areas", headers=other_headers).json() == []
    mismatch_response = client.post(
        "/areas",
        json={
            "workspace_id": str(uuid4()),
            "label": "fixture polygon",
            "geom_geojson": load_geometry("valid_polygon.geojson"),
        },
        headers=headers,
    )
    assert mismatch_response.status_code == 403
    creator_mismatch_response = client.post(
        "/areas",
        json={
            "created_by": str(uuid4()),
            "label": "fixture polygon",
            "geom_geojson": load_geometry("valid_polygon.geojson"),
        },
        headers=headers,
    )
    assert creator_mismatch_response.status_code == 403


def test_api_scaffold_creates_and_gets_report_run() -> None:
    client = TestClient(create_app())
    headers = auth_headers()
    area_id = create_fixture_area(client, headers)["area_id"]

    create_response = client.post(
        "/report-runs",
        json={"area_id": area_id, "intent_code": "homestead_feasibility"},
        headers=headers,
    )

    assert create_response.status_code == 201
    report_run = create_response.json()
    assert report_run["area_id"] == area_id
    assert report_run["workspace_id"] == headers["X-Workspace-Id"]
    assert report_run["requested_by"] == headers["X-User-Id"]
    assert report_run["status"] == "succeeded"
    assert report_run["review_status"] == "needs_review"
    assert [record["domain"] for record in report_run["evidence"]] == list(NOT_EVALUATED_DOMAINS)
    assert [claim["claim_code"] for claim in report_run["claims"]] == (not_evaluated_claim_codes())
    assert [claim["claim_code"] for claim in report_run["unknowns"]] == (
        not_evaluated_claim_codes()
    )
    assert report_run["source_manifest"]["source_names"] == [NOT_EVALUATED_SOURCE_NAME]
    assert report_run["source_manifest"]["evidence_count"] == 4
    assert report_run["source_manifest"]["claim_count"] == 4
    assert report_run["artifact_metadata"]["artifact_kind"] == "report_run"
    assert report_run["artifact_metadata"]["report_schema"] == "report_run_contract_v1"
    assert report_run["artifact_metadata"]["persistence"] == "memory"
    assert report_run["artifact_metadata"]["cost_metrics"]["unknown_count"] == 4

    get_response = client.get(f"/report-runs/{report_run['report_run_id']}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["report_run_id"] == report_run["report_run_id"]
    assert (
        client.get(
            f"/report-runs/{report_run['report_run_id']}",
            headers=auth_headers(),
        ).status_code
        == 404
    )

    list_response = client.get(
        f"/report-runs?area_id={area_id}&intent_code=homestead_feasibility",
        headers=headers,
    )
    assert list_response.status_code == 200
    assert [run["report_run_id"] for run in list_response.json()] == [
        report_run["report_run_id"]
    ]
    assert client.get(f"/report-runs?area_id={uuid4()}", headers=headers).json() == []
    assert client.get("/report-runs?limit=0", headers=headers).status_code == 422


def test_api_report_run_create_supports_scope_and_idempotency() -> None:
    client = TestClient(create_app())
    workspace_id = str(uuid4())
    requested_by = str(uuid4())
    other_workspace_id = str(uuid4())
    headers = auth_headers(workspace_id, requested_by)
    area = create_fixture_area(client, headers)
    payload = {
        "area_id": area["area_id"],
        "intent_code": "homestead_feasibility",
        "workspace_id": workspace_id,
        "requested_by": requested_by,
        "idempotency_key": "sync-report-key-1",
    }

    first_response = client.post("/report-runs", json=payload)
    second_response = client.post("/report-runs", json=payload, headers=headers)

    assert first_response.status_code == 401
    assert second_response.status_code == 201
    first_response = client.post("/report-runs", json=payload, headers=headers)
    assert first_response.status_code == 201
    first = first_response.json()
    second = second_response.json()
    assert second["report_run_id"] == first["report_run_id"]
    assert first["workspace_id"] == workspace_id
    assert first["requested_by"] == requested_by
    assert first["idempotency_key"] == "sync-report-key-1"
    list_response = client.get(f"/report-runs?workspace_id={workspace_id}", headers=headers)
    assert [run["report_run_id"] for run in list_response.json()] == [
        first["report_run_id"]
    ]
    assert (
        client.get(f"/report-runs?workspace_id={other_workspace_id}", headers=headers).status_code
        == 403
    )
    mismatch_response = client.post(
        "/report-runs",
        json={**payload, "workspace_id": other_workspace_id},
        headers=headers,
    )
    assert mismatch_response.status_code == 403
    assert (
        client.post(
            "/report-runs",
            json={
                **payload,
                "workspace_id": None,
                "area_id": create_fixture_area(
                    client,
                    auth_headers(other_workspace_id, requested_by),
                    label="other workspace polygon",
                )["area_id"],
            },
            headers=headers,
        ).status_code
        == 404
    )


def test_api_report_run_jobs_are_queued_and_idempotent() -> None:
    client = TestClient(create_app())
    workspace_id = str(uuid4())
    user_id = str(uuid4())
    headers = auth_headers(workspace_id, user_id)
    area = create_fixture_area(client, headers)
    payload = {
        "area_id": area["area_id"],
        "intent_code": "homestead_feasibility",
        "workspace_id": workspace_id,
        "idempotency_key": "queued-report-key-1",
    }

    first_response = client.post("/report-runs/jobs", json=payload)
    second_response = client.post("/report-runs/jobs", json=payload, headers=headers)

    assert first_response.status_code == 401
    first_response = client.post("/report-runs/jobs", json=payload, headers=headers)
    assert first_response.status_code == 202
    assert second_response.status_code == 202
    first = first_response.json()
    second = second_response.json()
    assert second["job_id"] == first["job_id"]
    assert first["status"] == "queued"
    assert first["workspace_id"] == workspace_id
    assert first["idempotency_key"] == "queued-report-key-1"
    get_response = client.get(f"/report-runs/jobs/{first['job_id']}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["job_id"] == first["job_id"]
    execute_response = client.post(
        "/report-runs/jobs/execute-next",
        json={"worker_id": "api-report-worker-1"},
        headers=headers,
    )
    assert execute_response.status_code == 200
    executed = execute_response.json()
    assert executed["job_id"] == first["job_id"]
    assert executed["status"] == "succeeded"
    assert executed["attempts"] == 1
    assert executed["locked_by"] is None
    assert executed["report_run_id"] is not None
    report_response = client.get(f"/report-runs/{executed['report_run_id']}", headers=headers)
    assert report_response.status_code == 200
    assert report_response.json()["idempotency_key"] == "queued-report-key-1"
    assert (
        client.post(
            "/report-runs/jobs/execute-next",
            json={"worker_id": "api-report-worker-1"},
            headers=headers,
        ).status_code
        == 404
    )
    assert (
        client.post(
            "/report-runs/jobs/execute-next",
            json={"worker_id": "api-report-worker-1"},
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/report-runs/jobs",
            json={
                "area_id": area["area_id"],
                "intent_code": "homestead_feasibility",
                "idempotency_key": " ",
            },
            headers=headers,
        ).status_code
        == 422
    )


def test_api_report_run_review_actions_update_review_status() -> None:
    client = TestClient(create_app())
    workspace_id = str(uuid4())
    user_id = str(uuid4())
    headers = auth_headers(workspace_id, user_id)
    area = create_fixture_area(client, headers)
    create_response = client.post(
        "/report-runs",
        json={
            "area_id": area["area_id"],
            "intent_code": "homestead_feasibility",
        },
        headers=headers,
    )
    report_run_id = create_response.json()["report_run_id"]

    approve_response = client.post(
        f"/report-runs/{report_run_id}/approve",
        json={"reviewer_id": user_id, "reason": "ready"},
        headers=headers,
    )

    assert approve_response.status_code == 200
    approved = approve_response.json()
    assert approved["review_status"] == "approved"
    assert approved["reviewed_by"] == user_id
    assert approved["review_actions"][0]["from_status"] == "needs_review"
    assert approved["review_actions"][0]["to_status"] == "approved"

    supersede_response = client.post(
        f"/report-runs/{report_run_id}/supersede",
        json={"reviewer_id": user_id, "reason": "new evidence"},
        headers=headers,
    )

    assert supersede_response.status_code == 200
    assert supersede_response.json()["review_status"] == "superseded"
    assert len(supersede_response.json()["review_actions"]) == 2


def test_api_report_run_dossier_is_gated_on_approved_review() -> None:
    client = TestClient(create_app())
    workspace_id = str(uuid4())
    user_id = str(uuid4())
    headers = auth_headers(workspace_id, user_id)
    area = create_fixture_area(client, headers)
    create_response = client.post(
        "/report-runs",
        json={
            "area_id": area["area_id"],
            "intent_code": "homestead_feasibility",
        },
        headers=headers,
    )
    report_run_id = create_response.json()["report_run_id"]

    blocked_response = client.get(f"/report-runs/{report_run_id}/dossier", headers=headers)

    assert blocked_response.status_code == 409
    assert "requires approved review status" in blocked_response.json()["detail"]

    client.post(
        f"/report-runs/{report_run_id}/approve",
        json={"reviewer_id": user_id, "reason": "ready"},
        headers=headers,
    )
    dossier_response = client.get(f"/report-runs/{report_run_id}/dossier", headers=headers)

    assert dossier_response.status_code == 200
    assert dossier_response.headers["content-type"].startswith("text/markdown")
    assert "# Rural Land Dossier" in dossier_response.text
    assert "- Review status: approved" in dossier_response.text


def test_api_report_run_review_actions_validate_transitions() -> None:
    client = TestClient(create_app())
    workspace_id = str(uuid4())
    user_id = str(uuid4())
    headers = auth_headers(workspace_id, user_id)
    area = create_fixture_area(client, headers)
    create_response = client.post(
        "/report-runs",
        json={
            "area_id": area["area_id"],
            "intent_code": "homestead_feasibility",
        },
        headers=headers,
    )
    report_run_id = create_response.json()["report_run_id"]

    assert (
        client.post(
            f"/report-runs/{report_run_id}/reject",
            json={"reviewer_id": user_id},
            headers=headers,
        ).status_code
        == 422
    )
    assert (
        client.post(
            f"/report-runs/{uuid4()}/approve",
            json={"reviewer_id": user_id},
            headers=headers,
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/report-runs/{report_run_id}/approve",
            json={"reviewer_id": str(uuid4())},
            headers=headers,
        ).status_code
        == 403
    )


def test_api_report_run_surfaces_source_failure_unknowns() -> None:
    app = create_app()
    client = TestClient(app)
    headers = auth_headers()
    source_response = client.post(
        "/sources",
        json={
            "name": "Fixture FEMA failure source",
            "organization": "FEMA",
            "domain": "flood",
            "license_status": "approved",
            "commercial_use_status": "approved",
            "review_status": "approved",
        },
    )
    area = create_fixture_area(client, headers)
    source_id = UUID(source_response.json()["source_id"])
    area_id = UUID(str(area["area_id"]))
    services = cast(ApiServices, app.state.services)
    services.evidence_service.create_source_failure(
        area_id=area_id,
        source_id=source_id,
        method_code="fixture_flood_overlay",
        evidence_code="FLOOD_SOURCE_FAILURE",
        domain="flood",
        caveat="FEMA fixture endpoint returned 503.",
    )

    create_response = client.post(
        "/report-runs",
        json={
            "area_id": str(area_id),
            "intent_code": "homestead_feasibility",
        },
        headers=headers,
    )

    assert create_response.status_code == 201
    report_run = create_response.json()
    assert [claim["claim_code"] for claim in report_run["unknowns"]] == [
        "FLOOD_SOURCE_UNAVAILABLE_UNKNOWN",
        *not_evaluated_claim_codes(),
    ]
    assert report_run["artifact_metadata"]["cost_metrics"]["unknown_count"] == 5


def test_api_evidence_lists_only_authenticated_workspace_area_records() -> None:
    app = create_app()
    client = TestClient(app)
    headers = auth_headers()
    other_headers = auth_headers()
    source_response = client.post(
        "/sources",
        json={
            "name": "Fixture evidence source",
            "organization": "FEMA",
            "domain": "flood",
            "license_status": "approved",
            "commercial_use_status": "approved",
            "review_status": "approved",
        },
    )
    area = create_fixture_area(client, headers)
    source_id = UUID(source_response.json()["source_id"])
    area_id = UUID(str(area["area_id"]))
    services = cast(ApiServices, app.state.services)
    services.evidence_service.create_source_failure(
        area_id=area_id,
        source_id=source_id,
        method_code="fixture_flood_overlay",
        evidence_code="FLOOD_SOURCE_FAILURE",
        domain="flood",
        caveat="FEMA fixture endpoint returned 503.",
    )

    response = client.get(f"/evidence?area_id={area_id}", headers=headers)

    assert response.status_code == 200
    assert [record["area_id"] for record in response.json()] == [str(area_id)]
    assert client.get(f"/evidence?area_id={area_id}", headers=other_headers).json() == []


def test_api_scaffold_returns_422_for_bad_input() -> None:
    client = TestClient(create_app())
    headers = auth_headers()

    assert client.post("/sources", json={"name": "Missing domain"}).status_code == 422
    assert (
        client.post(
            "/areas",
            json={"geom_geojson": load_geometry("wrong_type.geojson")},
            headers=headers,
        ).status_code
        == 422
    )
    assert client.post("/report-runs", json={"intent_code": "missing area"}).status_code == 401
    assert (
        client.post(
            "/report-runs",
            json={"intent_code": "missing area"},
            headers=auth_headers(),
        ).status_code
        == 422
    )
    assert client.get("/evidence", headers=headers).status_code == 422
