from __future__ import annotations

import pytest

from app.connectors.license_guard import (
    ConnectorLicenseBlockedError,
    check_connector_source_license,
)
from app.domain.source_contracts import SourceContract


def _make_source(license_status: str) -> SourceContract:
    return SourceContract(name="Test Source", domain="flood", license_status=license_status)


class TestCheckConnectorSourceLicensePasses:
    def test_passes_for_allowed(self) -> None:
        source = _make_source("allowed")
        check_connector_source_license(source)  # must not raise

    def test_passes_for_allowed_with_attribution(self) -> None:
        source = _make_source("allowed_with_attribution")
        check_connector_source_license(source)

    def test_passes_for_review_required(self) -> None:
        source = _make_source("review_required")
        check_connector_source_license(source)

    def test_passes_for_unknown(self) -> None:
        source = _make_source("unknown")
        check_connector_source_license(source)

    def test_passes_for_unreviewed(self) -> None:
        source = _make_source("unreviewed")
        check_connector_source_license(source)


class TestCheckConnectorSourceLicenseBlocks:
    def test_raises_for_incompatible(self) -> None:
        source = _make_source("incompatible")
        with pytest.raises(ConnectorLicenseBlockedError):
            check_connector_source_license(source)

    def test_raises_for_unknown_blocking(self) -> None:
        source = _make_source("unknown_blocking")
        with pytest.raises(ConnectorLicenseBlockedError):
            check_connector_source_license(source)

    def test_error_attributes_incompatible(self) -> None:
        source = _make_source("incompatible")
        with pytest.raises(ConnectorLicenseBlockedError) as exc_info:
            check_connector_source_license(source)
        err = exc_info.value
        assert err.source_id == source.source_id
        assert err.license_status == "incompatible"

    def test_error_attributes_unknown_blocking(self) -> None:
        source = _make_source("unknown_blocking")
        with pytest.raises(ConnectorLicenseBlockedError) as exc_info:
            check_connector_source_license(source)
        err = exc_info.value
        assert err.source_id == source.source_id
        assert err.license_status == "unknown_blocking"


class TestConnectorLicenseBlockedErrorIsException:
    def test_is_subclass_of_exception(self) -> None:
        assert issubclass(ConnectorLicenseBlockedError, Exception)

    def test_instance_is_exception(self) -> None:
        source = _make_source("incompatible")
        err = ConnectorLicenseBlockedError(
            source_id=source.source_id, license_status="incompatible"
        )
        assert isinstance(err, Exception)
