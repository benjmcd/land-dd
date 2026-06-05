from __future__ import annotations

from app.domain.source_contracts import SourceContract

# License status values that block connector runs
_BLOCKING_STATUSES: frozenset[str] = frozenset({"incompatible", "unknown_blocking"})


class ConnectorLicenseBlockedError(Exception):
    """Raised when a connector run is blocked by incompatible or unknown-blocking license status."""

    def __init__(self, source_id: object, license_status: str) -> None:
        self.source_id = source_id
        self.license_status = license_status
        super().__init__(
            f"connector run blocked: source {source_id} has license_status={license_status!r}"
        )


def check_connector_source_license(source: SourceContract) -> None:
    """Raise ConnectorLicenseBlockedError if the source license blocks production use.

    Passes silently for: allowed, allowed_with_attribution, review_required, unknown, unreviewed.
    Raises for: incompatible, unknown_blocking.
    """
    if source.license_status in _BLOCKING_STATUSES:
        raise ConnectorLicenseBlockedError(
            source_id=source.source_id,
            license_status=source.license_status,
        )


__all__ = ["ConnectorLicenseBlockedError", "check_connector_source_license"]
