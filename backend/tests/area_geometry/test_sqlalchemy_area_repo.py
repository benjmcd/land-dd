from __future__ import annotations

import json
import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any, cast
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.area_geometry.area_repo import SqlAlchemyAreaRepository
from app.area_geometry.models import AreaModel, AreaVersionModel, PostGISGeometry
from app.area_geometry.service import AreaService
from app.db.engine import build_engine
from app.domain.area_contracts import AreaContract
from app.domain.enums import AreaType, ConfidenceBand

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "geometries"


def load_geometry(name: str) -> dict[str, object]:
    data = json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return cast(dict[str, object], data)


def test_area_model_maps_core_areas_table_without_creating_postgis_types() -> None:
    area_table = cast(Any, AreaModel.__table__)
    version_table = cast(Any, AreaVersionModel.__table__)

    assert area_table.schema == "core"
    assert area_table.name == "areas"
    assert isinstance(area_table.c.geom.type, PostGISGeometry)
    assert area_table.c.geom.type.get_col_spec() == "geometry(MultiPolygon, 4326)"
    assert area_table.c.area_type.type.create_type is False
    assert area_table.c.geom_confidence.type.create_type is False
    assert version_table.schema == "core"
    assert version_table.name == "area_versions"
    assert isinstance(version_table.c.geom.type, PostGISGeometry)
    assert version_table.c.geom.type.get_col_spec() == "geometry(MultiPolygon, 4326)"
    assert any(
        set(constraint.columns.keys()) == {"area_id", "version_num"}
        for constraint in version_table.constraints
    )


@pytest.fixture
def session() -> Iterator[Session]:
    if os.getenv("RUN_DB_SMOKE") != "1":
        pytest.skip("DB smoke not enabled")

    engine = build_engine()
    with Session(engine) as db_session:
        try:
            yield db_session
        finally:
            db_session.rollback()


@pytest.mark.parametrize(
    "fixture_name",
    ["valid_polygon.geojson", "valid_multipolygon.geojson"],
)
def test_sqlalchemy_area_repository_persists_geometry_as_postgis_multipolygon(
    fixture_name: str,
    session: Session,
) -> None:
    repo = SqlAlchemyAreaRepository(session)
    area = AreaContract(
        area_type=AreaType.DRAWN_POLYGON,
        label="fixture polygon",
        geom_geojson=load_geometry(fixture_name),
        geom_source="Lane B fixture",
        geom_confidence=ConfidenceBand.MEDIUM,
        geom_validated=True,
    )

    created = repo.add(area)
    session.commit()

    try:
        assert created.area_id == area.area_id
        assert created.area_type == AreaType.DRAWN_POLYGON
        assert created.geom_geojson["type"] == "MultiPolygon"
        assert created.geom_srid == 4326
        assert created.geom_source == "Lane B fixture"
        assert created.geom_confidence == ConfidenceBand.MEDIUM
        assert created.geom_validated is True

        with Session(session.get_bind()) as read_session:
            read_repo = SqlAlchemyAreaRepository(read_session)
            retrieved = read_repo.get(area.area_id)
            assert retrieved == created
            assert read_repo.exists(area.area_id) is True
            assert any(stored.area_id == area.area_id for stored in read_repo.list_all())
    finally:
        _delete_area(session, area.area_id)


def test_area_service_can_use_sqlalchemy_area_repository(session: Session) -> None:
    service = AreaService(SqlAlchemyAreaRepository(session))
    area = AreaContract(
        area_type=AreaType.PARCEL_LIKE,
        label="parcel-like fixture",
        geom_geojson=load_geometry("valid_polygon.geojson"),
        geom_source="county parcel fixture",
        geom_validated=True,
    )

    created = service.create(area)
    session.commit()

    try:
        assert created.geom_validated is False
        assert service.area_is_registered(area.area_id) is True
        assert service.get(area.area_id) == created
    finally:
        _delete_area(session, area.area_id)


@pytest.mark.parametrize(
    "fixture_name",
    ["valid_polygon.geojson", "valid_multipolygon.geojson"],
)
def test_sqlalchemy_area_repository_reads_postgis_metrics(
    fixture_name: str,
    session: Session,
) -> None:
    repo = SqlAlchemyAreaRepository(session)
    area = AreaContract(
        area_type=AreaType.DRAWN_POLYGON,
        label="metric fixture",
        geom_geojson=load_geometry(fixture_name),
        geom_source="Lane B metric fixture",
    )

    created = repo.add(area)
    session.commit()

    try:
        metrics = repo.get_metrics(created.area_id)
        retrieved = repo.get(created.area_id)

        assert metrics is not None
        assert metrics.area_id == created.area_id
        assert metrics.geom_srid == 4326
        assert metrics.centroid_geojson["type"] == "Point"
        assert metrics.bbox_geojson["type"] == "Polygon"
        assert metrics.area_sq_meters > 0
        assert metrics.measurement_method == "postgis_geography_area"
        assert "not a survey" in metrics.measurement_caveat
        assert retrieved is not None
        assert retrieved.geom_geojson["type"] == "MultiPolygon"
    finally:
        _delete_area(session, area.area_id)


