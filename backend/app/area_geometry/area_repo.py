from __future__ import annotations

import json
from typing import Any, Protocol
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import TextClause

from app.area_geometry.geometry_validator import validate_geojson
from app.domain.area_contracts import (
    AreaContract,
    AreaMetricsContract,
    AreaSpatialRelationContract,
    AreaVersionContract,
)
from app.domain.enums import AreaType, ConfidenceBand


class AreaRepository(Protocol):
    def add(self, area: AreaContract) -> AreaContract: ...

    def get(self, area_id: UUID) -> AreaContract | None: ...

    def list_all(self) -> list[AreaContract]: ...

    def exists(self, area_id: UUID) -> bool: ...


class InMemoryAreaRepository:
    def __init__(self) -> None:
        self._store: dict[UUID, AreaContract] = {}

    def add(self, area: AreaContract) -> AreaContract:
        self._store[area.area_id] = area
        return area

    def get(self, area_id: UUID) -> AreaContract | None:
        return self._store.get(area_id)

    def list_all(self) -> list[AreaContract]:
        return list(self._store.values())

    def exists(self, area_id: UUID) -> bool:
        return area_id in self._store


class SqlAlchemyAreaRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, area: AreaContract) -> AreaContract:
        if area.geom_srid != 4326:
            raise ValueError("core.areas only supports SRID 4326")

        row = self._session.execute(
            text(
                """
                INSERT INTO core.areas (
                    area_id,
                    workspace_id,
                    area_type,
                    label,
                    geom,
                    geom_validated,
                    geom_source,
                    created_by,
                    geom_confidence,
                    metadata
                )
                VALUES (
                    :area_id,
                    :workspace_id,
                    CAST(:area_type AS core.area_type),
                    :label,
                    ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(:geom_geojson), :geom_srid)),
                    :geom_validated,
                    :geom_source,
                    :created_by,
                    CAST(:geom_confidence AS evidence.confidence_band),
                    CAST(:area_metadata AS jsonb)
                )
                RETURNING
                    area_id,
                    workspace_id,
                    area_type::text AS area_type,
                    label,
                    ST_AsGeoJSON(geom) AS geom_geojson,
                    ST_SRID(geom) AS geom_srid,
                    geom_source,
                    created_by,
                    geom_confidence::text AS geom_confidence,
                    geom_validated,
                    metadata AS area_metadata
                """
            ),
            {
                "area_id": area.area_id,
                "workspace_id": area.workspace_id,
                "area_type": _area_type_to_db(area.area_type),
                "area_metadata": json.dumps(_area_metadata_for(area.area_type)),
                "label": area.label,
                "geom_geojson": json.dumps(area.geom_geojson),
                "geom_srid": area.geom_srid,
                "geom_validated": area.geom_validated,
                "geom_source": area.geom_source,
                "created_by": area.created_by,
                "geom_confidence": area.geom_confidence.value,
            },
        ).mappings().one()
        self._session.flush()
        return _row_to_area(row)

    def get(self, area_id: UUID) -> AreaContract | None:
        row = self._session.execute(
            _select_area_statement("WHERE area_id = :area_id"),
            {"area_id": area_id},
        ).mappings().one_or_none()
        if row is None:
            return None
        return _row_to_area(row)

    def list_all(self) -> list[AreaContract]:
        rows = self._session.execute(
            _select_area_statement("ORDER BY created_at, area_id")
        ).mappings().all()
        return [_row_to_area(row) for row in rows]

    def exists(self, area_id: UUID) -> bool:
        return (
            self._session.execute(
                text("SELECT 1 FROM core.areas WHERE area_id = :area_id LIMIT 1"),
                {"area_id": area_id},
            ).first()
            is not None
        )

    def get_metrics(self, area_id: UUID) -> AreaMetricsContract | None:
        row = self._session.execute(
            text(
                """
                SELECT
                    area_id,
                    ST_SRID(geom) AS geom_srid,
                    ST_AsGeoJSON(centroid) AS centroid_geojson,
                    ST_AsGeoJSON(bbox) AS bbox_geojson,
                    ST_Area(geom::geography) AS area_sq_meters
                FROM core.areas
                WHERE area_id = :area_id
                """
            ),
            {"area_id": area_id},
        ).mappings().one_or_none()
        if row is None:
            return None
        return _row_to_area_metrics(row)

    def get_spatial_relation(
        self,
        area_id: UUID,
        comparison_geom_geojson: dict[str, object],
        *,
        comparison_geom_srid: int = 4326,
    ) -> AreaSpatialRelationContract | None:
        _validate_comparison_geometry(
            comparison_geom_geojson,
            srid=comparison_geom_srid,
        )
        row = self._session.execute(
            text(
                """
                WITH comparison AS (
                    SELECT ST_Multi(
                        ST_SetSRID(
                            ST_GeomFromGeoJSON(:comparison_geom_geojson),
                            :comparison_geom_srid
                        )
                    ) AS geom
                )
                SELECT
                    area_id,
                    :comparison_geom_srid AS comparison_geom_srid,
                    ST_Intersects(a.geom, c.geom) AS intersects,
                    ST_Contains(a.geom, c.geom) AS contains,
                    ST_Distance(a.geom::geography, c.geom::geography) AS distance_meters,
                    CASE
                        WHEN ST_Intersects(a.geom, c.geom)
                        THEN ST_Area(ST_Intersection(a.geom, c.geom)::geography)
                        ELSE 0
                    END AS intersection_area_sq_meters,
                    CASE
                        WHEN ST_Area(a.geom::geography) = 0 THEN 0
                        WHEN ST_Intersects(a.geom, c.geom)
                        THEN ST_Area(ST_Intersection(a.geom, c.geom)::geography)
                            / ST_Area(a.geom::geography)
                        ELSE 0
                    END AS intersection_ratio
                FROM core.areas a
                CROSS JOIN comparison c
                WHERE area_id = :area_id
                """
            ),
            {
                "area_id": area_id,
                "comparison_geom_geojson": json.dumps(comparison_geom_geojson),
                "comparison_geom_srid": comparison_geom_srid,
            },
        ).mappings().one_or_none()
        if row is None:
            return None
        return _row_to_spatial_relation(row)

    def replace_geometry(
        self,
        area_id: UUID,
        geom_geojson: dict[str, object],
        *,
        change_reason: str | None,
        geom_srid: int = 4326,
        geom_source: str | None = None,
        geom_confidence: ConfidenceBand = ConfidenceBand.UNKNOWN,
        geom_validated: bool = False,
    ) -> AreaContract | None:
        _validate_comparison_geometry(geom_geojson, srid=geom_srid)
        row = self._session.execute(
            text(
                """
                WITH current_area AS (
                    SELECT area_id, geom
                    FROM core.areas
                    WHERE area_id = :area_id
                    FOR UPDATE
                ),
                next_version AS (
                    SELECT COALESCE(MAX(version_num), 0) + 1 AS version_num
                    FROM core.area_versions
                    WHERE area_id = :area_id
                ),
                inserted_version AS (
                    INSERT INTO core.area_versions (
                        area_id,
                        version_num,
                        geom,
                        change_reason
                    )
                    SELECT
                        current_area.area_id,
                        next_version.version_num,
                        current_area.geom,
                        :change_reason
                    FROM current_area
                    CROSS JOIN next_version
                    RETURNING area_version_id
                )
                UPDATE core.areas
                SET
                    geom = ST_Multi(
                        ST_SetSRID(ST_GeomFromGeoJSON(:geom_geojson), :geom_srid)
                    ),
                    geom_validated = :geom_validated,
                    geom_source = :geom_source,
                    geom_confidence = CAST(:geom_confidence AS evidence.confidence_band)
                WHERE area_id = :area_id
                    AND EXISTS (SELECT 1 FROM inserted_version)
                RETURNING
                    area_id,
                    workspace_id,
                    area_type::text AS area_type,
                    label,
                    ST_AsGeoJSON(geom) AS geom_geojson,
                    ST_SRID(geom) AS geom_srid,
                    geom_source,
                    created_by,
                    geom_confidence::text AS geom_confidence,
                    geom_validated,
                    metadata AS area_metadata
                """
            ),
            {
                "area_id": area_id,
                "geom_geojson": json.dumps(geom_geojson),
                "geom_srid": geom_srid,
                "change_reason": change_reason,
                "geom_validated": geom_validated,
                "geom_source": geom_source,
                "geom_confidence": geom_confidence.value,
            },
        ).mappings().one_or_none()
        if row is None:
            return None
        self._session.flush()
        return _row_to_area(row)

    def list_versions(self, area_id: UUID) -> list[AreaVersionContract]:
        rows = self._session.execute(
            text(
                """
                SELECT
                    area_version_id,
                    area_id,
                    version_num,
                    ST_AsGeoJSON(geom) AS geom_geojson,
                    ST_SRID(geom) AS geom_srid,
                    change_reason
                FROM core.area_versions
                WHERE area_id = :area_id
                ORDER BY version_num
                """
            ),
            {"area_id": area_id},
        ).mappings().all()
        return [_row_to_area_version(row) for row in rows]


