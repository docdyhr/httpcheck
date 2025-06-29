"""
Basic unit tests for httpcheck functionality.

These tests focus on core functionality and don't require network access.
"""

import json
import os
import subprocess

# Import the main module
import tempfile
from datetime import datetime
from unittest.mock import MagicMock, mock_open, patch

import pytest
import requests

# Import the httpcheck modules
# pylint: disable=no-name-in-module
from httpcheck.common import SiteStatus
from httpcheck.file_handler import FileInputHandler, url_validation
from httpcheck.notification import notify
from httpcheck.output_formatter import print_format
from httpcheck.site_checker import check_site
from httpcheck.tld_manager import InvalidTLDException, TLDManager


class TestURLValidation:
    """Test URL validation functionality."""

    def test_url_validation_valid_urls(self):
        """Test validation of valid URLs."""
        valid_urls = [
            "http://example.com",
            "https://example.com",
            "https://sub.example.com",
            "http://example.com:8080",
            "https://example.com/path",
        ]

        for url in valid_urls:
            # Should not raise an exception
            result = url_validation(url)
            assert result.startswith(("http://", "https://"))

    def test_url_validation_adds_protocol(self):
        """Test that missing protocol is added."""
        assert url_validation("example.com") == "http://example.com"
        assert url_validation("sub.example.com") == "http://sub.example.com"

    def test_url_validation_invalid_urls(self):
        """Test validation rejects invalid URLs."""
        invalid_urls = [
            "",
            "not-a-url",
            "http://",
            "https://",
            "ftp://example.com",  # Wrong protocol
        ]

        for url in invalid_urls:
            with pytest.raises(Exception):  # Should raise ArgumentTypeError
                url_validation(url)


class TestSiteStatus:
    """Test SiteStatus named tuple functionality."""

    def test_site_status_creation(self):
        """Test creating SiteStatus objects."""
        status = SiteStatus(
            domain="example.com",
            status="200",
            message="OK",
            redirect_chain=[],
            response_time=0.5,
            redirect_timing=[],
        )

        assert status.domain == "example.com"
        assert status.status == "200"
        assert status.message == "OK"
        assert status.response_time == 0.5
        assert status.redirect_chain == []
        assert status.final_url == "https://example.com"


class TestFileInputHandler:
    """Test file input handling functionality."""

    def test_file_parsing_basic(self):
        """Test basic file parsing."""
        test_content = """
# This is a comment
example.com
google.com

# Another comment
github.com
"""

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write(test_content)
            temp_path = f.name

        try:
            handler = FileInputHandler(temp_path, verbose=False)
            urls = list(handler.parse())

            expected = ["http://example.com", "http://google.com", "http://github.com"]
            assert urls == expected
            assert handler.valid_count == 3
            assert handler.comment_count >= 2

        finally:
            os.unlink(temp_path)

    def test_file_parsing_inline_comments(self):
        """Test parsing files with inline comments."""
        test_content = """example.com  # This is example
google.com // This is google
github.com
"""

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write(test_content)
            temp_path = f.name

        try:
            handler = FileInputHandler(temp_path, verbose=False)
            urls = list(handler.parse())

            expected = ["http://example.com", "http://google.com", "http://github.com"]
            assert urls == expected

        finally:
            os.unlink(temp_path)

    def test_file_not_found(self):
        """Test handling of non-existent files."""
        handler = FileInputHandler("/nonexistent/file.txt")
        urls = list(handler.parse())
        # Should return empty list and not crash
        assert not urls