def test_sqlalchemy_area_repository_returns_no_metrics_for_missing_area(
    session: Session,
) -> None:
    assert SqlAlchemyAreaRepository(session).get_metrics(UUID(int=0)) is None


def test_sqlalchemy_area_repository_reads_contained_spatial_relation(
    session: Session,
) -> None:
    repo = SqlAlchemyAreaRepository(session)
    area = AreaContract(
        area_type=AreaType.DRAWN_POLYGON,
        label="spatial relation fixture",
        geom_geojson=load_geometry("valid_polygon.geojson"),
        geom_source="Lane B spatial fixture",
    )

    created = repo.add(area)
    session.commit()

    try:
        relation = repo.get_spatial_relation(created.area_id, _contained_polygon())

        assert relation is not None
        assert relation.area_id == created.area_id
        assert relation.comparison_geom_srid == 4326
        assert relation.intersects is True
        assert relation.contains is True
        assert relation.distance_meters == 0
        assert relation.intersection_area_sq_meters > 0
        assert 0 < relation.intersection_ratio < 1
        assert relation.method_code == "postgis_st_relation_geography"
        assert "not a legal boundary" in relation.relation_caveat
    finally:
        _delete_area(session, area.area_id)


def test_sqlalchemy_area_repository_reads_disjoint_spatial_relation(
    session: Session,
) -> None:
    repo = SqlAlchemyAreaRepository(session)
    area = AreaContract(
        area_type=AreaType.DRAWN_POLYGON,
        label="spatial relation fixture",
        geom_geojson=load_geometry("valid_polygon.geojson"),
        geom_source="Lane B spatial fixture",
    )

    created = repo.add(area)
    session.commit()

    try:
        relation = repo.get_spatial_relation(created.area_id, _disjoint_polygon())

        assert relation is not None
        assert relation.intersects is False
        assert relation.contains is False
        assert relation.distance_meters > 0
        assert relation.intersection_area_sq_meters == 0
        assert relation.intersection_ratio == 0
    finally:
        _delete_area(session, area.area_id)


def test_sqlalchemy_area_repository_returns_no_relation_for_missing_area(
    session: Session,
) -> None:
    assert (
        SqlAlchemyAreaRepository(session).get_spatial_relation(
            UUID(int=0),
            _contained_polygon(),
        )
        is None
    )


def test_sqlalchemy_area_repository_rejects_wrong_relation_srid(
    session: Session,
) -> None:
    with pytest.raises(ValueError, match="geometry SRID must be 4326"):
        SqlAlchemyAreaRepository(session).get_spatial_relation(
            UUID(int=0),
            _contained_polygon(),
            comparison_geom_srid=3857,
        )


@pytest.mark.parametrize(
    "comparison_geom",
    [{}, load_geometry("wrong_type.geojson")],
)
def test_sqlalchemy_area_repository_rejects_invalid_relation_geometry(
    comparison_geom: dict[str, object],
    session: Session,
) -> None:
    with pytest.raises(ValueError, match="invalid comparison geometry"):
        SqlAlchemyAreaRepository(session).get_spatial_relation(
            UUID(int=0),
            comparison_geom,
        )


def test_sqlalchemy_area_repository_replaces_geometry_with_version_history(
    session: Session,
) -> None:
    repo = SqlAlchemyAreaRepository(session)
    original = repo.add(
        AreaContract(
            area_type=AreaType.DRAWN_POLYGON,
            label="version fixture",
            geom_geojson=load_geometry("valid_polygon.geojson"),
            geom_source="initial fixture",
            geom_confidence=ConfidenceBand.MEDIUM,
            geom_validated=True,
        )
    )
    session.commit()

    try:
        first_update = repo.replace_geometry(
            original.area_id,
            load_geometry("valid_multipolygon.geojson"),
            change_reason="add second fixture polygon",
            geom_source="replacement fixture",
            geom_confidence=ConfidenceBand.HIGH,
            geom_validated=True,
        )
        session.commit()

        assert first_update is not None
        versions = repo.list_versions(original.area_id)
        assert len(versions) == 1
        assert versions[0].version_num == 1
        assert versions[0].geom_geojson == original.geom_geojson
        assert versions[0].change_reason == "add second fixture polygon"
        assert first_update.geom_geojson["type"] == "MultiPolygon"
        assert first_update.geom_source == "replacement fixture"
        assert first_update.geom_confidence == ConfidenceBand.HIGH
        assert first_update.geom_validated is True

        second_update = repo.replace_geometry(
            original.area_id,
            load_geometry("valid_polygon.geojson"),
            change_reason="return to single fixture polygon",
            geom_source="second replacement fixture",
        )
        session.commit()

        assert second_update is not None
        versions = repo.list_versions(original.area_id)
        assert [version.version_num for version in versions] == [1, 2]
        assert versions[0].geom_geojson == original.geom_geojson
        assert versions[1].geom_geojson == first_update.geom_geojson
        assert versions[1].change_reason == "return to single fixture polygon"
    finally:
        _delete_area(session, original.area_id)