def _select_area_statement(suffix: str) -> TextClause:
    return text(
        f"""
        SELECT
            area_id,
            workspace_id,
            area_type::text AS area_type,
            label,
            ST_AsGeoJSON(geom) AS geom_geojson,
            ST_SRID(geom) AS geom_srid,
            geom_source,
            created_by,
            geom_confidence::text AS geom_confidence,
            geom_validated,
            metadata AS area_metadata,
            created_at
        FROM core.areas
        {suffix}
        """
    )


_DOMAIN_TO_DB_AREA_TYPE = {
    AreaType.PARCEL_LIKE: "parcel",
    AreaType.DRAWN_POLYGON: "polygon",
    AreaType.MULTI_POLYGON: "polygon",
    AreaType.LOCALITY: "locality",
    AreaType.BUFFER: "generated_candidate",
    AreaType.GENERATED_CANDIDATE: "generated_candidate",
}

_DB_TO_DOMAIN_AREA_TYPE = {
    "parcel": AreaType.PARCEL_LIKE,
    "polygon": AreaType.DRAWN_POLYGON,
    "locality": AreaType.LOCALITY,
    "generated_candidate": AreaType.GENERATED_CANDIDATE,
}


def _area_metadata_for(area_type: AreaType) -> dict[str, str]:
    return {"domain_area_type": area_type.value}


