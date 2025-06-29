"""Test cases for request customization features."""

from unittest.mock import Mock, call, patch

import requests

from httpcheck.common import parse_custom_headers
from httpcheck.site_checker import check_site


class TestCustomHeaders:
    """Test cases for custom HTTP headers."""

    def test_parse_custom_headers_valid(self):
        """Test parsing valid custom headers."""
        headers_list = [
            "Authorization: Bearer token123",
            "X-Custom-Header: value",
            "Accept: application/json",
        ]

        result = parse_custom_headers(headers_list)

        assert result == {
            "Authorization": "Bearer token123",
            "X-Custom-Header": "value",
            "Accept": "application/json",
        }

    def test_parse_custom_headers_with_colons_in_value(self):
        """Test parsing headers with colons in the value."""
        headers_list = ["Authorization: Bearer token:with:colons"]

        result = parse_custom_headers(headers_list)

        assert result == {"Authorization": "Bearer token:with:colons"}

    def test_parse_custom_headers_with_whitespace(self):
        """Test parsing headers with extra whitespace."""
        headers_list = ["  Content-Type  :  application/json  "]

        result = parse_custom_headers(headers_list)

        assert result == {"Content-Type": "application/json"}

    def test_parse_custom_headers_invalid(self):
        """Test parsing invalid header format."""
        headers_list = ["InvalidHeader", "Another-Invalid"]

        with patch("builtins.print") as mock_print:
            result = parse_custom_headers(headers_list)

            assert result is None
            assert (
                mock_print.call_count == 3
            )  # 1 validation warning + 2 format warnings
            # First call is the validation failure warning, subsequent calls are format warnings
            assert "Header validation failed" in str(mock_print.call_args_list[0])
            assert "Invalid header format" in str(mock_print.call_args_list[1])

    def test_parse_custom_headers_empty(self):
        """Test parsing empty headers list."""
        assert parse_custom_headers(None) is None
        assert parse_custom_headers([]) is None

    def test_check_site_with_custom_headers(self):
        """Test site checking with custom headers."""
        with patch("httpcheck.site_checker.requests.Session") as mock_session_class:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.history = []

            mock_session = Mock()
            mock_session.get.return_value = mock_response
            mock_session_class.return_value = mock_session

            custom_headers = {"Authorization": "Bearer token", "X-API-Key": "secret"}

            check_site("https://api.example.com", custom_headers=custom_headers)

            # Verify headers were passed
            call_args = mock_session.get.call_args
            headers = call_args[1]["headers"]
            assert "Authorization" in headers
            assert headers["Authorization"] == "Bearer token"
            assert "X-API-Key" in headers
            assert headers["X-API-Key"] == "secret"
            assert "User-Agent" in headers  # Default header should still be there


class TestSSLVerification:
    """Test cases for SSL verification options."""

    def test_ssl_verification_enabled(self):
        """Test site checking with SSL verification enabled (default)."""
        with patch("httpcheck.site_checker.requests.Session") as mock_session_class:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.history = []

            mock_session = Mock()
            mock_session.get.return_value = mock_response
            mock_session_class.return_value = mock_session

            result = check_site("https://example.com", verify_ssl=True)

            assert mock_session.verify is True
            assert result.status == "200"

    def test_ssl_verification_disabled(self):
        """Test site checking with SSL verification disabled."""
        with patch("httpcheck.site_checker.requests.Session") as mock_session_class:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.history = []

            mock_session = Mock()
            mock_session.get.return_value = mock_response
            mock_session_class.return_value = mock_session

            result = check_site("https://self-signed.example.com", verify_ssl=False)

            assert mock_session.verify is False
            assert result.status == "200"

    def test_ssl_error_with_verification_disabled(self):
        """Test SSL error handling when verification is disabled."""
        with patch("httpcheck.site_checker.requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session.get.side_effect = requests.RequestException(
                "SSL: CERTIFICATE_VERIFY_FAILED"
            )
            mock_session_class.return_value = mock_session

            result = check_site(
                "https://bad-ssl.example.com", verify_ssl=False, retries=0
            )

            assert result.status == "[request error]"
            assert "SSL verification disabled" in result.message
            assert "SSL: CERTIFICATE_VERIFY_FAILED" in result.message


