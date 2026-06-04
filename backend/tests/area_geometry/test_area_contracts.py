from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.domain.area_contracts import (
    AreaContract,
    AreaMetricsContract,
    AreaSpatialRelationContract,
    AreaVersionContract,
)
from app.domain.enums import AreaType, ConfidenceBand


def test_area_contract_defaults_to_unvalidated_drawn_polygon() -> None:
    area = AreaContract()

    assert area.area_type == AreaType.DRAWN_POLYGON
    assert area.geom_srid == 4326
    assert area.geom_confidence == ConfidenceBand.UNKNOWN
    assert area.geom_validated is False
    assert area.geom_geojson == {}


def test_area_metrics_contract_captures_screening_measurements() -> None:
    metrics = AreaMetricsContract(
        area_id=uuid4(),
        centroid_geojson={"type": "Point", "coordinates": [-120.0, 38.0]},
        bbox_geojson={
            "type": "Polygon",
            "coordinates": [
                [
                    [-120.0, 38.0],
                    [-119.9, 38.0],
                    [-119.9, 38.1],
                    [-120.0, 38.1],
                    [-120.0, 38.0],
                ]
            ],
        },
        area_sq_meters=100.0,
    )

    assert metrics.geom_srid == 4326
    assert metrics.measurement_method == "postgis_geography_area"
    assert "not a survey" in metrics.measurement_caveat


def test_area_metrics_contract_rejects_negative_area() -> None:
    with pytest.raises(ValidationError, match="greater than or equal to 0"):
        AreaMetricsContract(
            area_id=uuid4(),
            centroid_geojson={"type": "Point", "coordinates": [-120.0, 38.0]},
            bbox_geojson={"type": "Polygon", "coordinates": []},
            area_sq_meters=-1.0,
        )


def test_area_spatial_relation_contract_captures_screening_result() -> None:
    relation = AreaSpatialRelationContract(
        area_id=uuid4(),
        intersects=True,
        contains=False,
        distance_meters=0.0,
        intersection_area_sq_meters=250.0,
        intersection_ratio=0.5,
    )

    assert relation.comparison_geom_srid == 4326
    assert relation.method_code == "postgis_st_relation_geography"
    assert "not a legal boundary" in relation.relation_caveat


def test_area_spatial_relation_contract_rejects_out_of_range_ratio() -> None:
    with pytest.raises(ValidationError, match="less than or equal to 1"):
        AreaSpatialRelationContract(
            area_id=uuid4(),
            intersects=True,
            contains=True,
            distance_meters=0.0,
            intersection_area_sq_meters=1.0,
            intersection_ratio=1.5,
        )


def test_area_version_contract_captures_immutable_geometry_version() -> None:
    area_id = uuid4()
    version = AreaVersionContract(
        area_version_id=uuid4(),
        area_id=area_id,
        version_num=1,
        geom_geojson={
            "type": "MultiPolygon",
            "coordinates": [
                [
                    [
                        [-120.0, 38.0],
                        [-119.9, 38.0],
                        [-119.9, 38.1],
                        [-120.0, 38.1],
                        [-120.0, 38.0],
                    ]
                ]
            ],
        },
        change_reason="fixture boundary correction",
    )

    assert version.area_id == area_id
    assert version.geom_srid == 4326
    assert version.change_reason == "fixture boundary correction"


def test_area_version_contract_rejects_zero_version_number() -> None:
    with pytest.raises(ValidationError, match="greater than or equal to 1"):
        AreaVersionContract(
            area_version_id=uuid4(),
            area_id=uuid4(),
            version_num=0,
            geom_geojson={},
        )
