from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceConnectorInventoryEntry:
    source_registry_id: str
    connector_name: str
    surfaces: tuple[str, ...]


IMMEDIATE_OPERATOR_API = "immediate_operator_api"
DURABLE_LIVE_JOB = "durable_live_job"
REQUEST_TIME_ORCHESTRATION = "request_time_orchestration"

IMPLEMENTED_SOURCE_CONNECTORS: dict[str, SourceConnectorInventoryEntry] = {
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
    ),
    "DS-023": SourceConnectorInventoryEntry(
        source_registry_id="DS-023",
        connector_name="chatham_zoning_udo_recorded",
        surfaces=(IMMEDIATE_OPERATOR_API, REQUEST_TIME_ORCHESTRATION),
    ),
}


def source_connector_inventory_entry(
    source_registry_id: str,
) -> SourceConnectorInventoryEntry | None:
    return IMPLEMENTED_SOURCE_CONNECTORS.get(source_registry_id)


__all__ = [
    "DURABLE_LIVE_JOB",
    "IMMEDIATE_OPERATOR_API",
    "IMPLEMENTED_SOURCE_CONNECTORS",
    "REQUEST_TIME_ORCHESTRATION",
    "SourceConnectorInventoryEntry",
    "source_connector_inventory_entry",
]