def test_sqlalchemy_area_repository_returns_no_update_for_missing_area(
    session: Session,
) -> None:
    repo = SqlAlchemyAreaRepository(session)

    assert (
        repo.replace_geometry(
            UUID(int=0),
            load_geometry("valid_polygon.geojson"),
            change_reason="missing area",
        )
        is None
    )
    assert repo.list_versions(UUID(int=0)) == []


def test_sqlalchemy_area_repository_rolls_back_geometry_replacement(
    session: Session,
) -> None:
    repo = SqlAlchemyAreaRepository(session)
    original = repo.add(
        AreaContract(
            area_type=AreaType.DRAWN_POLYGON,
            label="rollback fixture",
            geom_geojson=load_geometry("valid_polygon.geojson"),
            geom_source="initial fixture",
        )
    )
    session.commit()

    try:
        replaced = repo.replace_geometry(
            original.area_id,
            load_geometry("valid_multipolygon.geojson"),
            change_reason="rolled back replacement",
            geom_source="replacement fixture",
        )
        assert replaced is not None
        session.rollback()

        retrieved = repo.get(original.area_id)
        assert retrieved == original
        assert repo.list_versions(original.area_id) == []
    finally:
        _delete_area(session, original.area_id)


def test_sqlalchemy_area_repository_rejects_invalid_replacement_geometry(
    session: Session,
) -> None:
    with pytest.raises(ValueError, match="invalid comparison geometry"):
        SqlAlchemyAreaRepository(session).replace_geometry(
            UUID(int=0),
            load_geometry("wrong_type.geojson"),
            change_reason="invalid replacement",
        )


@pytest.mark.parametrize(
    ("area_type", "db_area_type", "fixture_name"),
    [
        (AreaType.PARCEL_LIKE, "parcel", "valid_polygon.geojson"),
        (AreaType.DRAWN_POLYGON, "polygon", "valid_polygon.geojson"),
        (AreaType.MULTI_POLYGON, "polygon", "valid_multipolygon.geojson"),
        (AreaType.LOCALITY, "locality", "valid_polygon.geojson"),
        (AreaType.BUFFER, "generated_candidate", "valid_polygon.geojson"),
        (
            AreaType.GENERATED_CANDIDATE,
            "generated_candidate",
            "valid_polygon.geojson",
        ),
    ],
)
def test_sqlalchemy_area_repository_round_trips_supported_domain_area_types(
    area_type: AreaType,
    db_area_type: str,
    fixture_name: str,
    session: Session,
) -> None:
    repo = SqlAlchemyAreaRepository(session)
    area = AreaContract(
        area_type=area_type,
        label=f"{area_type.value} fixture",
        geom_geojson=load_geometry(fixture_name),
    )

    created = repo.add(area)
    session.commit()

    try:
        assert created.area_type == area_type
        assert created.geom_geojson["type"] == "MultiPolygon"

        stored = session.execute(
            text(
                """
                SELECT area_type::text AS area_type, metadata
                FROM core.areas
                WHERE area_id = :area_id
                """
            ),
            {"area_id": created.area_id},
        ).mappings().one()
        assert stored["area_type"] == db_area_type
        assert stored["metadata"]["domain_area_type"] == area_type.value

        with Session(session.get_bind()) as read_session:
            retrieved = SqlAlchemyAreaRepository(read_session).get(created.area_id)
            assert retrieved == created
    finally:
        _delete_area(session, area.area_id)


def test_sqlalchemy_area_repository_rejects_conflicting_area_type_metadata(
    session: Session,
) -> None:
    area_id = uuid4()
    session.execute(
        text(
            """
            INSERT INTO core.areas (
                area_id,
                area_type,
                label,
                geom,
                metadata
            )
            VALUES (
                :area_id,
                'polygon',
                'conflicting metadata fixture',
                ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(:geom_geojson), 4326)),
                '{"domain_area_type": "buffer"}'::jsonb
            )
            """
        ),
        {
            "area_id": area_id,
            "geom_geojson": json.dumps(load_geometry("valid_polygon.geojson")),
        },
    )
    session.commit()

    try:
        with pytest.raises(ValueError, match="conflicts with stored area_type"):
            SqlAlchemyAreaRepository(session).get(area_id)
    finally:
        _delete_area(session, area_id)


def _delete_area(session: Session, area_id: UUID) -> None:
    session.execute(
        text("DELETE FROM core.area_versions WHERE area_id = :area_id"),
        {"area_id": area_id},
    )
    session.execute(
        text("DELETE FROM core.areas WHERE area_id = :area_id"),
        {"area_id": area_id},
    )
    session.commit()


def _contained_polygon() -> dict[str, object]:
    return {
        "type": "Polygon",
        "coordinates": [
            [
                [-119.98, 38.02],
                [-119.96, 38.02],
                [-119.96, 38.04],
                [-119.98, 38.04],
                [-119.98, 38.02],
            ]
        ],
    }


def _disjoint_polygon() -> dict[str, object]:
    return {
        "type": "Polygon",
        "coordinates": [
            [
                [-121.0, 37.0],
                [-120.9, 37.0],
                [-120.9, 37.1],
                [-121.0, 37.1],
                [-121.0, 37.0],
            ]
        ],
    }
