from __future__ import annotations

import inspect
from email.message import Message
from typing import Any
from urllib.error import HTTPError
from uuid import UUID, uuid4

import pytest

import app.connectors.ssurgo as ssurgo_module
from app.connectors.evidence_ingestion import ConnectorEvidenceIngestionAdapter
from app.connectors.license_guard import ConnectorLicenseBlockedError
from app.connectors.observability import ConnectorEventType
from app.connectors.retrieval_provenance import ConnectorRetrievalProvenanceAdapter
from app.connectors.ssurgo import (
    SSURGO_CAVEAT,
    SSURGO_CONNECTOR_NAME,
    SSURGO_MAX_ROWS,
    SSURGO_METHOD_CODE,
    SSURGO_POST_REST_URL,
    SsurgoBbox,
    SsurgoConnector,
    SsurgoConnectorError,
)
from app.domain.enums import ConfidenceBand, EvidenceType
from app.domain.evidence_contracts import EvidenceContract
from app.domain.source_contracts import (
    SourceContract,
    SourceRetrievalRunContract,
    SourceRetrievalStatus,
)
from app.evidence_ledger.evidence_repo import InMemoryEvidenceRepository
from app.evidence_ledger.service import EvidenceService


def _source(*, license_status: str = "approved-with-restrictions") -> SourceContract:
    return SourceContract(
        name="USDA Web Soil Survey/SSURGO",
        organization="USDA NRCS",
        source_type="Public official",
        domain="Soils",
        geographic_scope="US",
        license_status=license_status,
        commercial_use_status="approved-with-restrictions",
        redistribution_status="approved-with-restrictions",
        attribution_required=True,
        cache_allowed="approved-with-restrictions",
        export_allowed="approved-with-restrictions",
        ai_use_allowed="restricted",
        raw_data_allowed="approved-with-restrictions",
        freshness_class="current-effective",
        last_checked_at="2026-06-05",
        review_owner="operator",
        review_status="approved-with-restrictions",
        metadata={"source_registry_id": "DS-003"},
    )


def _bbox() -> SsurgoBbox:
    return SsurgoBbox(xmin=-77.10, ymin=38.80, xmax=-77.09, ymax=38.81)


def _table() -> dict[str, object]:
    return {
        "Table": [
            [
                "mukey",
                "musym",
                "muname",
                "cokey",
                "compname",
                "comppct_r",
                "majcompflag",
                "hydricrating",
                "drainagecl",
                "hydgrp",
                "slope_r",
            ],
            [
                "1912968",
                "30A",
                "Codorus and Hatboro soils, 0 to 2 percent slopes, occasionally flooded",
                "27342553",
                "Codorus",
                "55",
                "Yes",
                "No",
                "Somewhat poorly drained",
                "B/D",
                "1",
            ],
        ]
    }


class RecordingRetrievalPort:
    def __init__(self) -> None:
        self.recorded_runs: list[SourceRetrievalRunContract] = []

    def retrieval_run_exists(self, _ingest_run_id: UUID) -> bool:
        return False

    def record_retrieval_run(
        self,
        retrieval_run: SourceRetrievalRunContract,
    ) -> SourceRetrievalRunContract:
        self.recorded_runs.append(retrieval_run)
        return retrieval_run


class RecordingEvidencePort:
    def __init__(self) -> None:
        self.created_observations: list[EvidenceContract] = []

    def create_observation(self, evidence: EvidenceContract) -> EvidenceContract:
        self.created_observations.append(evidence)
        return evidence

    def create_source_failure(
        self,
        *,
        evidence_id: UUID | None = None,
        area_id: UUID,
        source_id: UUID,
        method_code: str,
        caveat: str,
        evidence_code: str = "SOURCE_FAILURE",
        domain: str = "unknown",
        observation: str | None = None,
        observed_value: dict[str, object] | None = None,
        source_ingest_run_id: UUID | None = None,
    ) -> EvidenceContract:
        raise AssertionError("success path should not create source failure")

    def evidence_exists(self, _evidence_id: UUID) -> bool:
        return False

    def list_by_area(self, _area_id: UUID) -> list[EvidenceContract]:
        return []


class StubSourceChecker:
    def __init__(self, registered: set[UUID]) -> None:
        self._registered = registered

    def source_is_registered(self, source_id: UUID) -> bool:
        return source_id in self._registered

    def source_production_use_allowed(self, source_id: UUID) -> bool:
        return source_id in self._registered


class StubAreaChecker:
    def __init__(self, registered: set[UUID]) -> None:
        self._registered = registered

    def area_is_registered(self, area_id: UUID) -> bool:
        return area_id in self._registered


