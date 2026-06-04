from __future__ import annotations

from collections.abc import Mapping, Sequence
from math import isfinite
from typing import cast

SUPPORTED_GEOMETRY_TYPES = {"Polygon", "MultiPolygon"}
SUPPORTED_SRID = 4326
SUPPORTED_CRS_NAMES = {"EPSG:4326", "urn:ogc:def:crs:EPSG::4326"}


def validate_geojson(geom: Mapping[str, object], srid: int = SUPPORTED_SRID) -> list[str]:
    errors: list[str] = []
    if srid != SUPPORTED_SRID:
        errors.append("geometry SRID must be 4326")
    if not geom:
        errors.append("geometry must not be empty")
        return errors

    geom_type = geom.get("type")
    if not isinstance(geom_type, str):
        errors.append("geometry.type is required")
        return errors
    if geom_type not in SUPPORTED_GEOMETRY_TYPES:
        errors.append("geometry.type must be Polygon or MultiPolygon")
        return errors

    coordinates = geom.get("coordinates")
    if not isinstance(coordinates, list) or not coordinates:
        errors.append("geometry.coordinates must be a non-empty array")
        return errors

    errors.extend(_validate_crs(geom))
    if geom_type == "Polygon":
        errors.extend(_validate_polygon(coordinates, "coordinates"))
    else:
        for polygon_index, polygon in enumerate(coordinates):
            errors.extend(_validate_polygon(polygon, f"coordinates[{polygon_index}]"))
    return errors


def _validate_crs(geom: Mapping[str, object]) -> list[str]:
    crs = geom.get("crs")
    if crs is None:
        return []
    if not isinstance(crs, Mapping):
        return ["geometry.crs must be an object when provided"]
    if crs.get("type") != "name":
        return ["geometry.crs.type must be name when provided"]

    properties = crs.get("properties")
    if not isinstance(properties, Mapping):
        return ["geometry.crs.properties must be an object when provided"]
    name = properties.get("name")
    if name not in SUPPORTED_CRS_NAMES:
        return ["geometry.crs.properties.name must be EPSG:4326"]
    return []


def _validate_polygon(value: object, path: str) -> list[str]:
    if not isinstance(value, list) or not value:
        return [f"{path} must contain at least one linear ring"]

    errors: list[str] = []
    for ring_index, ring in enumerate(value):
        errors.extend(_validate_ring(ring, f"{path}[{ring_index}]"))
    return errors


def _validate_ring(value: object, path: str) -> list[str]:
    if not isinstance(value, list):
        return [f"{path} must be an array of positions"]
    if len(value) < 4:
        return [f"{path} must contain at least four positions"]

    errors: list[str] = []
    for position_index, position in enumerate(value):
        if not _is_position(position):
            errors.append(f"{path}[{position_index}] must be a numeric lon/lat position")
            continue
        position_pair = _position_pair(position)
        if position_pair is not None:
            errors.extend(_validate_position_bounds(position_pair, f"{path}[{position_index}]"))

    if errors:
        return errors
    if not _positions_equal(value[0], value[-1]):
        errors.append(f"{path} must be closed")
    return errors


def _is_position(value: object) -> bool:
    if not isinstance(value, Sequence) or isinstance(value, str | bytes):
        return False
    if len(value) < 2:
        return False
    return _is_number(value[0]) and _is_number(value[1])


def _is_number(value: object) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _positions_equal(left: object, right: object) -> bool:
    left_position = _position_pair(left)
    right_position = _position_pair(right)
    if left_position is None or right_position is None:
        return False
    return left_position == right_position


def _position_pair(value: object) -> tuple[int | float, int | float] | None:
    if not _is_position(value):
        return None
    position = cast(Sequence[object], value)
    return cast(int | float, position[0]), cast(int | float, position[1])


def _validate_position_bounds(
    position: tuple[int | float, int | float],
    path: str,
) -> list[str]:
    longitude, latitude = position
    if not isfinite(longitude) or not isfinite(latitude):
        return [f"{path} longitude and latitude must be finite"]

    errors: list[str] = []
    if longitude < -180 or longitude > 180:
        errors.append(f"{path} longitude must be between -180 and 180")
    if latitude < -90 or latitude > 90:
        errors.append(f"{path} latitude must be between -90 and 90")
    return errors


__all__ = ["validate_geojson"]
