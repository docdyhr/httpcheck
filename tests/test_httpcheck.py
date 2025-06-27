"""
Basic unit tests for httpcheck functionality.

These tests focus on core functionality and don't require network access.
"""

import json
import os

# Import the main module
import sys
import tempfile
from datetime import datetime
from unittest.mock import MagicMock, mock_open, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import httpcheck


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
            result = httpcheck.url_validation(url)
            assert result.startswith(("http://", "https://"))

    def test_url_validation_adds_protocol(self):
        """Test that missing protocol is added."""
        assert httpcheck.url_validation("example.com") == "http://example.com"
        assert httpcheck.url_validation("sub.example.com") == "http://sub.example.com"

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
                httpcheck.url_validation(url)


class TestSiteStatus:
    """Test SiteStatus named tuple functionality."""

    def test_site_status_creation(self):
        """Test creating SiteStatus objects."""
        status = httpcheck.SiteStatus(
            domain="example.com",
            status="200",
            message="OK",
            response_time=0.5,
            redirect_chain=[],
            final_url="https://example.com",
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
            handler = httpcheck.FileInputHandler(temp_path, verbose=False)
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
            handler = httpcheck.FileInputHandler(temp_path, verbose=False)
            urls = list(handler.parse())

            expected = ["http://example.com", "http://google.com", "http://github.com"]
            assert urls == expected

        finally:
            os.unlink(temp_path)

    def test_file_not_found(self):
        """Test handling of non-existent files."""
        with pytest.raises(FileNotFoundError):
            handler = httpcheck.FileInputHandler("/nonexistent/file.txt")
            list(handler.parse())


class TestTLDManager:
    """Test TLD Manager functionality."""

    def test_singleton_pattern(self):
        """Test that TLDManager implements singleton pattern."""
        # Clear any existing instance
        httpcheck.TLDManager._instance = None

        manager1 = httpcheck.TLDManager()
        manager2 = httpcheck.TLDManager()

        assert manager1 is manager2

    @patch(
        "builtins.open",
        mock_open(
            read_data='{"tlds": ["com", "org", "net"], "update_time": "2023-01-01T00:00:00"}'
        ),
    )
    @patch("os.path.exists", return_value=True)
    @patch("os.path.getmtime", return_value=1640995200)  # Recent timestamp
    def test_load_from_cache_json(self, mock_getmtime, mock_exists):
        """Test loading TLD cache from JSON file."""
        # Clear singleton
        httpcheck.TLDManager._instance = None

        manager = httpcheck.TLDManager(verbose=False)

        # Should have loaded from mock cache
        assert "com" in manager.tlds
        assert "org" in manager.tlds
        assert "net" in manager.tlds
        assert len(manager.tlds) == 3

    def test_json_cache_migration(self):
        """Test that new JSON cache format works."""
        # Clear singleton
        httpcheck.TLDManager._instance = None

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
                httpcheck.TLDManager, "DEFAULT_CACHE_FILE", os.path.basename(temp_path)
            ):
                with patch.object(
                    httpcheck.TLDManager,
                    "DEFAULT_CACHE_PATH",
                    os.path.dirname(temp_path),
                ):
                    manager = httpcheck.TLDManager(verbose=False)

                    assert "com" in manager.tlds
                    assert "io" in manager.tlds
                    assert len(manager.tlds) == 4

        finally:
            os.unlink(temp_path)


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

        result = httpcheck.check_site("https://example.com")

        assert result.status == "200"
        assert result.domain == "example.com"
        assert result.message == "OK"
        assert result.response_time == 0.5

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

        result = httpcheck.check_site("https://example.com/notfound")

        assert result.status == "404"
        assert result.domain == "example.com"
        assert result.message == "Not Found"

    @patch("requests.Session.get")
    def test_check_site_timeout(self, mock_get):
        """Test site checking with timeout."""
        from requests.exceptions import Timeout

        mock_get.side_effect = Timeout("Request timed out")

        result = httpcheck.check_site("https://slow-site.com", retries=0)

        assert result.status == "[timeout]"
        assert result.domain == "slow-site.com"
        assert result.message == "Request timed out"


class TestOutputFormatting:
    """Test output formatting functionality."""

    def test_print_format_normal(self):
        """Test normal output formatting."""
        status = httpcheck.SiteStatus(
            domain="example.com",
            status="200",
            message="OK",
            response_time=0.5,
            redirect_chain=[],
            final_url="https://example.com",
        )

        result = httpcheck.print_format(
            status, quiet=False, verbose=False, code_only=False
        )

        assert "example.com" in result
        assert "200" in result
        assert "OK" in result

    def test_print_format_quiet(self):
        """Test quiet mode formatting."""
        status = httpcheck.SiteStatus(
            domain="example.com",
            status="200",
            message="OK",
            response_time=0.5,
            redirect_chain=[],
            final_url="https://example.com",
        )

        result = httpcheck.print_format(
            status, quiet=True, verbose=False, code_only=False
        )

        # Quiet mode should return empty string for successful requests
        assert result == ""

    def test_print_format_code_only(self):
        """Test code-only output formatting."""
        status = httpcheck.SiteStatus(
            domain="example.com",
            status="200",
            message="OK",
            response_time=0.5,
            redirect_chain=[],
            final_url="https://example.com",
        )

        result = httpcheck.print_format(
            status, quiet=False, verbose=False, code_only=True
        )

        assert result.strip() == "200"


if __name__ == "__main__":
    pytest.main([__file__])
