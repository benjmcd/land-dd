from __future__ import annotations

import importlib
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.api import ui as ui_module
from app.main import create_app

REPO_ROOT = Path(__file__).resolve().parents[3]

EXPECTED_AUTHORITY_TITLES = {
    "DS-017 Commercial Parcel Vendor Authority",
    "Hosted Platform Authority",
    "Secrets Authority",
    "Identity And RBAC Authority",
    "Image Publication Authority",
    "Billing And Cost Authority",
    "Alerting Authority",
    "Production Workload And Retention Authority",
    "Bologna Recorded-Source Pilot Authority",
}
EXPECTED_EXTERNAL_AREAS = {
    "Hosted deployment",
    "Secret management",
    "Identity/RBAC",
    "DS-017 commercial parcel vendor",
    "Registry/image publication",
    "Hosted alerting/on-call",
    "Billing/cost approval",
    "Hosted workload/SLO",
}

production_authority_module: ModuleType | None
try:
    production_authority_module = importlib.import_module("app.production_authority")
except ModuleNotFoundError:
    production_authority_module = None


def _helper_attr(name: str) -> Any:
    if production_authority_module is None:
        pytest.skip("app.production_authority helper is not implemented yet")
    return getattr(production_authority_module, name)


def _packet_text() -> str:
    return (REPO_ROOT / "state" / "PRODUCTION_AUTHORITY_PACKET.md").read_text(
        encoding="utf-8",
    )


def _split_text() -> str:
    return (REPO_ROOT / "state" / "POST_RC_AUTHORITY_SPLIT.md").read_text(
        encoding="utf-8",
    )


def test_production_authority_parser_extracts_required_authority_sections() -> None:
    load_production_authority = _helper_attr("load_production_authority")

    readiness = load_production_authority(REPO_ROOT)

    titles = {requirement.title for requirement in readiness.requirements}
    assert titles == EXPECTED_AUTHORITY_TITLES
    external_areas = {blocker.area for blocker in readiness.external_blockers}
    assert external_areas == EXPECTED_EXTERNAL_AREAS
    assert readiness.packet_path == "state/PRODUCTION_AUTHORITY_PACKET.md"
    assert readiness.split_path == "state/POST_RC_AUTHORITY_SPLIT.md"
    assert "Do not implement a DS-017 connector" in readiness.fail_closed_rule
    assert any("DS-017 has no vendor" in blocker for blocker in readiness.open_blockers)
    assert any(
        "source review" in lane
        for requirement in readiness.requirements
        if requirement.title == "DS-017 Commercial Parcel Vendor Authority"
        for lane in requirement.unlocked_lane
    )


def test_production_authority_parser_fails_closed_when_section_missing() -> None:
    parse_production_authority = _helper_attr("parse_production_authority")
    authority_error = _helper_attr("ProductionAuthorityError")
    packet = _packet_text().replace("## Hosted Platform Authority", "## Hosted Platform")

    with pytest.raises(authority_error, match="Hosted Platform Authority"):
        parse_production_authority(packet, _split_text())


def test_production_authority_parser_fails_closed_when_decisions_missing() -> None:
    parse_production_authority = _helper_attr("parse_production_authority")
    authority_error = _helper_attr("ProductionAuthorityError")
    packet = _packet_text().replace("- External decisions required:", "- Decisions:")

    with pytest.raises(authority_error, match="External decisions"):
        parse_production_authority(packet, _split_text())


def test_production_authority_parser_fails_closed_when_external_table_drifts() -> None:
    parse_production_authority = _helper_attr("parse_production_authority")
    authority_error = _helper_attr("ProductionAuthorityError")
    split = _split_text().replace("DS-017 commercial parcel vendor", "DS-017 vendor")

    with pytest.raises(authority_error, match="external authority blocker"):
        parse_production_authority(_packet_text(), split)


