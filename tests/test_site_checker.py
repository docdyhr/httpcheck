"""Test cases for the site_checker module."""

from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

from httpcheck.common import VERSION, SiteStatus
from httpcheck.site_checker import (
    _create_custom_headers,
    _handle_request_exception,
    _should_stop_redirect,
    check_site,
)


class TestSiteChecker:
    """Test cases for the check_site function."""

    def test_check_site_success(self):
        """Test successful site check."""
        with patch("httpcheck.site_checker.requests.Session") as mock_session_class:
            # Create mock response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.raise_for_status = Mock()
            mock_response.history = []

            # Create mock session
            mock_session = Mock()
            mock_session.get.return_value = mock_response
            mock_session_class.return_value = mock_session

            result = check_site("https://example.com")

            assert isinstance(result, SiteStatus)
            assert result.domain == "example.com"
            assert result.status == "200"
            assert result.message == "OK"
            assert result.redirect_chain == []

    def test_check_site_with_timeout(self):
        """Test site check with custom timeout."""
        with patch("httpcheck.site_checker.requests.Session") as mock_session_class:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.history = []

            mock_session = Mock()
            mock_session.get.return_value = mock_response
            mock_session_class.return_value = mock_session

            result = check_site("https://example.com", timeout=5)

            # Verify timeout was passed (with headers)
            mock_session.get.assert_called_with(
                "https://example.com",
                headers={"User-Agent": f"httpcheck Agent {VERSION}"},
                timeout=5,
                allow_redirects=True,
            )

    def test_check_site_connection_error(self):
        """Test site check with connection error."""
        with patch("httpcheck.site_checker.requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session.get.side_effect = requests.ConnectionError("Connection failed")
            mock_session_class.return_value = mock_session

            result = check_site("https://unreachable.example.com")

            assert result.status == "[connection error]"
            assert result.message == "Connection failed"
            assert result.response_time == 0.0

    def test_check_site_timeout_error(self):
        """Test site check with timeout error."""
        with patch("httpcheck.site_checker.requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session.get.side_effect = requests.Timeout("Request timed out")
            mock_session_class.return_value = mock_session

            result = check_site("https://slow.example.com")

            assert result.status == "[timeout]"
            assert result.message == "Request timed out"

    def test_check_site_with_retries(self):
        """Test site check with retries on failure."""
        with patch("httpcheck.site_checker.requests.Session") as mock_session_class:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.history = []

            mock_session = Mock()
            # Fail twice, then succeed
            mock_session.get.side_effect = [
                requests.ConnectionError("Connection failed"),
                requests.ConnectionError("Connection failed"),
                mock_response,
            ]
            mock_session_class.return_value = mock_session

            result = check_site("https://flaky.example.com", retries=2)

            assert result.status == "200"
            assert result.message == "OK"
            assert mock_session.get.call_count == 3

    def test_check_site_http_only_redirects(self):
        """Test site check with http-only redirect following."""
        with patch("httpcheck.site_checker.requests.Session") as mock_session_class:
            # Create mock responses
            response1 = Mock()
            response1.status_code = 301
            response1.is_redirect = True
            response1.headers = {"location": "http://example.com/page"}
            response1.url = "http://example.com"

            response2 = Mock()
            response2.status_code = 301
            response2.is_redirect = True
            response2.headers = {"location": "https://example.com/page"}
            response2.url = "http://example.com/page"

            # Mock session
            mock_session = Mock()
            original_get = Mock()
            original_get.side_effect = [response1, response2]
            mock_session.get = original_get
            mock_session_class.return_value = mock_session

            # Need to patch datetime for timing
            with patch("httpcheck.site_checker.datetime") as mock_datetime:
                mock_datetime.now.return_value = datetime(2024, 1, 1, 10, 0, 0)

                result = check_site("http://example.com", follow_redirects="http-only")

                # Should stop at HTTPS redirect
                assert result.status == "301"
                assert len(result.redirect_chain) == 1
                assert result.redirect_chain[0] == ("http://example.com", 301)

    def test_check_site_https_only_redirects(self):
        """Test site check with https-only redirect following."""
        with patch("httpcheck.site_checker.requests.Session") as mock_session_class:
            # Create mock responses
            response1 = Mock()
            response1.status_code = 301
            response1.is_redirect = True
            response1.headers = {"location": "https://secure.example.com"}
            response1.url = "https://example.com"

            response2 = Mock()
            response2.status_code = 301
            response2.is_redirect = True
            response2.headers = {"location": "http://example.com/insecure"}
            response2.url = "https://secure.example.com"

            # Mock session
            mock_session = Mock()
            original_get = Mock()
            original_get.side_effect = [response1, response2]
            mock_session.get = original_get
            mock_session_class.return_value = mock_session

            with patch("httpcheck.site_checker.datetime") as mock_datetime:
                mock_datetime.now.return_value = datetime(2024, 1, 1, 10, 0, 0)

                result = check_site(
                    "https://example.com", follow_redirects="https-only"
                )

                # Should stop at HTTP redirect
                assert result.status == "301"
                assert len(result.redirect_chain) == 1

    def test_check_site_never_follow_redirects(self):
        """Test site check with redirect following disabled."""
        with patch("httpcheck.site_checker.requests.Session") as mock_session_class:
            mock_response = Mock()
            mock_response.status_code = 301
            mock_response.headers = {"location": "https://example.com/new"}
            mock_response.history = []
            mock_response.url = Mock()  # Add url attribute

            mock_session = Mock()
            mock_session.get.return_value = mock_response
            mock_session_class.return_value = mock_session

            result = check_site("https://example.com/old", follow_redirects="never")

            assert result.status == "301"
            # When follow_redirects="never", redirect_chain might still be populated from response
            # if the response has a url attribute

            # Verify allow_redirects=False was used
            mock_session.get.assert_called_with(
                "https://example.com/old",
                headers={"User-Agent": f"httpcheck Agent {VERSION}"},
                timeout=5.0,
                allow_redirects=False,
            )

    def test_check_site_max_redirects(self):
        """Test site check with max redirects limit."""
        with patch("httpcheck.site_checker.requests.Session") as mock_session_class:
            # Create a redirect loop
            responses = []
            for i in range(5):
                response = Mock()
                response.status_code = 301
                response.is_redirect = True
                response.headers = {"location": f"http://example.com/page{i + 1}"}
                response.url = f"http://example.com/page{i}"
                responses.append(response)

            mock_session = Mock()
            original_get = Mock()
            original_get.side_effect = responses
            mock_session.get = original_get
            mock_session_class.return_value = mock_session

            with patch("httpcheck.site_checker.datetime") as mock_datetime:
                mock_datetime.now.return_value = datetime(2024, 1, 1, 10, 0, 0)

                result = check_site(
                    "http://example.com/page0",
                    follow_redirects="http-only",
                    max_redirects=3,
                )

                # Should stop after 3 redirects
                assert len(result.redirect_chain) == 3

    def test_check_site_redirect_timing(self):
        """Test site check captures redirect timing."""
        with patch("httpcheck.site_checker.requests.Session") as mock_session_class:
            with patch("httpcheck.site_checker.datetime") as mock_datetime:
                # Mock datetime for timing
                times = [
                    datetime(2024, 1, 1, 10, 0, 0),
                    datetime(2024, 1, 1, 10, 0, 1),
                    datetime(2024, 1, 1, 10, 0, 2),
                    datetime(2024, 1, 1, 10, 0, 3),
                    datetime(2024, 1, 1, 10, 0, 4),
                    datetime(2024, 1, 1, 10, 0, 5),
                ]
                mock_datetime.now.side_effect = times

                # Create redirect responses
                response1 = Mock()
                response1.status_code = 301
                response1.is_redirect = True
                response1.headers = {"location": "http://example.com/page2"}
                response1.url = "http://example.com/page1"

                response2 = Mock()
                response2.status_code = 200
                response2.is_redirect = False
                response2.url = "http://example.com/page2"
                response2.history = []

                mock_session = Mock()
                original_get = Mock()
                original_get.side_effect = [response1, response2]
                mock_session.get = original_get
                mock_session_class.return_value = mock_session

                result = check_site(
                    "http://example.com/page1", follow_redirects="http-only"
                )

                # Check timing was captured
                assert len(result.redirect_timing) == 1
                assert result.redirect_timing[0][0] == "http://example.com/page2"
                assert result.redirect_timing[0][1] == 200
                assert result.redirect_timing[0][2] == 1.0  # 1 second

    def test_check_site_http_error(self):
        """Test site check with HTTP error status."""
        with patch("httpcheck.site_checker.requests.Session") as mock_session_class:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = requests.HTTPError(
                response=mock_response
            )
            mock_response.history = []

            mock_session = Mock()
            mock_session.get.return_value = mock_response
            mock_session_class.return_value = mock_session

            result = check_site("https://example.com/notfound")

            assert result.status == "404"
            # For 404, the message should be "Not Found" from STATUS_CODES
            assert result.message == "Not Found"

    def test_check_site_request_exception(self):
        """Test site check with general request exception."""
        with patch("httpcheck.site_checker.requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session.get.side_effect = requests.RequestException("General error")
            mock_session_class.return_value = mock_session

            result = check_site("https://example.com")

            assert result.status == "[request error]"
            assert result.message == "Request failed"

    def test_check_site_ssl_error(self):
        """Test site check with SSL error."""
        with patch("httpcheck.site_checker.requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session.get.side_effect = requests.exceptions.SSLError(
                "SSL certificate error"
            )
            mock_session_class.return_value = mock_session

            result = check_site("https://self-signed.example.com")

            # SSLError is a subclass of ConnectionError
            assert result.status == "[connection error]"
            assert result.message == "Connection failed"

    def test_check_site_redirect_with_relative_url(self):
        """Test site check with relative URL in redirect."""
        with patch("httpcheck.site_checker.requests.Session") as mock_session_class:
            response1 = Mock()
            response1.status_code = 301
            response1.is_redirect = True
            response1.headers = {"location": "/newpath"}
            response1.url = "http://example.com/oldpath"

            response2 = Mock()
            response2.status_code = 200
            response2.is_redirect = False
            response2.history = []

            mock_session = Mock()
            original_get = Mock()
            original_get.side_effect = [response1, response2]
            mock_session.get = original_get
            mock_session_class.return_value = mock_session

            with patch("httpcheck.site_checker.datetime") as mock_datetime:
                mock_datetime.now.return_value = datetime(2024, 1, 1, 10, 0, 0)

                result = check_site(
                    "http://example.com/oldpath", follow_redirects="http-only"
                )

                # Should handle relative redirect
                assert result.status == "200"

    def test_check_site_empty_redirect_location(self):
        """Test site check with empty redirect location."""
        with patch("httpcheck.site_checker.requests.Session") as mock_session_class:
            response = Mock()
            response.status_code = 301
            response.is_redirect = True
            response.headers = {}  # No location header
            response.url = "http://example.com"
            response.history = []

            mock_session = Mock()
            mock_session.get.return_value = response
            mock_session_class.return_value = mock_session

            result = check_site("http://example.com", follow_redirects="http-only")

            # Should handle missing location gracefully
            assert result.status == "301"
            assert result.redirect_chain == []

    def test_check_site_404_status(self):
        """Test site check with 404 status code."""
        with patch("httpcheck.site_checker.requests.Session") as mock_session_class:
            mock_response = Mock()
            mock_response.status_code = 404
            # 404 doesn't raise by default in requests
            mock_response.raise_for_status = Mock()
            mock_response.history = []

            mock_session = Mock()
            mock_session.get.return_value = mock_response
            mock_session_class.return_value = mock_session

            result = check_site("https://example.com/notfound")

            assert result.status == "404"
            assert result.message == "Not Found"

    def test_check_site_500_status(self):
        """Test site check with 500 status code."""
        with patch("httpcheck.site_checker.requests.Session") as mock_session_class:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.raise_for_status = Mock()
            mock_response.history = []

            mock_session = Mock()
            mock_session.get.return_value = mock_response
            mock_session_class.return_value = mock_session

            result = check_site("https://example.com/error")

            assert result.status == "500"
            assert result.message == "Internal Server Error"

    def test_check_site_unknown_status_code(self):
        """Test site check with unknown status code."""
        with patch("httpcheck.site_checker.requests.Session") as mock_session_class:
            mock_response = Mock()
            mock_response.status_code = 999
            mock_response.raise_for_status = Mock()
            mock_response.history = []

            mock_session = Mock()
            mock_session.get.return_value = mock_response
            mock_session_class.return_value = mock_session

            result = check_site("https://example.com")

            assert result.status == "999"
            assert result.message == "Unknown"

    def test_check_site_all_retries_fail(self):
        """Test site check when all retries fail."""
        with patch("httpcheck.site_checker.requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session.get.side_effect = requests.ConnectionError("Connection failed")
            mock_session_class.return_value = mock_session

            result = check_site("https://broken.example.com", retries=2)

            assert result.status == "[connection error]"
            assert result.message == "Connection failed"
            assert mock_session.get.call_count == 3  # Initial + 2 retries

    def test_check_site_with_custom_headers(self):
        """Test site check with custom headers."""
        with patch("httpcheck.site_checker.requests.Session") as mock_session_class:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.history = []

            mock_session = Mock()
            mock_session.get.return_value = mock_response
            mock_session_class.return_value = mock_session

            custom_headers = {
                "Authorization": "Bearer token123",
                "X-Custom-Header": "custom-value",
            }

            result = check_site("https://example.com", custom_headers=custom_headers)

            expected_headers = {
                "User-Agent": f"httpcheck Agent {VERSION}",
                "Authorization": "Bearer token123",
                "X-Custom-Header": "custom-value",
            }

            mock_session.get.assert_called_with(
                "https://example.com",
                headers=expected_headers,
                timeout=5.0,
                allow_redirects=True,
            )
            assert result.status == "200"

    def test_check_site_with_ssl_verification_disabled(self):
        """Test site check with SSL verification disabled."""
        with patch("httpcheck.site_checker.requests.Session") as mock_session_class:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.history = []

            mock_session = Mock()
            mock_session.get.return_value = mock_response
            mock_session_class.return_value = mock_session

            result = check_site("https://example.com", verify_ssl=False)

            # Verify SSL verification was disabled on the session
            assert mock_session.verify is False
            assert result.status == "200"

    def test_check_site_with_ssl_error_and_verification_disabled(self):
        """Test site check with SSL error when verification is disabled."""
        with patch("httpcheck.site_checker.requests.Session") as mock_session_class:
            mock_session = Mock()
            ssl_error = requests.RequestException("SSL: CERTIFICATE_VERIFY_FAILED")
            mock_session.get.side_effect = ssl_error
            mock_session_class.return_value = mock_session

            result = check_site(
                "https://badssl.example.com", verify_ssl=False, retries=0
            )

            assert result.status == "[request error]"
            assert "SSL verification disabled" in result.message

    def test_check_site_with_retry_delay(self):
        """Test site check with retry delay."""
        with (
            patch("httpcheck.site_checker.requests.Session") as mock_session_class,
            patch("httpcheck.site_checker.time.sleep") as mock_sleep,
        ):
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.history = []

            mock_session = Mock()
            # Fail once, then succeed
            mock_session.get.side_effect = [
                requests.ConnectionError("Connection failed"),
                mock_response,
            ]
            mock_session_class.return_value = mock_session

            result = check_site("https://flaky.example.com", retries=1, retry_delay=2.5)

            # Verify sleep was called with the correct delay
            mock_sleep.assert_called_once_with(2.5)
            assert result.status == "200"
            assert mock_session.get.call_count == 2

    def test_check_site_with_no_retry_delay(self):
        """Test site check with retry delay set to 0."""
        with (
            patch("httpcheck.site_checker.requests.Session") as mock_session_class,
            patch("httpcheck.site_checker.time.sleep") as mock_sleep,
        ):
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.history = []

            mock_session = Mock()
            # Fail once, then succeed
            mock_session.get.side_effect = [
                requests.ConnectionError("Connection failed"),
                mock_response,
            ]
            mock_session_class.return_value = mock_session

            result = check_site("https://flaky.example.com", retries=1, retry_delay=0.0)

            # Verify sleep was not called when retry_delay is 0
            mock_sleep.assert_not_called()
            assert result.status == "200"
            assert mock_session.get.call_count == 2

    def test_check_site_custom_headers_override_user_agent(self):
        """Test that custom headers can override the default User-Agent."""
        with patch("httpcheck.site_checker.requests.Session") as mock_session_class:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.history = []

            mock_session = Mock()
            mock_session.get.return_value = mock_response
            mock_session_class.return_value = mock_session

            custom_headers = {"User-Agent": "Custom Bot 1.0"}

            result = check_site("https://example.com", custom_headers=custom_headers)

            expected_headers = {"User-Agent": "Custom Bot 1.0"}

            mock_session.get.assert_called_with(
                "https://example.com",
                headers=expected_headers,
                timeout=5.0,
                allow_redirects=True,
            )
            assert result.status == "200"


class TestSiteCheckerHelpers:
    """Tests for site_checker helper functions."""

    def test_create_custom_headers_default_user_agent(self):
        """Default User-Agent is always present."""
        headers = _create_custom_headers()
        assert "User-Agent" in headers
        assert "httpcheck" in headers["User-Agent"]

    def test_create_custom_headers_merged(self):
        """Custom headers are merged with the default User-Agent."""
        headers = _create_custom_headers({"X-Custom": "test"})
        assert "User-Agent" in headers
        assert headers["X-Custom"] == "test"

    def test_should_stop_redirect_http_only_stops_https(self):
        """http-only stops at HTTPS redirect URLs."""
        assert _should_stop_redirect("http-only", "https://example.com") is True

    def test_should_stop_redirect_http_only_allows_http(self):
        """http-only allows HTTP redirect URLs."""
        assert _should_stop_redirect("http-only", "http://example.com") is False

    def test_should_stop_redirect_https_only_stops_http(self):
        """https-only stops at HTTP redirect URLs."""
        assert _should_stop_redirect("https-only", "http://example.com") is True

    def test_should_stop_redirect_https_only_allows_https(self):
        """https-only allows HTTPS redirect URLs."""
        assert _should_stop_redirect("https-only", "https://example.com") is False

    def test_should_stop_redirect_always_never_stops(self):
        """always policy never stops a redirect."""
        assert _should_stop_redirect("always", "https://example.com") is False
        assert _should_stop_redirect("always", "http://example.com") is False

    def test_handle_request_exception_timeout_on_last_attempt(self):
        """Returns SiteStatus with [timeout] for Timeout on the last attempt."""
        exc = requests.Timeout("timed out")
        result = _handle_request_exception(
            exc,
            attempt=0,
            retries=0,
            retry_delay=0,
            site="https://example.com",
            verify_ssl=True,
        )
        assert result is not None
        assert result.status == "[timeout]"

    def test_handle_request_exception_connection_error_on_last_attempt(self):
        """Returns SiteStatus with [connection error] for ConnectionError."""
        exc = requests.ConnectionError("refused")
        result = _handle_request_exception(
            exc,
            attempt=2,
            retries=2,
            retry_delay=0,
            site="https://example.com",
            verify_ssl=True,
        )
        assert result is not None
        assert result.status == "[connection error]"

    def test_handle_request_exception_http_error_without_response(self):
        """HTTPError with no response attribute falls back gracefully."""
        exc = requests.HTTPError("bad")
        exc.response = None  # no response object
        result = _handle_request_exception(
            exc,
            attempt=0,
            retries=0,
            retry_delay=0,
            site="https://example.com",
            verify_ssl=True,
        )
        assert result is not None
        assert result.status == "None"

    def test_handle_request_exception_not_last_attempt_returns_none(self):
        """Before the last attempt, returns None to signal retry."""
        exc = requests.ConnectionError("refused")
        result = _handle_request_exception(
            exc,
            attempt=0,
            retries=2,
            retry_delay=0,
            site="https://example.com",
            verify_ssl=True,
        )
        assert result is None

    def test_handle_request_exception_ssl_request_exception(self):
        """RequestException with SSL in message includes ssl context in error."""
        exc = requests.RequestException("SSL certificate error")
        result = _handle_request_exception(
            exc,
            attempt=0,
            retries=0,
            retry_delay=0,
            site="https://example.com",
            verify_ssl=False,
        )
        assert result is not None
        assert "SSL verification disabled" in result.message
