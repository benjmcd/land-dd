from __future__ import annotations

from dataclasses import dataclass

from app.connectors.assessor_not_evaluated import ASSESSOR_NOT_EVALUATED_CONNECTOR_NAME
from app.connectors.blm_mlrs import BLM_MLRS_CONNECTOR_NAME
from app.connectors.brunswick_parcels import BRUNSWICK_PARCELS_CONNECTOR_NAME
from app.connectors.brunswick_zoning_recorded import BRUNSWICK_ZONING_CONNECTOR_NAME
from app.connectors.buncombe_parcels import BUNCOMBE_PARCELS_CONNECTOR_NAME
from app.connectors.census_tiger import CENSUS_TIGER_CONNECTOR_NAME
from app.connectors.epa_echo import EPA_ECHO_CONNECTOR_NAME
from app.connectors.fcc_broadband import FCC_BROADBAND_CONNECTOR_NAME
from app.connectors.nc_geologic_map import NC_GEOLOGIC_MAP_CONNECTOR_NAME
from app.connectors.noaa_climate import NOAA_CLIMATE_CONNECTOR_NAME
from app.connectors.osm_road_access import OSM_ROAD_ACCESS_CONNECTOR_NAME
from app.connectors.usgs_mrds import USGS_MRDS_CONNECTOR_NAME
from app.connectors.usgs_water_monitoring import USGS_WATER_CONNECTOR_NAME


@dataclass(frozen=True)
class SourceConnectorInventoryEntry:
    source_registry_id: str
    connector_name: str
    surfaces: tuple[str, ...]
    scope_note: str = ""


IMMEDIATE_OPERATOR_API = "immediate_operator_api"
DURABLE_LIVE_JOB = "durable_live_job"
REQUEST_TIME_ORCHESTRATION = "request_time_orchestration"

