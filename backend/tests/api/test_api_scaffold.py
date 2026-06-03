from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app


def test_api_scaffold_exposes_health_endpoint() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200