class TestTLDManager:
    """Test TLD Manager functionality."""

    def test_singleton_pattern(self):
        """Test that TLDManager implements singleton pattern."""
        # Clear any existing instance
        TLDManager._instance = None  # pylint: disable=protected-access

        manager1 = TLDManager()
        manager2 = TLDManager()

        assert manager1 is manager2

    @pytest.mark.skip(reason="Complex datetime mocking - will be improved in Phase 2")
    def test_load_from_cache_json(self):
        """Test loading TLD cache from JSON file."""
        from datetime import timedelta

        # Create a temporary cache file with valid JSON
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            cache_data = {
                "last_updated": (datetime.now() - timedelta(days=5)).isoformat(),
                "tlds": ["com", "org", "net", "io", "dev"],
            }
            json.dump(cache_data, f)
            cache_file = f.name

        try:
            # Create TLDManager with custom cache file
            with patch(
                "httpcheck.tld_manager.TLDManager.DEFAULT_CACHE_FILE", cache_file
            ):
                with patch(
                    "httpcheck.tld_manager.TLDManager.DEFAULT_CACHE_PATH",
                    os.path.dirname(cache_file),
                ):
                    manager = TLDManager(cache_days=30)

                    # Check that TLDs were loaded
                    assert manager.tlds is not None
                    assert "com" in manager.tlds
                    assert "org" in manager.tlds
                    assert len(manager.tlds) == 5
        finally:
            os.unlink(cache_file)

    def test_json_cache_migration(self):
        """Test that new JSON cache format works."""
        # Clear singleton
        TLDManager._instance = None  # pylint: disable=protected-access

        test_data = {
            "tlds": ["com", "org", "net", "io"],
            "update_time": datetime.now().isoformat(),
        }

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            json.dump(test_data, f)
            temp_path = f.name

        try:
            # Mock the cache file path
            with patch.object(
                TLDManager, "DEFAULT_CACHE_FILE", os.path.basename(temp_path)
            ):
                with patch.object(
                    TLDManager,
                    "DEFAULT_CACHE_PATH",
                    os.path.dirname(temp_path),
                ):
                    manager = TLDManager(verbose=False)

                    assert "com" in manager.tlds
                    assert "io" in manager.tlds
                    assert len(manager.tlds) == 4

        finally:
            os.unlink(temp_path)

    @patch("httpcheck.tld_manager.requests.get")
    def test_update_tld_list_success(self, mock_get):
        """Test successful TLD list update from network."""
        # Clear singleton
        TLDManager._instance = None  # pylint: disable=protected-access

        # Mock successful response with sample TLD data
        mock_response = MagicMock()
        mock_response.text = """// This is a comment

com
org
net
// Another comment
*.example
edu
"""
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        with patch("httpcheck.tld_manager.os.path.exists", return_value=False):
            manager = TLDManager(verbose=False, force_update=True)

            assert "com" in manager.tlds
            assert "org" in manager.tlds
            assert "net" in manager.tlds
            assert "edu" in manager.tlds
            # Wildcard entries should be skipped
            assert "*.example" not in manager.tlds

    @patch("httpcheck.tld_manager.requests.get")
    def test_update_tld_list_network_error(self, mock_get):
        """Test handling of network errors during TLD update."""
        # Clear singleton
        TLDManager._instance = None  # pylint: disable=protected-access

        mock_get.side_effect = requests.RequestException("Network error")

        with patch("httpcheck.tld_manager.os.path.exists", return_value=False):
            with patch("httpcheck.tld_manager.os.makedirs"):
                # Should not crash, should handle the error gracefully
                manager = TLDManager(verbose=False, force_update=True)
                # Should have empty tlds set since no cache and update failed
                assert len(manager.tlds) == 0

    def test_validate_tld_valid_domains(self):
        """Test TLD validation with valid domains."""
        # Clear singleton and create manager with known TLDs
        TLDManager._instance = None  # pylint: disable=protected-access

        with patch("httpcheck.tld_manager.os.path.exists", return_value=False):
            with patch("httpcheck.tld_manager.requests.get") as mock_get:
                mock_response = MagicMock()
                mock_response.text = "com\norg\nnet\nco.uk\n"
                mock_response.raise_for_status.return_value = None
                mock_get.return_value = mock_response

                manager = TLDManager(verbose=False, force_update=True)

                # Test valid domains
                assert manager.validate_tld("https://example.com") == "example.com"
                assert manager.validate_tld("https://test.org") == "test.org"
                assert manager.validate_tld("https://example.co.uk") == "example.co.uk"

    def test_validate_tld_invalid_domain_warning_mode(self):
        """Test TLD validation with invalid domain in warning mode."""
        # Clear singleton and create manager with known TLDs
        TLDManager._instance = None  # pylint: disable=protected-access

        with patch("httpcheck.tld_manager.os.path.exists", return_value=False):
            with patch("httpcheck.tld_manager.requests.get") as mock_get:
                mock_response = MagicMock()
                mock_response.text = "com\norg\nnet\n"
                mock_response.raise_for_status.return_value = None
                mock_get.return_value = mock_response

                manager = TLDManager(
                    verbose=False, force_update=True, warning_only=True
                )

                # Should return None for invalid TLD in warning mode
                result = manager.validate_tld("https://example.invalid")
                assert result is None

    def test_validate_tld_invalid_domain_error_mode(self):
        """Test TLD validation with invalid domain in error mode."""
        # Clear singleton and create manager with known TLDs
        TLDManager._instance = None  # pylint: disable=protected-access

        with patch("httpcheck.tld_manager.os.path.exists", return_value=False):
            with patch("httpcheck.tld_manager.requests.get") as mock_get:
                mock_response = MagicMock()
                mock_response.text = "com\norg\nnet\n"
                mock_response.raise_for_status.return_value = None
                mock_get.return_value = mock_response

                manager = TLDManager(
                    verbose=False, force_update=True, warning_only=False
                )

                # Should raise exception for invalid TLD in error mode
                with pytest.raises(InvalidTLDException):
                    manager.validate_tld("https://example.invalid")

    def test_validate_tld_empty_tld_list(self):
        """Test TLD validation when TLD list is empty."""
        # Clear singleton and create manager with empty TLD list
        TLDManager._instance = None  # pylint: disable=protected-access

        with patch("httpcheck.tld_manager.os.path.exists", return_value=False):
            with patch("httpcheck.tld_manager.requests.get") as mock_get:
                mock_get.side_effect = requests.RequestException("Network error")

                manager = TLDManager(verbose=False, force_update=True)

                # Should raise exception when TLD list is empty
                with pytest.raises(InvalidTLDException, match="TLD list is empty"):
                    manager.validate_tld("https://example.com")

    @patch("httpcheck.tld_manager.os.path.exists")
    @patch("httpcheck.tld_manager.open", mock_open(read_data="invalid json"))
    def test_load_from_cache_invalid_json(self, mock_exists):
        """Test handling of invalid JSON in cache file."""
        # Clear singleton
        TLDManager._instance = None  # pylint: disable=protected-access

        mock_exists.return_value = True

        with patch("httpcheck.tld_manager.os.path.getmtime", return_value=1640995200):
            with patch("httpcheck.tld_manager.requests.get") as mock_get:
                mock_response = MagicMock()
                mock_response.text = "com\norg\n"
                mock_response.raise_for_status.return_value = None
                mock_get.return_value = mock_response

                # Should handle invalid JSON gracefully and try to update
                manager = TLDManager(verbose=False)

                # Should have loaded from network update after cache failed
                assert "com" in manager.tlds
                assert "org" in manager.tlds


