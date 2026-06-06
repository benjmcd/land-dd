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
from fastapi.testclient import TestClient

from app.api.report_auth import create_report_identity_token, verify_report_identity_token
from app.core.config import Settings
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

    assert response.status_code == 201
    report = response.json()
    assert report["workspace_id"] == workspace_id
    assert report["requested_by"] == user_id
    assert (
        client.get(
            f"/report-runs/{report['report_run_id']}",
            headers=bearer_headers(str(uuid4()), user_id),
        ).status_code
        == 404
    )


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
        == 201
    )
    assert (
        client.post(
            "/report-runs",
            json=payload,
            headers={**headers, "X-Workspace-Id": str(uuid4())},
        ).status_code
        == 403
    )


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
    assert run_resp.status_code == 201
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
