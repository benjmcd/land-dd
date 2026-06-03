from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest

from app.area_geometry.area_repo import InMemoryAreaRepository
from app.area_geometry.geometry_validator import validate_geojson
from app.area_geometry.service import AreaService
from app.domain.area_contracts import AreaContract
from app.domain.enums import AreaType

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "geometries"


def load_geometry(name: str) -> dict[str, object]:
    data = json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return cast(dict[str, object], data)


def test_area_service_creates_and_gets_valid_area() -> None:
    service = AreaService(InMemoryAreaRepository())
    area = AreaContract(
        label="fixture polygon",
        geom_geojson=load_geometry("valid_polygon.geojson"),
        geom_source="fixture",
    )

    created = service.create(area)

    assert created.area_id == area.area_id
    assert created.geom_srid == 4326
    assert created.geom_validated is False
    assert service.get(area.area_id) == created
    assert service.area_is_registered(area.area_id) is True


def test_area_service_returns_none_for_missing_area() -> None:
    service = AreaService(InMemoryAreaRepository())
    area = AreaContract(geom_geojson=load_geometry("valid_polygon.geojson"))

    assert service.get(area.area_id) is None
    assert service.area_is_registered(area.area_id) is False


def test_area_service_rejects_invalid_geometry() -> None:
    service = AreaService(InMemoryAreaRepository())
    area = AreaContract(geom_geojson=load_geometry("wrong_type.geojson"))

    with pytest.raises(ValueError, match="Polygon or MultiPolygon"):
        service.create(area)


def test_area_service_rejects_unsupported_srid() -> None:
    service = AreaService(InMemoryAreaRepository())
    area = AreaContract(geom_geojson=load_geometry("valid_polygon.geojson"), geom_srid=3857)

    with pytest.raises(ValueError, match="SRID must be 4326"):
        service.create(area)


def test_area_service_rejects_duplicate_area_id() -> None:
    service = AreaService(InMemoryAreaRepository())
    area = AreaContract(geom_geojson=load_geometry("valid_polygon.geojson"))

    service.create(area)

    with pytest.raises(ValueError, match="already registered"):
        service.create(area)


def test_parcel_like_area_remains_unvalidated() -> None:
    service = AreaService(InMemoryAreaRepository())
    area = AreaContract(
        area_type=AreaType.PARCEL_LIKE,
        geom_geojson=load_geometry("valid_polygon.geojson"),
        geom_source="county parcel fixture",
        geom_validated=True,
    )

    created = service.create(area)

    assert created.geom_validated is False


def test_drawn_polygon_can_preserve_explicit_validation_flag() -> None:
    service = AreaService(InMemoryAreaRepository())
    area = AreaContract(
        area_type=AreaType.DRAWN_POLYGON,
        geom_geojson=load_geometry("valid_polygon.geojson"),
        geom_source="survey fixture",
        geom_validated=True,
    )

    created = service.create(area)

    assert created.geom_validated is True


@pytest.mark.parametrize(
    "fixture_name",
    ["valid_polygon.geojson", "valid_multipolygon.geojson", "large_polygon.geojson"],
)
def test_validate_geojson_accepts_supported_geometries(fixture_name: str) -> None:
    assert validate_geojson(load_geometry(fixture_name)) == []


@pytest.mark.parametrize(
    ("fixture_name", "expected_error"),
    [
        ("empty_coordinates.geojson", "non-empty array"),
        ("missing_type.geojson", "geometry.type is required"),
        ("wrong_type.geojson", "Polygon or MultiPolygon"),
        ("wrong_srid.geojson", "must be EPSG:4326"),
        ("open_ring.geojson", "must be closed"),
    ],
)
def test_validate_geojson_rejects_invalid_geometries(
    fixture_name: str,
    expected_error: str,
) -> None:
    errors = validate_geojson(load_geometry(fixture_name))

    assert any(expected_error in error for error in errors)
