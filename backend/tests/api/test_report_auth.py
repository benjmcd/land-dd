from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import cast
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient

from app.api.dependencies import ApiServices, create_api_services, get_services
from app.api.report_auth import create_report_identity_token, verify_report_identity_token
from app.api.reports import _optional_report_auth_context
from app.core.config import Settings
from app.domain.enums import IntentCode, JobStatus
from app.main import create_app

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "geometries"
SECRET = "report-identity-secret-with-at-least-32-characters"


def load_geometry(name: str) -> dict[str, object]:
    data = json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return cast(dict[str, object], data)


def create_area(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post(
        "/areas",
        json={
            "label": "signed token fixture polygon",
            "geom_geojson": load_geometry("valid_polygon.geojson"),
            "geom_source": "api fixture",
        },
        headers=headers,
    )
    assert response.status_code == 201
    return str(response.json()["area_id"])


def bearer_headers(workspace_id: str, user_id: str) -> dict[str, str]:
    token = create_report_identity_token(
        workspace_id=UUID(workspace_id),
        user_id=UUID(user_id),
        secret=SECRET,
        expires_in=timedelta(minutes=10),
    )
    return {"Authorization": f"Bearer {token}"}


def signed_token_client(secret: str | None = SECRET) -> TestClient:
    return TestClient(
        create_app(
            settings=Settings(
                REPORT_AUTH_MODE="signed_token",
                REPORT_IDENTITY_TOKEN_SECRET=secret,
            )
        )
    )


def request_with_settings(settings: Settings) -> Request:
    app = FastAPI()
    app.state.settings = settings
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [],
            "app": app,
        }
    )


def test_optional_report_auth_allows_anonymous_local_trusted_headers() -> None:
    auth = _optional_report_auth_context(
        request_with_settings(
            Settings(APP_ENV="local", REPORT_AUTH_MODE="trusted_headers")
        ),
        authorization=None,
        x_workspace_id=None,
        x_user_id=None,
    )

    assert auth is None