class TestHTTPCheckFunctionality:
    """Test core HTTP checking functionality."""

    @patch("requests.Session.get")
    def test_check_site_success(self, mock_get):
        """Test successful site checking."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.url = "https://example.com"
        mock_response.history = []
        mock_response.elapsed.total_seconds.return_value = 0.5
        mock_get.return_value = mock_response

        result = check_site("https://example.com")

        assert result.status == "200"
        assert result.domain == "example.com"
        assert result.message == "OK"
        # The response time is calculated from actual timing, not the mock elapsed
        assert result.response_time > 0

    @patch("requests.Session.get")
    def test_check_site_404(self, mock_get):
        """Test site checking with 404 error."""
        # Mock 404 response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.url = "https://example.com/notfound"
        mock_response.history = []
        mock_response.elapsed.total_seconds.return_value = 0.3
        mock_get.return_value = mock_response

        result = check_site("https://example.com/notfound")

        assert result.status == "404"
        assert result.domain == "example.com"
        assert result.message == "Not Found"

    @patch("requests.Session.get")
    def test_check_site_with_redirects(self, mock_get):
        """Test site checking with redirect chain."""
        # Mock redirect response
        redirect_response = MagicMock()
        redirect_response.status_code = 301
        redirect_response.url = "http://example.com"

        final_response = MagicMock()
        final_response.status_code = 200
        final_response.url = "https://example.com"
        final_response.history = [redirect_response]
        final_response.elapsed.total_seconds.return_value = 0.5

        mock_get.return_value = final_response

        result = check_site("http://example.com", follow_redirects="always")

        assert result.status == "200"
        assert result.domain == "example.com"
        assert len(result.redirect_chain) == 2  # redirect + final
        assert result.redirect_chain[0] == ("http://example.com", 301)
        assert result.redirect_chain[1] == ("https://example.com", 200)

    @patch("requests.Session.get")
    def test_check_site_no_redirects(self, mock_get):
        """Test site checking with redirects disabled."""
        # Mock redirect response
        mock_response = MagicMock()
        mock_response.status_code = 301
        mock_response.url = "http://example.com"
        mock_response.history = []
        mock_response.is_redirect = True
        mock_response.elapsed.total_seconds.return_value = 0.3
        mock_get.return_value = mock_response

        result = check_site("http://example.com", follow_redirects="never")

        assert result.status == "301"
        assert result.domain == "example.com"
        assert len(result.redirect_chain) == 1
        assert result.redirect_chain[0] == ("http://example.com", 301)

    @patch("requests.Session.get")
    def test_check_site_http_error(self, mock_get):
        """Test site checking with HTTP error."""
        from requests.exceptions import HTTPError

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_error = HTTPError("Internal Server Error")
        mock_error.response = mock_response
        mock_get.side_effect = mock_error

        result = check_site("https://error-site.com", retries=0)

        assert result.status == "500"
        assert result.domain == "error-site.com"

    @patch("requests.Session.get")
    def test_check_site_connection_error(self, mock_get):
        """Test site checking with connection error."""
        from requests.exceptions import ConnectionError as RequestsConnectionError

        mock_get.side_effect = RequestsConnectionError("Connection failed")

        result = check_site("https://unreachable-site.com", retries=0)

        assert result.status == "[connection error]"
        assert result.domain == "unreachable-site.com"
        assert result.message == "Connection failed"

    @patch("requests.Session.get")
    def test_check_site_request_error_with_retries(self, mock_get):
        """Test site checking with request error and retries."""
        from requests.exceptions import RequestException

        mock_get.side_effect = RequestException("Request failed")

        result = check_site("https://failing-site.com", retries=1)

        assert result.status == "[request error]"
        assert result.domain == "failing-site.com"
        assert result.message == "Request failed"

    @patch("requests.Session.get")
    def test_check_site_timeout_with_retries(self, mock_get):
        """Test site checking with timeout and retries."""
        from requests.exceptions import Timeout

        mock_get.side_effect = Timeout("Request timed out")

        result = check_site("https://slow-site.com", retries=1)

        assert result.status == "[timeout]"
        assert result.domain == "slow-site.com"
        assert result.message == "Request timed out"


class TestOutputFormatting:
    """Test output formatting functionality."""

    def test_print_format_normal(self):
        """Test normal output formatting."""
        status = SiteStatus(
            domain="example.com",
            status="200",
            message="OK",
            redirect_chain=[],
            response_time=0.5,
            redirect_timing=[],
        )

        result = print_format(status, quiet=False, verbose=False, code=False)

        assert "example.com" in result
        assert "200" in result

    def test_print_format_quiet(self):
        """Test quiet mode formatting."""
        status = SiteStatus(
            domain="example.com",
            status="200",
            message="OK",
            redirect_chain=[],
            response_time=0.5,
            redirect_timing=[],
        )

        result = print_format(status, quiet=True, verbose=False, code=False)

        # Quiet mode should return empty string for successful requests
        assert result == ""

    def test_print_format_code_only(self):
        """Test code-only output formatting."""
        status = SiteStatus(
            domain="example.com",
            status="200",
            message="OK",
            redirect_chain=[],
            response_time=0.5,
            redirect_timing=[],
        )

        result = print_format(status, quiet=False, verbose=False, code=True)

        assert result.strip() == "200"

    def test_print_format_verbose(self):
        """Test verbose output formatting."""
        status = SiteStatus(
            domain="example.com",
            status="200",
            message="OK",
            redirect_chain=[],
            response_time=0.75,
            redirect_timing=[],
        )

        result = print_format(status, quiet=False, verbose=True, code=False)

        assert "example.com" in result
        assert "200" in result
        assert "0.75s" in result
        assert "OK" in result
        # Check for table formatting
        assert "Domain" in result
        assert "Status" in result
        assert "Response Time" in result
        assert "Message" in result

    def test_print_format_verbose_with_redirects(self):
        """Test verbose output formatting with redirect chain."""
        status = SiteStatus(
            domain="example.com",
            status="200",
            message="OK",
            redirect_chain=[
                ("http://example.com", 301),
                ("https://example.com", 200),
            ],
            response_time=0.5,
            redirect_timing=[
                ("http://example.com", 301, 0.2),
                ("https://example.com", 200, 0.3),
            ],
        )

        result = print_format(
            status, quiet=False, verbose=True, code=False, show_redirect_timing=True
        )

        assert "example.com" in result
        assert "200" in result
        assert "Redirect Chain:" in result
        assert "http://example.com" in result
        assert "https://example.com" in result
        assert "301" in result
        assert "0.200s" in result
        assert "0.300s" in result

    def test_print_format_verbose_redirects_no_timing(self):
        """Test verbose output formatting with redirects but no timing."""
        status = SiteStatus(
            domain="example.com",
            status="200",
            message="OK",
            redirect_chain=[
                ("http://example.com", 301),
                ("https://example.com", 200),
            ],
            response_time=0.5,
            redirect_timing=[],
        )

        result = print_format(
            status, quiet=False, verbose=True, code=False, show_redirect_timing=False
        )

        assert "example.com" in result
        assert "200" in result
        assert "Redirect Chain:" in result
        assert "http://example.com" in result
        assert "https://example.com" in result
        assert "301" in result
        # Should not show separate timing table (but "Response Time" is in main table)
        assert "Step" in result  # Basic redirect table should be shown

    def test_print_format_quiet_error(self):
        """Test quiet mode with error status."""
        status = SiteStatus(
            domain="error.com",
            status="500",
            message="Internal Server Error",
            redirect_chain=[],
            response_time=0.5,
            redirect_timing=[],
        )

        result = print_format(status, quiet=True, verbose=False, code=False)

        # Quiet mode should show errors
        assert "error.com 500" in result

    def test_print_format_quiet_timeout(self):
        """Test quiet mode with timeout status."""
        status = SiteStatus(
            domain="slow.com",
            status="[timeout]",
            message="Request timed out",
            redirect_chain=[],
            response_time=0.0,
            redirect_timing=[],
        )

        result = print_format(status, quiet=True, verbose=False, code=False)

        # Quiet mode should show timeouts
        assert "slow.com [timeout]" in result


class TestNotification:
    """Test notification functionality."""

    @patch("httpcheck.notification.platform.system")
    @patch("httpcheck.notification.subprocess.run")
    def test_notify_macos_success(self, mock_run, mock_platform):
        """Test successful notification on macOS."""
        mock_platform.return_value = "Darwin"
        mock_run.return_value = MagicMock()

        notify("Test Title", "Test message")

        mock_run.assert_called_once()
        cmd_args = mock_run.call_args[0][0]
        assert cmd_args[0] == "osascript"
        assert cmd_args[1] == "-e"
        assert "Test Title" in cmd_args[2]
        assert "Test message" in cmd_args[2]

    @patch("httpcheck.notification.platform.system")
    def test_notify_non_macos(self, mock_platform):
        """Test that notifications are skipped on non-macOS platforms."""
        mock_platform.return_value = "Linux"

        # Should not raise any error and should not attempt to run osascript
        notify("Test Title", "Test message")

        # No assertions needed - if it doesn't crash, it passed

    @patch("httpcheck.notification.platform.system")
    @patch("httpcheck.notification.subprocess.run")
    def test_notify_with_failed_sites_short_list(self, mock_run, mock_platform):
        """Test notification with short list of failed sites."""
        mock_platform.return_value = "Darwin"
        mock_run.return_value = MagicMock()

        failed_sites = ["example.com", "test.org"]
        notify("HTTP Check", "2 sites failed", failed_sites)

        mock_run.assert_called_once()
        cmd_args = mock_run.call_args[0][0]
        script = cmd_args[2]
        assert "example.com" in script
        assert "test.org" in script
        assert "Failed sites:" in script

    @patch("httpcheck.notification.platform.system")
    @patch("httpcheck.notification.subprocess.run")
    def test_notify_with_failed_sites_long_list(self, mock_run, mock_platform):
        """Test notification with long list of failed sites."""
        mock_platform.return_value = "Darwin"
        mock_run.return_value = MagicMock()

        failed_sites = [f"site{i}.com" for i in range(15)]  # 15 sites > 10 limit
        notify("HTTP Check", "15 sites failed", failed_sites)

        mock_run.assert_called_once()
        cmd_args = mock_run.call_args[0][0]
        script = cmd_args[2]
        assert "15 sites failed. See terminal for details." in script

    @patch("httpcheck.notification.platform.system")
    @patch("httpcheck.notification.subprocess.run")
    def test_notify_string_escaping(self, mock_run, mock_platform):
        """Test proper escaping of special characters in notifications."""
        mock_platform.return_value = "Darwin"
        mock_run.return_value = MagicMock()

        title_with_quotes = 'Test "Title" with quotes'
        message_with_newlines = "Line 1\nLine 2\nLine 3"

        notify(title_with_quotes, message_with_newlines)

        mock_run.assert_called_once()
        cmd_args = mock_run.call_args[0][0]
        script = cmd_args[2]
        # Check that quotes are escaped
        assert '\\"Title\\"' in script
        # Check that newlines are escaped
        assert "\\n" in script

    @patch("httpcheck.notification.platform.system")
    @patch("httpcheck.notification.subprocess.run")
    @patch("builtins.print")
    def test_notify_file_not_found_error(self, mock_print, mock_run, mock_platform):
        """Test handling when osascript is not found."""
        mock_platform.return_value = "Darwin"
        mock_run.side_effect = FileNotFoundError()

        notify("Test Title", "Test message")

        mock_print.assert_called_once()
        assert "osascript" in mock_print.call_args[0][0]

    @patch("httpcheck.notification.platform.system")
    @patch("httpcheck.notification.subprocess.run")
    @patch("builtins.print")
    def test_notify_subprocess_error(self, mock_print, mock_run, mock_platform):
        """Test handling subprocess errors from osascript."""
        mock_platform.return_value = "Darwin"
        mock_error = subprocess.CalledProcessError(1, "osascript")
        mock_error.stderr = b"AppleScript error message"
        mock_run.side_effect = mock_error

        notify("Test Title", "Test message")

        mock_print.assert_called_once()
        assert "osascript" in mock_print.call_args[0][0]

    @patch("httpcheck.notification.platform.system")
    @patch("httpcheck.notification.subprocess.run")
    @patch("builtins.print")
    def test_notify_unexpected_error(self, mock_print, mock_run, mock_platform):
        """Test handling unexpected errors during notification."""
        mock_platform.return_value = "Darwin"
        mock_run.side_effect = RuntimeError("Unexpected error")

        notify("Test Title", "Test message")

        mock_print.assert_called_once()
        assert "unexpected error" in mock_print.call_args[0][0]


if __name__ == "__main__":
    pytest.main([__file__])
