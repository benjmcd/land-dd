from __future__ import annotations

from app.domain.area_contracts import AreaContract
from app.domain.enums import AreaType, ConfidenceBand


def test_area_contract_defaults_to_unvalidated_drawn_polygon() -> None:
    area = AreaContract()

    assert area.area_type == AreaType.DRAWN_POLYGON
    assert area.geom_srid == 4326
    assert area.geom_confidence == ConfidenceBand.UNKNOWN
    assert area.geom_validated is False
    assert area.geom_geojson == {}
