"""
Tests for error_safety.py — covers the 5 leak vectors identified in PR #85.

Each test is labelled with the fix number it guards.
A regression suite at the bottom asserts existing good behavior still holds.
"""
from __future__ import annotations

from app.core.error_safety import (
    REDACTED_ERROR_MESSAGE,
    safe_error_message,
    safe_payload_copy,
    safe_url_summary,
)

# ---------------------------------------------------------------------------
# Fix 1 — /workspace/ path must be redacted
# ---------------------------------------------------------------------------

class TestFix1WorkspacePath:
    def test_workspace_path_in_error_is_redacted(self) -> None:
        msg = "could not open /workspace/land-dd/local_artifacts/source.json"
        result = safe_error_message(msg)
        assert result == REDACTED_ERROR_MESSAGE, (
            f"/workspace/ path leaked — got: {result!r}"
        )

    def test_workspace_path_mixed_case_is_redacted(self) -> None:
        msg = "Error reading /Workspace/land-dd/config.yaml"
        result = safe_error_message(msg)
        assert result == REDACTED_ERROR_MESSAGE, (
            f"/Workspace/ (mixed-case) path leaked — got: {result!r}"
        )


# ---------------------------------------------------------------------------
# Fix 2 — apikey= (no separator) must be redacted from error messages
# ---------------------------------------------------------------------------

class TestFix2ApikeyNoSeparator:
    def test_apikey_no_separator_is_redacted(self) -> None:
        msg = "request failed with apikey=raw-key-abc123"
        result = safe_error_message(msg)
        assert result == REDACTED_ERROR_MESSAGE, (
            f"apikey= leaked — got: {result!r}"
        )

    def test_apikey_camel_case_is_redacted(self) -> None:
        # apiKey lowercases to apikey, must also be caught
        msg = "request failed with apiKey=raw-key-abc123"
        result = safe_error_message(msg)
        assert result == REDACTED_ERROR_MESSAGE, (
            f"apiKey= leaked — got: {result!r}"
        )


# ---------------------------------------------------------------------------
# Fix 3 — safe_url_summary must strip userinfo and run path through marker check
# ---------------------------------------------------------------------------

class TestFix3SafeUrlSummaryUserinfo:
    def test_userinfo_stripped_from_url(self) -> None:
        url = "https://user:pass@example.test/live/api_key/raw-key?x=1"
        result = safe_url_summary(url)
        assert result is not None
        assert "user:pass" not in result, (
            f"userinfo leaked — got: {result!r}"
        )
        assert "pass" not in result, (
            f"password leaked — got: {result!r}"
        )

    def test_url_with_api_key_in_path_is_redacted(self) -> None:
        # After stripping userinfo, the path contains api_key — should still redact
        url = "https://user:pass@example.test/live/api_key/raw-key"
        result = safe_url_summary(url)
        assert result == REDACTED_ERROR_MESSAGE, (
            f"URL with api_key in path not redacted — got: {result!r}"
        )

    def test_userinfo_only_no_path_sensitivity_returns_clean_url(self) -> None:
        # Userinfo stripped; remaining URL is benign
        url = "https://user:pass@example.test/some/benign/path"
        result = safe_url_summary(url)
        assert result is not None
        assert "user:pass" not in result, (
            f"userinfo leaked in benign-path case — got: {result!r}"
        )
        # Should not contain the raw password
        assert "pass" not in result, (
            f"password leaked in benign-path case — got: {result!r}"
        )

    def test_query_params_stripped(self) -> None:
        url = "https://example.test/endpoint?geometry=POINT&where=1%3D1"
        result = safe_url_summary(url)
        assert result is not None
        assert "geometry" not in result, (
            f"query param leaked — got: {result!r}"
        )
        assert "where" not in result, (
            f"query param leaked — got: {result!r}"
        )


# ---------------------------------------------------------------------------
# Fix 4 — URL-shaped string values in payloads must be routed through safe_url_summary
# ---------------------------------------------------------------------------