def test_success_query_builds_bounded_ssurgo_request_and_evidence() -> None:
    queries: list[str] = []
    source = _source()

    def fetch_json(query: str, timeout_seconds: float) -> dict[str, object]:
        queries.append(query)
        assert timeout_seconds == 30.0
        return _table()

    area_id = uuid4()
    result = SsurgoConnector(source=source, fetch_json=fetch_json).query_bbox(
        area_id=area_id,
        bbox=_bbox(),
    )

    assert queries
    assert "SDA_Get_Mukey_from_intersection_with_WktWgs84" in queries[0]
    assert "join mapunit mu" in queries[0]
    assert "left join component co" in queries[0]
    assert f"select top {SSURGO_MAX_ROWS}" in queries[0]
    assert result.request_url == SSURGO_POST_REST_URL
    assert result.request_query == queries[0]

    assert result.retrieval_run.connector_name == SSURGO_CONNECTOR_NAME
    assert result.retrieval_run.status == SourceRetrievalStatus.SUCCEEDED
    assert result.retrieval_run.row_count == 1
    assert result.retrieval_run.error_count == 0
    assert result.retrieval_run.metrics["source_registry_id"] == "DS-003"
    assert result.retrieval_run.metrics["format"] == "JSON+COLUMNNAME"

    evidence = result.evidence_inputs[0]
    assert evidence.area_id == area_id
    assert evidence.source_id == source.source_id
    assert evidence.evidence_type == EvidenceType.SPATIAL_INTERSECTION
    assert evidence.domain == "soil_septic"
    assert evidence.method_code == SSURGO_METHOD_CODE
    assert evidence.confidence == ConfidenceBand.MEDIUM
    assert evidence.caveat == SSURGO_CAVEAT
    assert evidence.source_ingest_run_id == result.retrieval_run.ingest_run_id
    assert evidence.source_date == evidence.observed_at.date().isoformat()
    assert evidence.geometry_geojson is None
    assert evidence.spatial_precision_meters is None
    assert evidence.observed_value["intersects_soil_mapunit"] is True
    assert evidence.observed_value["soil_mapunit_key"] == "1912968"
    assert evidence.observed_value["soil_mapunit_symbol"] == "30A"
    assert evidence.observed_value["soil_component_name"] == "Codorus"
    assert evidence.observed_value["soil_component_percent"] == 55.0
    assert evidence.observed_value["soil_major_component"] is True
    assert evidence.observed_value["hydric_rating"] == "No"
    assert evidence.observed_value["drainage_class"] == "Somewhat poorly drained"
    assert evidence.observed_value["hydrologic_group"] == "B/D"
    assert evidence.observed_value["slope_percent"] == 1.0

    assert len(result.observability_log.events_of_type(ConnectorEventType.run_started)) == 1
    assert len(result.observability_log.events_of_type(ConnectorEventType.evidence_stored)) == 1
    assert len(result.observability_log.events_of_type(ConnectorEventType.run_succeeded)) == 1


def test_success_evidence_ingests_through_real_evidence_service() -> None:
    source = _source()
    area_id = uuid4()

    def fetch_json(_query: str, _timeout_seconds: float) -> dict[str, object]:
        return _table()

    result = SsurgoConnector(source=source, fetch_json=fetch_json).query_bbox(
        area_id=area_id,
        bbox=_bbox(),
    )
    service = EvidenceService(
        InMemoryEvidenceRepository(),
        StubSourceChecker({source.source_id}),
        StubAreaChecker({area_id}),
    )

    created = service.create_observation(result.evidence_inputs[0])

    assert created.evidence_id == result.evidence_inputs[0].evidence_id
    assert created.observed_value["intersects_soil_mapunit"] is True


def test_null_slope_and_component_percent_are_excluded_from_observed_value() -> None:
    """Rows where slope_r or comppct_r are absent/null must not set those keys.

    The payload validator rejects None for numeric fields when the key is present,
    so the connector must omit the key entirely rather than setting it to None.
    """
    source = _source()
    area_id = uuid4()

    def fetch_json(_query: str, _timeout_seconds: float) -> dict[str, object]:
        return {
            "Table": [
                [
                    "mukey",
                    "musym",
                    "muname",
                    "cokey",
                    "compname",
                    "comppct_r",
                    "majcompflag",
                    "hydricrating",
                    "drainagecl",
                    "hydgrp",
                    "slope_r",
                ],
                # slope_r and comppct_r are empty strings (as SSURGO sometimes returns)
                [
                    "9999999",
                    "XX",
                    "Test unit",
                    "12345678",
                    "TestSoil",
                    "",
                    "Yes",
                    "No",
                    "Well drained",
                    "A",
                    "",
                ],
            ]
        }

    result = SsurgoConnector(source=source, fetch_json=fetch_json).query_bbox(
        area_id=area_id,
        bbox=_bbox(),
    )

    assert len(result.evidence_inputs) == 1
    ev = result.evidence_inputs[0]
    assert "slope_percent" not in ev.observed_value
    assert "soil_component_percent" not in ev.observed_value

    # Must also ingest successfully through the real evidence service (no validation error)
    service = EvidenceService(
        InMemoryEvidenceRepository(),
        StubSourceChecker({source.source_id}),
        StubAreaChecker({area_id}),
    )
    created = service.create_observation(ev)
    assert created.evidence_id == ev.evidence_id


