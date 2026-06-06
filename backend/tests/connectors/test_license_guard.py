from __future__ import annotations

import pytest

from app.connectors.license_guard import (
    ConnectorLicenseBlockedError,
    check_connector_source_license,
)
from app.domain.source_contracts import SourceContract


def _make_source(
    license_status: str = "approved",
    *,
    review_status: str = "approved",
    commercial_use_status: str = "yes",
    redistribution_status: str = "restricted",
    cache_allowed: str = "yes",
    export_allowed: str = "approved-with-restrictions",
    raw_data_allowed: str = "allowed",
    ai_use_allowed: str = "restricted",
) -> SourceContract:
    return SourceContract(
        name="Test Source",
        domain="flood",
        license_status=license_status,
        review_status=review_status,
        commercial_use_status=commercial_use_status,
        redistribution_status=redistribution_status,
        cache_allowed=cache_allowed,
        export_allowed=export_allowed,
        raw_data_allowed=raw_data_allowed,
        ai_use_allowed=ai_use_allowed,
    )


class TestCheckConnectorSourceLicensePasses:
    def test_passes_for_approved_source(self) -> None:
        source = _make_source("approved")
        check_connector_source_license(source)  # must not raise

    def test_passes_for_approved_with_restrictions(self) -> None:
        source = _make_source(
            "approved-with-restrictions",
            export_allowed="approved-with-restrictions",
        )
        check_connector_source_license(source)

    def test_passes_for_restricted_usage_rights(self) -> None:
        source = _make_source(
            redistribution_status="restricted",
            ai_use_allowed="restricted",
        )
        check_connector_source_license(source)  # must not raise

    def test_passes_for_case_insensitive_statuses(self) -> None:
        source = _make_source("Approved", review_status="Approved")
        check_connector_source_license(source)  # must not raise


class TestCheckConnectorSourceLicenseBlocks:
    @pytest.mark.parametrize(
        "license_status",
        ["blocked", "incompatible", "unknown", "unknown_blocking", "unreviewed"],
    )
    def test_raises_for_blocked_or_unknown_license(self, license_status: str) -> None:
        source = _make_source(license_status)
        with pytest.raises(ConnectorLicenseBlockedError) as exc_info:
            check_connector_source_license(source)
        err = exc_info.value
        assert err.source_id == source.source_id
        assert err.license_status == license_status
        assert err.blocked_fields == ("license_status",)

    def test_raises_for_unapproved_review_status(self) -> None:
        source = _make_source(review_status="pending")
        with pytest.raises(ConnectorLicenseBlockedError) as exc_info:
            check_connector_source_license(source)

        assert exc_info.value.blocked_fields == ("review_status",)

    @pytest.mark.parametrize(
        ("field_name", "blocked_value"),
        [
            ("commercial_use_status", "blocked"),
            ("redistribution_status", "unknown"),
            ("cache_allowed", "blocked"),
            ("export_allowed", "unknown"),
            ("raw_data_allowed", "blocked"),
            ("ai_use_allowed", "unknown"),
        ],
    )
    def test_raises_for_unknown_or_blocked_usage_rights(
        self,
        field_name: str,
        blocked_value: str,
    ) -> None:
        source = _make_source().model_copy(update={field_name: blocked_value})
        with pytest.raises(ConnectorLicenseBlockedError) as exc_info:
            check_connector_source_license(source)

        assert exc_info.value.blocked_fields == (field_name,)


class TestConnectorLicenseBlockedErrorIsException:
    def test_is_subclass_of_exception(self) -> None:
        assert issubclass(ConnectorLicenseBlockedError, Exception)

    def test_instance_is_exception(self) -> None:
        source = _make_source("blocked")
        err = ConnectorLicenseBlockedError(
            source_id=source.source_id,
            license_status="blocked",
            blocked_fields=("license_status",),
        )
        assert isinstance(err, Exception)
