from __future__ import annotations

from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.domain.enums import AreaType, ConfidenceBand


class AreaContract(BaseModel):
    area_id: UUID = Field(default_factory=uuid4)
    area_type: AreaType = AreaType.DRAWN_POLYGON
    label: str | None = None
    geom_geojson: dict[str, object] = Field(default_factory=dict)
    geom_source: str | None = None
    geom_confidence: ConfidenceBand = ConfidenceBand.UNKNOWN
    geom_validated: bool = False
