from __future__ import annotations

import csv
from copy import deepcopy
from datetime import date
from pathlib import Path
from typing import Any, cast

import pytest
import yaml
from fastapi.testclient import TestClient

from app.api import ui as ui_module
from app.main import create_app
from app.source_provenance import (
    SourceProvenanceError,
    load_source_provenance,
    parse_source_provenance,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
AS_OF = date(2026, 6, 20)
EXPECTED_COUNTIES = {"buncombe_nc", "chatham_nc", "brunswick_nc"}
EXPECTED_SELECTED_SOURCES = {"DS-010", "DS-011", "DS-023"}


def _catalog() -> dict[str, Any]:
    payload = yaml.safe_load(
        (REPO_ROOT / "config" / "private_mvp_beta_readiness.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert isinstance(payload, dict)
    return cast(dict[str, Any], payload)


def _registry_rows() -> list[dict[str, str]]:
    with (REPO_ROOT / "registers" / "data_source_registry.csv").open(
        newline="",
        encoding="utf-8",
    ) as csv_file:
        return [dict(row) for row in csv.DictReader(csv_file)]


def test_source_provenance_parser_composes_selected_county_contract() -> None:
    readiness = load_source_provenance(REPO_ROOT, as_of=AS_OF)

    assert readiness.schema_version == "private_mvp_beta_readiness_v1"
    assert readiness.must_source_count == 8
    assert readiness.must_ready_count == 7
    assert readiness.must_blocked_source_ids == ("DS-017",)
    assert readiness.selected_source_ids == tuple(sorted(EXPECTED_SELECTED_SOURCES))
    assert {county.county_key for county in readiness.counties} == EXPECTED_COUNTIES
    assert readiness.ds017_blocker is not None
    assert readiness.ds017_blocker.name == "Commercial parcel vendor"
    assert readiness.ds017_blocker.connector_ready is False
    assert "license_status" in readiness.ds017_blocker.blocked_fields
    assert "connector_implemented" in readiness.ds017_blocker.blocked_fields

    buncombe = next(
        county for county in readiness.counties if county.county_key == "buncombe_nc"
    )
    assert buncombe.county_label == "Buncombe County, NC"
    assert buncombe.source_manifest == "docs/geographies/nc/buncombe/source_manifest.md"
    assert {source.source_registry_id for source in buncombe.sources} == (
        EXPECTED_SELECTED_SOURCES
    )
    buncombe_ds023 = next(
        source for source in buncombe.sources if source.source_registry_id == "DS-023"
    )
    assert buncombe_ds023.out_of_scope is True
    assert buncombe_ds023.connector_names == ()
    assert buncombe_ds023.dataset_expectation == "not_required_out_of_scope"
    assert "Buncombe zoning" in buncombe_ds023.out_of_scope_reason

    chatham = next(
        county for county in readiness.counties if county.county_key == "chatham_nc"
    )
    chatham_ds023 = next(
        source for source in chatham.sources if source.source_registry_id == "DS-023"
    )
    assert chatham_ds023.connector_names == ("chatham_zoning_udo_recorded",)
    assert chatham_ds023.dataset_expectation == "recorded_fixture_dataset"
    assert chatham_ds023.version_expectation == "recorded_fixture_version"
    assert chatham_ds023.retrieval_expectation == "fixture_retrieval_metadata"


def test_source_provenance_parser_fails_closed_on_ds017_catalog_drift() -> None:
    catalog = deepcopy(_catalog())
    chatham_sources = catalog["selected_county_source_provenance_scope"]["counties"][
        "chatham_nc"
    ]["sources"]
    chatham_sources["DS-017"] = {
        "source_registry_id": "DS-017",
        "connector_names": [],
        "dataset_expectation": "county_source_dataset",
        "version_expectation": "source_version_or_access_date",
        "retrieval_expectation": "connector_retrieval_metadata",
        "out_of_scope": False,
    }

    with pytest.raises(SourceProvenanceError, match="DS-017"):
        parse_source_provenance(
            catalog,
            _registry_rows(),
            root=REPO_ROOT,
            as_of=AS_OF,
        )


def test_source_provenance_loader_uses_repo_relative_error_paths(
    tmp_path: Path,
) -> None:
    with pytest.raises(SourceProvenanceError) as exc_info:
        load_source_provenance(tmp_path, as_of=AS_OF)

    message = str(exc_info.value)
    assert "config/private_mvp_beta_readiness.yaml" in message
    assert str(tmp_path) not in message


def test_ui_source_provenance_route_returns_503_when_loader_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _raise_loader() -> None:
        raise SourceProvenanceError("test source provenance failure")

    monkeypatch.setattr(ui_module, "load_source_provenance", _raise_loader)
    client = TestClient(create_app())

    response = client.get("/ui/source-provenance")

    assert response.status_code == 503
    assert "Source provenance unavailable from repo-owned artifacts" in response.text
    assert "test source provenance failure" in response.text
    assert "Traceback" not in response.text


def test_ui_source_provenance_route_renders_catalog_and_boundaries() -> None:
    client = TestClient(create_app())

    response = client.get("/ui/source-provenance")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert 'name="viewport"' in response.text
    assert "Source Provenance" in response.text
    for text in (
        "private_mvp_beta_readiness_v1",
        "Buncombe County, NC",
        "Chatham County, NC",
        "Brunswick County, NC",
        "DS-010",
        "DS-011",
        "DS-023",
        "DS-017",
        "Commercial parcel vendor",
        "source_version_or_access_date",
        "static_sentinel_version",
        "recorded_fixture_version",
        "connector_retrieval_metadata",
        "source_failure_metadata",
        "fixture_retrieval_metadata",
        "not_required_out_of_scope",
        "chatham_zoning_udo_recorded",
        "brunswick_zoning_udo_recorded",
        "license_status",
        "connector_implemented",
        "does not run connectors",
        "does not seed runtime provenance",
        "does not relabel fixture evidence as live data",
        "does not approve DS-017",
        "does not expand county coverage",
        "does not start Bologna",
        "does not prove hosted source authority",
    ):
        assert text in response.text


def test_current_ui_navigation_links_to_source_provenance() -> None:
    client = TestClient(create_app())

    for path in ("/ui/", "/ui/raw-data", "/ui/deployment-readiness"):
        response = client.get(path)

        assert response.status_code == 200
        assert 'href="/ui/source-provenance"' in response.text
