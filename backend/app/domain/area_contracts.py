from __future__ import annotations

from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.domain.enums import AreaType, ConfidenceBand


class AreaContract(BaseModel):
    area_id: UUID = Field(default_factory=uuid4)
    workspace_id: UUID | None = None
    created_by: UUID | None = None
    area_type: AreaType = AreaType.DRAWN_POLYGON
    label: str | None = None
    geom_geojson: dict[str, object] = Field(default_factory=dict)
    geom_srid: int = 4326
    geom_source: str | None = None
    geom_confidence: ConfidenceBand = ConfidenceBand.UNKNOWN
    geom_validated: bool = False


class AreaMetricsContract(BaseModel):
    area_id: UUID
    geom_srid: int = 4326
    centroid_geojson: dict[str, object] = Field(default_factory=dict)
    bbox_geojson: dict[str, object] = Field(default_factory=dict)
    area_sq_meters: float = Field(ge=0)
    measurement_method: str = "postgis_geography_area"
    measurement_caveat: str = (
        "Screening measurement from stored geometry; not a survey area."
    )


class AreaSpatialRelationContract(BaseModel):
    area_id: UUID
    comparison_geom_srid: int = 4326
    intersects: bool
    contains: bool
    distance_meters: float = Field(ge=0)
    intersection_area_sq_meters: float = Field(ge=0)
    intersection_ratio: float = Field(ge=0, le=1)
    method_code: str = "postgis_st_relation_geography"
    relation_caveat: str = (
        "Screening spatial relationship from stored geometry; not a legal boundary "
        "determination."
    )


class AreaVersionContract(BaseModel):
    area_version_id: UUID
    area_id: UUID
    version_num: int = Field(ge=1)
    geom_geojson: dict[str, object] = Field(default_factory=dict)
    geom_srid: int = 4326
    change_reason: str | None = None