def test_optional_report_auth_requires_workspace_identity_in_non_local_env() -> None:
    with pytest.raises(HTTPException) as exc_info:
        _optional_report_auth_context(
            request_with_settings(
                Settings(APP_ENV="production", REPORT_AUTH_MODE="trusted_headers")
            ),
            authorization=None,
            x_workspace_id=None,
            x_user_id=None,
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "X-Workspace-Id header is required"


def test_report_create_route_requires_workspace_identity_in_non_local_env() -> None:
    settings = Settings(
        APP_ENV="production",
        USE_DB_SERVICES=True,
        REPORT_AUTH_MODE="trusted_headers",
        REVIEWER_ACCOUNTS=f"reviewer:sha256:{hashlib.sha256(b'token').hexdigest()}",
        REVIEWER_ACCOUNT_SCOPES="reviewer:operations:read",
    )
    services = create_api_services(settings)
    app = create_app(settings=settings)
    app.dependency_overrides[get_services] = lambda: services
    client = TestClient(app)
    area = client.post(
        "/areas",
        json={
            "label": "production fixture polygon",
            "geom_geojson": load_geometry("valid_polygon.geojson"),
            "geom_source": "api fixture",
        },
    )
    assert area.status_code == 201

    response = client.post(
        "/report-runs",
        json={
            "area_id": area.json()["area_id"],
            "intent_code": "homestead_feasibility",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "X-Workspace-Id header is required"


def test_optional_report_auth_signed_token_fails_closed_without_valid_bearer_token() -> None:
    request = request_with_settings(
        Settings(
            REPORT_AUTH_MODE="signed_token",
            REPORT_IDENTITY_TOKEN_SECRET=SECRET,
        )
    )

    with pytest.raises(HTTPException) as missing_exc:
        _optional_report_auth_context(
            request,
            authorization=None,
            x_workspace_id=None,
            x_user_id=None,
        )
    with pytest.raises(HTTPException) as invalid_exc:
        _optional_report_auth_context(
            request,
            authorization="Bearer invalid",
            x_workspace_id=None,
            x_user_id=None,
        )

    assert missing_exc.value.status_code == 401
    assert invalid_exc.value.status_code == 401


def test_signed_token_area_create_uses_token_identity_over_body() -> None:
    client = signed_token_client()
    workspace_id = str(uuid4())
    user_id = str(uuid4())

    response = client.post(
        "/areas",
        json={
            "label": "signed token fixture polygon",
            "workspace_id": str(uuid4()),
            "created_by": str(uuid4()),
            "geom_geojson": load_geometry("valid_polygon.geojson"),
            "geom_source": "api fixture",
        },
        headers=bearer_headers(workspace_id, user_id),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["workspace_id"] == workspace_id
    assert body["created_by"] == user_id


def test_signed_report_identity_token_binds_report_scope() -> None:
    client = signed_token_client()
    workspace_id = str(uuid4())
    user_id = str(uuid4())
    area_id = create_area(client, bearer_headers(workspace_id, user_id))

    response = client.post(
        "/report-runs",
        json={"area_id": area_id, "intent_code": "homestead_feasibility"},
        headers=bearer_headers(workspace_id, user_id),
    )

    assert response.status_code == 202
    job = response.json()
    assert job["status"] == "queued"
    assert set(job) == {
        "report_run_id",
        "status",
        "connector_ingest_run_id",
        "connector_review_status",
        "retry_of_report_run_id",
    }
    report = client.get(
        f"/report-runs/{job['report_run_id']}",
        headers=bearer_headers(workspace_id, user_id),
    ).json()
    assert report["workspace_id"] == workspace_id
    assert report["requested_by"] == user_id
    assert (
        client.get(
            f"/report-runs/{report['report_run_id']}",
            headers=bearer_headers(str(uuid4()), user_id),
        ).status_code
        == 404
    )


def test_signed_report_create_idempotency_replays_same_report() -> None:
    client = signed_token_client()
    workspace_id = str(uuid4())
    user_id = str(uuid4())
    headers = bearer_headers(workspace_id, user_id)
    area_id = create_area(client, headers)
    payload = {"area_id": area_id, "intent_code": "homestead_feasibility"}
    key = str(uuid4())

    first = client.post(
        "/report-runs",
        json=payload,
        headers={**headers, "Idempotency-Key": key},
    )
    second = client.post(
        "/report-runs",
        json=payload,
        headers={**headers, "Idempotency-Key": key},
    )

    assert first.status_code == 202
    assert second.status_code == 200
    assert first.json()["report_run_id"] == second.json()["report_run_id"]
    assert set(second.json()) == {
        "report_run_id",
        "status",
        "connector_ingest_run_id",
        "connector_review_status",
        "retry_of_report_run_id",
    }
    report = client.get(
        f"/report-runs/{second.json()['report_run_id']}",
        headers=headers,
    ).json()
    assert report["workspace_id"] == workspace_id
    assert report["requested_by"] == user_id


def test_signed_report_create_idempotency_rejects_payload_mismatch() -> None:
    client = signed_token_client()
    workspace_id = str(uuid4())
    user_id = str(uuid4())
    headers = bearer_headers(workspace_id, user_id)
    area_id_1 = create_area(client, headers)
    area_id_2 = create_area(client, headers)
    key = str(uuid4())

    first = client.post(
        "/report-runs",
        json={"area_id": area_id_1, "intent_code": "homestead_feasibility"},
        headers={**headers, "Idempotency-Key": key},
    )
    second = client.post(
        "/report-runs",
        json={"area_id": area_id_2, "intent_code": "homestead_feasibility"},
        headers={**headers, "Idempotency-Key": key},
    )

    assert first.status_code == 202
    assert second.status_code == 409
    assert "different payload" in second.json()["detail"]


def test_signed_report_create_idempotency_is_principal_scoped() -> None:
    client = signed_token_client()
    workspace_a = str(uuid4())
    workspace_b = str(uuid4())
    user_a = str(uuid4())
    user_b = str(uuid4())
    headers_a = bearer_headers(workspace_a, user_a)
    headers_b = bearer_headers(workspace_b, user_b)
    area_a = create_area(client, headers_a)
    area_b = create_area(client, headers_b)
    key = str(uuid4())

    first = client.post(
        "/report-runs",
        json={"area_id": area_a, "intent_code": "homestead_feasibility"},
        headers={**headers_a, "Idempotency-Key": key},
    )
    second = client.post(
        "/report-runs",
        json={"area_id": area_b, "intent_code": "homestead_feasibility"},
        headers={**headers_b, "Idempotency-Key": key},
    )

    assert first.status_code == 202
    assert second.status_code == 202
    assert first.json()["report_run_id"] != second.json()["report_run_id"]
    first_report = client.get(
        f"/report-runs/{first.json()['report_run_id']}",
        headers=headers_a,
    ).json()
    second_report = client.get(
        f"/report-runs/{second.json()['report_run_id']}",
        headers=headers_b,
    ).json()
    assert first_report["workspace_id"] == workspace_a
    assert second_report["workspace_id"] == workspace_b


def test_signed_report_identity_token_rejects_missing_invalid_and_mismatch() -> None:
    client = signed_token_client()
    workspace_id = str(uuid4())
    user_id = str(uuid4())
    area_id = create_area(client, bearer_headers(workspace_id, user_id))
    payload = {"area_id": area_id, "intent_code": "homestead_feasibility"}
    headers = bearer_headers(workspace_id, user_id)

    assert client.post("/report-runs", json=payload).status_code == 401
    assert (
        client.post(
            "/report-runs",
            json=payload,
            headers={"Authorization": "Bearer invalid"},
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/report-runs",
            json=payload,
            headers={
                **headers,
                "X-Workspace-Id": workspace_id,
                "X-User-Id": user_id,
            },
        ).status_code
        == 202
    )
    assert (
        client.post(
            "/report-runs",
            json=payload,
            headers={**headers, "X-Workspace-Id": str(uuid4())},
        ).status_code
        == 403
    )


@pytest.mark.parametrize("job_status", [JobStatus.QUEUED, JobStatus.FAILED])
def test_signed_report_job_status_reads_do_not_cross_workspace(
    job_status: JobStatus,
) -> None:
    app = create_app(
        settings=Settings(
            REPORT_AUTH_MODE="signed_token",
            REPORT_IDENTITY_TOKEN_SECRET=SECRET,
        )
    )
    client = TestClient(app)
    workspace_a = str(uuid4())
    workspace_b = str(uuid4())
    user_id = str(uuid4())
    headers_a = bearer_headers(workspace_a, user_id)
    area_id = create_area(client, headers_a)
    services = cast(ApiServices, app.state.services)
    job = services.async_report_jobs.create(
        area_id=UUID(area_id),
        intent_code=IntentCode.RURAL_LAND_PURCHASE,
        workspace_id=UUID(workspace_a),
        requested_by=UUID(user_id),
    )
    if job_status == JobStatus.FAILED:
        services.async_report_jobs.mark_failed(
            job.report_run_id,
            error_msg="fixture failure",
        )

    response = client.get(
        f"/report-runs/{job.report_run_id}",
        headers=bearer_headers(workspace_b, user_id),
    )

    assert response.status_code == 404


def test_signed_report_list_filters_to_authenticated_workspace() -> None:
    app = create_app(
        settings=Settings(
            REPORT_AUTH_MODE="signed_token",
            REPORT_IDENTITY_TOKEN_SECRET=SECRET,
        )
    )
    client = TestClient(app)
    workspace_a = str(uuid4())
    workspace_b = str(uuid4())
    user_id = str(uuid4())
    headers_a = bearer_headers(workspace_a, user_id)
    headers_b = bearer_headers(workspace_b, user_id)
    area_a = create_area(client, headers_a)
    area_b = create_area(client, headers_b)
    services = cast(ApiServices, app.state.services)
    job_a = services.async_report_jobs.create(
        area_id=UUID(area_a),
        intent_code=IntentCode.RURAL_LAND_PURCHASE,
        workspace_id=UUID(workspace_a),
        requested_by=UUID(user_id),
    )
    job_b = services.async_report_jobs.create(
        area_id=UUID(area_b),
        intent_code=IntentCode.HOMESTEAD_FEASIBILITY,
        workspace_id=UUID(workspace_b),
        requested_by=UUID(user_id),
    )

    response = client.get("/report-runs", headers=headers_a)

    assert response.status_code == 200
    listed_ids = {item["report_run_id"] for item in response.json()}
    assert str(job_a.report_run_id) in listed_ids
    assert str(job_b.report_run_id) not in listed_ids


@pytest.mark.parametrize("secret", [None, "short"])
def test_signed_report_identity_token_fails_closed_without_valid_secret(
    secret: str | None,
) -> None:
    client = signed_token_client(secret=secret)

    response = client.post(
        "/report-runs",
        json={"area_id": str(uuid4()), "intent_code": "homestead_feasibility"},
        headers={"Authorization": "Bearer token"},
    )

    assert response.status_code == 500


def test_report_identity_token_verifies_signature_and_expiration() -> None:
    workspace_id = uuid4()
    user_id = uuid4()
    issued_at = datetime(2026, 1, 1, tzinfo=UTC)
    token = create_report_identity_token(
        workspace_id=workspace_id,
        user_id=user_id,
        secret=SECRET,
        expires_in=timedelta(minutes=1),
        issued_at=issued_at,
    )

    claims = verify_report_identity_token(
        token,
        secret=SECRET,
        now=issued_at + timedelta(seconds=30),
    )

    assert claims.workspace_id == workspace_id
    assert claims.user_id == user_id
    with pytest.raises(ValueError, match="signature"):
        verify_report_identity_token(f"{token}x", secret=SECRET)
    with pytest.raises(ValueError, match="expired"):
        verify_report_identity_token(
            token,
            secret=SECRET,
            now=issued_at + timedelta(minutes=2),
        )
    missing_exp_token = signed_test_token(
        {
            "workspace_id": str(workspace_id),
            "user_id": str(user_id),
            "iat": int(issued_at.timestamp()),
        }
    )
    with pytest.raises(ValueError, match="expiration is required"):
        verify_report_identity_token(missing_exp_token, secret=SECRET)
    with pytest.raises(ValueError, match="expiration must be in the future"):
        create_report_identity_token(
            workspace_id=workspace_id,
            user_id=user_id,
            secret=SECRET,
            expires_in=timedelta(seconds=0),
        )


@pytest.mark.parametrize(
    "route_fn",
    [
        lambda rid: f"/report-runs/{rid}/dossier",
        lambda rid: f"/report-runs/{rid}/lineage",
        lambda rid: f"/report-runs/compare?ids={rid},{rid}",
        lambda rid: f"/report-runs/{rid}/diff?base_id={rid}",
    ],
    ids=["dossier", "lineage", "compare", "diff"],
)
def test_report_adjacent_routes_fail_closed_for_wrong_workspace(
    route_fn: object,
) -> None:
    client = signed_token_client()
    workspace_a = str(uuid4())
    workspace_b = str(uuid4())
    user_id = str(uuid4())

    area_id = create_area(client, bearer_headers(workspace_a, user_id))
    run_resp = client.post(
        "/report-runs",
        json={"area_id": area_id, "intent_code": "rural_land_purchase"},
        headers=bearer_headers(workspace_a, user_id),
    )
    assert run_resp.status_code == 202
    report_run_id = run_resp.json()["report_run_id"]

    url = route_fn(report_run_id)  # type: ignore[operator]
    response = client.get(url, headers=bearer_headers(workspace_b, user_id))
    assert response.status_code == 404


def signed_test_token(payload: dict[str, object]) -> str:
    payload_segment = base64url_encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    signed_part = f"land-dd-report-v1.{payload_segment}"
    signature = base64url_encode(
        hmac.new(SECRET.encode("utf-8"), signed_part.encode("utf-8"), hashlib.sha256).digest()
    )
    return f"{signed_part}.{signature}"


def base64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")