IMPLEMENTED_SOURCE_CONNECTORS: dict[str, SourceConnectorInventoryEntry] = {
    "DS-005": SourceConnectorInventoryEntry(
        source_registry_id="DS-005",
        connector_name=USGS_WATER_CONNECTOR_NAME,
        surfaces=(IMMEDIATE_OPERATOR_API, REQUEST_TIME_ORCHESTRATION),
        scope_note=(
            "USGS water monitoring context only; not water-rights, well-yield, "
            "or potable-water suitability proof."
        ),
    ),
    "DS-006": SourceConnectorInventoryEntry(
        source_registry_id="DS-006",
        connector_name=EPA_ECHO_CONNECTOR_NAME,
        surfaces=(IMMEDIATE_OPERATOR_API, REQUEST_TIME_ORCHESTRATION),
        scope_note=(
            "EPA ECHO facility/compliance screening context only; not an "
            "environmental liability determination."
        ),
    ),
    "DS-007": SourceConnectorInventoryEntry(
        source_registry_id="DS-007",
        connector_name=BLM_MLRS_CONNECTOR_NAME,
        surfaces=(IMMEDIATE_OPERATOR_API, REQUEST_TIME_ORCHESTRATION),
        scope_note=(
            "Active federal mining-claim geospatial context only; not private "
            "mineral-rights, title, hazard, value, or extraction proof."
        ),
    ),
    "DS-008": SourceConnectorInventoryEntry(
        source_registry_id="DS-008",
        connector_name=USGS_MRDS_CONNECTOR_NAME,
        surfaces=(IMMEDIATE_OPERATOR_API, REQUEST_TIME_ORCHESTRATION),
        scope_note=(
            "Historical mineral-occurrence screening only; MRDS updates ceased "
            "in 2011 and does not prove mineral rights or hazards."
        ),
    ),
    "DS-015": SourceConnectorInventoryEntry(
        source_registry_id="DS-015",
        connector_name=NC_GEOLOGIC_MAP_CONNECTOR_NAME,
        surfaces=(IMMEDIATE_OPERATOR_API, REQUEST_TIME_ORCHESTRATION),
        scope_note=(
            "NCGS 1985 statewide geologic map-unit context only; not "
            "geotechnical, hazard, mineral-resource, or buildability proof."
        ),
    ),
    "DS-001": SourceConnectorInventoryEntry(
        source_registry_id="DS-001",
        connector_name="usgs_tnm_live",
        surfaces=(IMMEDIATE_OPERATOR_API, DURABLE_LIVE_JOB, REQUEST_TIME_ORCHESTRATION),
    ),
    "DS-002": SourceConnectorInventoryEntry(
        source_registry_id="DS-002",
        connector_name="fema_nfhl_live",
        surfaces=(IMMEDIATE_OPERATOR_API, DURABLE_LIVE_JOB, REQUEST_TIME_ORCHESTRATION),
    ),
    "DS-003": SourceConnectorInventoryEntry(
        source_registry_id="DS-003",
        connector_name="ssurgo_live",
        surfaces=(IMMEDIATE_OPERATOR_API, DURABLE_LIVE_JOB, REQUEST_TIME_ORCHESTRATION),
    ),
    "DS-004": SourceConnectorInventoryEntry(
        source_registry_id="DS-004",
        connector_name="nwi_live",
        surfaces=(IMMEDIATE_OPERATOR_API, DURABLE_LIVE_JOB, REQUEST_TIME_ORCHESTRATION),
    ),
    "DS-010": SourceConnectorInventoryEntry(
        source_registry_id="DS-010",
        connector_name="chatham_parcels_live",
        surfaces=(IMMEDIATE_OPERATOR_API, REQUEST_TIME_ORCHESTRATION),
        scope_note=(
            "Chatham County NC parcel screening only; no owner/value/title "
            "fields; durable live-job support not claimed."
        ),
    ),
    "DS-010-buncombe": SourceConnectorInventoryEntry(
        source_registry_id="DS-010",
        connector_name=BUNCOMBE_PARCELS_CONNECTOR_NAME,
        surfaces=(IMMEDIATE_OPERATOR_API, REQUEST_TIME_ORCHESTRATION),
        scope_note=(
            "Buncombe County NC parcel screening only; no owner/value/title "
            "fields; durable live-job support not claimed."
        ),
    ),
    "DS-010-brunswick": SourceConnectorInventoryEntry(
        source_registry_id="DS-010",
        connector_name=BRUNSWICK_PARCELS_CONNECTOR_NAME,
        surfaces=(IMMEDIATE_OPERATOR_API, REQUEST_TIME_ORCHESTRATION),
        scope_note=(
            "Brunswick County NC parcel screening only; no owner/value/title "
            "fields; durable live-job support not claimed."
        ),
    ),
    "DS-011": SourceConnectorInventoryEntry(
        source_registry_id="DS-011",
        connector_name=ASSESSOR_NOT_EVALUATED_CONNECTOR_NAME,
        surfaces=(IMMEDIATE_OPERATOR_API, REQUEST_TIME_ORCHESTRATION),
        scope_note=(
            "Assessor NOT_EVALUATED sentinel only; no live assessor portal "
            "query and no owner/value/sale-history data."
        ),
    ),
    "DS-016": SourceConnectorInventoryEntry(
        source_registry_id="DS-016",
        connector_name=OSM_ROAD_ACCESS_CONNECTOR_NAME,
        surfaces=(IMMEDIATE_OPERATOR_API, REQUEST_TIME_ORCHESTRATION),
    ),
    "DS-020": SourceConnectorInventoryEntry(
        source_registry_id="DS-020",
        connector_name=NOAA_CLIMATE_CONNECTOR_NAME,
        surfaces=(IMMEDIATE_OPERATOR_API, REQUEST_TIME_ORCHESTRATION),
        scope_note=(
            "NOAA NWS point/forecast-zone context only; not climate normals, "
            "frost-date, growing-season, or agricultural-risk proof."
        ),
    ),
    "DS-021": SourceConnectorInventoryEntry(
        source_registry_id="DS-021",
        connector_name=FCC_BROADBAND_CONNECTOR_NAME,
        surfaces=(IMMEDIATE_OPERATOR_API, REQUEST_TIME_ORCHESTRATION),
    ),
    "DS-022": SourceConnectorInventoryEntry(
        source_registry_id="DS-022",
        connector_name=CENSUS_TIGER_CONNECTOR_NAME,
        surfaces=(IMMEDIATE_OPERATOR_API, REQUEST_TIME_ORCHESTRATION),
        scope_note=(
            "TIGERweb geography context only; ACS demographic variables and "
            "protected-class/residential-steering uses are excluded."
        ),
    ),
    "DS-023": SourceConnectorInventoryEntry(
        source_registry_id="DS-023",
        connector_name="chatham_zoning_udo_recorded",
        surfaces=(IMMEDIATE_OPERATOR_API, REQUEST_TIME_ORCHESTRATION),
        scope_note=(
            "Chatham County NC recorded-fixture UDO district lookup only; not "
            "live PDF ingestion or legal zoning advice."
        ),
    ),
    "DS-023-brunswick": SourceConnectorInventoryEntry(
        source_registry_id="DS-023",
        connector_name=BRUNSWICK_ZONING_CONNECTOR_NAME,
        surfaces=(IMMEDIATE_OPERATOR_API, REQUEST_TIME_ORCHESTRATION),
        scope_note=(
            "Brunswick County NC recorded-fixture UDO district lookup only; not "
            "live PDF ingestion or legal zoning advice."
        ),
    ),
}


def source_connector_inventory_entry(
    source_registry_id: str,
) -> SourceConnectorInventoryEntry | None:
    return IMPLEMENTED_SOURCE_CONNECTORS.get(source_registry_id)


def source_connector_inventory_entries(
    source_registry_id: str,
) -> tuple[SourceConnectorInventoryEntry, ...]:
    return tuple(
        entry
        for entry in IMPLEMENTED_SOURCE_CONNECTORS.values()
        if entry.source_registry_id == source_registry_id
    )


__all__ = [
    "DURABLE_LIVE_JOB",
    "IMMEDIATE_OPERATOR_API",
    "IMPLEMENTED_SOURCE_CONNECTORS",
    "REQUEST_TIME_ORCHESTRATION",
    "SourceConnectorInventoryEntry",
    "source_connector_inventory_entries",
    "source_connector_inventory_entry",
]