def _area_type_to_db(area_type: AreaType) -> str:
    db_value = _DOMAIN_TO_DB_AREA_TYPE.get(area_type)
    if db_value is None:
        raise ValueError(f"area type '{area_type.value}' has no core.areas mapping")
    return db_value


def _db_area_type_to_domain(
    area_type: str,
    area_metadata: dict[str, object],
) -> AreaType:
    metadata_area_type = area_metadata.get("domain_area_type")
    if metadata_area_type is not None:
        if not isinstance(metadata_area_type, str):
            raise ValueError("core.areas metadata domain_area_type must be a string")
        try:
            domain_area_type = AreaType(metadata_area_type)
        except ValueError as exc:
            raise ValueError(
                "core.areas metadata domain_area_type is not supported"
            ) from exc
        expected_db_type = _DOMAIN_TO_DB_AREA_TYPE[domain_area_type]
        if expected_db_type != area_type:
            raise ValueError(
                "core.areas metadata domain_area_type conflicts with stored area_type"
            )
        return domain_area_type

    domain_value = _DB_TO_DOMAIN_AREA_TYPE.get(area_type)
    if domain_value is None:
        raise ValueError(f"core.areas area type '{area_type}' has no domain mapping")
    return domain_value


def _row_to_area(row: Any) -> AreaContract:
    geom_geojson = row["geom_geojson"]
    if isinstance(geom_geojson, str):
        geom_geojson = json.loads(geom_geojson)
    if not isinstance(geom_geojson, dict):
        raise ValueError("core.areas returned invalid GeoJSON")

    return AreaContract(
        area_id=row["area_id"],
        workspace_id=row["workspace_id"],
        created_by=row["created_by"],
        area_type=_db_area_type_to_domain(
            row["area_type"],
            _json_object(row["area_metadata"], "area metadata"),
        ),
        label=row["label"],
        geom_geojson=geom_geojson,
        geom_srid=row["geom_srid"],
        geom_source=row["geom_source"],
        geom_confidence=ConfidenceBand(row["geom_confidence"]),
        geom_validated=row["geom_validated"],
    )


def _row_to_area_metrics(row: Any) -> AreaMetricsContract:
    return AreaMetricsContract(
        area_id=row["area_id"],
        geom_srid=row["geom_srid"],
        centroid_geojson=_json_object(row["centroid_geojson"], "centroid"),
        bbox_geojson=_json_object(row["bbox_geojson"], "bbox"),
        area_sq_meters=float(row["area_sq_meters"]),
    )


def _row_to_spatial_relation(row: Any) -> AreaSpatialRelationContract:
    return AreaSpatialRelationContract(
        area_id=row["area_id"],
        comparison_geom_srid=row["comparison_geom_srid"],
        intersects=row["intersects"],
        contains=row["contains"],
        distance_meters=float(row["distance_meters"]),
        intersection_area_sq_meters=float(row["intersection_area_sq_meters"]),
        intersection_ratio=float(row["intersection_ratio"]),
    )


def _row_to_area_version(row: Any) -> AreaVersionContract:
    return AreaVersionContract(
        area_version_id=row["area_version_id"],
        area_id=row["area_id"],
        version_num=row["version_num"],
        geom_geojson=_json_object(row["geom_geojson"], "area version"),
        geom_srid=row["geom_srid"],
        change_reason=row["change_reason"],
    )


def _validate_comparison_geometry(
    geom_geojson: dict[str, object],
    *,
    srid: int,
) -> None:
    errors = validate_geojson(geom_geojson, srid=srid)
    if errors:
        raise ValueError("invalid comparison geometry: " + "; ".join(errors))


def _json_object(value: object, label: str) -> dict[str, object]:
    if isinstance(value, str):
        value = json.loads(value)
    if not isinstance(value, dict):
        raise ValueError(f"core.areas returned invalid {label} GeoJSON")
    return value


__all__ = [
    "AreaRepository",
    "InMemoryAreaRepository",
    "SqlAlchemyAreaRepository",
]