class TestRetryConfiguration:
    """Test cases for retry configuration."""

    def test_retry_delay_applied(self):
        """Test that retry delay is applied between attempts."""
        with patch("httpcheck.site_checker.requests.Session") as mock_session_class:
            with patch("httpcheck.site_checker.time.sleep") as mock_sleep:
                mock_session = Mock()
                # Fail twice, then succeed
                mock_session.get.side_effect = [
                    requests.ConnectionError("Connection failed"),
                    requests.Timeout("Timeout"),
                    Mock(status_code=200, history=[]),
                ]
                mock_session_class.return_value = mock_session

                result = check_site(
                    "https://flaky.example.com", retries=2, retry_delay=2.5
                )

                assert result.status == "200"
                assert mock_sleep.call_count == 2
                mock_sleep.assert_has_calls([call(2.5), call(2.5)])

    def test_no_retry_delay(self):
        """Test retries with zero delay."""
        with patch("httpcheck.site_checker.requests.Session") as mock_session_class:
            with patch("httpcheck.site_checker.time.sleep") as mock_sleep:
                mock_session = Mock()
                mock_session.get.side_effect = [
                    requests.ConnectionError("Connection failed"),
                    Mock(status_code=200, history=[]),
                ]
                mock_session_class.return_value = mock_session

                result = check_site("https://example.com", retries=1, retry_delay=0)

                assert result.status == "200"
                assert mock_sleep.call_count == 0

    def test_retry_with_different_exceptions(self):
        """Test retry behavior with different exception types."""
        with patch("httpcheck.site_checker.requests.Session") as mock_session_class:
            with patch("httpcheck.site_checker.time.sleep") as mock_sleep:
                mock_session = Mock()
                mock_session.get.side_effect = [
                    requests.Timeout("Timeout"),
                    requests.ConnectionError("Connection error"),
                    requests.RequestException("General error"),
                    Mock(status_code=200, history=[]),
                ]
                mock_session_class.return_value = mock_session

                result = check_site("https://example.com", retries=3, retry_delay=0.5)

                assert result.status == "200"
                assert mock_sleep.call_count == 3
                assert mock_session.get.call_count == 4


class TestTimeoutConfiguration:
    """Test cases for timeout configuration."""

    def test_custom_timeout(self):
        """Test site checking with custom timeout."""
        with patch("httpcheck.site_checker.requests.Session") as mock_session_class:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.history = []

            mock_session = Mock()
            mock_session.get.return_value = mock_response
            mock_session_class.return_value = mock_session

            check_site("https://slow.example.com", timeout=30.0)

            # Verify timeout was passed
            call_args = mock_session.get.call_args
            assert call_args[1]["timeout"] == 30.0

    def test_timeout_with_retries(self):
        """Test timeout is applied on each retry attempt."""
        with patch("httpcheck.site_checker.requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session.get.side_effect = [
                requests.Timeout("Timeout"),
                requests.Timeout("Timeout"),
                Mock(status_code=200, history=[]),
            ]
            mock_session_class.return_value = mock_session

            result = check_site("https://slow.example.com", timeout=2.0, retries=2)

            assert result.status == "200"
            # Check all calls used the same timeout
            for call_item in mock_session.get.call_args_list:
                assert call_item[1]["timeout"] == 2.0


class TestIntegration:
    """Integration tests for request customization features."""

    def test_all_customizations_together(self):
        """Test using all customization features together."""
        with patch("httpcheck.site_checker.requests.Session") as mock_session_class:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.history = []
            mock_response.is_redirect = False
            mock_response.headers = {}

            mock_session = Mock()
            mock_session.get.return_value = mock_response
            mock_session_class.return_value = mock_session

            custom_headers = {
                "Authorization": "Bearer token",
                "Accept": "application/json",
            }

            result = check_site(
                "https://api.example.com/endpoint",
                timeout=15.0,
                retries=3,
                retry_delay=2.0,
                custom_headers=custom_headers,
                verify_ssl=False,
                follow_redirects="always",
                max_redirects=5,
            )

            assert result.status == "200"

            # Verify session configuration
            assert mock_session.verify is False
            assert mock_session.max_redirects == 5

            # Verify request parameters
            call_args = mock_session.get.call_args
            headers = call_args[1]["headers"]
            assert headers["Authorization"] == "Bearer token"
            assert headers["Accept"] == "application/json"
            assert call_args[1]["timeout"] == 15.0

    def test_custom_headers_override_defaults(self):
        """Test that custom headers can override default headers."""
        with patch("httpcheck.site_checker.requests.Session") as mock_session_class:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.history = []

            mock_session = Mock()
            mock_session.get.return_value = mock_response
            mock_session_class.return_value = mock_session

            custom_headers = {"User-Agent": "Custom Agent 1.0"}

            check_site("https://example.com", custom_headers=custom_headers)

            call_args = mock_session.get.call_args
            headers = call_args[1]["headers"]
            assert headers["User-Agent"] == "Custom Agent 1.0"

    def test_http_error_not_retried(self):
        """Test that HTTP errors (4xx, 5xx) are not retried."""
        with patch("httpcheck.site_checker.requests.Session") as mock_session_class:
            with patch("httpcheck.site_checker.time.sleep") as mock_sleep:
                mock_response = Mock()
                mock_response.status_code = 404
                mock_response.history = []
                mock_response.is_redirect = False
                mock_response.headers = {}

                mock_session = Mock()
                mock_session.get.return_value = mock_response
                mock_session_class.return_value = mock_session

                result = check_site(
                    "https://example.com/notfound", retries=3, retry_delay=1.0
                )

                assert result.status == "404"
                assert mock_session.get.call_count == 1
                assert mock_sleep.call_count == 0