class TestFix4UrlShapedPayloadValues:
    def test_url_value_query_params_not_leaked_in_payload_copy(self) -> None:
        payload = {
            "log_uri": "https://host.example/query?geometry=POINT&where=1%3D1&secret=x",
        }
        result = safe_payload_copy(payload)
        log_uri_val = result.get("log_uri")
        # Either the key is gone (redacted entirely) or the query string is stripped
        if log_uri_val is not None:
            assert "geometry" not in str(log_uri_val), (
                f"query param leaked in payload — got: {log_uri_val!r}"
            )
            assert "secret=x" not in str(log_uri_val), (
                f"secret leaked in URL value — got: {log_uri_val!r}"
            )

    def test_request_url_query_params_not_leaked(self) -> None:
        payload = {
            "request_url": "https://api.example.com/data?token=abc&geometry=POLYGON",
        }
        result = safe_payload_copy(payload)
        req_val = result.get("request_url")
        # token key is sensitive so the whole key may be dropped, but if retained:
        if req_val is not None:
            assert "token=abc" not in str(req_val), (
                f"token in URL query param leaked — got: {req_val!r}"
            )
            assert "geometry=POLYGON" not in str(req_val), (
                f"geometry query param leaked — got: {req_val!r}"
            )

    def test_benign_url_value_retained_without_query(self) -> None:
        payload = {
            "source_endpoint": "https://api.example.com/v1/parcels",
        }
        result = safe_payload_copy(payload)
        src_val = result.get("source_endpoint")
        # Base URL (scheme + host + path, no query) should be retained
        assert src_val is not None, "Benign URL value was incorrectly dropped"
        assert "api.example.com" in str(src_val), (
            f"Base URL not retained — got: {src_val!r}"
        )


# ---------------------------------------------------------------------------
# Fix 5 — camelCase payload keys must be caught by _is_sensitive_payload_key
# ---------------------------------------------------------------------------

class TestFix5CamelCasePayloadKeys:
    def test_apikey_camel_key_omitted_by_payload_copy(self) -> None:
        payload = {"apiKey": "raw-key-12345"}
        result = safe_payload_copy(payload)
        assert "apiKey" not in result, (
            f"apiKey not omitted — got: {result!r}"
        )

    def test_accesstoken_camel_key_omitted_by_payload_copy(self) -> None:
        payload = {"accessToken": "bearer-tok-xyz"}
        result = safe_payload_copy(payload)
        assert "accessToken" not in result, (
            f"accessToken not omitted — got: {result!r}"
        )

    def test_access_token_underscore_key_omitted(self) -> None:
        # Existing marker "token" already covers this but confirm explicitly
        payload = {"access_token": "bearer-tok-xyz"}
        result = safe_payload_copy(payload)
        assert "access_token" not in result, (
            f"access_token not omitted — got: {result!r}"
        )

    def test_api_key_underscore_key_omitted(self) -> None:
        payload = {"api_key": "raw-key-12345"}
        result = safe_payload_copy(payload)
        assert "api_key" not in result, (
            f"api_key not omitted — got: {result!r}"
        )


# ---------------------------------------------------------------------------
# Regression — existing good (benign) behavior must still pass through
# ---------------------------------------------------------------------------

class TestRegressionBenignPassthrough:
    def test_benign_error_message_unchanged(self) -> None:
        msg = "source returned HTTP 404"
        result = safe_error_message(msg)
        assert result == "source returned HTTP 404"

    def test_none_message_returns_none(self) -> None:
        assert safe_error_message(None) is None

    def test_empty_message_returns_none(self) -> None:
        assert safe_error_message("") is None
        assert safe_error_message("   ") is None

    def test_long_message_truncated(self) -> None:
        msg = "x" * 300
        result = safe_error_message(msg)
        assert result is not None
        assert len(result) <= 240

    def test_benign_payload_keys_retained(self) -> None:
        payload = {
            "status": "ok",
            "record_count": 42,
            "enabled": True,
            "source_name": "usgs_nlcd",
        }
        result = safe_payload_copy(payload)
        assert result["status"] == "ok"
        assert result["record_count"] == 42
        assert result["enabled"] is True
        assert result["source_name"] == "usgs_nlcd"

    def test_benign_url_no_userinfo_retained(self) -> None:
        url = "https://example.com/api/v1/parcels"
        result = safe_url_summary(url)
        assert result == "https://example.com/api/v1/parcels"

    def test_existing_local_path_markers_still_redact(self) -> None:
        # /home/ and /app/ are existing markers — must not regress
        assert safe_error_message("/home/user/secrets.txt") == REDACTED_ERROR_MESSAGE
        assert safe_error_message("error in /app/server.py") == REDACTED_ERROR_MESSAGE

    def test_existing_error_markers_still_redact(self) -> None:
        assert safe_error_message("authorization: Bearer tok") == REDACTED_ERROR_MESSAGE
        assert safe_error_message("password=hunter2") == REDACTED_ERROR_MESSAGE


