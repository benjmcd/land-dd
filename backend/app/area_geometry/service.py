from __future__ import annotations

from uuid import UUID

from app.area_geometry.area_repo import AreaRepository
from app.area_geometry.geometry_validator import validate_geojson
from app.domain.area_contracts import AreaContract
from app.domain.enums import AreaType


class AreaService:
    def __init__(self, repo: AreaRepository) -> None:
        self._repo = repo

    def create(self, area: AreaContract) -> AreaContract:
        if self._repo.exists(area.area_id):
            raise ValueError(f"Area '{area.area_id}' is already registered")

        errors = validate_geojson(area.geom_geojson, srid=area.geom_srid)
        if errors:
            raise ValueError("invalid area geometry: " + "; ".join(errors))

        stored_area = area
        if area.area_type == AreaType.PARCEL_LIKE and area.geom_validated:
            stored_area = area.model_copy(update={"geom_validated": False})
        return self._repo.add(stored_area)

    def get(self, area_id: UUID) -> AreaContract | None:
        return self._repo.get(area_id)

    def list_all(self) -> list[AreaContract]:
        return self._repo.list_all()

    def area_is_registered(self, area_id: UUID) -> bool:
        return self._repo.exists(area_id)


__all__ = ["AreaService"]
