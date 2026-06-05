from __future__ import annotations

import pytest

from app.connectors.policy import DEFAULT_FIXTURE_POLICY, ConnectorPolicy


class TestConnectorPolicyDefaults:
    def test_valid_default_creation(self) -> None:
        policy = ConnectorPolicy()
        assert policy.rate_limit_per_minute == 0
        assert policy.timeout_seconds == 30.0
        assert policy.max_retries == 3
        assert policy.retry_backoff_seconds == 1.0

    def test_valid_explicit_values(self) -> None:
        policy = ConnectorPolicy(
            rate_limit_per_minute=60,
            timeout_seconds=10.0,
            max_retries=5,
            retry_backoff_seconds=2.5,
        )
        assert policy.rate_limit_per_minute == 60
        assert policy.timeout_seconds == 10.0
        assert policy.max_retries == 5
        assert policy.retry_backoff_seconds == 2.5


class TestConnectorPolicyValidation:
    def test_negative_rate_limit_raises(self) -> None:
        with pytest.raises(ValueError, match="rate_limit_per_minute"):
            ConnectorPolicy(rate_limit_per_minute=-1)

    def test_negative_timeout_raises(self) -> None:
        with pytest.raises(ValueError, match="timeout_seconds"):
            ConnectorPolicy(timeout_seconds=-0.1)

    def test_negative_max_retries_raises(self) -> None:
        with pytest.raises(ValueError, match="max_retries"):
            ConnectorPolicy(max_retries=-1)

    def test_negative_retry_backoff_raises(self) -> None:
        with pytest.raises(ValueError, match="retry_backoff_seconds"):
            ConnectorPolicy(retry_backoff_seconds=-1.0)

    def test_zero_values_are_valid(self) -> None:
        policy = ConnectorPolicy(
            rate_limit_per_minute=0,
            timeout_seconds=0.0,
            max_retries=0,
            retry_backoff_seconds=0.0,
        )
        assert policy.rate_limit_per_minute == 0
        assert policy.timeout_seconds == 0.0
        assert policy.max_retries == 0
        assert policy.retry_backoff_seconds == 0.0


class TestDefaultFixturePolicy:
    def test_expected_values(self) -> None:
        assert DEFAULT_FIXTURE_POLICY.rate_limit_per_minute == 0
        assert DEFAULT_FIXTURE_POLICY.timeout_seconds == 5.0
        assert DEFAULT_FIXTURE_POLICY.max_retries == 0
        assert DEFAULT_FIXTURE_POLICY.retry_backoff_seconds == 0.0


class TestConnectorPolicyHashable:
    def test_is_hashable(self) -> None:
        policy = ConnectorPolicy()
        assert hash(policy) is not None

    def test_can_be_used_as_dict_key(self) -> None:
        policy = ConnectorPolicy(rate_limit_per_minute=10)
        d = {policy: "value"}
        assert d[policy] == "value"

    def test_can_be_added_to_set(self) -> None:
        p1 = ConnectorPolicy(rate_limit_per_minute=10)
        p2 = ConnectorPolicy(rate_limit_per_minute=10)
        p3 = ConnectorPolicy(rate_limit_per_minute=20)
        s = {p1, p2, p3}
        assert len(s) == 2