# ---------------------------------------------------------------------------
# Guard G1 — safe_url_summary must NEVER raise (malformed / out-of-range port)
# ---------------------------------------------------------------------------

class TestGuardG1NeverRaises:
    def test_malformed_port_does_not_raise(self) -> None:
        # urlsplit("https://host:notaport/x") raises ValueError in some Pythons;
        # .port access raises ValueError for out-of-range (e.g. port 99999).
        # safe_url_summary must catch all of these and return REDACTED_ERROR_MESSAGE.
        result = safe_url_summary("https://host:notaport/x")
        assert result == REDACTED_ERROR_MESSAGE, (
            f"malformed port did not return REDACTED — got: {result!r}"
        )

    def test_out_of_range_port_does_not_raise(self) -> None:
        result = safe_url_summary("https://host:99999/x")
        assert result == REDACTED_ERROR_MESSAGE, (
            f"out-of-range port did not return REDACTED — got: {result!r}"
        )

    def test_invalid_ipv6_url_does_not_raise(self) -> None:
        # urlsplit raises ValueError: "Invalid IPv6 URL" for malformed brackets.
        result = safe_url_summary("https://[::1/x")
        assert result == REDACTED_ERROR_MESSAGE, (
            f"invalid IPv6 URL raised or leaked — got: {result!r}"
        )

    def test_none_still_returns_none(self) -> None:
        assert safe_url_summary(None) is None

    def test_empty_still_returns_none(self) -> None:
        assert safe_url_summary("") is None


# ---------------------------------------------------------------------------
# Guard G2 — IPv6 host must round-trip without corruption
# ---------------------------------------------------------------------------

class TestGuardG2IPv6HostRoundTrip:
    def test_ipv6_literal_host_not_corrupted(self) -> None:
        # parsed.hostname strips [], so naïve reconstruction yields
        # "https://2001:db8::1:8443/x" — a colon-ambiguous broken URL.
        # The fixed code must re-wrap the host in [...].
        url = "https://[2001:db8::1]:8443/x"
        result = safe_url_summary(url)
        assert result is not None
        assert result != REDACTED_ERROR_MESSAGE, (
            f"benign IPv6 URL wrongly redacted — got: {result!r}"
        )
        # The reconstructed URL must be re-parseable and yield the same host.
        from urllib.parse import urlsplit as _us
        reparsed = _us(result)
        assert reparsed.hostname == "2001:db8::1", (
            f"IPv6 host corrupted in output — got hostname: {reparsed.hostname!r} from {result!r}"
        )
        assert reparsed.port == 8443, (
            f"IPv6 port wrong — got: {reparsed.port!r} from {result!r}"
        )

    def test_ipv6_no_port_benign_round_trips(self) -> None:
        url = "https://[::1]/path"
        result = safe_url_summary(url)
        assert result is not None
        assert result != REDACTED_ERROR_MESSAGE, (
            f"benign IPv6 no-port URL wrongly redacted — got: {result!r}"
        )
        from urllib.parse import urlsplit as _us
        reparsed = _us(result)
        assert reparsed.hostname == "::1", (
            f"IPv6 loopback host corrupted — got: {reparsed.hostname!r} from {result!r}"
        )


# ---------------------------------------------------------------------------
# Guard G3 — userinfo must be stripped for scheme-relative and non-http(s) URLs
# ---------------------------------------------------------------------------