def test_success_result_uses_existing_provenance_and_evidence_adapters() -> None:
    def fetch_json(_query: str, _timeout_seconds: float) -> dict[str, object]:
        return _table()

    result = SsurgoConnector(source=_source(), fetch_json=fetch_json).query_bbox(
        area_id=uuid4(),
        bbox=_bbox(),
    )
    retrieval_port = RecordingRetrievalPort()
    evidence_port = RecordingEvidencePort()

    provenance = ConnectorRetrievalProvenanceAdapter(retrieval_port).record(result)
    ingestion = ConnectorEvidenceIngestionAdapter(evidence_port).ingest(result)

    assert provenance.recorded_run == result.retrieval_run
    assert retrieval_port.recorded_runs == [result.retrieval_run]
    assert ingestion.created_evidence == result.evidence_inputs
    assert evidence_port.created_observations == list(result.evidence_inputs)


def test_success_query_is_idempotent_for_same_source_area_and_bbox() -> None:
    source = _source()
    area_id = uuid4()

    def fetch_json(_query: str, _timeout_seconds: float) -> dict[str, object]:
        return _table()

    connector = SsurgoConnector(source=source, fetch_json=fetch_json)
    first = connector.query_bbox(area_id=area_id, bbox=_bbox())
    second = connector.query_bbox(area_id=area_id, bbox=_bbox())

    assert first.retrieval_run.ingest_run_id == second.retrieval_run.ingest_run_id
    assert first.evidence_inputs[0].evidence_id == second.evidence_inputs[0].evidence_id


def test_empty_table_response_emits_source_failure_evidence() -> None:
    def fetch_json(_query: str, _timeout_seconds: float) -> dict[str, object]:
        return {"Table": [["mukey", "musym", "muname"]]}

    result = SsurgoConnector(source=_source(), fetch_json=fetch_json).query_bbox(
        area_id=uuid4(),
        bbox=_bbox(),
    )

    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    assert result.retrieval_run.row_count == 0
    assert result.retrieval_run.error_count == 1
    assert result.retrieval_run.metrics["failure_reason"] == "ssurgo_no_mapunits"

    evidence = result.evidence_inputs[0]
    assert evidence.evidence_type == EvidenceType.SOURCE_FAILURE
    assert evidence.is_source_failure is True
    assert evidence.source_ingest_run_id == result.retrieval_run.ingest_run_id
    assert evidence.confidence == ConfidenceBand.UNKNOWN
    assert evidence.observed_value["attempted_url"] == SSURGO_POST_REST_URL
    assert evidence.observed_value["failure_reason"] == "ssurgo_no_mapunits"
    assert evidence.observed_value["retryable"] is False


def test_service_error_response_emits_retryable_source_failure() -> None:
    def fetch_json(_query: str, _timeout_seconds: float) -> dict[str, object]:
        return {"error": {"message": "Soil Data Mart is down."}}

    result = SsurgoConnector(source=_source(), fetch_json=fetch_json).query_bbox(
        area_id=uuid4(),
        bbox=_bbox(),
    )

    evidence = result.evidence_inputs[0]
    assert result.retrieval_run.metrics["failure_reason"] == "ssurgo_service_error"
    assert evidence.observed_value["error_message"] == "Soil Data Mart is down."
    assert evidence.observed_value["retryable"] is True


def test_http_error_response_emits_status_code_source_failure() -> None:
    def fetch_json(_query: str, _timeout_seconds: float) -> dict[str, object]:
        raise HTTPError(
            url=SSURGO_POST_REST_URL,
            code=500,
            msg="Internal Server Error",
            hdrs=Message(),
            fp=None,
        )

    result = SsurgoConnector(source=_source(), fetch_json=fetch_json).query_bbox(
        area_id=uuid4(),
        bbox=_bbox(),
    )

    evidence = result.evidence_inputs[0]
    assert result.retrieval_run.metrics["failure_reason"] == "ssurgo_http_error"
    assert result.retrieval_run.metrics["status_code"] == 500
    assert evidence.observed_value["failure_reason"] == "ssurgo_http_error"
    assert evidence.observed_value["status_code"] == 500
    assert evidence.observed_value["retryable"] is True


