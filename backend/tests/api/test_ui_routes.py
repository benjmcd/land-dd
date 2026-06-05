from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import create_app

client = TestClient(create_app())


def test_ui_index_returns_200_html() -> None:
    response = client.get("/ui/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Land Diligence" in response.text


def test_ui_index_has_intent_form() -> None:
    response = client.get("/ui/")
    assert response.status_code == 200
    assert "rural_land_purchase" in response.text
    assert "homestead_feasibility" in response.text


def test_ui_report_run_returns_404_page_for_unknown_id() -> None:
    response = client.get(f"/ui/report-runs/{uuid4()}")
    assert response.status_code == 200  # We return 200 HTML with "not found" message
    assert "text/html" in response.headers["content-type"]
    assert "Not Found" in response.text


def test_ui_report_run_invalid_uuid_returns_422() -> None:
    response = client.get("/ui/report-runs/not-a-uuid")
    assert response.status_code == 422
