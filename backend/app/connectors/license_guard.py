from __future__ import annotations

from app.domain.source_contracts import SourceContract
from app.source_registry.usage_rights import source_production_use_blocking_fields


class ConnectorLicenseBlockedError(Exception):
    """Raised when a connector run is blocked by source production-use rights."""

    def __init__(
        self,
        source_id: object,
        license_status: str,
        blocked_fields: tuple[str, ...],
    ) -> None:
        self.source_id = source_id
        self.license_status = license_status
        self.blocked_fields = blocked_fields
        super().__init__(
            f"connector run blocked: source {source_id} has "
            f"license_status={license_status!r}; blocked_fields={blocked_fields!r}"
        )


def check_connector_source_license(source: SourceContract) -> None:
    """Raise ConnectorLicenseBlockedError unless production source rights are approved."""
    blocked_fields = source_production_use_blocking_fields(source)
    if blocked_fields:
        raise ConnectorLicenseBlockedError(
            source_id=source.source_id,
            license_status=source.license_status,
            blocked_fields=blocked_fields,
        )


__all__ = ["ConnectorLicenseBlockedError", "check_connector_source_license"]