def test_malformed_response_emits_source_failure_instead_of_raising() -> None:
    def fetch_json(_query: str, _timeout_seconds: float) -> dict[str, object]:
        return {"Table": [["mukey"], ["1912968", "extra"]]}

    result = SsurgoConnector(source=_source(), fetch_json=fetch_json).query_bbox(
        area_id=uuid4(),
        bbox=_bbox(),
    )

    evidence = result.evidence_inputs[0]
    assert result.retrieval_run.status == SourceRetrievalStatus.FAILED
    assert result.retrieval_run.metrics["failure_reason"] == "ssurgo_malformed_response"
    assert evidence.evidence_type == EvidenceType.SOURCE_FAILURE
    assert evidence.observed_value["failure_reason"] == "ssurgo_malformed_response"


def test_malformed_row_emits_source_failure_instead_of_raising() -> None:
    def fetch_json(_query: str, _timeout_seconds: float) -> dict[str, object]:
        response = _table()
        response["Table"] = [
            ["mukey", "musym", "muname"],
            [None, "30A", "Codorus and Hatboro soils"],
        ]
        return response

    result = SsurgoConnector(source=_source(), fetch_json=fetch_json).query_bbox(
        area_id=uuid4(),
        bbox=_bbox(),
    )

    evidence = result.evidence_inputs[0]
    assert result.retrieval_run.metrics["failure_reason"] == "ssurgo_malformed_row"
    assert evidence.evidence_type == EvidenceType.SOURCE_FAILURE


def test_license_blocked_before_fetch() -> None:
    called = False

    def fetch_json(_query: str, _timeout_seconds: float) -> dict[str, object]:
        nonlocal called
        called = True
        return _table()

    with pytest.raises(ConnectorLicenseBlockedError):
        SsurgoConnector(
            source=_source(license_status="unknown"),
            fetch_json=fetch_json,
        ).query_bbox(area_id=uuid4(), bbox=_bbox())

    assert called is False


@pytest.mark.parametrize(
    ("bbox_values", "message"),
    [
        ((-77.0, 38.0, -77.1, 38.1), "xmin must be less than xmax"),
        ((-77.1, 38.1, -77.0, 38.0), "ymin must be less than ymax"),
        ((-181.0, 38.0, -180.5, 38.1), "longitude values"),
        ((-77.1, -91.0, -77.0, -90.5), "latitude values"),
        ((-77.5, 38.0, -77.0, 38.1), "longitude span exceeds"),
        ((-77.1, 38.0, -77.0, 38.5), "latitude span exceeds"),
    ],
)
def test_bbox_validation(bbox_values: tuple[float, float, float, float], message: str) -> None:
    with pytest.raises(SsurgoConnectorError, match=message):
        SsurgoBbox(*bbox_values)


def test_max_rows_validation() -> None:
    with pytest.raises(SsurgoConnectorError, match="max_rows"):
        SsurgoConnector(source=_source(), fetch_json=lambda _q, _t: _table()).query_bbox(
            area_id=uuid4(),
            bbox=_bbox(),
            max_rows=SSURGO_MAX_ROWS + 1,
        )


def test_live_fetch_uses_official_sda_post_rest_and_json_columnname(monkeypatch: Any) -> None:
    captured: dict[str, object] = {}

    class FakeResponse:
        def __enter__(self) -> FakeResponse:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self) -> bytes:
            return b'{"Table":[["mukey"],["1912968"]]}'

    def fake_urlopen(request: Any, timeout: float | None = None) -> FakeResponse:
        captured["full_url"] = request.full_url
        captured["data"] = request.data.decode("utf-8")
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(ssurgo_module, "urlopen", fake_urlopen)

    payload = ssurgo_module._fetch_json("select top 1 mukey from mapunit", 12.5)

    assert captured["full_url"] == SSURGO_POST_REST_URL
    encoded_data = captured["data"]
    assert isinstance(encoded_data, str)
    assert "format=JSON%2BCOLUMNNAME" in encoded_data
    assert "query=select+top+1+mukey+from+mapunit" in encoded_data
    assert captured["timeout"] == 12.5
    assert payload == {"Table": [["mukey"], ["1912968"]]}


def test_connector_does_not_import_requests_dependency() -> None:
    source = inspect.getsource(ssurgo_module)

    assert "import requests" not in source