def test_production_authority_preserves_wrapped_open_blocker_text() -> None:
    load_production_authority = _helper_attr("load_production_authority")

    readiness = load_production_authority(REPO_ROOT)

    # The Bologna and secret/RBAC blockers wrap onto indented continuation lines
    # in the packet; the parser must fold them so operator-facing text is whole.
    bologna = next(
        (blocker for blocker in readiness.open_blockers if blocker.startswith("Bologna has no")),
        None,
    )
    assert bologna is not None
    assert "DB-backed pilot proof" in bologna  # tail of a three-line wrapped bullet
    assert any(
        "hosted log retention remain blocked" in blocker
        for blocker in readiness.open_blockers
    )


def test_production_authority_fails_closed_on_unlisted_authority_section(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if production_authority_module is None:
        pytest.skip("app.production_authority helper is not implemented yet")
    parse_production_authority = _helper_attr("parse_production_authority")
    authority_error = _helper_attr("ProductionAuthorityError")
    # Drop Bologna from the expected set while the packet still declares it as an
    # authority section; the coverage guard must fail closed, not silently omit it.
    reduced = tuple(
        title
        for title in production_authority_module.EXPECTED_AUTHORITY_TITLES
        if title != "Bologna Recorded-Source Pilot Authority"
    )
    monkeypatch.setattr(production_authority_module, "EXPECTED_AUTHORITY_TITLES", reduced)

    with pytest.raises(authority_error, match="authority section coverage mismatch"):
        parse_production_authority(_packet_text(), _split_text())


def test_ui_production_authority_route_returns_503_when_loader_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if production_authority_module is not None:
        authority_error = production_authority_module.ProductionAuthorityError
    else:
        authority_error = RuntimeError

    def _raise_loader() -> None:
        raise authority_error("test production authority failure")

    monkeypatch.setattr(ui_module, "load_production_authority", _raise_loader, raising=False)
    client = TestClient(create_app())

    response = client.get("/ui/production-authority")

    assert response.status_code == 503
    assert "Production authority unavailable from repo-owned authority artifacts" in response.text
    assert "test production authority failure" in response.text
    assert "Traceback" not in response.text


def test_ui_production_authority_route_renders_authority_requirements() -> None:
    client = TestClient(create_app())

    response = client.get("/ui/production-authority")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert 'name="viewport"' in response.text
    assert "Production Authority" in response.text
    for text in (
        "state/PRODUCTION_AUTHORITY_PACKET.md",
        "state/POST_RC_AUTHORITY_SPLIT.md",
        "External Authority Blockers",
        "Authority Requirements",
        "Repo-Local Candidates",
        "Open Production Blockers",
        "DS-017 Commercial Parcel Vendor Authority",
        "Hosted Platform Authority",
        "Secrets Authority",
        "Identity And RBAC Authority",
        "Image Publication Authority",
        "Billing And Cost Authority",
        "Alerting Authority",
        "Production Workload And Retention Authority",
        "Bologna Recorded-Source Pilot Authority",
        "DS-017 has no vendor",
        "hosted platform",
        "secret manager",
        "IdP/OAuth/OIDC",
        "registry repository",
        "billing owner",
        "alert manager",
        "hosted load proof",
        "Local production-authority view only",
        "does not approve DS-017",
        "does not provision hosted deployment",
        "does not write secrets",
        "does not publish images",
        "does not create accounts",
        "does not approve billing",
        "does not mutate state",
    ):
        assert text in response.text


def test_ui_navigation_links_to_production_authority() -> None:
    client = TestClient(create_app())

    # Routes registered on this branch's UI router. The readiness/coverage/
    # release-readiness hub pages are not part of this harvest, so navigation
    # is asserted against the pages that exist here.
    responses = [
        client.get("/ui/"),
        client.get("/ui/expansion"),
        client.get("/ui/dossier-readiness"),
        client.get("/ui/deployment-readiness"),
        client.get("/ui/raw-data"),
    ]

    for response in responses:
        assert response.status_code == 200
        assert 'href="/ui/production-authority"' in response.text
