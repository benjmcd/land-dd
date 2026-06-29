from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, cast

import pytest
import yaml
from fastapi.testclient import TestClient

from app.api import ui as ui_module
from app.expansion_readiness import (
    ExpansionReadinessError,
    load_expansion_readiness,
    parse_expansion_readiness,
)
from app.main import create_app

REPO_ROOT = Path(__file__).resolve().parents[3]


def _catalog() -> dict[str, Any]:
    payload = yaml.safe_load(
        (REPO_ROOT / "config" / "checklist_dry_run.yaml").read_text(encoding="utf-8")
    )
    assert isinstance(payload, dict)
    return cast(dict[str, Any], payload)


def _checklists(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    return cast(list[dict[str, Any]], catalog["checklists"])


def _dry_run_items(checklist: dict[str, Any]) -> list[dict[str, Any]]:
    return cast(list[dict[str, Any]], checklist["dry_run"])


def test_expansion_readiness_parser_counts_checklists_and_fail_closed_statuses() -> None:
    readiness = load_expansion_readiness(REPO_ROOT)

    assert readiness.schema_version == "checklist_dry_run_v1"
    assert readiness.status == "repo_local_validate_only"
    assert readiness.validation == "scripts/run_checklist_dry_run_check.ps1"
    assert readiness.candidate.status == "hypothetical_not_selected"
    assert readiness.candidate.approvals == {
        "ds017_unblocked": False,
        "hosted_production_ready": False,
        "new_geography_selected": False,
        "new_rulepack_approved": False,
        "new_source_approved": False,
    }
    assert readiness.limits["validate_only_catalog"] is True
    assert readiness.limits["selects_new_geography"] is False
    assert {checklist.checklist_id for checklist in readiness.checklists} == {
        "jurisdiction_readiness",
        "rulepack_readiness",
    }
    for status_name in (
        "repo_confirmed",
        "missing_candidate_decision",
        "missing_repo_evidence",
        "blocked_external_authority",
        "not_applicable_existing_scope",
    ):
        assert readiness.status_counts[status_name] > 0


def test_parser_rejects_flipped_validate_only_limits() -> None:
    catalog = deepcopy(_catalog())
    limits = cast(dict[str, bool], catalog["limits"])
    limits["selects_new_geography"] = True

    with pytest.raises(ExpansionReadinessError, match="limits changed"):
        parse_expansion_readiness(catalog, root=REPO_ROOT)


def test_parser_rejects_missing_dry_run_item() -> None:
    catalog = deepcopy(_catalog())
    first_checklist = _checklists(catalog)[0]
    _dry_run_items(first_checklist).pop()

    with pytest.raises(ExpansionReadinessError, match="dry-run coverage mismatch"):
        parse_expansion_readiness(catalog, root=REPO_ROOT)


def test_parser_rejects_stale_repo_evidence_assertion() -> None:
    catalog = deepcopy(_catalog())
    for checklist in _checklists(catalog):
        for item in _dry_run_items(checklist):
            if item["status"] == "repo_confirmed":
                assertions = cast(list[dict[str, str]], item["evidence_assertions"])
                assertions[0]["contains"] = "definitely-not-current-repo-evidence"
                with pytest.raises(ExpansionReadinessError, match="assertion missing text"):
                    parse_expansion_readiness(catalog, root=REPO_ROOT)
                return
    pytest.fail("fixture catalog did not contain a repo_confirmed item")


def test_parser_rejects_empty_repo_evidence_assertion() -> None:
    catalog = deepcopy(_catalog())
    for checklist in _checklists(catalog):
        for item in _dry_run_items(checklist):
            if item["status"] == "repo_confirmed":
                assertions = cast(list[dict[str, str]], item["evidence_assertions"])
                # An empty assertion string would make the later containment check
                # vacuously pass, so the parser must reject it before reading.
                assertions[0]["contains"] = ""
                with pytest.raises(
                    ExpansionReadinessError, match="contains must be a non-empty string"
                ):
                    parse_expansion_readiness(catalog, root=REPO_ROOT)
                return
    pytest.fail("fixture catalog did not contain a repo_confirmed item")


def test_ui_expansion_route_returns_503_when_loader_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _raise_loader() -> None:
        raise ExpansionReadinessError("test expansion readiness failure")

    monkeypatch.setattr(ui_module, "load_expansion_readiness", _raise_loader)
    client = TestClient(create_app())

    response = client.get("/ui/expansion")

    assert response.status_code == 503
    assert (
        "Expansion readiness unavailable from repo-owned checklist dry-run artifacts"
        in response.text
    )
    assert "test expansion readiness failure" in response.text
    assert "Traceback" not in response.text


def test_ui_expansion_route_renders_checklist_dry_run_evidence_and_boundaries() -> None:
    client = TestClient(create_app())

    response = client.get("/ui/expansion")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert 'name="viewport"' in response.text
    assert "Expansion Readiness" in response.text
    assert "checklist_dry_run_v1" in response.text
    assert "repo_local_validate_only" in response.text
    assert "hypothetical_next_county_existing_homestead_mvp" in response.text
    assert "hypothetical_not_selected" in response.text
    assert "Checklist Status Counts" in response.text
    assert "Approval Flags" in response.text
    assert "Validate-Only Limits" in response.text
    assert "Checklist Coverage" in response.text
    assert "Checklist Items and Next Actions" in response.text
    assert "jurisdiction_readiness" in response.text
    assert "rulepack_readiness" in response.text
    assert "docs/checklists/jurisdiction_readiness.md" in response.text
    assert "docs/checklists/rulepack_readiness.md" in response.text
    assert "config/ruleset_homestead_mvp.yaml" in response.text
    assert "professional wetland delineation requirement confirmed" in response.text
    assert "repo_confirmed" in response.text
    assert "missing_candidate_decision" in response.text
    assert "missing_repo_evidence" in response.text
    assert "blocked_external_authority" in response.text
    assert "not_applicable_existing_scope" in response.text
    assert "new_geography_selected" in response.text
    assert "false" in response.text
    assert "validate_only_catalog" in response.text
    assert "true" in response.text
    assert "does not approve a new geography" in response.text
    assert "does not approve a new rulepack" in response.text
    assert "does not approve a new source" in response.text
    assert "does not unblock DS-017" in response.text
    assert "does not run live connectors" in response.text
    assert "hosted production readiness" in response.text
    assert "legal review" in response.text
    assert "full identity/RBAC" in response.text


def test_ui_navigation_links_to_expansion_readiness() -> None:
    client = TestClient(create_app())

    # The /ui/readiness and /ui/coverage hub pages are not part of this harvest;
    # navigation is asserted against the readiness pages that exist on this branch.
    home = client.get("/ui/")
    dossier = client.get("/ui/dossier-readiness")
    raw_data = client.get("/ui/raw-data")

    assert home.status_code == 200
    assert dossier.status_code == 200
    assert raw_data.status_code == 200
    assert 'href="/ui/expansion"' in home.text
    assert 'href="/ui/expansion"' in dossier.text
    assert 'href="/ui/expansion"' in raw_data.text