class TestGuardG3UserinfoBroadStrip:
    def test_scheme_relative_userinfo_does_not_leak(self) -> None:
        # "//user:pass@host/p" — no scheme, has netloc after urlsplit
        result = safe_url_summary("//user:pass@host/p")
        assert result is not None
        assert "pass" not in str(result), (
            f"password leaked from scheme-relative URL — got: {result!r}"
        )
        assert "user:pass" not in str(result), (
            f"userinfo leaked from scheme-relative URL — got: {result!r}"
        )

    def test_no_scheme_no_netloc_userinfo_does_not_leak(self) -> None:
        # "user:pass@host/p" — urlsplit gives scheme="user", path="pass@host/p"
        # The fallback safe_error_message path must catch the "@" or "pass" portion.
        result = safe_url_summary("user:pass@host/p")
        # Either REDACTED or a value with no "pass" in it
        if result != REDACTED_ERROR_MESSAGE:
            assert "pass" not in str(result), (
                f"password leaked from bare user:pass@host — got: {result!r}"
            )

    def test_ftp_userinfo_does_not_leak(self) -> None:
        result = safe_url_summary("ftp://user:secret@files.example.com/pub")
        assert result is not None
        assert "secret" not in str(result), (
            f"password leaked from ftp:// URL — got: {result!r}"
        )
        assert "user:secret" not in str(result), (
            f"userinfo leaked from ftp:// URL — got: {result!r}"
        )

    def test_ftp_url_in_payload_does_not_leak_creds(self) -> None:
        # _safe_payload_value only routed http/https; ftp:// must also be routed.
        from app.core.error_safety import safe_payload_copy
        payload = {"endpoint": "ftp://admin:hunter2@files.internal/data"}
        result = safe_payload_copy(payload)
        val = result.get("endpoint")
        if val is not None:
            assert "hunter2" not in str(val), (
                f"ftp password leaked in payload — got: {val!r}"
            )

    def test_scheme_relative_url_in_payload_does_not_leak_creds(self) -> None:
        from app.core.error_safety import safe_payload_copy
        payload = {"link": "//user:pass@host/p"}
        result = safe_payload_copy(payload)
        val = result.get("link")
        if val is not None:
            assert "pass" not in str(val), (
                f"password leaked from scheme-relative URL in payload — got: {val!r}"
            )


# ---------------------------------------------------------------------------
# Guard G4 — private_key / passwd / credential markers
# ---------------------------------------------------------------------------

class TestGuardG4AdditionalMarkers:
    def test_private_key_in_error_is_redacted(self) -> None:
        msg = "could not load private_key from vault"
        result = safe_error_message(msg)
        assert result == REDACTED_ERROR_MESSAGE, (
            f"private_key not redacted — got: {result!r}"
        )

    def test_privatekey_camel_in_error_is_redacted(self) -> None:
        msg = "privateKey=BEGIN RSA PRIVATE KEY"
        result = safe_error_message(msg)
        assert result == REDACTED_ERROR_MESSAGE, (
            f"privateKey not redacted — got: {result!r}"
        )

    def test_passwd_in_error_is_redacted(self) -> None:
        msg = "passwd=abc123"
        result = safe_error_message(msg)
        assert result == REDACTED_ERROR_MESSAGE, (
            f"passwd not redacted — got: {result!r}"
        )

    def test_credential_in_error_is_redacted(self) -> None:
        msg = "invalid credential for user admin"
        result = safe_error_message(msg)
        assert result == REDACTED_ERROR_MESSAGE, (
            f"credential not redacted — got: {result!r}"
        )

    def test_private_key_payload_key_omitted(self) -> None:
        from app.core.error_safety import safe_payload_copy
        payload = {"private_key": "BEGIN RSA PRIVATE KEY..."}
        result = safe_payload_copy(payload)
        assert "private_key" not in result, (
            f"private_key key not omitted from payload — got: {result!r}"
        )

    def test_passwd_payload_key_omitted(self) -> None:
        from app.core.error_safety import safe_payload_copy
        payload = {"passwd": "hunter2"}
        result = safe_payload_copy(payload)
        assert "passwd" not in result, (
            f"passwd key not omitted from payload — got: {result!r}"
        )

    def test_credential_payload_key_omitted(self) -> None:
        from app.core.error_safety import safe_payload_copy
        payload = {"credential": "some-cred-value"}
        result = safe_payload_copy(payload)
        assert "credential" not in result, (
            f"credential key not omitted from payload — got: {result!r}"
        )
